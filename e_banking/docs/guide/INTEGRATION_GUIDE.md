# Frontend-Backend Integration Guide

## Overview
The frontend has been fully integrated with the Python backend for secure money transfer transactions using cryptographic operations.

## Integration Components

### 1. Utilities Created

#### `src/utils/crypto.ts`
Frontend cryptographic engine that mirrors the Python backend:
- **`generateHmac()`** - Creates F1/F2 using K1 and message via SHA256-HMAC
- **`encryptData()`** - Encrypts M+F1 using AES-256-CBC
- **`decryptData()`** - Decrypts ciphertext to recover M and F1
- **`_deriveAesKey()`** - Derives AES key from K2, BP, and T

#### `src/utils/api.ts`
API client for backend communication:
- **`processTransfer()`** - Sends encrypted transaction to backend
- Handles error responses (insufficient balance, HMAC mismatch, user not found)
- Returns status and new timestamp from backend

#### `src/utils/session.ts`
Session management for storing user credentials:
- **`saveUserSession()`** - Stores user K1, K2, BP, T, username, and balance
- **`getUserSession()`** - Retrieves stored session
- **`updateUserTimestamp()`** - Updates T after successful transaction
- **`updateUserBalance()`** - Updates balance after successful transaction
- **`clearUserSession()`** - Logout functionality

### 2. Updated Screens

#### Login Screen (`src/app/screens/Login.tsx`)
- Demo authentication with credentials:
  - **sohan** / Sohan_Password_K2 (balance: 5000)
  - **bob** / Bob_Password (balance: 2000)
- Stores K1, K2, BP, T in localStorage
- Validates credentials before allowing access

#### Dashboard (`src/app/screens/Dashboard.tsx`)
- Displays logged-in user's username and balance
- Shows daily spending limit indicator
- Logout button redirects to login
- Protected route - redirects to login if no session

#### SendMoney (`src/app/screens/SendMoney.tsx`)
- Collects receiver username and amount
- Validates against daily limit
- Passes data to TransactionProcessing

#### TransactionProcessing (`src/app/screens/TransactionProcessing.tsx`)
- **Biometric Verification** - Shows fingerprint overlay
- **Cryptographic Flow**:
  1. Creates message: `"Receiver:username|Amt:amount"`
  2. Generates F1 = HMAC-SHA256(message, K1)
  3. Encrypts {M, F1} using AES-CBC derived from K2, BP, T
  4. Sends to backend via POST `/transfer`
- **Processing Steps**:
  - Step 1: Message preparation
  - Step 2: HMAC generation & encryption
  - Step 3: Backend verification & execution
- **Response Handling**:
  - Success: Updates timestamp, balance, navigates to result
  - Failure: Maps error to appropriate status (hmac_mismatch, insufficient_balance, etc.)

#### TransactionResult (`src/app/screens/TransactionResult.tsx`)
- Displays transaction status (success/failure)
- Shows security verification badges for successful transactions
- Displays new balance (from backend)
- Different messages for various failure scenarios

### 3. Dependencies Added
```json
{
  "crypto-js": "4.2.0"
}
```

## Security Flow

### Frontend → Backend Transaction

```
User fills form
     ↓
Biometric verification
     ↓
Generate message M = "Receiver:username|Amt:amount"
     ↓
Generate F1 = HMAC-SHA256(M, K1)
     ↓
Derive AES key = SHA256(K2 + BP + T)
     ↓
Encrypt {M, F1} using AES-256-CBC
     ↓
Send {username, encrypted_payload} to backend
     ↓
Backend decrypts, verifies HMAC
     ↓
Backend processes transfer
     ↓
Backend returns new T
     ↓
Frontend updates session and displays result
```

## Backend API Endpoint

### POST `/transfer`
**Request:**
```json
{
  "username": "sohan",
  "payload": "base64_encrypted_data"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Transfer of 1000 to bob successful",
  "new_t": "2026-05-17T14:30:45.123456"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Decryption failed or invalid Timestamp"
}
```

## Running the System

### Start Backend
```bash
cd e_banking/
python app.py
# Server runs on http://localhost:5000
```

### Start Frontend
```bash
npm run dev
# App runs on http://localhost:5173
```

## Demo Users

| Username | Password              | Balance | K1                      | K2                   | BP                         |
|----------|----------------------|---------|------------------------|----------------------|---------------------------|
| sohan    | Sohan_Password_K2    | 5000    | Sohan_Secret_Key_K1_123| Sohan_Password_K2    | Sohan_Fingerprint_Template_XYZ |
| bob      | Bob_Password         | 2000    | Bob_Secret_Key_K1_456  | Bob_Password         | Bob_Fingerprint_Template_ABC   |

## Transaction Flow Example

1. Login as "sohan"
2. Click "Send Money"
3. Enter receiver: "bob", amount: "100"
4. Verify with fingerprint
5. System:
   - Creates: `"Receiver:bob|Amt:100"`
   - Generates F1 with K1
   - Encrypts with K2, BP, current T
   - Sends to backend
6. Backend:
   - Decrypts using K2, BP, T
   - Verifies F1 = F2 (HMAC check)
   - Updates balances
   - Returns new T
7. Frontend:
   - Updates sohan's balance to 4900
   - Updates timestamp T
   - Shows success screen

## Error Handling

The system handles various failure scenarios:

| Error Type | Cause | Frontend Message |
|-----------|-------|-----------------|
| HMAC Mismatch | F1 ≠ F2 | "Data integrity compromised" |
| Insufficient Balance | balance < amount | "Your account balance is insufficient" |
| Receiver Not Found | username doesn't exist | "The receiver username does not exist" |
| Decryption Failed | Invalid K2/BP/T | "Decryption failed or invalid Timestamp" |
| Network Error | Backend unreachable | "Failed to connect to backend server" |

## Notes

- All cryptographic operations match between frontend (CryptoJS) and backend (pycryptodome)
- AES-256-CBC with PKCS7 padding
- HMAC-SHA256 for message authentication
- Timestamps (T) are updated after each successful transaction
- Session data stored in localStorage for demo purposes (use secure storage in production)
- CORS may need configuration for production deployments

## Testing

Test the integration by:
1. Running both backend and frontend
2. Login with demo credentials
3. Attempt transfers to existing users
4. Verify transaction responses and balance updates
5. Check browser console for any errors
6. Monitor backend logs for transaction details
