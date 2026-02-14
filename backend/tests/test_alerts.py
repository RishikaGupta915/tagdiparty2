"""Tests for the alerting subsystem: event ingestion, metrics CRUD, history."""


# ── Event ingestion ────────────────────────────────────────────────


def test_ingest_event(client) -> None:
    response = client.post(
        "/api/v1/alert",
        json={"event_type": "login_failure", "source": "test", "payload": '{"ip": "1.2.3.4"}'},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "event_id" in body["data"]
    assert isinstance(body["data"]["event_id"], int)


def test_ingest_event_defaults(client) -> None:
    response = client.post("/api/v1/alert", json={"event_type": "heartbeat"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True


def test_ingest_event_empty_type_rejected(client) -> None:
    response = client.post("/api/v1/alert", json={"event_type": ""})
    assert response.status_code == 422  # validation error


# ── Metrics CRUD ───────────────────────────────────────────────────


def test_create_metric(client) -> None:
    response = client.post(
        "/api/v1/alerts/metrics",
        json={
            "name": "test_metric_cpu",
            "description": "CPU spike detector",
            "query": "SELECT COUNT(*) FROM events WHERE event_type = 'cpu_spike'",
            "window_minutes": 30,
            "threshold": 5.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    metric = body["data"]["metric"]
    assert metric["name"] == "test_metric_cpu"
    assert metric["threshold"] == 5.0
    assert metric["window_minutes"] == 30


def test_list_metrics(client) -> None:
    # Ensure at least one metric exists
    client.post(
        "/api/v1/alerts/metrics",
        json={"name": "test_metric_list", "query": "SELECT 1", "threshold": 1.0},
    )
    response = client.get("/api/v1/alerts/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"]["metrics"], list)
    assert len(body["data"]["metrics"]) >= 1


def test_update_metric(client) -> None:
    # Create
    resp = client.post(
        "/api/v1/alerts/metrics",
        json={"name": "test_metric_update", "query": "SELECT 1", "threshold": 1.0},
    )
    metric_id = resp.json()["data"]["metric"]["id"]

    # Update
    response = client.put(
        f"/api/v1/alerts/metrics/{metric_id}",
        json={"name": "test_metric_update", "query": "SELECT 2", "threshold": 9.9, "window_minutes": 120},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["metric"]["threshold"] == 9.9
    assert body["data"]["metric"]["window_minutes"] == 120


def test_update_metric_not_found(client) -> None:
    response = client.put(
        "/api/v1/alerts/metrics/99999",
        json={"name": "ghost", "query": "SELECT 1", "threshold": 0},
    )
    assert response.status_code == 404


def test_delete_metric(client) -> None:
    resp = client.post(
        "/api/v1/alerts/metrics",
        json={"name": "test_metric_delete_me", "query": "SELECT 1", "threshold": 0},
    )
    metric_id = resp.json()["data"]["metric"]["id"]

    response = client.delete(f"/api/v1/alerts/metrics/{metric_id}")
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

    # Confirm it's gone
    response = client.delete(f"/api/v1/alerts/metrics/{metric_id}")
    assert response.status_code == 404


def test_delete_metric_not_found(client) -> None:
    response = client.delete("/api/v1/alerts/metrics/99999")
    assert response.status_code == 404


# ── History / anomaly endpoints ────────────────────────────────────


def test_alert_history_empty_initially(client) -> None:
    response = client.get("/api/v1/alerts/history")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"]["history"], list)


def test_anomaly_history_empty_initially(client) -> None:
    response = client.get("/api/v1/alerts/anomalies")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"]["anomalies"], list)
