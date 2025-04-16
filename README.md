# Docker-Cert-Monitor

## Overview
Docker-Cert-Monitor is a fully self-hosted SSL/TLS certificate monitoring system. It is designed to monitor domains for certificate expiration, issuer changes, and root CA changes. The system is built entirely using Python, Flask, and Docker, with no reliance on Node.js or NPM.

## Features
- **Certificate Monitoring**: Extracts and stores certificate details such as expiry date, issuer, and fingerprints.
- **Alert System**: Sends alerts via email for certificate expiry or changes in issuer/CA.
- **REST API**: Exposes endpoints for certificate history, status, and alerts.
- **Prometheus Integration**: Provides metrics for Grafana dashboards.
- **Web Dashboard**: Displays certificate status and history using Flask and Jinja2 templates.

## Architecture
The system consists of the following components:
- **Cert Scanner**: A Python-based scanner that retrieves and analyzes SSL/TLS certificates.
- **Database**: PostgreSQL for storing certificate details and alert logs.
- **Flask API**: Provides REST endpoints and serves the web dashboard.
- **Prometheus**: Scrapes metrics from the Flask API.
- **Grafana**: Visualizes certificate status and trends.

## Folder Structure
```

├── cert_monitor/
│   ├── cleanup.py
│   ├── config.yaml
│   ├── db.py
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── scanner.py
├── cert_api/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── routes.py
│   ├── templates/
│   │   ├── dashboard.html
├── cron/
│   ├── crontab
│   ├── Dockerfile
├── db/
│   ├── init.sql
├── grafana/
│   ├── provisioning/
│   │   ├── dashboards/
│   │   │   ├── cert-monitor-dashboard.json
│   │   │   ├── dashboard.yml
│   │   ├── datasources/
│   │   │   ├── datasource.yml
├── prometheus/
│   ├── prometheus.yml
├── docker-compose.yml
├── project-requirements.md
├── README.md
├── test.py
```

## Configuration
### `.env`
```env
POSTGRES_DB=certwatch
POSTGRES_USER=certuser
POSTGRES_PASSWORD=certpass
GRAFANA_PASSWORD=adminpass
```

### `config.yaml`
```yaml
domains:
  - name: www.example.com
  - name: www.github.com
expire_threshold_days: 90
cleanup_days: 7
cleanup_enabled: true
alert_channels:
  email:
    enabled: true
    smtp_host: smtp.example.com
    smtp_port: 587
    from: alerts@example.com
    to: team@example.com
    send_email: true
```

## Usage
1. Clone the repository and create a `.env` file with the required configuration.
2. Add domains to monitor in `config.yaml`.
3. Build and start the Docker containers:
   ```bash
   docker-compose up --build
   ```
4. Access the services:
   - Flask API: `http://localhost:5000`
   - Grafana: `http://localhost:3000`
   - Prometheus: `http://localhost:9090`

## REST API Endpoints
- `/metrics`: For metrics.
- `/alerts-metrics`: Provides alert data for Prometheus.

## Prometheus Metrics
- `cert_expiry_days{domain=...}`: Days until certificate expiry.

## Grafana Dashboard
The Grafana dashboard includes panels for:
- Certificate expiry countdown.
- Domain scan history.
- Certificate alerts over time.
- Fired Alerts table panel displaying alerts grouped by `domain`, `alert_type`, and `timestamp`.

## Running the Cleanup Container

The `db-cleanup` container is designed to clean up old entries from the database based on the configuration in `config.yaml`. To run the cleanup container manually, follow these steps:

1. Ensure the `db-cleanup` container is built by running:
   ```bash
   docker-compose build db-cleanup
   ```

2. Trigger the cleanup process by starting the container:
   ```bash
   docker-compose start db-cleanup
   ```

This will execute the `cleanup.py` script and clean up the database according to the `cleanup_days` and `cleanup_enabled` settings in `config.yaml`. The container will exit automatically after completing the cleanup process.

## License
This project is licensed under the MIT License.