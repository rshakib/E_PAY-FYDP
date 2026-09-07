# Docker Sandbox Guide

This project can run as a Dockerized pentest target behind an Nginx TLS reverse proxy. The app container builds the React frontend, serves it through the Flask backend, and Nginx exposes the sandbox over HTTPS.

## Start The Sandbox

From the repository root:

```powershell
$env:SANDBOX_FAKE_DB="1"
docker compose up --build
```

Open:

```text
https://localhost
```

The TLS certificate is self-signed, so your browser will show a certificate warning. Accept it only for this local sandbox.

This is the recommended mode for penetration testing because HTTP is redirected to HTTPS by Nginx.
For safety, Nginx binds to `127.0.0.1`, so the sandbox is reachable from your PC only.
When `SANDBOX_FAKE_DB=1` is set, the backend uses in-memory fake users and does not use real Supabase data.

Health check:

```powershell
curl -k https://localhost/health
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

For penetration testing, prefer the fake sandbox variables from:

```text
e_banking/backend/.env.sandbox
```

The most important variable is:

```text
SANDBOX_FAKE_DB=1
```

The Docker frontend build uses same-origin API calls by default, so browser requests stay on HTTPS through Nginx.

For non-Docker local development, `frontend/.env` can still use:

```text
http://localhost:5001
```

To use another HTTPS host port:

```powershell
$env:NGINX_SSL_PORT="8443"
$env:VITE_BACKEND_URL=""
docker compose up --build
```

Then open:

```text
https://localhost:8443
```

## Reset The Sandbox

```powershell
docker compose down
docker compose up --build
```

## Local HTTPS Without Docker

From the app folder:

```powershell
cd e_banking
python app.py
```

This uses the same self-signed certificate files and starts:

```text
https://localhost:5001
```

If you explicitly need plain HTTP for debugging:

```powershell
$env:ENABLE_TLS="0"
python app.py
```

## Run OWASP ZAP Baseline

The compose file includes an optional ZAP service for baseline scanning.

```powershell
$env:SANDBOX_FAKE_DB="1"
docker compose --profile security-tools up --build zap
```

The report is written to:

```text
zap-reports/zap-baseline-report.html
```

## Notes For Penetration Testing

The app, Nginx, and security tooling share a private Docker network named `e-pay-sandbox`. From another container on that network, the HTTPS target URL is:

```text
https://nginx
```

From your host machine, the target URL is:

```text
https://localhost
```

## Run Organized Offline Tests

For the safest repeatable test pass, run the offline test runner:

```powershell
python tests/security/sandbox_pentest_runner.py
```

Reports are written to:

```text
reports/sandbox-pentest-latest.md
reports/sandbox-pentest-latest.json
```

See `e_banking/docs/PENTEST_SANDBOX_WORKFLOW.md` for the full workflow.
