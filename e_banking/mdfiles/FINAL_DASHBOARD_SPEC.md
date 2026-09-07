# FINAL UI SPECIFICATION: MODERNIZED DASHBOARD

This document serves as the final UI specification and source of truth for the redesigned, responsive E-Banking dashboard.

---

## 1. Responsive Layout Dimensions & Breakpoints

The dashboard uses a responsive layout that adapts to different screen sizes:

### 1.1 Desktop Layout ($\ge 1024\text{px}$ - Tailwind `lg`)
*   **Structure:** Two-column grid layout.
    *   **Column 1 (Sidebar):** Persistent sidebar, fixed width of `260px`, spans the full height of the viewport.
    *   **Column 2 (Main Workspace):** Flexible width (`1fr`), contains the top navigation bar (`height: 70px`) and the dashboard content area.
*   **Main Content Grid:** A multi-column flex grid containing the Balance Card, Stats Cards, Quick Actions, and the Recent Activity feed.

### 1.2 Tablet Layout ($768\text{px}$ to $1023\text{px}$ - Tailwind `md`)
*   **Structure:** Single-column workspace.
    *   **Sidebar:** Hidden by default, toggled via a hamburger menu button in the top navbar.
    *   **Header:** Standard navbar containing the search bar, notification bell, and user avatar.
*   **Content Grid:** Cards stack vertically. Balance and Stats cards are displayed at the top, followed by Quick Actions and Recent Activity.

### 1.3 Mobile Layout ($< 768\text{px}$)
*   **Structure:** Optimized single-column vertical layout.
    *   **Sidebar:** Hidden. Accessed only via a full-screen drawer menu.
    *   **Header:** Navbar displaying the search bar and menu triggers.
*   **Content Cards:** Stacked vertically, filling the width of the viewport (`w-full`).

---

## 2. Component Hierarchy
```
Dashboard (Screen Layout Container)
 ├── DesktopSidebar (Hidden on mobile, persistent on desktop)
 └── Workspace Wrapper (Flex column)
      ├── TopNavbar (Search, Notifications, Profile avatar)
      └── Main Grid Area
           ├── Row 1 (Grid: Cols 1/3)
           │    ├── BalanceCard (Displays balance and limits)
           │    │    └── DailyLimitIndicator (Progress bar)
           │    └── StatsCards (Grid of metric cards)
           └── Row 2 (Grid: Cols 1/2)
                ├── QuickActionsGrid (Quick action buttons)
                └── RecentActivityFeed (Ledger list)
                     └── TransactionCard (Rendered items)
```

---

## 3. Section Specifications

### 3.1 Desktop Sidebar
*   **Content:**
    *   **Brand Logo:** Deep teal e-pay icon and title text.
    *   **Navigation Links:** Dashboard, Send Money, Merchant, Recharge, Bills, QR Pay, History, Profile, Security, Settings.
    *   **Session Action:** Log Out button.
    *   **Security Badge:** Embedded active `Device Verified` badge.
*   **Behavior:**
    *   Active navigation items are highlighted in green (`#0D7C66`).
    *   Hovering over navigation links displays a subtle gray background transition.
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
    *   **Search:** Filters the transaction list by recipient username or reference code.
    *   **Notification Bell:** Toggle element that fetches active alerts from the `/notifications/<username>` endpoint.
    *   **Profile Dropdown:** Opens a menu with links to Profile, Settings, and Log Out.
*   **Data Source:**
    *   User profile data from `getUserSession()`.
    *   Notifications list fetched via `getNotifications(username)`.
*   **Reused Component:** None.
*   **New Component:** `Navbar`

### 3.3 Balance Card
*   **Content:**
    *   **Wallet Header:** Title label "Wallet Balance".
    *   **BDT Value Display:** Main balance value formatting (`৳{balance}`).
    *   **Limit indicator:** Embedded `<DailyLimitIndicator>` progress bar showing spent and remaining limits.
*   **Behavior:**
    *   Updates dynamically after successful transactions.
    *   The limit bar color changes dynamically based on usage (green $\le 70\%$, yellow $\le 90\%$, red otherwise).
*   **Data Source:** User session parameters (`balance`, `today_spent`, `daily_limit`).
*   **Reused Component:** [DailyLimitIndicator.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/DailyLimitIndicator.tsx)
*   **New Component:** `BalanceCard`

### 3.4 Stats Cards
*   **Content:**
    *   **Spent Today Card:** Displays `session.today_spent`.
    *   **Remaining Limit Card:** Displays calculated remaining limit.
    *   **Transaction Volume Card:** Displays count of transactions in the recent history list.
*   **Behavior:** Updates dynamically as transaction statuses are updated.
*   **Data Source:** User session parameters and transaction history array.
*   **Reused Component:** None.
*   **New Component:** `StatsCards`

### 3.5 Quick Actions
*   **Content:**
    *   A grid of action buttons: Send Money, Transport, Utilities, Market.
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

---

## 4. Styling & Typography Guidelines
*   **Font Stack:** Inter, sans-serif.
*   **Color Palette:**
    *   Primary: `#0D7C66`
    *   Secondary: `#E8F5F3`
    *   Background: `#F8F9FA`
    *   Card Background: `#FFFFFF`
    *   Text: `#1A1A1A`
    *   Muted Text: `#757575`
*   **Visual Enhancements:** Cards should feature rounded corners (`rounded-2xl`), subtle shadows (`shadow-sm`), and clear border rules (`border border-border`).
