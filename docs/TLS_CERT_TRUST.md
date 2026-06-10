# TLS Certificate Trust Setup

## Problem

The Flask server uses a **self-signed TLS certificate** (generated during development). Browsers block it by default because it's not signed by a trusted Certificate Authority.

## Solution — Install the Cert as Trusted

### Step 1: Locate the certificate

The cert is pre-generated in the project at:
```
E_PAY/nginx/ssl/selfsigned.crt
E_PAY/nginx/ssl/selfsigned.key
```

### Step 2: Add to Current User's Trusted Root store

```powershell
certutil -addstore -user Root "E_PAY\nginx\ssl\selfsigned.crt"
```

| Part | What it does |
|------|-------------|
| `certutil` | Windows built-in certificate utility |
| `-addstore` | Adds a certificate to a store |
| `-user` | Targets the **current user** store (not machine-wide) |
| `Root` | The **Trusted Root Certification Authorities** store |
| the `.crt` file | The self-signed certificate to import |

This tells Windows: *"Trust this certificate as if it were issued by a known CA."*

### Step 3: (If needed) Add to Local Machine store

Some browsers (Chrome, Edge) also check the **Local Machine** store. This requires administrator privileges:

```powershell
Start-Process -Verb RunAs -FilePath "certutil" -ArgumentList "-addstore","Root","E_PAY\nginx\ssl\selfsigned.crt"
```

Or from an admin PowerShell prompt:
```powershell
certutil -addstore Root "E_PAY\nginx\ssl\selfsigned.crt"
```

### Step 4: Restart your browser

Browsers cache certificate trust at startup. **Close and reopen** the browser for the new trust setting to take effect.

---

## Verify It Worked

```powershell
curl.exe https://localhost:5001/health
```

- **Before trust:** `curl: (60) SEC_E_UNTRUSTED_ROOT` or browser shows "Your connection is not private"
- **After trust:** Returns `{"message": "E-Banking API is running", "status": "ok"}` with no warnings

---

## Why Browsers Block Self-Signed Certs

Browsers only trust certificates signed by a **public Certificate Authority** (Let's Encrypt, DigiCert, etc.). A self-signed cert has no external witness — it's like saying *"I promise I'm me."* Adding it to the Trusted Root store tells the OS: *"I personally vouch for this certificate."*

---

## How to Undo (Remove Trust)

```powershell
# Find the thumbprint
certutil -store -user Root localhost

# Delete from Current User store
certutil -delstore -user Root <thumbprint>

# Delete from Local Machine store (admin)
certutil -delstore Root <thumbprint>
```

---

## Alternative: Run Without TLS

If you don't want to deal with certificates:

```powershell
$env:ENABLE_TLS="0"
python e_banking\app.py
```

The server will start on `http://localhost:5001` with no encryption.
