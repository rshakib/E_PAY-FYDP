# E-Banking System - Final Integration Guide

## Project Overview

This is a **complete, production-ready e-banking system** with:
- **Frontend**: React 18 + TypeScript with Tailwind CSS & Vite
- **Backend**: Python Flask with Supabase PostgreSQL
- **Database**: Supabase (Secure, scalable cloud PostgreSQL)
- **Security**: AES-256-CBC encryption + HMAC-SHA256 authentication + Biometric verification

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Login → Dashboard → SendMoney → TransactionProcessing │
│  - CryptoJS for AES encryption & HMAC generation         │
│  - Supabase REST API for user data                       │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP/JSON
                 ↓
┌─────────────────────────────────────────────────────────┐
│              Backend (Python Flask)                      │
│  - /transfer endpoint for encrypted transactions         │
│  - /user/<username> for user info                        │
│  - /transactions/<username> for history                  │
│  - Cryptographic verification with pycryptodome          │
└────────────────┬────────────────────────────────────────┘
                 │ Supabase Client
                 ↓
┌─────────────────────────────────────────────────────────┐
│           Supabase PostgreSQL Database                   │
│  - profiles (users with K1, K2, BP, T)                  │
│  - accounts (balances & transactions)                    │
│  - transactions (immutable records)                      │
│  - merchants_or_billers (corporate accounts)             │
│  - beneficiaries (saved contacts)                        │
│  - staff_profiles (bank employees)                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Database Schema

### 1. **profiles** table
- Extends Supabase auth.users
- Stores cryptographic keys (K1, K2, BP, T)
- Daily transaction limits and spending tracking

### 2. **accounts** table
- User account balance records
- Links to profiles (one-to-many)
- Account type: savings/current/business

### 3. **transactions** table
- Immutable transaction records
- Records sender, receiver, amount, status
- Stores failure reasons for debugging

### 4. **merchants_or_billers** table
- Registered corporate accounts
- Utility, transport, education, market types

### 5. **beneficiaries** table
- Saved frequent transfer contacts
- Unique per user

### 6. **staff_profiles** table
- Bank staff and administrative access

---

## 🚀 Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.9+
- npm or yarn
- Supabase account (free tier available)

### Step 1: Backend Setup

```bash
# Navigate to project directory
cd e_banking

# Install Python dependencies
pip install flask flask-cors pycryptodome supabase python-dotenv

# Verify installation
pip list | grep -E "flask|pycryptodome|supabase"
```

### Step 2: Frontend Setup

```bash
# Install npm dependencies
npm install

# Build to check for errors
npm run build

# Verify build success
ls dist/
```

### Step 3: Frontend Environment Variables

Create a `.env` file in the frontend root:

```env
VITE_BACKEND_URL=http://localhost:5000
```

### Step 4: Start the Application

**Terminal 1 - Backend:**
```bash
python app.py
# Server will start on http://localhost:5000
```

**Terminal 2 - Frontend:**
```bash
npm run dev
# App will open at http://localhost:5173
```

---

## 🔐 Security Flow

### Transaction Security Layers

1. **Biometric Verification** (Frontend)
   - Fingerprint overlay before transaction
   - User confirms transaction identity

2. **Message Encryption** (Frontend)
   ```
   Message M = "Receiver:username|Amt:amount"
   F1 = HMAC-SHA256(M, K1)
   AES_Key = SHA256(K2 + BP + T)
   Encrypted = AES-256-CBC({M, F1}, AES_Key)
   ```

3. **Backend Verification**
   ```
   Decrypted {M, F1} = AES-256-CBC(Encrypted, AES_Key)
   F2 = HMAC-SHA256(M, K1)
   if F1 ≠ F2: REJECT (integrity compromised)
   ```

4. **Transaction Execution**
   - Verify sender has sufficient balance
   - Verify receiver exists in database
   - Update balances (atomic operation)
   - Update timestamp T (replay attack prevention)
   - Record transaction immutably

---

## 📁 Project Structure

```
e_banking/
├── Frontend (React + TypeScript)
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx (routing)
│   │   │   ├── screens/
│   │   │   │   ├── Login.tsx (Supabase auth)
│   │   │   │   ├── Dashboard.tsx (user info)
│   │   │   │   ├── SendMoney.tsx (receiver search)
│   │   │   │   ├── TransactionProcessing.tsx (crypto + backend call)
│   │   │   │   ├── TransactionResult.tsx (feedback)
│   │   │   │   └── ...other screens
│   │   │   └── components/
│   │   │       ├── FingerprintOverlay.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Button.tsx
│   │   │       └── ...UI components
│   │   └── utils/
│   │       ├── crypto.ts (CryptoJS encryption/HMAC)
│   │       ├── api.ts (backend API client)
│   │       ├── database.ts (Supabase REST API)
│   │       ├── session.ts (localStorage management)
│   │       └── supabase.ts (Supabase config)
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── Backend (Python Flask)
│   ├── app.py (main Flask application)
│   ├── crypto.py (pycryptodome encryption)
│   ├── supabase_config.py (Supabase credentials)
│   └── requirements.txt (Python dependencies)
│
└── Documentation
    ├── INTEGRATION_GUIDE.md
    ├── README.md
    └── THESIS_DOCUMENTATION.md
```

---

## 🔑 API Endpoints

### `/transfer` (POST)
**Process encrypted money transfer**
```json
Request: {
  "username": "sohan",
  "payload": "base64_encrypted_data"
}

Response (Success): {
  "status": "success",
  "message": "Transfer of 1000 to bob successful",
  "new_t": "2026-05-17T14:30:45Z",
  "new_balance": 4000
}

Response (Error): {
  "status": "error|futile",
  "message": "Decryption failed or insufficient balance"
}
```

### `/user/<username>` (GET)
**Get user profile and account info**
```json
Response: {
  "status": "success",
  "user": {
    "id": "uuid-123",
    "username": "sohan",
    "balance": 5000,
    "daily_limit": 50000,
    "today_spent": 1000
  }
}
```

### `/transactions/<username>` (GET)
**Get transaction history**
```json
Response: {
  "status": "success",
  "transactions": [
    {
      "id": "uuid",
      "amount": 1000,
      "status": "success",
      "created_at": "2026-05-17T14:30:45Z",
      "reference": "TXN-..."
    }
  ]
}
```

---

## 🔐 Cryptographic Details

### Key Derivation
```
K1 = HMAC Secret Key (unique per user)
K2 = Password-based encryption key
BP = Biometric template hash
T = Timestamp (updated after each transaction)
AES_Key = SHA256(K2 + BP + T)
```

### Message Format
```
M = "Receiver:{username}|Amt:{amount}"
F1 = HMAC-SHA256(M, K1)
Plaintext = {M, F1}
Ciphertext = AES-256-CBC(Plaintext, AES_Key) with PKCS7 padding
```

### Verification Process
```
1. Frontend sends {username, base64_encrypted_payload}
2. Backend derives same AES_Key from stored K2, BP, T
3. Backend decrypts to get {M, F1}
4. Backend generates F2 = HMAC-SHA256(M, K1)
5. If F1 = F2: integrity verified ✓
6. If F1 ≠ F2: REJECT transaction ✗
```

---

## 🧪 Testing

### Test Case 1: Successful Transfer
```
User: sohan (Balance: 5000, Limit: 50000)
Receiver: bob
Amount: 1000

Expected:
- sohan balance: 4000
- bob balance: 3000 (received 1000)
- new timestamp T updated
- transaction recorded as 'success'
```

### Test Case 2: Insufficient Balance
```
User: bob (Balance: 2000)
Amount: 3000

Expected:
- Transaction rejected
- Status: 'futile'
- Balances unchanged
- transaction recorded as 'aborted'
```

### Test Case 3: HMAC Mismatch (Tampering)
```
Attacker modifies encrypted payload

Expected:
- Decryption succeeds but F1 ≠ F2
- Transaction rejected
- Status: 'error'
- Message: "Data integrity compromised"
```

### Test Case 4: Invalid Timestamp (Replay)
```
Old transaction encrypted with old T
Replayed after T has been updated

Expected:
- Decryption fails (different T)
- Transaction rejected
- Status: 'error'
```

---

## 🛠️ Development Commands

```bash
# Frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run linter

# Backend
python app.py        # Start Flask server
python -m pytest     # Run tests (when available)

# Database
# Access Supabase dashboard at:
# https://app.supabase.com/
```

---

## 📊 User Flow

```
1. Login Screen
   ├─→ Enter username & password (K2)
   ├─→ Verify against Supabase profiles table
   ├─→ Load K1, BP, T into session
   └─→ Navigate to Dashboard

2. Dashboard
   ├─→ Display balance from accounts table
   ├─→ Show daily limit status
   ├─→ Quick action buttons to Send Money
   └─→ View transaction history

3. SendMoney Screen
   ├─→ Enter receiver username
   ├─→ Search in Supabase profiles table
   ├─→ Enter amount (validate against daily limit)
   └─→ Navigate to TransactionProcessing

4. TransactionProcessing
   ├─→ Show biometric overlay (fingerprint)
   ├─→ On approval: encrypt {M, F1}
   ├─→ Send to backend /transfer endpoint
   ├─→ Receive new_t and new_balance
   ├─→ Update session
   └─→ Navigate to TransactionResult

5. TransactionResult
   ├─→ Show success/failure status
   ├─→ Display transaction details
   ├─→ Show security verification
   └─→ Option to return to Dashboard
```

---

## 🔍 Monitoring & Debugging

### Backend Logs
```bash
# Enable debug mode (already enabled in development)
# Watch for errors in console output
python app.py
```

### Frontend Console
```javascript
// Open browser DevTools (F12)
// Check Console tab for errors
// Network tab shows API calls to /transfer, Supabase
```

### Supabase Logs
```
1. Go to supabase.com dashboard
2. Navigate to project
3. Select "Logs" → "Edge Functions"
4. View real-time API calls
```

---

## 📱 Deployment

### Frontend (Vercel/Netlify)
```bash
npm run build
# Deploy dist/ folder
```

### Backend (Heroku/Railway/Render)
```bash
# Set environment variables
SUPABASE_URL=...
SUPABASE_KEY=...
FLASK_ENV=production

gunicorn app:app
```

### Environment Variables
```
Frontend:
VITE_BACKEND_URL=https://backend-production.com

Backend:
SUPABASE_URL=https://khzndbglgukpdtiwqspc.supabase.co
SUPABASE_KEY=sb_publishable_NU2tIO21EoQQwrOu9MvxVw_skcg9Lq0
FLASK_ENV=production
```

---

## 🎯 Key Features

✅ **Secure Transactions**
- AES-256-CBC encryption
- HMAC-SHA256 authentication
- Timestamp-based replay protection
- Biometric verification

✅ **Database Integration**
- Supabase PostgreSQL
- Row-level security (RLS)
- Immutable transaction records
- Efficient indexing

✅ **User Experience**
- Intuitive React UI
- Real-time receiver search
- Daily limit tracking
- Transaction history

✅ **Production Ready**
- Error handling
- CORS support
- Type safety (TypeScript)
- Responsive design

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend connection refused | Ensure `python app.py` is running on port 5000 |
| Login fails | Check Supabase credentials in `supabase_config.py` |
| Receiver not found | Verify username exists in profiles table |
| Balance not updating | Check Supabase accounts table permissions |
| Encryption errors | Ensure crypto-js and pycryptodome versions match |
| CORS errors | Verify Flask-CORS is installed and enabled |

---

## 📚 Resources

- [Supabase Docs](https://supabase.com/docs)
- [React Docs](https://react.dev)
- [Flask Docs](https://flask.palletsprojects.com)
- [TailwindCSS Docs](https://tailwindcss.com)
- [CryptoJS Docs](https://cryptojs.gitbook.io/docs)
- [PyCryptodome Docs](https://pycryptodome.readthedocs.io)

---

## 📄 License

University FYDP Project - May 2026

---

**Last Updated**: May 17, 2026
**Project Status**: ✅ Complete & Integrated
**Version**: 1.0.0
