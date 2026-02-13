from pydantic import BaseModel
from typing import Optional


class MaintenanceRefreshRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class MaintenanceArchiveRequest(BaseModel):
    before_date: str
