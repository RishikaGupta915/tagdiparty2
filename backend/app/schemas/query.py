from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    domain: Optional[str] = None


class QueryResult(BaseModel):
    sql: Optional[str]
    rows: List[Dict[str, Any]]
    visualization: Dict[str, Any]
    insights: List[str]
    clarification_needed: bool
    clarification_questions: List[str]


class QueryResponse(BaseModel):
    result: QueryResult
