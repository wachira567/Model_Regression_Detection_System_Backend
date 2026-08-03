from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exclude certain paths from auth like health check, webhooks, docs
        excluded_paths = ["/health", "/docs", "/openapi.json", "/api/v1/webhooks"]
        
        if any(request.url.path.startswith(path) for path in excluded_paths):
            return await call_next(request)

        # Skip auth if not configured in settings
        if not settings.API_SECRET_KEY:
            return await call_next(request)
            
        api_key = request.headers.get("Authorization")
        expected_key = f"Bearer {settings.API_SECRET_KEY.get_secret_value()}"
        
        if not api_key or api_key != expected_key:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API Key"})

        return await call_next(request)
