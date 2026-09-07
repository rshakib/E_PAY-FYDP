# MVP Payment Portals Changelog

This changelog documents the files created and modified to implement the Minimum Viable Product (MVP) for Merchant Payment, Mobile Recharge, and Bill Payment portals, adhering to the constraint of zero backend or database modifications.

---

## 🚀 Added Screens

### 1. `MerchantPayment.tsx`
*   **Path:** [MerchantPayment.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/MerchantPayment.tsx)
*   **Features:**
    *   Search UI to lookup active merchant usernames.
    *   Recommended merchants selection grid (Amazon Store, Walmart Hub).
    *   Recent merchants shortcuts (SuperMart Central, Tech Haven, City Cafe).
    *   Initials avatar tags updated from legacy green to modern fintech blue/indigo theme.
    *   Daily petty cash limit validation logic.
    *   Direct transaction dispatch through `/transaction-processing`.

### 2. `MobileRecharge.tsx`
*   **Path:** [MobileRecharge.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/MobileRecharge.tsx)
*   **Features:**
    *   11-digit Bangladeshi phone number input validation (`/^01[3-9]\d{8}$/`).
    *   Mobile operator selection grid showing logo blocks (Grameenphone, Robi, Banglalink, Airtel, Teletalk).
    *   Amount input box with quick preset BDT buttons (৳20, ৳50, ৳100, ৳200, ৳500).
    *   Daily limit exceeding warning panel.
    *   Secure transfer processing to the target operator account (`operator_gp`).

### 3. `BillPayment.tsx`
*   **Path:** [BillPayment.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/BillPayment.tsx)
*   **Features:**
    *   Utility categories grid (Electricity, Water, Gas, Internet, Television, Insurance) with rounded icons.
    *   Mock unpaid bills display syncing with actual transaction ledger history.
    *   Separate "Pending Bills" and "Payment History" tabs showing unpaid and paid states.
    *   Automatic removal of paid bills from the unpaid tab upon successful transaction history match with `desco_biller` target accounts.

---

## 🛠️ Modified Components & Routing

### 1. `App.tsx`
*   **Path:** [App.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/App.tsx)
*   **Changes:**
    *   Imported new payment screens.
    *   Registered routes: `/merchant`, `/recharge`, `/bills`.

### 2. `Sidebar.tsx`
*   **Path:** [Sidebar.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/Sidebar.tsx)
*   **Changes:**
    *   Updated the Merchant, Recharge, and Bills buttons to navigate to `/merchant`, `/recharge`, and `/bills` instead of `/send-money`.

### 3. `Dashboard.tsx`
*   **Path:** [Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)
*   **Changes:**
    *   Updated Quick Actions paths for Merchant, Recharge, and Bills from `/send-money` to their respective dedicated routes.

---

## 🔒 Preserved Security & Zero Backend Constraints
*   **No backend endpoints added:** Rested entirely on client-side state handling and routing to `/transaction-processing`.
*   **No database migrations:** Postponed new ledger tables (`public.unpaid_bills`, `public.merchants_or_billers`).
*   **No new cryptographic code:** Reused the existing K1/K2 AES encryption + HMAC signing pipelines.
