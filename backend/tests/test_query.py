from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_query_list_users() -> None:
    response = client.post("/api/v1/query", json={"query": "List users"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "result" in body["data"]
