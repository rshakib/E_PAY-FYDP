# PHASE 1 CHANGELOG: DASHBOARD REDESIGN

This document details the changes introduced during Phase 1 of the E-Banking Dashboard UI Redesign.

---

## 1. Files Created
*   **[Sidebar.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/Sidebar.tsx)**: Left-aligned navigation panel featuring logo brand, security badges, and logout link.
*   **[Navbar.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/Navbar.tsx)**: Top navbar with search input, notifications indicator bell, user profile block, and hamburger menu button.
*   **[BalanceCard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/BalanceCard.tsx)**: Card display showing total balance (with hide/show eye toggle), Send/Cash Out links, and daily limits.
*   **[StatsCards.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/StatsCards.tsx)**: Card row displaying daily spend, remaining limits, and transaction counts.

---

## 2. Files Modified
*   **[Dashboard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/screens/Dashboard.tsx)**: Replaced the old green-first mobile layout with a responsive two-column layout that integrates the new sidebar, navbar, balance, and stats components.

---

## 3. Components Added
*   `Sidebar`
*   `Navbar`
*   `BalanceCard`
*   `StatsCards`

---

## 4. Components Reused
*   **`DailyLimitIndicator`** ([DailyLimitIndicator.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/DailyLimitIndicator.tsx)): Reused to render the limit gauge within the balance card.
*   **`SecurityBadge`** ([SecurityBadge.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/SecurityBadge.tsx)): Reused to render the verification status inside the sidebar.
*   **`TransactionCard`** ([TransactionCard.tsx](file:///E:/Apps/Sohan/E_PAY/e_banking/frontend/src/app/components/TransactionCard.tsx)): Reused to display items in the recent activity list.

---

## 5. Breaking Changes
*   **None.** All existing APIs, routes, session states, and security checks are preserved.
