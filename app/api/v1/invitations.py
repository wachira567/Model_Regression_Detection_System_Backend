from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
from datetime import datetime
import secrets

from app.db.session import get_db
from app.dependencies import require_role
from app.models.invitation import Invitation
from app.models.organization_user import OrganizationUser
from app.models.user import User
from app.config import settings

router = APIRouter()

class InviteRequest(BaseModel):
    email: str
    role: str = "member"

class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    token: str

class AcceptInviteRequest(BaseModel):
    token: str

@router.post("/", response_model=InviteResponse)
async def create_invitation(
    request: InviteRequest,
    user_info = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    _, org_id, _ = user_info
    
    # Check if user already in org
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    
    if existing_user:
        stmt2 = select(OrganizationUser).where(
            OrganizationUser.user_id == existing_user.id,
            OrganizationUser.organization_id == org_id
        )
        res2 = await db.execute(stmt2)
        if res2.scalars().first():
            raise HTTPException(status_code=400, detail="User is already in this organization")

    # Invalidate pending invites for this email + org
    stmt = select(Invitation).where(
        Invitation.email == request.email,
        Invitation.organization_id == org_id,
        Invitation.status == "pending"
    )
    res = await db.execute(stmt)
    pending = res.scalars().all()
    for p in pending:
        p.status = "expired"
        
    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        email=request.email,
        organization_id=org_id,
        role=request.role,
        token=token
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    
    # Normally we would send an email here via Resend
    
    return {
        "id": invitation.id,
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation.status,
        "token": invitation.token
    }

@router.get("/", response_model=List[InviteResponse])
async def list_invitations(
    user_info = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    _, org_id, _ = user_info
    stmt = select(Invitation).where(
        Invitation.organization_id == org_id,
        Invitation.status == "pending"
    )
    result = await db.execute(stmt)
    invites = result.scalars().all()
    
    return [
        {
            "id": i.id,
            "email": i.email,
            "role": i.role,
            "status": i.status,
            "token": i.token
        } for i in invites
    ]

@router.post("/accept")
async def accept_invitation(
    request: AcceptInviteRequest,
    user_info = Depends(require_role("member")), # Needs any valid logged in user (new or existing)
    db: AsyncSession = Depends(get_db)
):
    user, current_org_id, _ = user_info
    
    stmt = select(Invitation).where(Invitation.token == request.token)
    res = await db.execute(stmt)
    invitation = res.scalars().first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
        
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Invitation is no longer valid")
        
    if invitation.expires_at < datetime.utcnow():
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")
        
    if user.email != invitation.email:
        raise HTTPException(status_code=403, detail="Invitation was sent to a different email address")
        
    # Check if already in org
    stmt = select(OrganizationUser).where(
        OrganizationUser.user_id == user.id,
        OrganizationUser.organization_id == invitation.organization_id
    )
    res = await db.execute(stmt)
    if res.scalars().first():
        invitation.status = "accepted"
        await db.commit()
        return {"message": "Already a member"}
        
    # Add user to org
    org_user = OrganizationUser(
        organization_id=invitation.organization_id,
        user_id=user.id,
        role=invitation.role
    )
    db.add(org_user)
    
    invitation.status = "accepted"
    await db.commit()
    
    return {"message": "Invitation accepted successfully", "new_org_id": invitation.organization_id}
