from fastapi import APIRouter
from app.api.v1 import prompts, datasets, eval, eval_runs, reports

api_router = APIRouter()
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(eval.router, prefix="/eval", tags=["eval"])
api_router.include_router(eval_runs.router, prefix="/eval-runs", tags=["eval-runs"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
