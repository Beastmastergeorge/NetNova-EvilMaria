#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/netnova-isp-billing}"
DOMAIN="${DOMAIN:-netnovabilling.ambertelecoms.co.ke}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-ambertel_netnovabilling}"
DB_USER="${DB_USER:-ambertel_netnovabilling}"
DB_PASSWORD="${DB_PASSWORD:-Faith!@#}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker and Docker Compose first." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is required (docker compose)." >&2
  exit 1
fi

echo "[1/5] Preparing application directory at ${APP_DIR}"
sudo mkdir -p "${APP_DIR}"
sudo rsync -a --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  ./ "${APP_DIR}/"

cat <<EOF | sudo tee "${APP_DIR}/.env" >/dev/null
APP_NAME="NET NOVA ISP BILLING"
ENVIRONMENT="production"
DEBUG="false"
HOST="0.0.0.0"
PORT="8000"
PUBLIC_BASE_URL="https://${DOMAIN}"
ALLOWED_ORIGINS="https://${DOMAIN}"
DB_DRIVER="mysql+pymysql"
DB_HOST="${DB_HOST}"
DB_PORT="${DB_PORT}"
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}"
EOF

echo "[2/5] Building and starting NET NOVA ISP BILLING containers"
cd "${APP_DIR}"
sudo docker compose up --build -d

echo "[3/5] Running health check"
if ! curl -fsS http://127.0.0.1:8000/api/health >/dev/null; then
  echo "Warning: app started but health endpoint did not respond yet." >&2
fi

echo "[4/5] Generating Nginx vhost template"
cat <<NGINX
server {
  listen 80;
  server_name ${DOMAIN};

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
}
NGINX

echo "[5/5] Installation complete"
echo "Open: https://${DOMAIN}/login"
echo "Default admin account: admin / admin123 (change immediately)."
