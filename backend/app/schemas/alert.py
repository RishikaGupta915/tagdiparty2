from typing import Optional
from pydantic import BaseModel, Field


class AlertEventRequest(BaseModel):
    event_type: str = Field(..., min_length=1)
    source: str = Field(default="api")
    payload: str = Field(default="{}")


class MetricRequest(BaseModel):
    name: str
    description: Optional[str] = None
    query: str
    window_minutes: int = 60
    threshold: float = 0.0
