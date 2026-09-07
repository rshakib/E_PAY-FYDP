# Settings MVP Changelog

This changelog documents all files created and modified to implement the dedicated Settings MVP page.

---

## 🚀 Added Screens

### 1. `Settings.tsx`
*   **Path:** [Settings.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Settings.tsx)
*   **Features:**
    *   **Display & Appearance:** Theme Dark Mode switch toggle (local state), Language Selector dropdown (English/Bangla), and Currency Display Selector dropdown (BDT ৳/USD $).
    *   **Preferences:** Display Name text input, Transaction Alerts Toggle switch, and Email Alerts Toggle switch.
    *   **Application Info:** Renders metadata cards containing App Version (`v1.2.0-beta`), Build Status (`Passed`), and Environment (`Sandbox TLS`).
    *   **Action Buttons:** Features a "Save Preferences" button (triggers a success notification banner) and a "Discard Changes" button (resets all controls to defaults).

---

## 🛠️ Modified Routing & Navigation

### 1. `App.tsx`
*   **Path:** [App.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/App.tsx)
*   **Changes:**
    *   Imported `Settings` screen.
    *   Registered route path `/settings`.

### 2. `Sidebar.tsx`
*   **Path:** [Sidebar.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/Sidebar.tsx)
*   **Changes:**
    *   Updated the Settings button navigation path to point to `/settings` instead of `/features`.

### 3. `Profile.tsx`
*   **Path:** [Profile.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Profile.tsx)
*   **Changes:**
    *   Added a "Configure Settings" button under the security button in the left sidebar metadata block.

### 4. `Security.tsx`
*   **Path:** [Security.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Security.tsx)
*   **Changes:**
    *   Added a "Preferences & Alerts" configure card in the right column container that redirects users to the `/settings` screen.
    *   Fixed a JSX closing tag nesting hierarchy mismatch in the right column card wrapper.

---

## 🔒 Session & Zero Backend Design Compliance
*   **No backend changes:** Rested entirely on client-side state parameters.
*   **No database migrations:** User configuration toggles and preferences run on local React state.
*   **Reused UI assets:** Integrated `Input` fields and `Button` components to maintain styling consistency.
