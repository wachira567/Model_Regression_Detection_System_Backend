from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.db.session import get_db
from app.models.semantic_cache import SemanticCache
from app.services.cache_engine import CacheEngine

router = APIRouter(prefix="/cache", tags=["Semantic Cache"])

class CacheCheckRequest(BaseModel):
    feature_id: str
    prompt: str

class CacheStoreRequest(BaseModel):
    feature_id: str
    prompt: str
    response: dict

@router.post("/check")
async def check_cache(request: CacheCheckRequest, db: AsyncSession = Depends(get_db)):
    engine = CacheEngine(db)
    cached = await engine.check_cache(request.feature_id, request.prompt)
    if cached:
        return {"status": "hit", "response": cached}
    return {"status": "miss"}

@router.post("/store")
async def store_cache(request: CacheStoreRequest, db: AsyncSession = Depends(get_db)):
    engine = CacheEngine(db)
    cache_id = await engine.store_cache(request.feature_id, request.prompt, request.response)
    return {"status": "success", "cache_id": cache_id}

@router.get("/stats")
async def get_cache_stats(db: AsyncSession = Depends(get_db)):
    # Total cached items
    total_query = await db.execute(select(func.count(SemanticCache.id)))
    total_items = total_query.scalar() or 0
    
    # Total hits
    hits_query = await db.execute(select(func.sum(SemanticCache.hit_count)))
    total_hits = hits_query.scalar() or 0
    
    # Recent active cached items
    recent_query = await db.execute(
        select(SemanticCache)
        .order_by(SemanticCache.last_accessed.desc())
        .limit(10)
    )
    recent = recent_query.scalars().all()
    
    return {
        "total_items": total_items,
        "total_hits": total_hits,
        "recent_items": [
            {
                "id": str(c.id),
                "feature_id": c.feature_id,
                "prompt_text": c.prompt_text,
                "hit_count": c.hit_count,
                "last_accessed": c.last_accessed.isoformat()
            } for c in recent
        ]
    }
