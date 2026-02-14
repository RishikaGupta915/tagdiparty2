from typing import Optional, Literal
from pydantic import BaseModel, Field


class IngestSyncRequest(BaseModel):
    data_center_id: int = Field(..., description="Target data center id")
    source_id: Optional[int] = Field(default=None, description="Optional source identifier")


class IngestUploadRequest(BaseModel):
    dataset: Literal["users", "transactions", "login_events"]
    data_center_id: Optional[int] = None
    source_id: Optional[str] = None
