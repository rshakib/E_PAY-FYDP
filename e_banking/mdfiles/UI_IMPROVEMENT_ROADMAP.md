# UI Improvement Roadmap

This roadmap groups the findings from the visual audit of the E-Banking codebase and screenshots into three prioritized milestones.

---

## 🛑 Phase A: Critical UI Fixes

### 1. Resolve 404 Route Failure on the Notifications Page
*   **Issue:** Clicking the notification bell or navigating to the notifications path triggers a Next.js `404 | This page could not be found` error page (`17-notifications.png`).
*   **Fix:** Repair the frontend route mapping in the application router. Ensure the notifications page points to the correct component, or replace the page link with an overlay drawer modal.

### 2. Purge Legacy Green Theme Remnants
*   **Issue:** The Merchant Payment page (`13-merchant-payment.png`) contains profile initials (SM, TH, CC) styled in the old green-first branding palette (`bg-green-50 text-green-600`), creating a visual mismatch with the primary blue layout.
*   **Fix:** Re-style initials badges using the new fintech blue system (e.g. `bg-blue-50 text-blue-600` or `bg-slate-100 text-slate-700`).

### 3. Align Status Badge Colors
*   **Issue:** The Transaction History page (`10-history.png`) displays completed payments using a brown-orange badge (`COMPLETED`), whereas the Dashboard recent transactions list uses green badges.
*   **Fix:** Standardize status pill styling across the entire frontend. Completed transactions should use consistent emerald styling (e.g., `bg-emerald-50 text-emerald-600`).

---

## 🎨 Phase B: Visual Polish

### 1. Standardize Currency Symbols
*   **Issue:** All screenshots display the United States Dollar (`$`) symbol, but the master specifications and functional database operate in Bangladeshi Taka (`৳`).
*   **Fix:** Ensure all currency render templates are updated to display the Taka symbol (`৳`) consistently across all screens (Dashboard, Send Money, History, etc.).

### 2. Upgrade Operator Logos in Mobile Recharge
*   **Issue:** The Mobile Recharge screen (`11-recharge.png`) uses simple, flat-colored square boxes (blue, red, orange) as placeholder operator logos.
*   **Fix:** Replace these flat placeholders with high-quality operator brand logo graphics for Grameenphone, Robi, Banglalink, Airtel, and Teletalk.

### 3. Refine Floating Toast Placement
*   **Issue:** The "Login successful!" alert block overlays the middle of the recent transactions list on the Dashboard, obstructing the view of the data.
*   **Fix:** Move the toast alert notification to the top-right or bottom-right corner of the workspace, and apply a clean fade-out timer.

---

## ✨ Phase C: Premium Fintech Enhancements

### 1. Bind Theme Toggle in Settings
*   **Issue:** The Theme Mode selector in Settings (`16-settings.png`) is a static UI switch.
*   **Fix:** Connect the switch to a theme provider to toggle light/dark modes by updating document class attributes and swapping CSS custom variables.

### 2. Implement Client-side Search and Filters
*   **Issue:** The search bars in the Navbar, Transaction History, and Merchant Payment pages are UI-only.
*   **Fix:** Implement local filtering logic that filters items dynamically as the user types.

### 3. Connect Profile Avatar Editor
*   **Issue:** The camera upload button overlay on the profile avatar (`14-profile.png`) is non-functional.
*   **Fix:** Bind the button to trigger a file-selection prompt, letting users upload or update their profile photos.
