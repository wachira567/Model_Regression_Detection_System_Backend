from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.dependencies import get_current_user_and_role
from app.models.user import User

router = APIRouter()

class UserProfileUpdate(BaseModel):
    name: str

class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str | None
    is_superadmin: bool
    created_at: datetime
    role: str

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    user_info = Depends(get_current_user_and_role),
    db: AsyncSession = Depends(get_db)
):
    user, org_id, role = user_info
    
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_superadmin=user.is_superadmin,
        created_at=user.created_at,
        role=role
    )

@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    request: UserProfileUpdate,
    user_info = Depends(get_current_user_and_role),
    db: AsyncSession = Depends(get_db)
):
    user, org_id, role = user_info
    
    user.name = request.name
    await db.commit()
    await db.refresh(user)
    
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_superadmin=user.is_superadmin,
        created_at=user.created_at,
        role=role
    )
