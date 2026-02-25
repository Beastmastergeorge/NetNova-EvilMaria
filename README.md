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
