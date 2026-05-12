from datetime import datetime
from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    service_name: str
    team: str
    environment: str
    criticality: str


class MetricCreate(BaseModel):
    service_name: str
    timestamp: datetime
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    response_time_ms: int = Field(ge=0)
    request_count: int = Field(ge=0)
    error_rate: float = Field(ge=0, le=100)


class IncidentCreate(BaseModel):
    service_name: str
    timestamp: datetime
    severity: str
    incident_type: str
    duration_minutes: int = Field(ge=0)
    resolved: bool