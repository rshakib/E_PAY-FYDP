# Feasibility Review & MVP Recommendations

This document outlines the Minimum Viable Product (MVP) recommendation to implement Merchant Payments, Mobile Recharge, and Bill Payments as quickly and safely as possible while maintaining complete security and reusing the existing transaction pipeline.

---

## 📈 MVP Feasibility Summary

To minimize complexity and eliminate integration risks, we can deliver **100% screenshot-quality functionality** by handling metadata on the frontend and routing all transactions through the existing `/transfer` backend endpoint. 

By representing merchants, mobile operators, and bill providers as standard user profiles, the backend will process their balances and rotate keys out of the box.

---

## 📋 Feature-by-Feature Analysis

### 1. Merchant Payment
*   **MVP Version:** 
    *   Hardcode recommended merchant buttons (Amazon, Walmart) and recent merchants (SuperMart Central, Tech Haven, City Cafe) in the frontend React dashboard.
    *   Clicking a merchant populates the transaction receiver name field (e.g. `@merchant_store`) and triggers the standard, secure `processTransfer` flow.
*   **Full Version:** Adds dynamically queried merchant registers, search database indexes, and merchant activity metrics.
*   **Extra Complexity of Full Version:** Requires new database tables, endpoint queries (`GET /api/merchants`), and additional backend search logic.
*   **Recommended Version:** **MVP Version** (Delivers the exact target UI and runs a real secure transfer to the merchant's account with zero backend changes).

---

### 2. Mobile Recharge
*   **MVP Version:** 
    *   Hardcode the five operators (Grameenphone, Robi, Banglalink, Airtel, Teletalk) in a clean frontend grid.
    *   When the user selects an operator, enters their phone number, and inputs the BDT amount, the frontend executes a secure transfer to the operator's account (e.g. `operator_gp`).
*   **Full Version:** Adds real-time mobile number validation queries, and operator balance triggers.
*   **Extra Complexity of Full Version:** Requires new database tables, validation integrations, and operators logs.
*   **Recommended Version:** **MVP Version** (Renders operator lists matching screenshots and triggers a real balance transfer to the operator account).

---

### 3. Bill Payment
*   **MVP Version:**
    *   Render the utility categories and display mock unpaid bills (e.g. Electricity: ৳850.00, Water: ৳450.00) in the frontend React state.
    *   When the user clicks "Pay", it runs a real secure transfer to the biller's username (e.g. `desco_biller`). Upon success, it updates the frontend state to remove the bill from the unpaid list.
*   **Full Version:** Adds an invoices tracking table, database balance checks for billers, and auto-generated monthly bill triggers.
*   **Extra Complexity of Full Version:** Requires database schema migrations, bill statement endpoints, and invoice state synchronization hooks.
*   **Recommended Version:** **MVP Version** (Simulates outstanding bills and pays them through the secure transfer pipeline with zero backend modifications).

---

## 🛑 Postponed Infrastructure

To ensure a rapid and safe release, we recommend postponing the following database and API changes:

### Postponed Database Tables
1.  `public.unpaid_bills` (Postponed): Can be replaced by client-side mock lists in React state.
2.  `public.merchants_or_billers` (Postponed): We can resolve merchant, operator, and biller accounts by querying their standard profile rows in the `public.profiles` table.

### Postponed Backend APIs
1.  `GET /api/merchants` (Postponed): Replaced by static frontend lists.
2.  `GET /api/recharge-operators` (Postponed): Replaced by static operator selections.
3.  `GET /api/bills/<username>` (Postponed): Replaced by local state list variables.

---

## 🏆 MVP Architecture Highlights

*   **Zero Database Modifications:** No SQL schema migrations or table creation scripts are executed.
*   **Zero Backend API Modifications:** We keep `/transfer` as the single point of transaction entry.
*   **Complete Security Coverage:** Because all payments go through `/transfer`, they automatically benefit from K2 AES encryption, HMAC integrity checks, and rotating timestamps ($T$).
