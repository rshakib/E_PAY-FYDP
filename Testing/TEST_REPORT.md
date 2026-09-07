# Testing Report — Security Enhanced E-Payment System

**Project:** E-PAY (E-Banking System)  
**Date:** June 10, 2026  
**Environment:** Local — Flask dev server (https://localhost:5001)  
**Database:** Supabase (Cloud PostgreSQL)

---

## Table of Contents

1. [Test Execution Summary](#1-test-execution-summary)
2. [Test 1: Unit Testing — Cryptographic Functions](#2-test-1-unit-testing--cryptographic-functions)
3. [Test 2: Integration Testing — Transaction Flow](#3-test-2-integration-testing--transaction-flow)
4. [Test 3: Security Testing — Replay Attack Prevention](#4-test-3-security-testing--replay-attack-prevention)
5. [Bug Report: TC-2.8 Transaction History 500 Error](#5-bug-report-tc-28-transaction-history-500-error)
6. [Detailed Test Results Spreadsheet](#6-detailed-test-results-spreadsheet)

---

## 1. Test Execution Summary

| Test Suite       | Total Tests | Passed | Failed | Pass Rate |
|------------------|:-----------:|:------:|:------:|:---------:|
| Test 1 — Crypto  | 8           | 8      | 0      | **100%**  |
| Test 2 — Integration | 11      | 10     | 1      | **91%**   |
| Test 3 — Replay  | 7           | 7      | 0      | **100%**  |
| **Overall**      | **26**      | **25** | **1**  | **96%**   |

**1 Bug Found:** `GET /transactions/<username>` returns HTTP 500 Internal Server Error (see [Section 5](#5-bug-report-tc-28-transaction-history-500-error)).

---

## 2. Test 1: Unit Testing — Cryptographic Functions

**Objective:** Verify that AES-256 CBC encryption/decryption, HMAC-SHA256 generation, PBKDF2 key stretching, and dynamic AES key derivation (K2 + Bp + T) produce correct and consistent outputs in isolation.

**Approach:** Python `pytest` tests against the `CryptoEngine` class from `backend/crypto.py`.

### Test Cases & Results

| ID     | Test Name                              | Result | Notes |
|--------|----------------------------------------|:------:|-------|
| TC-1.1 | AES-256 Encrypt → Decrypt Roundtrip    | ✅ PASS | Message `"Receiver:Alice\|Amt:500"` encrypted and decrypted successfully. F1 preserved. |
| TC-1.2 | HMAC-SHA256 Deterministic Output       | ✅ PASS | Same key+message → same hash. Different key → different hash. |
| TC-1.3 | Key Derivation (K2+Bp+T) Deterministic | ✅ PASS | Same inputs → same 32-byte key. Different T or K2 → different key. |
| TC-1.4 | Altered Ciphertext → Decryption Fails  | ✅ PASS | Flipping one byte causes `decrypt_data()` to return `None`. |
| TC-1.5 | Altered HMAC → Mismatch Detection      | ✅ PASS | F1 (wrong key) ≠ F2 (correct key). Integrity verification works. |
| TC-1.6 | Same Plaintext + Different T           | ✅ PASS | Different T values produce different ciphertexts (timestamp binding). |
| TC-1.7 | PBKDF2 Password Stretching             | ✅ PASS | 64-char hex output deterministic. Different NID → different output. |
| TC-1.8 | Multiple Encrypt/Decrypt Cycles        | ✅ PASS | Amounts 50, 9999.99, 0.01 — all roundtrips succeed. |

### Commands Run

```bash
cd Testing
python -m pytest Test1_Unit_Crypto/test_crypto.py -v
```

---

## 3. Test 2: Integration Testing — Transaction Flow

**Objective:** Ensure the full transaction pipeline works correctly: user registration → login → transaction encryption → server decryption → approval/rejection.

**Approach:** Python `requests` library for API calls + `Playwright` for browser UI screenshots.

### Test Cases & Results

| ID     | Test Name                              | Result | Notes |
|--------|----------------------------------------|:------:|-------|
| TC-2.0 | Backend Health Check                   | ✅ PASS | `GET /health` → 200 OK |
| TC-2.1 | User Registration                      | ✅ PASS | HTTP 201, account created |
| TC-2.2 | Login Returns Crypto Keys              | ✅ PASS | K1, K2, Bp, T, balance, accountId all present |
| TC-2.3 | Valid Transfer Success                 | ✅ PASS | HTTP 200, `new_t` and `new_balance` returned |
| TC-2.4 | Tampered HMAC Rejection                | ✅ PASS | HTTP 401 — transaction blocked (HMAC mismatch causes key derivation to fail) |
| TC-2.5 | Invalid Receiver → 404                 | ✅ PASS | `"Receiver not found"` |
| TC-2.6 | Insufficient Balance → 400 Futile      | ✅ PASS | `{"status": "futile", "message": "Insufficient balance"}` |
| TC-2.7 | Balance Retrieval                      | ✅ PASS | `GET /user` returns correct balance |
| TC-2.8 | Transaction in History                 | ❌ FAIL | **HTTP 500** — backend error (see [Section 5](#5-bug-report-tc-28-transaction-history-500-error)) |
| TC-2.9 | Login Page Screenshot                  | ✅ PASS | Screenshot captured |
| TC-2.10 | Post-Login Screenshot                 | ✅ PASS | Screenshot captured |

### Screenshots Captured

| Screenshot | Description |
|------------|-------------|
| `screenshots/2.9_login_page.png` | Login form page rendered |
| `screenshots/2.10_after_login.png` | Dashboard after successful login |

---

## 4. Test 3: Security Testing — Replay Attack Prevention

**Objective:** Confirm that the timestamp + key derivation mechanism correctly blocks replayed or duplicate transaction packets.

**Approach:** Python `requests` library with `CryptoEngine` to craft and replay payloads.

### Test Cases & Results

| ID     | Test Name                              | Result | Notes |
|--------|----------------------------------------|:------:|-------|
| TC-3.0 | Test User Setup                        | ✅ PASS | User registered and logged in |
| TC-3.1 | Same Payload Twice → Second Rejected   | ✅ PASS | First: 200 OK. Second: 401 (T rotated or balance changed) |
| TC-3.2 | Stale/Old T Payload Rejected           | ✅ PASS | Payload encrypted with previous T → HTTP 401 (key derivation mismatch) |
| TC-3.3 | Corrupted Ciphertext Rejected          | ✅ PASS | Bit-flipped payload → HTTP 401 |
| TC-3.4 | Missing Fields → 400                   | ✅ PASS | Both missing payload and missing IV return 400 |
| TC-3.5 | No Auth Token → 401                    | ✅ PASS | Request without `Authorization` header returns 401 |
| TC-3.6 | UI Screenshots                         | ✅ PASS | Login and dashboard screenshots captured |

### Key Security Findings

1. **Replay Protection via T Rotation:** After each successful transfer, the user's timestamp `T` is updated in the database. Since the AES key is derived from `K2 + Bp + T`, any replayed payload using the old `T` cannot be decrypted.

2. **No Explicit Nonce Check:** The backend does not maintain a nonce/ID cache for duplicate detection. Replay resistance relies entirely on `T` rotation and balance depletion. For stronger protection, a nonce table or Redis cache should be added.

3. **Tamper Evidence:** Any modification to the ciphertext causes decryption to fail (PKCS7 padding error or HMAC mismatch), making the transaction untamperable in transit.

### Screenshots Captured

| Screenshot | Description |
|------------|-------------|
| `screenshots/3.5_login_page.png` | Login page for replay test user |
| `screenshots/3.6_dashboard.png` | Dashboard after login |

---

## 5. Bug Report: TC-2.8 Transaction History 500 Error

### Summary

| Field       | Value |
|-------------|-------|
| **Test**    | TC-2.8 — Transaction appears in history |
| **Endpoint** | `GET /transactions/<username>` |
| **Status**  | ❌ FAIL |
| **HTTP Code** | 500 Internal Server Error |
| **Response** | `{"status": "error", "message": "Internal server error"}` |

### Bug Visualization

The bug report HTML can be found at:
`Testing/Test2_Integration_Transaction/screenshots/bug_tc2.8.html`

Open this file in a browser to see a formatted view of the error.

### Reproduction Steps

1. Register a new user via `POST /register`
2. Login via `POST /login` to obtain a Bearer token
3. Perform a transfer via `POST /transfer` (encrypted payload)
4. Call `GET /transactions/<username>` with the token

### Root Cause Analysis

The backend's `get_transactions()` in `backend/app.py`:
1. Queries `supabase.table('transactions')` for sent and received transactions
2. For each transaction, it looks up the counterparty's account → profile to get the username
3. The 500 error occurs during one of these lookups — likely a Supabase FK constraint issue or schema cache miss

The `is_missing_schema_error()` check catches schema-related errors and returns a friendly message, but the actual error is not a schema error — it is an unhandled exception during the account/profile lookup.

### Impact

Users cannot view their transaction history. The frontend will show an error message or blank state when navigating to the history page.

---

## 6. Detailed Test Results Spreadsheet

The complete test case spreadsheet with all columns populated (Test ID, Module, Test Name, Description, Preconditions, Step #, Step Description, Input Data, Expected Result, Actual Result, Pass/Fail, Screenshot Ref, Notes/Bugs) is available at:

**`Testing/Test_Cases.xlsx`**

### Spreadsheet Summary

| Sheet Name          | Rows | Description |
|---------------------|:----:|-------------|
| Test 1 — Unit Crypto | 25   | 8 test cases with detailed steps |
| Test 2 — Integration | 16   | 11 test cases with API and UI tests |
| Test 3 — Replay Security | 10 | 7 test cases for replay prevention |

---

## Appendix: Project Structure

```
Testing/
├── Test_Cases.xlsx                              ← Detailed spreadsheet (ALL columns populated)
├── test_helpers.py                              ← Shared BackendClient + CryptoEngine helpers
├── create_spreadsheet.py                        ← Script to generate the spreadsheet
├── Test1_Unit_Crypto/
│   └── test_crypto.py                           ← pytest unit tests (8 tests)
├── Test2_Integration_Transaction/
│   ├── test_transaction_flow.py                 ← Integration + UI tests
│   └── screenshots/
│       ├── 2.9_login_page.png
│       ├── 2.10_after_login.png
│       ├── bug_tc2.8.html                       ← Bug visualization (open in browser)
│       └── bug_tc2.8_transactions_500.png       ← Bug screenshot
└── Test3_Security_Replay/
    ├── test_replay_attack.py                    ← Replay security tests
    └── screenshots/
        ├── 3.5_login_page.png
        └── 3.6_dashboard.png
```

---

*Report generated automatically from test execution results.*
