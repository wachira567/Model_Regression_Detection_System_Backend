from fastapi import APIRouter, Depends
from app.api.v1 import prompts, datasets, eval, eval_runs, reports, auth, admin, experiments, logs, autopilot, flags, traces
from app.dependencies import get_current_org

api_router = APIRouter()
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"], dependencies=[Depends(get_current_org)])
api_router.include_router(experiments.router, tags=["experiments"], dependencies=[Depends(get_current_org)])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"], dependencies=[Depends(get_current_org)])
api_router.include_router(eval.router, prefix="/eval", tags=["eval"], dependencies=[Depends(get_current_org)])
api_router.include_router(eval_runs.router, prefix="/eval-runs", tags=["eval-runs"], dependencies=[Depends(get_current_org)])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_org)])
api_router.include_router(logs.router, tags=["logs"], dependencies=[Depends(get_current_org)])
api_router.include_router(autopilot.router, dependencies=[Depends(get_current_org)])
api_router.include_router(flags.router, dependencies=[Depends(get_current_org)])
api_router.include_router(traces.router, dependencies=[Depends(get_current_org)])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
