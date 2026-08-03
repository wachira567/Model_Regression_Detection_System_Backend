import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base

class EvalResult(Base):
    __tablename__ = "eval_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eval_run_id = Column(UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=False, index=True)
    test_case_id = Column(String, nullable=False, index=True)
    
    input = Column(JSONB, nullable=False)
    expected_output = Column(JSONB, nullable=False)
    actual_output = Column(JSONB, nullable=True)
    
    category_match = Column(Boolean, nullable=False)
    relevance_score = Column(Float, nullable=True) # 1-5 from judge
    latency_ms = Column(Float, nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    
    status = Column(String, nullable=False) # pass | fail | error | timeout
    error_message = Column(String, nullable=True)
    judge_reasoning = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    eval_run = relationship("EvalRun", back_populates="results")
