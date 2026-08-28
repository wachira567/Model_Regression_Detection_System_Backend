import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class RoutingDecision(Base):
    __tablename__ = "routing_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False, default="default_org")
    feature_id = Column(String, index=True, nullable=False)
    
    input_hash = Column(String, index=True, nullable=False)
    complexity_score = Column(Float, nullable=False)
    routed_model = Column(String, nullable=False)
    
    cost_saved_usd = Column(Float, nullable=False, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
