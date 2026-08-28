import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False, default="default_org")
    name = Column(String, nullable=False)
    feature_id = Column(String, index=True, nullable=False)
    
    is_enabled = Column(Boolean, default=True, nullable=False)
    rollout_percentage = Column(Integer, default=0, nullable=False) # 0 to 100
    
    baseline_config_id = Column(UUID(as_uuid=True), ForeignKey("prompt_configs.id", ondelete="CASCADE"), nullable=False)
    experimental_config_id = Column(UUID(as_uuid=True), ForeignKey("prompt_configs.id", ondelete="CASCADE"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
