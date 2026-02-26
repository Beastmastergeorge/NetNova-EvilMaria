# NetNova Billing + EVIL MARIA

Production-ready starter for an ISP billing platform (**NetNova**) integrated with a monitoring & notification web application (**EVIL MARIA**) with speech-alert capabilities.

## Included stack

- **Backend API**: FastAPI + SQLModel + SQLite (drop-in replaceable with PostgreSQL)
- **Frontend UI**: Server-rendered Jinja dashboard with responsive CSS and live polling JS
- **Operations features**:
  - customer provisioning and status toggle
  - invoice generation and payment updates
  - monitoring event ingestion and acknowledgement
  - real-time KPI cards and critical alert tracking
  - browser speech notifications for critical incidents
- **Deployment**: Gunicorn/Uvicorn startup script, Dockerfile, docker-compose, env template

## Project structure
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
  main.py
  models.py
  schemas.py
  models.py
  schemas.py
  main.py
  routers/
    api.py
    web.py
  services/
    metrics.py
  templates/
    dashboard.html
  static/
    style.css
    app.js
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

Open `http://127.0.0.1:8000`.

## API docs

- Swagger UI: `http://127.0.0.1:8000/docs`
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

## Run tests
## API quick checks

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/metrics
```

## Tests

```bash
pytest -q
```

## Notes for production hardening

- Add auth + RBAC
- Add Alembic migrations and PostgreSQL
- Add asynchronous workers for external channels (email/SMS/voice)
- Add observability and CI/CD checks
## Production hardening next steps

- Add authentication and role-based access control.
- Add DB migrations (Alembic) and move from SQLite to PostgreSQL.
- Add background workers for asynchronous notifications (email/SMS/voice gateways).
- Add observability stack (structured logging, tracing, metrics exporter).
- Add CI/CD and image scanning/signing before deployment.
# NetNova-EvilMaria
Enterprise ISP billing and monitoring system with STK push and voice alerts
# NetNova + EVIL MARIA

An ISP-grade billing platform (`NetNova`) integrated with a monitoring and notification web app called **EVIL MARIA**, including browser speech notifications for incident alerts.

## Features

- Customer onboarding with plan and MRR tracking.
- Invoice generation with due-date automation and receivables visibility.
- Monitoring dashboard for network nodes with latency-based health checks.
- Alert generation for degraded/critical conditions.
- Notification dispatch records (email, SMS, voice callback).
- Voice alert announcements in the browser via Web Speech API.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5050`.

## App Name Mapping

- **NetNova**: Billing and revenue operations.
- **EVIL MARIA**: Monitoring, alerting, and notification orchestration.
