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
from app.models.otp import OneTimePassword
from app.config import settings
import resend
import random
import string
import hashlib

router = APIRouter()
resend.api_key = settings.RESEND_API_KEY.get_secret_value() if settings.RESEND_API_KEY else "re_123"

class GoogleLoginRequest(BaseModel):
    token: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    organization_id: str
    is_superadmin: bool

class EmailOTPRequest(BaseModel):
    email: str

class EmailOTPVerify(BaseModel):
    email: str
    code: str

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7) # 7 day session
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.API_SECRET_KEY.get_secret_value(), algorithm="HS256")
    return encoded_jwt

def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

async def _provision_user_org(db: AsyncSession, email: str, name: str = None) -> tuple[User, str]:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        user = User(email=email, name=name)
        db.add(user)
        await db.flush() # get user.id
        
        org = Organization(name=f"{name or email}'s Workspace")
        db.add(org)
        await db.flush() # get org.id
        
        org_user = OrganizationUser(organization_id=org.id, user_id=user.id, role="owner")
        db.add(org_user)
        await db.commit()
        
        org_id = org.id
    else:
        stmt = select(OrganizationUser).where(OrganizationUser.user_id == user.id).limit(1)
        result = await db.execute(stmt)
        org_user = result.scalars().first()
        if not org_user:
            org = Organization(name=f"{user.name or email}'s Workspace")
            db.add(org)
            await db.flush()
            org_user = OrganizationUser(organization_id=org.id, user_id=user.id, role="owner")
            db.add(org_user)
            await db.commit()
        
        org_id = org_user.organization_id

    return user, org_id


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
            
        
        user, org_id = await _provision_user_org(db, email, name=name)
            
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": user.id, "org_id": org_id, "email": user.email}
        )
        
        return AuthResponse(
            access_token=access_token,
            user_id=user.id,
            organization_id=org_id,
            is_superadmin=user.is_superadmin
        )
            
    except ValueError:
        # Invalid token
        raise HTTPException(status_code=401, detail="Invalid Google token")

@router.post("/email/request")
async def request_otp(request: EmailOTPRequest, db: AsyncSession = Depends(get_db)):
    # Generate 6-digit code
    code = ''.join(random.choices(string.digits, k=6))
    hashed_code = _hash_otp(code)

    # Invalidate previous OTPs for this email
    # For simplicity, we just insert a new one and verify the latest
    
    otp = OneTimePassword(email=request.email, hashed_code=hashed_code)
    db.add(otp)
    await db.commit()

    try:
        resend.Emails.send({
            "from": "MRDS Auth <onboarding@resend.dev>",
            "to": request.email,
            "subject": "Your MRDS Login Code",
            "html": f"<p>Your secure login code is: <strong>{code}</strong></p><p>This code expires in 10 minutes.</p>"
        })
    except Exception as e:
        print("Resend Error:", e)
        # We don't fail hard so local dev still works if API key is invalid
        # But we log it.

    return {"message": "OTP sent"}

@router.post("/email/verify", response_model=AuthResponse)
async def verify_otp(request: EmailOTPVerify, db: AsyncSession = Depends(get_db)):
    # Find latest OTP for email
    stmt = select(OneTimePassword).where(
        OneTimePassword.email == request.email,
        OneTimePassword.expires_at > datetime.utcnow()
    ).order_by(OneTimePassword.created_at.desc())
    
    result = await db.execute(stmt)
    otp = result.scalars().first()

    if not otp:
        raise HTTPException(status_code=401, detail="OTP expired or not found")

    if otp.hashed_code != _hash_otp(request.code):
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    # OTP is valid, provision user
    user, org_id = await _provision_user_org(db, request.email)

    access_token = create_access_token(
        data={"sub": user.id, "org_id": org_id, "email": user.email}
    )
    
    return AuthResponse(
        access_token=access_token,
        user_id=user.id,
        organization_id=org_id,
        is_superadmin=user.is_superadmin
    )
