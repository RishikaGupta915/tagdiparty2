import os
from sqlalchemy import Table
from app.db.session import (
    engine_primary,
    engine_alerts,
    engine_dashboards,
    SessionLocalPrimary,
)
from app.models.base import Base
from app.models.demo import User, Transaction, LoginEvent
from app.models.alerts import Metric, Event, AlertHistory, AnomalyHistory
from app.models.sentinel import ScanHistory
from app.models.dashboard import Dashboard
from app.models.ingestion import DataCenter, IngestionRun, SchemaRegistry
from app.models.analytics import DailyTransactionMetric
from app.models.archive import TransactionArchive, LoginEventArchive


def _ensure_sqlite_dir(database_url: str) -> None:
    if database_url.startswith("sqlite"):
        path = database_url.replace("sqlite:///", "")
        if path.startswith("./"):
            path = path[2:]
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)


def init_db(database_url: str) -> None:
    _ensure_sqlite_dir(database_url)

    primary_tables = [
        Base.metadata.tables["users"],
        Base.metadata.tables["transactions"],
        Base.metadata.tables["login_events"],
        Base.metadata.tables["transactions_archive"],
        Base.metadata.tables["login_events_archive"],
        Base.metadata.tables["daily_transaction_metrics"],
        Base.metadata.tables["scan_history"],
        Base.metadata.tables["data_centers"],
        Base.metadata.tables["ingestion_runs"],
        Base.metadata.tables["schema_registry"],
    ]
    alerts_tables = [
        Base.metadata.tables["metrics"],
        Base.metadata.tables["events"],
        Base.metadata.tables["alert_history"],
        Base.metadata.tables["anomaly_history"],
    ]
    dashboards_tables = [
        Base.metadata.tables["dashboards"],
    ]

    Base.metadata.create_all(bind=engine_primary, tables=primary_tables)
    Base.metadata.create_all(bind=engine_alerts, tables=alerts_tables)
    Base.metadata.create_all(bind=engine_dashboards, tables=dashboards_tables)

    _seed_demo_data()
    _seed_data_centers()


def _seed_demo_data() -> None:
    """Insert demo data if the users table is empty."""
    db = SessionLocalPrimary()
    try:
        from sqlalchemy import select
        existing = db.execute(select(User)).first()
        if existing:
            return  # already seeded

        u1 = User(name="Ava Chen", email="ava.chen@example.com", role="analyst")
        u2 = User(name="Jordan Miles", email="jordan.miles@example.com", role="admin")
        db.add_all([u1, u2])
        db.flush()

        t1 = Transaction(user_id=u1.id, amount=1200.50, currency="USD", status="completed")
        t2 = Transaction(user_id=u2.id, amount=340.00, currency="USD", status="flagged")
        db.add_all([t1, t2])

        l1 = LoginEvent(user_id=u1.id, ip_address="10.0.0.1", success=1, event_metadata='{"browser":"Chrome"}')
        l2 = LoginEvent(user_id=u2.id, ip_address="192.168.1.100", success=0, event_metadata='{"browser":"Firefox"}')
        db.add_all([l1, l2])

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _seed_data_centers() -> None:
    """Insert demo data centers if empty."""
    db = SessionLocalPrimary()
    try:
        from sqlalchemy import select
        existing = db.execute(select(DataCenter)).first()
        if existing:
            return
        defaults = [
            DataCenter(name="dc-west", status="healthy"),
            DataCenter(name="dc-east", status="healthy"),
            DataCenter(name="dc-eu", status="degraded"),
        ]
        db.add_all(defaults)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
