# NET NOVA ISP BILLING

Production-ready starter for an ISP billing platform (**NET NOVA ISP BILLING**) integrated with a monitoring & notification web application (**EVIL MARIA**) with speech-alert capabilities.

## Included stack

- **Backend API**: FastAPI + SQLModel (SQLite for local dev, MySQL supported for production)
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


## Amber Telecom domain + database integration

This project is pre-configured to run behind `netnovabilling.ambertelecoms.co.ke` with a MySQL database on the same host (`localhost`) via environment variables.

1. Copy env template and keep the production values:
   ```bash
   cp .env.example .env
   ```
2. Confirm these values are set in `.env`:
   - `PUBLIC_BASE_URL=https://netnovabilling.ambertelecoms.co.ke`
   - `ALLOWED_ORIGINS=https://netnovabilling.ambertelecoms.co.ke`
   - `DB_HOST=localhost`
   - `DB_NAME=ambertel_netnovabilling`
   - `DB_USER=ambertel_netnovabilling`
   - `DB_PASSWORD=Faith!@#`
3. Start app (`docker compose up --build` or `uvicorn app.main:app --host 0.0.0.0 --port 8000`).
4. Configure your web server reverse proxy to forward `netnovabilling.ambertelecoms.co.ke` to this app.

`Settings` now builds `DATABASE_URL` automatically from `DB_*` values when `DATABASE_URL` is not explicitly set.


## Admin dashboard and client portal

- `/login` provides role-based portal access.
- Admin dashboard: `/admin/dashboard` with full client lifecycle controls (create, disable/enable, remove), router visibility, and operations data.
- Client portal: `/client/portal` for profile/package edits, payment gateway registration, router setup + script download, and transaction tracking.
- A default admin user is auto-created on first run: `admin / admin123` (change immediately in production).


## One-click website installer file

- Added `website-installer.php` for environments that require a browser-opened installer page.
- Added `scripts/website_install.sh` which performs the actual deployment to your website server (copies files, writes `.env`, runs Docker Compose, prints Nginx config).

Usage:

1. Upload project files to your server.
2. Set installer secret in your web server/PHP environment:
   ```bash
   export NETNOVA_INSTALL_SECRET="set-a-strong-secret"
   ```
3. Open `https://your-domain/website-installer.php`.
4. Enter the secret and run install.

> Security: delete `website-installer.php` immediately after installation.

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

## Website landing page

- `index.html` is provided as a website entry page linking to the dashboard, API docs, health/metrics endpoints, and integration docs.
