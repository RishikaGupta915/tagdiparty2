from typing import Optional
from sqlalchemy.orm import Session
from app.models.alerts import Event


def ingest_event(db: Session, event_type: str, source: str, payload: str) -> Event:
    record = Event(event_type=event_type, source=source, payload=payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def evaluate_metrics(db: Session, metric_name: Optional[str] = None) -> None:
    return None
