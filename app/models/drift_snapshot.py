import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class DriftSnapshot(Base):
    __tablename__ = "drift_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(String, nullable=False, index=True)
    
    rolling_avg_accuracy = Column(Float, nullable=False)
    rolling_avg_relevance = Column(Float, nullable=False)
    rolling_avg_latency_ms = Column(Float, nullable=False)
    
    window_size = Column(Integer, nullable=False)
    drift_detected = Column(Boolean, nullable=False, default=False)
    drift_type = Column(String, nullable=False, default="none") # none | warning | critical
    
    window_run_ids = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
