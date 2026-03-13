from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_analyze_success():
    payload = {"transactions": [
        {"id": "t1", "date": "2025-01-01", "amount": 5000,   "description": "Salary",    "type": "credit"},
        {"id": "t2", "date": "2025-01-03", "amount": 3000,   "description": "Freelance", "type": "credit"},
        {"id": "t3", "date": "2025-01-05", "amount": -1200,  "description": "Rent",      "type": "debit"},
        {"id": "t4", "date": "2025-01-07", "amount": -150,   "description": "Utilities", "type": "debit"},
        {"id": "t5", "date": "2025-01-10", "amount": -75.50, "description": "Groceries", "type": "debit"},
    ]}
    resp = client.post("/analyze-file", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data["summary"]["total_inflow"] == 8000.0
    assert data["summary"]["total_outflow"] == 1425.5
    assert data["summary"]["net_cash_flow"] == 6574.5
    assert data["readiness"] in ("strong", "structured", "requires_clarification")


def test_empty_payload_422():
    assert client.post("/analyze-file", json={"transactions": []}).status_code == 422


def test_missing_field_422():
    assert client.post("/analyze-file", json={}).status_code == 422


def test_bad_type_422():
    bad = {"transactions": [{"id": "1", "date": "2025-01-01", "amount": 100, "description": "", "type": "transfer"}]}
    assert client.post("/analyze-file", json=bad).status_code == 422


def test_nsf_flag_shows_up():
    payload = {"transactions": [
        {"id": "t1", "date": "2025-01-01", "amount": 5000, "description": "Salary", "type": "credit"},
        {"id": "t2", "date": "2025-01-02", "amount": 3000, "description": "Bonus",  "type": "credit"},
        {"id": "t3", "date": "2025-01-05", "amount": -50,  "description": "NSF fee", "type": "debit"},
    ]}
    data = client.post("/analyze-file", json=payload).json()
    assert "nsf_activity_detected" in [f["flag"] for f in data["risk_flags"]]


def test_risky_profile():
    """Throw a bunch of red flags at it and make sure it catches them."""
    payload = {"transactions": [
        {"id": "t1", "date": "2025-01-01", "amount": 500,   "description": "Small deposit", "type": "credit"},
        {"id": "t2", "date": "2025-01-02", "amount": -2000, "description": "Big expense",   "type": "debit"},
        {"id": "t3", "date": "2025-01-03", "amount": -50,   "description": "NSF fee",       "type": "debit"},
        {"id": "t4", "date": "2025-01-04", "amount": -100,  "description": "Returned item", "type": "debit"},
    ]}
    data = client.post("/analyze-file", json=payload).json()
    assert data["readiness"] == "requires_clarification"
    assert len(data["risk_flags"]) >= 3  # should catch several issues
