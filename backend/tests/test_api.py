from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_CSV = "date,description,amount\n" + "\n".join(
    f"2024-{m:02d}-01,NETFLIX.COM,15.49" for m in range(1, 5)
)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "agent_configured" in body


def test_audit_endpoint_detects_subscription(tmp_path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(SAMPLE_CSV)

    with open(csv_path, "rb") as fh:
        response = client.post("/api/audit", files={"files": ("transactions.csv", fh, "text/csv")})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total_subscriptions"] == 1
    assert body["subscriptions"][0]["merchant"] == "Netflix"
    assert "audit_id" in body


def test_audit_endpoint_rejects_empty_upload():
    response = client.post("/api/audit", files={})
    assert response.status_code in (400, 422)


def test_chat_endpoint_requires_known_audit_id():
    response = client.post("/api/chat", json={"audit_id": "does-not-exist", "question": "hi"})
    assert response.status_code == 404


def test_chat_endpoint_calls_agent_with_stored_report(tmp_path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(SAMPLE_CSV)
    with open(csv_path, "rb") as fh:
        audit_response = client.post("/api/audit", files={"files": ("transactions.csv", fh, "text/csv")})
    audit_id = audit_response.json()["audit_id"]

    with patch("app.api.routes.run_agent_turn", return_value="Netflix costs $15.49/month.") as mock_agent:
        response = client.post("/api/chat", json={"audit_id": audit_id, "question": "How much is Netflix?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Netflix costs $15.49/month."
    assert mock_agent.call_count == 1
