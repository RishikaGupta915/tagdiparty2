from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.alert import AlertEventRequest
from app.schemas.common import APIResponse
from app.services.alerts.engine import ingest_event

router = APIRouter()


@router.post("/api/v1/alert", response_model=APIResponse)
def create_alert(payload: AlertEventRequest, db: Session = Depends(get_db)) -> APIResponse:
    record = ingest_event(db, payload.event_type, payload.source, payload.payload)
    return APIResponse(success=True, data={"event_id": record.id})
