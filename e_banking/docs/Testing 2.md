# Testing 2

## 1. Overview

This document contains the second round of testing for the E-Banking / E-Payment system. The purpose of this round is to avoid repeating tests that were already formally documented and to add new testing for missing areas.

The following test areas were requested:

| Requested Test Area | Decision | Reason |
| --- | --- | --- |
| Cryptographic Testing, unit testing | Skipped as duplicate | Already documented in `Testing/Test1_Unit_Crypto/test_crypto.py` with 8 crypto unit tests |
| Transaction Flow, integration testing | Skipped as duplicate | Already documented in `Testing/Test2_Integration_Transaction/test_transaction_flow.py` |
| Replay Attack Prevention, security testing | Done now also | Previously documented, and now retested inside Testing 2 |
| Performance Testing | Done now | Added new second-round offline tests |
| Input Validation and Security Vulnerability Scanning | Done now | Added new black-box, white-box, robustness, and security scan tests |
| Additional functional, non-functional, white/black box, attack testing | Done now | Added notification, transaction history, daily-spend, self-transfer, IDOR, sensitive response, CORS, header, and traversal tests |

The new test runner created for this round is:

```text
tests/security/testing2_extended_runner.py
```

Command executed:

```powershell
python tests/security/testing2_extended_runner.py
```

Generated reports:

```text
reports/testing-2-latest.md
reports/testing-2-latest.json
reports/testing-2-20260611-012204.md
reports/testing-2-20260611-012204.json
```

Execution mode:

| Field | Value |
| --- | --- |
| Test mode | Offline Flask test client |
| Database mode | Fake in-memory sandbox database |
| Environment flag | `SANDBOX_FAKE_DB=1` |
| Production data used | No |
| Real Supabase used | No |
| External network used | No |
| Local execution date | 2026-06-11, Asia/Dhaka |

Final result for Testing 2:

| Status | Count |
| --- | ---: |
| PASS | 18 |
| FAIL | 8 |
| WARN | 2 |
| Total | 28 |

Status meaning:

| Status | Meaning |
| --- | --- |
| PASS | Expected behavior was found |
| FAIL | Required behavior was missing or a vulnerability was observed |
| WARN | Behavior needs configuration review or manual confirmation |

## 2. Previous Testing Skipped

### 2.1 Cryptographic Testing

Existing file:

```text
Testing/Test1_Unit_Crypto/test_crypto.py
```

Previously documented coverage:

| Test ID | Test Name | Previous Result |
| --- | --- | --- |
| TC-1.1 | AES-256 encrypt and decrypt roundtrip | PASS |
| TC-1.2 | HMAC-SHA256 deterministic output | PASS |
| TC-1.3 | Dynamic AES key derivation | PASS |
| TC-1.4 | Altered ciphertext fails | PASS |
| TC-1.5 | Altered HMAC mismatch detection | PASS |
| TC-1.6 | Same plaintext with different timestamp | PASS |
| TC-1.7 | PBKDF2 password stretching | PASS |
| TC-1.8 | Multiple encryption/decryption cycles | PASS |

Local rerun note:

```text
python -m pytest Testing\Test1_Unit_Crypto\test_crypto.py -q
```

This command could not run in the current environment because `pytest` is not installed:

```text
No module named pytest
```

Evaluation:

The crypto tests already exist and were previously documented, so no duplicate cryptographic unit test file was added in Testing 2.

### 2.2 Transaction Flow Integration Testing

Existing file:

```text
Testing/Test2_Integration_Transaction/test_transaction_flow.py
```

Previously documented result:

| Suite | Total | Passed | Failed |
| --- | ---: | ---: | ---: |
| Transaction Flow Integration | 11 | 10 | 1 |

Known previous issue:

```text
TC-2.8 Transaction History 500 Error
```

Evaluation:

The integration test already covers registration, login, encrypted transfer, invalid receiver, insufficient balance, balance retrieval, transaction history, and screenshots. It was not duplicated.

### 2.3 Previous Replay Attack Prevention

Existing file:

```text
Testing/Test3_Security_Replay/test_replay_attack.py
```

Previously documented result:

| Suite | Total | Passed | Failed |
| --- | ---: | ---: | ---: |
| Replay Attack Prevention | 7 | 7 | 0 |

Existing replay coverage:

| Test ID | Test Name | Previous Result |
| --- | --- | --- |
| TC-3.1 | Same payload twice, second rejected | PASS |
| TC-3.2 | Stale timestamp payload rejected | PASS |
| TC-3.3 | Corrupted ciphertext rejected | PASS |
| TC-3.4 | Missing fields return 400 | PASS |
| TC-3.5 | No auth token returns 401 | PASS |

Previous evaluation:

Replay prevention was already formally documented, but the user requested that replay attack testing also be included inside this Testing 2 document. Therefore, a new replay retest was added to the Testing 2 runner and documented below.

## 3. New Testing 2 Runner

### 3.1 Sandbox Setup Code

The new runner forces fake database mode before importing the backend app.

```python
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "e_banking" / "backend"
REPORTS_DIR = REPO_ROOT / "reports"

os.environ["SANDBOX_FAKE_DB"] = "1"
os.environ.setdefault("SUPABASE_URL", "https://sandbox.invalid")
os.environ.setdefault("SUPABASE_KEY", "sandbox-key-not-used")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "sandbox-service-key-not-used")
os.environ.setdefault("FLASK_ENV", "testing")

sys.path.insert(0, str(BACKEND_DIR))

import app as banking_app
```

Evaluation:

This prevents accidental testing against production data. The tests run against fake users and fake balances only.

### 3.2 Test Result Model Code

Each finding is stored in a structured result object.

```python
@dataclass
class TestResult:
    test_id: str
    category: str
    title: str
    test_type: str
    severity: str
    status: str
    expected: str
    actual: str
    recommendation: str
    code_reference: str = ""
```

Evaluation:

This keeps each test result consistent and makes it possible to generate Markdown and JSON reports.

### 3.3 Runner Helper Code

The runner uses Flask's in-process test client.

```python
class Testing2Runner:
    def __init__(self):
        banking_app.app.config["TESTING"] = True
        self.app_module = banking_app
        self.client = banking_app.app.test_client()
        self.results: list[TestResult] = []

    def reset(self):
        if hasattr(self.app_module.supabase, "reset"):
            self.app_module.supabase.reset()
        self.app_module.active_sessions.clear()
```

Authentication helper:

```python
def login(self, username="alice", password="AlicePass123!"):
    return self.client.post("/login", json={"username": username, "password": password})

def auth_header(self, username="alice", password="AlicePass123!"):
    response = self.login(username, password)
    data = response.get_json() or {}
    return {"Authorization": f"Bearer {data.get('token')}"}
```

Encrypted transfer helper:

```python
def transfer_body(self, sender, receiver, amount, message_override=None):
    profile = self.app_module.get_user_profile(sender)
    message = message_override or f"Receiver:{receiver}|Amt:{amount}"
    f1 = self.app_module.crypto.generate_hmac(profile["hmac_key_k1"], message)
    encrypted = self.app_module.crypto.encrypt_data(
        message,
        f1,
        profile["password_key_k2"],
        profile.get("fingerprint_bp") or "123456",
        profile["timestamp_t"],
    )
    return {"username": sender, "payload": encrypted["payload"], "iv": encrypted["iv"]}
```

Evaluation:

The helper creates realistic encrypted transfer payloads using the backend's own crypto engine. This makes the new tests useful for both black-box and white-box validation.

## 4. Replay Attack Prevention Retest

### 4.1 Duplicate Payload Replay Code

This test sends one valid encrypted transfer payload and then sends the exact same encrypted payload again.

```python
token_header = self.auth_header()
replay_body = self.transfer_body("alice", "bob", 10)
first = self.client.post("/transfer", headers=token_header, json=replay_body)
second = self.client.post("/transfer", headers=token_header, json=replay_body)
```

Expected result:

```text
First request: success
Second request: rejected
```

Actual result:

```text
First status 200
Replay status 401
```

### 4.2 Stale Timestamp Replay Code

This test saves Alice's old timestamp `T`, performs one successful transfer so the backend rotates `T`, then creates another encrypted payload using the old timestamp.

```python
self.reset()
token_header = self.auth_header()
profile = self.app_module.get_user_profile("alice")
old_t = profile["timestamp_t"]
first_body = self.transfer_body("alice", "bob", 10)
first = self.client.post("/transfer", headers=token_header, json=first_body)

message = "Receiver:bob|Amt:5"
f1 = self.app_module.crypto.generate_hmac(profile["hmac_key_k1"], message)
stale_encrypted = self.app_module.crypto.encrypt_data(
    message,
    f1,
    profile["password_key_k2"],
    profile.get("fingerprint_bp") or "123456",
    old_t,
)
stale_body = {
    "username": "alice",
    "payload": stale_encrypted["payload"],
    "iv": stale_encrypted["iv"],
}
stale = self.client.post("/transfer", headers=token_header, json=stale_body)
```

Expected result:

```text
Payload encrypted with old timestamp T should fail after T rotation.
```

Actual result:

```text
First status 200
Stale timestamp status 401
```

### 4.3 Replay Attack Results

| Test ID | Test Case | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| REPLAY2-001 | Duplicate encrypted transfer payload is rejected | First succeeds, replay fails | First 200; replay 401 | PASS |
| REPLAY2-002 | Stale timestamp transfer payload is rejected | Old timestamp payload fails after T rotation | First 200; stale 401 | PASS |

Evaluation:

The replay attack retest passed. The backend rejected both the exact duplicate encrypted payload and a payload encrypted using a stale timestamp. This confirms that timestamp `T` rotation is working as replay protection in the offline sandbox. For stronger production security, a nonce or transaction ID cache should still be considered.

## 5. Performance Testing

### 5.1 Performance Timing Code

```python
def timed(self, fn, iterations):
    durations = []
    statuses = []
    for _ in range(iterations):
        start = time.perf_counter()
        response = fn()
        durations.append((time.perf_counter() - start) * 1000)
        statuses.append(response.status_code)
    return durations, statuses
```

Health endpoint test:

```python
health_times, health_statuses = self.timed(lambda: self.client.get("/health"), 100)
```

Login endpoint test:

```python
login_times, login_statuses = self.timed(lambda: self.login(), 50)
```

Authenticated profile lookup test:

```python
profile_times, profile_statuses = self.timed(
    lambda: self.client.get("/user/alice", headers=token_header),
    50,
)
```

Encrypted transfer performance test:

```python
for _ in range(10):
    body = self.transfer_body("alice", "bob", 1)
    start = time.perf_counter()
    response = self.client.post("/transfer", headers=token_header, json=body)
    transfer_times.append((time.perf_counter() - start) * 1000)
    transfer_statuses.append(response.status_code)
```

### 5.2 Performance Results

| Test ID | Test Case | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| PERF-001 | Health endpoint response time | 100 requests, p95 below 100 ms | avg=0.16 ms; p95=0.26 ms; status 200 | PASS |
| PERF-002 | Login endpoint response time | 50 requests, p95 below 250 ms | avg=98.94 ms; p95=103.22 ms; status 200 | PASS |
| PERF-003 | Authenticated profile lookup response time | 50 requests, p95 below 150 ms | avg=0.18 ms; p95=0.20 ms; status 200 | PASS |
| PERF-004 | Encrypted transfer response time | 10 transfers, p95 below 750 ms | avg=0.38 ms; p95=0.51 ms; status 200 | PASS |

Evaluation:

The tested backend functions performed well in the offline sandbox. These are local in-process timings, so they do not represent real network or production Supabase latency. However, they confirm that the route logic itself is lightweight in fake database mode.

## 6. Input Validation Testing

### 6.1 Required Field Validation Code

```python
missing_login = self.client.post("/login", json={"username": "alice"})

missing_register = self.client.post(
    "/register",
    json={"username": "new_user", "password": "Pass123!", "nid": "NID-NEW"},
)

duplicate = self.client.post(
    "/register",
    json={
        "username": "alice",
        "password": "AlicePass123!",
        "nid": "NID-ALICE",
        "activationCode": "ACT-ALICE",
    },
)
```

### 6.2 Invalid JSON Robustness Code

```python
text_login = self.client.post("/login", data="username=alice", content_type="text/plain")

malformed_json = self.client.post("/login", data="{", content_type="application/json")
```

### 6.3 Username Validation Code

```python
script_username = "<script>alert(1)</script>"
script_register = self.client.post(
    "/register",
    json={
        "username": script_username,
        "password": "ScriptPass123!",
        "nid": "NID-XSS-2",
        "activationCode": "ACT-XSS-2",
    },
)

long_username = "u" * 512
long_register = self.client.post(
    "/register",
    json={
        "username": long_username,
        "password": "LongPass123!",
        "nid": "NID-LONG",
        "activationCode": "ACT-LONG",
    },
)
```

### 6.4 Encrypted Message Validation Code

```python
bad_message_body = self.transfer_body("alice", "bob", 10, message_override="ReceiverOnly:Bob")
bad_message = self.client.post("/transfer", headers=token_header, json=bad_message_body)

nonnumeric_body = self.transfer_body(
    "alice",
    "bob",
    10,
    message_override="Receiver:bob|Amt:not-a-number",
)
nonnumeric = self.client.post("/transfer", headers=token_header, json=nonnumeric_body)
```

### 6.5 Input Validation Results

| Test ID | Test Case | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| IVS-001 | Login rejects missing password | 400 | Status 400 | PASS |
| IVS-002 | Register rejects missing activation code | 400 | Status 400 | PASS |
| IVS-003 | Register rejects duplicate username | 400 | Status 400 | PASS |
| IVS-004 | Login handles non-JSON request safely | 400 or 415, not 500 | Status 500 | FAIL |
| IVS-005 | Login handles malformed JSON safely | 400 or 415, not 500 | Status 500 | FAIL |
| IVS-006 | Register rejects script-like username | Reject or canonicalize | Status 201 | FAIL |
| IVS-007 | Register rejects overlong username | Reject | Status 201 | FAIL |
| IVS-008 | Transfer rejects malformed encrypted message | 400 | Status 400 | PASS |
| IVS-009 | Transfer rejects nonnumeric amount | 400 | Status 400 | PASS |

Evaluation:

Required fields, duplicate usernames, malformed encrypted transfer messages, and nonnumeric encrypted transfer amounts are handled correctly. However, the login endpoint returns HTTP 500 for non-JSON and malformed JSON bodies. Registration also accepts script-like and overlong usernames. These should be fixed with strict request parsing and server-side field validation.

## 7. Additional Functional Testing

### 7.1 Notification Test Code

```python
token_header = self.auth_header()
notification = self.client.get("/notifications/alice", headers=token_header)
notification_data = notification.get_json() or {}
```

### 7.2 Transaction History Test Code

```python
transfer = self.client.post(
    "/transfer",
    headers=token_header,
    json=self.transfer_body("alice", "bob", 25),
)
tx_alice = self.client.get("/transactions/alice", headers=token_header)
tx_data = tx_alice.get_json() or {}
has_success = any(txn.get("status") == "success" for txn in tx_data.get("transactions", []))
```

### 7.3 Daily Spend Test Code

```python
profile_after = self.client.get("/user/alice", headers=token_header)
profile_data = profile_after.get_json() or {}
today_spent = profile_data.get("user", {}).get("today_spent")
```

### 7.4 Self-Transfer Test Code

```python
self_transfer = self.client.post(
    "/transfer",
    headers=token_header,
    json=self.transfer_body("alice", "alice", 10),
)
```

### 7.5 Additional Functional Results

| Test ID | Test Case | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| FUNC2-001 | Authenticated notification list works | 200 with notifications array | Status 200; notifications key exists | PASS |
| FUNC2-002 | Successful transfer appears in sender history | Transfer and history both succeed | transfer=200; history=200; success found | PASS |
| FUNC2-003 | Daily spend updates after transfer | today_spent at least 25 | today_spent=25.0 | PASS |
| FUNC2-004 | Self-transfer is blocked | 400 | Status 400 | PASS |

Evaluation:

The new functional checks passed in sandbox mode. Notification retrieval, transaction history, daily-spend update, and self-transfer blocking are working.

## 8. Input Validation and Security Vulnerability Scanning

### 8.1 IDOR Scan Code

The following tests check whether Alice's token can access Bob's private resources.

```python
alice_header = self.auth_header("alice", "AlicePass123!")

bob_profile = self.client.get("/user/bob", headers=alice_header)

bob_transactions = self.client.get("/transactions/bob", headers=alice_header)

bob_notifications = self.client.get("/notifications/bob", headers=alice_header)
```

### 8.2 Sensitive Response Scan Code

```python
login_data = (self.login().get_json() or {}).get("user", {})
exposed = [
    field
    for field in ["k1", "k2", "password_hash", "nid_brc_hash", "activation_code_hash"]
    if field in login_data
]

profile_data = (self.client.get("/user/alice", headers=alice_header).get_json() or {}).get("user", {})
profile_secret_fields = [
    field
    for field in ["password", "password_hash", "password_key_k2", "hmac_key_k1", "nid_brc_hash"]
    if field in profile_data
]
```

### 8.3 HTTP Method and Path Traversal Scan Code

```python
get_login = self.client.get("/login")
get_login_text = get_login.get_data(as_text=True)
leaks_api_data = any(secret in get_login_text for secret in ["\"token\"", "\"k1\"", "\"k2\""])

traversal = self.client.get("/..%2F..%2Fe_banking%2Fbackend%2Fapp.py")
traversal_text = traversal.get_data(as_text=True)
leaked_source = "def login" in traversal_text and "SUPABASE" in traversal_text
```

### 8.4 CORS and Security Header Scan Code

```python
cors_response = self.client.get("/health", headers={"Origin": "https://attacker.example"})
allow_origin = cors_response.headers.get("Access-Control-Allow-Origin", "")

header_response = self.client.get("/health")
required_headers = ["X-Content-Type-Options", "Content-Security-Policy", "X-Frame-Options"]
missing_headers = [header for header in required_headers if header not in header_response.headers]
```

### 8.5 Security Scan Results

| Test ID | Test Case | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| SCAN-001 | IDOR scan: profile endpoint | Alice cannot access Bob profile | Status 200 | FAIL |
| SCAN-002 | IDOR scan: transaction endpoint | Alice cannot access Bob transactions | Status 200 | FAIL |
| SCAN-003 | IDOR scan: notification endpoint | Alice cannot access Bob notifications | Status 200 | FAIL |
| SCAN-004 | Sensitive login response scan | No secret fields | Exposed `k1`, `k2` | FAIL |
| SCAN-005 | Sensitive profile response scan | No secret fields | None exposed | PASS |
| SCAN-006 | GET `/login` does not leak API data | No token or crypto keys | No API data leaked | PASS |
| SCAN-007 | Path traversal source exposure | Backend source not exposed | No source leaked | PASS |
| SCAN-008 | CORS configuration scan | Trusted origins only | Allows `https://attacker.example` | WARN |
| SCAN-009 | Security header scan | Security headers present | Missing CSP, X-Frame-Options, X-Content-Type-Options | WARN |

Evaluation:

The major security issue found in Testing 2 is IDOR, also called insecure direct object reference. An authenticated user's bearer token can access another user's profile, transaction history, and notifications. The login response also exposes `k1` and `k2`, which are sensitive cryptographic values. CORS and security headers should be configured more strictly for production.

## 9. Report Generation Code

The runner writes Markdown and JSON reports.

```python
def write_reports(results: list[TestResult], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / f"testing-2-{timestamp}.json"
    md_path = output_dir / f"testing-2-{timestamp}.md"
    latest_json = output_dir / "testing-2-latest.json"
    latest_md = output_dir / "testing-2-latest.md"

    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mode": "offline Flask test client with SANDBOX_FAKE_DB=1",
        "target": "local in-process Flask app; no external website or Supabase project",
        "summary": summarize(results),
        "results": [asdict(result) for result in results],
    }
```

Main execution code:

```python
def main():
    runner = Testing2Runner()
    results = runner.run_all()
    md_path, json_path = write_reports(results, REPORTS_DIR)
    counts = summarize(results)

    print("Testing 2 completed.")
    print("Mode: SANDBOX_FAKE_DB=1; offline Flask test client")
    print(f"Summary: {counts}")
    print(f"Markdown report: {md_path}")
    print(f"JSON report: {json_path}")
    return 0
```

Evaluation:

The runner produces reproducible test evidence in both human-readable and machine-readable formats.

## 10. Issues Found in Testing 2

| Area | Issue | Priority |
| --- | --- | --- |
| Request parsing | Non-JSON login request returns 500 | High |
| Request parsing | Malformed JSON login request returns 500 | High |
| Input validation | Script-like username is accepted | High |
| Input validation | 512-character username is accepted | Medium |
| Authorization | Alice's token can access Bob's profile | High |
| Authorization | Alice's token can access Bob's transactions | Critical |
| Authorization | Alice's token can access Bob's notifications | High |
| Secret exposure | Login response exposes `k1` and `k2` | Critical |
| CORS | Unexpected origin is allowed | Medium |
| Security headers | CSP, X-Frame-Options, and X-Content-Type-Options are missing | Medium |

## 11. Recommended Fixes

| Priority | Fix |
| --- | --- |
| Critical | Remove `k1` and `k2` from login responses and keep cryptographic secrets server-side |
| Critical | Bind `/transactions/<username>` to the authenticated session user |
| High | Bind `/user/<username>` and `/notifications/<username>` to the authenticated session user |
| High | Use safe JSON parsing such as `request.get_json(silent=True)` and return controlled 400 or 415 responses |
| High | Add username allow-list validation and length limits |
| Medium | Restrict CORS to trusted frontend origins |
| Medium | Add security headers in Flask or Nginx |

## 12. Final Evaluation

Testing 2 added 28 new test cases across replay attack prevention, performance, input validation, functional behavior, non-functional behavior, black-box attack checks, white-box response scanning, and security configuration checks.

The system performed well in offline performance testing. Additional functional behavior also passed, including notifications, transaction history, daily spend update, and self-transfer blocking.

The main weaknesses found are request parsing robustness, username validation, cross-user authorization, sensitive login response data, permissive CORS, and missing security headers.

Final result:

```text
Total tests: 28
PASS: 18
FAIL: 8
WARN: 2
```
