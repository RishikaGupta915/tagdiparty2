"""Tests for DB diagnostics endpoints and database integrity."""


def test_db_health(client) -> None:
    response = client.get("/api/db-test/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_db_tables(client) -> None:
    response = client.get("/api/db-test/tables")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    tables = body["data"]["tables"]
    assert isinstance(tables, list)
    # Core demo tables (primary DB)
    assert "users" in tables
    assert "transactions" in tables
    assert "login_events" in tables
    # Sentinel
    assert "scan_history" in tables
    # Analytics & archive
    assert "daily_transaction_metrics" in tables
    assert "transactions_archive" in tables
    assert "login_events_archive" in tables

    # Alert subsystem tables (alerts DB)
    resp_alerts = client.get("/api/db-test/alerts")
    assert resp_alerts.status_code == 200
    alert_tables = resp_alerts.json()["data"]["tables"]
    assert "metrics" in alert_tables
    assert "events" in alert_tables
    assert "alert_history" in alert_tables
    assert "anomaly_history" in alert_tables

    # Dashboards (dashboards DB)
    resp_dash = client.get("/api/db-test/dashboards")
    assert resp_dash.status_code == 200
    dash_tables = resp_dash.json()["data"]["tables"]
    assert "dashboards" in dash_tables


def test_db_schema(client) -> None:
    response = client.get("/api/db-test/schema")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    schema = body["data"]["schema"]
    assert isinstance(schema, dict)
    # Verify users table has expected columns
    user_cols = [c["name"] for c in schema["users"]]
    assert "id" in user_cols
    assert "name" in user_cols
    assert "email" in user_cols
    assert "role" in user_cols
    assert "created_at" in user_cols


def test_db_schema_transactions_columns(client) -> None:
    response = client.get("/api/db-test/schema")
    body = response.json()
    schema = body["data"]["schema"]
    tx_cols = [c["name"] for c in schema["transactions"]]
    assert "id" in tx_cols
    assert "user_id" in tx_cols
    assert "amount" in tx_cols
    assert "currency" in tx_cols
    assert "status" in tx_cols
    assert "created_at" in tx_cols


def test_db_schema_login_events_columns(client) -> None:
    response = client.get("/api/db-test/schema")
    body = response.json()
    schema = body["data"]["schema"]
    le_cols = [c["name"] for c in schema["login_events"]]
    assert "id" in le_cols
    assert "user_id" in le_cols
    assert "ip_address" in le_cols
    assert "success" in le_cols
    assert "metadata" in le_cols  # DB column name stays 'metadata'


def test_db_seed_data_present(client) -> None:
    """Verify init_db seeded demo data."""
    response = client.post("/api/v1/query", json={"query": "List users"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    rows = body["data"]["result"]["rows"]
    assert len(rows) >= 2
    names = [r["name"] for r in rows]
    assert "Ava Chen" in names
    assert "Jordan Miles" in names
