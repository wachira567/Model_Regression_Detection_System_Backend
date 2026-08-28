import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.models.experiment import Experiment, ExperimentStatus
from app.models.experiment_variant import ExperimentVariant
from app.models.prompt_config import PromptConfig

class ExperimentRouter:
    @staticmethod
    def _hash_to_percentage(request_hash: str) -> int:
        """
        Converts a request hash string into a deterministic integer between 0 and 99.
        """
        hash_val = int(hashlib.sha256(request_hash.encode('utf-8')).hexdigest(), 16)
        return hash_val % 100

    @classmethod
    async def get_prompt_config(cls, db: Session, feature_id: str, request_hash: str) -> tuple[Optional[PromptConfig], Optional[ExperimentVariant]]:
        """
        Returns the appropriate PromptConfig and potentially the assigned ExperimentVariant for a given feature_id.
        If an active experiment is running, routes traffic based on variant percentages.
        Otherwise, returns the active baseline prompt config.
        """
        # 1. Check if there's a running experiment for this feature_id
        experiment = await db.execute(
            select(Experiment)
            .where(Experiment.feature_id == feature_id)
            .where(Experiment.status == ExperimentStatus.RUNNING.value)
            .limit(1)
        )
        experiment = experiment.scalar_one_or_none()

        if experiment:
            # 2. Get variants for the experiment
            variants_query = await db.execute(
                select(ExperimentVariant)
                .where(ExperimentVariant.experiment_id == experiment.id)
                .order_by(ExperimentVariant.id)
            )
            variants = variants_query.scalars().all()
            
            if variants:
                # 3. Determine bucket based on request_hash
                bucket = cls._hash_to_percentage(request_hash)
                
                current_threshold = 0
                for variant in variants:
                    current_threshold += variant.traffic_percentage
                    if bucket < current_threshold:
                        # Fetch the prompt config for this variant
                        prompt_query = await db.execute(select(PromptConfig).where(PromptConfig.id == variant.prompt_config_id))
                        prompt_config = prompt_query.scalar_one_or_none()
                        return prompt_config, variant
        
        # 4. Fallback: If no running experiment or routing failed, return the active baseline prompt config
        fallback_query = await db.execute(
            select(PromptConfig)
            .where(PromptConfig.feature_id == feature_id)
            .where(PromptConfig.is_active == True)
            .order_by(PromptConfig.created_at.desc())
            .limit(1)
        )
        fallback_config = fallback_query.scalar_one_or_none()
        
        return fallback_config, None
