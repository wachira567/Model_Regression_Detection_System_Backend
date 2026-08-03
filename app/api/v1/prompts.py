from fastapi import APIRouter, Query
from app.services.prompt_loader import PromptLoader, PromptConfigData
from app.config import settings
from app.schemas.pagination import PaginatedResponse

router = APIRouter()
prompt_loader = PromptLoader(settings.PROMPTS_DIR)

@router.get("/")
async def list_prompts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None)
):
    prompts = prompt_loader.load_all()
    
    if search:
        search_lower = search.lower()
        prompts = [p for p in prompts if search_lower in p.feature_id.lower() or search_lower in p.model.lower()]
    
    total = len(prompts)
    pages = (total + size - 1) // size
    offset = (page - 1) * size
    
    paginated = prompts[offset:offset + size]
    
    return {
        "items": paginated,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{feature_id}")
async def get_prompts_for_feature(
    feature_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    prompts = prompt_loader.load_all()
    filtered = [p for p in prompts if p.feature_id == feature_id]
    
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
