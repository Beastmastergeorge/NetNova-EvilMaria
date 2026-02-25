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
  - **auto IP assignment + MikroTik router script generation** when customer router is enabled
- **Deployment**: Gunicorn/Uvicorn startup script, Dockerfile, docker-compose, env template

## MikroTik auto-provisioning flow

1. Create customer with `has_router=true` (web form checkbox or API payload).
2. System assigns a dedicated `/30` transit block and generates a MikroTik script.
3. Retrieve script from:
   - UI link in Customers table (`/customers/{id}/router-config`)
   - API endpoint (`/api/customers/{id}/router-config`)

## Project structure

```text
app/
  config.py
  database.py
  main.py
  models.py
  schemas.py
  routers/
    api.py
    web.py
  services/
    metrics.py
    mikrotik.py
  templates/
    dashboard.html
  static/
    style.css
    app.js
scripts/start.sh
Dockerfile
docker-compose.yml
requirements.txt
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

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

## Run tests

```bash
pytest -q
```

## Notes for production hardening

- Add auth + RBAC
- Add Alembic migrations and PostgreSQL
- Add asynchronous workers for external channels (email/SMS/voice)
- Add observability and CI/CD checks

## Website integration guide

- See `docs/website-integration-installation-guide.md` for full installation and integration steps.
