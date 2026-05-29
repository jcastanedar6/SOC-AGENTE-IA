from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="low", index=True)
    status = Column(String(20), default="open", index=True)
    attack_type = Column(String(100), nullable=True)
    affected_servers = Column(JSON, default=list)
    source_ips = Column(JSON, default=list)
    event_ids = Column(JSON, default=list)
    recommendation = Column(Text, nullable=True)
    llm_analysis = Column(Text, nullable=True)
    notified = Column(String(1), default="N")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
