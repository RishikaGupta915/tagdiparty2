from typing import Any, Dict, List
from pydantic import BaseModel


class ScanSummary(BaseModel):
    scan_id: str
    domain: str
    status: str
    risk_score: int
    findings: List[Dict[str, Any]]
    narrative: str
