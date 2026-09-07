# Project Structure

```text
e_banking/
  backend/    Flask API, crypto engine, Supabase config, Python requirements
  frontend/   React/Vite application, UI screens, frontend package files
  database/   Supabase SQL setup files
  docs/       Guides, notes, and project documentation
```

## Run

From the app folder:

```powershell
cd e_banking
python app.py
```

This starts the local server at `https://localhost:5001` when `nginx/ssl/selfsigned.crt` and `nginx/ssl/selfsigned.key` are available.

From the frontend folder:

```powershell
cd e_banking/frontend
npm run dev
```

## Supabase

Paste `database/SUPABASE_NEW_DATABASE_SETUP.sql` into Supabase SQL Editor for a fresh database.

Backend secrets live in `backend/.env.backend`.
Frontend environment variables live in `frontend/.env`.
