# DASHBOARD REDESIGN PLAN

This document outlines the architectural plan for transitioning the E-Banking dashboard from a mobile-first stacked view to a desktop-first responsive interface, preserving existing security parameters.

---

## 1. Preservation Parameters
The core authentication and cryptographic security elements must remain unchanged:
*   **Session Management:** Keep the current session loading mechanism (`getUserSession()`) based on transient in-memory parameters.
*   **Device Verification:** Continue to display the active "Device Verified" status (`SecurityBadge`) indicating key binding.
*   **Daily Limit checks:** Retain the daily petty cash limits (৳5,000.00 BDT) and spent trackers.
*   **Transaction API Integration:** Reuse `getTransactionHistory()` and `processTransfer()` endpoints.
*   **Existing Routes:** Retain all route mappings in React Router (`/`, `/send-money`, `/history`, etc.).

---

## 2. UI Mapping Matrix

| Target UI Element | Existing Component Reuse | New Component Needed | File Location |
| :--- | :--- | :--- | :--- |
| **Desktop Sidebar** | None | `Sidebar` | `components/Sidebar.tsx` |
| **Top Navbar** | `SecurityBadge` | `Navbar` | `components/Navbar.tsx` |
| **Balance Card** | `DailyLimitIndicator` | `BalanceCard` | `components/BalanceCard.tsx` |
| **Stats Cards** | None | `StatsCards` | `components/StatsCards.tsx` |
| **Quick Actions** | Button component | `QuickActionsGrid` | `components/QuickActionsGrid.tsx` |
| **Recent Activity** | `TransactionCard` | `RecentActivityFeed` | `components/RecentActivityFeed.tsx` |

---

## 3. Section Specifications

### A. Desktop Sidebar
*   **Navigation items:** Dashboard, Send Money, Merchant, Recharge, Bills, QR Pay, History, Profile, Security, Settings, Logout.
*   **Implementation:** Render on screen widths $\ge 768\text{px}$ (`md:block`). Include standard navigation links that map to existing routes. The logout link should clear session storage and redirect the user.

### B. Top Navbar
*   **Search Bar:** An input field to filter the transaction list by recipient username or reference code.
*   **Notification Bell:** Toggle element that fetches active alerts from the `/notifications/<username>` endpoint.
*   **User Profile Area:** Displays the username and active profile avatar.

### C. Balance Card
*   **Design:** A desktop-width card layout featuring the BDT currency symbol.
*   **Integration:** Map database metrics (`balance`, `today_spent`, `daily_limit`) to the card and render the `DailyLimitIndicator` progress bar.

### D. Stats Cards
*   **Calculable using current APIs:**
    *   **Today's Spending:** Derived from `session.today_spent`.
    *   **Remaining Limit:** Calculated locally as `session.daily_limit - session.today_spent`.
    *   **Recent Transaction Count:** Derived from the count of items in `recentTransactions`.
*   **Requires new API endpoints:**
    *   **Monthly Aggregate Totals:** Aggregated monthly spent totals.
    *   **Spending Categories:** Categorized totals (e.g. Utilities, Transport, Market) over all time.

### E. Quick Actions
*   Grid layout holding:
    *   **Send Money / Transport / Utilities / Market:** Reuse routes `/send-money`.
    *   **QR / NFC:** Link to simulated features in `/features`.

### F. Recent Transactions
*   **Implementation:** Grid area showing recent transactions.
*   **Component:** Maps transaction items to the updated `TransactionCard` component (with the received/sent type fix).

---

## 4. Change Impact Table

| Task / Change | File to Modify | Component to Create | Component to Reuse | Estimated Risk |
| :--- | :--- | :--- | :--- | :--- |
| **Add Sidebar Layout** | `screens/Dashboard.tsx` | `Sidebar.tsx` | None | **Low** |
| **Add Top Header** | `screens/Dashboard.tsx` | `Navbar.tsx` | `SecurityBadge` | **Low** |
| **Desktop Balance Card**| `screens/Dashboard.tsx` | `BalanceCard.tsx` | `DailyLimitIndicator`| **Low** |
| **Add Analytics Cards** | `screens/Dashboard.tsx` | `StatsCards.tsx` | None | **Low** |
| **Recent Feed Grid** | `screens/Dashboard.tsx` | `RecentActivityFeed.tsx`| `TransactionCard` | **Medium** (Ensure type mapping is correct) |

---

## 5. Responsive Layout Strategy
Use a CSS grid layout:
*   **Desktop ($\ge 768\text{px}$):** Renders a two-column grid (`grid-cols-[260px_1fr]`). The left column holds the persistent sidebar, and the right column holds the main content area.
*   **Mobile ($< 768\text{px}$):** Hides the sidebar (`hidden`) and displays a top navbar with a toggle menu button for navigation.

---

## 6. Visual Wireframe (ASCII)

```text
+------------------------------------------------------------------------------------+
|                                      NAVBAR                                        |
|  [Search Transaction...]                         [Bell]  [Device Verified]  [User] |
+-------------------+----------------------------------------------------------------+
|                   |                                                                |
|      SIDEBAR      |  +---------------------------+  +----------------------------+ |
|                   |  |    BDT BALANCE CARD       |  |      ANALYTICS CARDS       | |
|  • Dashboard      |  |  Current Balance:         |  |  Spent Today: ৳250.00      | |
|  • Send Money     |  |  ৳ 4,750.00               |  |  Remaining:   ৳4,750.00    | |
|  • Merchant       |  |                           |  |  Trans Count: 12           | |
|  • Recharge       |  |  [==== Limit Progress =]  |  +----------------------------+ |
|  • Bills          |  +---------------------------+                                 |
|  • QR Pay         |                                 +----------------------------+ |
|  • History        |  +---------------------------+  |    RECENT TRANSACTION FEED | |
|  • Profile        |  |       QUICK ACTIONS       |  |  • Alice   -৳250.00  Sent  | |
|  • Security       |  |  [Send] [Util] [NFC] [QR] |  |  • Bob     +৳100.00  Recv  | |
|  • Settings       |  +---------------------------+  |  • Gas Co  -৳500.00  Sent  | |
|  • Logout         |                                 +----------------------------+ |
+-------------------+----------------------------------------------------------------+
```
