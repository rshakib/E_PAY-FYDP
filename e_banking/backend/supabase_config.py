"""
Supabase Configuration — Dual Database Setup

DB1 (Identity): Profiles, PII, crypto keys
DB2 (Business): Accounts, transactions, notifications
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env.backend')

# ============================================
# DB1: Identity/Auth Database
# ============================================
IDENTITY_SUPABASE_URL = os.environ.get('IDENTITY_SUPABASE_URL', '')
IDENTITY_SUPABASE_KEY = os.environ.get('IDENTITY_SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('IDENTITY_SUPABASE_ANON_KEY', '')

# ============================================
# DB2: Business/Transaction Database
# ============================================
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY', '')

# ============================================
# PII Encryption
# ============================================
PII_ENCRYPTION_KEY = os.environ.get('PII_ENCRYPTION_KEY', '')
PII_HMAC_PEPPER = os.environ.get('PII_HMAC_PEPPER', '')
