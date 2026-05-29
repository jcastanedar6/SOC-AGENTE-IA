from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional


class EventCreate(BaseModel):
    event_type: str
    source_ip: Optional[str] = None
    target_server: Optional[str] = None
    severity: str = "low"
    raw_data: Optional[dict[str, Any]] = None


class EventOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    event_type: str
    source_ip: Optional[str]
    target_server: Optional[str]
    severity: str
    raw_data: Optional[dict[str, Any]]
    processed: bool
    correlated: bool
    created_at: datetime


class EventStats(BaseModel):
    total: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
    unprocessed: int
