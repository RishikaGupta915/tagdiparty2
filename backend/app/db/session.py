import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()


def _ensure_sqlite_dir(database_url: str) -> None:
    if database_url.startswith("sqlite"):
        db_path = database_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)


def _make_engine(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        _ensure_sqlite_dir(database_url)
    engine = create_engine(database_url, connect_args=connect_args, future=True)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, connection_record):  # type: ignore[no-redef]
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON;")
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.execute("PRAGMA temp_store=MEMORY;")
                cursor.execute("PRAGMA cache_size=-20000;")
            finally:
                cursor.close()
    return engine


engine_primary = _make_engine(settings.database_url)
engine_alerts = _make_engine(settings.alerts_database_url)
engine_dashboards = _make_engine(settings.dashboards_database_url)

SessionLocalPrimary = sessionmaker(bind=engine_primary, autoflush=False, autocommit=False, future=True)
SessionLocalAlerts = sessionmaker(bind=engine_alerts, autoflush=False, autocommit=False, future=True)
SessionLocalDashboards = sessionmaker(bind=engine_dashboards, autoflush=False, autocommit=False, future=True)


def get_db_primary():
    db = SessionLocalPrimary()
    try:
        yield db
    finally:
        db.close()


def get_db_alerts():
    db = SessionLocalAlerts()
    try:
        yield db
    finally:
        db.close()


def get_db_dashboards():
    db = SessionLocalDashboards()
    try:
        yield db
    finally:
        db.close()


# Backward-compatible alias for primary DB usage
def get_db():
    yield from get_db_primary()
