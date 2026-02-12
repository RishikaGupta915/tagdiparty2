from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import APIError, APIResponse
from app.schemas.query import QueryRequest, QueryResult
from app.services.nl2sql.engine import generate_sql, validate_sql, execute_sql

router = APIRouter()


@router.post("/api/v1/query", response_model=APIResponse)
def run_query(payload: QueryRequest, db: Session = Depends(get_db)) -> APIResponse:
    sql, questions = generate_sql(payload.query, payload.domain)
    if not sql:
        result = QueryResult(
            sql=None,
            rows=[],
            visualization={"type": "table"},
            insights=[],
            clarification_needed=True,
            clarification_questions=questions,
        )
        return APIResponse(success=True, data={"result": result.model_dump()})

    error = validate_sql(sql)
    if error:
        return APIResponse(success=False, error=APIError(code="INVALID_SQL", message=error))

    rows = execute_sql(db, sql)
    result = QueryResult(
        sql=sql,
        rows=rows,
        visualization={"type": "table", "rowCount": len(rows)},
        insights=[f"Returned {len(rows)} rows."],
        clarification_needed=False,
        clarification_questions=[],
    )
    return APIResponse(success=True, data={"result": result.model_dump()})
