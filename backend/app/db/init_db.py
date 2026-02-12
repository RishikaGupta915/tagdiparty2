import json
import os
from sqlalchemy import select
from app.db.session import engine, SessionLocal
from app.models.base import Base
from app.models.demo import User, Transaction, LoginEvent
from app.models.alerts import Metric, Event, AlertHistory, AnomalyHistory
from app.models.sentinel import ScanHistory
from app.models.dashboard import Dashboard


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
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        has_user = session.execute(select(User).limit(1)).scalar_one_or_none()
        if has_user is None:
            users = [
                User(name="Ava Chen", email="ava.chen@example.com", role="analyst"),
                User(name="Jordan Miles", email="jordan.miles@example.com", role="executive"),
            ]
            session.add_all(users)
            session.flush()
            transactions = [
                Transaction(user_id=users[0].id, amount=1200.50, status="completed"),
                Transaction(user_id=users[1].id, amount=4500.00, status="flagged"),
            ]
            login_events = [
                LoginEvent(user_id=users[0].id, ip_address="192.168.1.10", success=1, metadata=json.dumps({"device": "laptop"})),
                LoginEvent(user_id=users[1].id, ip_address="10.0.0.12", success=0, metadata=json.dumps({"reason": "mfa_failed"})),
            ]
            session.add_all(transactions + login_events)
            session.commit()
