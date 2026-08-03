from fastapi import APIRouter
from app.services.dataset_loader import DatasetLoader, GoldenDatasetData
from app.config import settings

router = APIRouter()
dataset_loader = DatasetLoader(settings.GOLDEN_DATASET_DIR)

@router.get("/", response_model=list[GoldenDatasetData])
async def list_datasets():
    return dataset_loader.load_all()

@router.get("/{feature_id}", response_model=list[GoldenDatasetData])
async def get_datasets_for_feature(feature_id: str):
    datasets = dataset_loader.load_all()
    return [d for d in datasets if d.feature_id == feature_id]
