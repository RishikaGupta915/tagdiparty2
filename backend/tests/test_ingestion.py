import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.db.session import SessionLocalPrimary
from app.models.demo import User
from app.models.ingestion import DataCenter, DataCenterSource
from app.services.ingestion.sync import sync_source


def _create_source_db(path: Path) -> str:
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE users_src (
            id INTEGER PRIMARY KEY,
            full_name TEXT,
            email_address TEXT,
            role_name TEXT,
            created_at TEXT
        )
        """
    )
    now = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO users_src (full_name, email_address, role_name, created_at) VALUES (?, ?, ?, ?)",
        ("Source User", f"source_{now}@example.com", "analyst", now),
    )
    conn.commit()
    conn.close()
    return f"sqlite:///{path}"


def test_csv_pickup_and_archive(tmp_path: Path) -> None:
    ingest_dir = tmp_path / "ingest"
    archive_dir = tmp_path / "archive"
    error_dir = tmp_path / "error"
    ingest_dir.mkdir(parents=True, exist_ok=True)

    csv_path = ingest_dir / "users_001.csv"
    unique_email = f"test_user_{datetime.utcnow().timestamp()}@example.com"
    csv_path.write_text(f"name,email,role\nTest User,{unique_email},analyst\n", encoding="utf-8")

    with SessionLocalPrimary() as session:
        dc = DataCenter(name=f"dc-test-{datetime.utcnow().timestamp()}", status="healthy")
        session.add(dc)
        session.commit()
        session.refresh(dc)

        config = {
            "path": str(ingest_dir),
            "archive_path": str(archive_dir),
            "error_path": str(error_dir),
        }
        source = DataCenterSource(
            data_center_id=dc.id,
            source_type="csv",
            config_json=json.dumps(config),
            status="active",
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        sync_source(session, source)

        assert not csv_path.exists()
        assert (archive_dir / "users_001.csv").exists()
        assert source.last_error == ""
        assert source.last_sync is not None
        assert source.status == "active"

        session.delete(source)
        session.delete(dc)
        session.commit()


def test_db_connector_mapping_and_cursor(tmp_path: Path) -> None:
    source_db_path = tmp_path / "source.db"
    database_url = _create_source_db(source_db_path)

    with SessionLocalPrimary() as session:
        dc = DataCenter(name=f"dc-test-db-{datetime.utcnow().timestamp()}", status="healthy")
        session.add(dc)
        session.commit()
        session.refresh(dc)

        config = {
            "database_url": database_url,
            "table_map": {"users_src": "users"},
            "mappings": {
                "users": {
                    "full_name": "name",
                    "email_address": "email",
                    "role_name": "role",
                }
            },
            "incremental": {"users": {"field": "created_at"}},
        }
        source = DataCenterSource(
            data_center_id=dc.id,
            source_type="db",
            config_json=json.dumps(config),
            cursor_json="{}",
            status="active",
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        run = sync_source(session, source)
        assert run.records_ingested >= 1
        cursor = json.loads(source.cursor_json)
        assert "users" in cursor

        inserted = session.query(User).filter(User.email.like("source_%@example.com")).count()
        assert inserted >= 1

        session.delete(source)
        session.delete(dc)
        session.commit()
