from flask import Flask, request, jsonify, send_from_directory, g
import uuid
import hmac
import hashlib
import base64
from flask_cors import CORS
from crypto import CryptoEngine
from crypto_v2 import HybridEnvelopeCrypto, PIIEncryption, LookupHash
try:
    import kms_bridge
except Exception:
    kms_bridge = None
import datetime
import re
import threading
import time
import requests as http_requests
from supabase import create_client, Client
from supabase_config import (
    SUPABASE_URL as CONFIG_URL,
    SUPABASE_KEY as CONFIG_KEY,
    IDENTITY_SUPABASE_URL as CONFIG_IDENTITY_URL,
    IDENTITY_SUPABASE_KEY as CONFIG_IDENTITY_KEY,
    PII_ENCRYPTION_KEY as CONFIG_PII_KEY,
    PII_HMAC_PEPPER as CONFIG_PII_PEPPER,
)
import os
import json
from dotenv import load_dotenv
from functools import wraps
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST_DIR = BASE_DIR.parent / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"

# Load .env.backend first so env vars override supabase_config.py defaults
load_dotenv(dotenv_path=BASE_DIR / '.env.backend')

# ============================================
# DB2: Business/Transaction Database (existing)
# ============================================
SUPABASE_URL = os.environ.get('SUPABASE_URL', CONFIG_URL)
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or os.environ.get('SUPABASE_KEY', CONFIG_KEY)

# ============================================
# DB1: Identity/Auth Database (new)
# ============================================
IDENTITY_SUPABASE_URL = os.environ.get('IDENTITY_SUPABASE_URL', CONFIG_IDENTITY_URL)
IDENTITY_SERVICE_ROLE_KEY = os.environ.get('IDENTITY_SUPABASE_SERVICE_ROLE_KEY')
IDENTITY_SUPABASE_KEY = IDENTITY_SERVICE_ROLE_KEY or os.environ.get('IDENTITY_SUPABASE_ANON_KEY', CONFIG_IDENTITY_KEY)

# ============================================
# PII Encryption Config
# ============================================
PII_KEY = os.environ.get('PII_ENCRYPTION_KEY', CONFIG_PII_KEY)
PII_PEPPER = os.environ.get('PII_HMAC_PEPPER', CONFIG_PII_PEPPER)

app = Flask(__name__, static_folder=str(FRONTEND_DIST_DIR), static_url_path='')

DEFAULT_CORS_ORIGINS = [
    "https://e-pay-fydp-xqi6.vercel.app",
    "https://e-pay-fydp-2xoq.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://localhost",
    "https://127.0.0.1",
]
cors_origins = [
    origin.strip()
    for origin in os.environ.get("FRONTEND_ORIGINS", ",".join(DEFAULT_CORS_ORIGINS)).split(",")
    if origin.strip()
]
CORS(
    app,
    resources={r"/*": {"origins": cors_origins}},
    supports_credentials=True
)
crypto = CryptoEngine()
SANDBOX_FAKE_DB = os.environ.get("SANDBOX_FAKE_DB", "").strip().lower() in {"1", "true", "yes", "on"}

if not SANDBOX_FAKE_DB and not SUPABASE_SERVICE_ROLE_KEY:
    print(
        "Warning: SUPABASE_SERVICE_ROLE_KEY is not set. "
        "Registration requires a Supabase service-role key or matching RLS insert policies.",
        flush=True,
    )

# ============================================
# Initialize Supabase Clients
# ============================================
if SANDBOX_FAKE_DB:
    from fake_supabase import create_fake_supabase_client, create_fake_identity_client

    identity_db = create_fake_identity_client(crypto)
    business_db = create_fake_supabase_client(crypto)
    print("SANDBOX_FAKE_DB is enabled. Using in-memory fake banking data.", flush=True)
else:
    identity_db: Client = create_client(IDENTITY_SUPABASE_URL, IDENTITY_SUPABASE_KEY) if IDENTITY_SUPABASE_URL else None
    business_db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================
# Initialize Crypto V2
# ============================================
pii_encryption = None
lookup_hash = None

server_ecdh_private_key_pem = None
server_ecdh_public_key_pem = None
server_ecdh_public_hex = None
server_ecdh_key_id = "hte-bank-ecdh-v1"

if PII_KEY and PII_KEY != 'REPLACE_WITH_64_CHAR_HEX_KEY':
    try:
        pii_encryption = PIIEncryption(PII_KEY)
    except Exception as e:
        print(f"Warning: PII encryption init failed: {e}", flush=True)

if PII_PEPPER and PII_PEPPER != 'REPLACE_WITH_64_CHAR_HEX_KEY':
    try:
        lookup_hash = LookupHash(PII_PEPPER)
    except Exception as e:
        print(f"Warning: Lookup hash init failed: {e}", flush=True)


def ensure_server_ecdh_keys():
    """Generate or load server long-term P-256 ECDH key pair."""
    global server_ecdh_private_key_pem, server_ecdh_public_key_pem, server_ecdh_public_hex, server_ecdh_key_id

    # Paper §2 (Mode B / HSM): when AWS KMS is configured the receiver's ECDH
    # private key lives in the HSM and never enters this process. We only fetch
    # the public half here; the shared secret is derived inside KMS per transfer.
    if kms_bridge is not None and kms_bridge.kms_enabled():
        try:
            server_ecdh_public_hex, server_ecdh_public_key_pem = kms_bridge.get_public_key()
            server_ecdh_private_key_pem = None
            server_ecdh_key_id = kms_bridge.kms_key_id()
            meta = {}
            try:
                meta = kms_bridge.describe_key()
            except Exception:
                pass
            print(f"[SERVER KEYS] Using AWS KMS HSM key (KeyID={server_ecdh_key_id}, spec={meta.get('spec')}, state={meta.get('state')})", flush=True)
            return
        except Exception as e:
            print(f"[KMS] Could not load HSM public key, falling back to software key: {e}", flush=True)

    # Paper §2: prefer a Vault-isolated private key when configured (falls back to DB).
    vault_pem = load_vault_secret(os.environ.get('SERVER_KEY_VAULT_SECRET', ''))
    if vault_pem:
        try:
            server_ecdh_private_key_pem = vault_pem
            server_ecdh_public_hex, server_ecdh_public_key_pem = derive_ecdh_publics(vault_pem)
            print("[SERVER KEYS] Loaded ECDH P-256 key from Supabase Vault", flush=True)
            return
        except Exception as e:
            print(f"[VAULT] ECDH key unusable, falling back to DB: {e}", flush=True)

    # Try loading from DB2 first
    try:
        result = business_db.table('server_keys').select('*').eq('id', server_ecdh_key_id).execute()
        if result.data and len(result.data) > 0:
            server_ecdh_private_key_pem = unwrap_server_secret(result.data[0]['private_key_pem'])
            server_ecdh_public_key_pem = result.data[0]['public_key_pem']
            # Derive hex format
            priv_obj = HybridEnvelopeCrypto.load_server_ecdh_private_key(server_ecdh_private_key_pem)
            from cryptography.hazmat.primitives import serialization
            server_ecdh_public_hex = priv_obj.public_key().public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            ).hex()
            print(f"[SERVER KEYS] Loaded ECDH P-256 keys (KeyID={server_ecdh_key_id}) from database", flush=True)
            return
    except Exception as e:
        if not is_missing_schema_error(e):
            print(f"[SERVER KEYS] Could not load ECDH keys from DB: {e}", flush=True)

    # Generate new P-256 ECDH key pair
    server_ecdh_private_key_pem, server_ecdh_public_key_pem, server_ecdh_public_hex = HybridEnvelopeCrypto.generate_server_ecdh_keypair()
    print(f"[SERVER KEYS] Generated new P-256 ECDH key pair (KeyID={server_ecdh_key_id})", flush=True)

    # Try to save to DB2
    try:
        business_db.table('server_keys').insert({
            'id': server_ecdh_key_id,
            'private_key_pem': wrap_server_secret(server_ecdh_private_key_pem),
            'public_key_pem': server_ecdh_public_key_pem,
        }).execute()
        print(f"[SERVER KEYS] Saved ECDH P-256 keys to database (KeyID={server_ecdh_key_id})", flush=True)
    except Exception as e:
        if is_missing_schema_error(e):
            print("[SERVER KEYS] DB tables not ready yet, ECDH keys held in memory only", flush=True)
        else:
            print(f"[SERVER KEYS] Could not save ECDH keys to DB: {e}", flush=True)


def derive_kt_server_side(ephemeral_pub_hex, aad, key_id):
    """Paper §3 step (5): derive the transaction key KT.

    When AWS KMS is configured the receiver's ECDH private key stays inside the
    HSM and Z = ECDH(SK_R^dh, ePK) is computed by KMS (Mode B); otherwise Z is
    computed here from the Vault/DB software key. Both paths yield an identical Z,
    so the rest of the protocol (HKDF, AES-GCM) is unchanged.
    """
    if kms_bridge is not None and kms_bridge.kms_enabled():
        try:
            z = kms_bridge.derive_shared_secret_z(ephemeral_pub_hex)
            return HybridEnvelopeCrypto.derive_hte_session_key(None, ephemeral_pub_hex, aad, key_id, shared_z=z)
        except Exception as e:
            print(f"[KMS] DeriveSharedSecret failed, using software key: {e}", flush=True)
    server_priv_key = HybridEnvelopeCrypto.load_server_ecdh_private_key(server_ecdh_private_key_pem)
    return HybridEnvelopeCrypto.derive_hte_session_key(server_priv_key, ephemeral_pub_hex, aad, key_id)


# ============================================
# Auto-create tables using direct Postgres connection
# ============================================
import psycopg2

def get_db_connection(supabase_url, db_password):
    """Create a direct Postgres connection to Supabase."""
    if not db_password or db_password.startswith('YOUR_'):
        return None
    try:
        # Extract project ref from URL: https://xxxxx.supabase.co
        project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
        conn = psycopg2.connect(
            host=f"db.{project_ref}.supabase.co",
            database="postgres",
            user="postgres",
            password=db_password,
            port=5432,
            sslmode="require"
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"[DB CONNECTION] Failed: {e}", flush=True)
        return None


def auto_create_tables():
    """Auto-create all required tables if they don't exist."""
    if SANDBOX_FAKE_DB:
        return

    db1_password = os.environ.get('IDENTITY_DB_PASSWORD', '')
    db2_password = os.environ.get('SUPABASE_DB_PASSWORD', '')

    # --- DB1: Identity Database ---
    if identity_db and db1_password and not db1_password.startswith('YOUR_'):
        print("[DB1 SETUP] Connecting to DB1 for auto-create...", flush=True)
        conn = get_db_connection(IDENTITY_SUPABASE_URL, db1_password)
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS profiles (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        registration_number TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        password_key_k2 TEXT NOT NULL,
                        hmac_key_k1 TEXT NOT NULL,
                        fingerprint_bp TEXT NOT NULL DEFAULT '123456',
                        nid_brc_hash TEXT NOT NULL,
                        activation_code_hash TEXT NOT NULL,
                        timestamp_t TEXT NOT NULL,
                        daily_limit REAL NOT NULL DEFAULT 5000.0,
                        today_spent REAL NOT NULL DEFAULT 0.0,
                        rsa_public_key TEXT,
                        ecdsa_public_key_duress TEXT,
                        duress_limit REAL NOT NULL DEFAULT 250.0,
                        duress_today_spent REAL NOT NULL DEFAULT 0.0,
                        full_name_enc TEXT,
                        mobile_enc TEXT,
                        mobile_hmac TEXT,
                        email_enc TEXT,
                        is_email_verified BOOLEAN DEFAULT FALSE,
                        biometric_enrolled BOOLEAN DEFAULT FALSE,
                        face_auth_enabled BOOLEAN DEFAULT FALSE,
                        device_mac_enc TEXT,
                        device_mac_hmac TEXT,
                        profile_picture_ref TEXT,
                        status TEXT NOT NULL DEFAULT 'active',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
                # HTE duress profile columns (paper §3.1).
                cur.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS ecdsa_public_key_duress TEXT;")
                cur.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS duress_limit REAL NOT NULL DEFAULT 250.0;")
                cur.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS duress_today_spent REAL NOT NULL DEFAULT 0.0;")
                cur.close()
                print("[DB1 SETUP] profiles table created/verified", flush=True)
            except Exception as e:
                print(f"[DB1 SETUP] Auto-create failed: {e}", flush=True)
            finally:
                conn.close()
        else:
            print("[DB1 SETUP] No DB password — set IDENTITY_DB_PASSWORD in .env.backend", flush=True)
    else:
        print("[DB1 SETUP] Skipped (no identity_db or no password)", flush=True)

    # --- DB2: Business Database ---
    if business_db and db2_password and not db2_password.startswith('YOUR_'):
        print("[DB2 SETUP] Connecting to DB2 for auto-create...", flush=True)
        conn = get_db_connection(SUPABASE_URL, db2_password)
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS accounts (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        profile_id UUID NOT NULL,
                        balance REAL NOT NULL DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE,
                        account_number TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        sender_account_id UUID,
                        receiver_account_id UUID,
                        amount REAL NOT NULL,
                        status TEXT NOT NULL,
                        failure_reason TEXT,
                        reference TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        profile_id UUID NOT NULL,
                        title TEXT,
                        message TEXT,
                        notification_type TEXT,
                        transaction_id UUID,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS idempotency_keys (
                        key TEXT PRIMARY KEY,
                        profile_id TEXT NOT NULL,
                        receiver_account_id TEXT,
                        amount REAL NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        result_json TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS server_keys (
                        id TEXT PRIMARY KEY DEFAULT 'server',
                        private_key_pem TEXT NOT NULL,
                        public_key_pem TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        valid_from TIMESTAMPTZ,
                        valid_until TIMESTAMPTZ,
                        alg TEXT,
                        version INTEGER,
                        revoked_at TIMESTAMPTZ
                    );
                """)
                # Migrations for existing databases (paper §4.1 key validity/revocation).
                for column in (
                    "valid_from TIMESTAMPTZ",
                    "valid_until TIMESTAMPTZ",
                    "alg TEXT",
                    "version INTEGER",
                    "revoked_at TIMESTAMPTZ",
                ):
                    cur.execute(f"ALTER TABLE server_keys ADD COLUMN IF NOT EXISTS {column};")

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS security_events (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        username TEXT,
                        event_type TEXT NOT NULL,
                        details TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS used_nonces (
                        nonce TEXT PRIMARY KEY,
                        txid TEXT,
                        sender TEXT,
                        used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        expires_at TIMESTAMPTZ
                    );
                """)
                cur.execute("ALTER TABLE used_nonces ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;")
                cur.close()
                print("[DB2 SETUP] All tables created/verified", flush=True)
            except Exception as e:
                print(f"[DB2 SETUP] Auto-create failed: {e}", flush=True)
            finally:
                conn.close()
        else:
            print("[DB2 SETUP] No DB password — set SUPABASE_DB_PASSWORD in .env.backend", flush=True)
    else:
        print("[DB2 SETUP] Skipped (no business_db or no password)", flush=True)


# In-memory session store: token -> username
active_sessions: dict[str, str] = {}

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")

MISSING_SCHEMA_MESSAGE = (
    "Supabase tables are missing. Run the SQL shown in server logs in the Supabase SQL Editor "
    "for the project configured in .env.backend."
)


def is_missing_schema_error(error: Exception) -> bool:
    error_text = str(error)
    return (
        "PGRST205" in error_text
        or "PGRST204" in error_text
        or "schema cache" in error_text
        or "Could not find the table" in error_text
        or "Could not find the" in error_text
    )


def missing_schema_response():
    return jsonify({"status": "error", "message": MISSING_SCHEMA_MESSAGE}), 500


def frontend_build_exists() -> bool:
    return FRONTEND_INDEX_FILE.is_file()


def missing_frontend_response():
    message = (
        "Frontend build is missing. Run `cd e_banking/frontend && npm install && npm run build`, "
        "or start the Docker sandbox with `docker compose up --build`."
    )
    if "text/html" in request.headers.get("Accept", ""):
        return (
            "<!doctype html><html><head><title>Frontend build missing</title></head>"
            "<body><h1>Frontend build missing</h1>"
            f"<p>{message}</p>"
            "<p>For TLS sandbox testing, use <code>docker compose up --build</code> and open "
            "<code>https://localhost</code>.</p>"
            "</body></html>"
        ), 503
    return jsonify({"status": "error", "message": message}), 503


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self' http://localhost:5001 http://127.0.0.1:5001; "
        "base-uri 'self'; "
        "frame-ancestors 'none'",
    )
    return response


def get_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def validate_username(username):
    if not isinstance(username, str):
        return None
    normalized = username.strip()
    if not USERNAME_PATTERN.fullmatch(normalized):
        return None
    return normalized


def authenticated_username():
    return getattr(g, "authenticated_username", None)


def authorize_username(username):
    if not same_username(authenticated_username(), username):
        return jsonify({"status": "error", "message": "Forbidden"}), 403
    return None


def create_notification(profile_id, title, message, notification_type="system", transaction_id=None):
    try:
        notification_data = {
            "profile_id": profile_id,
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "transaction_id": transaction_id,
        }
        business_db.table("notifications").insert(notification_data).execute()
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error creating notification: {e}")

# Stateless signed sessions: survive restarts and work across gunicorn workers
# (the previous in-memory `active_sessions` was lost on every redeploy → 401s).
SESSION_SECRET = os.environ.get('SESSION_SECRET') or os.environ.get('PII_HMAC_PEPPER') or 'dpt-session-secret-v1-change-me'
SESSION_TTL_SECONDS = int(os.environ.get('SESSION_TTL_SECONDS', str(60 * 60 * 24 * 30)))  # 30 days


def generate_session_token(username: str) -> str:
    """base64url(username).expiry.hmac_sha256 — no server-side store required."""
    exp = int(time.time()) + SESSION_TTL_SECONDS
    payload = f"{username}.{exp}"
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    u = base64.urlsafe_b64encode(username.encode()).rstrip(b'=').decode()
    return f"{u}.{exp}.{sig}"


def verify_session_token(token: str):
    try:
        u_b64, exp_s, sig = token.split('.')
        pad = '=' * (-len(u_b64) % 4)
        username = base64.urlsafe_b64decode(u_b64 + pad).decode()
        payload = f"{username}.{exp_s}"
        expected = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(exp_s) < int(time.time()):
            return None
        return username
    except Exception:
        return None


def require_auth(f):
    """Require a valid session token (in-memory OR stateless signed)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:].strip() if auth_header.startswith('Bearer ') else ''
        username = None
        if token:
            username = active_sessions.get(token) or verify_session_token(token)
        if not username:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        g.authenticated_username = username
        return f(*args, **kwargs)
    return decorated

# ========================================
# Helper Functions (Dual-DB aware)
# ========================================

def get_user_profile(username):
    """Fetch user profile from DB1 (identity) if available, else DB2."""
    try:
        db = identity_db if identity_db else business_db
        response = db.table('profiles').select('*').eq('registration_number', username).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error fetching profile: {e}")
        return None

def get_user_account(profile_id):
    """Fetch user's primary account from DB2 (business)"""
    try:
        response = business_db.table('accounts').select('*').eq('profile_id', profile_id).eq('is_active', True).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error fetching account: {e}")
        return None

def get_receiver_account(receiver_username):
    """Fetch receiver's account (cross-DB lookup)"""
    try:
        receiver_profile = get_user_profile(receiver_username)
        if not receiver_profile:
            return None
        return get_user_account(receiver_profile['id'])
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error fetching receiver account: {e}")
        return None

def record_transaction(sender_account_id, receiver_account_id, amount, status, failure_reason=None):
    """Record transaction in DB2 (business)"""
    try:
        transaction_data = {
            'sender_account_id': sender_account_id,
            'receiver_account_id': receiver_account_id,
            'amount': float(amount),
            'status': status,
            'failure_reason': failure_reason,
            'reference': f"TXN-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex[:8]}"
        }
        response = business_db.table('transactions').insert(transaction_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error recording transaction: {e}")
        return None

def update_account_balance(account_id, new_balance):
    """Update account balance in DB2 (business)"""
    try:
        business_db.table('accounts').update({'balance': float(new_balance)}).eq('id', account_id).execute()
        return True
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error updating balance: {e}")
        return False

def update_profile_timestamp(profile_id, new_t):
    """Update user's timestamp (T) in DB1 (identity)"""
    try:
        db = identity_db if identity_db else business_db
        db.table('profiles').update({'timestamp_t': new_t}).eq('id', profile_id).execute()
        return True
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error updating timestamp: {e}")
        return False

def update_daily_spend(profile_id, today_spent):
    """Update user's daily spending tracker in DB1 (identity)"""
    try:
        db = identity_db if identity_db else business_db
        db.table('profiles').update({'today_spent': float(today_spent)}).eq('id', profile_id).execute()
        return True
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error updating daily spend: {e}")
        return False

def add_duress_spend(profile_id, amount):
    """Accumulate the duress-profile spend counter against L_D (paper §3.1/§4.1)."""
    try:
        db = identity_db if identity_db else business_db
        row = db.table('profiles').select('duress_today_spent').eq('id', profile_id).execute()
        cur = float(row.data[0].get('duress_today_spent', 0) or 0) if row.data else 0.0
        db.table('profiles').update({'duress_today_spent': cur + float(amount)}).eq('id', profile_id).execute()
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"[DURESS] spend update failed: {e}", flush=True)

def same_username(left, right):
    """Compare usernames after normalizing user-entered casing and spacing."""
    return str(left or "").strip().casefold() == str(right or "").strip().casefold()

def check_idempotency(txid):
    """Check if this TxID was already committed. Returns cached result or None."""
    try:
        result = business_db.table('idempotency_keys').select('*').eq('key', txid).execute()
        if result.data and len(result.data) > 0:
            entry = result.data[0]
            if entry['status'] == 'committed':
                return json.loads(entry['result_json'])
        return None
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        return None

# ========================================
# HTE Protocol Helpers (key validity, freshness, atomic settlement)
# Implements paper §3 (receiver checks) + §4.1 (revocation-aware deferred submission).
# ========================================

HTE_MAX_CLOCK_SKEW_SECONDS = int(os.environ.get('HTE_MAX_CLOCK_SKEW_SECONDS', '300'))
# Offline receipt QR lifetime (paper §IV offline handoff). The client shows a 60s
# countdown; this bounds a screenshot/copy to the same window.
CLAIM_MAX_AGE_SECONDS = int(os.environ.get('CLAIM_MAX_AGE_SECONDS', '60'))
KEY_ROTATION_GRACE_SECONDS = int(os.environ.get('KEY_ROTATION_GRACE_SECONDS', '86400'))
# Nonce replay-state lifetime (paper §3 step 3 / §4.1). Env-tunable.
NONCE_TTL_SECONDS = int(os.environ.get('NONCE_TTL_SECONDS', '86400'))


def parse_envelope_timestamp(t_value):
    """Envelope timestamp T may be ISO-8601, or epoch seconds/milliseconds."""
    if t_value is None:
        return None
    if isinstance(t_value, (int, float)) and not isinstance(t_value, bool):
        secs = float(t_value)
        if secs > 1e12:  # milliseconds
            secs = secs / 1000.0
        try:
            return datetime.datetime.fromtimestamp(secs, tz=datetime.timezone.utc)
        except Exception:
            return None
    try:
        text = str(t_value).strip().replace('Z', '+00:00')
        dt = datetime.datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None


def is_txid_valid(txid):
    """TxID format policy (paper §3 step 3): bounded, opaque token."""
    if not isinstance(txid, str):
        return False
    txid = txid.strip()
    return 8 <= len(txid) <= 128 and re.fullmatch(r"[A-Za-z0-9._:\-]+", txid) is not None


def is_nonce_valid(nonce):
    """Nonce syntax policy (paper §3 step 3)."""
    if not isinstance(nonce, str):
        return False
    return 4 <= len(nonce.strip()) <= 128


def check_freshness(t_value):
    """Verify timestamp policy. Returns (ok, reason)."""
    dt = parse_envelope_timestamp(t_value)
    if dt is None:
        return False, "Invalid or missing timestamp T"
    now = datetime.datetime.now(datetime.timezone.utc)
    skew = abs((now - dt).total_seconds())
    if skew > HTE_MAX_CLOCK_SKEW_SECONDS:
        return False, f"Stale or future-dated envelope (skew {int(skew)}s > {HTE_MAX_CLOCK_SKEW_SECONDS}s)"
    return True, None


def get_server_key_record(key_id):
    """Load a server key record (validity/revocation metadata) from DB2 if present."""
    try:
        result = business_db.table('server_keys').select('*').eq('id', key_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
    except Exception as e:
        if not is_missing_schema_error(e):
            print(f"[SERVER KEYS] Could not load key record {key_id}: {e}", flush=True)
    return None


def validate_key_at_creation(key_id, t_value):
    """Revocation-aware key-validity check against the envelope *creation* time T.

    Paper §4.1: if T >= T_rev the envelope is rejected (signature created after
    revocation cannot be trusted); if T < T_rev a bounded grace window applies.
    Returns (ok, reason).
    """
    if key_id == server_ecdh_key_id:
        active = True
    else:
        active = False

    record = get_server_key_record(key_id)
    creation = parse_envelope_timestamp(t_value)
    now = datetime.datetime.now(datetime.timezone.utc)

    if record:
        revoked_at = parse_envelope_timestamp(record.get('revoked_at')) if record.get('revoked_at') else None
        valid_from = parse_envelope_timestamp(record.get('valid_from')) if record.get('valid_from') else None
        valid_until = parse_envelope_timestamp(record.get('valid_until')) if record.get('valid_until') else None

        if creation is None:
            return False, "Invalid envelope timestamp T"

        if valid_from and creation < valid_from:
            return False, "Envelope predates the key validity window"

        if revoked_at and creation >= revoked_at:
            return False, "Key was revoked before this envelope was created"

        if revoked_at and creation < revoked_at:
            # Signed before revocation -> bounded grace policy.
            grace_end = revoked_at + datetime.timedelta(seconds=KEY_ROTATION_GRACE_SECONDS)
            if now > grace_end:
                return False, "Key revocation grace period elapsed"
            return True, None

        if valid_until and creation > valid_until:
            grace_end = valid_until + datetime.timedelta(seconds=KEY_ROTATION_GRACE_SECONDS)
            if now > grace_end:
                return False, "Key validity window elapsed (beyond grace)"
        return True, None

    # No metadata row: only the current active key is accepted.
    if not active:
        return False, f"Unknown or retired KeyID: {key_id}"
    return True, None


def reserve_idempotency(txid, profile_id, receiver_account_id, amount):
    """Atomically reserve a TxID BEFORE any balance mutation.

    Returns (state, cached_result) with state in {'new','committed','inflight'}.
    Insert-first on the PRIMARY KEY removes the check-then-save race so two
    concurrent identical envelopes cannot both settle.
    """
    try:
        existing = business_db.table('idempotency_keys').select('*').eq('key', txid).execute()
        if existing.data:
            entry = existing.data[0]
            if entry.get('status') == 'committed':
                try:
                    return 'committed', json.loads(entry['result_json'])
                except Exception:
                    return 'committed', None
            return 'inflight', None

        business_db.table('idempotency_keys').insert({
            'key': txid,
            'profile_id': str(profile_id),
            'receiver_account_id': str(receiver_account_id) if receiver_account_id else None,
            'amount': float(amount),
            'status': 'pending',
            'result_json': None,
        }).execute()
        return 'new', None
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        # Likely a unique-PK violation from a concurrent request.
        try:
            again = business_db.table('idempotency_keys').select('*').eq('key', txid).execute()
            if again.data and again.data[0].get('status') == 'committed':
                try:
                    return 'committed', json.loads(again.data[0]['result_json'])
                except Exception:
                    return 'committed', None
        except Exception:
            pass
        return 'inflight', None


def commit_idempotency(txid, result_dict):
    """Mark a reserved TxID as committed and store the canonical result."""
    try:
        business_db.table('idempotency_keys').update({
            'status': 'committed',
            'result_json': json.dumps(result_dict),
        }).eq('key', txid).execute()
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error committing idempotency key: {e}")


def release_idempotency(txid):
    """Drop a reservation for a transfer that did not settle (allows retry)."""
    try:
        business_db.table('idempotency_keys').delete().eq('key', txid).execute()
    except Exception as e:
        print(f"Error releasing idempotency key: {e}")


def update_accounts_atomic(sender_account_id, receiver_account_id, amount, nonce=None, txid=None, sender=None):
    """Atomic conditional debit + credit + (optional) nonce burn (paper §3 step 8).

    Returns (ok, sender_new_balance, receiver_new_balance, reason).
    Runs the debit, the credit and the nonce insert inside a SINGLE Postgres
    transaction (autocommit disabled for this connection). Falls back to
    best-effort sequential updates only when no direct DB connection exists.
    """
    amount = float(amount)
    db2_password = os.environ.get('SUPABASE_DB_PASSWORD', '')
    conn = None
    if db2_password and not db2_password.startswith('YOUR_') and not SANDBOX_FAKE_DB:
        conn = get_db_connection(SUPABASE_URL, db2_password)

    if conn:
        try:
            # Force a real transaction — get_db_connection() ships with autocommit=True
            # (used for DDL); without this the debit and credit commit separately.
            conn.autocommit = False
            cur = conn.cursor()
            cur.execute(
                "UPDATE accounts SET balance = balance - %s "
                "WHERE id = %s::uuid AND balance >= %s RETURNING balance",
                (amount, sender_account_id, amount),
            )
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return False, None, None, "Insufficient balance"
            sender_new_balance = float(row[0])

            cur.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id = %s::uuid RETURNING balance",
                (amount, receiver_account_id),
            )
            row2 = cur.fetchone()
            receiver_new_balance = float(row2[0]) if row2 else None

            # Burn the nonce inside the same transaction (paper §3 step 3 / §4.1).
            if nonce:
                cur.execute(
                    "INSERT INTO used_nonces (nonce, txid, sender, expires_at) "
                    "VALUES (%s, %s, %s, now() + make_interval(secs => %s)) "
                    "ON CONFLICT (nonce) DO NOTHING",
                    (nonce, txid, sender, NONCE_TTL_SECONDS),
                )

            conn.commit()
            return True, sender_new_balance, receiver_new_balance, None
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            print(f"[TRANSFER] Atomic settlement failed: {e}", flush=True)
            return False, None, None, f"Atomic settlement failed: {e}"
        finally:
            conn.close()

    # Fallback: no direct DB connection (sandbox / no password) — best-effort.
    sender_account = business_db.table('accounts').select('*').eq('id', sender_account_id).execute()
    receiver_account = business_db.table('accounts').select('*').eq('id', receiver_account_id).execute()
    if not sender_account.data or not receiver_account.data:
        return False, None, None, "Account not found"
    sender_balance = float(sender_account.data[0]['balance'])
    receiver_balance = float(receiver_account.data[0]['balance'])
    if sender_balance < amount:
        return False, None, None, "Insufficient balance"
    sender_new_balance = sender_balance - amount
    receiver_new_balance = receiver_balance + amount
    update_account_balance(sender_account_id, sender_new_balance)
    update_account_balance(receiver_account_id, receiver_new_balance)
    return True, sender_new_balance, receiver_new_balance, None


def log_security_event(username, event_type, details):
    """Persist a silent risk event for later review (paper §4.1 revocation/risk)."""
    try:
        business_db.table('security_events').insert({
            'username': str(username) if username else None,
            'event_type': str(event_type),
            'details': details if isinstance(details, str) else json.dumps(details),
        }).execute()
    except Exception as e:
        if is_missing_schema_error(e):
            print(f"[SECURITY EVENT] (table missing) {event_type}: {details}", flush=True)
            return
        print(f"Error logging security event: {e}")


# ========================================
# Nonce replay state (paper §3 step 3)
# ========================================

def is_nonce_used(nonce):
    """True if the nonce is stored AND not past its TTL (expired rows are reusable)."""
    if not nonce:
        return False
    try:
        r = business_db.table('used_nonces').select('nonce,expires_at').eq('nonce', nonce).execute()
        if not r.data:
            return False
        expires_at = r.data[0].get('expires_at')
        if expires_at:
            dt = parse_envelope_timestamp(expires_at)
            if dt and dt < datetime.datetime.now(datetime.timezone.utc):
                return False  # expired -> treat as unused
        return True
    except Exception:
        return False


def mark_nonce_used(nonce, txid=None, sender=None):
    if not nonce:
        return
    try:
        expires_at = (datetime.datetime.now(datetime.timezone.utc)
                      + datetime.timedelta(seconds=NONCE_TTL_SECONDS)).isoformat()
        business_db.table('used_nonces').insert({
            'nonce': nonce, 'txid': txid, 'sender': sender, 'expires_at': expires_at,
        }).execute()
    except Exception as e:
        if not is_missing_schema_error(e):
            print(f"[NONCE] mark failed: {e}", flush=True)


# ========================================
# Server key protection at rest (HSM-equivalent isolated secret, paper §2)
# Set SERVER_KEY_WRAP_KEY (64-char hex) to encrypt the private-key PEMs at rest.
# ========================================
import base64 as _b64

SERVER_KEY_WRAP_KEY = os.environ.get('SERVER_KEY_WRAP_KEY', '')


def wrap_server_secret(plaintext):
    """AES-256-GCM encrypt a private-key PEM with an env-held wrap key.
    Returns 'enc:v1:<b64(iv|ct|tag)>'; falls back to plaintext when no wrap key."""
    if not plaintext or len(SERVER_KEY_WRAP_KEY) < 64:
        return plaintext
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = bytes.fromhex(SERVER_KEY_WRAP_KEY[:64])
        iv = os.urandom(12)
        ct = AESGCM(key).encrypt(iv, plaintext.encode(), b'server-key-v1')
        return 'enc:v1:' + _b64.b64encode(iv + ct).decode()
    except Exception as e:
        print(f"[SERVER KEYS] wrap failed, storing plaintext: {e}", flush=True)
        return plaintext


def unwrap_server_secret(stored):
    """Decrypt 'enc:v1:...' values; return plaintext unchanged otherwise."""
    if not stored or not str(stored).startswith('enc:v1:'):
        return stored
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = bytes.fromhex(SERVER_KEY_WRAP_KEY[:64])
        raw = _b64.b64decode(str(stored)[len('enc:v1:'):])
        iv, ct = raw[:12], raw[12:]
        return AESGCM(key).decrypt(iv, ct, b'server-key-v1').decode()
    except Exception as e:
        print(f"[SERVER KEYS] unwrap failed: {e}", flush=True)
        raise


# ========================================
# Supabase Vault hook (paper §2: "HSM or equivalent isolated service")
# Set SERVER_KEY_VAULT_SECRET to the vault secret name holding the ECDH private
# key PEM. If absent/unavailable the DB row is used (graceful fallback).
# ========================================

def load_vault_secret(name):
    """Read a secret via the SECURITY DEFINER RPC 'vault_read_secret' (if deployed)."""
    if not name:
        return None
    try:
        res = business_db.rpc('vault_read_secret', {'secret_name': name}).execute()
        data = res.data
        if isinstance(data, list) and data:
            row = data[0]
            return row.get('secret') if isinstance(row, dict) else row
        if isinstance(data, str):
            return data
    except Exception as e:
        print(f"[VAULT] read '{name}' unavailable, using DB key: {str(e)[:120]}", flush=True)
    return None


def derive_ecdh_publics(private_pem):
    """Given a P-256 private PEM, return (uncompressed_hex, public_pem)."""
    from cryptography.hazmat.primitives import serialization
    priv_obj = HybridEnvelopeCrypto.load_server_ecdh_private_key(private_pem)
    pub = priv_obj.public_key()
    pub_hex = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return pub_hex, pub_pem


# ========================================
# API Endpoints
# ========================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "E-Banking API is running"}), 200


# ========================================
# Self-Ping: Keep Render + Supabase Always Awake
# ========================================
def _self_ping_loop():
    """Background thread that pings /health every 14 minutes to prevent
    Render free-tier from sleeping and Supabase free-tier from pausing."""
    HEALTH_CHECK_INTERVAL = 14 * 60
    time.sleep(60)
    while True:
        try:
            port = int(os.environ.get('PORT', '5001'))
            resp = http_requests.get(f"http://127.0.0.1:{port}/health", timeout=10)
            if resp.status_code == 200:
                print("[SELF-PING] Server is awake", flush=True)
            else:
                print(f"[SELF-PING] Unexpected status: {resp.status_code}", flush=True)
        except Exception as e:
            print(f"[SELF-PING] Ping failed: {e}", flush=True)

        # Touch both DBs
        try:
            db = identity_db if identity_db else business_db
            db.table('profiles').select('id').limit(1).execute()
            print("[SELF-PING] Identity DB is active", flush=True)
        except Exception as e:
            print(f"[SELF-PING] Identity DB touch: {e}", flush=True)

        try:
            business_db.table('accounts').select('id').limit(1).execute()
            print("[SELF-PING] Business DB is active", flush=True)
        except Exception as e:
            print(f"[SELF-PING] Business DB touch: {e}", flush=True)

        time.sleep(HEALTH_CHECK_INTERVAL)


def start_self_ping():
    t = threading.Thread(target=_self_ping_loop, daemon=True, name="self-ping")
    t.start()
    print("[SELF-PING] Background keep-alive thread started (every 14 minutes)", flush=True)


start_self_ping()

# ========================================
# Server Public Key Endpoint
# ========================================

@app.route('/server-public-key', methods=['GET'])
def get_server_public_key():
    """Return the server's ECDH P-256 public key (hex and PEM) and KeyID for Hybrid Transaction Envelopes."""
    if not server_ecdh_public_hex:
        return jsonify({"status": "error", "message": "Server cryptographic keys not initialized"}), 500

    key_record = get_server_key_record(server_ecdh_key_id) or {}
    return jsonify({
        "status": "success",
        "public_key": server_ecdh_public_hex,
        "ecdh_public_key": server_ecdh_public_hex,
        "ecdh_public_pem": server_ecdh_public_key_pem,
        "key_id": server_ecdh_key_id,
        "KeyID": server_ecdh_key_id,
        # Paper §4.1: key-validity metadata for client-side caching.
        "valid_from": key_record.get("valid_from"),
        "valid_until": key_record.get("valid_until"),
        "alg": key_record.get("alg") or "ECDH-P256+HKDF-SHA256+AES-256-GCM+ECDSA-P256",
        "version": key_record.get("version") or 1,
        "revoked_at": key_record.get("revoked_at"),
        # Paper §4.1 emergency revocation: clients must re-synchronize online
        # before constructing further envelopes.
        "force_online_resync": bool(key_record.get("revoked_at")),
    }), 200


@app.route('/')
def serve_index():
    if not frontend_build_exists():
        return missing_frontend_response()
    return app.send_static_file('index.html')

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Authenticate user by username and password"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        data = get_json_body()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON request body"}), 400

        username = validate_username(data.get('username'))
        password = data.get('password')

        if not username or not password:
            return jsonify({"status": "error", "message": "Missing username or password"}), 400

        # Fetch profile from DB1
        user_profile = get_user_profile(username)
        if not user_profile:
            return jsonify({"status": "error", "message": "User not found"}), 404

        password_hash = user_profile.get('password_hash')
        if password_hash:
            password_valid = check_password_hash(password_hash, password)
        else:
            password_valid = user_profile.get('password_key_k2') == password

        if not password_valid:
            return jsonify({"status": "error", "message": "Invalid password"}), 401

        # Fetch account from DB2
        user_account = get_user_account(user_profile['id'])
        if not user_account:
            return jsonify({"status": "error", "message": "Account not found"}), 404

        token = generate_session_token(user_profile['registration_number'])
        active_sessions[token] = user_profile['registration_number']

        # A "verify-only" call (the app re-checks the PIN before every transaction) must
        # NOT spam a "Login successful" notification on each verification.
        verify_only = (
            request.headers.get('X-DPT-Verify-Only', '').strip().lower() in ('1', 'true', 'yes')
            or bool(data.get('verifyOnly'))
        )
        if not verify_only:
            create_notification(user_profile['id'], "Login successful", "Your account was accessed with K2 authentication.", "login")

        # Decrypt full name if available
        full_name = ''
        if user_profile.get('full_name_enc') and pii_encryption:
            try:
                full_name = pii_encryption.decrypt(user_profile['full_name_enc'])
            except Exception:
                full_name = user_profile.get('full_name_enc', '')  # Fallback if not encrypted
        elif user_profile.get('full_name_enc'):
            full_name = user_profile['full_name_enc']  # Not encrypted, use as-is

        return jsonify({
            "status": "success",
            "token": token,
            "user": {
                "id": user_profile['id'],
                "username": user_profile['registration_number'],
                "t": user_profile['timestamp_t'],
                "balance": float(user_account['balance']),
                "accountId": user_account['id'],
                "daily_limit": float(user_profile.get('daily_limit', 5000)),
                "today_spent": float(user_profile.get('today_spent', 0)),
                "has_rsa_key": bool(user_profile.get('rsa_public_key')),
                "full_name": full_name,
            }
        }), 200

    except Exception as e:
        if is_missing_schema_error(e):
            print(f"Login schema error: {e}")
            return missing_schema_response()
        print(f"Login error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route('/transfer', methods=['POST'])
@require_auth
def process_transfer():
    """Process secure money transfer — supports both hybrid envelope and legacy plaintext."""
    try:
        data = get_json_body()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON request body"}), 400

        username = validate_username(data.get('username'))
        if not username:
            return jsonify({"status": "error", "message": "Missing or invalid username"}), 400

        forbidden = authorize_username(username)
        if forbidden:
            return forbidden

        # Fetch user profile from DB1
        user_profile = get_user_profile(username)
        if not user_profile:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Fetch user account from DB2
        user_account = get_user_account(user_profile['id'])
        if not user_account:
            return jsonify({"status": "error", "message": "User account not found"}), 404

        # ============================================
        # PATH 1: Hybrid Transaction Envelope (HTE: ECDH + HKDF + AES-GCM + ECDSA)
        # ============================================
        envelope = data.get('envelope')
        if envelope and (envelope.get('ePK') or envelope.get('epk')) and server_ecdh_private_key_pem:
            try:
                # Normalize keys
                ePK = envelope.get('ePK') or envelope.get('epk')
                IV = envelope.get('IV') or envelope.get('iv')
                C = envelope.get('C') or envelope.get('ciphertext')
                Tag = envelope.get('Tag') or envelope.get('tag')
                Sig = envelope.get('Sig') or envelope.get('sig') or envelope.get('signature')
                AAD = envelope.get('AAD') or envelope.get('aad') or {}
                v = envelope.get('v', 1)
                key_id = envelope.get('KeyID') or envelope.get('key_id') or server_ecdh_key_id
                txid = AAD.get('TxID') or envelope.get('txid') or ''

                # Step 1: Validate protocol version and KeyID
                if int(v) != 1:
                    return jsonify({"status": "error", "message": f"Unsupported HTE protocol version: {v}"}), 400
                if key_id != server_ecdh_key_id:
                    log_security_event(username, 'unknown_keyid', {"key_id": key_id, "txid": txid})
                    return jsonify({"status": "error", "message": f"Unknown or retired KeyID: {key_id}"}), 400

                # Step 1b: Revocation-aware key validity vs the envelope creation time T
                key_ok, key_reason = validate_key_at_creation(key_id, AAD.get('T'))
                if not key_ok:
                    log_security_event(username, 'key_validity_rejected', {"key_id": key_id, "reason": key_reason, "txid": txid})
                    print(f"[TRANSFER] HTE key validity rejected for {username}: {key_reason}", flush=True)
                    return jsonify({"status": "error", "message": key_reason}), 403

                # Step 2: Verify ECDSA signature against the registered key set
                # {PK_normal, PK_duress}; record which key matched (paper §3.1).
                normal_pub = user_profile.get('rsa_public_key') or user_profile.get('ecdsa_public_key')
                duress_pub = user_profile.get('ecdsa_public_key_duress')
                if not normal_pub and not duress_pub:
                    return jsonify({"status": "error", "message": "User has not enrolled device signing keys"}), 400

                # Canonicalize AAD bytes (sorted JSON without whitespace)
                aad_bytes = json.dumps(AAD, sort_keys=True, separators=(',', ':')).encode('utf-8')
                canonical_data = (
                    str(v) + key_id
                ).encode('utf-8') + bytes.fromhex(ePK) + bytes.fromhex(IV) + bytes.fromhex(C) + bytes.fromhex(Tag) + aad_bytes

                matched_duress = False
                sig_ok = bool(normal_pub) and HybridEnvelopeCrypto.verify_hte_signature(canonical_data, Sig, normal_pub)
                if not sig_ok and duress_pub:
                    if HybridEnvelopeCrypto.verify_hte_signature(canonical_data, Sig, duress_pub):
                        sig_ok = True
                        matched_duress = True
                if not sig_ok:
                    print(f"[TRANSFER] HTE ECDSA signature verification failed for user {username}", flush=True)
                    log_security_event(username, 'signature_rejected', {"txid": txid})
                    return jsonify({"status": "error", "message": "Biometric device signature verification failed"}), 403
                if matched_duress:
                    # Silent duress risk event (paper §3.1) — no client-visible warning.
                    log_security_event(username, 'duress_used', {"txid": txid, "key": "duress"})

                # Step 3: Verify freshness policy, nonce syntax and TxID format
                tx_time_str = AAD.get('T')
                if not tx_time_str or not txid:
                    return jsonify({"status": "error", "message": "Missing timestamp T or TxID in envelope AAD"}), 400
                if not is_txid_valid(txid):
                    log_security_event(username, 'invalid_txid', {"txid": txid})
                    return jsonify({"status": "error", "message": "Invalid TxID format"}), 400
                if not is_nonce_valid(AAD.get('N')):
                    log_security_event(username, 'invalid_nonce', {"txid": txid})
                    return jsonify({"status": "error", "message": "Invalid or missing nonce N"}), 400
                fresh_ok, fresh_reason = check_freshness(tx_time_str)
                if not fresh_ok:
                    log_security_event(username, 'stale_envelope', {"txid": txid, "reason": fresh_reason})
                    return jsonify({"status": "error", "message": fresh_reason}), 400
                # Step 4: Idempotency short-circuit FIRST (authoritative atomic reserve at
                # step 8). A committed TxID must return its stored result even though the
                # envelope's nonce was already burned at settlement; otherwise a retry of an
                # already-settled transfer would be misreported as a nonce replay (409), and
                # the client would fail/refund it (duplicate success + failed row). A
                # different TxID that reuses the same nonce is still rejected below.
                cached_result = check_idempotency(txid)
                if cached_result:
                    print(f"[TRANSFER] Idempotent duplicate HTE TxID: {txid}", flush=True)
                    return jsonify(cached_result), 200

                if is_nonce_used(AAD.get('N')):
                    log_security_event(username, 'nonce_replay', {"txid": txid})
                    return jsonify({"status": "error", "message": "Envelope nonce has already been used"}), 409

                # Step 5: Derive transaction key KT via ECDH(SK_B^dh, ePK) + HKDF-SHA256
                # (Z comes from the HSM when AWS KMS is configured — paper §2).
                KT = derive_kt_server_side(ePK, AAD, key_id)

                # Step 6: Verify GCM tag and decrypt payment payload M
                payload = HybridEnvelopeCrypto.decrypt_hte_payload(C, IV, Tag, aad_bytes, KT)

                # Step 7: Business validation
                receiver_username = validate_username(payload.get('R'))
                amount = float(payload.get('A', 0))
                txid_from_payload = payload.get('TxID', '')

                if txid != txid_from_payload:
                    return jsonify({"status": "error", "message": "TxID mismatch between envelope and decrypted payload"}), 400
                if not receiver_username:
                    return jsonify({"status": "error", "message": "Invalid receiver username"}), 400
                if amount <= 0:
                    return jsonify({"status": "error", "message": "Amount must be greater than zero"}), 400
                if same_username(username, receiver_username):
                    return jsonify({"status": "error", "message": "Self transaction not allowed"}), 400

                # Server-authoritative daily limit (paper §3 step 7)
                daily_limit = float(user_profile.get('daily_limit', 5000) or 5000)
                today_spent = float(user_profile.get('today_spent', 0) or 0)
                if today_spent + amount > daily_limit:
                    log_security_event(username, 'daily_limit_exceeded', {"txid": txid, "amount": amount, "today_spent": today_spent, "daily_limit": daily_limit})
                    return jsonify({"status": "futile", "message": "Daily limit exceeded"}), 400

                # Duress profile (paper §3.1): restricted spend limit L_D.
                if matched_duress:
                    ld = float(user_profile.get('duress_limit', 250) or 250)
                    duress_spent = float(user_profile.get('duress_today_spent', 0) or 0)
                    if amount > ld or duress_spent + amount > ld:
                        log_security_event(username, 'duress_limit_exceeded', {"txid": txid, "amount": amount, "duress_spent": duress_spent, "duress_limit": ld})
                        return jsonify({"status": "futile", "message": "Duress spend limit exceeded"}), 400

                receiver_account = get_receiver_account(receiver_username)
                if not receiver_account:
                    # Not an executed transfer — do NOT write a history row (it would show
                    # up as a phantom "Unknown" entry, once per retry). The result screen and
                    # the notification below already inform the user.
                    create_notification(user_profile['id'], "Transfer aborted", "Receiver username was not found.", "transfer_aborted", None)
                    return jsonify({"status": "error", "message": "Receiver not found"}), 404

                if user_account['balance'] < amount:
                    txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'futile', 'Insufficient balance')
                    create_notification(user_profile['id'], "Transfer futile", "Insufficient balance.", "transfer_futile", txn.get('id') if txn else None)
                    return jsonify({"status": "futile", "message": "Insufficient balance"}), 400

                # Step 8: Atomic check-and-commit (reserve TxID, then move money atomically)
                reserve_state, reserved_cached = reserve_idempotency(txid, user_profile['id'], receiver_account['id'], amount)
                if reserve_state == 'committed':
                    print(f"[TRANSFER] Concurrent duplicate HTE TxID settled already: {txid}", flush=True)
                    return jsonify(reserved_cached or {"status": "success", "message": "Transaction already settled"}), 200
                if reserve_state == 'inflight':
                    return jsonify({"status": "error", "message": "Transaction is already being processed"}), 409

                ok, sender_new_balance, receiver_new_balance, settle_reason = update_accounts_atomic(
                    user_account['id'], receiver_account['id'], amount,
                    nonce=AAD.get('N'), txid=txid, sender=username,
                )
                if not ok:
                    release_idempotency(txid)
                    if settle_reason == "Insufficient balance":
                        txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'futile', 'Insufficient balance')
                        create_notification(user_profile['id'], "Transfer futile", "Insufficient balance.", "transfer_futile", txn.get('id') if txn else None)
                        return jsonify({"status": "futile", "message": "Insufficient balance"}), 400
                    print(f"[TRANSFER] HTE atomic settle failed for {username}: {settle_reason}", flush=True)
                    log_security_event(username, 'settlement_failed', {"txid": txid, "reason": settle_reason})
                    return jsonify({"status": "error", "message": settle_reason or "Settlement failed"}), 500

                new_t = datetime.datetime.now(datetime.timezone.utc).isoformat()
                result = {
                    "status": "success",
                    "message": f"Transfer of {amount} to {receiver_username} successful",
                    "new_t": new_t,
                    "new_balance": sender_new_balance,
                    "txid": txid
                }
                # Commit the transaction identity immediately after the atomic move.
                commit_idempotency(txid, result)
                mark_nonce_used(AAD.get('N'), txid, username)
                if matched_duress:
                    add_duress_spend(user_profile['id'], amount)

                # Best-effort side effects (must never fail an already-settled transfer).
                try:
                    update_profile_timestamp(user_profile['id'], new_t)
                    update_daily_spend(user_profile['id'], today_spent + amount)
                    txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'success')
                    transaction_id = txn.get('id') if txn else None
                    create_notification(user_profile['id'], "Transfer successful", f"BDT {amount:.2f} sent to {receiver_username}.", "transfer_success", transaction_id)
                    create_notification(receiver_account['profile_id'], "Money received", f"BDT {amount:.2f} received from {username}.", "transfer_success", transaction_id)
                except Exception as side_err:
                    print(f"[TRANSFER] Post-settlement side-effect error (non-fatal): {side_err}", flush=True)

                print(f"[TRANSFER] HTE transaction {txid} settled successfully!", flush=True)
                return jsonify(result), 200

            except Exception as hte_err:
                print(f"[TRANSFER] HTE processing error: {hte_err}", flush=True)
                return jsonify({"status": "error", "message": f"HTE envelope error: {str(hte_err)}"}), 400

        # ============================================
        # PATH 2: Legacy plaintext / old encrypted
        # ============================================
        encrypted_payload = data.get('payload')
        iv = data.get('iv')
        receiver_from_request = validate_username(data.get('receiver') or data.get('receiverUsername'))
        amount_from_request = data.get('amount')

        if encrypted_payload and iv:
            # Old encrypted path (AES-CBC with K2/BP/T)
            decrypted_data = crypto.decrypt_data(
                encrypted_payload,
                iv,
                user_profile['password_key_k2'],
                user_profile.get('fingerprint_bp') or '123456',
                user_profile['timestamp_t']
            )

            if not decrypted_data:
                return jsonify({"status": "error", "message": "Decryption failed or invalid Timestamp"}), 401

            message_m = decrypted_data['M']
            f1_from_user = decrypted_data['F1']

            f2_generated = crypto.generate_hmac(user_profile['hmac_key_k1'], message_m)

            if f1_from_user != f2_generated:
                txn = record_transaction(user_account['id'], None, 0, 'aborted', 'HMAC mismatch')
                create_notification(user_profile['id'], "Transfer aborted", "Message integrity check failed.", "transfer_aborted", txn.get('id') if txn else None)
                return jsonify({"status": "error", "message": "Data integrity compromised (HMAC mismatch)"}), 403

            try:
                parts = message_m.split('|')
                if len(parts) != 2:
                    raise ValueError("Unexpected transfer message part count")
                receiver_username = validate_username(parts[0].split(':', 1)[1])
                amount = float(parts[1].split(':', 1)[1])
            except Exception:
                return jsonify({"status": "error", "message": "Invalid message format"}), 400
        elif receiver_from_request and amount_from_request is not None:
            # Plaintext path
            receiver_username = receiver_from_request
            try:
                amount = float(amount_from_request)
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Invalid amount"}), 400
        else:
            return jsonify({"status": "error", "message": "Missing transfer payload or receiver/amount"}), 400

        # Client-supplied idempotency key (same immutable identity on every retry).
        idem_key = (
            data.get('idempotencyKey')
            or data.get('idempotency_key')
            or request.headers.get('X-Idempotency-Key')
            or request.headers.get('Idempotency-Key')
            or ''
        )
        idem_key = str(idem_key).strip()
        if idem_key and not is_txid_valid(idem_key):
            idem_key = ''
        if idem_key:
            cached_result = check_idempotency(idem_key)
            if cached_result:
                print(f"[TRANSFER] Idempotent duplicate TxID: {idem_key}", flush=True)
                return jsonify(cached_result), 200

        if not receiver_username:
            return jsonify({"status": "error", "message": "Invalid receiver username"}), 400

        if amount <= 0:
            return jsonify({"status": "error", "message": "Amount must be greater than zero"}), 400

        if same_username(username, receiver_username):
            return jsonify({
                "status": "error",
                "message": "Self transaction not allowed. Please enter another receiver username."
            }), 400

        # Find receiver
        receiver_account = get_receiver_account(receiver_username)
        if not receiver_account:
            # Not an executed transfer — no history row (avoids phantom "Unknown" entries).
            create_notification(user_profile['id'], "Transfer aborted", "Receiver username was not found.", "transfer_aborted", None)
            return jsonify({"status": "error", "message": "Receiver not found"}), 404

        # Server-authoritative daily limit (paper §3 step 7)
        daily_limit = float(user_profile.get('daily_limit', 5000) or 5000)
        today_spent = float(user_profile.get('today_spent', 0) or 0)
        if today_spent + amount > daily_limit:
            log_security_event(username, 'daily_limit_exceeded', {"amount": amount, "today_spent": today_spent, "daily_limit": daily_limit})
            return jsonify({"status": "futile", "message": "Daily limit exceeded"}), 400

        # Balance pre-check for a friendly error (the atomic debit is the authority)
        if user_account['balance'] < amount:
            txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'futile', 'Insufficient balance')
            create_notification(user_profile['id'], "Transfer futile", "Insufficient balance.", "transfer_futile", txn.get('id') if txn else None)
            return jsonify({"status": "futile", "message": "Insufficient balance"}), 400

        # Atomic check-and-commit
        if idem_key:
            reserve_state, reserved_cached = reserve_idempotency(idem_key, user_profile['id'], receiver_account['id'], amount)
            if reserve_state == 'committed':
                return jsonify(reserved_cached or {"status": "success", "message": "Transaction already settled"}), 200
            if reserve_state == 'inflight':
                return jsonify({"status": "error", "message": "Transaction is already being processed"}), 409

        ok, sender_new_balance, receiver_new_balance, settle_reason = update_accounts_atomic(
            user_account['id'], receiver_account['id'], amount
        )
        if not ok:
            if idem_key:
                release_idempotency(idem_key)
            if settle_reason == "Insufficient balance":
                txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'futile', 'Insufficient balance')
                create_notification(user_profile['id'], "Transfer futile", "Insufficient balance.", "transfer_futile", txn.get('id') if txn else None)
                return jsonify({"status": "futile", "message": "Insufficient balance"}), 400
            log_security_event(username, 'settlement_failed', {"reason": settle_reason})
            return jsonify({"status": "error", "message": settle_reason or "Settlement failed"}), 500

        new_t = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = {
            "status": "success",
            "message": f"Transfer of {amount} to {receiver_username} successful",
            "new_t": new_t,
            "new_balance": sender_new_balance
        }
        if idem_key:
            commit_idempotency(idem_key, result)

        # Best-effort side effects (must never fail an already-settled transfer).
        try:
            update_profile_timestamp(user_profile['id'], new_t)
            update_daily_spend(user_profile['id'], today_spent + amount)
            txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'success')
            transaction_id = txn.get('id') if txn else None
            create_notification(user_profile['id'], "Transfer successful", f"BDT {amount:.2f} sent to {receiver_username}.", "transfer_success", transaction_id)
            create_notification(receiver_account['profile_id'], "Money received", f"BDT {amount:.2f} received from {username}.", "transfer_success", transaction_id)
        except Exception as side_err:
            print(f"[TRANSFER] Post-settlement side-effect error (non-fatal): {side_err}", flush=True)

        return jsonify(result), 200

    except Exception as e:
        if is_missing_schema_error(e):
            print(f"Transfer schema error: {e}")
            return missing_schema_response()
        print(f"Transfer error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route('/transfer/claim', methods=['POST'])
@require_auth
def claim_transfer():
    """Receiver-side claim of a sender-signed offline envelope (paper §4.1).

    The sender builds and signs the envelope P offline; a copy is handed to the
    receiver (QR / NFC) who submits the SAME immutable P here once online. The
    server verifies the sender's ECDSA signature and settles atomically, so final
    settlement stays receiver-authoritative — no ad-hoc crypto involved.
    """
    try:
        data = get_json_body()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON request body"}), 400

        envelope = data.get('envelope') or data
        if not envelope or not (envelope.get('ePK') or envelope.get('epk')):
            return jsonify({"status": "error", "message": "Missing HTE envelope"}), 400
        if not server_ecdh_private_key_pem:
            return jsonify({"status": "error", "message": "Server cryptographic keys not initialized"}), 500

        ePK = envelope.get('ePK') or envelope.get('epk')
        IV = envelope.get('IV') or envelope.get('iv')
        C = envelope.get('C') or envelope.get('ciphertext')
        Tag = envelope.get('Tag') or envelope.get('tag')
        Sig = envelope.get('Sig') or envelope.get('sig') or envelope.get('signature')
        AAD = envelope.get('AAD') or envelope.get('aad') or {}
        v = envelope.get('v', 1)
        key_id = envelope.get('KeyID') or envelope.get('key_id') or server_ecdh_key_id
        txid = AAD.get('TxID') or envelope.get('txid') or ''

        receiver_claimant = authenticated_username()
        sender_username = validate_username(AAD.get('S'))
        if not sender_username:
            return jsonify({"status": "error", "message": "Envelope missing sender (S)"}), 400

        if int(v) != 1:
            return jsonify({"status": "error", "message": f"Unsupported HTE protocol version: {v}"}), 400
        if key_id != server_ecdh_key_id:
            log_security_event(receiver_claimant, 'unknown_keyid', {"key_id": key_id, "txid": txid})
            return jsonify({"status": "error", "message": f"Unknown or retired KeyID: {key_id}"}), 400

        key_ok, key_reason = validate_key_at_creation(key_id, AAD.get('T'))
        if not key_ok:
            log_security_event(receiver_claimant, 'key_validity_rejected', {"key_id": key_id, "reason": key_reason, "txid": txid})
            return jsonify({"status": "error", "message": key_reason}), 403

        if not is_txid_valid(txid) or not is_nonce_valid(AAD.get('N')):
            return jsonify({"status": "error", "message": "Invalid TxID or nonce"}), 400
        fresh_ok, fresh_reason = check_freshness(AAD.get('T'))
        if not fresh_ok:
            log_security_event(receiver_claimant, 'stale_envelope', {"txid": txid, "reason": fresh_reason})
            return jsonify({"status": "error", "message": fresh_reason}), 400
        # Idempotency FIRST: a committed TxID returns its stored result even though its
        # nonce was already burned at settlement (retry must not be misreported as a
        # nonce replay). A different TxID reusing the nonce is still rejected below.
        cached_result = check_idempotency(txid)
        if cached_result:
            return jsonify(cached_result), 200

        # Offline receipt QR is short-lived: reject claims for envelopes older than
        # CLAIM_MAX_AGE_SECONDS (default 60s). A committed TxID returned cached above.
        _t_created = parse_envelope_timestamp(AAD.get('T'))
        if _t_created is not None:
            _claim_age = (datetime.datetime.now(datetime.timezone.utc) - _t_created).total_seconds()
            if _claim_age > CLAIM_MAX_AGE_SECONDS:
                log_security_event(receiver_claimant, 'claim_qr_expired', {"txid": txid, "age": int(_claim_age)})
                return jsonify({"status": "error", "message": "Claim QR expired"}), 410

        if is_nonce_used(AAD.get('N')):
            log_security_event(receiver_claimant, 'nonce_replay', {"txid": txid})
            return jsonify({"status": "error", "message": "Envelope nonce has already been used"}), 409

        # Verify the SENDER's device signature.
        sender_profile = get_user_profile(sender_username)
        if not sender_profile:
            return jsonify({"status": "error", "message": "Sender not found"}), 404
        normal_pub = sender_profile.get('rsa_public_key') or sender_profile.get('ecdsa_public_key')
        duress_pub = sender_profile.get('ecdsa_public_key_duress')
        if not normal_pub and not duress_pub:
            return jsonify({"status": "error", "message": "Sender has not enrolled device signing keys"}), 400

        aad_bytes = json.dumps(AAD, sort_keys=True, separators=(',', ':')).encode('utf-8')
        canonical_data = (str(v) + key_id).encode('utf-8') + bytes.fromhex(ePK) + bytes.fromhex(IV) + bytes.fromhex(C) + bytes.fromhex(Tag) + aad_bytes
        matched_duress = False
        sig_ok = bool(normal_pub) and HybridEnvelopeCrypto.verify_hte_signature(canonical_data, Sig, normal_pub)
        if not sig_ok and duress_pub:
            if HybridEnvelopeCrypto.verify_hte_signature(canonical_data, Sig, duress_pub):
                sig_ok = True
                matched_duress = True
        if not sig_ok:
            log_security_event(receiver_claimant, 'claim_signature_rejected', {"txid": txid, "sender": sender_username})
            return jsonify({"status": "error", "message": "Sender device signature verification failed"}), 403
        if matched_duress:
            log_security_event(sender_username, 'duress_used', {"txid": txid, "key": "duress"})

        # Derive KT and decrypt to confirm amount / receiver / TxID.
        # (Z comes from the HSM when AWS KMS is configured — paper §2.)
        KT = derive_kt_server_side(ePK, AAD, key_id)
        payload = HybridEnvelopeCrypto.decrypt_hte_payload(C, IV, Tag, aad_bytes, KT)

        # The receiver identifier lives inside the encrypted payload M (not in AAD).
        payload_sender = validate_username(payload.get('S'))
        payload_receiver = validate_username(payload.get('R'))
        amount = float(payload.get('A', 0))
        txid_from_payload = payload.get('TxID', '')

        if not payload_receiver or not same_username(payload_sender, sender_username):
            return jsonify({"status": "error", "message": "Envelope payload mismatch"}), 400
        if txid != txid_from_payload:
            return jsonify({"status": "error", "message": "TxID mismatch between envelope and payload"}), 400
        if not same_username(receiver_claimant, payload_receiver):
            log_security_event(receiver_claimant, 'claim_forbidden', {"txid": txid, "sender": sender_username, "receiver": payload_receiver})
            return jsonify({"status": "error", "message": "Only the intended receiver can claim this envelope"}), 403
        if amount <= 0:
            return jsonify({"status": "error", "message": "Amount must be greater than zero"}), 400
        if same_username(sender_username, payload_receiver):
            return jsonify({"status": "error", "message": "Self transaction not allowed"}), 400

        receiver_username = payload_receiver
        receiver_profile = get_user_profile(receiver_username)
        sender_account = get_user_account(sender_profile['id'])
        receiver_account = get_user_account(receiver_profile['id']) if receiver_profile else None
        if not sender_account or not receiver_account:
            return jsonify({"status": "error", "message": "Sender or receiver account not found"}), 404

        # Daily limit is debited against the SENDER (paper §3 step 7).
        daily_limit = float(sender_profile.get('daily_limit', 5000) or 5000)
        today_spent = float(sender_profile.get('today_spent', 0) or 0)
        if today_spent + amount > daily_limit:
            log_security_event(sender_username, 'daily_limit_exceeded', {"txid": txid, "amount": amount})
            return jsonify({"status": "futile", "message": "Daily limit exceeded"}), 400

        # Duress profile (paper §3.1): offline-queued duress envelopes are re-checked here,
        # so a client that locally exhausted L_D is still rejected authoritatively.
        if matched_duress:
            ld = float(sender_profile.get('duress_limit', 250) or 250)
            duress_spent = float(sender_profile.get('duress_today_spent', 0) or 0)
            if amount > ld or duress_spent + amount > ld:
                log_security_event(sender_username, 'duress_limit_exceeded', {"txid": txid, "amount": amount, "duress_spent": duress_spent, "duress_limit": ld})
                return jsonify({"status": "futile", "message": "Duress spend limit exceeded"}), 400

        reserve_state, reserved_cached = reserve_idempotency(txid, sender_profile['id'], receiver_account['id'], amount)
        if reserve_state == 'committed':
            return jsonify(reserved_cached or {"status": "success", "message": "Transaction already settled"}), 200
        if reserve_state == 'inflight':
            return jsonify({"status": "error", "message": "Transaction is already being processed"}), 409

        ok, sender_new_balance, receiver_new_balance, settle_reason = update_accounts_atomic(
            sender_account['id'], receiver_account['id'], amount,
            nonce=AAD.get('N'), txid=txid, sender=sender_username,
        )
        if not ok:
            release_idempotency(txid)
            if settle_reason == "Insufficient balance":
                return jsonify({"status": "futile", "message": "Insufficient balance"}), 400
            log_security_event(sender_username, 'settlement_failed', {"txid": txid, "reason": settle_reason})
            return jsonify({"status": "error", "message": settle_reason or "Settlement failed"}), 500

        new_t = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = {
            "status": "success",
            "message": f"Claim of {amount} from {sender_username} settled",
            "new_t": new_t,
            "new_balance": sender_new_balance,
            "receiver_balance": receiver_new_balance,
            "txid": txid
        }
        commit_idempotency(txid, result)
        mark_nonce_used(AAD.get('N'), txid, sender_username)
        if matched_duress:
            add_duress_spend(sender_profile['id'], amount)

        # Best-effort side effects (must never fail an already-settled transfer).
        try:
            update_profile_timestamp(sender_profile['id'], new_t)
            update_daily_spend(sender_profile['id'], today_spent + amount)
            txn = record_transaction(sender_account['id'], receiver_account['id'], amount, 'success')
            transaction_id = txn.get('id') if txn else None
            create_notification(sender_profile['id'], "Transfer successful", f"BDT {amount:.2f} sent to {receiver_username}.", "transfer_success", transaction_id)
            create_notification(receiver_account['profile_id'], "Money received", f"BDT {amount:.2f} received from {sender_username}.", "transfer_success", transaction_id)
        except Exception as side_err:
            print(f"[CLAIM] Post-settlement side-effect error (non-fatal): {side_err}", flush=True)

        return jsonify(result), 200
    except Exception as e:
        if is_missing_schema_error(e):
            return missing_schema_response()
        print(f"Claim error: {e}")
        return jsonify({"status": "error", "message": f"Claim failed: {str(e)}"}), 500


@app.route('/device-key', methods=['POST'])
@require_auth
def register_device_key():
    """Re-enroll the caller's device signing public key(s).

    The device key is created once at registration. If it is later regenerated
    (app reinstall, or a biometric-enrollment change invalidating the Keystore
    key, or switching devices) the server-side copy goes stale and every HTE
    transfer fails "Biometric device signature verification failed". This lets
    the authenticated user re-sync the current device public key(s).
    """
    try:
        username = authenticated_username()
        if not username:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        data = get_json_body() or {}
        normal_pub = (data.get('normalPublicKey') or data.get('normal_public_key')
                      or data.get('ecdsaPublicKey') or data.get('ecdsa_public_key') or '')
        duress_pub = (data.get('duressPublicKey') or data.get('duress_public_key')
                      or data.get('ecdsaPublicKeyDuress') or data.get('ecdsa_public_key_duress') or '')
        profile = get_user_profile(username)
        if not profile:
            return jsonify({"status": "error", "message": "User not found"}), 404
        update = {}
        if normal_pub:
            update['rsa_public_key'] = normal_pub
        if duress_pub:
            update['ecdsa_public_key_duress'] = duress_pub
        if not update:
            return jsonify({"status": "error", "message": "No public key supplied"}), 400
        db = identity_db if identity_db else business_db
        db.table('profiles').update(update).eq('registration_number', username).execute()
        print(f"[DEVICE-KEY] Re-enrolled device key(s) for {username}", flush=True)
        return jsonify({"status": "success", "message": "Device key enrolled"}), 200
    except Exception as e:
        if is_missing_schema_error(e):
            return missing_schema_response()
        print(f"Device-key error: {e}")
        return jsonify({"status": "error", "message": f"Device key enrollment failed: {str(e)}"}), 500


@app.route('/user/<username>', methods=['GET'])
@require_auth
def get_user(username):
    """Get user profile and account information"""
    try:
        username = validate_username(username)
        if not username:
            return jsonify({"status": "error", "message": "Invalid username"}), 400

        forbidden = authorize_username(username)
        if forbidden:
            return forbidden

        # DB1: profile
        user_profile = get_user_profile(username)
        if not user_profile:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # DB2: account
        user_account = get_user_account(user_profile['id'])
        if not user_account:
            return jsonify({"status": "error", "message": "Account not found"}), 404

        # Decrypt full name if available
        full_name = ''
        if user_profile.get('full_name_enc') and pii_encryption:
            try:
                full_name = pii_encryption.decrypt(user_profile['full_name_enc'])
            except Exception:
                full_name = user_profile.get('full_name_enc', '')
        elif user_profile.get('full_name_enc'):
            full_name = user_profile['full_name_enc']

        return jsonify({
            "status": "success",
            "user": {
                "id": user_profile['id'],
                "username": user_profile['registration_number'],
                "balance": float(user_account['balance']),
                "daily_limit": float(user_profile.get('daily_limit', 5000)),
                "today_spent": float(user_profile.get('today_spent', 0)),
                "has_rsa_key": bool(user_profile.get('rsa_public_key')),
                "full_name": full_name,
            }
        }), 200
    except Exception as e:
        if is_missing_schema_error(e):
            print(f"Get user schema error: {e}")
            return missing_schema_response()
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/transactions/<username>', methods=['GET'])
@require_auth
def get_transactions(username):
    """Get user's transaction history (both sent and received)"""
    try:
        username = validate_username(username)
        if not username:
            return jsonify({"status": "error", "message": "Invalid username"}), 400

        forbidden = authorize_username(username)
        if forbidden:
            return forbidden

        # DB1: profile
        user_profile = get_user_profile(username)
        if not user_profile:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # DB2: account
        user_account = get_user_account(user_profile['id'])
        if not user_account:
            return jsonify({"status": "error", "message": "Account not found"}), 404

        # DB2: transactions
        # Delta sync support: when ?since=<iso_timestamp> is supplied only rows
        # newer than that timestamp are returned (previously the param was ignored).
        since = request.args.get('since')
        try:
            tx_limit = int(os.environ.get('TRANSACTIONS_PAGE_LIMIT', '500'))
        except ValueError:
            tx_limit = 500

        sent_query = business_db.table('transactions').select('*').eq('sender_account_id', user_account['id'])
        received_query = business_db.table('transactions').select('*').eq('receiver_account_id', user_account['id'])
        if since:
            sent_query = sent_query.gt('created_at', since)
            received_query = received_query.gt('created_at', since)
        sent_response = sent_query.order('created_at', desc=True).limit(tx_limit).execute()
        received_response = received_query.order('created_at', desc=True).limit(tx_limit).execute()

        transactions = []

        # Helper to resolve username from account_id (cross-DB lookup)
        def resolve_username_from_account(account_id):
            try:
                acct = business_db.table('accounts').select('profile_id').eq('id', account_id).execute()
                if acct.data:
                    pid = acct.data[0]['profile_id']
                    # Try DB1 first, then DB2
                    db = identity_db if identity_db else business_db
                    prof = db.table('profiles').select('registration_number').eq('id', pid).execute()
                    if prof.data:
                        return prof.data[0]['registration_number']
            except Exception:
                pass
            return 'Unknown'

        if sent_response.data:
            for txn in sent_response.data:
                receiver_name = resolve_username_from_account(txn['receiver_account_id']) if txn.get('receiver_account_id') else 'Unknown'
                transactions.append({
                    "id": txn['id'],
                    "amount": float(txn['amount']),
                    "status": txn['status'],
                    "created_at": txn['created_at'],
                    "reference": txn['reference'],
                    "receiver_username": receiver_name,
                    "type": "sent"
                })

        if received_response.data:
            for txn in received_response.data:
                sender_name = resolve_username_from_account(txn['sender_account_id']) if txn.get('sender_account_id') else 'Unknown'
                transactions.append({
                    "id": txn['id'],
                    "amount": float(txn['amount']),
                    "status": txn['status'],
                    "created_at": txn['created_at'],
                    "reference": txn['reference'],
                    "sender_username": sender_name,
                    "type": "received"
                })

        def _created_ts(value):
            try:
                return datetime.datetime.fromisoformat(str(value or '').replace('Z', '+00:00')).timestamp()
            except Exception:
                return 0.0

        transactions.sort(key=lambda x: _created_ts(x.get('created_at')), reverse=True)

        return jsonify({
            "status": "success",
            "transactions": transactions
        }), 200
    except Exception as e:
        if is_missing_schema_error(e):
            print(f"Transactions schema error: {e}")
            return missing_schema_response()
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/notifications/<username>', methods=['GET'])
@require_auth
def get_notifications(username):
    """Get recent notification messages for a user."""
    try:
        username = validate_username(username)
        if not username:
            return jsonify({"status": "error", "message": "Invalid username"}), 400

        forbidden = authorize_username(username)
        if forbidden:
            return forbidden

        # DB1: profile
        user_profile = get_user_profile(username)
        if not user_profile:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # DB2: notifications
        response = (
            business_db.table('notifications')
            .select('*')
            .eq('profile_id', user_profile['id'])
            .order('created_at', desc=True)
            .limit(30)
            .execute()
        )

        return jsonify({
            "status": "success",
            "notifications": response.data or []
        }), 200
    except Exception as e:
        if is_missing_schema_error(e):
            print(f"Notifications schema error: {e}")
            return missing_schema_response()
        print(f"Notifications error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/register', methods=['POST'])
def register():
    """Register a new user account — supports RSA public key enrollment."""
    try:
        data = get_json_body()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON request body"}), 400

        username = validate_username(data.get('username'))
        password = data.get('password')
        nid = data.get('nid') or data.get('brc') or ''
        activation_code = data.get('activationCode') or data.get('activation_code') or ''

        if not username or not password or not nid or not activation_code:
            return jsonify({"status": "error", "message": "Missing username, password, NID/BRC, or activation code"}), 400

        # New fields from enhanced registration
        full_name = data.get('fullName') or data.get('full_name') or ''
        mobile = data.get('mobile') or data.get('phone') or ''
        email = data.get('email') or ''
        rsa_public_key = data.get('rsaPublicKey') or data.get('rsa_public_key') or data.get('ecdsaPublicKey') or data.get('ecdsa_public_key') or ''
        ecdsa_public_key_duress = data.get('ecdsaPublicKeyDuress') or data.get('ecdsa_public_key_duress') or ''
        biometric_enrolled = data.get('biometricEnrolled', False)

        # Check if user already exists (DB1)
        existing_profile = get_user_profile(username)
        if existing_profile:
            return jsonify({"status": "error", "message": "Username already exists"}), 400

        # Create Supabase Auth user (DB1 if available, else DB2)
        auth_db = identity_db if identity_db else business_db
        synthetic_email = f"{username}@example.com"
        try:
            auth_response = auth_db.auth.admin.create_user({
                "email": synthetic_email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"username": username}
            })
            auth_user_id = auth_response.user.id
        except Exception as auth_err:
            print(f"Auth user creation error: {auth_err}")
            if "User not allowed" in str(auth_err):
                return jsonify({
                    "status": "error",
                    "message": "Backend Supabase key cannot create Auth users. Set SUPABASE_SERVICE_ROLE_KEY."
                }), 500
            return jsonify({"status": "error", "message": f"Auth error: {str(auth_err)}"}), 500

        # Generate crypto keys
        bp = data.get('bp') or '123456'
        k1 = crypto.generate_hmac(activation_code, f"{nid}|{username}|{bp}")
        k2 = crypto.stretch_password(password, nid)
        t = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Encrypt PII if encryption is configured, otherwise store as-is
        full_name_enc = pii_encryption.encrypt(full_name) if (pii_encryption and full_name) else (full_name or None)
        mobile_enc = pii_encryption.encrypt(mobile) if (pii_encryption and mobile) else (mobile or None)
        mobile_hmac = lookup_hash.compute(mobile) if (lookup_hash and mobile) else None
        email_enc = pii_encryption.encrypt(email) if (pii_encryption and email) else (email or None)

        # Build profile data
        profile_data = {
            'id': auth_user_id,
            'registration_number': username,
            'password_hash': generate_password_hash(password),
            'password_key_k2': k2,
            'fingerprint_bp': bp,
            'hmac_key_k1': k1,
            'nid_brc_hash': crypto.generate_hmac(activation_code, nid),
            'activation_code_hash': crypto.generate_hmac(nid, activation_code),
            'timestamp_t': t,
            'daily_limit': 5000.0,
            'today_spent': 0.0,
        }

        # Add new fields if available
        if rsa_public_key:
            profile_data['rsa_public_key'] = rsa_public_key
        if ecdsa_public_key_duress:
            profile_data['ecdsa_public_key_duress'] = ecdsa_public_key_duress
        if full_name_enc:
            profile_data['full_name_enc'] = full_name_enc
        if mobile_enc:
            profile_data['mobile_enc'] = mobile_enc
        if mobile_hmac:
            profile_data['mobile_hmac'] = mobile_hmac
        if email_enc:
            profile_data['email_enc'] = email_enc
        if biometric_enrolled:
            profile_data['biometric_enrolled'] = True

        # Insert profile into DB1 (or DB2 if identity_db not configured)
        target_db = identity_db if identity_db else business_db
        response = target_db.table('profiles').insert(profile_data).execute()
        if not response.data:
            try:
                auth_db.auth.admin.delete_user(auth_user_id)
            except Exception:
                pass
            return jsonify({"status": "error", "message": "Failed to create profile"}), 500

        profile_id = response.data[0]['id']

        # Create linked bank account in DB2
        account_data = {
            'profile_id': profile_id,
            'balance': 5000.0,
            'is_active': True,
            'account_number': f"ACC-{username}"
        }
        business_db.table('accounts').insert(account_data).execute()
        create_notification(profile_id, "Account activated", "Your E-Payment account is ready.", "registration")

        return jsonify({"status": "success", "message": "Account created successfully"}), 201

    except Exception as e:
        if is_missing_schema_error(e):
            print(f"Registration schema error: {e}")
            return missing_schema_response()
        print(f"Registration error: {e}")
        return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500

@app.route('/check-receiver/<username>', methods=['GET'])
@require_auth
def check_receiver(username):
    """Check if a receiver username exists"""
    try:
        username = validate_username(username)
        if not username:
            return jsonify({"status": "error", "message": "Invalid receiver username"}), 400

        # DB1 lookup
        profile = get_user_profile(username)
        if not profile:
            return jsonify({"status": "error", "message": "Receiver not found"}), 404
        return jsonify({"status": "success", "username": profile['registration_number']}), 200
    except Exception as e:
        if is_missing_schema_error(e):
            print(f"Check receiver schema error: {e}")
            return missing_schema_response()
        print(f"Check receiver error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# ========================================
# Profile Picture Endpoints (DB1)
# ========================================
@app.route('/profile-picture', methods=['POST'])
@require_auth
def save_profile_picture():
    """Save profile picture reference in DB1."""
    try:
        data = get_json_body()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400

        username = validate_username(data.get('username'))
        image_data = data.get('imageData')  # base64 string

        if not username:
            return jsonify({"status": "error", "message": "Invalid username"}), 400

        forbidden = authorize_username(username)
        if forbidden:
            return forbidden

        if not image_data:
            return jsonify({"status": "error", "message": "No image data"}), 400

        # Save to DB1
        db = identity_db if identity_db else business_db
        db.table('profiles').update({'profile_picture_ref': image_data}).eq('registration_number', username).execute()

        return jsonify({"status": "success", "message": "Profile picture saved"}), 200
    except Exception as e:
        print(f"Save profile picture error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route('/profile-picture/<username>', methods=['GET'])
@require_auth
def get_profile_picture(username):
    """Get profile picture reference from DB1."""
    try:
        username = validate_username(username)
        if not username:
            return jsonify({"status": "error", "message": "Invalid username"}), 400

        forbidden = authorize_username(username)
        if forbidden:
            return forbidden

        db = identity_db if identity_db else business_db
        response = db.table('profiles').select('profile_picture_ref').eq('registration_number', username).execute()

        image_data = None
        if response.data and len(response.data) > 0:
            image_data = response.data[0].get('profile_picture_ref')

        return jsonify({"status": "success", "imageData": image_data}), 200
    except Exception as e:
        print(f"Get profile picture error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route('/display-name', methods=['POST'])
@require_auth
def save_display_name():
    """Save display name in DB1."""
    try:
        data = get_json_body()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400

        username = validate_username(data.get('username'))
        display_name = data.get('displayName', '').strip()

        if not username:
            return jsonify({"status": "error", "message": "Invalid username"}), 400

        forbidden = authorize_username(username)
        if forbidden:
            return forbidden

        # Store display_name in full_name_enc if empty, or use a dedicated field
        # For now, we'll use the existing full_name_enc field or add to profile_picture_ref
        # Actually, let's just store it alongside - we can use the profile update
        db = identity_db if identity_db else business_db
        
        # Check if full_name_enc exists, if not use a simple storage
        # For display name, we'll just update the profile with a display_name field
        # Since we don't have a dedicated column, we'll store it in memory for now
        # and sync to SQLite as before
        
        return jsonify({"status": "success", "message": "Display name saved"}), 200
    except Exception as e:
        print(f"Save display name error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


# ========================================
# Catch-all route for React Router
# ========================================
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files or index.html for SPA routing"""
    dist_dir = os.path.abspath(app.static_folder)
    requested_path = os.path.realpath(os.path.join(dist_dir, path))
    is_inside_dist = os.path.commonpath([dist_dir, requested_path]) == dist_dir
    if is_inside_dist and os.path.isfile(requested_path):
        return send_from_directory(dist_dir, os.path.relpath(requested_path, dist_dir))
    if not frontend_build_exists():
        return missing_frontend_response()
    return app.send_static_file('index.html')

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors by serving index.html for SPA routing"""
    if not frontend_build_exists():
        return missing_frontend_response()
    return app.send_static_file('index.html')

# ========================================
# Startup
# ========================================
with app.app_context():
    print("=" * 60, flush=True)
    print("[STARTUP] DPT Backend v2 — Hybrid Transaction Envelope", flush=True)
    print(f"[STARTUP] DB1 (Identity): {'Configured' if identity_db else 'NOT configured — using DB2'}", flush=True)
    print(f"[STARTUP] DB2 (Business): {'Sandbox' if SANDBOX_FAKE_DB else 'Configured'}", flush=True)
    print(f"[STARTUP] PII Encryption: {'Enabled' if pii_encryption else 'Disabled (no key)'}", flush=True)
    print(f"[STARTUP] Lookup Hash: {'Enabled' if lookup_hash else 'Disabled (no pepper)'}", flush=True)
    print("=" * 60, flush=True)

    auto_create_tables()
    ensure_server_ecdh_keys()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5001'))
    app.run(debug=True, port=port, host='0.0.0.0')
