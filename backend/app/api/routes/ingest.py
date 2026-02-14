import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.ingestion import DataCenter, DataCenterSource
from app.schemas.common import APIResponse
from app.schemas.ingest import IngestSyncRequest
from app.services.ingestion.engine import (
    create_ingestion_run,
    finalize_ingestion_run,
    ingest_csv,
    get_latest_ingestion_run,
    touch_data_center,
)
from app.services.ingestion.sync import sync_source

router = APIRouter()


@router.post("/api/v1/ingest/upload", response_model=APIResponse)
async def ingest_upload(
    dataset: str = Form(...),
    file: UploadFile = File(...),
    data_center_id: int | None = Form(default=None),
    source_id: str | None = Form(default=None),
    mapping_json: str | None = Form(default=None),
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
    mapping = None
    if mapping_json:
        try:
            mapping = json.loads(mapping_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="mapping_json must be valid JSON")
    ingested, error = ingest_csv(db, dataset, content, mapping=mapping)
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
    query = db.query(DataCenterSource).filter(DataCenterSource.data_center_id == payload.data_center_id)
    if payload.source_id:
        query = query.filter(DataCenterSource.id == int(payload.source_id))
    sources = query.all()
    if not sources:
        raise HTTPException(status_code=404, detail="No sources configured for data center")
    results = []
    touch_data_center(db, payload.data_center_id, status="syncing")
    for source in sources:
        run = sync_source(db, source)
        results.append({"run_id": run.id, "status": run.status, "source_id": source.id})
    return APIResponse(success=True, data={"runs": results})


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
