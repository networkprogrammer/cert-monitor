# 🔒 SSL/TLS Certificate Monitoring – Docker-Based System (No Node.js/NPM)

## 📌 Project Name
**docker-cert-monitor**

---

## 🎯 Objective

Develop a **fully self-hosted certificate monitoring system** that:
- Monitors domains for certificate expiration and CA/root CA changes
- Stores history and exposes it via REST API
- Displays a web dashboard (pure Flask + Jinja2 templates)
- Sends alerts via email
- Exposes metrics to Prometheus for Grafana dashboards

> ❌ **No use of Node.js or NPM**.  
> ✅ **Entirely Python + Flask + Bootstrap + Docker**.

---

## 🧱 Architecture

```text
+---------------------+
| Cron Scheduler      | (in Docker)
+--------+------------+
         |
         v
+--------+------------+      +------------------+
|  Python Scanner     | ---> |  PostgreSQL DB    |
+--------+------------+      +------------------+
         |
         v
+---------------------+      +-------------------+
| Flask Web + API     | ---> |  Prometheus /     |
| (Jinja2 templates)  |      |  Grafana Dashboard|
+---------------------+      +-------------------+
         |
         v
+---------------------+
| Alerts: Email       |
+---------------------+
```

---

## 🔧 Core Features

### ✅ Certificate Monitoring
- Use Python `ssl` and `cryptography` modules
- Connect to domain on port 443
- Extract and store:
  - Expiry date
  - Issuer name
  - Intermediate + Root CA fingerprints
- Compare against last scan
- Store history in PostgreSQL
- Schedule via `cron` (inside Docker)

### 📬 Alert System
- Trigger alert when:
  - Expiry date is within threshold (default 30 days)
  - Issuer or CA fingerprint changes
- Send alerts via:
  - Email (SMTP)
- Configurable via `config.yaml` or `.env`

### 🌐 Flask Web UI + REST API
- Jinja2 templated frontend (no React/JS framework)
- REST Endpoints:
  - `/api/history` – full scan logs
  - `/api/status` – most recent scan
  - `/api/alerts` – alert logs
- HTML Pages:
  - Dashboard view
  - Certificate chain viewer
  - Alerts and historical logs

### 📊 Prometheus Integration
- Flask app exposes `/metrics` for:
  - `cert_expiry_days{domain=...}`
  - `cert_fingerprint_changed`
- Grafana dashboards for:
  - Certificate expiry heatmap
  - Domain scan status
  - CA changes over time

---

## 📁 Folder Structure

```
docker-cert-monitor/
├── cert_monitor/
│   ├── main.py
│   ├── scanner.py
│   ├── db.py
│   ├── notifier.py
│   ├── metrics.py
│   └── config.yaml
├── cert_api/
│   ├── app.py
│   ├── routes.py
│   ├── templates/
│   │   ├── dashboard.html
│   │   ├── history.html
│   │   └── alerts.html
├── db/init.sql
├── prometheus/prometheus.yml
├── grafana/provisioning/
│   ├── dashboards/
│   └── datasources/
├── cron/crontab
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
```

---

## ⚙️ Configuration

### `.env`
```env
POSTGRES_DB=certwatch
POSTGRES_USER=certuser
POSTGRES_PASSWORD=certpass
SMTP_USER=alerts@yourdomain.com
SMTP_PASS=yourpass
```

### `config.yaml`
```yaml
domains:
  - name: example.com
  - name: internal.example.net
expire_threshold_days: 30
alert_channels:
  email:
    enabled: true
    smtp_host: smtp.mail.com
    smtp_port: 587
    from: alerts@yourdomain.com
    to: yourteam@yourdomain.com
```

---

## 🐳 Dockerized Services

| Service      | Description                          |
|--------------|--------------------------------------|
| cert-scanner | Python scanner + alert system        |
| cert-db      | PostgreSQL for history & config      |
| cert-api     | Flask UI/API/metrics + Jinja templates |
| cert-cron    | Cron trigger for scans               |
| prometheus   | Scrapes metrics from Flask API       |
| grafana      | Visualizes cert status and trends    |

---

## 📊 Prometheus Setup

### `prometheus/prometheus.yml`
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cert_monitor'
    static_configs:
      - targets: ['cert-api:5000']
```

---

## 📈 Grafana Dashboard Panels

- **Cert Expiry Countdown**
- **Changed Issuers / Root CA**
- **Domain Scan History**
- **Certificate Alerts Over Time**

---

## 🚀 Getting Started

1. Clone repo and create `.env`
2. Add domains in `config.yaml`
3. Run:

```bash
docker-compose up --build
```

All services will start:
- Flask UI at `http://localhost:5000`
- Grafana at `http://localhost:3000`
- Prometheus at `http://localhost:9090`

---

## ✅ Done. No Node. No NPM. No React.
All UI built with:
- Flask
- Jinja2
- Bootstrap (via CDN)