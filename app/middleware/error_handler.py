import uuid
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

def add_error_handler_middleware(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.error("Unhandled exception", exc_info=exc, request_id=request_id, path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id}
        )
