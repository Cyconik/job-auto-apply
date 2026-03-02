"""
auto_applicator.py — v3
✅ Visible browser (tum dekh sakte ho)
✅ Screenshots proof (screenshots/ folder mein save)
✅ Platform-specific apply logic
"""
import time
import random
import os
import tempfile
from datetime import datetime
from pathlib import Path

SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


def apply(job: dict, resume_data: dict, resume_file=None) -> dict:
    if not job.get("url"):
        return _r("failed", "No URL")
    if job.get("_is_demo"):
        return _demo(job)

    platform = job.get("platform","")
    try:
        if platform == "LinkedIn Easy Apply":
            return _linkedin(job, resume_data, resume_file)
        elif platform == "Indeed":
            return _indeed(job, resume_data, resume_file)
        elif platform == "Naukri":
            return _naukri(job, resume_data, resume_file)
        else:  # Remotive and others
            return _open_browser(job)
    except ImportError:
        return _r("pending", f"selenium install karo: pip install selenium webdriver-manager | Manual: {job['url']}")
    except Exception as e:
        return _r("failed", str(e)[:120])


# ── DRIVER SETUP (visible browser) ───────────────────────
def _driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    # VISIBLE MODE — browser window khulega
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        drv = webdriver.Chrome(options=opts)
    except Exception:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

    drv.execute_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    return drv


# ── SCREENSHOT ────────────────────────────────────────────
def _shot(drv, job, stage):
    company = job.get("company","unknown").replace(" ","_")[:15]
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    path    = SCREENSHOT_DIR / f"{stage}_{company}_{ts}.png"
    try:
        drv.save_screenshot(str(path))
        return str(path)
    except Exception:
        return ""


# ── RESUME FILE SAVE ──────────────────────────────────────
def _save_resume(resume_file):
    if not resume_file:
        return ""
    try:
        suffix = ".pdf" if resume_file.name.lower().endswith(".pdf") else ".docx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            resume_file.seek(0)
            f.write(resume_file.read())
            resume_file.seek(0)
            return f.name
    except Exception:
        return ""


# ── LINKEDIN EASY APPLY ───────────────────────────────────
def _linkedin(job, resume_data, resume_file):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    email    = os.environ.get("LINKEDIN_EMAIL","")
    password = os.environ.get("LINKEDIN_PASSWORD","")
    if not email or not password:
        return _r("pending","LINKEDIN_EMAIL / LINKEDIN_PASSWORD config.env mein set karo")

    drv  = _driver()
    wait = WebDriverWait(drv, 20)

    try:
        # Login
        drv.get("https://www.linkedin.com/login")
        wait.until(EC.presence_of_element_located((By.ID,"username"))).send_keys(email)
        drv.find_element(By.ID,"password").send_keys(password)
        drv.find_element(By.CSS_SELECTOR,"button[type='submit']").click()
        time.sleep(3)

        if "checkpoint" in drv.current_url or "challenge" in drv.current_url:
            ss = _shot(drv, job, "linkedin_2fa")
            return _r("pending", f"2FA/Captcha — browser mein manually complete karo. Screenshot: {ss}")

        # Open job
        drv.get(job["url"])
        time.sleep(2)
        _shot(drv, job, "linkedin_before")

        # Easy Apply button
        clicked = False
        for sel in [
            ".jobs-apply-button--top-card button",
            "button.jobs-apply-button",
            "//button[contains(.,'Easy Apply')]",
        ]:
            try:
                if sel.startswith("//"):
                    btn = wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                else:
                    btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                btn.click()
                clicked = True
                time.sleep(1.5)
                break
            except Exception:
                continue

        if not clicked:
            ss = _shot(drv, job, "linkedin_no_btn")
            return _r("failed", f"Easy Apply button nahi mila. Screenshot: {ss}")

        # Multi-step form
        resume_path = _save_resume(resume_file)
        for _ in range(10):
            time.sleep(1.2)

            # Upload resume
            try:
                for fi in drv.find_elements(By.CSS_SELECTOR, "input[type='file']"):
                    if resume_path and fi.is_displayed():
                        fi.send_keys(resume_path)
                        time.sleep(1)
            except Exception:
                pass

            # Fill phone
            try:
                ph = drv.find_element(By.CSS_SELECTOR, "input[id*='phoneNumber'],input[id*='phone']")
                if not ph.get_attribute("value"):
                    ph.send_keys(resume_data.get("phone",""))
            except Exception:
                pass

            # Submit?
            try:
                sub = drv.find_element(By.CSS_SELECTOR,"button[aria-label='Submit application']")
                _shot(drv, job, "linkedin_before_submit")
                sub.click()
                time.sleep(2)
                ss = _shot(drv, job, "linkedin_PROOF")
                return _r("applied", f"✅ LinkedIn Easy Apply submitted! Screenshot: {ss}")
            except Exception:
                pass

            # Next
            for nsel in ["button[aria-label='Continue to next step']",".artdeco-button--primary"]:
                try:
                    btns = drv.find_elements(By.CSS_SELECTOR, nsel)
                    if btns:
                        btns[-1].click()
                        break
                except Exception:
                    pass

        ss = _shot(drv, job, "linkedin_partial")
        return _r("pending", f"Partially filled — browser mein complete karo. Screenshot: {ss}")

    finally:
        time.sleep(1)
        drv.quit()


# ── INDEED ────────────────────────────────────────────────
def _indeed(job, resume_data, resume_file):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    email    = os.environ.get("INDEED_EMAIL","")
    password = os.environ.get("INDEED_PASSWORD","")
    if not email:
        return _r("pending", f"INDEED_EMAIL config.env mein set karo | Manual: {job['url']}")

    drv  = _driver()
    wait = WebDriverWait(drv, 20)

    try:
        drv.get("https://secure.indeed.com/account/login")
        time.sleep(2)
        try:
            wait.until(EC.presence_of_element_located((By.NAME,"emailOrUsername"))).send_keys(email)
            drv.find_element(By.CSS_SELECTOR,"button[type='submit']").click()
            time.sleep(1.5)
            drv.find_element(By.NAME,"password").send_keys(password)
            drv.find_element(By.CSS_SELECTOR,"button[type='submit']").click()
            time.sleep(3)
        except Exception:
            ss = _shot(drv, job, "indeed_login_fail")
            return _r("pending", f"Login issue. Screenshot: {ss}")

        drv.get(job["url"])
        time.sleep(2)
        _shot(drv, job, "indeed_before")

        try:
            btn = wait.until(EC.element_to_be_clickable((By.ID,"indeedApplyButton")))
            btn.click()
            time.sleep(2)
        except Exception:
            try:
                btn = drv.find_element(By.XPATH,"//button[contains(.,'Apply now')]")
                btn.click()
                time.sleep(2)
            except Exception:
                ss = _shot(drv, job, "indeed_no_btn")
                return _r("pending", f"Apply button nahi mila | Manual: {job['url']}. Screenshot: {ss}")

        try:
            rp = _save_resume(resume_file)
            if rp:
                drv.find_element(By.CSS_SELECTOR,"input[type='file']").send_keys(rp)
                time.sleep(2)
        except Exception:
            pass

        try:
            drv.find_element(By.CSS_SELECTOR,"button[type='submit']").click()
            time.sleep(2)
            ss = _shot(drv, job, "indeed_PROOF")
            return _r("applied", f"✅ Indeed submitted! Screenshot: {ss}")
        except Exception:
            ss = _shot(drv, job, "indeed_partial")
            return _r("pending", f"Browser mein submit karo. Screenshot: {ss}")

    finally:
        time.sleep(1)
        drv.quit()


# ── NAUKRI ────────────────────────────────────────────────
def _naukri(job, resume_data, resume_file):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    email    = os.environ.get("NAUKRI_EMAIL","")
    password = os.environ.get("NAUKRI_PASSWORD","")
    if not email:
        return _r("pending","NAUKRI_EMAIL config.env mein set karo")

    drv  = _driver()
    wait = WebDriverWait(drv, 20)

    try:
        drv.get("https://www.naukri.com/nlogin/login")
        time.sleep(3)

        try:
            wait.until(EC.presence_of_element_located((By.ID,"usernameField"))).send_keys(email)
            drv.find_element(By.ID,"passwordField").send_keys(password)
            drv.find_element(By.XPATH,"//button[contains(text(),'Login')]").click()
            time.sleep(3)
        except Exception:
            ss = _shot(drv, job, "naukri_login_fail")
            return _r("pending", f"Login issue. Screenshot: {ss}")

        drv.get(job["url"])
        time.sleep(3)
        _shot(drv, job, "naukri_before")

        try:
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH,"//button[contains(text(),'Apply') or contains(text(),'apply')]")
            ))
            btn.click()
            time.sleep(2)
            ss = _shot(drv, job, "naukri_PROOF")
            return _r("applied", f"✅ Naukri Quick Apply! Screenshot: {ss}")
        except Exception:
            ss = _shot(drv, job, "naukri_no_btn")
            return _r("pending", f"Browser mein apply karo. Screenshot: {ss}")

    finally:
        time.sleep(1)
        drv.quit()


# ── OPEN BROWSER (Remotive/generic) ──────────────────────
def _open_browser(job):
    import webbrowser
    webbrowser.open(job.get("url",""))
    return _r("pending", f"Browser mein khola — manually apply karo: {job['url']}")


# ── DEMO ─────────────────────────────────────────────────
def _demo(job):
    time.sleep(random.uniform(0.5, 1.5))
    co = job.get("company","Company")
    outcomes = [
        ("applied", f"✅ [{co}] Easy Apply submitted (demo mode)"),
        ("applied", f"✅ [{co}] Application sent (demo mode)"),
        ("pending", f"⚠️ [{co}] Redirected to company portal (demo mode)"),
        ("failed",  f"❌ [{co}] Captcha detected — skipped (demo mode)"),
    ]
    s, n = random.choices(outcomes, weights=[0.45, 0.35, 0.12, 0.08])[0]
    return _r(s, n)


def _r(status, note=""):
    return {"status": status, "note": note, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
