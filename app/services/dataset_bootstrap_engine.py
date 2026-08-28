import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.production_log import ProductionLog
from app.config import settings

class DatasetBootstrapEngine:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_dir = settings.GOLDEN_DATASET_DIR

    async def bootstrap_from_logs(self, feature_id: str, days_back: int = 7, max_cases: int = 50) -> Dict[str, Any]:
        """
        Harvests production logs, clusters them to find diverse examples,
        and bootstraps them into the Golden Dataset for the given feature.
        """
        # 1. Harvest Logs
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        logs_query = await self.db.execute(
            select(ProductionLog)
            .where(ProductionLog.feature_id == feature_id)
            .where(ProductionLog.created_at >= cutoff_date)
            # Prefer logs that got positive feedback, then just general logs
            .order_by(ProductionLog.user_feedback_score.desc(), ProductionLog.created_at.desc())
            .limit(max_cases * 3) # Fetch more to allow for filtering
        )
        logs = logs_query.scalars().all()

        if not logs:
            return {"status": "success", "added_cases": 0, "message": "No production logs found in the timeframe."}

        # 2. Extract & Cluster (Mocked clustering for now)
        # In a real scenario, we'd use an LLM or embeddings to cluster `input_data` to ensure diversity.
        # Here we will do a simple deduplication based on input hash and take the top `max_cases`.
        
        unique_inputs = set()
        selected_cases = []
        
        for log in logs:
            if len(selected_cases) >= max_cases:
                break
                
            # Stringify input to hash it
            input_str = json.dumps(log.input_data, sort_keys=True)
            if input_str not in unique_inputs:
                unique_inputs.add(input_str)
                selected_cases.append({
                    "id": f"tc-auto-{uuid.uuid4().hex[:8]}",
                    "input": log.input_data,
                    "expected_output": log.output_data, # For now, we assume the output was good (especially if feedback > 0)
                    "metadata": {
                        "source": "production_log",
                        "log_id": str(log.id),
                        "bootstrapped_at": datetime.utcnow().isoformat(),
                        "user_feedback": log.user_feedback_score
                    }
                })

        if not selected_cases:
            return {"status": "success", "added_cases": 0, "message": "No new unique cases found."}

        # 3. Write to Golden Dataset
        feature_dataset_path = os.path.join(self.dataset_dir, f"{feature_id}.json")
        
        dataset_content = {
            "feature_id": feature_id,
            "version": "1.0",
            "test_cases": []
        }
        
        if os.path.exists(feature_dataset_path):
            with open(feature_dataset_path, "r") as f:
                dataset_content = json.load(f)
                
        # Append new cases
        dataset_content["test_cases"].extend(selected_cases)
        
        # Bump version simply
        current_version = float(dataset_content.get("version", "1.0"))
        dataset_content["version"] = str(round(current_version + 0.1, 1))

        # Save back
        os.makedirs(self.dataset_dir, exist_ok=True)
        with open(feature_dataset_path, "w") as f:
            json.dump(dataset_content, f, indent=2)

        return {
            "status": "success", 
            "added_cases": len(selected_cases), 
            "new_dataset_version": dataset_content["version"],
            "message": f"Successfully bootstrapped {len(selected_cases)} cases into the golden dataset."
        }
