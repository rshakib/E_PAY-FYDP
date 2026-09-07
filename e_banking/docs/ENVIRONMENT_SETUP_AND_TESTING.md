# Environment Setup Guide

This guide explains how to prepare the environment for running the E-Banking / E-Payment system.

## 1. What You Need To Install

Install these tools before running the project:

| Tool | Recommended Version | Why It Is Needed |
| --- | --- | --- |
| Git | Latest stable | To clone and manage the project |
| Python | 3.11 or newer | To run the Flask backend |
| pip | Comes with Python | To install backend packages |
| Node.js | 18 or newer, 20 recommended | To run and build the React frontend |
| npm | Comes with Node.js | To install frontend packages |
| Docker Desktop | Latest stable | To run the project with Docker and Nginx |
| Supabase account | Cloud account | To create the database and authentication backend |

Check that the tools are installed:

```powershell
git --version
python --version
pip --version
node --version
npm --version
docker --version
```

## 2. Project Folder Overview

The main project folders are:

```text
e_banking/
  app.py
  backend/
  database/
  docs/
  frontend/
nginx/
docker-compose.yml
```

Important folders:

| Folder/File | Purpose |
| --- | --- |
| `e_banking/backend` | Flask backend code |
| `e_banking/frontend` | React frontend code |
| `e_banking/database` | Supabase SQL database setup file |
| `e_banking/app.py` | Local launcher for backend and built frontend |
| `docker-compose.yml` | Docker setup for app and Nginx |
| `nginx` | Nginx HTTPS reverse proxy configuration |

## 3. Clone Or Open The Project

If cloning for the first time:

```powershell
git clone <repository-url>
cd e_banking
```

If the project already exists on your computer, open the root folder that contains:

```text
docker-compose.yml
```

In this workspace, the root folder is:

```text
e:\UIU COURSE\10th tri\FYDP-I Section A\Web\e_banking
```

## 4. Backend Environment File

Create or edit this file:

```text
e_banking/backend/.env.backend
```

Add your Supabase values:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Explanation:

| Variable | Meaning |
| --- | --- |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side key used by the backend to create users and write protected rows |

The service-role key is required because the backend creates Supabase Auth users during registration.

Do not publish a real service-role key in a public repository.

## 5. Optional Backend Variables

You may also add these variables to `e_banking/backend/.env.backend` if needed:

```env
PORT=5001
ENABLE_TLS=1
AUTO_BUILD_FRONTEND=1
SANDBOX_FAKE_DB=0
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `PORT` | `5001` | Backend port |
| `ENABLE_TLS` | `1` | Runs local launcher with HTTPS if certificate files exist |
| `AUTO_BUILD_FRONTEND` | `1` | Builds the frontend automatically when `frontend/dist` is missing |
| `SANDBOX_FAKE_DB` | `0` | Uses fake in-memory data when set to `1` |

Use this only for local fake-data mode:

```env
SANDBOX_FAKE_DB=1
```

## 6. Database Setup Environment

The project uses Supabase/PostgreSQL.

First, create a Supabase project. Then run the SQL setup file:

```text
e_banking/database/SUPABASE_NEW_DATABASE_SETUP.sql
```

Steps:

1. Open Supabase Dashboard.
2. Select your project.
3. Open SQL Editor.
4. Open `e_banking/database/SUPABASE_NEW_DATABASE_SETUP.sql` from this project.
5. Copy the full SQL content.
6. Paste it into Supabase SQL Editor.
7. Run the SQL.

Optional variables for automatic database setup:

```env
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_DB_HOST=db.your-project-ref.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_USER=postgres
```

If these are configured, the database setup script can be run from:

```powershell
cd e_banking/backend
python init_database.py
```

If this command fails, use the manual Supabase SQL Editor method.

## 7. Frontend Environment File

Create or edit:

```text
e_banking/frontend/.env
```

For normal local frontend development, add:

```env
VITE_BACKEND_URL=http://localhost:5001
```

Explanation:

| Variable | Meaning |
| --- | --- |
| `VITE_BACKEND_URL` | Backend API URL used by the React frontend |

If the backend runs on a different port, update this value.

Example:

```env
VITE_BACKEND_URL=http://localhost:5002
```

For Docker/Nginx HTTPS mode, this value can be empty because frontend and backend use the same origin:

```env
VITE_BACKEND_URL=
```

## 8. Install Backend Dependencies

From the project root:

```powershell
cd e_banking/backend
python -m pip install -r requirements.txt
cd ../..
```

This installs packages such as Flask, Supabase client, Gunicorn, dotenv, and cryptography dependencies.

## 9. Install Frontend Dependencies

From the project root:

```powershell
cd e_banking/frontend
npm install
cd ../..
```

For a clean install using the lock file:

```powershell
cd e_banking/frontend
npm ci
cd ../..
```

## 10. Build The Frontend

The backend can serve the frontend only after the frontend is built.

Run:

```powershell
cd e_banking/frontend
npm run build
cd ../..
```

After the build, this folder should exist:

```text
e_banking/frontend/dist
```

## 11. Run Locally With The Python Launcher

This is the easiest local setup because one command serves the backend and the built frontend.

From the inner app folder:

```powershell
cd e_banking
python app.py
```

Default URL:

```text
https://localhost:5001
```

Notes:

| Situation | What Happens |
| --- | --- |
| Frontend build is missing | The launcher tries to build it automatically |
| TLS certificate exists | The app starts with HTTPS |
| TLS certificate is missing | The app starts with HTTP |
| Port `5001` is busy | The launcher tries the next available port |

To run without HTTPS:

```powershell
$env:ENABLE_TLS="0"
cd e_banking
python app.py
```

## 12. Run Frontend And Backend Separately

Use this setup while editing the frontend.

Terminal 1, start backend:

```powershell
cd e_banking/backend
python app.py
```

Backend URL:

```text
http://localhost:5001
```

Terminal 2, start frontend:

```powershell
cd e_banking/frontend
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173/
```

Make sure `e_banking/frontend/.env` has:

```env
VITE_BACKEND_URL=http://localhost:5001
```

## 13. Run With Docker

Docker builds the frontend, installs backend dependencies, runs the backend with Gunicorn, and exposes the app through Nginx.

From the project root:

```powershell
docker compose up --build
```

Default Docker URLs:

```text
http://localhost
https://localhost
```

The HTTPS certificate is self-signed, so the browser may show a warning.

To run Docker with fake local data:

```powershell
$env:SANDBOX_FAKE_DB="1"
docker compose up --build
```

To use custom ports:

```powershell
$env:NGINX_PORT="8080"
$env:NGINX_SSL_PORT="8443"
docker compose up --build
```

Then open:

```text
https://localhost:8443
```

To stop Docker:

```powershell
docker compose down
```

## 14. Recommended Setup Order

Follow this order for a clean setup:

1. Install Git, Python, Node.js, npm, Docker, and create a Supabase account.
2. Clone or open the project.
3. Create `e_banking/backend/.env.backend`.
4. Add Supabase backend values.
5. Create the Supabase database using `SUPABASE_NEW_DATABASE_SETUP.sql`.
6. Create `e_banking/frontend/.env`.
7. Set `VITE_BACKEND_URL=http://localhost:5001`.
8. Install backend dependencies.
9. Install frontend dependencies.
10. Build the frontend.
11. Run the project using `python app.py` or Docker.

## 15. Common Setup Problems

### Backend says Supabase tables are missing

Run this SQL file again in Supabase SQL Editor:

```text
e_banking/database/SUPABASE_NEW_DATABASE_SETUP.sql
```

### Registration fails because service role is missing

Check this file:

```text
e_banking/backend/.env.backend
```

Make sure it contains:

```env
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Restart the backend after editing the file.

### Frontend cannot connect to backend

Check:

```text
e_banking/frontend/.env
```

It should contain:

```env
VITE_BACKEND_URL=http://localhost:5001
```

Restart the frontend after changing `.env`.

### Frontend build folder is missing

Run:

```powershell
cd e_banking/frontend
npm install
npm run build
```

### Port 5001 is already used

Use another port:

```powershell
$env:PORT="5002"
cd e_banking
python app.py
```

Then update frontend `.env`:

```env
VITE_BACKEND_URL=http://localhost:5002
```

### Docker port 80 or 443 is already used

Use custom Docker ports:

```powershell
$env:NGINX_PORT="8080"
$env:NGINX_SSL_PORT="8443"
docker compose up --build
```

## 16. Final Environment Checklist

Before running the system, confirm:

| Item | Done |
| --- | --- |
| Python 3.11 or newer installed | |
| Node.js installed | |
| npm installed | |
| Docker installed | |
| Supabase project created | |
| Supabase SQL setup file executed | |
| `e_banking/backend/.env.backend` created | |
| `SUPABASE_URL` added | |
| `SUPABASE_KEY` added | |
| `SUPABASE_SERVICE_ROLE_KEY` added | |
| `e_banking/frontend/.env` created | |
| `VITE_BACKEND_URL` configured | |
| Backend dependencies installed | |
| Frontend dependencies installed | |
| Frontend build created | |
