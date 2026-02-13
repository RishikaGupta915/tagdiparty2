import csv
from io import StringIO
from typing import Iterable, Tuple
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.demo import User, Transaction, LoginEvent
from app.models.ingestion import DataCenter, IngestionRun


ALLOWED_DATASETS = {"users", "transactions", "login_events"}


def create_ingestion_run(
    db: Session,
    data_center_id: int | None,
    source_id: str | None,
    status: str = "running",
) -> IngestionRun:
    run = IngestionRun(
        data_center_id=data_center_id,
        source_id=source_id or "manual",
        status=status,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finalize_ingestion_run(
    db: Session,
    run: IngestionRun,
    status: str,
    records_ingested: int,
    errors: str = "",
) -> None:
    run.status = status
    run.records_ingested = records_ingested
    run.errors = errors
    run.completed_at = func.now()
    db.commit()


def _parse_csv(content: str) -> Iterable[dict]:
    reader = csv.DictReader(StringIO(content))
    if reader.fieldnames is None:
        return []
    return list(reader)


def ingest_csv(
    db: Session,
    dataset: str,
    content: str,
) -> Tuple[int, str]:
    if dataset not in ALLOWED_DATASETS:
        return 0, f"Unsupported dataset: {dataset}"

    rows = _parse_csv(content)
    if not rows:
        return 0, "No rows found in CSV"

    try:
        if dataset == "users":
            records = []
            for row in rows:
                name = (row.get("name") or "").strip()
                email = (row.get("email") or "").strip()
                role = (row.get("role") or "analyst").strip()
                if not name or not email:
                    return 0, "Users CSV must include name and email"
                records.append(User(name=name, email=email, role=role))
            db.add_all(records)

        if dataset == "transactions":
            records = []
            for row in rows:
                user_id = int(row.get("user_id") or 0)
                amount_raw = row.get("amount")
                amount = float(amount_raw) if amount_raw not in (None, "") else None
                currency = (row.get("currency") or "USD").strip()
                status = (row.get("status") or "completed").strip()
                if user_id <= 0 or amount is None:
                    return 0, "Transactions CSV must include user_id and amount"
                records.append(
                    Transaction(
                        user_id=user_id,
                        amount=float(amount),
                        currency=currency,
                        status=status,
                    )
                )
            db.add_all(records)

        if dataset == "login_events":
            records = []
            for row in rows:
                user_id = int(row.get("user_id") or 0)
                ip_address = (row.get("ip_address") or "").strip()
                success = int(row.get("success") or 1)
                metadata = (row.get("metadata") or row.get("event_metadata") or "{}").strip()
                if user_id <= 0 or not ip_address:
                    return 0, "Login events CSV must include user_id and ip_address"
                records.append(
                    LoginEvent(
                        user_id=user_id,
                        ip_address=ip_address,
                        success=success,
                        event_metadata=metadata,
                    )
                )
            db.add_all(records)

        db.commit()
        return len(rows), ""
    except (ValueError, SQLAlchemyError) as exc:
        db.rollback()
        return 0, str(exc)


def get_latest_ingestion_run(db: Session) -> IngestionRun | None:
    return db.execute(
        select(IngestionRun).order_by(IngestionRun.started_at.desc())
    ).scalars().first()


def touch_data_center(db: Session, data_center_id: int, status: str = "healthy") -> None:
    data_center = db.get(DataCenter, data_center_id)
    if data_center is None:
        return
    data_center.status = status
    data_center.last_sync = func.now()
    db.commit()
