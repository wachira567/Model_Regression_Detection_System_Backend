from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
from jose import jwt

from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_user import OrganizationUser
from app.config import settings

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    token: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    organization_id: str

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7) # 7 day session
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.API_SECRET_KEY.get_secret_value(), algorithm="HS256")
    return encoded_jwt

@router.post("/google", response_model=AuthResponse)
async def google_login(request: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Verify Google token (if using a specific client ID, pass audience=CLIENT_ID)
        # We don't have the client ID here yet, so we verify without audience check or pass it via env
        # For full security, we should pass the expected audience.
        idinfo = id_token.verify_oauth2_token(request.token, requests.Request())
        
        email = idinfo.get("email")
        google_id = idinfo.get("sub")
        name = idinfo.get("name")
        
        if not email:
            raise HTTPException(status_code=400, detail="Google token does not contain email")
            
        # 1. Find or create user
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            user = User(email=email, google_id=google_id, name=name)
            db.add(user)
            await db.flush() # get user.id
            
            # 2. Auto-create personal organization for new user
            org = Organization(name=f"{name}'s Workspace")
            db.add(org)
            await db.flush() # get org.id
            
            # 3. Map user to org
            org_user = OrganizationUser(organization_id=org.id, user_id=user.id, role="owner")
            db.add(org_user)
            await db.commit()
            
            org_id = org.id
        else:
            # User exists, get their default organization
            stmt = select(OrganizationUser).where(OrganizationUser.user_id == user.id).limit(1)
            result = await db.execute(stmt)
            org_user = result.scalars().first()
            if not org_user:
                # Should not happen, but fallback
                org = Organization(name=f"{user.name or 'User'}'s Workspace")
                db.add(org)
                await db.flush()
                org_user = OrganizationUser(organization_id=org.id, user_id=user.id, role="owner")
                db.add(org_user)
                await db.commit()
            
            org_id = org_user.organization_id
            
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": user.id, "org_id": org_id, "email": user.email}
        )
        
        return AuthResponse(
            access_token=access_token,
            user_id=user.id,
            organization_id=org_id
        )
            
    except ValueError:
        # Invalid token
        raise HTTPException(status_code=401, detail="Invalid Google token")
