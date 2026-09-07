# Setup Guide — E-PAY (E-Banking System)

## Prerequisites

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/)
- **npm** (ships with Node.js)

---

## 1. Clone & Navigate

```bash
git clone <repo-url> E_PAY
cd E_PAY/e_banking
```

---

## 2. Backend — Install Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

**Packages installed:** Flask, flask-cors, pycryptodome, supabase, python-dotenv, gunicorn, psycopg2-binary

---

## 3. Frontend — Install Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## 4. Supabase Configuration

The app uses Supabase (cloud PostgreSQL) for all data. Open `backend/.env.backend` and set your credentials:

```env
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
```

> The repo includes a pre-configured project that may work as-is. If not, create a free project at [supabase.com](https://supabase.com) and copy your URL + keys here.

### Apply the Database Schema

**Option A** — Via Supabase Dashboard:
1. Log into [supabase.com](https://supabase.com)
2. Open your project → **SQL Editor**
3. Paste the contents of `database/SUPABASE_NEW_DATABASE_SETUP.sql` and run it

**Option B** — Via CLI (requires `SUPABASE_DB_PASSWORD` in `.env.backend`):
```bash
cd backend
python init_database.py
```

---

## 5. Run the Project

### Option A — Single Production-Like Server (Recommended)

```bash
cd e_banking
python app.py
```

This will:
- Auto-build the frontend if `frontend/dist/` is missing
- Start Flask on **https://localhost:5001** (uses `nginx/ssl/selfsigned.crt` for TLS)

Open **https://localhost:5001** in your browser.

> **Note:** The self-signed certificate will show a browser warning. On Windows, run this once to trust it:
> ```bash
> certutil -addstore -user Root nginx\ssl\selfsigned.crt
> ```

### Option B — Separate Dev Servers (Hot Reload)

**Terminal 1 — Backend:**
```bash
cd e_banking
set ENABLE_TLS=0
python backend/app.py
```
Runs on `http://localhost:5001`

**Terminal 2 — Frontend:**
```bash
cd e_banking/frontend
npm run dev
```
Runs on `http://localhost:5173` with hot reload

The frontend `.env` file sets `VITE_BACKEND_URL=http://localhost:5001` so API calls go to the Flask server.

---

## 6. Verify It Works

```bash
curl -k https://localhost:5001/health
```

Expected response:
```json
{
  "message": "E-Banking API is running",
  "status": "ok"
}
```

---

## 7. Running Tests

```bash
cd Testing

# Test 1 — Unit Crypto (pytest)
python -m pytest Test1_Unit_Crypto/test_crypto.py -v

# Test 2 — Integration Transaction Flow
python Test2_Integration_Transaction/test_transaction_flow.py

# Test 3 — Replay Attack Prevention
python Test3_Security_Replay/test_replay_attack.py
```

---

## Project Structure

```
E_PAY/
├── docker-compose.yml          ← Docker orchestration (alternative to local setup)
├── nginx/
│   ├── nginx.conf              ← TLS reverse proxy config
│   └── ssl/                    ← Self-signed certificates
├── e_banking/
│   ├── app.py                  ← Launcher script (builds frontend + starts Flask)
│   ├── backend/
│   │   ├── app.py              ← Flask API server
│   │   ├── crypto.py           ← AES/HMAC/PBKDF2 crypto engine
│   │   ├── supabase_config.py  ← Default Supabase credentials
│   │   ├── init_database.py    ← Schema deployment script
│   │   ├── requirements.txt    ← Python dependencies
│   │   └── .env.backend        ← Supabase credentials
│   ├── frontend/
│   │   ├── index.html           ← Vite entry point
│   │   ├── package.json         ← Node dependencies
│   │   ├── vite.config.ts       ← Vite configuration
│   │   └── src/                 ← React source code
│   └── database/
│       └── SUPABASE_NEW_DATABASE_SETUP.sql  ← Full DB schema
├── Testing/
│   ├── Test_Cases.xlsx          ← Detailed test case spreadsheet
│   ├── TEST_REPORT.md           ← Test execution report
│   ├── Test1_Unit_Crypto/
│   ├── Test2_Integration_Transaction/
│   └── Test3_Security_Replay/
└── SETUP.md                     ← This file
```

---

## Troubleshooting

| Problem | Likely Fix |
|---------|------------|
| `pip install` fails | Upgrade pip: `python -m pip install --upgrade pip` |
| Supabase connection error | Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env.backend` |
| Frontend blank page | Run `npm run build` in `frontend/` and restart Flask |
| Port 5001 in use | The launcher auto-selects 5002, etc. Check the console output |
| Browser shows cert warning | Trust the self-signed cert (see step 5 note) or set `ENABLE_TLS=0` |
| Transaction history 500 error | Known bug in `GET /transactions/<user>` — see `Testing/TEST_REPORT.md` |
