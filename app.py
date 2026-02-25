from __future__ import annotations

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "netnova.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "netnova-evil-maria-demo"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                plan TEXT NOT NULL,
                monthly_rate REAL NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'unpaid',
                created_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS monitor_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                expected_latency_ms INTEGER NOT NULL,
                last_latency_ms INTEGER,
                last_seen TEXT,
                health TEXT NOT NULL DEFAULT 'unknown'
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(node_id) REFERENCES monitor_nodes(id)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                target TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        existing_customers = conn.execute("SELECT COUNT(*) AS count FROM customers").fetchone()["count"]
        if existing_customers == 0:
            conn.executemany(
                """
                INSERT INTO customers (name, plan, monthly_rate, phone, email, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    ("Acme Fiber Park", "Enterprise 2Gbps", 850.0, "+1-202-555-0111", "noc@acmefiber.example", "active"),
                    ("Blue Wave Campus", "Business 1Gbps", 490.0, "+1-202-555-0122", "it@bluewave.example", "active"),
                    ("North Ridge Hospital", "Dedicated 5Gbps", 1900.0, "+1-202-555-0133", "ops@northridge.example", "active"),
                ],
            )

        existing_nodes = conn.execute("SELECT COUNT(*) AS count FROM monitor_nodes").fetchone()["count"]
        if existing_nodes == 0:
            conn.executemany(
                """
                INSERT INTO monitor_nodes (name, region, expected_latency_ms, health)
                VALUES (?, ?, ?, ?)
                """,
                [
                    ("Edge Router Alpha", "Metro Core", 15, "healthy"),
                    ("Backhaul Link Orion", "Northern Ring", 28, "healthy"),
                    ("Tower POP Delta", "Coastal Zone", 22, "healthy"),
                ],
            )


def run_monitor_cycle() -> dict:
    now = datetime.utcnow().isoformat(timespec="seconds")
    alerts_created = 0

    with get_connection() as conn:
        nodes = conn.execute("SELECT * FROM monitor_nodes").fetchall()
        for node in nodes:
            jitter = random.randint(-5, 45)
            measured_latency = max(3, node["expected_latency_ms"] + jitter)
            if measured_latency > node["expected_latency_ms"] + 30:
                health = "critical"
                severity = "critical"
                message = f"{node['name']} latency spike to {measured_latency}ms in {node['region']}"
            elif measured_latency > node["expected_latency_ms"] + 15:
                health = "degraded"
                severity = "warning"
                message = f"{node['name']} is degraded at {measured_latency}ms"
            else:
                health = "healthy"
                severity = "info"
                message = f"{node['name']} is stable at {measured_latency}ms"

            conn.execute(
                """
                UPDATE monitor_nodes
                SET last_latency_ms = ?, last_seen = ?, health = ?
                WHERE id = ?
                """,
                (measured_latency, now, health, node["id"]),
            )

            should_alert = severity in {"warning", "critical"}
            if should_alert:
                conn.execute(
                    """
                    INSERT INTO alerts (node_id, severity, message, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (node["id"], severity, message, now),
                )
                alerts_created += 1

        conn.commit()

    return {"ran_at": now, "alerts_created": alerts_created}


@app.get("/")
def dashboard():
    with get_connection() as conn:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS customers,
                COALESCE(SUM(monthly_rate), 0) AS monthly_mrr
            FROM customers
            WHERE status = 'active'
            """
        ).fetchone()

        receivables = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS open_receivables
            FROM invoices
            WHERE status = 'unpaid'
            """
        ).fetchone()

        customers = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
        invoices = conn.execute(
            """
            SELECT i.*, c.name AS customer_name
            FROM invoices i
            JOIN customers c ON c.id = i.customer_id
            ORDER BY i.created_at DESC
            LIMIT 8
            """
        ).fetchall()
        nodes = conn.execute("SELECT * FROM monitor_nodes ORDER BY id").fetchall()
        alerts = conn.execute(
            """
            SELECT a.*, n.name AS node_name
            FROM alerts a
            JOIN monitor_nodes n ON n.id = a.node_id
            ORDER BY a.created_at DESC
            LIMIT 12
            """
        ).fetchall()

    return render_template(
        "dashboard.html",
        totals=totals,
        receivables=receivables,
        customers=customers,
        invoices=invoices,
        nodes=nodes,
        alerts=alerts,
    )


@app.post("/customers")
def create_customer():
    name = request.form["name"].strip()
    plan = request.form["plan"].strip()
    monthly_rate = float(request.form["monthly_rate"])
    phone = request.form["phone"].strip()
    email = request.form["email"].strip()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO customers (name, plan, monthly_rate, phone, email, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            """,
            (name, plan, monthly_rate, phone, email),
        )
        conn.commit()

    flash(f"Customer {name} onboarded into NetNova billing.", "success")
    return redirect(url_for("dashboard"))


@app.post("/invoices")
def create_invoice():
    customer_id = int(request.form["customer_id"])
    amount = float(request.form["amount"])
    due_days = int(request.form.get("due_days", 14))
    due_date = (datetime.utcnow() + timedelta(days=due_days)).date().isoformat()
    created_at = datetime.utcnow().isoformat(timespec="seconds")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO invoices (customer_id, amount, due_date, status, created_at)
            VALUES (?, ?, ?, 'unpaid', ?)
            """,
            (customer_id, amount, due_date, created_at),
        )
        conn.commit()

    flash("Invoice generated and queued for payment collection.", "success")
    return redirect(url_for("dashboard"))


@app.post("/notifications")
def create_notification():
    channel = request.form["channel"]
    target = request.form["target"].strip()
    message = request.form["message"].strip()
    created_at = datetime.utcnow().isoformat(timespec="seconds")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO notifications (channel, target, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (channel, target, message, created_at),
        )
        conn.commit()

    flash(f"EVIL MARIA sent a {channel} notification to {target}.", "success")
    return redirect(url_for("dashboard"))


@app.post("/api/monitor/run")
def monitor_run_api():
    result = run_monitor_cycle()
    return jsonify(result)


@app.get("/api/alerts/latest")
def latest_alerts_api():
    with get_connection() as conn:
        alerts = conn.execute(
            """
            SELECT a.id, a.severity, a.message, a.created_at, n.name AS node_name
            FROM alerts a
            JOIN monitor_nodes n ON n.id = a.node_id
            WHERE a.acknowledged = 0
            ORDER BY a.created_at DESC
            LIMIT 5
            """
        ).fetchall()

    return jsonify([dict(row) for row in alerts])


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5050)
