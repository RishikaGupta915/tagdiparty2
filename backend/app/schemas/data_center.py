from typing import Optional, Literal
from pydantic import BaseModel, Field


class DataCenterSourceCreate(BaseModel):
    source_type: Literal["csv", "db", "api"]
    config_json: str = Field(default="{}")
    status: Optional[str] = Field(default="active")


class DataCenterSourceUpdate(BaseModel):
    config_json: Optional[str] = None
    status: Optional[str] = None
