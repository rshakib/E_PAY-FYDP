# Missing Features Report: MVP to Full Production Specification

This report defines the structural gaps between the currently implemented MVP screens and the final production-ready features. It provides the database schemas, backend APIs, and integrations required for full implementation.

---

## 🗄️ Database Schema Requirements

To transition from client-side mock lists and local state toggles to persistent, database-backed configurations, the following tables and columns must be created or updated in Supabase:

### 1. `public.unpaid_bills` (New Table)
Stores dynamic unpaid invoice statements for users:
```sql
create table public.unpaid_bills (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid references public.profiles(id) on delete cascade,
    biller_code text not null, -- e.g., 'DESCO', 'WASA'
    invoice_number text not null unique,
    amount numeric(14, 2) not null,
    due_date date not null,
    is_paid boolean not null default false,
    created_at timestamptz not null default now()
);
```

### 2. `public.merchants_or_billers` (New Table)
Maintains registry details for verified business entities:
```sql
create table public.merchants_or_billers (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid references public.profiles(id) on delete set null,
    display_name text not null,
    merchant_code text not null unique,
    category text not null, -- e.g., 'retail', 'utility', 'education'
    avatar_color text not null default 'bg-blue-100 text-blue-600',
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);
```

### 3. `public.user_devices` (New Table)
Tracks authenticated device login events:
```sql
create table public.user_devices (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid references public.profiles(id) on delete cascade,
    device_name text not null,
    device_type text not null, -- 'mobile' | 'desktop'
    ip_address text not null,
    location text,
    is_primary boolean not null default false,
    last_active timestamptz not null default now()
);
```

### 4. `public.profiles` (New Columns)
Add preference and biometrics flags to the standard profile:
```sql
alter table public.profiles 
add column if not exists display_name text,
add column if not exists avatar_url text,
add column if not exists fingerprint_enabled boolean not null default false,
add column if not exists face_id_enabled boolean not null default false,
add column if not exists theme_preference text not null default 'light',
add column if not exists language_preference text not null default 'en',
add column if not exists transaction_alerts boolean not null default true,
add column if not exists email_alerts boolean not null default false;
```

---

## 🔌 Backend API Specifications

The following backend endpoints must be added to the Flask API (`backend/app.py`) to serve dynamic content:

### 1. Merchant Payments
*   `GET /api/merchants`
    *   *Purpose:* Retrieves a list of active verified merchants.
    *   *Response:* `{"status": "success", "merchants": [{"name": "Amazon Store", "username": "merchant_store", ...}]}`
*   `GET /api/merchants/search?q=<query>`
    *   *Purpose:* Filters merchants registry in real-time.

### 2. Mobile Recharge
*   `GET /api/recharge/operators`
    *   *Purpose:* Returns supported operators list and active BDT recharge presets.

### 3. Bill Payments
*   `GET /api/bills`
    *   *Purpose:* Queries outstanding invoices for the authenticated user from `unpaid_bills`.
*   `POST /api/bills/pay`
    *   *Purpose:* Commits bill payments, updates invoice status to `is_paid = true`, and records ledger entries.

### 4. User Profile
*   `POST /api/user/avatar`
    *   *Purpose:* Handles multipart image uploads, saves files in Supabase Storage buckets, and updates `avatar_url` in the profile.
*   `GET /api/user/devices`
    *   *Purpose:* Returns a list of active sessions from `user_devices`.
*   `POST /api/user/devices/revoke`
    *   *Purpose:* Revokes access tokens and deletes device rows.

### 5. Settings
*   `GET /api/user/preferences`
    *   *Purpose:* Fetches saved theme, language, and notification states.
*   `POST /api/user/preferences`
    *   *Purpose:* Updates user preference columns in the database.

---

## ⚡ Integration Specifications

### 1. Payment Gateway Integrations
*   **Mobile Operators:** Integrate with commercial airtime recharge APIs (e.g., Grameenphone, Robi bulk top-up gateways) using SOAP/REST web services to commit top-ups.
*   **Utility Providers:** Connect with biller hubs (DESCO, WASA, Titas Gas) to query real-time customer account balances and post payment clearances.

### 2. WebAuthn Biometric API
*   Replace local state switches with standard browser WebAuthn credentials enrollment:
    *   Use navigator.credentials.create() to register public keys with biometric touch ID or Face ID sensors.
    *   Verify public keys on login/transfers.

### 3. Front-End Dark Theme
*   Define global CSS variables in `index.css` for light/dark properties (e.g. `--background`, `--text`).
*   Inject the `dark` class on the `<html>` node when settings load `theme_preference == 'dark'`.
