# TARGET VISUAL UI ANALYSIS

This document details the visual components, color palettes, spacing, typography, and iconography representing the target modern fintech dashboard design.

---

## 1. Layout Structure
*   **Grid Framework:** Standard 2-column sidebar design on desktop viewports.
*   **Sidebar (Left):** Spans the full height of the viewport (`h-screen`). Fixed width (`260px`). Left border separates it from the content area.
*   **Main Workspace (Right):** Flex container containing the Top Header and the main content dashboard cards.
*   **Card Framework:** Main content is arranged in rounded cards with clear borders and subtle shadows (`border border-slate-200 shadow-sm`).

---

## 2. Colors & Styling System
The layout implements a modern fintech blue color system:
*   **Primary Accent:** Royal Blue (`#2563EB`) used for primary button fills, active navigation highlights, and text links.
*   **Primary Deep:** Deep Indigo (`#1E40AF`) used for hover highlights and main section headers.
*   **Subtle backgrounds:** Light Slate/Blue Tint (`#EFF6FF`) for balance cards, state selections, and active link blocks.
*   **Neutral canvas:** Soft gray-slate canvas (`#F8FAFC`) to minimize visual fatigue.
*   **Typography contrast:** Slate 900 (`#0F172A`) for text headers and body content, Slate 500 (`#64748B`) for helper text.

---

## 3. Spacing & Grid Alignment
*   **Margins:** 24px padding (`p-6`) on the main container.
*   **Margins between card blocks:** 24px gaps (`gap-6`) between core containers.
*   **Component padding:** 16px to 24px (`p-4` to `p-6`) inside content cards.
*   **Typography heights:** Consistent line-height settings to maintain vertical rhythm.

---

## 4. Typography
*   **Typeface:** Clean, sans-serif typography (Inter/Roboto stack).
*   **Font Weights:** Medium (`font-medium`) for navigation items, Semi-bold (`font-semibold`) and Bold (`font-bold`) for balance values and section headers.

---

## 5. Icon Usage
*   **Style:** Minimalist line icons (Lucide React).
*   **Coloring:** Blue-tinted icons for quick actions and metrics.
*   **Actions:** Small chevron indicators on links.

---

## 6. Layout Elements & Visual Design

### 6.1 Desktop Sidebar
*   Persistent left column containing:
    *   Header brand emblem.
    *   List of 10 navigation items.
    *   Log Out button fixed at the bottom.

### 6.2 Top Navbar
*   An inline flex navbar with:
    *   Left side: Search bar with search icon.
    *   Right side: Notification bell with a red badge, active `Device Verified` badge, and user profile avatar.

### 6.3 Balance Card
*   A card container displaying:
    *   "Total Balance" header.
    *   Masked balance value (`৳••••••`) with a toggle eye button.
    *   Two prominent action buttons: **Send Money** and **Cash Out**.
    *   An embedded daily transaction limit progress indicator.

### 6.4 Stats Cards
*   A row of 3 rounded cards:
    *   **Spent Today:** Displays a money counter.
    *   **Remaining Daily Limit:** Displays calculated limits.
    *   **Transaction Volume:** Displays count of transactions.

### 6.5 Quick Actions Grid
*   A 2x4 grid layout containing quick action items (Send Money, Merchant, Recharge, Bills, Cash Out, QR Pay, History, Profile).

### 6.6 Recent Activity Feed
*   Lists the last 3 transaction items with correct color coding (green `+` for received, black `-` for sent).
