# E-Payment System - Screen Flow Diagrams

## Flow A: First Time Setup (Bank-Assisted Activation)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ONBOARDING FLOW                             │
└─────────────────────────────────────────────────────────────────┘

1. Activation Start (/)
   │
   │ User clicks "I Have an Activation Code"
   │
   ↓
2. Officer Verify (/officer-verify)
   │ Input: NID/BRC Number
   │ Input: Activation Code
   │ Input: Bank-Assigned Username
   │ 🔐 Generates K1 (Device MAC + Activation Code + NID)
   │
   │ Clicks "Verify & Continue"
   │
   ↓
3. Biometric Enrollment (/biometric-enrollment)
   │ Scan 1 of 3
   │ Scan 2 of 3
   │ Scan 3 of 3
   │ 🔐 Captures BP (Biometric Fingerprint)
   │
   │ Clicks "Complete Enrollment"
   │
   ↓
4. Create Password (/create-password)
   │ Input: Password (K2)
   │ Input: Confirm Password
   │ Password strength indicator
   │ 🔐 Establishes K2 (Known only to user)
   │
   │ Clicks "Set Password"
   │
   ↓
5. Activation Success (/activation-success)
   │ Display: Username
   │ Display: Daily Limit (৳5,000)
   │ Display: Security Features (K1, K2, BP, AES, HMAC)
   │
   │ Clicks "Go to Login"
   │
   ↓
6. Login (/login)
```

## Flow B: Daily Transaction (Core Thesis Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│                  TRANSACTION FLOW                               │
└─────────────────────────────────────────────────────────────────┘

6. Login (/login)
   │ Input: Username
   │ Input: Password (K2)
   │ ✓ Authenticates with K2
   │
   │ Clicks "Login"
   │
   ↓
7. Dashboard (/dashboard)
   │ Shows: Current Balance (৳3,200.00)
   │ Shows: Daily Limit Progress (৳1,800 spent / ৳5,000 limit)
   │ Shows: "Device Verified" badge (K1 active)
   │ Shows: Recent transactions
   │ Shows: Quick actions (Send Money, Transport, Utilities, Market)
   │
   │ Clicks "Send Money"
   │
   ↓
8. Send Money (/send-money)
   │ Input: Receiver's Username
   │ ✓ Validates receiver exists in database
   │ Input: Amount (BDT)
   │ ✓ Validates against daily limit remaining
   │ 🔐 Constructs Message M = (Receiver + Amount)
   │
   │ Clicks "Proceed"
   │
   ↓
9. Transaction Processing (/transaction-processing)
   │
   │ ┌─────────────────────────────────┐
   │ │  BIOMETRIC CONFIRMATION         │
   │ │  🔐 User places fingerprint     │
   │ │  ✓ BP captured and injected     │
   │ └─────────────────────────────────┘
   │
   │ ┌─────────────────────────────────────────────────┐
   │ │  CRYPTOGRAPHIC PROCESSING (Visualized)         │
   │ │                                                │
   │ │  Step 1 (800ms):                              │
   │ │  📊 Generating HMAC...                        │
   │ │  🔐 F1 = F(M, K1)                            │
   │ │                                                │
   │ │  Step 2 (800ms):                              │
   │ │  🔒 Encrypting with AES...                    │
   │ │  🔐 AES(K2 + BP + T)                         │
   │ │  📅 Timestamp (T): 13/05/2026 14:30:22       │
   │ │                                                │
   │ │  Step 3 (800ms):                              │
   │ │  📡 Transmitting through secure channel...    │
   │ │  🌐 Data packet animation                     │
   │ └─────────────────────────────────────────────────┘
   │
   │ Auto-navigate after processing complete
   │
   ↓
10. Transaction Result (/transaction-result)
    │
    │ ┌─────────────────────────────────────────┐
    │ │  SUCCESS STATE                         │
    │ │  ✅ Transaction Successful             │
    │ │  🔐 HMAC Verified: F1 = F2            │
    │ │  📊 Sent to: @vegetable_market_01     │
    │ │  💰 Amount: ৳250.00                   │
    │ │  💵 New Balance: ৳2,950.00            │
    │ │  📅 Timestamp Updated (T): [new time] │
    │ │  ✓ AES Encrypted | HMAC Verified      │
    │ └─────────────────────────────────────────┘
    │
    │ OR
    │
    │ ┌─────────────────────────────────────────┐
    │ │  FAILURE STATES                        │
    │ │                                        │
    │ │  ❌ HMAC Mismatch (F1 ≠ F2)          │
    │ │  ⚠️  Insufficient Balance              │
    │ │  ❌ Receiver Not Found                 │
    │ │                                        │
    │ │  Only sender is notified of failure   │
    │ └─────────────────────────────────────────┘
    │
    │ Clicks "Back to Home"
    │
    ↓
7. Dashboard (updated with new balance)
```

## Flow C: Review Transaction History

```
┌─────────────────────────────────────────────────────────────────┐
│                  HISTORY REVIEW FLOW                            │
└─────────────────────────────────────────────────────────────────┘

7. Dashboard (/dashboard)
   │
   │ Clicks "View All" or History icon
   │
   ↓
11. Transaction History (/history)
    │
    │ Filter Tabs: [All] [Successful] [Rejected]
    │
    │ Transaction Cards show:
    │ • Receiver Username
    │ • Amount (৳ BDT)
    │ • Timestamp
    │ • Status (Success/Rejected)
    │ • Security Badges (AES Secured, HMAC Verified)
    │
    │ Empty state: "No transactions today"
    │
    │ Clicks Back arrow
    │
    ↓
7. Dashboard
```

## Flow D: Additional Features (Non-Thesis Extensions)

```
┌─────────────────────────────────────────────────────────────────┐
│              ADDITIONAL FEATURES FLOW                           │
└─────────────────────────────────────────────────────────────────┘

7. Dashboard (/dashboard)
   │
   │ Clicks "Additional Features" button
   │
   ↓
12. Additional Features (/features)
    │
    │ ┌────────────────────────────┐
    │ │  📧 Email Verification     │
    │ │  • Input email address     │
    │ │  • Send verification code  │
    │ │  • ✓ Email verified badge  │
    │ └────────────────────────────┘
    │
    │ ┌────────────────────────────┐
    │ │  📱 QR Code Scanner        │
    │ │  • Camera preview          │
    │ │  • Scan merchant QR        │
    │ │  • Auto-populate receiver  │
    │ └────────────────────────────┘
    │
    │ ┌────────────────────────────┐
    │ │  📡 NFC Tap-to-Pay        │
    │ │  • Proximity animation     │
    │ │  • Tap phone on terminal   │
    │ │  • Instant payment         │
    │ └────────────────────────────┘
    │
    │ ┌────────────────────────────┐
    │ │  💳 Card Linking          │
    │ │  • Link credit/debit card  │
    │ │  • Card list display       │
    │ │  • Backup payment method   │
    │ └────────────────────────────┘
    │
    │ ┌────────────────────────────┐
    │ │  🔐 Social Login          │
    │ │  • Continue with Google    │
    │ │  • Continue with Facebook  │
    │ │  • OAuth flow             │
    │ └────────────────────────────┘
    │
    │ Clicks Back arrow
    │
    ↓
7. Dashboard
```

## Cryptographic Flow Visualization

```
USER SIDE (Fig. 2 from Paper)              SERVER SIDE (Fig. 3 from Paper)
─────────────────────────────              ──────────────────────────────

1. Construct M                             6. Receive encrypted packet
   (Receiver + Amount)                        ↓
   ↓                                       7. Decrypt with AES
2. Generate F1 = F(M, K1)                     (Extract K2, BP, T)
   (HMAC with device key)                     ↓
   ↓                                       8. Regenerate F2 = F(M, K1)
3. Encrypt with AES                           (Server computes HMAC)
   (K2 + BP + T)                              ↓
   ↓                                       9. Compare F1 = F2?
4. Transmit encrypted packet                  │
   (Over insecure channel)                    ├─ YES → Accept transaction
   ↓                                          │         Update balances
5. Wait for response                          │         Update timestamp T
                                              │
                                              └─ NO → Reject transaction
                                                      Notify sender only
```

## Screen Navigation Map

```
                    ┌──────────────┐
                    │ Activation   │
                    │   Start      │
                    │     (/)      │
                    └──────┬───────┘
                           │
                           ↓
                    ┌──────────────┐
                    │  Officer     │
                    │   Verify     │
                    └──────┬───────┘
                           │
                           ↓
                    ┌──────────────┐
                    │ Biometric    │
                    │ Enrollment   │
                    └──────┬───────┘
                           │
                           ↓
                    ┌──────────────┐
                    │   Create     │
                    │  Password    │
                    └──────┬───────┘
                           │
                           ↓
                    ┌──────────────┐
                    │ Activation   │
                    │  Success     │
                    └──────┬───────┘
                           │
                           ↓
    ┌──────────────────────┴──────────────────────┐
    │                                              │
    ↓                                              ↓
┌────────┐                                  ┌──────────────┐
│ Login  │                                  │  Dashboard   │◄─┐
└───┬────┘                                  └──────┬───────┘  │
    │                                              │          │
    └──────────────────────────────────────────────┘          │
                                                   │          │
                    ┌──────────────────────────────┼──────────┤
                    │                              │          │
                    ↓                              ↓          │
            ┌───────────────┐            ┌─────────────────┐ │
            │  Send Money   │            │  Transaction    │ │
            └───────┬───────┘            │    History      │─┘
                    │                    └─────────────────┘
                    ↓
            ┌───────────────┐
            │ Transaction   │
            │  Processing   │
            └───────┬───────┘
                    │
                    ↓
            ┌───────────────┐
            │ Transaction   │
            │    Result     │
            └───────┬───────┘
                    │
                    ↓
            ┌───────────────┐
            │   Dashboard   │
            └───────────────┘

                    Additional Features (/features)
                    Can be accessed from Dashboard
```

## Key User Journeys

### Journey 1: New User Activation (5-10 minutes)
1. Visit bank with NID/BRC → Get activation code
2. Open app → Activation Start
3. Enter NID + Activation Code + Username → K1 generated
4. Scan fingerprint 3 times → BP captured
5. Create password → K2 established
6. View activation success → Ready to use

### Journey 2: Daily Payment (30-60 seconds)
1. Login with username + password
2. Dashboard → Click "Send Money"
3. Enter receiver username + amount
4. Verify with fingerprint
5. Watch cryptographic processing
6. View success confirmation
7. Return to dashboard

### Journey 3: Transaction Review (1-2 minutes)
1. From dashboard → Click history
2. Filter: All / Successful / Rejected
3. View transaction details with security badges
4. Return to dashboard

## Security Checkpoints

| Screen | Security Element | Verification |
|--------|-----------------|--------------|
| Officer Verify | K1 Generation | Device MAC + NID + Activation Code |
| Biometric Enrollment | BP Capture | 3 fingerprint scans |
| Create Password | K2 Creation | User-only knowledge, no officer access |
| Login | K2 Authentication | Password verification |
| Dashboard | K1 Status | "Device Verified" badge |
| Send Money | Daily Limit | Amount ≤ Remaining limit |
| Transaction Processing | BP Injection | Fingerprint required |
| Transaction Processing | HMAC | F1 = F(M, K1) |
| Transaction Processing | AES Encryption | Encrypt(K2 + BP + T) |
| Transaction Result | HMAC Verification | F1 = F2 check |

---

**For Thesis Presentation**: Use these flows to demonstrate how each screen implements specific parts of the paper's methodology.
