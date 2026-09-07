import copy
import datetime
import uuid
from types import SimpleNamespace

from werkzeug.security import generate_password_hash


class FakeSupabaseResponse:
    def __init__(self, data=None):
        self.data = data or []


class FakeTableQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = []
        self.order_field = None
        self.order_desc = False
        self.limit_count = None
        self.insert_payload = None
        self.update_payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, field, desc=False):
        self.order_field = field
        self.order_desc = desc
        return self

    def limit(self, count):
        self.limit_count = count
        return self

    def insert(self, payload):
        self.insert_payload = payload
        return self

    def update(self, payload):
        self.update_payload = payload
        return self

    def execute(self):
        if self.insert_payload is not None:
            rows = self.insert_payload if isinstance(self.insert_payload, list) else [self.insert_payload]
            inserted = []
            for row in rows:
                new_row = copy.deepcopy(row)
                if "id" not in new_row:
                    new_row["id"] = f"{self.table_name}-{uuid.uuid4()}"
                if "created_at" not in new_row and self.table_name in {"transactions", "notifications"}:
                    new_row["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                self.client.tables[self.table_name].append(new_row)
                inserted.append(copy.deepcopy(new_row))
            return FakeSupabaseResponse(inserted)

        rows = self._matching_rows()

        if self.update_payload is not None:
            updated = []
            for row in rows:
                row.update(copy.deepcopy(self.update_payload))
                updated.append(copy.deepcopy(row))
            return FakeSupabaseResponse(updated)

        result = [copy.deepcopy(row) for row in rows]
        if self.order_field:
            result.sort(key=lambda row: row.get(self.order_field, ""), reverse=self.order_desc)
        if self.limit_count is not None:
            result = result[: self.limit_count]
        return FakeSupabaseResponse(result)

    def _matching_rows(self):
        rows = self.client.tables[self.table_name]
        for field, value in self.filters:
            rows = [row for row in rows if row.get(field) == value]
        return rows


class FakeAuthAdmin:
    def __init__(self, client):
        self.client = client

    def create_user(self, payload):
        user_id = f"fake-auth-{uuid.uuid4()}"
        self.client.auth_users[user_id] = copy.deepcopy(payload)
        return SimpleNamespace(user=SimpleNamespace(id=user_id))

    def delete_user(self, user_id):
        self.client.auth_users.pop(user_id, None)


class FakeSupabaseClient:
    def __init__(self, crypto):
        self.crypto = crypto
        self.auth_users = {}
        self.auth = SimpleNamespace(admin=FakeAuthAdmin(self))
        self.reset()

    def table(self, table_name):
        if table_name not in self.tables:
            self.tables[table_name] = []
        return FakeTableQuery(self, table_name)

    def reset(self):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        alice_k1 = self.crypto.generate_hmac("ACT-ALICE", "NID-ALICE|alice|123456")
        bob_k1 = self.crypto.generate_hmac("ACT-BOB", "NID-BOB|bob|123456")
        self.tables = {
            "profiles": [
                {
                    "id": "profile-alice",
                    "registration_number": "alice",
                    "password_hash": generate_password_hash("AlicePass123!"),
                    "password_key_k2": self.crypto.stretch_password("AlicePass123!", "NID-ALICE"),
                    "fingerprint_bp": "123456",
                    "hmac_key_k1": alice_k1,
                    "nid_brc_hash": self.crypto.generate_hmac("ACT-ALICE", "NID-ALICE"),
                    "activation_code_hash": self.crypto.generate_hmac("NID-ALICE", "ACT-ALICE"),
                    "timestamp_t": now,
                    "daily_limit": 5000.0,
                    "today_spent": 0.0,
                },
                {
                    "id": "profile-bob",
                    "registration_number": "bob",
                    "password_hash": generate_password_hash("BobPass123!"),
                    "password_key_k2": self.crypto.stretch_password("BobPass123!", "NID-BOB"),
                    "fingerprint_bp": "123456",
                    "hmac_key_k1": bob_k1,
                    "nid_brc_hash": self.crypto.generate_hmac("ACT-BOB", "NID-BOB"),
                    "activation_code_hash": self.crypto.generate_hmac("NID-BOB", "ACT-BOB"),
                    "timestamp_t": now,
                    "daily_limit": 5000.0,
                    "today_spent": 0.0,
                },
            ],
            "accounts": [
                {
                    "id": "account-alice",
                    "profile_id": "profile-alice",
                    "balance": 5000.0,
                    "is_active": True,
                    "account_number": "ACC-alice",
                },
                {
                    "id": "account-bob",
                    "profile_id": "profile-bob",
                    "balance": 1500.0,
                    "is_active": True,
                    "account_number": "ACC-bob",
                },
            ],
            "transactions": [],
            "notifications": [],
        }


def create_fake_supabase_client(crypto):
    return FakeSupabaseClient(crypto)
