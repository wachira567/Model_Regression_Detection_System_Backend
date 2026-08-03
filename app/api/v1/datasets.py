from fastapi import APIRouter, Query
from app.services.dataset_loader import DatasetLoader, GoldenDatasetData
from app.config import settings
from app.schemas.pagination import PaginatedResponse

router = APIRouter()
dataset_loader = DatasetLoader(settings.GOLDEN_DATASET_DIR)

@router.get("/")
async def list_datasets(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None)
):
    datasets = dataset_loader.load_all()
    
    if search:
        search_lower = search.lower()
        datasets = [d for d in datasets if search_lower in d.name.lower()]
    
    total = len(datasets)
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    
    paginated = datasets[offset:offset + size]
    
    return {
        "items": paginated,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{feature_id}")
async def get_datasets_for_feature(
    feature_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    datasets = dataset_loader.load_all()
    filtered = [d for d in datasets if d.feature_id == feature_id]
    
    total = len(filtered)
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    
    paginated = filtered[offset:offset + size]
    
    return {
        "items": paginated,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }
