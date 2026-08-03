from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings

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

async def get_current_org_mock():
    """Mock dependency for local testing without tokens"""
    return "default_org"
