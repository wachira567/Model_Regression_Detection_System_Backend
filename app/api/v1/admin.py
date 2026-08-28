from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.dependencies import get_super_admin

router = APIRouter()

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    is_active: bool
    is_superadmin: bool
    created_at: datetime

class PaginatedUsersResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int

@router.get("/users", response_model=PaginatedUsersResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    admin: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * size
    
    # Base query
    stmt = select(User)
    count_stmt = select(func.count(User.id))
    
    # Optional search
    if search:
        search_filter = User.email.ilike(f"%{search}%") | User.name.ilike(f"%{search}%")
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)
        
    # Get total count
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # Get paginated items
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    pages = (total + size - 1) // size
    
    return PaginatedUsersResponse(
        items=[
            UserResponse(
                id=u.id,
                email=u.email,
                name=u.name,
                is_active=u.is_active,
                is_superadmin=u.is_superadmin,
                created_at=u.created_at
            ) for u in users
        ],
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/users/{user_id}/elevate")
async def elevate_user(
    user_id: str,
    admin: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db)
):
    # Prevent self-demotion or modifying self via this route
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own super admin status via this endpoint")
        
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_superadmin = not user.is_superadmin
    await db.commit()
    
    status = "elevated to Super Admin" if user.is_superadmin else "demoted to normal user"
    return {"message": f"User {user.email} successfully {status}"}

@router.get("/stats")
async def get_platform_stats(
    admin: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.eval_run import EvalRun
    from app.models.semantic_cache import SemanticCache
    from app.models.routing_decision import RoutingDecision
    
    users_query = await db.execute(select(func.count(User.id)))
    total_users = users_query.scalar() or 0
    
    evals_query = await db.execute(select(func.count(EvalRun.id)))
    total_evals = evals_query.scalar() or 0
    
    cache_query = await db.execute(select(func.count(SemanticCache.id)))
    total_cache_items = cache_query.scalar() or 0
    
    routing_query = await db.execute(select(func.count(RoutingDecision.id)))
    total_routing_decisions = routing_query.scalar() or 0
    
    return {
        "total_users": total_users,
        "total_eval_runs": total_evals,
        "total_cache_items": total_cache_items,
        "total_routing_decisions": total_routing_decisions
    }
