import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class ProductionLog(Base):
    __tablename__ = "production_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False, default="default_org")
    feature_id = Column(String, index=True, nullable=False)
    prompt_config_id = Column(UUID(as_uuid=True), ForeignKey("prompt_configs.id", ondelete="SET NULL"), nullable=True)
    
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=False)
    
    latency_ms = Column(Float, nullable=True)
    user_feedback_score = Column(Integer, nullable=True) # e.g. 1 (thumbs up), -1 (thumbs down)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
