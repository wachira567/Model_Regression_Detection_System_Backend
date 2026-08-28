from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
from app.config import settings
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()

async def get_current_org(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verifies the custom JWT token and extracts the organization_id (org_id).
    """
    token = credentials.credentials
    try:
        # Verify the custom token using our API_SECRET_KEY
        payload = jwt.decode(
            token,
            settings.API_SECRET_KEY.get_secret_value(),
            algorithms=["HS256"],
        )

        org_id = payload.get("org_id")
        if not org_id:
            raise HTTPException(status_code=401, detail="Token missing organization_id")

        return org_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unable to parse authentication token: {str(e)}")



async def get_super_admin(credentials: HTTPAuthorizationCredentials = Security(security), db: AsyncSession = Depends(get_db)):
    """
    Verifies the JWT token and ensures the user is a superadmin.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.API_SECRET_KEY.get_secret_value(),
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing user_id")

        # Fetch user to check superadmin status
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user or not user.is_superadmin:
            raise HTTPException(status_code=403, detail="Forbidden: Super Admin access required")
        
        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=401, detail=f"Unable to parse authentication token: {str(e)}")

async def get_current_user_and_role(
    credentials: HTTPAuthorizationCredentials = Security(security), 
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the user and their role in the current organization.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.API_SECRET_KEY.get_secret_value(),
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        org_id = payload.get("org_id")
        
        if not user_id or not org_id:
            raise HTTPException(status_code=401, detail="Token missing user_id or org_id")

        from app.models.organization_user import OrganizationUser
        stmt = select(OrganizationUser).where(
            OrganizationUser.user_id == user_id,
            OrganizationUser.organization_id == org_id
        )
        result = await db.execute(stmt)
        org_user = result.scalars().first()

        if not org_user:
            raise HTTPException(status_code=403, detail="User does not belong to this organization")
            
        # Also get the user object
        stmt_user = select(User).where(User.id == user_id)
        result_user = await db.execute(stmt_user)
        user = result_user.scalars().first()

        return user, org_id, org_user.role

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(min_role: str):
    """
    Dependency to enforce RBAC. Roles hierarchy: owner > admin > member
    """
    def role_checker(user_info = Depends(get_current_user_and_role)):
        user, org_id, role = user_info
        
        roles_hierarchy = {"owner": 3, "admin": 2, "member": 1}
        
        user_level = roles_hierarchy.get(role, 0)
        required_level = roles_hierarchy.get(min_role, 1)
        
        if user_level < required_level:
            raise HTTPException(status_code=403, detail=f"Requires {min_role} role. You have {role} role.")
            
        return user, org_id, role
        
    return role_checker
