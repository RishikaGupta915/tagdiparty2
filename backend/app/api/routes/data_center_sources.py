from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.ingestion import DataCenter, DataCenterSource
from app.schemas.common import APIResponse
from app.schemas.data_center import DataCenterSourceCreate, DataCenterSourceUpdate

router = APIRouter()


@router.get("/api/v1/data-centers/{data_center_id}/sources", response_model=APIResponse)
def list_sources(data_center_id: int, db: Session = Depends(get_db)) -> APIResponse:
    dc = db.get(DataCenter, data_center_id)
    if dc is None:
        raise HTTPException(status_code=404, detail="Data center not found")
    sources = list(
        db.execute(select(DataCenterSource).where(DataCenterSource.data_center_id == data_center_id)).scalars()
    )
    data = [
        {
            "id": s.id,
            "data_center_id": s.data_center_id,
            "type": s.source_type,
            "status": s.status,
            "config_json": s.config_json,
            "last_sync": str(s.last_sync) if s.last_sync else None,
            "last_error": s.last_error,
            "cursor_json": s.cursor_json,
        }
        for s in sources
    ]
    return APIResponse(success=True, data={"sources": data})


@router.post("/api/v1/data-centers/{data_center_id}/sources", response_model=APIResponse)
def create_source(
    data_center_id: int,
    payload: DataCenterSourceCreate,
    db: Session = Depends(get_db),
) -> APIResponse:
    dc = db.get(DataCenter, data_center_id)
    if dc is None:
        raise HTTPException(status_code=404, detail="Data center not found")
    source = DataCenterSource(
        data_center_id=data_center_id,
        source_type=payload.source_type,
        config_json=payload.config_json,
        status=payload.status or "active",
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return APIResponse(success=True, data={"source_id": source.id})


@router.put("/api/v1/sources/{source_id}", response_model=APIResponse)
def update_source(source_id: int, payload: DataCenterSourceUpdate, db: Session = Depends(get_db)) -> APIResponse:
    source = db.get(DataCenterSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if payload.config_json is not None:
        source.config_json = payload.config_json
    if payload.status is not None:
        source.status = payload.status
    db.commit()
    db.refresh(source)
    return APIResponse(success=True, data={"source_id": source.id})
