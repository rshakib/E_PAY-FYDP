# Implementation Order: Payment Portals Integration

This document outlines the step-by-step developer tasks to implement Merchant Payments, Mobile Recharge, and Bill Payments.

---

## 🛠️ Step-by-Step Execution Tasks

### Task 1: Database Setup & Seed Profiles
*   **Action:** Register mock provider profiles and accounts in the Supabase database.
*   **Execution Steps:**
    1.  Insert profile rows and corresponding account rows for operators (`operator_gp`, `operator_robi`, etc.), merchants (`merchant_store`), and billers (`desco_biller`).
    2.  Register these records in the `public.merchants_or_billers` table matching categories:
        *   `merchant_store` ──► category: `merchant_payment`
        *   `operator_gp` ──► category: `utility`
        *   `desco_biller` ──► category: `bill_payment`
    3.  Create the `public.unpaid_bills` database table:
        ```sql
        create table public.unpaid_bills (
            id uuid primary key default gen_random_uuid(),
            profile_id uuid references public.profiles(id) on delete cascade,
            biller_code text not null,
            amount numeric(14, 2) not null,
            due_date date not null,
            is_paid boolean not null default false
        );
        ```

### Task 2: Backend API Endpoint Configuration
*   **Action:** Add metadata API routes and update transfer logs in `backend/app.py`.
*   **Execution Steps:**
    1.  Add `GET /api/merchants` to query rows from `merchants_or_billers` where category is `'merchant_payment'`, `'market'`, or `'transport'`.
    2.  Add `GET /api/recharge-operators` to retrieve operator list.
    3.  Add `GET /api/bills/<username>` to query outstanding bills from `unpaid_bills` for the profile matching `<username>`.
    4.  Update the `process_transfer()` `/transfer` endpoint:
        *   After the receiver account is resolved, query `merchants_or_billers` to check if `receiver_profile_id` exists.
        *   If it is a merchant or biller, pass the `merchant_id` and the merchant's category channel when calling `record_transaction()`.
        *   If the transaction type is a biller, update the corresponding invoice in `unpaid_bills` setting `is_paid = true`.

### Task 3: Frontend Route Definitions
*   **Action:** Register route paths in `frontend/src/app/App.tsx`.
*   **Execution Steps:**
    1.  Import the new screens: `MerchantPayment`, `MobileRecharge`, and `BillPayment`.
    2.  Define routes:
        *   `<Route path="/merchant" element={<MerchantPayment />} />`
        *   `<Route path="/recharge" element={<MobileRecharge />} />`
        *   `<Route path="/bills" element={<BillPayment />} />`
    3.  Update navigation links inside the desktop `Sidebar.tsx` and `Dashboard.tsx` quick actions grid to navigate to these routes instead of the generic `/send-money` form.

### Task 4: Frontend Screen Layout Design
*   **Action:** Create the UI screens matching the reference screenshots.
*   **Execution Steps:**
    1.  Create `MerchantPayment.tsx` under `screens/` containing search inputs, recommended merchant cards, and recent merchant logs.
    2.  Create `MobileRecharge.tsx` under `screens/` displaying operator logo grids, mobile input numbers, and BDT recharge values.
    3.  Create `BillPayment.tsx` under `screens/` displaying category tiles (Electricity, Water, Gas, etc.) and lists of outstanding bills.

### Task 5: Secure Payment Pipeline Linkage
*   **Action:** Connect UI form inputs to call the secure encryption transfer utility.
*   **Execution Steps:**
    1.  Integrate form submissions (e.g. clicking "Pay Bill" or "Recharge") to use the existing `processTransfer` client wrapper.
    2.  Pass the operator code (e.g. `operator_gp`), merchant code (e.g. `merchant_store`), or biller username (e.g. `desco_biller`) inside the AES ciphertext payload `Receiver:{username}|Amt:{amount}`.
    3.  Verify the transaction rotates user sessions and updates the dashboard ledger feeds on success.
