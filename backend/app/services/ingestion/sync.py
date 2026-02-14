import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple
from urllib import request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.models.demo import User, Transaction, LoginEvent
from app.models.ingestion import DataCenterSource, IngestionRun
from app.services.ingestion.engine import create_ingestion_run, finalize_ingestion_run, ingest_csv, touch_data_center


def sync_source(db: Session, source: DataCenterSource) -> IngestionRun:
    run = create_ingestion_run(db, source.data_center_id, source.source_type, status="running")
    ingested = 0
    error = ""
    cursor_state = _load_config(source.cursor_json)
    config = _load_config(source.config_json)
    try:
        if source.source_type == "csv":
            ingested = _sync_csv_source(db, source, config, cursor_state)
        elif source.source_type == "db":
            ingested = _sync_db_source(db, source, config, cursor_state)
        elif source.source_type == "api":
            ingested = _sync_api_source(db, source, config, cursor_state)
        else:
            raise RuntimeError(f"Unknown source_type: {source.source_type}")
    except Exception as exc:
        error = str(exc)

    if error:
        finalize_ingestion_run(db, run, "failed", 0, error)
        source.last_error = error
        source.status = "error"
    else:
        finalize_ingestion_run(db, run, "success", ingested, "")
        source.last_error = ""
        source.status = "active"
        source.last_sync = datetime.utcnow()
        source.cursor_json = json.dumps(cursor_state)
        touch_data_center(db, source.data_center_id, status="healthy")

    db.commit()
    return run


def _sync_csv_source(db: Session, source: DataCenterSource, config: Dict[str, Any], cursor_state: Dict[str, Any]) -> int:
    path = config.get("path") or "./data/ingest"
    archive_path = config.get("archive_path") or os.path.join(path, "processed")
    error_path = config.get("error_path") or os.path.join(path, "error")
    if not os.path.isdir(path):
        raise RuntimeError(f"CSV path not found: {path}")
    os.makedirs(archive_path, exist_ok=True)
    os.makedirs(error_path, exist_ok=True)

    total = 0
    for entry in os.scandir(path):
        if not entry.is_file() or not entry.name.lower().endswith(".csv"):
            continue

        dataset = _dataset_from_filename(entry.name)
        if dataset is None:
            continue
        with open(entry.path, "r", encoding="utf-8", errors="replace") as handle:
            content = handle.read()
        mapping = _dataset_mapping(config, dataset)
        ingested, error = ingest_csv(db, dataset, content, mapping=mapping)
        if error:
            _move_file(entry.path, error_path)
            raise RuntimeError(error)
        total += ingested
        _move_file(entry.path, archive_path)

    return total


def _sync_db_source(db: Session, source: DataCenterSource, config: Dict[str, Any], cursor_state: Dict[str, Any]) -> int:
    database_url = config.get("database_url")
    if not database_url:
        raise RuntimeError("DB connector missing database_url")

    engine = create_engine(database_url, future=True)
    total = 0
    table_map = _table_map(config)
    with engine.connect() as conn:
        for source_table, dataset in table_map:
            rows = _fetch_rows(conn, source_table, dataset, config, cursor_state)
            if not rows:
                continue
            total += _insert_rows(db, dataset, rows, config)
            _update_cursor(cursor_state, dataset, rows, config)
    return total


def _fetch_rows(
    conn,
    source_table: str,
    dataset: str,
    config: Dict[str, Any],
    cursor_state: Dict[str, Any],
) -> List[Dict[str, Any]]:
    field = _incremental_field(config, dataset)
    cursor_value = cursor_state.get(dataset)
    if cursor_value is not None:
        stmt = text(f"SELECT * FROM {source_table} WHERE {field} > :cursor")
        rows = conn.execute(stmt, {"cursor": cursor_value}).mappings().all()
    else:
        stmt = text(f"SELECT * FROM {source_table}")
        rows = conn.execute(stmt).mappings().all()
    return list(rows)


def _insert_rows(db: Session, table: str, rows: Iterable[Dict[str, Any]], config: Dict[str, Any]) -> int:
    records = []
    mapping = _dataset_mapping(config, table)
    if table == "users":
        for row in rows:
            row = _apply_mapping(row, mapping)
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            role = (row.get("role") or "analyst").strip()
            if not name or not email:
                continue
            records.append(User(name=name, email=email, role=role))
    elif table == "transactions":
        for row in rows:
            row = _apply_mapping(row, mapping)
            user_id = int(row.get("user_id") or 0)
            amount = row.get("amount")
            if user_id <= 0 or amount is None:
                continue
            currency = (row.get("currency") or "USD").strip()
            status = (row.get("status") or "completed").strip()
            records.append(
                Transaction(
                    user_id=user_id,
                    amount=float(amount),
                    currency=currency,
                    status=status,
                )
            )
    elif table == "login_events":
        for row in rows:
            row = _apply_mapping(row, mapping)
            user_id = int(row.get("user_id") or 0)
            ip_address = (row.get("ip_address") or "").strip()
            if user_id <= 0 or not ip_address:
                continue
            success = int(row.get("success") or 1)
            metadata = (row.get("metadata") or row.get("event_metadata") or "{}").strip()
            records.append(
                LoginEvent(
                    user_id=user_id,
                    ip_address=ip_address,
                    success=success,
                    event_metadata=metadata,
                )
            )
    if not records:
        return 0
    db.add_all(records)
    db.commit()
    return len(records)


def _dataset_from_filename(filename: str) -> str | None:
    name = filename.lower()
    if name.startswith("users"):
        return "users"
    if name.startswith("transactions"):
        return "transactions"
    if name.startswith("login_events") or name.startswith("login-events"):
        return "login_events"
    return None


def _sync_api_source(db: Session, source: DataCenterSource, config: Dict[str, Any], cursor_state: Dict[str, Any]) -> int:
    base_url = config.get("base_url")
    endpoints = config.get("endpoints") or {}
    headers = config.get("headers") or {}
    if not base_url or not endpoints:
        raise RuntimeError("API connector missing base_url or endpoints")

    total = 0
    for dataset in ("users", "transactions", "login_events"):
        endpoint = endpoints.get(dataset)
        if not endpoint:
            continue
        url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")
        data = _http_get_json(url, headers=headers)
        if not isinstance(data, list):
            raise RuntimeError(f"API endpoint did not return list for {dataset}")
        total += _insert_rows(db, dataset, data, config)
        _update_cursor(cursor_state, dataset, data, config)
    return total


def _http_get_json(url: str, headers: Dict[str, str]) -> Any:
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req, timeout=30) as resp:
        payload = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from API: {exc}") from exc


def _move_file(path: str, target_dir: str) -> None:
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, os.path.basename(path))
    shutil.move(path, target)


def _table_map(config: Dict[str, Any]) -> List[Tuple[str, str]]:
    mapping = config.get("table_map") or {}
    if mapping:
        return [(source, dataset) for source, dataset in mapping.items()]
    return [("users", "users"), ("transactions", "transactions"), ("login_events", "login_events")]


def _dataset_mapping(config: Dict[str, Any], dataset: str) -> Dict[str, str] | None:
    mappings = config.get("mappings") or {}
    mapping = mappings.get(dataset)
    return mapping if isinstance(mapping, dict) else None


def _incremental_field(config: Dict[str, Any], dataset: str) -> str:
    incremental = config.get("incremental") or {}
    if dataset in incremental and isinstance(incremental[dataset], dict):
        field = incremental[dataset].get("field")
        if field:
            return field
    return "created_at"


def _update_cursor(cursor_state: Dict[str, Any], dataset: str, rows: Iterable[Dict[str, Any]], config: Dict[str, Any]) -> None:
    field = _incremental_field(config, dataset)
    values = [row.get(field) for row in rows if row.get(field) is not None]
    if not values:
        return
    try:
        max_value = max(values)
    except TypeError:
        max_value = max(str(v) for v in values)
    if isinstance(max_value, datetime):
        cursor_state[dataset] = max_value.isoformat()
    else:
        cursor_state[dataset] = max_value


def _apply_mapping(row: Dict[str, Any], mapping: Dict[str, str] | None) -> Dict[str, Any]:
    if not mapping:
        return row
    mapped = dict(row)
    for source_field, dest_field in mapping.items():
        if source_field in row:
            mapped[dest_field] = row[source_field]
    return mapped


def _load_config(raw: str) -> Dict[str, Any]:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
