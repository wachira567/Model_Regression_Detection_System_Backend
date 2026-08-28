import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class SemanticCache(Base):
    __tablename__ = "semantic_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False, default="default_org")
    feature_id = Column(String, index=True, nullable=False)
    
    prompt_hash = Column(String, index=True, nullable=False, unique=True)
    prompt_text = Column(String, nullable=False)
    
    cached_response = Column(JSONB, nullable=False)
    
    hit_count = Column(Integer, default=0, nullable=False)
    
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
