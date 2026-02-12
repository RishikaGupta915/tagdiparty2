from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import APIResponse

router = APIRouter(prefix="/api/db-test")


@router.get("/health", response_model=APIResponse)
def db_health(db: Session = Depends(get_db)) -> APIResponse:
    db.execute(text("SELECT 1"))
    return APIResponse(success=True, data={"status": "ok"})


@router.get("/tables", response_model=APIResponse)
def db_tables(db: Session = Depends(get_db)) -> APIResponse:
    inspector = inspect(db.bind)
    return APIResponse(success=True, data={"tables": inspector.get_table_names()})


@router.get("/schema", response_model=APIResponse)
def db_schema(db: Session = Depends(get_db)) -> APIResponse:
    inspector = inspect(db.bind)
    schema = {}
    for table in inspector.get_table_names():
        columns = inspector.get_columns(table)
        schema[table] = [
            {**column, "type": str(column.get("type"))}
            for column in columns
        ]
    return APIResponse(success=True, data={"schema": schema})
