# QR Pay MVP Changelog

This changelog outlines all file updates and additions implemented to deliver the dedicated QR Pay MVP page.

---

## 🚀 Added Screens

### 1. `QRPay.tsx`
*   **Path:** [QRPay.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/QRPay.tsx)
*   **Features:**
    *   **Self-Contained Scanner UI:** Houses a CSS-animated scanning laser grid inside a camera frame window overlay.
    *   **Simulated Scan Action:** Clicking "Scan QR" triggers a simulated checkout for the demo merchant `SuperMart Central` (receiver: `merchant_store`) at a preset BDT 100.00 amount.
    *   **Simulated Image Upload:** Simulates uploading a payment coupon image, triggering a checkout for `Tech Haven Outlet` (receiver: `merchant_store`) at BDT 150.00.
    *   **Manual Entry Form:** A toggleable code form that accepts merchant username strings and BDT amounts manually.
    *   **Recent QR Payments:** Lists the last 3 QR payments processed to `merchant_store` in the transaction history ledger.

---

## 🛠️ Modified Routing & Navigation

### 1. `App.tsx`
*   **Path:** [App.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/App.tsx)
*   **Changes:**
    *   Imported `QRPay` screen.
    *   Registered route path `/qr-pay`.

### 2. `Sidebar.tsx`
*   **Path:** [Sidebar.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/Sidebar.tsx)
*   **Changes:**
    *   Updated the "My QR" menu item path to point to `/qr-pay` instead of `/features`.

### 3. `Dashboard.tsx`
*   **Path:** [Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)
*   **Changes:**
    *   Updated the "QR Pay" action button in the Quick Actions grid to link to `/qr-pay` instead of `/features`.

---

## 🔒 Session & Zero Backend Design Compliance
*   **No backend changes:** Rested entirely on frontend simulators and client-side states.
*   **No database migrations:** Transaction checks verify standard `merchant_store` profiles in the existing `accounts` ledger.
*   **Reused UI elements:** Utilized custom `Input` and standard styling layouts.
