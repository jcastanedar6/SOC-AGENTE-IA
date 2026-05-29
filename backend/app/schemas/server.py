from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ServerCreate(BaseModel):
    hostname: str
    ip_address: str
    role: Optional[str] = None
    os: Optional[str] = None
    services: list[str] = []


class ServerUpdate(BaseModel):
    status: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    services: Optional[list[str]] = None


class ServerOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    hostname: str
    ip_address: str
    role: Optional[str]
    os: Optional[str]
    status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    services: list[str]
    last_seen: datetime
    created_at: datetime
