import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class Trace(Base):
    __tablename__ = "traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eval_result_id = Column(UUID(as_uuid=True), ForeignKey("eval_results.id", ondelete="CASCADE"), index=True, nullable=False)
    
    step_name = Column(String, nullable=False) # e.g. "Context Retrieval", "LLM Generation", "Parsing"
    step_order = Column(Float, nullable=False) # To sort steps chronologically
    
    input_payload = Column(JSONB, nullable=True)
    output_payload = Column(JSONB, nullable=True)
    
    error_message = Column(String, nullable=True)
    duration_ms = Column(Float, nullable=False, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
