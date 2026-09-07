# Master Plan: Merchant, Mobile Recharge, and Bill Payments

This document details the unified architecture to implement Merchant Payments, Mobile Recharge, and Bill Payments, reusing the existing secure cryptographic transfer pipeline.

---

## 🎨 Unified Payment Architecture

To ensure security and prevent code duplication, all payments reuse the core transfer pipeline:
```
[Frontend Form UI] 
       │ (Selects Merchant / Biller / Operator details)
       ▼
[Cryptographic Payload Engine] (Derives K2, BP, T, hashes message M|F1)
       │ (Encrypts payload using AES-CBC)
       ▼
[API processTransfer()] ──► POST /transfer ──► [Backend Decryption & Verification]
                                                      │
                                                      ▼ (Saves to ledger)
                                              [Supabase Tables]
```

By formatting the receiver's unique code/username as the target in the encrypted message string (`Receiver:{receiver_username}|Amt:{amount}`), we can reuse the entire backend verification, decryption, and rotate-key pipeline.

---

## 📋 Portal Specifications

### 1. Merchant Payment
*   **Exact Route:** `/merchant`
*   **Screen Hierarchy:**
    *   Dashboard (`/dashboard`) ──► Click "Merchant" ──► Merchant Dashboard (`/merchant`)
    *   Search Merchant ──► Choose Recommended/Recent Merchant ──► Pay Form ──► Processing ──► Success Screen
*   **Reusable Components:** `Button`, `Input`, `Navbar`, `Sidebar`, `TransactionCard`.
*   **New Components:** `MerchantSearchDashboard`, `MerchantCard`, `RecentMerchantsFeed`.
*   **Database Changes:**
    *   Ensure the `public.merchants_or_billers` table is populated.
    *   Ensure target merchants exist as profile and account rows in `public.profiles` and `public.accounts` with the type `'merchant'`.
*   **Backend Changes:**
    *   Add GET `/api/merchants` to query verified outlets from `merchants_or_billers` where category in (`'merchant_payment'`, `'market'`, `'transport'`).
    *   Modify `/transfer` response to check if the receiver's profile ID exists in `merchants_or_billers`. If yes, pass the `merchant_id` and correct channel (e.g. `'merchant_payment'`) when calling `record_transaction()`.
*   **API Changes:**
    *   `export async function getMerchants()` inside `utils/api.ts`.
*   **Validation Rules:** User input validation for merchant username checks and limit constraints.
*   **Transaction Recording:** Saves transaction channel as `merchant_payment` and links `merchant_id`.

---

### 2. Mobile Recharge
*   **Exact Route:** `/recharge`
*   **Screen Hierarchy:**
    *   Dashboard ──► Click "Recharge" ──► Operator Picker (`/recharge`)
    *   Select Operator ──► Input Mobile & Amount ──► Crypto Encryption ──► Success Screen
*   **Reusable Components:** `Input`, `Button`, `Navbar`, `Sidebar`.
*   **New Components:** `OperatorGrid`, `OperatorTile`, `RechargeAmountSelector`.
*   **Database Changes:**
    *   Insert profile and account rows for mobile operators (e.g., `operator_gp`, `operator_robi`, `operator_bl`, `operator_airtel`, `operator_teletalk`) with the type `'biller'`.
    *   Ensure operator rows are registered in `merchants_or_billers` matching category `'utility'`.
*   **Backend Changes:**
    *   Add GET `/api/recharge-operators` to fetch recharge accounts.
*   **API Changes:**
    *   `export async function getRechargeOperators()` in `utils/api.ts`.
*   **Validation Rules:** Mobile number format validation (`^01[3-9]\d{8}$`) and BDT limits.
*   **Transaction Recording:** Saves transaction channel as `utility` and links operator's `merchant_id`.

---

### 3. Bill Payment
*   **Exact Route:** `/bills`
*   **Screen Hierarchy:**
    *   Dashboard ──► Click "Bills" ──► Utilities Portal (`/bills`)
    *   Select Service (Electricity, Water, etc.) ──► Input Invoice Details ──► Verify Bill ──► Cryptographic Payment ──► Success
*   **Reusable Components:** `Navbar`, `Sidebar`, `Button`, `Input`.
*   **New Components:** `BillCategoryTile`, `PendingBillsList`, `BillPaymentModal`.
*   **Database Changes:**
    *   Add table `public.unpaid_bills` containing fields: `id`, `profile_id`, `biller_code`, `amount`, `due_date`, `is_paid`.
    *   Insert provider accounts (e.g., `desco_biller`, `wasa_biller`) with account type `'biller'`.
*   **Backend Changes:**
    *   Add GET `/api/bills/<username>` to fetch pending user bills.
    *   Modify `/transfer` so that a successful transfer to a biller mark the invoice as `is_paid = true` in `unpaid_bills`.
*   **API Changes:**
    *   `export async function getPendingBills(username)` and `export async function payBill(data)`.
*   **Validation Rules:** Bill reference number checks, outstanding invoice match.
*   **Transaction Recording:** Channel recorded as `bill_payment`, links the biller's `merchant_id` in transactions log.

---

## 🔒 Security Implications

1.  **Replay Protection:** Re-using the secure `/transfer` route guarantees that timestamp rotation $T$ happens on every single merchant, bill, or recharge transaction.
2.  **Mitigating Key Exposure:** The decryption keys ($K2$, $BP$) are processed in-memory during transaction signing and are never exposed.
3.  **Authorization Integrity:** Backend authorization checks `require_auth` session tokens. IDOR checks ensure users cannot query outstanding bills or transactions for other accounts.
