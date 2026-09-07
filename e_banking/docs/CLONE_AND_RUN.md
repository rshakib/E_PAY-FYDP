# Clone And Run Guide

This guide explains how a new developer can clone and run the E-Payment project locally.

## 1. Required Software

Install these first:

```text
Python 3.11+
Node.js 18+
npm
Git
Supabase account
```

## 2. Clone The Project

```powershell
git clone <repository-url>
cd e_banking
```

The project is organized like this:

```text
e_banking/
  app.py
  backend/
  frontend/
  database/
  docs/
```

## 3. Create Supabase Database

Create a new Supabase project, then run the database setup SQL.

1. Open Supabase Dashboard.
2. Select your project.
3. Go to **SQL Editor**.
4. Open this project file:

```text
database/SUPABASE_NEW_DATABASE_SETUP.sql
```

5. Paste the full SQL content into Supabase SQL Editor.
6. Click **Run**.

Do not add seed data. The app creates users through registration.

## 4. Configure Backend Environment

Open:

```text
backend/.env.backend
```

Set these values from your Supabase project:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

The backend needs `SUPABASE_SERVICE_ROLE_KEY` because registration creates Supabase Auth users and inserts protected profile/account rows.

Optional, only if you want to run automatic database initialization instead of using SQL Editor:

```env
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_DB_HOST=your-database-host
SUPABASE_DB_PORT=5432
SUPABASE_DB_USER=postgres
```

## 5. Configure Frontend Environment

Open:

```text
frontend/.env
```

For the separate Vite development server, keep:

```env
VITE_BACKEND_URL=http://localhost:5001
```

If your backend runs on another port, update this value and restart the frontend dev server.

For the HTTPS sandbox or the one-command local Flask launcher, API calls are same-origin and stay on HTTPS.

## 6. Install Backend Dependencies

From the project root:

```powershell
cd backend
python -m pip install -r requirements.txt
cd ..
```

## 7. Install Frontend Dependencies

From the project root:

```powershell
cd frontend
npm install
cd ..
```

## 8. Run The App With Local HTTPS

From the project root:

```powershell
python app.py
```

On first run, this command builds the frontend if `frontend/dist` is missing. It uses the self-signed certificate from `../nginx/ssl`.

Expected app URL:

```text
https://localhost:5001
```

Your browser will show a self-signed certificate warning. Accept it only for local testing.

Health check:

```powershell
curl -k https://localhost:5001/health
```

Expected response:

```json
{"message":"E-Banking API is running","status":"ok"}
```

## 9. Optional Separate Frontend Dev Server

Use this only when you want Vite hot reload while editing the UI. Open a second terminal.

From the project root:

```powershell
cd frontend
npm run dev
```

Expected frontend URL:

```text
http://127.0.0.1:5173/
```

Open that URL in the browser.

The separate Vite development server is HTTP. For penetration testing the TLS surface, use `python app.py` or Docker Compose instead.

## 10. First User Flow

1. Open the frontend URL.
2. Click **I have an activation code**.
3. Enter NID/BRC, activation code, and bank username.
4. Continue through BP confirmation.
5. Create the private K2 password.
6. Log in with username and K2 password.
7. Register another user the same way.
8. Send money from one username to the other.

## 11. Important Security Notes

`backend/.env.backend` contains the Supabase service-role key. That key has admin-level database access.

For local academic/project use, the env files are required so a cloned project can run. If this repository becomes public, replace real keys with placeholder values before publishing.

## 12. Common Issues

### Backend says Supabase tables are missing

Run the full SQL file again:

```text
database/SUPABASE_NEW_DATABASE_SETUP.sql
```

Use Supabase SQL Editor, not Table Editor.

### Registration says service role key is missing

Check:

```text
backend/.env.backend
```

Make sure this exists and has a value:

```env
SUPABASE_SERVICE_ROLE_KEY=...
```

Restart the backend after editing it.

### Frontend cannot connect to backend

Check:

```text
frontend/.env
```

It should contain:

```env
VITE_BACKEND_URL=http://localhost:5001
```

Then restart:

```powershell
cd frontend
npm run dev
```

### Port 5001 is busy

The backend launcher chooses the next free port automatically. If it starts on a different port, update:

```text
frontend/.env
```

Then restart the frontend.

### Port 5173 is busy

Run:

```powershell
cd frontend
npm run dev -- --port 5174
```

## 13. Quick Command Summary

Terminal 1:

```powershell
cd e_banking
python app.py
```

Terminal 2:

```powershell
cd e_banking/frontend
npm run dev
```

Browser:

```text
http://127.0.0.1:5173/
```
