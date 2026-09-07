# TASK BREAKDOWN: E-Banking Security & Quality Enhancements

This document provides a detailed step-by-step breakdown of every task listed in the [ROADMAP.md](file:///E:/Apps/Sohan/E_PAY/e_banking/ROADMAP.md).

---

## 🔒 PHASE 1: Critical Security Fixes

### TSK-1.1: Fix IDOR Vulnerability on Profile, Transactions, and Notifications

#### Backend Steps
1.  Open [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py).
2.  Update the `@require_auth` decorator or modify endpoints `/user/<username>`, `/transactions/<username>`, and `/notifications/<username>` to extract the token from the `Authorization` header.
3.  Look up the authenticated username mapping in the `active_sessions` dictionary:
    ```python
    session_username = active_sessions.get(token)
    ```
4.  Compare `session_username` with the path variable `username`.
5.  If they do not match, return a `403 Forbidden` response:
    ```python
    return jsonify({"status": "error", "message": "Forbidden: Access denied to user data"}), 403
    ```

#### Frontend Steps
None.

#### Database Steps
None.

#### Testing Steps
1.  Log in as `tester1` to obtain session token `TokenA`.
2.  Log in as `tester2` to obtain session token `TokenB`.
3.  Send a GET request to `/transactions/tester2` using `TokenA` in the authorization header.
4.  Verify the response returns HTTP status code `403` with the correct error message.
5.  Send a GET request to `/transactions/tester1` using `TokenA` and verify it returns HTTP status `200` with the transaction list.

---

### TSK-1.2: Resolve Cryptographic Key Exposure in the Browser

#### Backend Steps
None.

#### Frontend Steps
1.  Open [frontend/src/utils/session.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/session.ts).
2.  Modify the `UserSession` interface to remove the fields `k1`, `k2`, and `bp` from the persistently stored data structure if they are saved in `localStorage`.
3.  Implement a transient, in-memory state store (such as a React Context or global variable) to hold `k1`, `k2`, and `bp` during active sessions:
    ```typescript
    // In-memory reference that resets on reload/tab close
    let sessionKeysInMemory: { k1: string; k2: string; bp: string } | null = null;
    ```
4.  Update `saveUserSession()` to write only public session parameters (such as `username`, `token`, `accountId`, and `balance`) to `localStorage`.
5.  Update `Login.tsx` to set the in-memory keys on successful login.
6.  Update `TransactionProcessing.tsx` to read the keys from the in-memory store.

#### Database Steps
None.

#### Testing Steps
1.  Log in to the application and complete a transaction.
2.  Open browser Developer Tools, inspect **Application -> Local Storage**, and verify that `k1`, `k2`, and `bp` are absent.
3.  Verify that transactions can still be completed successfully.
4.  Refresh the page and verify that the keys are cleared, requiring a re-login.

---

## 🛠️ PHASE 2: Backend Improvements

### TSK-2.1: Transactional Atomic Checks for Timestamp Synchronization

#### Backend Steps
1.  Open [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py).
2.  Locate the transaction execution block within `process_transfer()`.
3.  Wrap database updates for `update_profile_timestamp`, `update_daily_spend`, and the sender/receiver balance updates in a transactional block.
4.  If any update returns `False` or raises an exception:
    *   Roll back previous balance adjustments.
    *   Record a failure log in the transaction table.
    *   Return a `500 Internal Server Error` response.
    ```python
    if not update_profile_timestamp(...) or not update_daily_spend(...):
        # Trigger rollback logic
        return jsonify({"status": "error", "message": "Failed to commit security parameters"}), 500
    ```

#### Frontend Steps
None.

#### Database Steps
None.

#### Testing Steps
1.  Inject a failure behavior into the `update_profile_timestamp` function to return `False`.
2.  Attempt to send money.
3.  Verify the API returns a 500 error and no funds are deducted from the sender's balance.

---

### TSK-2.2: Fix SPA Catch-all Routing for Malicious Payloads

#### Backend Steps
1.  Open [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py).
2.  Locate the catch-all route `@app.route('/<path:path>')`.
3.  Implement validation on the incoming `path` string to check for directory traversal (`../`) or script tag patterns (`<script>`).
4.  If a malicious pattern is detected, return a `400 Bad Request` or `404 Not Found` response:
    ```python
    if "../" in path or "<script>" in path.lower():
        return jsonify({"status": "error", "message": "Resource not found"}), 404
    ```

#### Frontend Steps
None.

#### Database Steps
None.

#### Testing Steps
1.  Send a GET request to `/check-receiver/../../../etc/passwd`.
2.  Verify the response returns HTTP status code `404` instead of the SPA landing page.
3.  Send a GET request to `/check-receiver/<script>alert(1)</script>` and verify it returns a `404` response.

---

## 💻 PHASE 3: Frontend Improvements

### TSK-3.1: Fix TransactionCard Incoming Transaction Bug

#### Backend Steps
None.

#### Frontend Steps
1.  Open [frontend/src/app/components/TransactionCard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/TransactionCard.tsx).
2.  Add a `type` parameter (e.g. `'sent'` vs `'received'`) and `senderUsername` to the component props interface:
    ```typescript
    interface TransactionCardProps {
      type?: 'sent' | 'received';
      senderUsername?: string;
      // ... existing props
    }
    ```
3.  Update the rendering logic to format deposit transactions with a green `+৳` indicator showing the sender's username, and sent transactions with a black `-৳` showing the recipient's username.
4.  Open [frontend/src/app/screens/TransactionHistory.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionHistory.tsx) and [Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx), and pass the `type` and `senderUsername` parameters to the card component.

#### Database Steps
None.

#### Testing Steps
1.  Log in as a user who has both sent and received transactions.
2.  Verify that received payments display with green text, a `+` symbol, and the sender's username.
3.  Verify that sent payments continue to display correctly.

---

### TSK-3.2: Use Server-Returned Balance Instead of Local Calculations

#### Backend Steps
None.

#### Frontend Steps
1.  Open [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx).
2.  Locate `updateUserBalance(session.balance - amount)`.
3.  Modify this to update the session balance using the balance returned from the API:
    ```typescript
    if (response.new_balance !== undefined) {
      updateUserBalance(response.new_balance);
    }
    ```

#### Database Steps
None.

#### Testing Steps
1.  Complete a transaction.
2.  Verify the dashboard balance matches the database state.

---

### TSK-3.3: Handle Missing Timestamp Safely in Success Navigation

#### Backend Steps
None.

#### Frontend Steps
1.  Open [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx).
2.  Locate the success check:
    ```typescript
    if (response.status === 'success' && response.new_t)
    ```
3.  Modify this check to validate the transaction status first, then update the timestamp if `new_t` is present:
    ```typescript
    if (response.status === 'success') {
      if (response.new_t) {
        updateUserTimestamp(response.new_t);
      }
      // Continue navigation to success page
    }
    ```

#### Database Steps
None.

#### Testing Steps
1.  Intercept the transfer network response and remove the `new_t` parameter from the payload.
2.  Verify the application still navigates to the success page.

---

## 🗄️ PHASE 4: Database Improvements

### TSK-4.1: Enforce Row-Level Security (RLS) Policies on Supabase

#### Backend Steps
None.

#### Frontend Steps
None.

#### Database Steps
1.  Open [database/SUPABASE_NEW_DATABASE_SETUP.sql](file:///E:/Apps/Sohan/E_PAY/e_banking/database/SUPABASE_NEW_DATABASE_SETUP.sql).
2.  Add Row-Level Security (RLS) policies to restrict direct queries on profiles and transactions using the anon key:
    ```sql
    ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
    CREATE POLICY profiles_individual_select ON public.profiles
      FOR SELECT TO authenticated USING (id = auth.uid());
    ```

#### Testing Steps
1.  Log in as `tester1`.
2.  Send a query to the Supabase REST endpoint to read a profile belonging to another user.
3.  Verify that the server returns an empty list or permission denied.

---

## 🎨 PHASE 5: UX/UI Improvements

### TSK-5.1: Dynamic Header Title Mapping on Quick Actions

#### Backend Steps
None.

#### Frontend Steps
1.  Open [frontend/src/app/screens/Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx).
2.  Update the quick actions list to pass the title in the route state:
    ```typescript
    navigate('/send-money', { state: { label: 'Utility Payment' } });
    ```
3.  Open [frontend/src/app/screens/SendMoney.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/SendMoney.tsx).
4.  Modify the header element to render the title dynamically:
    ```typescript
    const location = useLocation();
    const pageTitle = location.state?.label || 'Send Money';
    ```

#### Database Steps
None.

#### Testing Steps
1.  On the dashboard, click on **Utilities**.
2.  Verify that the header on the payment screen displays "Utility Payment".

---

### TSK-5.2: Eliminate Race Conditions in Transaction Loading Animations

#### Backend Steps
None.

#### Frontend Steps
1.  Open [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx).
2.  Remove artificial timeouts (e.g. `setTimeout`) that delay navigation.
3.  Navigate immediately to the results page once the backend API response is received:
    ```typescript
    const response = await processTransfer(session.username, encryptedPayload);
    // Navigate immediately based on response status
    ```

#### Database Steps
None.

#### Testing Steps
1.  Trigger a transaction and verify that the application navigates to the result screen immediately after receiving the response.

---

## 🚀 PHASE 6: Production Readiness

### TSK-6.1: Clean Up Unused UI Components

#### Backend Steps
None.

#### Frontend Steps
1.  Inspect [frontend/src/app/components/ui/](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/ui/) and identify unused shadcn components.
2.  Delete the unused files from the project.

#### Database Steps
None.

#### Testing Steps
1.  Run the Vite build command and verify it completes successfully without missing dependency errors:
    ```powershell
    npm run build
    ```

---

### TSK-6.2: Restrict CORS Policies and Rotate Environment Secrets

#### Backend Steps
1.  Open [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py).
2.  Update `CORS(app)` to whitelist only authorized origins.
3.  In the Supabase console, rotate the public anon key and the service role key.
4.  Update the keys in [backend/.env.backend](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/.env.backend) with the new values.
5.  Remove any plaintext keys from version control.

#### Frontend Steps
1.  Open [frontend/src/utils/supabase.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/supabase.ts) and update the anon key if needed.

#### Database Steps
None.

#### Testing Steps
1.  Send a request to the API from an unauthorized origin and verify it is blocked.
2.  Verify that the application functions normally with the rotated keys.
