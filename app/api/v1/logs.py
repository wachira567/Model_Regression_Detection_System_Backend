from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.db.session import get_db
from app.models.production_log import ProductionLog

router = APIRouter(prefix="/logs", tags=["Production Logs"])

@router.post("/ingest")
async def ingest_production_log(
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a single production log from a live AI application.
    Expected data: feature_id, input_data, output_data, latency_ms, user_feedback_score (optional), prompt_config_id (optional)
    """
    feature_id = data.get("feature_id")
    input_data = data.get("input_data")
    output_data = data.get("output_data")
    
    if not feature_id or not input_data or not output_data:
        raise HTTPException(status_code=400, detail="Missing required fields: feature_id, input_data, or output_data")
        
    log = ProductionLog(
        organization_id="default_org",
        feature_id=feature_id,
        input_data=input_data,
        output_data=output_data,
        latency_ms=data.get("latency_ms"),
        user_feedback_score=data.get("user_feedback_score"),
        prompt_config_id=data.get("prompt_config_id")
    )
    
    db.add(log)
    await db.commit()
    
    return {"status": "success", "log_id": str(log.id)}
