def test_query_list_users(client) -> None:
    response = client.post("/api/v1/query", json={"query": "List users"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "result" in body["data"]
