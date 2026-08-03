from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from jinja2 import Template
from app.db.session import get_db
from app.services.diff_engine import DiffEngine
from datetime import datetime, timedelta

from app.services.report_generator import ReportGenerator

from app.dependencies import get_current_org
from app.models.eval_run import EvalRun

router = APIRouter()

@router.get("/{curr_run_id}/diff/{base_run_id}", response_class=HTMLResponse)
async def generate_html_report(curr_run_id: str, base_run_id: str, db: AsyncSession = Depends(get_db), org_id: str = Depends(get_current_org)):
    curr_run = await db.get(EvalRun, curr_run_id)
    base_run = await db.get(EvalRun, base_run_id)
    if not curr_run or curr_run.organization_id != org_id or not base_run or base_run.organization_id != org_id:
        raise HTTPException(status_code=404, detail="One or both runs not found")

    diff_engine = DiffEngine(db)
    report = await diff_engine.compare(curr_run_id, base_run_id)
    if not report:
        raise HTTPException(status_code=404, detail="One or both runs not found")
        
    generator = ReportGenerator()
    html_content = generator.generate_html(report)
    return HTMLResponse(content=html_content)

@router.get("/analytics/trends")
async def get_analytics_trends(
    days: int = 7, 
    db: AsyncSession = Depends(get_db), 
    org_id: str = Depends(get_current_org)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Simple grouping by casting timestamp to Date in Postgres
    stmt = (
        select(
            func.date(EvalRun.created_at).label("day"),
            func.avg(EvalRun.overall_accuracy).label("avg_accuracy"),
            func.avg(EvalRun.avg_latency_ms).label("avg_latency")
        )
        .where(EvalRun.organization_id == org_id)
        .where(EvalRun.created_at >= start_date)
        .where(EvalRun.status == 'completed')
        .group_by(func.date(EvalRun.created_at))
        .order_by(func.date(EvalRun.created_at))
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    data = []
    for row in rows:
        day, acc, lat = row
        # Ensure it handles None safely
        data.append({
            "name": day.strftime("%b %d") if day else "Unknown",
            "accuracy": round((acc or 0) * 100, 1),
            "latency": round(lat or 0, 1)
        })
        
    return data
