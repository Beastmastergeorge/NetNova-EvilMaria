from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def create_test_client(tmp_path: Path) -> TestClient:
    test_db = tmp_path / "test.db"
    settings = Settings(database_url=f"sqlite:///{test_db}", environment="test", debug=False)
    app = create_app(settings)
    return TestClient(app)


def test_healthcheck(tmp_path: Path):
    client = create_test_client(tmp_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_loads(tmp_path: Path):
    client = create_test_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "NetNova ISP Billing" in response.text
    assert "EVIL MARIA" in response.text


def test_api_customer_invoice_and_event_flow(tmp_path: Path):
    client = create_test_client(tmp_path)

    customer_response = client.post(
        "/api/customers",
        json={
            "name": "Acme Fiber",
            "plan_name": "Enterprise 1G",
            "monthly_rate": 249.99,
            "due_day": 15,
            "email": "billing@acme.example",
        },
    )
    assert customer_response.status_code == 201

    invoice_response = client.post(
        "/api/invoices",
        json={"customer_id": 1, "billing_month": "2026-01", "amount": 249.99},
    )
    assert invoice_response.status_code == 201

    event_response = client.post(
        "/api/events",
        json={"service_name": "POP-1", "severity": "critical", "message": "Backhaul down"},
    )
    assert event_response.status_code == 201

    ack_response = client.post("/api/events/1/ack")
    assert ack_response.status_code == 200
    assert ack_response.json()["acknowledged"] is True
