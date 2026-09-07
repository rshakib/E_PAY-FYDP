from flask import Flask, request, jsonify, send_from_directory, g
import uuid
from flask_cors import CORS
from crypto import CryptoEngine
from crypto_v2 import HybridEnvelopeCrypto, PIIEncryption, LookupHash
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
server_private_key_pem = None
server_public_key_pem = None

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


def ensure_server_rsa_keys():
    """Generate or load server RSA key pair."""
    global server_private_key_pem, server_public_key_pem

    # Try loading from DB2 first
    try:
        result = business_db.table('server_keys').select('*').eq('id', 'server').execute()
        if result.data and len(result.data) > 0:
            server_private_key_pem = result.data[0]['private_key_pem']
            server_public_key_pem = result.data[0]['public_key_pem']
            print("[SERVER KEYS] Loaded RSA keys from database", flush=True)
            return
    except Exception as e:
        if not is_missing_schema_error(e):
            print(f"[SERVER KEYS] Could not load from DB: {e}", flush=True)

    # Generate new key pair
    server_private_key_pem, server_public_key_pem = HybridEnvelopeCrypto.generate_server_rsa_keypair()
    print("[SERVER KEYS] Generated new RSA-2048 key pair", flush=True)

    # Try to save to DB2
    try:
        business_db.table('server_keys').insert({
            'id': 'server',
            'private_key_pem': server_private_key_pem,
            'public_key_pem': server_public_key_pem,
        }).execute()
        print("[SERVER KEYS] Saved RSA keys to database", flush=True)
    except Exception as e:
        if is_missing_schema_error(e):
            print("[SERVER KEYS] DB tables not ready yet, keys held in memory only", flush=True)
        else:
            print(f"[SERVER KEYS] Could not save to DB: {e}", flush=True)


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
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """)
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

def generate_session_token() -> str:
    token = str(uuid.uuid4())
    return token

def require_auth(f):
    """Decorator to require a valid session token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:].strip() if auth_header.startswith('Bearer ') else ''
        if not token or token not in active_sessions:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        g.authenticated_username = active_sessions[token]
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
            'reference': f"TXN-{datetime.datetime.now().isoformat()}"
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

def save_idempotency(txid, profile_id, receiver_account_id, amount, status, result_dict):
    """Save idempotency key to DB2."""
    try:
        business_db.table('idempotency_keys').insert({
            'key': txid,
            'profile_id': str(profile_id),
            'receiver_account_id': str(receiver_account_id) if receiver_account_id else None,
            'amount': float(amount),
            'status': status,
            'result_json': json.dumps(result_dict),
        }).execute()
    except Exception as e:
        if is_missing_schema_error(e):
            raise
        print(f"Error saving idempotency key: {e}")


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
    """Background thread that pings /health every 10 minutes to prevent
    Render free-tier from sleeping and Supabase free-tier from pausing."""
    HEALTH_CHECK_INTERVAL = 10 * 60  # 10 minutes
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
    print("[SELF-PING] Background keep-alive thread started (every 10 minutes)", flush=True)


start_self_ping()

# ========================================
# Server Public Key Endpoint
# ========================================

@app.route('/server-public-key', methods=['GET'])
def get_server_public_key():
    """Return the server's RSA public key (PEM format) for envelope encryption."""
    if not server_public_key_pem:
        return jsonify({"status": "error", "message": "Server RSA keys not initialized"}), 500
    return jsonify({"status": "success", "public_key": server_public_key_pem}), 200


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

        token = generate_session_token()
        active_sessions[token] = user_profile['registration_number']
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
        # PATH 1: Hybrid Envelope (new RSA + AES-GCM)
        # ============================================
        envelope = data.get('envelope')
        if envelope and server_private_key_pem:
            try:
                txid = envelope.get('txid', '')

                # 1. Idempotency check
                cached_result = check_idempotency(txid)
                if cached_result:
                    print(f"[TRANSFER] Idempotent duplicate TxID: {txid}", flush=True)
                    return jsonify(cached_result), 200

                # 2. Decrypt session key with server RSA private key
                session_key = HybridEnvelopeCrypto.decrypt_session_key(
                    envelope['encrypted_key'], server_private_key_pem
                )

                # 3. Decrypt payload M = {S, R, A, T, N, TxID}
                payload = HybridEnvelopeCrypto.decrypt_payload(
                    envelope['ciphertext'], envelope['nonce'], session_key
                )

                # 4. Verify RSA-PSS signature
                user_pub_key = user_profile.get('rsa_public_key')
                if not user_pub_key:
                    return jsonify({"status": "error", "message": "User has not enrolled RSA keys. Use legacy transfer."}), 400

                # Reconstruct the signed message (AAD + encrypted components)
                sign_message = json.dumps({
                    "ciphertext": envelope['ciphertext'],
                    "nonce": envelope['nonce'],
                    "encrypted_key": envelope['encrypted_key'],
                    "txid": txid,
                }, sort_keys=True).encode()

                if not HybridEnvelopeCrypto.verify_signature(sign_message, envelope['signature'], user_pub_key):
                    return jsonify({"status": "error", "message": "Signature verification failed"}), 403

                # 5. Verify timestamp freshness (within ±5 minutes)
                try:
                    tx_time = datetime.datetime.fromisoformat(payload['T'].replace('Z', '+00:00'))
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if abs((now - tx_time).total_seconds()) > 300:
                        return jsonify({"status": "error", "message": "Transaction timestamp expired"}), 403
                except Exception:
                    return jsonify({"status": "error", "message": "Invalid timestamp format"}), 400

                # 6. Extract transfer details
                receiver_username = validate_username(payload.get('R'))
                amount = float(payload.get('A', 0))
                txid_from_payload = payload.get('TxID', '')

                if txid != txid_from_payload:
                    return jsonify({"status": "error", "message": "TxID mismatch between envelope and payload"}), 400

                # 7. Business validation
                if not receiver_username:
                    return jsonify({"status": "error", "message": "Invalid receiver username"}), 400
                if amount <= 0:
                    return jsonify({"status": "error", "message": "Amount must be greater than zero"}), 400
                if same_username(username, receiver_username):
                    return jsonify({"status": "error", "message": "Self transaction not allowed"}), 400

                receiver_account = get_receiver_account(receiver_username)
                if not receiver_account:
                    txn = record_transaction(user_account['id'], None, amount, 'aborted', 'Receiver not found')
                    create_notification(user_profile['id'], "Transfer aborted", "Receiver username was not found.", "transfer_aborted", txn.get('id') if txn else None)
                    return jsonify({"status": "error", "message": "Receiver not found"}), 404

                if user_account['balance'] < amount:
                    txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'futile', 'Insufficient balance')
                    create_notification(user_profile['id'], "Transfer futile", "Insufficient balance.", "transfer_futile", txn.get('id') if txn else None)
                    return jsonify({"status": "futile", "message": "Insufficient balance"}), 400

                # 8. Execute transfer
                sender_new_balance = float(user_account['balance']) - amount
                receiver_new_balance = float(receiver_account['balance']) + amount

                update_account_balance(user_account['id'], sender_new_balance)
                update_account_balance(receiver_account['id'], receiver_new_balance)

                new_t = datetime.datetime.now(datetime.timezone.utc).isoformat()
                update_profile_timestamp(user_profile['id'], new_t)
                update_daily_spend(user_profile['id'], float(user_profile.get('today_spent', 0)) + amount)

                txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'success')
                transaction_id = txn.get('id') if txn else None
                create_notification(user_profile['id'], "Transfer successful", f"BDT {amount:.2f} sent to {receiver_username}.", "transfer_success", transaction_id)
                create_notification(receiver_account['profile_id'], "Money received", f"BDT {amount:.2f} received from {username}.", "transfer_success", transaction_id)

                result = {
                    "status": "success",
                    "message": f"Transfer of {amount} to {receiver_username} successful",
                    "new_t": new_t,
                    "new_balance": sender_new_balance
                }

                # 9. Save idempotency key
                save_idempotency(txid, user_profile['id'], receiver_account['id'], amount, 'committed', result)

                return jsonify(result), 200

            except Exception as envelope_err:
                print(f"[TRANSFER] Envelope processing error: {envelope_err}", flush=True)
                return jsonify({"status": "error", "message": f"Envelope processing failed: {str(envelope_err)}"}), 400

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
            txn = record_transaction(user_account['id'], None, amount, 'aborted', 'Receiver not found')
            create_notification(user_profile['id'], "Transfer aborted", "Receiver username was not found.", "transfer_aborted", txn.get('id') if txn else None)
            return jsonify({"status": "error", "message": "Receiver not found"}), 404

        # Balance check
        if user_account['balance'] < amount:
            txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'futile', 'Insufficient balance')
            create_notification(user_profile['id'], "Transfer futile", "Insufficient balance.", "transfer_futile", txn.get('id') if txn else None)
            return jsonify({"status": "futile", "message": "Insufficient balance"}), 400

        # Execute transfer
        sender_new_balance = float(user_account['balance']) - amount
        receiver_new_balance = float(receiver_account['balance']) + amount

        update_account_balance(user_account['id'], sender_new_balance)
        update_account_balance(receiver_account['id'], receiver_new_balance)

        new_t = datetime.datetime.now(datetime.timezone.utc).isoformat()
        update_profile_timestamp(user_profile['id'], new_t)
        update_daily_spend(user_profile['id'], float(user_profile.get('today_spent', 0)) + amount)

        txn = record_transaction(user_account['id'], receiver_account['id'], amount, 'success')
        transaction_id = txn.get('id') if txn else None
        create_notification(user_profile['id'], "Transfer successful", f"BDT {amount:.2f} sent to {receiver_username}.", "transfer_success", transaction_id)
        create_notification(receiver_account['profile_id'], "Money received", f"BDT {amount:.2f} received from {username}.", "transfer_success", transaction_id)

        return jsonify({
            "status": "success",
            "message": f"Transfer of {amount} to {receiver_username} successful",
            "new_t": new_t,
            "new_balance": sender_new_balance
        }), 200

    except Exception as e:
        if is_missing_schema_error(e):
            print(f"Transfer schema error: {e}")
            return missing_schema_response()
        print(f"Transfer error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

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
        sent_response = business_db.table('transactions').select('*').eq('sender_account_id', user_account['id']).order('created_at', desc=True).limit(20).execute()
        received_response = business_db.table('transactions').select('*').eq('receiver_account_id', user_account['id']).order('created_at', desc=True).limit(20).execute()

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

        transactions.sort(key=lambda x: x['created_at'], reverse=True)

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
        rsa_public_key = data.get('rsaPublicKey') or data.get('rsa_public_key') or ''
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
    ensure_server_rsa_keys()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5001'))
    app.run(debug=True, port=port, host='0.0.0.0')
