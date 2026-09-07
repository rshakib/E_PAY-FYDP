# CURRENT DASHBOARD ANALYSIS

This document provides a detailed analysis of the current dashboard implementation in the E-Banking application before any redesign or modification is performed.

---

## 1. Location of the Dashboard Page
*   **File Path:** [frontend/src/app/screens/Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)

---

## 2. Current Dashboard Layout & Structure

### 2.1 Overall Layout Structure
*   The dashboard uses a mobile-first responsive layout centered in a container (`max-w-2xl mx-auto`).
*   It consists of two main visual blocks:
    1.  **Top Header Panel:** A green gradient container (`bg-gradient-to-b from-[#0D7C66] to-[#0B6B57]`) containing the welcome greeting, security badges, balance card, and daily limit progress indicator.
    2.  **Quick Actions & Activity Feed:** A white-background section (`bg-background`) containing cards for quick actions, recent activities, supported transaction categories, and a CTA link to the Additional Features screen.

### 2.2 Sidebar Structure
*   **None.** The current implementation does not include a navigation sidebar. The interface is optimized for single-column mobile views.

### 2.3 Header / Navbar Structure
*   A simplified, inline layout containing:
    *   Left side: User profile header (`Welcome back`, `@username`).
    *   Right side: Two action buttons:
        *   **History Icon Button:** Navigates to `/history`.
        *   **Log Out Icon Button:** Invokes session cleanup and redirects to `/login`.

### 2.4 Balance Card
*   An inline container built directly into the top green header block.
*   Displays the label "Current Balance" and formatting of the BDT currency value (`৳{session.balance.toFixed(2)}`).
*   Embeds the `<DailyLimitIndicator>` component directly below the balance value.

### 2.5 Statistics Cards
*   **None.** There are no dedicated statistics cards (such as monthly charts, spending breakdowns, or total transaction summaries). The only metric displayed is the daily limit progress.

### 2.6 Quick Actions Section
*   A grid container containing four action buttons:
    *   **Send Money:** Navigates to `/send-money`.
    *   **Transport:** Navigates to `/send-money`.
    *   **Utilities:** Navigates to `/send-money`.
    *   **Market:** Navigates to `/send-money`.
*   *Note: All actions currently redirect to the generic `/send-money` screen.*

### 2.7 Recent Transaction Section
*   Displays a list of up to three transactions retrieved dynamically from the backend.
*   Renders each item using the custom `<TransactionCard>` component.
*   If the list is empty, it falls back to a dashed container showing the placeholder text "No transactions yet".

---

## 3. Component Hierarchy & Data Flow

### 3.1 Component Hierarchy
```
Dashboard (Screen)
 ├── SecurityBadge (Device Verified status)
 ├── DailyLimitIndicator (Embedded inside the balance block)
 ├── Quick Actions Grid
 ├── Recent Transaction List
 │    └── TransactionCard (Rendered items)
 └── Additional Features CTA Button
```

### 3.2 Data Flow
```
1. Dashboard mounts
       │
       ▼
2. Check getUserSession() ──────► (If absent: redirects to /login)
       │
       ▼
3. Load session state (username, balance, limit, spent)
       │
       ▼
4. Call getTransactionHistory(username) ──► Update recentTransactions state
```

---

## 4. API Dependencies
*   **Endpoint:** `GET /transactions/<username>`
*   **Function:** `getTransactionHistory(session.username)` (imported from [frontend/src/utils/api.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/api.ts)).

---

## 5. State Management
*   **User Session:** Loaded and managed via `getUserSession()` and `clearUserSession()` (imported from [session.ts](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/utils/session.ts)) reading from `localStorage`.
*   **Local States:**
    *   `recentTransactions`: Stores the API response array of transaction records.

---

## 6. Elements That MUST Remain Unchanged
To maintain the security protocol specified in the academic thesis, the following elements **must not be altered**:
1.  **Device Verified Status Indicator:** The application must continue to render the "Device Verified" (`SecurityBadge`) status indicating that $K1$ keys are loaded.
2.  **Daily Limit Constraints:** The progress bar and validation rules for the daily limit (৳5,000.00 BDT) must remain.
3.  **Active Session Verification:** The dashboard must continue to enforce authentication checks, redirecting to `/login` if session token keys are absent.

---

## 7. Elements That Can Be Redesigned Safely
The following elements can be redesigned or updated without impacting security parameters:
1.  **Sidebar / Layout Structure:** Adding a sidebar for desktop views is safe and will improve usability on larger screens.
2.  **Statistics Cards:** Adding cards to display spending trends, monthly transaction volumes, or utility expenses will enhance the dashboard.
3.  **Recent Activity Layout:** The transaction feed can be redesigned to group items by date or add filter controls.
4.  **Categories Section:** The list of supported categories can be redesigned to use interactive filter tabs or modal info overlays.
