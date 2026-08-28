import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.semantic_cache import SemanticCache

class CacheEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _hash_prompt(self, feature_id: str, prompt: str) -> str:
        """Create a deterministic hash for a prompt string."""
        # Simple exact text hash for now. 
        # In production, we'd hash the vector embedding.
        normalized = prompt.strip().lower()
        content = f"{feature_id}::{normalized}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def check_cache(self, feature_id: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Check if we have a semantic hit for this prompt.
        """
        prompt_hash = self._hash_prompt(feature_id, prompt)
        
        result = await self.db.execute(
            select(SemanticCache).where(SemanticCache.prompt_hash == prompt_hash)
        )
        cache_entry = result.scalar_one_or_none()
        
        if cache_entry:
            # Update hit count and last accessed time
            cache_entry.hit_count += 1
            cache_entry.last_accessed = datetime.utcnow()
            await self.db.commit()
            
            return cache_entry.cached_response
            
        return None

    async def store_cache(self, feature_id: str, prompt: str, response: Dict[str, Any]) -> str:
        """
        Store a successful response in the semantic cache.
        """
        prompt_hash = self._hash_prompt(feature_id, prompt)
        
        # Check if exists to avoid unique constraint violations on concurrent requests
        result = await self.db.execute(
            select(SemanticCache).where(SemanticCache.prompt_hash == prompt_hash)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.cached_response = response
            existing.last_accessed = datetime.utcnow()
            await self.db.commit()
            return str(existing.id)
            
        new_entry = SemanticCache(
            feature_id=feature_id,
            prompt_hash=prompt_hash,
            prompt_text=prompt,
            cached_response=response,
            hit_count=0
        )
        self.db.add(new_entry)
        await self.db.commit()
        return str(new_entry.id)
