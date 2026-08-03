from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.prompt_config import PromptConfig
from app.models.eval_run import EvalRun
from app.services.eval_engine import execute_eval_run
import uuid

router = APIRouter()

@router.post("/run/{feature_id}")
async def trigger_eval_run(feature_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # Get active prompt config
    stmt = select(PromptConfig).where(
        PromptConfig.feature_id == feature_id,
        PromptConfig.is_active == True
    ).order_by(PromptConfig.created_at.desc()).limit(1)
    
    result = await db.execute(stmt)
    prompt_config = result.scalars().first()
    
    if not prompt_config:
        raise HTTPException(status_code=404, detail="No active prompt config found for feature")
        
    eval_run = EvalRun(
        prompt_config_id=prompt_config.id,
        dataset_version="latest",  # Simplification for now
        trigger_type="manual",
        status="pending"
    )
    db.add(eval_run)
    await db.commit()
    
    background_tasks.add_task(execute_eval_run, str(eval_run.id))
    
    return {"message": "Eval run started in the background", "eval_run_id": str(eval_run.id)}
