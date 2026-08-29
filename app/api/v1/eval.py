from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.prompt_config import PromptConfig
from app.models.eval_run import EvalRun
from app.services.eval_engine import execute_fast_eval_run, execute_deep_eval_run
import uuid

from app.dependencies import get_current_org

router = APIRouter()

@router.post("/run/{feature_id}")
async def trigger_eval_run(feature_id: str, background_tasks: BackgroundTasks, eval_mode: str = "fast", db: AsyncSession = Depends(get_db), org_id: str = Depends(get_current_org)):
    # Get active prompt config
    stmt = select(PromptConfig).where(
        PromptConfig.feature_id == feature_id,
        PromptConfig.is_active == True,
        PromptConfig.organization_id == org_id
    ).order_by(PromptConfig.created_at.desc()).limit(1)
    
    result = await db.execute(stmt)
    prompt_config = result.scalars().first()
    
    if not prompt_config:
        raise HTTPException(status_code=404, detail="No active prompt config found for feature")
        
    eval_run = EvalRun(
        prompt_config_id=prompt_config.id,
        organization_id=org_id,
        dataset_version="latest",  # Simplification for now
        trigger_type="manual",
        status="pending"
    )
    db.add(eval_run)
    await db.commit()
    
    if eval_mode == "deep":
        background_tasks.add_task(execute_deep_eval_run, str(eval_run.id))
    else:
        background_tasks.add_task(execute_fast_eval_run, str(eval_run.id))
    
    return {"message": f"Eval run started in the background (Mode: {eval_mode})", "eval_run_id": str(eval_run.id)}
