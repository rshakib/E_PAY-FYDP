# CODE REVIEW: e-Banking Thesis Project

## What Was This Supposed To Be?

A thesis project demonstrating a "cryptographic OTP-free authentication" e-payment
system. The academic idea: replace SMS OTPs with a 3-factor scheme using K1 (device
HMAC key), K2 (password), BP (biometric hash), and T (timestamp) to prevent replay
attacks. Encrypt messages with AES-CBC, authenticate with HMAC-SHA256. React
frontend, Flask backend, Supabase database. Targets a Bangladesh banking context.

## What Is This Actually?

A half-refactored, security-incoherent prototype with **two parallel codebases**
living side by side — one in `src/`, one in `src/app/` — where neither works
properly, the "secure" crypto scheme leaks every single key to the browser, and
the Supabase admin credentials are sitting in plaintext in a committed `.env`
file. The transaction flow is fully simulated (no actual API calls in the
processing screen), the biometrics are timeouts pretending to be fingerprint
scanners, and the dashboard calculates balances with `3200 - amount`.

---

## The Brutal List

### 1. Supabase Service Role Key Is Hardcoded and Committed

`.env.backend` contains a **Supabase service role key** (`role: service_role`)
with full admin privileges to your database. This key is in the repo. Anyone who
clones this repo can read, write, or delete every row in your Supabase
project. No exceptions, no exaggeration.

Same credentials are also hardcoded in:
- `src/utils/supabase.ts`
- `supabase_config.py`

### 2. Passwords Stored in Plaintext

`app.py:387` writes the user's password directly into the `password_key_k2`
column. No hashing. No bcrypt. No argon2. The login endpoint
(`app.py:126`) does a raw string comparison. If your Supabase data is
breached, every password is immediately readable.

### 3. Every Cryptographic Secret Gets Sent to the Browser

The login endpoint (`app.py:134-148`) returns K1, K2, BP, and T to the
frontend as plain JSON. These are supposed to be the foundation of your
"secure" multi-factor scheme. Instead, they're one XSS away from exfiltration
by any injected script. The entire cryptographic premise is undermined the
moment the secrets leave the server.

### 4. Secrets Stored in localStorage

`src/utils/session.ts` writes K1, K2, BP, and T into `localStorage` as a
JSON-serialized object. Any JavaScript running on the page (including
third-party scripts, compromised dependencies, browser extensions) can read
these. The scheme's security guarantees are theatrical.

### 5. No Authentication on Any API Endpoint

`/user/<username>`, `/transactions/<username>`, `/check-receiver/<username>` —
zero auth. Anyone who knows or guesses a username can fetch their profile,
balance, and full transaction history. The `/transfer` endpoint trusts the
`username` in the request body with no token verification. You could trivially
transfer money from any account if you know the scheme.

### 6. CORS Wide Open

`CORS(app)` with no restrictions. Any website on the internet can make
requests to your backend if a user visits it.

### 7. Passwords Are the Encryption Key

K2 is literally the user's password, used directly in AES key derivation
(`SHA256(K2 + BP + T)`). This means the encryption strength is bounded by
the strength of a user-chosen password. Dictionary words and "password123"
are now your encryption key material. The "AES-256" claim is security
theater when the key is `SHA256("password123" + ...)`.

### 8. Transaction Processing Screen Doesn't Call the API

`TransactionProcessing.tsx` shows a fancy 3-step animation (HMAC, AES,
Transmit) with a fingerprint overlay, but it **never calls the backend**.
It just waits 4.5 seconds and navigates to the result screen with
`status: 'success'`. The entire transaction processing pipeline is a
loading spinner with props.

### 9. Balance Calculated Client-Side With a Hardcoded Number

The transaction result screen does `const newBalance = 3200 - amount`.
3200. Harcoded. The server returns the actual `new_balance`, but it's
ignored. You're not showing the user their real balance — you're doing
arithmetic on a magic number.

### 10. Two Parallel, Duplicate Codebases

There are two complete hierarchies:

| Path | Status |
|------|--------|
| `src/screens/` | Orphaned (old) |
| `src/components/` | Orphaned (old) |
| `src/App.tsx` | Orphaned router |
| `src/app/screens/` | Active (new) |
| `src/app/components/` | Active (new) |
| `src/app/App.tsx` | Active router |

Both sets of screens have the same names with slightly different
implementations. The orphaned ones use `sessionStorage` directly, raw
`fetch('/login')`, and a fake receiver search. The active ones use
`utils/session.ts`, `utils/api.ts`, and actually call `checkReceiver()`.
Maintaining this is a nightmare. Deleting the wrong directory destroys
the app.

### 11. Active Input Component Ignores value/onChange

`src/app/components/Input.tsx` does NOT destructure `value` or `onChange`
from its props. These props fall through to `...rest` and get passed to
the `<input>`, but since they're not handled, the input is effectively
uncontrolled despite receiving `value`. The orphaned version has this
correctly wired.

### 12. Dashboard Has a Flash-of-Empty-State Vulnerability

`Dashboard.tsx` has a `useEffect` that checks for a session and redirects
to `/login`, but the component renders first (the `return null` guard
executes after the initial render). This means users see a flash of empty
dashboard before being redirected.

### 13. Receiver Search in Orphaned SendMoney Is Fake

`src/screens/SendMoney.tsx` sets `receiverFound = true` if the input is
longer than 2 characters. No API call. No real search.

### 14. Mock Data Everywhere

- Dashboard: hardcoded transactions
- Notifications: hardcoded
- MiniStatement: hardcoded
- TransactionResult: `3200 - amount`
- AdditionalFeatures: all simulated
- BiometricEnrollment: setTimeout, no actual fingerprint
- FingerprintOverlay: setTimeout, no actual fingerprint

It's a thesis prototype, so some simulation is acceptable. The problem is
that it's **inconsistent** — some flows try to be real (login, get user,
check receiver) while others are fully fake (transactions, biometrics).
The user experience is a slot machine: sometimes you get real data,
sometimes you get `3200`.

### 15. registerAccount() Exists but Is Never Called

`src/utils/api.ts` exports `registerAccount()` that calls
`POST /register`. The backend has the endpoint. No frontend screen calls
it. The registration flow (ActivationStart -> OfficerVerify ->
BiometricEnrollment -> CreatePassword -> ActivationSuccess) is entirely
frontend-only with no API integration.

### 16. 40+ Unused shadcn UI Components

`src/components/ui/` has 40+ shadcn components (accordion, dialog, form,
chart, etc.). The app uses custom components instead. These bloat the
bundle and exist solely because someone ran `npx shadcn add` on everything.

### 17. Python Cache Files (.pyc) Committed

`__pycache__/` is in the repo. These are compiled bytecode files with no
purpose in version control.

### 18. Package Name Is @figma/my-make-file

`package.json` still has `"name": "@figma/my-make-file"`. This project was
exported from Figma and never renamed. The HTML title says "e-pay". The
directory is `e_banking`. Three names for one project.

### 19. React/react-dom Are Optional Peer Dependencies

In `package.json`, `react` and `react-dom` are listed as **optional** peer
dependencies. A standard `npm install` might not install them. There's a
pnpm overrides section suggesting this was set up for pnpm but ships a
`package-lock.json`.

### 20. No Error Handling for API Failures

Several screens assume API calls will succeed. If Supabase is down, the
network fails, or credentials are wrong, the user gets either a spinner
that never resolves or a cryptic error. The `loginUser` function returns
`{ success: false, error: ... }` but not all callers check it properly.

### 21. No Loading States

`OfficerVerify`, `CreatePassword`, `BiometricEnrollment` — no loading
indicators during submission. The user can click buttons multiple times,
none of the flows have spinners.

### 22. Inconsistent Storage Mechanism

- `src/utils/session.ts` uses `localStorage`
- Orphaned screens use `sessionStorage`
- Both exist, both are used by different parts of the app
- The active `Login.tsx` stores in localStorage, but if the user opens a
  new tab, they're still logged in (no session timeout enforcement
  beyond the timestamp field that nothing actually checks)

### 23. Keys in the Wrong Directory

`SecurityBadge.tsx` lives in `src/components/` but is imported by
`src/app/screens/Dashboard.tsx` as `../components/SecurityBadge`. It
crosses the hierarchy boundary. If someone deletes `src/components/`
thinking it's all orphaned, the active Dashboard breaks.

### 24. Empty CSS Files

`src/styles/fonts.css` and `src/styles/globals.css` exist and are
completely empty. They're imported in `index.css`.

### 25. Redundant Theme File

`Default_shadcn_theme.css` at the root duplicates what's in
`src/styles/theme.css`.

---

## The Thesis Contradiction

The paper claims a "secure, OTP-free authentication scheme using
cryptographic primitives." But the implementation:

1. Stores passwords in plaintext
2. Sends all crypto keys to the browser
3. Stores them in localStorage
4. Never actually calls the crypto on the transaction processing screen
5. Has no real authentication on API endpoints
6. Uses the user's password as the AES key
7. Has a hardcoded balance of 3200

The academic contribution (the 3-factor scheme with K1/K2/BP/T) is
implemented correctly in `crypto.py` and `src/utils/crypto.ts` — AES-CBC
encrypt/decrypt with SHA256 key derivation, HMAC generation/verification.
But the **application security** that wraps it is nonexistent. The crypto
is like a bank vault door installed in a tent.

---

## Summary

**What was tried**: A full-stack e-banking thesis project with
cryptographic authentication.

**What exists**: Two unfinished codebases, one indentity crisis
(Figma-export named @figma/my-make-file), hardcoded keys to your database
in a committed file, no real authentication, fake transaction processing,
and a hardcoded balance of 3200 Taka.

**The most important action**: Revoke the Supabase service role key in
`.env.backend` immediately. It has full admin access to your database and
it's in this repo.
