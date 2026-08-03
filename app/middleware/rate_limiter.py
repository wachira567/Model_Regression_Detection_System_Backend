import time
from typing import Callable, Dict, Tuple
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.ip_rates: Dict[str, list[float]] = {}
        self.api_key_rates: Dict[str, list[float]] = {}
        self.RATE_LIMIT = settings.RATE_LIMIT_PER_MINUTE
        self.EVAL_RATE_LIMIT = settings.RATE_LIMIT_EVAL_PER_HOUR
    
    def _check_rate(self, history: list[float], limit: int, window: int) -> bool:
        now = time.time()
        # Remove old entries outside the window
        history[:] = [t for t in history if now - t < window]
        if len(history) >= limit:
            return False
        history.append(now)
        return True

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        if client_ip not in self.ip_rates:
            self.ip_rates[client_ip] = []
        
        # General API limits (e.g. 60/min)
        if not self._check_rate(self.ip_rates[client_ip], self.RATE_LIMIT, 60):
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
            
        # Eval limits based on API key
        if request.url.path.startswith("/api/v1/eval-runs") and request.method == "POST":
            api_key = request.headers.get("X-API-Key", "anonymous")
            if api_key not in self.api_key_rates:
                self.api_key_rates[api_key] = []
            
            if not self._check_rate(self.api_key_rates[api_key], self.EVAL_RATE_LIMIT, 3600):
                return JSONResponse(status_code=429, content={"detail": "Eval trigger rate limit exceeded"})
                
        return await call_next(request)
