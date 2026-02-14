def test_sentinel_scan(client) -> None:
    response = client.get("/api/v1/sentinel/scan?domain=security")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["domain"] == "security"
    assert "findings" in body["data"]
    assert "scan_id" in body["data"]
    assert "risk_score" in body["data"]
    assert "narrative" in body["data"]
    assert body["data"]["status"] == "completed"
    assert isinstance(body["data"]["findings"], list)
    assert len(body["data"]["findings"]) > 0


def test_sentinel_scan_general_domain(client) -> None:
    response = client.get("/api/v1/sentinel/scan?domain=general")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["domain"] == "general"
    assert body["data"]["status"] == "completed"
    for finding in body["data"]["findings"]:
        assert "mission_id" in finding
        assert "status" in finding


def test_sentinel_scan_all_domains(client) -> None:
    for domain in ("security", "risk", "operations", "compliance", "general"):
        response = client.get(f"/api/v1/sentinel/scan?domain={domain}")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["domain"] == domain


def test_sentinel_scan_unknown_domain_falls_back_to_general(client) -> None:
    response = client.get("/api/v1/sentinel/scan?domain=unknown_xyz")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "completed"


def test_sentinel_scan_default_domain(client) -> None:
    response = client.get("/api/v1/sentinel/scan")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["domain"] == "general"


def test_sentinel_scan_findings_have_completed_missions(client) -> None:
    response = client.get("/api/v1/sentinel/scan?domain=operations")
    assert response.status_code == 200
    body = response.json()
    findings = body["data"]["findings"]
    completed = [f for f in findings if f["status"] == "completed"]
    assert len(completed) > 0
    for f in completed:
        assert "sql" in f
        assert "rows" in f
        assert "risk" in f


def test_sentinel_history_persists(client) -> None:
    response = client.get("/api/v1/sentinel/scan?domain=compliance")
    assert response.status_code == 200
    scan_id = response.json()["data"]["scan_id"]

    response = client.get("/api/v1/sentinel/history")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    history = body["data"]["history"]
    assert isinstance(history, list)
    scan_ids = [h["scan_id"] for h in history]
    assert scan_id in scan_ids


def test_sentinel_history_detail(client) -> None:
    response = client.get("/api/v1/sentinel/scan?domain=general")
    assert response.status_code == 200
    scan_id = response.json()["data"]["scan_id"]

    response = client.get(f"/api/v1/sentinel/history/{scan_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["scan_id"] == scan_id
    assert "findings" in body["data"]


def test_sentinel_history_detail_not_found(client) -> None:
    response = client.get("/api/v1/sentinel/history/nonexistent_scan_id_12345")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"


def test_sentinel_scan_stream(client) -> None:
    response = client.get("/api/v1/sentinel/scan/stream?domain=general")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    text = response.text
    assert "event: status" in text
    assert "event: complete" in text
    assert "event: mission" in text
