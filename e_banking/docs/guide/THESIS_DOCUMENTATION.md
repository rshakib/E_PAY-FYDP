# E-Payment System Thesis Prototype

**Source Paper**: E-Payment System to Reduce Use of Paper Money for Daily Transactions (ICECTE 2022)

## Overview

This is a mobile-first responsive e-payment application prototype implementing the cryptographic methodology from the research paper. The system provides secure digital transactions for petty cash payments **without OTP, phone verification, or SMS recovery**.

## Core Cryptographic Elements

### Authentication Components

| Element | Description | UI Representation |
|---------|-------------|-------------------|
| **K1** | Private HMAC key (device-bound) | "Device Authenticated" badge, bound to MAC address |
| **K2** | User password | Password field with "(K2)" label, known only to user |
| **BP** | Biometric fingerprint | Fingerprint prompt overlay, required for each transaction |
| **T** | Timestamp key | Live timestamp during transaction processing |
| **M** | Message | Transfer form data (Receiver Username + Amount) |
| **F1/F2** | HMAC values | Integrity check animation, "HMAC Verified" badge |

### Security Features

- **AES Encryption**: All transactions encrypted using K2 + BP + T
- **HMAC Authentication**: Message integrity verified using K1
- **Insecure Channel**: Encrypted data transmitted (paper's specification)
- **Daily Limit**: Hard cap on petty cash transactions, set at registration

## Screen Architecture

### A. Onboarding Flow (Bank-Assisted Activation)

1. **Activation Start** (`/`)
   - Explains bank-assisted activation process
   - Requires NID or BRC to obtain activation code
   - Routes to Officer Verify screen

2. **Officer Verify** (`/officer-verify`)
   - **Generates K1**: Using activation code + NID/BRC + device MAC address
   - Bank officer provides username (not user-chosen)
   - Device binding for security

3. **Biometric Enrollment** (`/biometric-enrollment`)
   - **Captures BP**: Three fingerprint scans
   - Will be used to encrypt every transaction
   - Progress indicator (1 of 3, 2 of 3, 3 of 3)

4. **Create Password** (`/create-password`)
   - **Establishes K2**: User creates password known only to them
   - Password strength indicator
   - Critical constraint: Officer cannot view or reset this password

5. **Activation Success** (`/activation-success`)
   - Displays username and daily transaction limit
   - Shows enabled security features (AES, HMAC, K1, BP)
   - Routes to Login

### B. Core Application Flow

6. **Login** (`/login`)
   - Username + Password (K2) authentication
   - No OTP or phone verification
   - Password recovery only via bank branch visit

7. **Dashboard** (`/dashboard`)
   - Current balance and daily limit progress bar
   - "Device Verified" badge (K1 active indicator)
   - Quick action categories:
     - Send Money (primary)
     - Transport payments
     - Utilities
     - Market/Education
   - Recent transaction activity
   - Access to Additional Features

8. **Send Money** (`/send-money`)
   - **Constructs Message M**: Receiver Username + Amount
   - Username validation (bank-assigned only, not phone)
   - Daily limit validation (inline error if exceeded)
   - Receiver lookup and verification

9. **Transaction Processing** (`/transaction-processing`)
   - **Biometric Confirmation**: Fingerprint overlay (injects BP)
   - **Cryptographic Visualization**:
     - Step 1: Generating HMAC (F1 = F(M, K1))
     - Step 2: AES Encryption (K2 + BP + T)
     - Step 3: Secure transmission
   - Live timestamp (T) display
   - Represents paper's Fig. 2 (User Side)

10. **Transaction Result** (`/transaction-result`)
    - Success state: "HMAC Verified: F1 = F2" badge
    - Displays new balance and updated timestamp
    - Failure states:
      - HMAC Mismatch (F1 ≠ F2)
      - Insufficient Balance
      - Receiver Not Found
    - Represents paper's Fig. 3 (Server Side)

### C. Utility Screens

11. **Transaction History** (`/history`)
    - Filter tabs: All | Successful | Rejected
    - Each transaction shows:
      - Receiver username
      - Amount
      - Timestamp
      - Status with security badges
    - Empty state for filtered views

12. **Additional Features** (`/features`)
    - **Email Verification**: Account recovery option
    - **QR Code Scanner**: Scan merchant codes
    - **NFC Tap-to-Pay**: Contactless payments
    - **Card Linking**: Credit/debit card backup
    - **Social Login**: Google/Facebook OAuth
    - Note: These extend beyond core thesis methodology

## Critical Constraints

### What This System Does NOT Have

❌ **No OTP** - No one-time password verification  
❌ **No Phone Verification** - No phone number input anywhere  
❌ **No SMS Recovery** - Password reset only via bank branch  
❌ **No Phone-to-Phone Transfer** - Only username-to-username  
❌ **No Bank Account Transfer** - Petty cash system only  

### What This System DOES Have

✅ **K1 Device Binding** - MAC address bound to account  
✅ **K2 User Password** - Known only to user, not officer  
✅ **BP Biometric** - Fingerprint required for every transaction  
✅ **HMAC Verification** - Message integrity checks (F1 = F2)  
✅ **AES Encryption** - K2 + BP + T based encryption  
✅ **Daily Limit** - Petty cash hard cap, resets every 24 hours  
✅ **Timestamp Protection** - Prevents replay attacks  

## Design System

### Color Palette

- **Primary**: `#0D7C66` (Deep teal - trust, security)
- **Success**: `#10B981` (Emerald green)
- **Error**: `#DC143C` (Crimson red)
- **Background**: `#FFFFFF` (White) / `#F8F9FA` (Light gray)
- **Secondary**: `#E8F5F3` (Teal tint)

### Typography

- **Font Family**: Inter/Roboto (clean, legible)
- **Icons**: Lucide React (line style, professional)

### Component Library

- **Input**: Standard text and secure password (K2) variants
- **Button**: Primary, secondary, outline, danger variants
- **SecurityBadge**: Device-verified, HMAC-verified, AES-secured, integrity-check
- **FingerprintOverlay**: Modal with pulse animation
- **ProcessingStep**: Three-step cryptographic visualization
- **TransactionCard**: History and dashboard activity
- **DailyLimitIndicator**: Progress bar with spent/remaining

## Methodology Mapping

This prototype directly implements the paper's methodology:

### Paper Section → UI Implementation

- **Section II (Activation)** → Onboarding screens 1-5
- **Fig. 1 (Payment Categories)** → Dashboard quick actions
- **Fig. 2 (User-Side Encryption)** → Transaction Processing screen
- **Fig. 3 (Server-Side Verification)** → Transaction Result screen
- **Daily Limit Concept** → Dashboard limit indicator + Send Money validation
- **No OTP Requirement** → All authentication flows

## Technical Stack

- **Framework**: React 18.3.1
- **Routing**: React Router 7.13.0
- **Styling**: Tailwind CSS 4.1.12
- **Animations**: Motion (Framer Motion) 12.23.24
- **Icons**: Lucide React 0.487.0
- **Build Tool**: Vite 6.3.5

## Running the Application

The Vite dev server is already running. The application is mobile-first responsive and automatically adapts to:

- **Mobile**: iOS/Android dimensions (primary)
- **Tablet**: iPad and similar devices
- **Desktop**: Web breakpoint for larger screens

## Thesis Defense Notes

### Methodology Legend

For your thesis presentation, this prototype visualizes:

1. **K1 Generation**: Officer Verify screen shows device binding
2. **K2 Establishment**: Create Password screen emphasizes user-only knowledge
3. **BP Capture**: Biometric Enrollment with three-scan process
4. **Transaction Flow**: Processing screen shows all cryptographic steps
5. **HMAC Verification**: Result screen displays F1 = F2 check
6. **Timestamp Usage**: Live T value shown during processing

### Key Differentiators from Existing Systems

- **No reliance on telecom infrastructure** (no SMS/OTP)
- **Multi-factor without phone**: K1 (device) + K2 (password) + BP (biometric)
- **Petty cash focused**: Daily limit for small transactions
- **Bank-assisted security**: Officer involvement in initial setup
- **Cryptographic transparency**: Users see security in action

## Future Enhancements (Beyond Thesis)

The Additional Features screen demonstrates potential extensions:
- Email for notifications (not authentication)
- QR codes for merchant payments
- NFC for contactless terminals
- Card linking for backup funding
- Social login for convenience (not security)

## License & Attribution

Based on the research paper:
**"E-Payment System to Reduce Use of Paper Money for Daily Transactions"**  
Published at ICECTE 2022

---

**Developed as a thesis prototype implementing the paper's cryptographic methodology.**
