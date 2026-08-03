from fastapi import APIRouter
from app.api.v1 import api_router
from app.api.webhooks import github

router = APIRouter()
router.include_router(api_router, prefix="/api/v1")
router.include_router(github.router, prefix="/webhooks", tags=["webhooks"])
