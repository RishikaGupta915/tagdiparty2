from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.ingestion import DataCenter, IngestionRun
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/api/v1/data-centers", response_model=APIResponse)
def list_data_centers(db: Session = Depends(get_db)) -> APIResponse:
    centers = list(db.execute(select(DataCenter)).scalars())
    last_runs = {}
    runs = list(
        db.execute(
            select(IngestionRun).order_by(IngestionRun.started_at.desc())
        ).scalars()
    )
    for run in runs:
        if run.data_center_id is not None and run.data_center_id not in last_runs:
            last_runs[run.data_center_id] = run

    data = []
    for c in centers:
        last_run = last_runs.get(c.id)
        data.append(
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "last_sync": str(c.last_sync) if c.last_sync else None,
                "latest_ingestion": {
                    "id": last_run.id,
                    "status": last_run.status,
                    "records_ingested": last_run.records_ingested,
                    "started_at": str(last_run.started_at),
                    "completed_at": str(last_run.completed_at) if last_run.completed_at else None,
                }
                if last_run
                else None,
            }
        )
    return APIResponse(success=True, data={"data_centers": data})
