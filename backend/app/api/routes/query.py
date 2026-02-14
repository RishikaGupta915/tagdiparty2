from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import APIError, APIResponse
from app.schemas.query import QueryRequest
from app.services.nl2sql.engine import run_query_pipeline

router = APIRouter()


@router.post("/api/v1/query", response_model=APIResponse)
def run_query(payload: QueryRequest, db: Session = Depends(get_db)) -> APIResponse:
    result = run_query_pipeline(db, payload.query, payload.domain)
    if result.get("error"):
        return APIResponse(success=False, error=APIError(code="INVALID_SQL", message=result["error"]))
    return APIResponse(success=True, data={"result": result})
