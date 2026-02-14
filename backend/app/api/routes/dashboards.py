import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db_dashboards
from app.models.dashboard import Dashboard
from app.schemas.common import APIResponse
from app.schemas.dashboard import DashboardCreate

router = APIRouter()


@router.get("/api/v1/dashboards", response_model=APIResponse)
def list_dashboards(db: Session = Depends(get_db_dashboards)) -> APIResponse:
    dashboards = list(db.execute(select(Dashboard)).scalars())
    data = []
    for d in dashboards:
        try:
            config = json.loads(d.config_json or "{}")
        except json.JSONDecodeError:
            config = {}
        data.append({"id": d.id, "name": d.name, "description": d.description, "config": config})
    return APIResponse(success=True, data={"dashboards": data})


@router.post("/api/v1/dashboards", response_model=APIResponse)
def create_dashboard(payload: DashboardCreate, db: Session = Depends(get_db_dashboards)) -> APIResponse:
    dashboard = Dashboard(
        name=payload.name,
        description=payload.description or "",
        config_json=payload.config_json or "{}",
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return APIResponse(success=True, data={"dashboardId": dashboard.id})


@router.get("/api/v1/dashboards/{dashboardId}", response_model=APIResponse)
def get_dashboard(dashboardId: int, db: Session = Depends(get_db_dashboards)) -> APIResponse:
    dashboard = db.get(Dashboard, dashboardId)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    try:
        config = json.loads(dashboard.config_json or "{}")
    except json.JSONDecodeError:
        config = {}
    return APIResponse(
        success=True,
        data={
            "id": dashboard.id,
            "name": dashboard.name,
            "description": dashboard.description,
            "config": config,
        },
    )
