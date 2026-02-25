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
    assert "NetNova" in response.text
    assert "EVIL MARIA" in response.text


def test_router_auto_assignment_and_config_script(tmp_path: Path):
    client = create_test_client(tmp_path)

    customer_response = client.post(
        "/api/customers",
        json={
            "name": "Fiber Home 22",
            "plan_name": "Premium 500M",
            "monthly_rate": 89.90,
            "due_day": 20,
            "email": "noc@fiber22.example",
            "has_router": True,
            "router_identity": "CPE-Fiber22",
            "wan_interface": "ether1",
            "lan_interface": "ether2",
        },
    )
    assert customer_response.status_code == 201
    customer_id = customer_response.json()["id"]

    config_response = client.get(f"/api/customers/{customer_id}/router-config")
    assert config_response.status_code == 200
    payload = config_response.json()
    assert payload["customer_id"] == customer_id
    assert payload["subnet_cidr"].endswith("/30")
    assert "masquerade" in payload["script"]
    assert "CPE-Fiber22" in payload["script"]


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
            "has_router": False,
        },
    )
    assert customer_response.status_code == 201
    customer_id = customer_response.json()["id"]

    list_customers = client.get("/api/customers")
    assert list_customers.status_code == 200
    assert len(list_customers.json()) >= 1

    update_customer = client.patch(f"/api/customers/{customer_id}", json={"active": False, "plan_name": "Enterprise 2G"})
    assert update_customer.status_code == 200
    assert update_customer.json()["active"] is False

    invoice_response = client.post(
        "/api/invoices",
        json={"customer_id": customer_id, "billing_month": "2026-01", "amount": 249.99},
    )
    assert invoice_response.status_code == 201
    invoice_id = invoice_response.json()["id"]

    invoice_update = client.patch(f"/api/invoices/{invoice_id}", json={"status": "paid"})
    assert invoice_update.status_code == 200
    assert invoice_update.json()["status"] == "paid"

    event_response = client.post(
        "/api/events",
        json={"service_name": "POP-1", "severity": "critical", "message": "Backhaul down"},
    )
    assert event_response.status_code == 201

    ack_response = client.post("/api/events/1/ack")
    assert ack_response.status_code == 200
    assert ack_response.json()["acknowledged"] is True

    metrics = client.get("/api/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["customer_count"] >= 1
