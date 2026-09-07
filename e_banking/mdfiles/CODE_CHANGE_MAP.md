# CODE CHANGE MAP: E-Banking Security & Quality Enhancements

This document maps the planned changes to the codebase, detailing the exact files, code sections, risks, and side effects associated with each task.

---

## 🛠️ Roadmap Task Mapping

### TSK-1.1: Fix IDOR Vulnerability

#### Affected Elements
*   **Frontend Files:** None.
*   **Backend Files:** [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)
*   **Database Tables:** `profiles`, `transactions`, `notifications`
*   **API Endpoints:** `/user/<username>`, `/transactions/<username>`, `/notifications/<username>`
*   **Components:** None.

#### File Modifications

##### File: [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)
*   **Why:** Verify that the username associated with the authenticated session token matches the username parameter in the URL.
*   **Code Section:** Inside routes `get_user()`, `get_transactions()`, and `get_notifications()`.
*   **Risk Level:** Medium
*   **Possible Side Effects:** Legitimate requests could fail with a `403 Forbidden` error if the frontend session is out of sync or passes mismatched parameter formats.

---

### TSK-1.2: Resolve Cryptographic Key Exposure in the Browser

#### Affected Elements
*   **Frontend Files:**
    *   [frontend/src/utils/session.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/session.ts)
    *   [frontend/src/app/screens/Login.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Login.tsx)
    *   [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)
*   **Backend Files:** None.
*   **Database Tables:** None.
*   **API Endpoints:** None.
*   **Components:** None.

#### File Modifications

##### File: [frontend/src/utils/session.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/session.ts)
*   **Why:** Update the session manager to store only non-sensitive data (such as username and token) in `localStorage` and keep keys ($K1$, $K2$, $BP$) in transient memory.
*   **Code Section:** `saveUserSession()`, `getUserSession()`, and `clearUserSession()`.
*   **Risk Level:** High
*   **Possible Side Effects:** Reloading the browser tab will clear the keys from memory, requiring the user to log in again.

##### File: [frontend/src/app/screens/Login.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Login.tsx)
*   **Why:** Pass keys returned from the login API response to the transient in-memory store instead of `localStorage`.
*   **Code Section:** `handleSubmit()`
*   **Risk Level:** Medium
*   **Possible Side Effects:** Login succeeds but the frontend fails to complete transactions if the key mapping fails.

##### File: [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)
*   **Why:** Update the transaction flow to load $K1$, $K2$, and $BP$ from transient memory instead of `localStorage`.
*   **Code Section:** `startProcessing()`
*   **Risk Level:** High
*   **Possible Side Effects:** Transactions will fail if the transient keys are unavailable.

---

### TSK-2.1: Transactional Atomic Checks for Timestamp Synchronization

#### Affected Elements
*   **Frontend Files:** None.
*   **Backend Files:** [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)
*   **Database Tables:** `profiles`, `accounts`, `transactions`
*   **API Endpoints:** `/transfer`
*   **Components:** None.

#### File Modifications

##### File: [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)
*   **Why:** Wrap database updates in a transaction block. Roll back balance changes if updating the security timestamp $T$ fails.
*   **Code Section:** Inside `process_transfer()`.
*   **Risk Level:** High
*   **Possible Side Effects:** A database timeout during the timestamp update could trigger a rollback, causing transactions to be rejected even if the balance was updated.

---

### TSK-2.2: Fix SPA Catch-all Routing for Malicious Payloads

#### Affected Elements
*   **Frontend Files:** None.
*   **Backend Files:** [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)
*   **Database Tables:** None.
*   **API Endpoints:** `/*` (Catch-all routing)
*   **Components:** None.

#### File Modifications

##### File: [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)
*   **Why:** Block routing requests containing path traversal (`../`) or script tag injection patterns.
*   **Code Section:** Inside `serve_static()` and `not_found()` handlers.
*   **Risk Level:** Medium
*   **Possible Side Effects:** Strict path checking could block legitimate static resource URLs containing folders with matching names.

---

### TSK-3.1: Fix TransactionCard Incoming Transaction Bug

#### Affected Elements
*   **Frontend Files:**
    *   [frontend/src/app/components/TransactionCard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/TransactionCard.tsx)
    *   [frontend/src/app/screens/TransactionHistory.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionHistory.tsx)
    *   [frontend/src/app/screens/Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)
*   **Backend Files:** None.
*   **Database Tables:** None.
*   **API Endpoints:** None.
*   **Components:** `TransactionCard`

#### File Modifications

##### File: [frontend/src/app/components/TransactionCard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/TransactionCard.tsx)
*   **Why:** Update the component to accept a `type` parameter (e.g. `'sent'` vs `'received'`) and `senderUsername` to format incoming transactions correctly.
*   **Code Section:** Props interface and component rendering.
*   **Risk Level:** Low
*   **Possible Side Effects:** Layout formatting issues if the username lengths differ significantly.

##### File: [frontend/src/app/screens/TransactionHistory.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionHistory.tsx) & [Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)
*   **Why:** Pass the transaction type and sender details to the updated card component.
*   **Code Section:** Transaction list map render loops.
*   **Risk Level:** Low
*   **Possible Side Effects:** None.

---

### TSK-3.2: Use Server-Returned Balance Instead of Local Calculations

#### Affected Elements
*   **Frontend Files:** [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)
*   **Backend Files:** None.
*   **Database Tables:** None.
*   **API Endpoints:** None.
*   **Components:** None.

#### File Modifications

##### File: [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)
*   **Why:** Set the user's balance using the `new_balance` value returned from the API response instead of calculating it locally.
*   **Code Section:** `startProcessing()` API success block handler.
*   **Risk Level:** Low
*   **Possible Side Effects:** Mismatches could occur if the API returns an unexpected balance value.

---

### TSK-3.3: Handle Missing Timestamp Safely in Success Navigation

#### Affected Elements
*   **Frontend Files:** [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)
*   **Backend Files:** None.
*   **Database Tables:** None.
*   **API Endpoints:** None.
*   **Components:** None.

#### File Modifications

##### File: [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)
*   **Why:** Allow navigation to the success screen even if the new timestamp `new_t` is missing from the response.
*   **Code Section:** Success condition check block.
*   **Risk Level:** Low
*   **Possible Side Effects:** Future transactions could fail due to a timestamp mismatch if `new_t` was actually required but omitted.

---

### TSK-4.1: Enforce Row-Level Security (RLS) Policies on Supabase

#### Affected Elements
*   **Frontend Files:** None.
*   **Backend Files:** None.
*   **Database Tables:** `profiles`, `accounts`, `transactions`, `notifications`
*   **API Endpoints:** None.
*   **Components:** None.

#### File Modifications

##### File: [database/SUPABASE_NEW_DATABASE_SETUP.sql](file:///E:/Apps/Sohan/E_PAY/e_banking/database/SUPABASE_NEW_DATABASE_SETUP.sql)
*   **Why:** Add SQL policies to restrict user access to data matching their authenticated ID.
*   **Code Section:** Policy definitions.
*   **Risk Level:** Medium
*   **Possible Side Effects:** Backend queries could fail if the service role key configuration is incorrect and fails to bypass RLS policies.

---

### TSK-5.1: Dynamic Header Title Mapping on Quick Actions

#### Affected Elements
*   **Frontend Files:**
    *   [frontend/src/app/screens/Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)
    *   [frontend/src/app/screens/SendMoney.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/SendMoney.tsx)
*   **Backend Files:** None.
*   **Database Tables:** None.
*   **API Endpoints:** None.
*   **Components:** None.

#### File Modifications

##### File: [frontend/src/app/screens/Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)
*   **Why:** Pass the transaction category title (e.g. "Utility Payment") in the route state when navigating.
*   **Code Section:** Quick action navigation triggers.
*   **Risk Level:** Low
*   **Possible Side Effects:** None.

##### File: [frontend/src/app/screens/SendMoney.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/SendMoney.tsx)
*   **Why:** Dynamically render the page header using the title passed in the route state.
*   **Code Section:** Header title rendering.
*   **Risk Level:** Low
*   **Possible Side Effects:** None.

---

### TSK-5.2: Eliminate Race Conditions in Transaction Loading Animations

#### Affected Elements
*   **Frontend Files:** [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)
*   **Backend Files:** None.
*   **Database Tables:** None.
*   **API Endpoints:** None.
*   **Components:** `ProcessingStep`

#### File Modifications

##### File: [frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)
*   **Why:** Remove artificial timeouts and navigate to the result screen immediately after the API call completes.
*   **Code Section:** Cryptographic processing loops.
*   **Risk Level:** Low
*   **Possible Side Effects:** The transition animation might look rushed if the API response is returned very quickly.

---

### TSK-6.1: Clean Up Unused UI Components

#### Affected Elements
*   **Frontend Files:** Files in [frontend/src/app/components/ui/](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/ui/)
*   **Backend Files:** None.
*   **Database Tables:** None.
*   **API Endpoints:** None.
*   **Components:** Various unused UI elements.

#### File Modifications

##### Folder: [frontend/src/app/components/ui/](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/ui/)
*   **Why:** Delete unused shadcn components to reduce the project bundle size.
*   **Code Section:** Entire components.
*   **Risk Level:** Low
*   **Possible Side Effects:** Build errors if a component identified as unused was actually imported somewhere in the application.

---

### TSK-6.2: Restrict CORS Policies and Rotate Environment Secrets

#### Affected Elements
*   **Frontend Files:** [frontend/src/utils/supabase.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/supabase.ts)
*   **Backend Files:**
    *   [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)
    *   [backend/.env.backend](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/.env.backend)
*   **Database Tables:** None.
*   **API Endpoints:** All backend endpoints.
*   **Components:** None.

#### File Modifications

##### File: [backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)
*   **Why:** Restrict CORS configuration to allow requests only from authorized origins instead of wildcard matching.
*   **Code Section:** CORS initialization.
*   **Risk Level:** High
*   **Possible Side Effects:** Access to the backend will be blocked if the frontend origin is not correctly configured.

##### File: [backend/.env.backend](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/.env.backend) & [frontend/src/utils/supabase.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/supabase.ts)
*   **Why:** Rotate the committed Supabase keys and update references with the new secure keys.
*   **Code Section:** Environment variable declarations.
*   **Risk Level:** High
*   **Possible Side Effects:** Frontend or backend database connections will fail if the keys are mismatched.

---

## 📊 Dependency Impact Matrix

| File Path | Dependent Features | Dependent APIs | Dependent Components | Security Implications |
| :--- | :--- | :--- | :--- | :--- |
| **[backend/app.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/app.py)** | Session Authentication, Transfers, Profile Management | All endpoints | None | Manages API endpoints, session validation, and transaction authentication. |
| **[backend/crypto.py](file:///E:/Apps/Sohan/E_PAY/e_banking/backend/crypto.py)** | Secure Transfers, Key Stretching, Decryption | `/transfer`, `/register` | None | Manages server-side decryption and signature verification. |
| **[database/SUPABASE_NEW_DATABASE_SETUP.sql](file:///E:/Apps/Sohan/E_PAY/e_banking/database/SUPABASE_NEW_DATABASE_SETUP.sql)** | Account Ledgers, Profile Storage | All endpoints | None | Manages the database schema and RLS security policies. |
| **[frontend/src/utils/crypto.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/crypto.ts)** | Client-side Encryption, Key Derivation | `/transfer` | `ProcessingStep` | Manages client-side encryption and HMAC signature generation. |
| **[frontend/src/utils/session.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/session.ts)** | Session State, Key Management | All authenticated client calls | `DailyLimitIndicator` | Manages session state and cryptographic keys in the browser. |
| **[frontend/src/app/screens/TransactionProcessing.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionProcessing.tsx)** | Secure Transfers | `/transfer` | `ProcessingStep` | Executes the frontend cryptographic workflow. |

---

## 🏁 Implementation Order

To ensure a safe deployment and minimize regressions, implement the changes in the following order:

```
[Phase 1: IDOR & Key Protection] 
              │
              ▼
[Phase 2: Database RLS & API CORS Restriction]
              │
              ▼
[Phase 3: Transaction Checks & Rollback Logic]
              │
              ▼
[Phase 4: Client-side UI Mappings & Card Fixes]
              │
              ▼
[Phase 5: Secrets Rotation & Clean up]
```

### Safest Coding Sequence

#### 1. Implement IDOR Fix (`TSK-1.1`)
*   **Reason:** Simple backend change that secures access to user data with minimal risk of breaking other features.

#### 2. Implement Transient Key Storage (`TSK-1.2`)
*   **Reason:** Removes sensitive keys from `localStorage`. Do this early to ensure the new state management is stable before making changes to database security policies.

#### 3. Enforce Supabase RLS and Restrict CORS (`TSK-4.1`, `TSK-6.2`)
*   **Reason:** Restricts access to the database and API endpoints. Doing this after fixing IDOR and local key handling ensures no legitimate features are blocked.

#### 4. Add Transaction Rollback Logic (`TSK-2.1`)
*   **Reason:** Updates backend transaction handling. Implement this once API endpoints and database access rules are stabilized.

#### 5. Implement Frontend UI fixes (`TSK-3.1`, `TSK-3.2`, `TSK-3.3`, `TSK-5.1`, `TSK-5.2`)
*   **Reason:** Fixes bugs in the frontend (such as balance updates, transaction cards, and loading animations) that depend on updated backend responses.

#### 6. Clean Up Unused Components (`TSK-6.1`)
*   **Reason:** The final cleanup step. Safe to execute once all functional updates are completed and verified.
