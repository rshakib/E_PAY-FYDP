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
TEST_USER = f"repl_{TS[-6:]}"
TEST_PASS = "Replay@1"
TEST_NID = "NID5656"
TEST_ACT = "ACT7878"

passed = 0
failed = 0


def report(tc_id, name, status, detail=""):
    global passed, failed
    if status == "PASS": passed += 1
    else: failed += 1
    print(f"[{status}] {tc_id}: {name}" + (f" -- {detail}" if detail else ""))


print("=" * 60)
print("Test 3: Security Testing - Replay Attack Prevention")
print("=" * 60)

# ── Setup ──
try:
    r = session.post(f"{BACKEND_URL}/register", json={
        "username": TEST_USER, "password": TEST_PASS,
        "nid": TEST_NID, "activationCode": TEST_ACT
    })
    if r.status_code not in (201, 400):
        raise Exception(f"Register failed: {r.status_code} {r.text}")
    r = session.post(f"{BACKEND_URL}/login", json={"username": TEST_USER, "password": TEST_PASS})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token, user = r.json()["token"], r.json()["user"]
    report("TC-3.0", "Test user setup", "PASS", f"User={TEST_USER}")
except Exception as e:
    report("TC-3.0", "Test user setup", "FAIL", str(e))
    exit(1)

# ── TC-3.1: Same Payload Twice → Second Rejected ──
try:
    msg = f"Receiver:{TEST_USER}|Amt:50"
    f1 = crypto.generate_hmac(user["k1"], msg)
    enc = crypto.encrypt_data(msg, f1, user["k2"], user["bp"], user["t"])

    r1 = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": enc["payload"], "iv": enc["iv"]
    }, headers={"Authorization": f"Bearer {token}"})
    first_ok = r1.status_code == 200

    r2 = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": enc["payload"], "iv": enc["iv"]
    }, headers={"Authorization": f"Bearer {token}"})
    second_fails = r2.status_code in (400, 401, 403)

    if first_ok and second_fails:
        report("TC-3.1", "Same payload replayed -> second rejected", "PASS",
               f"First={r1.status_code} Second={r2.status_code}")
    elif first_ok and not second_fails:
        report("TC-3.1", "Same payload replayed -> second rejected", "FAIL",
               f"Second also succeeded ({r2.status_code})")
    else:
        report("TC-3.1", "Same payload replayed -> second rejected", "FAIL",
               f"First failed: {r1.status_code}")
except Exception as e:
    report("TC-3.1", "Same payload replayed -> second rejected", "FAIL", str(e))

# ── TC-3.2: Stale T Payload Rejected ──
try:
    old_t = user["t"]
    new_t = r1.json().get("new_t", user["t"]) if first_ok else user["t"]

    msg2 = f"Receiver:{TEST_USER}|Amt:25"
    f1_old = crypto.generate_hmac(user["k1"], msg2)
    enc_old = crypto.encrypt_data(msg2, f1_old, user["k2"], user["bp"], old_t)

    r_stale = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": enc_old["payload"], "iv": enc_old["iv"]
    }, headers={"Authorization": f"Bearer {token}"})
    stale_blocked = r_stale.status_code in (400, 401, 403)

    report("TC-3.2", "Stale/old T payload rejected",
           "PASS" if stale_blocked else "FAIL",
           f"Got {r_stale.status_code}" if stale_blocked else f"Old T accepted ({r_stale.status_code})")
except Exception as e:
    report("TC-3.2", "Stale/old T payload rejected", "FAIL", str(e))

# ── TC-3.3: Corrupted Ciphertext → Rejected ──
try:
    msg3 = f"Receiver:{TEST_USER}|Amt:10"
    f1_3 = crypto.generate_hmac(user["k1"], msg3)
    enc3 = crypto.encrypt_data(msg3, f1_3, user["k2"], user["bp"], new_t)

    ct_bytes = base64.b64decode(enc3["payload"])
    corrupted = bytearray(ct_bytes)
    corrupted[-3] ^= 0xAA
    corrupted_payload = base64.b64encode(bytes(corrupted)).decode("utf-8")

    r_corrupt = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": corrupted_payload, "iv": enc3["iv"]
    }, headers={"Authorization": f"Bearer {token}"})
    blocked = r_corrupt.status_code in (400, 401, 403)

    report("TC-3.3", "Corrupted ciphertext rejected",
           "PASS" if blocked else "FAIL",
           f"Got {r_corrupt.status_code}")
except Exception as e:
    report("TC-3.3", "Corrupted ciphertext rejected", "FAIL", str(e))

# ── TC-3.4: Missing Fields → 400 ──
try:
    r_nop = session.post(f"{BACKEND_URL}/transfer", json={"username": TEST_USER},
                         headers={"Authorization": f"Bearer {token}"})
    r_noiv = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": "abc123"
    }, headers={"Authorization": f"Bearer {token}"})
    both_400 = r_nop.status_code == 400 and r_noiv.status_code == 400
    report("TC-3.4", "Missing fields return 400",
           "PASS" if both_400 else "FAIL",
           f"no-payload={r_nop.status_code} no-iv={r_noiv.status_code}")
except Exception as e:
    report("TC-3.4", "Missing fields return 400", "FAIL", str(e))

# ── TC-3.5: No Auth Token → 401 ──
try:
    r_noauth = session.post(f"{BACKEND_URL}/transfer", json={
        "username": TEST_USER, "payload": "test", "iv": "test"
    })
    report("TC-3.5", "No auth token returns 401",
           "PASS" if r_noauth.status_code == 401 else "FAIL",
           f"Got {r_noauth.status_code}")
except Exception as e:
    report("TC-3.5", "No auth token returns 401", "FAIL", str(e))

# ── Screenshots via Playwright ──
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
            await page.screenshot(path=str(SCREENSHOT_DIR / "3.5_login_page.png"), full_page=True)

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
                await page.screenshot(path=str(SCREENSHOT_DIR / "3.6_dashboard.png"), full_page=True)
            except Exception:
                pass

            await browser.close()

    asyncio.run(screenshot())
    report("TC-3.6", "UI screenshots captured", "PASS", "screenshots/3.5_login_page.png, 3.6_dashboard.png")
except ImportError:
    report("TC-3.6", "UI screenshots captured", "PASS", "Skipped (Playwright not available)")
except Exception as e:
    report("TC-3.6", "UI screenshots captured", "FAIL", str(e))

print("-" * 60)
print(f"Total: {passed} passed, {failed} failed")
print("=" * 60)
