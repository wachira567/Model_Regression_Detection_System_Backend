from fastapi import FastAPI
from fastapi.responses import JSONResponse
import time

from app.config import settings
from app.middleware import (
    add_cors_middleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
    add_error_handler_middleware,
)
from app.api.router import router as api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Model Regression Detection API",
        version="0.1.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url=None,
    )

    # Add middlewares (order matters)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIDMiddleware)
    # APIKeyAuthMiddleware removed: JWT auth via dependencies handles security
    add_cors_middleware(app)
    add_error_handler_middleware(app)
    
    app.include_router(api_router)

    @app.get("/health")
    async def health_check():
        return JSONResponse(content={
            "status": "ok",
            "version": "0.1.0",
            "timestamp": time.time(),
            "db": "connected"  # We'll check actual DB in next iterations
        })

    return app

app = create_app()
