import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base

class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_config_id = Column(UUID(as_uuid=True), ForeignKey("prompt_configs.id"), nullable=False, index=True)
    dataset_version = Column(String, nullable=False)
    trigger_type = Column(String, nullable=False) # manual | ci | scheduled
    status = Column(String, nullable=False, default="pending") # pending | running | completed | failed
    
    overall_accuracy = Column(Float, nullable=True)
    avg_relevance_score = Column(Float, nullable=True)
    avg_latency_ms = Column(Float, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    estimated_cost_usd = Column(Float, nullable=True)
    
    total_cases = Column(Integer, nullable=True)
    passed_cases = Column(Integer, nullable=True)
    failed_cases = Column(Integer, nullable=True)
    regressions = Column(Integer, nullable=True)
    improvements = Column(Integer, nullable=True)
    
    comparison_baseline_id = Column(UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=True)
    summary_json = Column(JSONB, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    error_message = Column(String, nullable=True)
    report_url = Column(String, nullable=True)
    git_sha = Column(String, nullable=True)
    pr_number = Column(String, nullable=True)

    # Relationships
    prompt_config = relationship("PromptConfig")
    results = relationship("EvalResult", back_populates="eval_run", cascade="all, delete-orphan")
