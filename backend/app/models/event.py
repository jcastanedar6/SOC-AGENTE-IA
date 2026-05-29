from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.db.session import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    source_ip = Column(String(45), index=True)
    target_server = Column(String(100), index=True)
    severity = Column(String(20), default="low", index=True)
    raw_data = Column(JSON, nullable=True)
    processed = Column(Boolean, default=False, index=True)
    correlated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
