import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import select  # noqa: E402
from app.db.session import SessionLocalPrimary  # noqa: E402
from app.models.ingestion import DataCenter, DataCenterSource  # noqa: E402


def run() -> int:
    ingest_path = "./data/ingest/demo"
    config = {
        "path": ingest_path,
        "archive_path": os.path.join(ingest_path, "processed"),
        "error_path": os.path.join(ingest_path, "error"),
    }

    with SessionLocalPrimary() as session:
        dc = session.execute(select(DataCenter).where(DataCenter.name == "demo-dc")).scalars().first()
        if dc is None:
            dc = DataCenter(name="demo-dc", status="healthy")
            session.add(dc)
            session.commit()
            session.refresh(dc)

        source = session.execute(
            select(DataCenterSource).where(
                DataCenterSource.data_center_id == dc.id,
                DataCenterSource.source_type == "csv",
            )
        ).scalars().first()

        if source is None:
            source = DataCenterSource(
                data_center_id=dc.id,
                source_type="csv",
                config_json=json.dumps(config),
                status="active",
            )
            session.add(source)
            session.commit()
            session.refresh(source)
            print(f"Created demo source id={source.id}")
        else:
            source.config_json = json.dumps(config)
            source.status = "active"
            session.commit()
            print(f"Updated demo source id={source.id}")

        print("Demo data center ready.")
        return 0


if __name__ == "__main__":
    raise SystemExit(run())
