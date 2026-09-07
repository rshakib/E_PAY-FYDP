# IMPLEMENTATION PLAN: IDOR VULNERABILITY REPAIR (TSK-1.1)

This document details the plan to fix the Insecure Direct Object Reference (IDOR) vulnerability identified in the profile, history, and notifications endpoints.

---

## 1. Vulnerable Endpoints
*   `GET /user/<username>`
*   `GET /transactions/<username>`
*   `GET /notifications/<username>`

---

## 2. Root Cause
The custom authentication decorator `@require_auth` verifies that the `Authorization` header contains a valid token registered in the backend's in-memory `active_sessions` session dictionary. 

However, the endpoints load data using the `<username>` path parameter without verifying that the username associated with the token matches the requested `<username>`. As a result, any authenticated user can query data belonging to other users.

---

## 3. Authorization Flows

### 3.1 Current Authorization Flow
```
Client (tester1) ──────► GET /transactions/tester2 (Auth: Bearer TokenA)
                                  │
                                  ▼
                    @require_auth intercepts
                                  │
                  Is TokenA in active_sessions? (Yes)
                                  │
                                  ▼
                      Calls get_transactions()
                                  │
            Fetches tester2 transactions from Supabase
                                  │
                                  ▼
Client (tester1) ◄─────── 200 OK (tester2 Data)
```

### 3.2 Proposed Authorization Flow
```
Client (tester1) ──────► GET /transactions/tester2 (Auth: Bearer TokenA)
                                  │
                                  ▼
                    @require_auth intercepts
                                  │
                  Is TokenA in active_sessions? (Yes)
                                  │
                                  ▼
                      Calls get_transactions()
                                  │
          Does session_username == requested_username? (No)
                                  │
                                  ▼
Client (tester1) ◄────── 403 Forbidden (Error Payload)
```

---

## 4. Implementation Details

### 4.1 Files Requiring Modification
*   [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)

### 4.2 Functions Requiring Modification

#### `get_user(username)`
*   **Location:** [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py#L389)
*   **Changes:** Extract the Bearer token from the headers, retrieve the associated username from the `active_sessions` store, and reject requests where the values do not match.

#### `get_transactions(username)`
*   **Location:** [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py#L419)
*   **Changes:** Add the same token validation check before querying historical transaction records.

#### `get_notifications(username)`
*   **Location:** [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py#L496)
*   **Changes:** Add the token validation check before returning notifications.

---

## 5. Impact Analysis

### 5.1 Database Impact
*   None. No changes are required for Supabase tables, indexes, or stored procedures.

### 5.2 API Contract Impact
*   Authorized requests (where the token matches the requested username) return a `200 OK` response with the payload.
*   Unauthorized requests (where the token does not match) return a `403 Forbidden` response:
    ```json
    {
      "status": "error",
      "message": "Forbidden: Access denied to user data"
    }
    ```

### 5.3 Frontend Impact
*   None. The frontend client only requests data matching the logged-in user's username.

---

## 6. Regression Risks & Mitigations
*   **Risk:** Mismatched string casing (e.g. `UserA` vs `usera`) could cause the validation check to fail, returning unexpected `403` errors.
    *   *Mitigation:* Convert both values to lowercase and strip whitespace before comparing them.
*   **Risk:** Empty or malformed headers could raise unhandled exceptions in the route handlers.
    *   *Mitigation:* Use defensive programming techniques when parsing headers, checking for empty strings or invalid bearer formats before performing comparisons.

---

## 7. Testing Requirements

### 7.1 Test Case 1: Mismatched Token Access (IDOR Attempt)
*   **Setup:** Log in as `tester1` and retrieve their token.
*   **Action:** Send a GET request to `/transactions/tester2` passing the `tester1` token.
*   **Expectation:** The server rejects the request and returns a `403 Forbidden` response.

### 7.2 Test Case 2: Matching Token Access (Authorized Request)
*   **Setup:** Log in as `tester1` and retrieve their token.
*   **Action:** Send a GET request to `/transactions/tester1` passing the `tester1` token.
*   **Expectation:** The server accepts the request and returns a `200 OK` response with the user's transactions.

### 7.3 Test Case 3: Invalid Token Request
*   **Setup:** None.
*   **Action:** Send a GET request to `/transactions/tester1` passing an invalid token (`Bearer invalid_token`).
*   **Expectation:** The server rejects the request and returns a `401 Unauthorized` response.

---

## 8. Rollback Plan
1.  Before making changes, create a backup of the target file:
    ```powershell
    cp backend/app.py backend/app.py.bak
    ```
2.  If any regressions are identified during testing, restore the backup:
    ```powershell
    cp backend/app.py.bak backend/app.py
    ```
