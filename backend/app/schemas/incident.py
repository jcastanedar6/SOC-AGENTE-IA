from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "low"
    attack_type: Optional[str] = None
    affected_servers: list[str] = []
    source_ips: list[str] = []
    event_ids: list[int] = []


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None


class IncidentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    description: Optional[str]
    severity: str
    status: str
    attack_type: Optional[str]
    affected_servers: list[str]
    source_ips: list[str]
    event_ids: list[int]
    recommendation: Optional[str]
    llm_analysis: Optional[str]
    notified: str
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
