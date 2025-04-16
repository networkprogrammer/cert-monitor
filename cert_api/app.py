from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import psycopg2
from datetime import datetime, timezone
import os

app = Flask(__name__)

# Define Prometheus metrics
cert_expiry_days = Gauge('cert_expiry_days', 'Days until certificate expiry', ['domain'])
alerts_metric = Gauge('cert_alerts', 'Certificate Alerts', ['domain', 'alert_type', 'timestamp'])

def update_metrics():
    conn = psycopg2.connect(dbname="certwatch", user="certuser", password=os.getenv("POSTGRES_PASSWORD"), host="cert-db")
    cursor = conn.cursor()

    # Fetch domains and their metrics from the database
    cursor.execute("""
        SELECT DISTINCT ON (domain) domain, expiry_date, fingerprint 
        FROM certificates 
        WHERE cert_type = 'leaf' 
        ORDER BY domain, last_checked DESC
    """)
    rows = cursor.fetchall()

    for row in rows:
        domain, expiry_date, fingerprint = row
        now = datetime.now(timezone.utc)

        # Ensure expiry_date is timezone-aware
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)

        days_to_expiry = (expiry_date - now).days

        # Update metrics dynamically
        cert_expiry_days.labels(domain=domain).set(days_to_expiry)

    cursor.close()
    conn.close()

@app.route('/')
def home():
    return "Certificate Monitoring API is running."

@app.route('/metrics')
def metrics():
    # Update metrics dynamically
    update_metrics()

    # Expose Prometheus metrics
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)

@app.route('/alerts-metrics')
def alerts_metrics():
    conn = psycopg2.connect(dbname="certwatch", user="certuser", password=os.getenv("POSTGRES_PASSWORD"), host="cert-db")
    cursor = conn.cursor()

    # Fetch all alerts from the database
    cursor.execute("SELECT domain, alert_type, created_at FROM alerts")
    rows = cursor.fetchall()

    # Clear existing metrics
    alerts_metric.clear()

    # Populate the metric with alert data
    for row in rows:
        domain, alert_type, timestamp = row
        alerts_metric.labels(domain=domain, alert_type=alert_type, timestamp=timestamp).set(1)

    cursor.close()
    conn.close()

    return Response(generate_latest(alerts_metric), content_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)