# 🚀 Quick Start Guide - E-Banking System

## 5-Minute Setup

### 1. Install & Run Backend
```bash
cd e_banking
pip install -r requirements.txt
python app.py
# ✅ Backend runs on http://localhost:5000
```

### 2. Install & Run Frontend (New Terminal)
```bash
cd e_banking
npm install
npm run dev
# ✅ Frontend opens at http://localhost:5173
```

### 3. Add Demo Users (Optional)
```bash
python seed_supabase.py
```

### 4. Test Login
Use any of these credentials:
- Username: `sohan` | Password: `Sohan_Password_K2_1234567890AB`
- Username: `bob` | Password: `Bob_Password_K2_9876543210CD`
- Username: `alice` | Password: `Alice_Password_K2_ABCDEF123456`

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `app.py` | Flask backend with Supabase integration |
| `crypto.py` | Python cryptographic engine |
| `src/utils/crypto.ts` | Frontend cryptographic engine |
| `src/utils/database.ts` | Supabase REST API calls |
| `src/app/screens/Login.tsx` | Authentication page |
| `src/app/screens/SendMoney.tsx` | Transfer form |
| `supabase_config.py` | Database credentials |

---

## 🔑 Cryptographic Flow

```
Frontend: encryptData({message}, K2, BP, T)
  ↓
  AES-256-CBC encryption with CryptoJS
  ↓
Backend: decryptData(encrypted, K2, BP, T)
  ↓
  Verify HMAC (F1 = F2 check)
  ↓
  Update Supabase accounts & transactions
  ↓
Frontend: Display new_balance and status
```

---

## 🧪 Quick Tests

### Test 1: Login
1. Start both servers
2. Go to http://localhost:5173
3. Enter: sohan / Sohan_Password_K2_1234567890AB
4. Expected: Dashboard shows balance ৳5,000

### Test 2: Transfer
1. From Dashboard → Click "Send Money"
2. Receiver: bob
3. Amount: 500
4. Complete biometric (click approve)
5. Expected: Success page with new balance ৳4,500

### Test 3: Daily Limit
1. Try to send ৳60,000
2. Expected: Error "Exceeds daily petty cash limit"

### Test 4: Invalid Receiver
1. Enter non-existent username
2. Expected: "Receiver not found" message

---

## 🛠️ Common Issues

| Problem | Solution |
|---------|----------|
| Port 5000 in use | Change in app.py or kill existing process |
| Module not found | Run `pip install -r requirements.txt` |
| Receiver not found | Run `python seed_supabase.py` |
| Balance unchanged | Check backend logs for errors |
| CORS error | Verify Flask-CORS is installed |
| Encryption error | Ensure K2, BP, T match between frontend/backend |

---

## 📊 Database Tables

Access at: https://app.supabase.com/

Tables:
- `profiles` - User data with K1, K2, BP, T
- `accounts` - Account balances
- `transactions` - All transaction records
- `merchants_or_billers` - Corporate accounts
- `beneficiaries` - Saved contacts
- `staff_profiles` - Bank staff

---

## 🔐 Security Keys (Demo Users)

**Sohan:**
- K1: Sohan_Secret_Key_K1_123
- K2: Sohan_Password_K2_1234567890AB
- BP: sohan_fingerprint_template_hash_xyz

**Bob:**
- K1: Bob_Secret_Key_K1_456
- K2: Bob_Password_K2_9876543210CD
- BP: bob_fingerprint_template_hash_abc

**Alice:**
- K1: Alice_Secret_Key_K1_789
- K2: Alice_Password_K2_ABCDEF123456
- BP: alice_fingerprint_template_hash_def

---

## 📝 Development Tips

1. **Live Reload Frontend**: Changes auto-refresh during `npm run dev`
2. **Check Backend Logs**: Terminal shows all requests and errors
3. **Database Queries**: Query Supabase via web dashboard
4. **TypeScript Errors**: Run `npm run build` to see all issues
5. **Encryption Tests**: Add `console.log()` in `src/utils/crypto.ts`

---

## 📚 Learn More

- Full guide: `FINAL_INTEGRATION_GUIDE.md`
- Architecture: `README_FULL.md`
- Thesis: `THESIS_DOCUMENTATION.md`

---

## ✅ Checklist

- [ ] Backend installed & running on :5000
- [ ] Frontend installed & running on :5173
- [ ] Demo users seeded to Supabase
- [ ] Can login successfully
- [ ] Can transfer money between users
- [ ] Daily limit enforcement working
- [ ] Receiver validation working
- [ ] Transaction history showing
- [ ] Biometric overlay appearing

---

**Version**: 1.0.0 | **Last Updated**: May 17, 2026
