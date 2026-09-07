# FINAL UI SPECIFICATION V2: MODERNIZED DASHBOARD

This document serves as the updated UI specification and final source of truth for the redesigned, responsive E-Banking dashboard.

---

## 1. Fintech Blue Color Palette

The color system has been updated to transition from the deep teal brand color to a modern, premium fintech blue color scheme:

*   **Primary Blue:** `#2563EB` (Royal Blue - trust, clarity)
*   **Deep Primary:** `#1E40AF` (Deep Indigo Blue - hover states and primary text headers)
*   **Secondary Blue:** `#EFF6FF` (Light Blue Tint - card backgrounds and border indicators)
*   **Accent Blue:** `#3B82F6` (Electric Blue - highlight indicators and active states)
*   **Neutral Background:** `#F8FAFC` (Slate 50 - clean background canvas)
*   **Text (Dark):** `#0F172A` (Slate 900 - high-contrast typography)
*   **Text (Muted):** `#64748B` (Slate 500 - descriptions and secondary text)
*   **Border:** `#E2E8F0` (Slate 200 - clean border rules)

---

## 2. Layout & Viewport Specifications

### 2.1 Desktop Layout ($\ge 1024\text{px}$)
*   **Sidebar Column:** Width `260px`, height `100vh`, fixed positioning. Contains the primary navigation list, with the **Log Out** button fixed at the bottom.
*   **Content Column:** Flex width (`1fr`), containing the Top Navbar and the dashboard content grid.

### 2.2 Mobile & Tablet Layout ($< 1024\text{px}$)
*   **Sidebar Column:** Hidden. Navigation is moved to a slide-out hamburger menu drawer.
*   **Workspace:** Spans the full width of the screen. Cards stack vertically.

---

## 3. Section Specifications

### 3.1 Desktop Sidebar
*   **Content:**
    *   **Fintech Brand Logo:** Modern e-pay blue icon.
    *   **Navigation List:**
        *   Dashboard
        *   Send Money
        *   Merchant
        *   Recharge
        *   Bills
        *   My QR
        *   History
        *   Profile
        *   Security
        *   Settings
    *   **Logout Link:** Positioned at the bottom of the sidebar.
*   **Behavior:**
    *   Active navigation items are highlighted in blue (`#2563EB`) with a light blue background (`#EFF6FF`).
    *   Hovering over navigation links displays a gray background transition.
    *   Clicking **Log Out** clears the user session and redirects the browser to `/login`.
*   **Data Source:** User session username (loaded from `getUserSession()`).
*   **Reused Component:** [SecurityBadge.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/SecurityBadge.tsx)
*   **New Component:** `Sidebar`

### 3.2 Top Navbar
*   **Content:**
    *   **Search Input:** A text input with a magnifying glass icon.
    *   **Notification Icon:** A bell icon with a red badge indicating unread notifications count.
    *   **Profile Menu:** Displays the user avatar and username.
*   **Behavior:**
    *   **Search (UI Only):** Captures user input for transaction history searches. *Note: Backend filtering is not active in this phase.*
    *   **Notification Bell:** Toggle element that fetches active alerts from the `/notifications/<username>` endpoint.
*   **Data Source:**
    *   User profile data from `getUserSession()`.
    *   Notifications list fetched via `getNotifications(username)`.
*   **Reused Component:** None.
*   **New Component:** `Navbar`

### 3.3 Balance Card
*   **Content:**
    *   **Total Balance Title:** Text label "Total Balance".
    *   **Balance Display:** Main balance value formatting (`৳{balance}`).
    *   **Balance Hide/Show Toggle:** A button with an eye/eye-off icon.
    *   **Action Buttons:**
        *   **Send Money Button:** Navigates to `/send-money`.
        *   **Cash Out Button:** Navigates to `/send-money` with the cash out state.
    *   **Daily Limit indicator:** Embedded `<DailyLimitIndicator>` progress bar.
*   **Behavior:**
    *   **Toggle:** Clicking the eye icon toggles the balance display between the numeric balance value and masked characters (`৳••••••`).
    *   The limit bar color changes dynamically based on usage (green $\le 70\%$, yellow $\le 90\%$, red otherwise).
*   **Data Source:** User session parameters (`balance`, `today_spent`, `daily_limit`).
*   **Reused Component:** [DailyLimitIndicator.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/DailyLimitIndicator.tsx)
*   **New Component:** `BalanceCard`

### 3.4 Stats Cards
*   **Content:**
    *   **Spent Today Card:** Displays `session.today_spent`.
    *   **Remaining Limit Card:** Displays calculated remaining limit.
    *   **Transaction Volume Card:** Displays count of transactions in the recent history list.
*   **Design:** Modern fintech cards featuring light blue borders, colored status icons, and subtle shadows.
*   **Behavior:** Updates dynamically as transaction statuses are updated.
*   **Data Source:** User session parameters and transaction history array.
*   **Reused Component:** None.
*   **New Component:** `StatsCards`

### 3.5 Quick Actions
*   **Content:**
    *   A grid of action buttons:
        *   Send Money
        *   Merchant
        *   Recharge
        *   Bills
        *   Cash Out
        *   QR Pay
        *   History
        *   Profile
*   **Behavior:**
    *   Clicking **Send Money** navigates to `/send-money`.
    *   Clicking other options navigates to `/send-money` with the appropriate category state to dynamically set the header.
*   **Data Source:** Static navigation links.
*   **Reused Component:** [Button.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/Button.tsx)
*   **New Component:** `QuickActionsGrid`

### 3.6 Recent Transactions
*   **Content:**
    *   List of up to three transactions.
    *   "View All" redirect link pointing to the history screen.
*   **Behavior:**
    *   Displays recent transactions using the `TransactionCard` component.
    *   Uses the updated card logic to format incoming vs outgoing payments correctly.
*   **Data Source:** `recentTransactions` local state.
*   **Reused Component:** [TransactionCard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/TransactionCard.tsx)
*   **New Component:** `RecentActivityFeed`
