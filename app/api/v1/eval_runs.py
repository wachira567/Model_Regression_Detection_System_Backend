from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.eval_run import EvalRun
from app.models.eval_result import EvalResult
from app.services.diff_engine import DiffEngine
import uuid

router = APIRouter()

@router.get("/")
async def list_eval_runs(limit: int = 10, db: AsyncSession = Depends(get_db)):
    stmt = select(EvalRun).order_by(EvalRun.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{run_id}")
async def get_eval_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(EvalRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/{run_id}/results")
async def get_eval_results(run_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(EvalResult).where(EvalResult.eval_run_id == run_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{curr_run_id}/diff/{base_run_id}")
async def get_diff(curr_run_id: str, base_run_id: str, db: AsyncSession = Depends(get_db)):
    diff_engine = DiffEngine(db)
    report = await diff_engine.compare(curr_run_id, base_run_id)
    if not report:
        raise HTTPException(status_code=404, detail="One or both runs not found")
    return report
