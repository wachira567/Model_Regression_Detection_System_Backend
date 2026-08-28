from fastapi import APIRouter, Query, Depends, UploadFile, File, HTTPException
import json
import os
from app.services.dataset_loader import DatasetLoader, GoldenDatasetData
from app.config import settings
from app.schemas.pagination import PaginatedResponse
from app.db.session import get_db

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

@router.post("/{feature_id}/bootstrap")
async def bootstrap_dataset(
    feature_id: str,
    days_back: int = 7,
    max_cases: int = 50,
    db = Depends(get_db)
):
    from app.services.dataset_bootstrap_engine import DatasetBootstrapEngine
    engine = DatasetBootstrapEngine(db)
    result = await engine.bootstrap_from_logs(feature_id, days_back, max_cases)
    return result

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
        
    if "feature_id" not in data or "dataset_id" not in data:
        raise HTTPException(status_code=400, detail="Dataset must contain feature_id and dataset_id")
        
    os.makedirs(settings.GOLDEN_DATASET_DIR, exist_ok=True)
    file_path = os.path.join(settings.GOLDEN_DATASET_DIR, file.filename)
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
        
    return {"message": "Dataset uploaded successfully", "filename": file.filename}
