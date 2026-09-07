import os
import uuid
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env.backend')

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.backend.")
    print("Please set these variables to run the admin seed operations.")
    sys.exit(1)

# Initialize Supabase client with Service Role Key (bypasses RLS)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Define Entities to seed
merchants = [
    {"username": "supermart", "name": "SuperMart Central", "code": "MCH-SUPERMART", "category": "merchant_payment"},
    {"username": "techhaven", "name": "Tech Haven", "code": "MCH-TECHHAVEN", "category": "merchant_payment"},
    {"username": "citycafe", "name": "City Cafe", "code": "MCH-CITYCAFE", "category": "merchant_payment"}
]

billers = [
    {"username": "desco", "name": "DESCO Electricity", "code": "BLR-DESCO", "category": "bill_payment"},
    {"username": "wasa", "name": "Dhaka WASA", "code": "BLR-WASA", "category": "bill_payment"},
    {"username": "gas_service", "name": "Titas Gas Service", "code": "BLR-GAS", "category": "bill_payment"}
]

operators = [
    {"username": "gp", "name": "Grameenphone"},
    {"username": "robi", "name": "Robi"},
    {"username": "airtel", "name": "Airtel"},
    {"username": "banglalink", "name": "Banglalink"},
    {"username": "teletalk", "name": "Teletalk"}
]

def seed_profile_and_account(username, display_name, is_merchant_or_biller=False, code=None, category=None, is_biller=False):
    print(f"\nProcessing seeding for entity: @{username} ({display_name})...")
    
    # Check if profile already exists
    try:
        response = supabase.table('profiles').select('id').eq('registration_number', username).execute()
        if response.data and len(response.data) > 0:
            print(f"Profile @{username} already exists with ID: {response.data[0]['id']}. Skipping.")
            return
    except Exception as e:
        print(f"Error checking profile existence: {e}")
        return

    # Step 1: Create Supabase Auth user via Admin API
    synthetic_email = f"{username}@niropay.com"
    random_password = uuid.uuid4().hex + uuid.uuid4().hex  # Generate unmatchable locked password
    
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": synthetic_email,
            "password": random_password,
            "email_confirm": True,
            "user_metadata": {"username": username}
        })
        auth_user_id = auth_response.user.id
        print(f"-> Auth User created successfully with UUID: {auth_user_id}")
    except Exception as auth_err:
        print(f"-> Auth creation error for @{username}: {auth_err}")
        return

    # Step 2: Create profile record with locked hashes and default daily values
    profile_data = {
        'id': auth_user_id,
        'registration_number': username,
        'password_hash': 'locked_account_no_login_auth',
        'password_key_k2': 'locked_entity_k2',
        'hmac_key_k1': 'locked_entity_k1',
        'fingerprint_bp': '123456',
        'nid_brc_hash': 'locked_entity_nid',
        'activation_code_hash': 'locked_entity_activation',
        'full_name': display_name,
        'daily_limit': 500000.0,  # Elevated limits for recipients
        'today_spent': 0.0
    }

    try:
        supabase.table('profiles').insert(profile_data).execute()
        print(f"-> Profiles table entry successfully created.")
    except Exception as prof_err:
        print(f"-> Profile insertion failed: {prof_err}")
        # Cleanup orphaned auth user
        try:
            supabase.auth.admin.delete_user(auth_user_id)
        except Exception:
            pass
        return

    # Step 3: Create linked account ledger record with initial zero balance
    account_data = {
        'profile_id': auth_user_id,
        'balance': 0.00,
        'is_active': True,
        'account_type': 'biller' if is_biller else 'merchant' if is_merchant_or_biller else 'personal',
        'account_number': f"ACC-{username.upper()}"
    }

    account_id = None
    try:
        acc_resp = supabase.table('accounts').insert(account_data).execute()
        if acc_resp.data:
            account_id = acc_resp.data[0]['id']
            print(f"-> Accounts table entry successfully created (Account UUID: {account_id}).")
    except Exception as acc_err:
        print(f"-> Account insertion failed: {acc_err}")
        # Cleanup profile and auth user
        try:
            supabase.table('profiles').delete().eq('id', auth_user_id).execute()
            supabase.auth.admin.delete_user(auth_user_id)
        except Exception:
            pass
        return

    # Step 4: Map to merchants_or_billers if applicable
    if is_merchant_or_biller and account_id and code and category:
        mch_biller_data = {
            'profile_id': auth_user_id,
            'account_id': account_id,
            'display_name': display_name,
            'merchant_code': code,
            'category': category,
            'is_active': True
        }
        try:
            supabase.table('merchants_or_billers').insert(mch_biller_data).execute()
            print(f"-> merchants_or_billers mapping created successfully.")
        except Exception as mch_err:
            print(f"-> merchants_or_billers mapping insertion failed: {mch_err}")

def main():
    print("====================================================")
    # 1. Seed Merchants
    print("Phase 1: Seeding Merchants")
    for m in merchants:
        seed_profile_and_account(
            username=m["username"], 
            display_name=m["name"], 
            is_merchant_or_biller=True, 
            code=m["code"], 
            category=m["category"]
        )

    # 2. Seed Billers
    print("\nPhase 2: Seeding Billers")
    for b in billers:
        seed_profile_and_account(
            username=b["username"], 
            display_name=b["name"], 
            is_merchant_or_biller=True, 
            code=b["code"], 
            category=b["category"],
            is_biller=True
        )

    # 3. Seed Mobile Operators
    print("\nPhase 3: Seeding Mobile Operators")
    for o in operators:
        seed_profile_and_account(
            username=o["username"], 
            display_name=o["name"]
        )
    print("\n====================================================")
    print("Seed operations audit check completed.")

if __name__ == "__main__":
    main()
