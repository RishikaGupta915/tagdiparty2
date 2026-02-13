from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.alerts import Metric, AlertHistory, AnomalyHistory
from app.schemas.alert import MetricRequest
from app.schemas.common import APIResponse

router = APIRouter(prefix="/api/v1/alerts")


def _to_dict(model):
    data = model.__dict__.copy()
    data.pop("_sa_instance_state", None)
    return data


@router.get("/metrics", response_model=APIResponse)
def list_metrics(db: Session = Depends(get_db)) -> APIResponse:
    metrics = list(db.execute(select(Metric)).scalars())
    return APIResponse(success=True, data={"metrics": [_to_dict(m) for m in metrics]})


@router.post("/metrics", response_model=APIResponse)
def create_metric(payload: MetricRequest, db: Session = Depends(get_db)) -> APIResponse:
    metric = Metric(
        name=payload.name,
        description=payload.description or "",
        query=payload.query,
        window_minutes=payload.window_minutes,
        threshold=payload.threshold,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return APIResponse(success=True, data={"metric": _to_dict(metric)})


@router.put("/metrics/{metric_id}", response_model=APIResponse)
def update_metric(metric_id: int, payload: MetricRequest, db: Session = Depends(get_db)) -> APIResponse:
    metric = db.get(Metric, metric_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    metric.name = payload.name
    metric.description = payload.description or ""
    metric.query = payload.query
    metric.window_minutes = payload.window_minutes
    metric.threshold = payload.threshold
    db.commit()
    db.refresh(metric)
    return APIResponse(success=True, data={"metric": _to_dict(metric)})


@router.delete("/metrics/{metric_id}", response_model=APIResponse)
def delete_metric(metric_id: int, db: Session = Depends(get_db)) -> APIResponse:
    metric = db.get(Metric, metric_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    db.delete(metric)
    db.commit()
    return APIResponse(success=True, data={"deleted": True})


@router.get("/history", response_model=APIResponse)
def list_alert_history(db: Session = Depends(get_db)) -> APIResponse:
    rows = list(db.execute(select(AlertHistory)).scalars())
    return APIResponse(success=True, data={"history": [_to_dict(r) for r in rows]})


@router.get("/anomalies", response_model=APIResponse)
def list_anomaly_history(db: Session = Depends(get_db)) -> APIResponse:
    rows = list(db.execute(select(AnomalyHistory)).scalars())
    return APIResponse(success=True, data={"anomalies": [_to_dict(r) for r in rows]})
