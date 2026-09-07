# User Profile MVP Changelog

This changelog outlines all modifications and new files created to deliver the dedicated User Profile MVP screen with zero backend/database alterations.

---

## 🚀 Added Screens

### 1. `Profile.tsx`
*   **Path:** [Profile.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Profile.tsx)
*   **Features:**
    *   A centered Avatar display featuring username initials, matching [screenshots/14-profile.png](file:///E:/Apps/Sohan/E_PAY/e_banking/screenshots/14-profile.png).
    *   A simulated photo uploader camera icon button overlaid on the avatar.
    *   A ShieldCheck verified account badge container styled in fintech blue.
    *   Personal Information cards displaying Full Name, Email, Username, and Phone. Information is dynamically derived from the active session username (e.g. `@tester1` resolves to Tester One, `tester1@niropay.com`, +880 1712-345678).
    *   A Linked Devices section showcasing the Current Device ("Google Pixel 8 Pro" - Active Now) and a secondary desktop browser device.
    *   A red-bordered "Logout From All Devices" action button that clears the session and returns to login.

---

## 🛠️ Modified Routing & Navigation

### 1. `App.tsx`
*   **Path:** [App.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/App.tsx)
*   **Changes:**
    *   Imported `Profile` screen.
    *   Registered route path `/profile`.

### 2. `Sidebar.tsx`
*   **Path:** [Sidebar.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/Sidebar.tsx)
*   **Changes:**
    *   Updated the Profile item navigation link to point to `/profile` instead of `/features`.

### 3. `Navbar.tsx`
*   **Path:** [Navbar.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/Navbar.tsx)
*   **Changes:**
    *   Wrapped the profile header container widget in an interactive button styled as `cursor-pointer hover:opacity-80` that navigates users directly to `/profile`.

### 4. `Dashboard.tsx`
*   **Path:** [Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)
*   **Changes:**
    *   Updated the Profile button in the Quick Actions grid to link to `/profile` instead of `/features`.

---

## 🔒 Session & Zero Backend Design Compliance
*   **No new API endpoints:** Personal profile cards derive data from active `session.username` without database fetching or schema expansion.
*   **Placeholder Linked Devices:** Hardcoded devices list renders the exact target UI elements.
*   **UI only avatar uploader:** Styled camera button does not trigger any multi-part uploads to Supabase buckets.
