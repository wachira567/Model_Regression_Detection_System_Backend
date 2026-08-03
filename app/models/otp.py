import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime
from app.models.base import Base

def default_expiration():
    return datetime.utcnow() + timedelta(minutes=10)

class OneTimePassword(Base):
    __tablename__ = "one_time_passwords"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, index=True, nullable=False)
    hashed_code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, default=default_expiration, nullable=False)
