import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base

class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PrimaryMetric(str, enum.Enum):
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    LATENCY = "latency"

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False, default="default_org")
    name = Column(String, nullable=False)
    feature_id = Column(String, index=True, nullable=False)
    status = Column(String, default=ExperimentStatus.DRAFT.value, nullable=False)
    primary_metric = Column(String, default=PrimaryMetric.ACCURACY.value, nullable=False)
    target_sample_size = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    variants = relationship("ExperimentVariant", back_populates="experiment", cascade="all, delete-orphan")
    assignments = relationship("ExperimentAssignment", back_populates="experiment", cascade="all, delete-orphan")
