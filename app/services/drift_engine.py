import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.eval_run import EvalRun
from app.models.drift_snapshot import DriftSnapshot
from app.config import settings

logger = logging.getLogger(__name__)

class DriftEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect_drift(self, feature_id: str, new_eval_run_id: str) -> DriftSnapshot | None:
        """
        Calculates a rolling average of the last `DRIFT_WINDOW_SIZE` eval runs 
        for a given feature_id and compares it to the previous snapshot.
        """
        # Fetch the most recent completed eval runs for this feature
        # Since eval_run belongs to prompt_config, we need a join
        from app.models.prompt_config import PromptConfig
        
        stmt = (
            select(EvalRun)
            .join(PromptConfig)
            .where(PromptConfig.feature_id == feature_id)
            .where(EvalRun.status == "completed")
            .order_by(desc(EvalRun.completed_at))
            .limit(settings.DRIFT_WINDOW_SIZE)
        )
        
        result = await self.session.execute(stmt)
        recent_runs = result.scalars().all()
        
        if len(recent_runs) < settings.DRIFT_WINDOW_SIZE:
            logger.info(f"Not enough runs to calculate drift for {feature_id}. Have {len(recent_runs)}, need {settings.DRIFT_WINDOW_SIZE}.")
            return None
            
        # Calculate averages
        avg_accuracy = sum(r.overall_accuracy or 0 for r in recent_runs) / len(recent_runs)
        avg_relevance = sum(r.avg_relevance_score or 0 for r in recent_runs) / len(recent_runs)
        avg_latency = sum(r.avg_latency_ms or 0 for r in recent_runs) / len(recent_runs)
        
        # Determine if there is drift from previous snapshot
        prev_snapshot_stmt = (
            select(DriftSnapshot)
            .where(DriftSnapshot.feature_id == feature_id)
            .order_by(desc(DriftSnapshot.created_at))
            .limit(1)
        )
        prev_snapshot_result = await self.session.execute(prev_snapshot_stmt)
        prev_snapshot = prev_snapshot_result.scalars().first()
        
        drift_detected = False
        drift_type = "none"
        
        if prev_snapshot:
            # Check for regression (lower accuracy/relevance is worse)
            acc_diff = prev_snapshot.rolling_avg_accuracy - avg_accuracy
            if acc_diff >= settings.REGRESSION_CRITICAL_THRESHOLD:
                drift_detected = True
                drift_type = "critical"
            elif acc_diff >= settings.REGRESSION_WARNING_THRESHOLD:
                drift_detected = True
                drift_type = "warning"
                
            # Similar logic can be applied to relevance score or latency
            
        snapshot = DriftSnapshot(
            feature_id=feature_id,
            rolling_avg_accuracy=avg_accuracy,
            rolling_avg_relevance=avg_relevance,
            rolling_avg_latency_ms=avg_latency,
            window_size=settings.DRIFT_WINDOW_SIZE,
            drift_detected=drift_detected,
            drift_type=drift_type,
            window_run_ids=[str(r.id) for r in recent_runs]
        )
        self.session.add(snapshot)
        await self.session.commit()
        return snapshot
