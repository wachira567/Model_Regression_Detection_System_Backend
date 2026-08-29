from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
import hmac
import hashlib
from app.config import settings
from app.services.eval_engine import execute_fast_eval_run
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.eval_run import EvalRun
from app.models.prompt_config import PromptConfig
from sqlalchemy import select

router = APIRouter()

async def verify_github_signature(request: Request):
    if not settings.GITHUB_WEBHOOK_SECRET:
        return True # Skip verification if not configured
        
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature")
        
    body = await request.body()
    secret = settings.GITHUB_WEBHOOK_SECRET.get_secret_value().encode()
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    await verify_github_signature(request)
    
    event = request.headers.get("X-GitHub-Event")
    if event != "push" and event != "pull_request":
        return {"message": "Event ignored"}
        
    payload = await request.json()
    
    # In a real scenario, we'd parse the payload to see which prompt files changed.
    # For now, we just trigger an eval run for the main feature ID as a demo.
    feature_id = "email_classifier"
    
    stmt = select(PromptConfig).where(PromptConfig.feature_id == feature_id).order_by(PromptConfig.created_at.desc()).limit(1)
    result = await db.execute(stmt)
    prompt_config = result.scalars().first()
    
    if prompt_config:
        eval_run = EvalRun(
            prompt_config_id=prompt_config.id,
            dataset_version="latest",
            trigger_type="ci",
            status="pending"
        )
        db.add(eval_run)
        await db.commit()
        
        background_tasks.add_task(execute_fast_eval_run, str(eval_run.id))
        return {"message": "CI Eval run triggered"}
        
    return {"message": "No active config found"}
