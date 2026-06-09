# Docker Sandbox Guide

This project can run as a single Dockerized pentest target. The container builds the React frontend, serves it through the Flask backend, and exposes the app on port `5001`.

## Start The Sandbox

From the repository root:

```powershell
docker compose up --build
```

Open:

```text
http://localhost:5001
```

Health check:

```powershell
curl http://localhost:5001/health
```

Expected response:

```json
{"message":"E-Banking API is running","status":"ok"}
```

## Environment Files

Docker Compose loads backend secrets from:

```text
e_banking/backend/.env.backend
```

The frontend is built with this default backend URL:

```text
http://localhost:5001
```

To use another host port:

```powershell
$env:APP_PORT="8080"
$env:VITE_BACKEND_URL="http://localhost:8080"
docker compose up --build
```

## Reset The Sandbox

```powershell
docker compose down
docker compose up --build
```

## Run OWASP ZAP Baseline

The compose file includes an optional ZAP service for baseline scanning.

```powershell
docker compose --profile security-tools up --build zap
```

The report is written to:

```text
zap-reports/zap-baseline-report.html
```

## Notes For Penetration Testing

The app and security tooling share a private Docker network named `e-pay-sandbox`. From another container on that network, the target URL is:

```text
http://app:5001
```

From your host machine, the target URL is:

```text
http://localhost:5001
```
