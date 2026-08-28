from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.experiment import Experiment, ExperimentStatus
from app.models.experiment_variant import ExperimentVariant
from app.models.experiment_assignment import ExperimentAssignment
from app.models.prompt_config import PromptConfig
from app.models.eval_run import EvalRun

router = APIRouter(prefix="/experiments", tags=["Experiments"])

@router.post("/")
async def create_experiment(
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new experiment with variants"""
    feature_id = data.get("feature_id")
    name = data.get("name")
    variants = data.get("variants", []) # list of { prompt_config_id, traffic_percentage, is_baseline }
    
    if not feature_id or not name or not variants:
        raise HTTPException(status_code=400, detail="Missing required fields")
        
    # Validation: traffic must sum to 100
    if sum(v.get("traffic_percentage", 0) for v in variants) != 100:
        raise HTTPException(status_code=400, detail="Traffic percentages must sum to 100")
        
    experiment = Experiment(
        name=name,
        feature_id=feature_id,
        status=ExperimentStatus.DRAFT.value,
        organization_id="default_org" # Assuming default org for now
    )
    db.add(experiment)
    await db.flush()
    
    for v in variants:
        variant = ExperimentVariant(
            experiment_id=experiment.id,
            prompt_config_id=v["prompt_config_id"],
            traffic_percentage=v.get("traffic_percentage", 0),
            is_baseline=v.get("is_baseline", False)
        )
        db.add(variant)
        
    await db.commit()
    return {"status": "success", "experiment_id": str(experiment.id)}

@router.get("/")
async def list_experiments(
    feature_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Experiment).options(selectinload(Experiment.variants))
    if feature_id:
        query = query.where(Experiment.feature_id == feature_id)
        
    result = await db.execute(query)
    experiments = result.scalars().all()
    
    return [{
        "id": str(e.id),
        "name": e.name,
        "feature_id": e.feature_id,
        "status": e.status,
        "primary_metric": e.primary_metric,
        "created_at": e.created_at.isoformat(),
        "variants": [{
            "id": str(v.id),
            "prompt_config_id": str(v.prompt_config_id),
            "traffic_percentage": v.traffic_percentage,
            "is_baseline": v.is_baseline,
            "is_winner": v.is_winner
        } for v in e.variants]
    } for e in experiments]

@router.post("/{experiment_id}/start")
async def start_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Stop any other running experiments for this feature
    exp_query = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = exp_query.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    # Stop others
    await db.execute(
        select(Experiment).where(
            Experiment.feature_id == experiment.feature_id,
            Experiment.status == ExperimentStatus.RUNNING.value
        ).execution_options(synchronize_session=False)
    )
    # The above is just a select, let's actually update them if needed, but for simplicity we'll just check
    running_others = await db.execute(
        select(Experiment).where(
            Experiment.feature_id == experiment.feature_id,
            Experiment.status == ExperimentStatus.RUNNING.value,
            Experiment.id != experiment_id
        )
    )
    for other in running_others.scalars().all():
        other.status = ExperimentStatus.COMPLETED.value
        
    experiment.status = ExperimentStatus.RUNNING.value
    await db.commit()
    return {"status": "success"}

@router.post("/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    exp_query = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = exp_query.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    experiment.status = ExperimentStatus.COMPLETED.value
    await db.commit()
    return {"status": "success"}

@router.get("/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Fetch all variants
    exp_query = await db.execute(
        select(Experiment).options(selectinload(Experiment.variants)).where(Experiment.id == experiment_id)
    )
    experiment = exp_query.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    # In a real app, this would query experiment_assignments joined with eval_runs and eval_results
    # Since our "live" traffic is actually triggered through our eval pipeline offline,
    # we just fetch the latest EvalRun for each variant's PromptConfig
    
    results = []
    for variant in experiment.variants:
        eval_query = await db.execute(
            select(EvalRun).where(
                EvalRun.prompt_config_id == variant.prompt_config_id,
                EvalRun.status == "completed"
            ).order_by(EvalRun.completed_at.desc()).limit(1)
        )
        eval_run = eval_query.scalar_one_or_none()
        
        if eval_run:
            results.append({
                "variant_id": str(variant.id),
                "is_baseline": variant.is_baseline,
                "is_winner": variant.is_winner,
                "metrics": {
                    "accuracy": eval_run.overall_accuracy,
                    "relevance": eval_run.avg_relevance_score,
                    "latency": eval_run.avg_latency_ms,
                    "sample_size": eval_run.total_cases
                }
            })
        else:
             results.append({
                "variant_id": str(variant.id),
                "is_baseline": variant.is_baseline,
                "is_winner": variant.is_winner,
                "metrics": {
                    "accuracy": 0,
                    "relevance": 0,
                    "latency": 0,
                    "sample_size": 0
                }
            })           
            
    # Calculate simple statistical winner if enough samples
    # For now, just compare means
    
    return {
        "experiment_id": str(experiment.id),
        "status": experiment.status,
        "primary_metric": experiment.primary_metric,
        "target_sample_size": experiment.target_sample_size,
        "variant_results": results
    }
