from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.db.session import get_db, get_db_alerts, get_db_dashboards
from app.schemas.common import APIResponse

router = APIRouter(prefix="/api/db-test")


def _schema_payload(db: Session) -> dict:
    inspector = inspect(db.bind)
    schema = {}
    for table in inspector.get_table_names():
        columns = inspector.get_columns(table)
        schema[table] = [
            {**column, "type": str(column.get("type"))}
            for column in columns
        ]
    return schema


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
    return APIResponse(success=True, data={"schema": _schema_payload(db)})


@router.get("/alerts", response_model=APIResponse)
def db_alerts(db: Session = Depends(get_db_alerts)) -> APIResponse:
    db.execute(text("SELECT 1"))
    return APIResponse(success=True, data={"tables": inspect(db.bind).get_table_names(), "schema": _schema_payload(db)})


@router.get("/dashboards", response_model=APIResponse)
def db_dashboards(db: Session = Depends(get_db_dashboards)) -> APIResponse:
    db.execute(text("SELECT 1"))
    return APIResponse(success=True, data={"tables": inspect(db.bind).get_table_names(), "schema": _schema_payload(db)})
