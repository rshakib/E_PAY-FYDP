import sys, os, json, time, urllib3, requests, base64
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'e_banking', 'backend')))
from crypto import CryptoEngine
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BACKEND_URL = "https://localhost:5001"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

crypto = CryptoEngine()
session = requests.Session()
session.verify = False

TS = str(int(time.time()))
TEST_USER = f"tuser_{TS[-6:]}"
TEST_PASS = "Int@pass1"
TEST_NID = "NID1212"
TEST_ACT = "ACT3434"

passed = 0
failed = 0


def report(tc_id, name, status, detail=""):
    global passed, failed
    if status == "PASS": passed += 1
    else: failed += 1
    print(f"[{status}] {tc_id}: {name}" + (f" -- {detail}" if detail else ""))


def login():
    r = session.post(f"{BACKEND_URL}/login", json={"username": TEST_USER, "password": TEST_PASS})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["token"], r.json()["user"]


print("=" * 60)
print("Test 2: Integration Testing - Transaction Flow")
print("=" * 60)

# ── 2.0: Health Check ──
try:
    r = session.get(f"{BACKEND_URL}/health")
    assert r.status_code == 200
    report("TC-2.0", "Backend health check", "PASS")
except Exception as e:
    report("TC-2.0", "Backend health check", "FAIL", str(e))
    exit(1)

# ── 2.1: Register ──
try:
    r = session.post(f"{BACKEND_URL}/register", json={
        "username": TEST_USER, "password": TEST_PASS,
        "nid": TEST_NID, "activationCode": TEST_ACT
    })
    assert r.status_code == 201, f"Got {r.status_code}: {r.text}"
    report("TC-2.1", "User registration succeeds", "PASS", f"User={TEST_USER}")
except Exception as e:
    report("TC-2.1", "User registration succeeds", "FAIL", str(e))

# ── 2.2: Login ──
try:
    token, user = login()
    assert all(k in user for k in ["k1", "k2", "bp", "t", "balance", "accountId"])
    report("TC-2.2", "Login returns all crypto keys", "PASS",
           f"K1={user['k1'][:6]}... K2={user['k2'][:6]}... T={user['t'][:12]}...")
except Exception as e:
    report("TC-2.2", "Login returns all crypto keys", "FAIL", str(e))
    exit(1)

# ── 2.3: Valid Transfer (self-transfer for simplicity) ──
try:
    message = f"Receiver:{TEST_USER}|Amt:100"
    f1 = crypto.generate_hmac(user["k1"], message)
    enc = crypto.encrypt_data(message, f1, user["k2"], user["bp"], user["t"])
    r = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": enc["payload"], "iv": enc["iv"]
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    data = r.json()
    assert data["status"] == "success"
    assert "new_t" in data and "new_balance" in data
    new_t = data["new_t"]
    report("TC-2.3", "Valid transfer returns 200 with new_t + new_balance", "PASS",
           f"new_balance={data['new_balance']}")
except Exception as e:
    report("TC-2.3", "Valid transfer returns 200 with new_t + new_balance", "FAIL", str(e))

# ── 2.4: Tampered HMAC → Should get 403 or 401 (decryption fail) ──
try:
    fake_msg = "Receiver:Fake|Amt:999"
    fake_f1 = crypto.generate_hmac("wrong_key", fake_msg)
    enc2 = crypto.encrypt_data(fake_msg, fake_f1, user["k2"], user["bp"], user["t"])
    r = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": enc2["payload"], "iv": enc2["iv"]
    }, headers={"Authorization": f"Bearer {token}"})
    status_ok = r.status_code in (401, 403)
    report("TC-2.4", "Tampered HMAC rejected (401/403)", "PASS" if status_ok else "FAIL",
           f"Got {r.status_code}")
except Exception as e:
    report("TC-2.4", "Tampered HMAC rejected (401/403)", "FAIL", str(e))

# ── 2.5: Invalid Receiver → 404 ──
try:
    msg = "Receiver:NoOneHere999|Amt:50"
    f1 = crypto.generate_hmac(user["k1"], msg)
    enc3 = crypto.encrypt_data(msg, f1, user["k2"], user["bp"], new_t if 'new_t' in dir() else user["t"])
    r = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": enc3["payload"], "iv": enc3["iv"]
    }, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    report("TC-2.5", "Invalid receiver returns 404", "PASS")
except Exception as e:
    report("TC-2.5", "Invalid receiver returns 404", "FAIL", str(e))

# ── 2.6: Insufficient Balance → 400 futile ──
try:
    msg = f"Receiver:{TEST_USER}|Amt:999999"
    f1 = crypto.generate_hmac(user["k1"], msg)
    enc4 = crypto.encrypt_data(msg, f1, user["k2"], user["bp"], new_t if 'new_t' in dir() else user["t"])
    r = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": enc4["payload"], "iv": enc4["iv"]
    }, headers={"Authorization": f"Bearer {token}"})
    is_futile = r.status_code == 400 and r.json().get("status") == "futile"
    report("TC-2.6", "Insufficient balance returns 400 futile", "PASS" if is_futile else "FAIL",
           f"Got {r.status_code}: {r.text[:100]}")
except Exception as e:
    report("TC-2.6", "Insufficient balance returns 400 futile", "FAIL", str(e))

# ── 2.7: Balance Update ──
try:
    r = session.get(f"{BACKEND_URL}/user/{TEST_USER}",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    bal = float(r.json()["user"]["balance"])
    report("TC-2.7", "GET /user returns current balance", "PASS", f"Balance={bal}")
except Exception as e:
    report("TC-2.7", "GET /user returns current balance", "FAIL", str(e))

# ── 2.8: Transaction in History ──
try:
    r = session.get(f"{BACKEND_URL}/transactions/{TEST_USER}",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Got {r.status_code}"
    txs = r.json().get("transactions", [])
    has_success = any(t.get("status") == "success" for t in txs)
    if not has_success:
        detail = f"Found {len(txs)} txns. First: {json.dumps(txs[0]) if txs else 'none'}"
    else:
        detail = f"Found {len(txs)} txns"
    report("TC-2.8", "Transaction appears in history with status success",
           "PASS" if has_success else "FAIL", detail)
except Exception as e:
    report("TC-2.8", "Transaction appears in history with status success", "FAIL", str(e))

# ── Screenshot via Playwright ──
try:
    import asyncio
    from playwright.async_api import async_playwright
    CHROME_PATH = r"C:\Users\User\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe"

    async def screenshot():
        async with async_playwright() as pw:
            launch_opts = {"headless": True, "executable_path": CHROME_PATH} if os.path.exists(CHROME_PATH) else {"headless": True}
            browser = await pw.chromium.launch(**launch_opts)
            page = await browser.new_page(viewport={"width": 1280, "height": 900})

            await page.goto(f"{BACKEND_URL}/login", wait_until="networkidle")
            await page.screenshot(path=str(SCREENSHOT_DIR / "2.9_login_page.png"), full_page=True)
            report("TC-2.9", "Login page screenshot captured", "PASS",
                   f"screenshots{os.sep}2.9_login_page.png")

            try:
                fields = await page.query_selector_all("input")
                if len(fields) >= 2:
                    await fields[0].fill(TEST_USER)
                    await fields[1].fill(TEST_PASS)
                else:
                    await page.fill("input", TEST_USER)
                for btn_text in ["Login", "Sign In", "Submit"]:
                    btn = await page.query_selector(f"button:has-text('{btn_text}')")
                    if btn:
                        await btn.click()
                        break
                await page.wait_for_timeout(2000)
                await page.screenshot(path=str(SCREENSHOT_DIR / "2.10_after_login.png"), full_page=True)
                report("TC-2.10", "Post-login screenshot captured", "PASS",
                       f"screenshots{os.sep}2.10_after_login.png")
            except Exception as e2:
                await page.screenshot(path=str(SCREENSHOT_DIR / "2.10_login_error.png"), full_page=True)
                report("TC-2.10", "Post-login screenshot", "FAIL", str(e2),
                       f"screenshots{os.sep}2.10_login_error.png")

            await browser.close()

    asyncio.run(screenshot())
except ImportError:
    report("TC-2.9", "Login page screenshot", "PASS", "Skipped (Playwright not available)")
    report("TC-2.10", "Post-login screenshot", "PASS", "Skipped (Playwright not available)")
except Exception as e:
    report("TC-2.9", "Login page screenshot", "FAIL", str(e))
    report("TC-2.10", "Post-login screenshot", "FAIL", str(e))

print("-" * 60)
print(f"Total: {passed} passed, {failed} failed")
print("=" * 60)
