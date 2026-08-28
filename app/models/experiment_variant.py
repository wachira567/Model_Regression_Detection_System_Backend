import uuid
from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class ExperimentVariant(Base):
    __tablename__ = "experiment_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    prompt_config_id = Column(UUID(as_uuid=True), ForeignKey("prompt_configs.id", ondelete="CASCADE"), nullable=False)
    traffic_percentage = Column(Integer, nullable=False, default=50)
    is_baseline = Column(Boolean, default=False, nullable=False)
    is_winner = Column(Boolean, nullable=True)

    experiment = relationship("Experiment", back_populates="variants")
    prompt_config = relationship("PromptConfig")
