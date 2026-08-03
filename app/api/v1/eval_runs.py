from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db.session import get_db
from app.models.eval_run import EvalRun
from app.schemas.pagination import PaginatedResponse
from app.models.eval_result import EvalResult
from app.services.diff_engine import DiffEngine
import uuid

from app.dependencies import get_current_org

router = APIRouter()

@router.get("/")
async def list_eval_runs(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db), 
    org_id: str = Depends(get_current_org)
):
    offset = (page - 1) * size
    
    stmt = select(EvalRun).where(EvalRun.organization_id == org_id)
    count_stmt = select(func.count(EvalRun.id)).where(EvalRun.organization_id == org_id)
    
    if search:
        search_filter = or_(
            EvalRun.status.ilike(f"%{search}%"),
            EvalRun.trigger_type.ilike(f"%{search}%")
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    stmt = stmt.order_by(EvalRun.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    runs = result.scalars().all()
    
    pages = (total + size - 1) // size
    
    return {
        "items": runs,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{run_id}")
async def get_eval_run(run_id: str, db: AsyncSession = Depends(get_db), org_id: str = Depends(get_current_org)):
    run = await db.get(EvalRun, run_id)
    if not run or run.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/{run_id}/results")
async def get_eval_results(run_id: str, db: AsyncSession = Depends(get_db), org_id: str = Depends(get_current_org)):
    run = await db.get(EvalRun, run_id)
    if not run or run.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Run not found")
    stmt = select(EvalResult).where(EvalResult.eval_run_id == run_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{curr_run_id}/diff/{base_run_id}")
async def get_diff(curr_run_id: str, base_run_id: str, db: AsyncSession = Depends(get_db), org_id: str = Depends(get_current_org)):
    curr_run = await db.get(EvalRun, curr_run_id)
    base_run = await db.get(EvalRun, base_run_id)
    if not curr_run or curr_run.organization_id != org_id or not base_run or base_run.organization_id != org_id:
        raise HTTPException(status_code=404, detail="One or both runs not found")
    
    diff_engine = DiffEngine(db)
    report = await diff_engine.compare(curr_run_id, base_run_id)
    if not report:
        raise HTTPException(status_code=404, detail="One or both runs not found")
    return report
