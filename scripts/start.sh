#!/usr/bin/env bash
set -euo pipefail

export APP_NAME=${APP_NAME:-"NET NOVA ISP BILLING"}
export ENVIRONMENT=${ENVIRONMENT:-"production"}
export DEBUG=${DEBUG:-"false"}
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8000"}

exec gunicorn -k uvicorn.workers.UvicornWorker -w "${WORKERS:-2}" -b "${HOST}:${PORT}" app.main:app
