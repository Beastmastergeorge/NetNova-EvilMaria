# NET NOVA ISP BILLING Website Integration Installation Guide

This guide explains how to install and integrate the NET NOVA ISP BILLING platform into your website and operations environment.

## 1) Integration goals

You can integrate this project in three common ways:

1. **Embedded operations portal** for internal teams (billing + monitoring dashboard).
2. **API integration** from your public website (customer signup/provisioning flows).
3. **Router provisioning handoff** where customer onboarding triggers MikroTik config generation.

## 2) Prerequisites

- Linux server or VM (Ubuntu 22.04+ recommended)
- Docker and Docker Compose plugin installed (recommended deployment path)
- DNS name for your deployment (for this project: `netnovabilling.ambertelecoms.co.ke`)
- Reverse proxy / TLS termination (Nginx, Traefik, or cloud load balancer)
- Python 3.10+ (only needed for non-Docker runtime)

## 3) Install the platform

### Option A: Docker (recommended)

```bash
git clone <your-repo-url> netnova-evilmaria
cd netnova-evilmaria
cp .env.example .env
docker compose up --build -d
```

Verify service health:

```bash
curl http://127.0.0.1:8000/api/health
```

### Option B: Native Python runtime

```bash
git clone <your-repo-url> netnova-evilmaria
cd netnova-evilmaria
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 4) Configure environment for website integration

Edit `.env` and set for your live deployment:

```env
APP_NAME="NET NOVA ISP BILLING"
ENVIRONMENT="production"
DEBUG="false"
HOST="0.0.0.0"
PORT="8000"
PUBLIC_BASE_URL="https://netnovabilling.ambertelecoms.co.ke"
ALLOWED_ORIGINS="https://netnovabilling.ambertelecoms.co.ke"
DB_DRIVER="mysql+pymysql"
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="ambertel_netnovabilling"
DB_USER="ambertel_netnovabilling"
DB_PASSWORD="Faith!@#"
```

If `DATABASE_URL` is not set, the app automatically composes it from `DB_*` values.

## 5) Reverse proxy and TLS

Place NET NOVA ISP BILLING behind HTTPS. Example Nginx upstream:

```nginx
server {
  listen 443 ssl;
  server_name netnovabilling.ambertelecoms.co.ke;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
  }
}
```

## 6) Website integration patterns

### Pattern A: Internal portal link

From your website admin/ops area, link directly to:

- Dashboard UI: `https://netnovabilling.ambertelecoms.co.ke/`
- API docs: `https://netnovabilling.ambertelecoms.co.ke/docs`

### Pattern B: Server-to-server API integration

Use your website backend to call NET NOVA ISP BILLING APIs:

- `POST /api/customers` to create customer records
- `POST /api/invoices` to generate billing entries
- `POST /api/events` to push EVIL MARIA alerts
- `GET /api/customers/{id}/router-config` to retrieve MikroTik script

#### Example create customer with router enabled

```bash
curl -X POST https://netnovabilling.ambertelecoms.co.ke/api/customers \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "North District Fiber",
    "plan_name": "SMB 300M",
    "monthly_rate": 120.00,
    "due_day": 12,
    "email": "billing@northdistrict.example",
    "has_router": true,
    "router_identity": "ND-Fiber-CPE-01",
    "wan_interface": "ether1",
    "lan_interface": "ether2"
  }'
```

#### Example get generated MikroTik script

```bash
curl https://netnovabilling.ambertelecoms.co.ke/api/customers/1/router-config
```

### Pattern C: Embedded iframe (internal-only)

If needed for internal tools:

```html
<iframe
  src="https://netnovabilling.ambertelecoms.co.ke/"
  title="NET NOVA ISP BILLING EVIL MARIA"
  width="100%"
  height="900"
  style="border:0;"
></iframe>
```

> Note: current app sets `X-Frame-Options: DENY`; iframe embedding requires adjusting security headers first.

## 7) Router provisioning handoff workflow

1. Website captures onboarding details.
2. Website backend calls `POST /api/customers` with `has_router=true`.
3. NET NOVA ISP BILLING auto-assigns a `/30` transit IP block and generates MikroTik script.
4. Website/NOC fetches script via `GET /api/customers/{id}/router-config`.
5. NOC pastes script into RouterOS terminal on the customer router.

## 8) Validation checklist

After installation, verify:

- `GET /api/health` returns `{ "status": "ok" }`
- Dashboard loads at `/`
- You can create a customer from UI form
- Router-enabled customer shows script link in Customers table
- EVIL MARIA alerts appear and can be acknowledged
- Speech notifications can be enabled from dashboard button

## 9) Security hardening recommendations

- Put the app behind HTTPS only
- Restrict `ALLOWED_ORIGINS` to your exact website domains
- Add authentication + role-based access controls for UI and API
- Rotate credentials/secrets via secret manager
- Add audit logging and alerting for provisioning actions

## 10) Upgrade process

```bash
cd netnova-evilmaria
git pull
cp .env.example .env.example.latest
# merge new variables if any
docker compose up --build -d
```

Run smoke checks after deploy:

```bash
curl https://netnovabilling.ambertelecoms.co.ke/api/health
curl https://netnovabilling.ambertelecoms.co.ke/api/metrics
```


## 11) Browser-opened installer file (optional)

If your hosting workflow needs an installer file that runs when opened in a browser:

1. Keep `website-installer.php` and `scripts/website_install.sh` on the server.
2. Set `NETNOVA_INSTALL_SECRET` in PHP/web-server environment.
3. Open `https://netnovabilling.ambertelecoms.co.ke/website-installer.php`.
4. Enter the secret and click install.

The PHP file executes `scripts/website_install.sh`, which deploys the app and prints Nginx config guidance.

> Important: remove `website-installer.php` after successful installation.


## 12) Payment gateway integration UI (Stripe, M-Pesa, KopoKopo)

In the client portal (`/client/portal`), use **Major Payment Gateway Integration** cards to quickly enable:
- Stripe
- M-Pesa (Daraja)
- KopoKopo

You can also add custom credentials (public key/shortcode and callback URL) in the gateway form, then record payments from enabled gateways in the Transactions panel.
