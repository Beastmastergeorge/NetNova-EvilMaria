# NetNova Billing + EVIL MARIA (Production-Ready Starter)

A production-focused starter platform for an ISP-grade billing system (**NetNova**) integrated with a monitoring and notification web app (**EVIL MARIA**) including browser speech alerts.

## What is included

- **Backend**: FastAPI app with separated config/database/models/routers/services modules.
- **Frontend**: Jinja2 dashboard + static JS/CSS for operations workflows.
- **Billing**: Customer records, invoices, payment status lifecycle.
- **Monitoring**: Severity-tagged events and acknowledgement lifecycle.
- **Notifications**: Browser speech announcements for critical unacknowledged events.
- **API layer**: JSON endpoints for health, metrics, customer/invoice/event operations.
- **Security baseline**: CORS support and hardened response headers middleware.
- **Containerization**: Dockerfile + docker-compose for deployment.
- **Operational files**: `.env.example`, startup script, and `.gitignore`.
- **Tests**: Endpoint tests for health, dashboard, and API billing/monitoring flows.

## Project layout

```text
app/
  config.py
  database.py
  models.py
  schemas.py
  main.py
  routers/
    api.py
    web.py
  services/
    metrics.py
  templates/dashboard.html
  static/style.css
  static/app.js
scripts/start.sh
Dockerfile
docker-compose.yml
requirements.txt
tests/test_app.py
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open: `http://127.0.0.1:8000`

## Run in production mode (without Docker)

```bash
pip install -r requirements.txt
ENVIRONMENT=production DEBUG=false ./scripts/start.sh
```

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

## API quick checks

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/metrics
```

## Tests

```bash
pytest -q
```

## Production hardening next steps

- Add authentication and role-based access control.
- Add DB migrations (Alembic) and move from SQLite to PostgreSQL.
- Add background workers for asynchronous notifications (email/SMS/voice gateways).
- Add observability stack (structured logging, tracing, metrics exporter).
- Add CI/CD and image scanning/signing before deployment.
