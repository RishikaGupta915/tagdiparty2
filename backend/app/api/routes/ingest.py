from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.ingestion import DataCenter
from app.schemas.common import APIResponse
from app.schemas.ingest import IngestSyncRequest
from app.services.ingestion.engine import (
    create_ingestion_run,
    finalize_ingestion_run,
    ingest_csv,
    get_latest_ingestion_run,
    touch_data_center,
)

router = APIRouter()


@router.post("/api/v1/ingest/upload", response_model=APIResponse)
async def ingest_upload(
    dataset: str = Form(...),
    file: UploadFile = File(...),
    data_center_id: int | None = Form(default=None),
    source_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> APIResponse:
    if file.filename is None or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")

    if data_center_id is not None:
        dc = db.get(DataCenter, data_center_id)
        if dc is None:
            raise HTTPException(status_code=404, detail="Data center not found")

    run = create_ingestion_run(db, data_center_id, source_id, status="running")
    content = (await file.read()).decode("utf-8", errors="replace")
    ingested, error = ingest_csv(db, dataset, content)
    if error:
        finalize_ingestion_run(db, run, "failed", 0, error)
        raise HTTPException(status_code=400, detail=error)

    finalize_ingestion_run(db, run, "success", ingested, "")
    if data_center_id is not None:
        touch_data_center(db, data_center_id, status="healthy")
    return APIResponse(
        success=True,
        data={"ingested": ingested, "run_id": run.id},
    )


@router.post("/api/v1/ingest/sync", response_model=APIResponse)
def ingest_sync(payload: IngestSyncRequest, db: Session = Depends(get_db)) -> APIResponse:
    dc = db.get(DataCenter, payload.data_center_id)
    if dc is None:
        raise HTTPException(status_code=404, detail="Data center not found")

    run = create_ingestion_run(db, payload.data_center_id, payload.source_id, status="queued")
    touch_data_center(db, payload.data_center_id, status="syncing")
    return APIResponse(success=True, data={"run_id": run.id, "status": run.status})


@router.get("/api/v1/ingest/status", response_model=APIResponse)
def ingest_status(db: Session = Depends(get_db)) -> APIResponse:
    latest = get_latest_ingestion_run(db)
    if latest is None:
        return APIResponse(success=True, data={"latest": None})
    return APIResponse(
        success=True,
        data={
            "latest": {
                "id": latest.id,
                "data_center_id": latest.data_center_id,
                "source_id": latest.source_id,
                "status": latest.status,
                "records_ingested": latest.records_ingested,
                "errors": latest.errors,
                "started_at": str(latest.started_at),
                "completed_at": str(latest.completed_at) if latest.completed_at else None,
            }
        },
    )
