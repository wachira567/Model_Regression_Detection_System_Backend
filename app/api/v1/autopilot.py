from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.db.session import get_db
from app.models.routing_decision import RoutingDecision
from app.services.cost_autopilot import CostAutopilot

router = APIRouter(prefix="/autopilot", tags=["Autopilot"])

class RouteRequest(BaseModel):
    feature_id: str
    prompt: str
    fallback_model: str = "gpt-4o"

@router.post("/route")
async def route_prompt(
    request: RouteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Route a prompt to the most cost-effective model based on its complexity.
    """
    autopilot = CostAutopilot(db)
    result = await autopilot.route_request(
        feature_id=request.feature_id,
        prompt=request.prompt,
        fallback_model=request.fallback_model
    )
    return result

@router.get("/stats")
async def get_autopilot_stats(db: AsyncSession = Depends(get_db)):
    """
    Get aggregate stats for the Cost Pilot dashboard.
    """
    # Total savings
    total_savings_query = await db.execute(select(func.sum(RoutingDecision.cost_saved_usd)))
    total_savings = total_savings_query.scalar() or 0.0
    
    # Total requests
    total_reqs_query = await db.execute(select(func.count(RoutingDecision.id)))
    total_requests = total_reqs_query.scalar() or 0
    
    # Model distribution
    distribution_query = await db.execute(
        select(RoutingDecision.routed_model, func.count(RoutingDecision.id))
        .group_by(RoutingDecision.routed_model)
    )
    distribution = {row[0]: row[1] for row in distribution_query.all()}
    
    # Recent decisions
    recent_query = await db.execute(
        select(RoutingDecision)
        .order_by(RoutingDecision.created_at.desc())
        .limit(10)
    )
    recent = recent_query.scalars().all()
    
    return {
        "total_savings_usd": total_savings,
        "total_requests": total_requests,
        "model_distribution": distribution,
        "recent_decisions": [
            {
                "id": str(d.id),
                "feature_id": d.feature_id,
                "complexity": d.complexity_score,
                "routed_model": d.routed_model,
                "savings": d.cost_saved_usd,
                "created_at": d.created_at.isoformat()
            } for d in recent
        ]
    }
