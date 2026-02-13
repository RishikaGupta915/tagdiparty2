import argparse
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from sqlalchemy import inspect
from app.db.session import engine_primary, engine_alerts, engine_dashboards
from app.models.base import Base
from app.models import alerts, demo, sentinel, dashboard, analytics, archive  # noqa: F401


def _missing_tables(engine, table_names):
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    return [t for t in table_names if t not in existing]


def _create_tables(engine, table_names):
    if not table_names:
        return []
    tables = [Base.metadata.tables[name] for name in table_names]
    Base.metadata.create_all(bind=engine, tables=tables)
    return table_names


def run() -> int:
    parser = argparse.ArgumentParser(description="Initialize missing tables safely.")
    parser.add_argument("--all", action="store_true", help="Check all databases")
    parser.add_argument("--primary", action="store_true", help="Check primary database")
    parser.add_argument("--alerts", action="store_true", help="Check alerts database")
    parser.add_argument("--dashboards", action="store_true", help="Check dashboards database")
    args = parser.parse_args()

    if not (args.all or args.primary or args.alerts or args.dashboards):
        args.all = True

    results = []
    if args.all or args.primary:
        primary_tables = [
            "users",
            "transactions",
            "login_events",
            "transactions_archive",
            "login_events_archive",
            "daily_transaction_metrics",
            "scan_history",
        ]
        missing = _missing_tables(engine_primary, primary_tables)
        created = _create_tables(engine_primary, missing)
        results.append(("primary", missing, created))

    if args.all or args.alerts:
        alerts_tables = ["metrics", "events", "alert_history", "anomaly_history"]
        missing = _missing_tables(engine_alerts, alerts_tables)
        created = _create_tables(engine_alerts, missing)
        results.append(("alerts", missing, created))

    if args.all or args.dashboards:
        dashboards_tables = ["dashboards"]
        missing = _missing_tables(engine_dashboards, dashboards_tables)
        created = _create_tables(engine_dashboards, missing)
        results.append(("dashboards", missing, created))

    for name, missing, created in results:
        print(f"{name}: missing={missing} created={created}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
