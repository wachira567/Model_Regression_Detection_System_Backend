import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("experiment_variants.id", ondelete="CASCADE"), nullable=False)
    request_hash = Column(String, index=True, nullable=False)
    eval_run_id = Column(UUID(as_uuid=True), ForeignKey("eval_runs.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    experiment = relationship("Experiment", back_populates="assignments")
    variant = relationship("ExperimentVariant")
    eval_run = relationship("EvalRun")
