# 4.2 Testing and Evaluation

## 4.2.1 Overview

This document provides a complete reference for the tests performed so far on the E-Banking / E-Payment system.

The system was tested using an offline sandbox test runner. The test runner uses Flask's in-process test client and enables fake database mode using:

```text
SANDBOX_FAKE_DB=1
```

Therefore, the tests did not use real Supabase users, real banking records, real balances, or any external production server.

Most protected APIs require an authentication token. Authentication is handled using a bearer session token returned after successful login.

Protected request format:

```http
Authorization: Bearer {token}
```

Latest test execution:

| Field | Value |
| --- | --- |
| Test mode | Offline Flask test client |
| Database mode | Fake in-memory sandbox database |
| Target | Local Flask backend API |
| Report generated | 2026-06-10 16:06:14, Asia/Dhaka |
| Report file | `reports/sandbox-pentest-latest.md` |

Overall result:

| Status | Count |
| --- | ---: |
| PASS | 17 |
| FAIL | 9 |
| WARN | 2 |

Status meaning:

| Status | Meaning |
| --- | --- |
| PASS | Expected behavior was found |
| FAIL | Required behavior was missing or a vulnerability was found |
| WARN | Behavior needs further review or manual confirmation |

## 4.2.2 Test Environment

The following fake users were used during testing:

| Username | Password | Starting Balance |
| --- | --- | ---: |
| `alice` | `AlicePass123!` | 5000.00 |
| `bob` | `BobPass123!` | 1500.00 |

The main API port for normal local execution is:

```text
5001
```

However, the automated test runner does not call the server through a network port. It imports the Flask application directly and sends requests through Flask's test client.

Command used:

```powershell
python tests/security/sandbox_pentest_runner.py
```

## 4.2.3 User Authentication APIs

### Login API

Endpoint:

```text
POST /login
```

Description:

Authenticates a user and returns a bearer session token.

Request:

```json
{
  "username": "alice",
  "password": "AlicePass123!"
}
```

Successful response:

```json
{
  "status": "success",
  "token": "{session_token}",
  "user": {
    "id": "profile-alice",
    "username": "alice",
    "balance": 5000.0
  }
}
```

Tests performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| FUNC-002 | Known test user can log in | User `alice` logs in and receives token | Status 200; token returned | PASS |
| API-002 | Login validates required fields | Missing password returns 400 | Status 400 | PASS |
| API-003 | Login should not reveal account existence | Unknown user and wrong password should return the same generic error | Unknown user returned 404 | FAIL |

Evaluation:

The login API works for valid users and validates missing fields. However, the unknown-user response can reveal whether an account exists. The response should be changed to a generic authentication failure.

## 4.2.4 Functional API Testing

### Health Check API

Endpoint:

```text
GET /health
```

Description:

Checks whether the backend API is running.

Expected response:

```json
{
  "status": "ok",
  "message": "E-Banking API is running"
}
```

Test performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| FUNC-001 | Health endpoint responds | `GET /health` returns 200 | Status 200 | PASS |

### User Profile API

Endpoint:

```text
GET /user/{username}
```

Authentication:

Required.

Description:

Returns authenticated user profile and account information.

Request header:

```http
Authorization: Bearer {token}
```

Test performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| FUNC-003 | Authenticated profile lookup works | Authenticated `/user/alice` returns profile data | Status 200 | PASS |
| API-001 | Profile endpoint requires authentication | Request without token is rejected | Status 401 | PASS |
| API-004 | User cannot read another user's profile | Alice's token should not authorize `/user/bob` | Status 200 for `/user/bob` | FAIL |

Evaluation:

The endpoint correctly rejects unauthenticated requests. However, an authenticated user can retrieve another user's profile. The backend should bind the token identity to the requested username.

### Receiver Validation API

Endpoint:

```text
GET /check-receiver/{username}
```

Authentication:

Required.

Description:

Checks whether a receiver username exists before money transfer.

Test performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| FUNC-004 | Receiver validation works | Known receiver `bob` is accepted | Status 200 | PASS |

Evaluation:

The receiver validation endpoint works correctly for a known receiver in the sandbox database.

## 4.2.5 Transfer API Testing

### Money Transfer API

Endpoint:

```text
POST /transfer
```

Authentication:

Required.

Description:

Processes encrypted money transfer requests using password-derived cryptographic values, biometric placeholder value, timestamp, and HMAC verification.

Request:

```json
{
  "username": "alice",
  "payload": "{encrypted_payload}",
  "iv": "{initialization_vector}"
}
```

Successful response:

```json
{
  "status": "success",
  "message": "Transfer of 25.0 to bob successful",
  "new_t": "{new_timestamp}",
  "new_balance": 4975.0
}
```

Tests performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| FUNC-005 | Valid encrypted transfer completes | Valid Alice-to-Bob transfer succeeds | Status 200; response `success` | PASS |
| TXN-001 | Transfer over balance is rejected | Amount greater than balance is rejected | Status 400; response `futile` | PASS |
| TXN-002 | Negative transfer amount is rejected | Negative amount returns 400 | Status 200; response `success` | FAIL |
| TXN-003 | Zero transfer amount is rejected | Zero amount returns 400 | Status 200; response `success` | FAIL |
| TXN-004 | Tampered transaction HMAC is rejected | Bad HMAC returns 403 | Status 403 | PASS |
| TXN-005 | Duplicate encrypted transfer payload cannot be replayed | First request succeeds; replay fails | First status 200; replay status 401 | PASS |
| TXN-006 | Transfer sender is bound to authenticated session | Alice's token must not authorize a request claiming sender `bob` | Status 200; response `success` | FAIL |

Evaluation:

The transfer API successfully handles valid encrypted transfers, rejects over-balance transfers, rejects tampered HMAC values, and prevents duplicate encrypted payload replay. However, it currently accepts zero and negative amounts. It also allows a token from one user to submit a transfer for another username. Amount validation and sender-session binding should be added.

## 4.2.6 SQL Injection Testing

Target API:

```text
POST /login
```

Description:

SQL injection payloads were tested against the login endpoint to verify that injection strings do not authenticate a user.

Payload examples:

```text
' OR '1'='1
admin'--
' UNION SELECT NULL--
```

Tests performed:

| Test ID | Payload Type | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| SQLI-001 | Boolean-based login injection | Payload must not authenticate | Status 404 | PASS |
| SQLI-002 | Comment-based login injection | Payload must not authenticate | Status 404 | PASS |
| SQLI-003 | Union-based login injection | Payload must not authenticate | Status 404 | PASS |

Evaluation:

The tested SQL injection payloads did not authenticate. The system uses Supabase SDK filters for database lookup, which reduces direct SQL injection risk.

## 4.2.7 XSS Testing

Target API:

```text
POST /register
```

Description:

A script-like username was submitted to check whether dangerous characters are rejected or reflected.

Request example:

```json
{
  "username": "<script>alert(1)</script>",
  "password": "TestPass123!",
  "nid": "NID-XSS",
  "activationCode": "ACT-XSS"
}
```

Test performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| XSS-001 | Dangerous characters in username | API should reject or safely canonicalize script-like username | Register status 201; value reflected in JSON | WARN |

Evaluation:

The API accepted a script-like username. React normally escapes rendered text, but the backend should still validate usernames with an allow-list to reduce stored XSS risk.

## 4.2.8 CSRF Testing

Target API:

```text
POST /transfer
```

Description:

The transfer endpoint was tested for protection against unauthenticated state-changing requests and unexpected origin headers.

Tests performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| CSRF-001 | Transfer rejects unauthenticated requests | Request without token returns 401 | Status 401 | PASS |
| CSRF-002 | Unexpected origin is rejected | Cross-site origin should be rejected for transfer | Status 200 | WARN |

Evaluation:

The transfer endpoint correctly requires authentication. However, unexpected origin headers are not rejected. Since bearer tokens are used, CSRF risk is lower than cookie-based auth, but origin checking should be considered for sensitive state-changing routes.

## 4.2.9 Brute Force Login Testing

Target API:

```text
POST /login
```

Description:

Repeated wrong passwords were submitted to check whether the backend applies lockout or throttling.

Test performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| BRUTE-001 | Repeated failed login attempts | Login should be locked or rate-limited after repeated failures | Twelve wrong attempts returned 401; correct login after failures returned 200 | FAIL |

Evaluation:

The backend does not currently lock or throttle repeated login failures. Server-side attempt counters, temporary lockout, or rate limiting should be added. Nginx rate limiting can be used as an additional outer layer, but backend-level protection is also needed.

## 4.2.10 Session Testing

Target APIs:

```text
POST /login
GET /user/{username}
```

Description:

Session token behavior was tested using invalid tokens, copied tokens, and cookie checks.

Tests performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| SESS-001 | Invalid session token is rejected | Unknown token returns 401 | Status 401 | PASS |
| SESS-002 | Bearer token cannot be replayed from another client | Copied token should be constrained | Copied token returned status 200 | FAIL |
| SESS-003 | Session cookies are protected | No insecure session cookie should be issued | Login uses bearer token; no `Set-Cookie` used | PASS |

Evaluation:

Invalid tokens are rejected and the API does not issue insecure cookies. However, bearer tokens can be replayed from another client. Token expiry, logout invalidation, rotation, and device/session metadata should be added.

## 4.2.11 Password Storage Testing

Target areas:

```text
POST /login
backend password handling
```

Description:

Password storage and login response data were tested to ensure raw passwords and password-derived secrets are not exposed.

Tests performed:

| Test ID | Test Case | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| PASS-001 | Database password field stores a hash | Stored password is not raw plaintext | Hash exists; raw password does not match stored value | PASS |
| PASS-002 | Login response does not expose password-derived secrets | K1/K2 secrets should not be returned | Response exposed `k1` and `k2` | FAIL |
| PASS-003 | Codebase has no plaintext password fallback | Backend should not compare stored field directly to submitted password | Plaintext-style fallback found | FAIL |

Evaluation:

The password is stored as a hash in the fake database, which is correct. However, login responses expose cryptographic secrets, and the codebase contains a fallback comparison path. These issues should be fixed before production use.

## 4.2.12 API Authentication Summary

The following endpoints were tested for authentication behavior:

| Endpoint | Authentication Required | Test Result |
| --- | --- | --- |
| `GET /health` | No | Works without token |
| `POST /login` | No | Valid login works |
| `GET /user/{username}` | Yes | Missing token rejected, but cross-user access allowed |
| `GET /check-receiver/{username}` | Yes | Valid token accepted |
| `POST /transfer` | Yes | Missing token rejected, but sender mismatch allowed |

## 4.2.13 Evaluation Summary

The testing phase showed that the core system flow is functional. Login, profile retrieval, receiver checking, and valid encrypted transfers work in the sandbox environment. Several important security controls are also present, such as authentication checks on protected endpoints, rejection of invalid tokens, SQL injection resistance in tested login payloads, HMAC tamper detection, over-balance rejection, and duplicate encrypted payload replay failure.

The following issues were found and should be improved:

| Area | Issue | Priority |
| --- | --- | --- |
| Authentication | Unknown users return a different response from wrong passwords | Medium |
| Authorization | Users can read another user's profile | High |
| Login protection | No backend lockout after repeated failed attempts | High |
| Session security | Bearer token can be replayed from another client | High |
| Secret exposure | Login response exposes `k1` and `k2` | Critical |
| Password handling | Plaintext-style password fallback exists | High |
| Transaction validation | Negative transfer amount is accepted | Critical |
| Transaction validation | Zero transfer amount is accepted | High |
| Transaction authorization | Authenticated user can submit transfer as another sender | Critical |
| Input validation | Script-like username is accepted | Medium |
| Origin validation | Unexpected transfer origin is accepted | Medium |

Final result:

```text
Total tests: 28
PASS: 17
FAIL: 9
WARN: 2
```

