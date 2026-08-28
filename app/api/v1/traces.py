import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.trace import Trace
from app.dependencies import get_current_org

router = APIRouter(prefix="/traces", tags=["Traces"])

@router.get("/eval/{eval_result_id}")
async def get_traces_for_eval(eval_result_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch all trace steps for a specific evaluation result.
    """
    try:
        uuid_val = uuid.UUID(eval_result_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid eval_result_id format")

    result = await db.execute(
        select(Trace)
        .where(Trace.eval_result_id == uuid_val)
        .order_by(Trace.step_order.asc())
    )
    traces = result.scalars().all()
    
    return [
        {
            "id": str(t.id),
            "step_name": t.step_name,
            "step_order": t.step_order,
            "input_payload": t.input_payload,
            "output_payload": t.output_payload,
            "error_message": t.error_message,
            "duration_ms": t.duration_ms,
            "created_at": t.created_at.isoformat()
        } for t in traces
    ]
