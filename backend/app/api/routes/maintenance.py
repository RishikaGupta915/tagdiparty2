from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import APIResponse
from app.schemas.maintenance import MaintenanceArchiveRequest, MaintenanceRefreshRequest
from app.services.maintenance.archive import (
    archive_login_events,
    archive_transactions,
    refresh_daily_transaction_metrics,
)

router = APIRouter(prefix="/api/v1/maintenance")


@router.post("/refresh-metrics", response_model=APIResponse)
def refresh_metrics(payload: MaintenanceRefreshRequest, db: Session = Depends(get_db)) -> APIResponse:
    count = refresh_daily_transaction_metrics(db, payload.start_date, payload.end_date)
    return APIResponse(success=True, data={"updated": count})


@router.post("/archive", response_model=APIResponse)
def archive(payload: MaintenanceArchiveRequest, db: Session = Depends(get_db)) -> APIResponse:
    tx_count = archive_transactions(db, payload.before_date)
    le_count = archive_login_events(db, payload.before_date)
    return APIResponse(success=True, data={"transactions": tx_count, "login_events": le_count})
