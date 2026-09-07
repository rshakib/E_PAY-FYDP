# Refactor Recommendations: Code Quality & Component Optimization

This report outlines key code cleanups, component consolidations, and layout improvements to standardize the e-banking React application codebase and eliminate redundant files.

---

## 🧼 Code Cleanups & Directory Pruning

### 1. Prune Unused shadcn Directory
*   **Recommendation:** Delete the entire directory `frontend/src/app/components/ui/` containing 48 unused component files.
*   **Rationale:** The project relies on custom-built components (`Button.tsx`, `Input.tsx`, `Sidebar.tsx`) directly under `components/`. The shadcn directory is dead weight and clutters bundle checks.

### 2. Standardize Page Headers
*   **Recommendation:** Create a single reusable `<PageHeader title="String" subtitle="String" showBackButton={true} />` component.
*   **Rationale:** Currently, page headers are duplicated across files (e.g. `MerchantPayment.tsx`, `Profile.tsx`, `Security.tsx`, `SendMoney.tsx`) and use differing layout borders, padding heights, and styles. A unified component ensures design consistency.

### 3. Consolidate Custom Switches/Toggles
*   **Recommendation:** Extract the custom switch container used in `Security.tsx` and `Settings.tsx` into a reusable `<Switch checked={boolean} onChange={(val: boolean) => void} label="String" />` component under `components/`.
*   **Rationale:** The iOS-style switch logic is duplicated across security biometrics and settings preferences, violating the DRY (Don't Repeat Yourself) principle.

---

## 🛠️ Layout & UX Refinements

### 1. Fix Transaction Arrow Directions & Colors
*   **Recommendation:** Update [TransactionCard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/TransactionCard.tsx) and [TransactionHistory.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/TransactionHistory.tsx) to:
    *   Render green arrows pointing down/left with green amount texts for `incoming / received` transfers.
    *   Render red arrows pointing up/right with slate/red text for `outgoing / sent` transfers.
*   **Rationale:** Current layouts display red icons for both credit and debit operations, which violates standard fintech UX conventions.

### 2. Repurpose/Delete `/features` (AdditionalFeatures)
*   **Recommendation:** Either remove the `/features` route entirely or rename it to `/qr-pay`.
*   **Rationale:** Profile, Security, and Settings now have dedicated screens. The `/features` page is mostly empty and serves only as a landing route for the QR Pay placeholder.

### 3. Accessible Switch Roles
*   **Recommendation:** Add `role="switch"` and `aria-checked={checked}` attributes to all interactive switch elements to support screen readers and enhance keyboard navigation.
