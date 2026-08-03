from fastapi import FastAPI
from fastapi.responses import JSONResponse
import time

from app.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title="Model Regression Detection API",
        version="0.1.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url=None,
    )

    @app.get("/health")
    async def health_check():
        return JSONResponse(content={
            "status": "ok",
            "version": "0.1.0",
            "timestamp": time.time()
        })

    return app

app = create_app()
