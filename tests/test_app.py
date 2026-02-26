from pathlib import Path

from fastapi.testclient import TestClient
from app.config import Settings
from app.database import init_db
from app.main import create_app

def create_test_client(tmp_path: Path) -> TestClient:
    test_db = tmp_path / "test.db"
    settings = Settings(database_url=f"sqlite:///{test_db}", environment="test", debug=False)
    app = create_app(settings)
    init_db(app.state.engine)
    return TestClient(app)


def test_healthcheck(tmp_path: Path):
    client = create_test_client(tmp_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_redirects_to_login(tmp_path: Path):
    client = create_test_client(tmp_path)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_admin_and_client_portal_flow(tmp_path: Path):
    client = create_test_client(tmp_path)

    login = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/admin/dashboard"

    create_client = client.post(
        "/admin/accounts",
        data={
            "name": "Acme Fiber",
            "email": "billing@acme.example",
            "username": "acme",
            "password": "acme123",
            "plan_name": "Enterprise 1G",
            "monthly_rate": "249.99",
            "due_day": "15",
            "has_router": "true",
            "router_identity": "ACME-CPE",
            "wan_interface": "ether1",
            "lan_interface": "ether2",
        },
        follow_redirects=False,
    )
    assert create_client.status_code == 303

    client.post("/logout")
    client_login = client.post("/login", data={"username": "acme", "password": "acme123"}, follow_redirects=False)
    assert client_login.status_code == 303
    assert client_login.headers["location"] == "/client/portal"

    portal = client.get("/client/portal")
    assert portal.status_code == 200
    assert "Download Auto-Generated Router Script" in portal.text

    script = client.get("/client/router-script")
    assert script.status_code == 200
    assert "masquerade" in script.text


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

    invoice_response = client.post(
        "/api/invoices",
        json={"customer_id": customer_id, "billing_month": "2026-01", "amount": 249.99},
    )
    assert invoice_response.status_code == 201

    event_response = client.post(
        "/api/events",
        json={"service_name": "POP-1", "severity": "critical", "message": "Backhaul down"},
    )
    assert event_response.status_code == 201


def test_settings_builds_mysql_database_url_from_parts(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_DRIVER", "mysql+pymysql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_NAME", "ambertel_netnovabilling")
    monkeypatch.setenv("DB_USER", "ambertel_netnovabilling")
    monkeypatch.setenv("DB_PASSWORD", "Faith!@#")

    settings = Settings.from_env()

    assert settings.database_url == (
        "mysql+pymysql://ambertel_netnovabilling:Faith%21%40%23@localhost:3306/"
        "ambertel_netnovabilling"
    )
