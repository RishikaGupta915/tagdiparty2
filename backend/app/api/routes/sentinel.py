import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import APIError, APIResponse
from app.services.sentinel.engine import run_scan, list_history, get_history

router = APIRouter()


@router.get("/api/v1/sentinel/scan", response_model=APIResponse)
def sentinel_scan(domain: str = "general", db: Session = Depends(get_db)) -> APIResponse:
    result = run_scan(db, domain)
    return APIResponse(success=True, data=result)


@router.get("/api/v1/sentinel/scan/stream")
def sentinel_scan_stream(domain: str = "general", db: Session = Depends(get_db)) -> StreamingResponse:
    def event_stream():
        yield "event: status\ndata: {\"status\": \"started\"}\n\n"
        result = run_scan(db, domain)
        yield f"event: complete\ndata: {json.dumps(result)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/api/v1/sentinel/history", response_model=APIResponse)
def sentinel_history(db: Session = Depends(get_db)) -> APIResponse:
    history = list_history(db)
    data = [{"scan_id": h.scan_id, "domain": h.domain, "status": h.status, "risk_score": h.risk_score, "created_at": str(h.created_at)} for h in history]
    return APIResponse(success=True, data={"history": data})


@router.get("/api/v1/sentinel/history/{scan_id}", response_model=APIResponse)
def sentinel_history_detail(scan_id: str, db: Session = Depends(get_db)) -> APIResponse:
    record = get_history(db, scan_id)
    if record is None:
        return APIResponse(success=False, error=APIError(code="NOT_FOUND", message="Scan not found"))
    return APIResponse(success=True, data=json.loads(record.result_json))
