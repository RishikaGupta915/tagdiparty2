from typing import Optional
from pydantic import BaseModel


class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config_json: str = "{}"
