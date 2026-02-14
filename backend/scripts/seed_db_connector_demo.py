import json
import os
import sqlite3
import sys
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import select  # noqa: E402
from app.db.session import SessionLocalPrimary  # noqa: E402
from app.models.ingestion import DataCenter, DataCenterSource  # noqa: E402


def _init_source_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users_src (
            id INTEGER PRIMARY KEY,
            full_name TEXT,
            email_address TEXT,
            role_name TEXT,
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions_src (
            id INTEGER PRIMARY KEY,
            user_ref INTEGER,
            amount_usd REAL,
            status TEXT,
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS login_events_src (
            id INTEGER PRIMARY KEY,
            user_ref INTEGER,
            ip TEXT,
            success INTEGER,
            metadata TEXT,
            created_at TEXT
        )
        """
    )
    now = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO users_src (full_name, email_address, role_name, created_at) VALUES (?, ?, ?, ?)",
        ("DB Demo User", f"db_demo_{now}@example.com", "analyst", now),
    )
    cur.execute(
        "INSERT INTO transactions_src (user_ref, amount_usd, status, created_at) VALUES (?, ?, ?, ?)",
        (1, 250.0, "completed", now),
    )
    cur.execute(
        "INSERT INTO login_events_src (user_ref, ip, success, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
        (1, "10.10.0.1", 1, '{"browser":"Brave"}', now),
    )
    conn.commit()
    conn.close()


def run() -> int:
    source_db_path = os.path.join(BASE_DIR, "data", "source_demo.db")
    os.makedirs(os.path.dirname(source_db_path), exist_ok=True)
    _init_source_db(source_db_path)

    config = {
        "database_url": f"sqlite:///{source_db_path}",
        "table_map": {
            "users_src": "users",
            "transactions_src": "transactions",
            "login_events_src": "login_events",
        },
        "mappings": {
            "users": {"full_name": "name", "email_address": "email", "role_name": "role"},
            "transactions": {"user_ref": "user_id", "amount_usd": "amount"},
            "login_events": {"user_ref": "user_id", "ip": "ip_address", "metadata": "metadata"},
        },
        "incremental": {"users": {"field": "created_at"}, "transactions": {"field": "created_at"}, "login_events": {"field": "created_at"}},
    }

    with SessionLocalPrimary() as session:
        dc = session.execute(select(DataCenter).where(DataCenter.name == "demo-db-dc")).scalars().first()
        if dc is None:
            dc = DataCenter(name="demo-db-dc", status="healthy")
            session.add(dc)
            session.commit()
            session.refresh(dc)

        source = session.execute(
            select(DataCenterSource).where(
                DataCenterSource.data_center_id == dc.id,
                DataCenterSource.source_type == "db",
            )
        ).scalars().first()

        if source is None:
            source = DataCenterSource(
                data_center_id=dc.id,
                source_type="db",
                config_json=json.dumps(config),
                status="active",
            )
            session.add(source)
            session.commit()
            session.refresh(source)
            print(f"Created DB demo source id={source.id}")
        else:
            source.config_json = json.dumps(config)
            source.status = "active"
            session.commit()
            print(f"Updated DB demo source id={source.id}")

        print("DB connector demo ready.")
        return 0


if __name__ == "__main__":
    raise SystemExit(run())
