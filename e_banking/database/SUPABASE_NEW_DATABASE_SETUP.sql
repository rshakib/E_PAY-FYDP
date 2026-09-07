-- E-Payment Supabase Database Setup
-- Paste this whole file into Supabase Dashboard -> SQL Editor -> New query -> Run.
--
-- Intended app flow:
-- 1. Bank-assisted registration with NID/BRC + activation code.
-- 2. K1 is derived from activation code, NID/BRC, username, and BP.
-- 3. K2 is derived from the user's private password with PBKDF2-SHA256.
-- 4. Money transfer sends AES-CBC encrypted M|F1 through the backend.
-- 5. Server verifies F1/F2 using HMAC(K1), checks receiver and balance, then records
--    success, futile, or aborted transaction states.
-- 6. Server sends notifications to sender and receiver when appropriate.
--
-- No seed/demo data is inserted by this file.
-- After running this file, update .env.backend with the new project's:
-- SUPABASE_URL, SUPABASE_KEY, and SUPABASE_SERVICE_ROLE_KEY.

create extension if not exists pgcrypto;

do $$
begin
  create type public.account_status as enum ('active', 'frozen', 'closed');
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create type public.account_type as enum ('personal', 'merchant', 'biller', 'staff');
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create type public.transaction_status as enum ('pending', 'success', 'futile', 'aborted', 'reversed');
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create type public.transaction_channel as enum ('user_transfer', 'merchant_payment', 'bill_payment', 'transport', 'utility', 'market', 'education');
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create type public.notification_type as enum (
    'registration',
    'login',
    'transfer_success',
    'transfer_futile',
    'transfer_aborted',
    'payment_success',
    'payment_futile',
    'payment_aborted',
    'security',
    'system'
  );
exception
  when duplicate_object then null;
end $$;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  registration_number text not null unique,
  password_hash text not null,
  password_key_k2 text not null,
  hmac_key_k1 text not null,
  fingerprint_bp text not null default '123456',
  timestamp_t timestamptz not null default now(),
  nid_brc_hash text not null,
  activation_code_hash text not null,
  daily_limit numeric(14, 2) not null default 5000.00,
  today_spent numeric(14, 2) not null default 0.00,
  last_spend_reset_date date not null default current_date,
  full_name text,
  phone_number text,
  email text,
  status public.account_status not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profiles_daily_limit_nonnegative check (daily_limit >= 0),
  constraint profiles_today_spent_nonnegative check (today_spent >= 0)
);

create table if not exists public.accounts (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  account_number text not null unique,
  account_type public.account_type not null default 'personal',
  balance numeric(14, 2) not null default 5000.00,
  currency text not null default 'BDT',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint accounts_balance_nonnegative check (balance >= 0)
);

create table if not exists public.registered_devices (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  device_label text,
  device_mac_hash text,
  device_fingerprint text,
  is_primary boolean not null default true,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.merchants_or_billers (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references public.profiles(id) on delete set null,
  account_id uuid references public.accounts(id) on delete set null,
  display_name text not null,
  merchant_code text not null unique,
  category public.transaction_channel not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.beneficiaries (
  id uuid primary key default gen_random_uuid(),
  owner_profile_id uuid not null references public.profiles(id) on delete cascade,
  beneficiary_profile_id uuid not null references public.profiles(id) on delete cascade,
  alias text,
  is_favorite boolean not null default false,
  created_at timestamptz not null default now(),
  unique (owner_profile_id, beneficiary_profile_id)
);

create table if not exists public.transactions (
  id uuid primary key default gen_random_uuid(),
  sender_account_id uuid references public.accounts(id) on delete set null,
  receiver_account_id uuid references public.accounts(id) on delete set null,
  merchant_id uuid references public.merchants_or_billers(id) on delete set null,
  amount numeric(14, 2) not null,
  currency text not null default 'BDT',
  status public.transaction_status not null,
  channel public.transaction_channel not null default 'user_transfer',
  failure_reason text,
  reference text not null unique,
  message_m text,
  hmac_f1 text,
  hmac_f2 text,
  previous_timestamp_t timestamptz,
  new_timestamp_t timestamptz,
  created_at timestamptz not null default now(),
  constraint transactions_amount_positive check (amount >= 0)
);

create table if not exists public.transaction_crypto_audit (
  id uuid primary key default gen_random_uuid(),
  transaction_id uuid references public.transactions(id) on delete cascade,
  profile_id uuid references public.profiles(id) on delete set null,
  payload_digest text,
  iv_digest text,
  hmac_verified boolean,
  replay_guard_timestamp timestamptz,
  event_note text,
  created_at timestamptz not null default now()
);

create table if not exists public.payment_requests (
  id uuid primary key default gen_random_uuid(),
  requester_profile_id uuid references public.profiles(id) on delete set null,
  payer_profile_id uuid references public.profiles(id) on delete set null,
  merchant_id uuid references public.merchants_or_billers(id) on delete set null,
  amount numeric(14, 2) not null,
  currency text not null default 'BDT',
  memo text,
  status public.transaction_status not null default 'pending',
  transaction_id uuid references public.transactions(id) on delete set null,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint payment_requests_amount_positive check (amount > 0)
);

create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  transaction_id uuid references public.transactions(id) on delete set null,
  payment_request_id uuid references public.payment_requests(id) on delete set null,
  notification_type public.notification_type not null default 'system',
  title text not null,
  message text not null,
  is_read boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.login_events (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid references public.profiles(id) on delete set null,
  registration_number text,
  success boolean not null,
  failure_reason text,
  created_at timestamptz not null default now()
);

create table if not exists public.staff_profiles (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid references auth.users(id) on delete set null,
  staff_code text not null unique,
  full_name text not null,
  role text not null default 'officer',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_profile_id uuid references public.profiles(id) on delete set null,
  actor_staff_id uuid references public.staff_profiles(id) on delete set null,
  action text not null,
  table_name text,
  row_id uuid,
  details jsonb,
  created_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

drop trigger if exists accounts_set_updated_at on public.accounts;
create trigger accounts_set_updated_at
before update on public.accounts
for each row execute function public.set_updated_at();

drop trigger if exists registered_devices_set_updated_at on public.registered_devices;
create trigger registered_devices_set_updated_at
before update on public.registered_devices
for each row execute function public.set_updated_at();

drop trigger if exists merchants_or_billers_set_updated_at on public.merchants_or_billers;
create trigger merchants_or_billers_set_updated_at
before update on public.merchants_or_billers
for each row execute function public.set_updated_at();

drop trigger if exists payment_requests_set_updated_at on public.payment_requests;
create trigger payment_requests_set_updated_at
before update on public.payment_requests
for each row execute function public.set_updated_at();

create index if not exists idx_profiles_registration_number on public.profiles (registration_number);
create index if not exists idx_profiles_status on public.profiles (status);
create index if not exists idx_accounts_profile_id on public.accounts (profile_id);
create index if not exists idx_accounts_account_number on public.accounts (account_number);
create index if not exists idx_accounts_is_active on public.accounts (is_active);
create index if not exists idx_registered_devices_profile on public.registered_devices (profile_id);
create index if not exists idx_merchants_code on public.merchants_or_billers (merchant_code);
create index if not exists idx_beneficiaries_owner on public.beneficiaries (owner_profile_id);
create index if not exists idx_transactions_sender on public.transactions (sender_account_id);
create index if not exists idx_transactions_receiver on public.transactions (receiver_account_id);
create index if not exists idx_transactions_status on public.transactions (status);
create index if not exists idx_transactions_created_at on public.transactions (created_at desc);
create index if not exists idx_notifications_profile on public.notifications (profile_id, created_at desc);
create index if not exists idx_notifications_unread on public.notifications (profile_id, is_read);
create index if not exists idx_payment_requests_payer on public.payment_requests (payer_profile_id, status);
create index if not exists idx_login_events_profile on public.login_events (profile_id, created_at desc);
create index if not exists idx_audit_logs_created_at on public.audit_logs (created_at desc);

alter table public.profiles enable row level security;
alter table public.accounts enable row level security;
alter table public.registered_devices enable row level security;
alter table public.merchants_or_billers enable row level security;
alter table public.beneficiaries enable row level security;
alter table public.transactions enable row level security;
alter table public.transaction_crypto_audit enable row level security;
alter table public.payment_requests enable row level security;
alter table public.notifications enable row level security;
alter table public.login_events enable row level security;
alter table public.staff_profiles enable row level security;
alter table public.audit_logs enable row level security;

-- The Flask backend should use SUPABASE_SERVICE_ROLE_KEY. The service role bypasses
-- RLS, so no anon insert/update policies are required for this backend-first design.
-- Minimal authenticated read policies are included for future direct Supabase clients.

drop policy if exists profiles_self_read on public.profiles;
create policy profiles_self_read on public.profiles
for select to authenticated
using (id = auth.uid());

drop policy if exists accounts_self_read on public.accounts;
create policy accounts_self_read on public.accounts
for select to authenticated
using (profile_id = auth.uid());

drop policy if exists notifications_self_read on public.notifications;
create policy notifications_self_read on public.notifications
for select to authenticated
using (profile_id = auth.uid());

drop policy if exists registered_devices_self_read on public.registered_devices;
create policy registered_devices_self_read on public.registered_devices
for select to authenticated
using (profile_id = auth.uid());

drop policy if exists beneficiaries_self_read on public.beneficiaries;
create policy beneficiaries_self_read on public.beneficiaries
for select to authenticated
using (owner_profile_id = auth.uid());

notify pgrst, 'reload schema';




--  JvM1nwXN9kO7yPH3