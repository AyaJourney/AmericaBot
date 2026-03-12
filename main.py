# -*- coding: utf-8 -*-
import sys
import io
# Windows encoding fix - emoji ve turkce karakter sorunu cozumu
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse
import time
import requests
import traceback
import os
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager

# =====================================================
# ARG PARSE
# =====================================================
parser = argparse.ArgumentParser()
parser.add_argument("--bot-id", type=int, default=1, help="Bot instance ID (1,2,3...)")
args   = parser.parse_args()
BOT_ID = args.bot_id

print(f"[BOT-{BOT_ID}] Baslatildi")

# =====================================================
# CONFIG
# =====================================================
CRM_BASE = "http://localhost:3000/api/internal"

QUEUE_URL               = f"{CRM_BASE}/queue/ds160/start"
STATUS_URL              = f"{CRM_BASE}/job/status"
CAPTCHA_POLL_URL        = f"{CRM_BASE}/job/captcha"
CAPTCHA_REFRESH_ACK_URL = f"{CRM_BASE}/job/captcha/refresh/ack"

POLL_INTERVAL             = 3
SELENIUM_PAGELOAD_TIMEOUT = 120

# =====================================================
# CRM HELPERS
# =====================================================
def update_job_status(job_id: str, status: str, extra: dict | None = None):
    payload = {"job_id": job_id, "status": status}
    if extra:
        payload.update(extra)
    try:
        r = requests.post(STATUS_URL, json=payload, timeout=10)
        print(f"[BOT-{BOT_ID}] STATUS -> {status} ({r.status_code})")
    except Exception as e:
        print(f"[BOT-{BOT_ID}] Status update error: {e}")


def fetch_ds160_job():
    try:
        print(f"[BOT-{BOT_ID}] Queue kontrol ediliyor...")
        res = requests.get(QUEUE_URL, timeout=15)
        if res.status_code == 204:
            return None
        if res.status_code != 200:
            print(f"[BOT-{BOT_ID}] Queue error: {res.status_code} {res.text}")
            return None
        return res.json()
    except Exception as e:
        print(f"[BOT-{BOT_ID}] CRM baglanti hatasi: {e}")
        return None


def poll_captcha_state(job_id: str):
    try:
        res = requests.get(f"{CAPTCHA_POLL_URL}?job_id={job_id}", timeout=10)
        if res.status_code != 200:
            print(f"[BOT-{BOT_ID}] captcha poll status={res.status_code}")
            return None
        return res.json()
    except Exception as e:
        print(f"[BOT-{BOT_ID}] captcha poll error: {e}")
        return None


def ack_captcha_refresh(job_id: str):
    try:
        res = requests.post(CAPTCHA_REFRESH_ACK_URL, json={"job_id": job_id}, timeout=10)
        print(f"[BOT-{BOT_ID}] refresh ack -> {res.status_code}")
    except Exception as e:
        print(f"[BOT-{BOT_ID}] refresh ack error: {e}")


# =====================================================
# SELENIUM HELPERS
# =====================================================
def wait_clickable_safe(wait: WebDriverWait, by, value, retries=6):
    last_exc = None
    for _ in range(retries):
        try:
            return wait.until(EC.element_to_be_clickable((by, value)))
        except StaleElementReferenceException as e:
            last_exc = e
            time.sleep(0.15)
    if last_exc:
        raise last_exc
    raise RuntimeError("Element not clickable (stale too many times)")


def wait_document_ready(driver, timeout=60):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def get_captcha_image_base64(driver) -> str:
    captcha_img = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "img.LBD_CaptchaImage"))
    )
    return captcha_img.screenshot_as_base64


from selenium.common.exceptions import NoSuchElementException

def refresh_captcha_and_get_base64(driver, total_timeout=10):
    wait = WebDriverWait(driver, 5)
    reload_icon = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "img.LBD_ReloadIcon"))
    )
    reload_icon.click()
    print(f"[BOT-{BOT_ID}] CAPTCHA reload tiklandi")

    end_time = time.time() + total_timeout
    while time.time() < end_time:
        try:
            captcha_img = driver.find_element(By.CSS_SELECTOR, "img.LBD_CaptchaImage")
            b64 = captcha_img.screenshot_as_base64
            if b64:
                print(f"[BOT-{BOT_ID}] CAPTCHA screenshot alindi")
                return b64
        except (NoSuchElementException, StaleElementReferenceException):
            time.sleep(0.4)

    try:
        captcha_img = wait.until(EC.presence_of_element_located(
            (By.ID, "c_default_ctl00_sitecontentplaceholder_uclocation_identifycaptcha1_defaultcaptcha_CaptchaImage")
        ))
        print(f"[BOT-{BOT_ID}] CAPTCHA screenshot alindi (son deneme)")
        return captcha_img.screenshot_as_base64
    except Exception:
        print(f"[BOT-{BOT_ID}] CAPTCHA alinamadi ama bot devam ediyor")
        return None


def send_captcha_to_crm(job_id: str, captcha_b64: str, refreshed: bool):
    update_job_status(
        job_id,
        "waiting_captcha",
        {
            "captcha_image_base64": f"data:image/png;base64,{captcha_b64}",
            "refreshed": bool(refreshed),
        },
    )
    print(f"[BOT-{BOT_ID}] CAPTCHA gonderildi" + (" (REFRESH)" if refreshed else ""))


def read_refresh_flag(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("refresh") or payload.get("captcha_refresh"))


# =====================================================
# CHROME — her bot ayri profil + user-agent
# =====================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

def make_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Windows uyumlu ayri Chrome profili
    chrome_profile = os.path.join(os.path.expanduser("~"), f"chrome-bot-{BOT_ID}")
    options.add_argument(f"--user-data-dir={chrome_profile}")
    print(f"[BOT-{BOT_ID}] Chrome profil: {chrome_profile}")

    # Her bot farkli user-agent
    ua = USER_AGENTS[(BOT_ID - 1) % len(USER_AGENTS)]
    options.add_argument(f"--user-agent={ua}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_page_load_timeout(SELENIUM_PAGELOAD_TIMEOUT)

    # navigator.webdriver gizle
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return driver


# =====================================================
# DS-160 FLOW
# =====================================================
def run_ds160_until_captcha(job: dict):
    job_id = job["job_id"]
    data   = job.get("data", {}) or {}

    barcode_from_crm = data.get("BARCODE")
    IS_RETRIEVE      = bool(barcode_from_crm)
    LOCATION         = data.get("LOCATION", "ANK")

    print(f"[BOT-{BOT_ID}] JOB: {job_id}")
    print(f"[BOT-{BOT_ID}] MODE: {'RETRIEVE' if IS_RETRIEVE else 'NEW'}")
    print(f"[BOT-{BOT_ID}] LOCATION: {LOCATION}")

    update_job_status(job_id, "processing")

    driver = make_driver()
    wait   = WebDriverWait(driver, 120)

    try:
        # 1. SITE
        driver.get("https://ceac.state.gov/GenNIV/Default.aspx")
        wait_document_ready(driver, 90)

        # 2. LOCATION (sadece NEW)
        if not IS_RETRIEVE:
            print(f"[BOT-{BOT_ID}] Location seciliyor")
            location_select = wait_clickable_safe(
                wait, By.ID, "ctl00_SiteContentPlaceHolder_ucLocation_ddlLocation"
            )
            old_viewstate = driver.find_element(By.ID, "__VIEWSTATE").get_attribute("value")
            Select(location_select).select_by_value(LOCATION)
            WebDriverWait(driver, 60).until(
                lambda d: d.find_element(By.ID, "__VIEWSTATE").get_attribute("value") != old_viewstate
            )
            wait_document_ready(driver, 60)
        else:
            print(f"[BOT-{BOT_ID}] Retrieve mode -> location atlandi")

        # 3. CAPTCHA GONDER
        captcha_b64 = get_captcha_image_base64(driver)
        send_captcha_to_crm(job_id, captcha_b64, refreshed=False)
        print(f"[BOT-{BOT_ID}] CAPTCHA bekleniyor...")

        refresh_count = 0
        while True:
            time.sleep(POLL_INTERVAL)
            payload = poll_captcha_state(job_id)
            if not payload:
                continue
            answer = payload.get("captcha_answer")
            if answer:
                captcha_value = str(answer).strip()
                break
            if read_refresh_flag(payload):
                refresh_count += 1
                if refresh_count > 20:
                    raise RuntimeError("Captcha refresh limit asildi")
                new_b64 = refresh_captcha_and_get_base64(driver)
                if new_b64:
                    send_captcha_to_crm(job_id, new_b64, refreshed=True)
                ack_captcha_refresh(job_id)

        # 4. CAPTCHA INPUT
        captcha_input = wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_ucLocation_IdentifyCaptcha1_txtCodeTextBox")
        ))
        captcha_input.clear()
        captcha_input.send_keys(captcha_value)
        update_job_status(job_id, "captcha_verified")

        # 5. NEW / RETRIEVE
        if IS_RETRIEVE:
            print(f"[BOT-{BOT_ID}] Retrieve akisi")
            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_lnkRetrieve")
            )).click()

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_tbxApplicationID")
            )).send_keys(barcode_from_crm)

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_btnBarcodeSubmit")
            )).click()

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_txbSurname")
            )).send_keys(data["SURNAME"][:5].upper())

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_txbDOBYear")
            )).send_keys(data["BIRTH_YEAR"])

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_txbAnswer")
            )).send_keys(barcode_from_crm)

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_btnRetrieve")
            )).click()
            print(f"[BOT-{BOT_ID}] Retrieve bitti")

        else:
            print(f"[BOT-{BOT_ID}] New Application")
            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_lnkNew")
            )).click()

        wait_document_ready(driver, 90)

        # 6. BARCODE + PRIVACY
        barcode_from_crm = data.get("BARCODE")
        IS_RETRIEVE      = bool(barcode_from_crm)
        barcode_value    = None

        if IS_RETRIEVE:
            barcode_value = barcode_from_crm
            print(f"[BOT-{BOT_ID}] Retrieve mode -> barcode: {barcode_value}")
        else:
            barcode_label = wait.until(EC.visibility_of_element_located(
                (By.ID, "ctl00_SiteContentPlaceHolder_lblBarcode")
            ))
            barcode_value = barcode_label.text.strip()
            if not barcode_value:
                raise RuntimeError("Barcode bos geldi")
            print(f"[BOT-{BOT_ID}] New application -> barcode: {barcode_value}")

            privacy_cb = wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_chkbxPrivacyAct")
            ))
            if not privacy_cb.is_selected():
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", privacy_cb)
                time.sleep(0.2)
                privacy_cb.click()

            answer_input = wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_txtAnswer")
            ))
            answer_input.clear()
            answer_input.send_keys(barcode_value)

            continue_btn = wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_btnContinue")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", continue_btn)
            time.sleep(0.2)
            continue_btn.click()

            wait.until(EC.presence_of_element_located((By.ID, "Personal")))
            print(f"[BOT-{BOT_ID}] Form menusune girildi")

        if not barcode_value:
            raise RuntimeError("barcode_value set edilmedi")

        update_job_status(job_id, "barcode_received", {"barcode": barcode_value})

        if IS_RETRIEVE:
            handle_privacy_and_continue(wait, driver)
            clear_personal_1_form(wait, driver)

        # 7. BARCODE CRM'E BILDIR
        try:
            r = requests.post(
                f"{CRM_BASE}/job/barcode",
                json={"job_id": job_id, "barcode": barcode_value},
                timeout=10,
            )
            print(f"[BOT-{BOT_ID}] CRM barcode bildirildi: {r.status_code}")
        except Exception as e:
            print(f"[BOT-{BOT_ID}] CRM barcode bildirimi basarisiz: {e}")

        update_job_status(job_id, "entered_form")

        # 8. FORM DOLDUR
        if IS_RETRIEVE:
            print(f"[BOT-{BOT_ID}] RESUME FLOW baslatiliyor...")
            from ds160_resume_flow import fill_ds160_resume_application
            fill_ds160_resume_application(driver, wait, data)
        else:
            print(f"[BOT-{BOT_ID}] FULL FLOW baslatiliyor...")
            from ds160_full_flow import fill_ds160_full_application
            fill_ds160_full_application(driver, wait, data)

        update_job_status(job_id, "completed")

    except Exception as e:
        update_job_status(job_id, "failed", {"error": str(e)})
        traceback.print_exc()

    finally:
        driver.quit()


# =====================================================
# HELPERS
# =====================================================
def force_clear_input(wait, driver, input_id):
    el = wait.until(EC.presence_of_element_located((By.ID, input_id)))
    driver.execute_script("arguments[0].removeAttribute('disabled');", el)
    el.clear()
    time.sleep(0.1)


def clear_personal_1_form(wait, driver):
    print(f"[BOT-{BOT_ID}] Personal 1 temizleniyor")
    for field_id in [
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SURNAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_GIVEN_NAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_FULL_NAME_NATIVE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxDOBYear",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_POB_CITY",
    ]:
        force_clear_input(wait, driver, field_id)
    print(f"[BOT-{BOT_ID}] Personal 1 sifirlandı")


def handle_privacy_and_continue(wait, driver):
    print(f"[BOT-{BOT_ID}] Personal 1'e geciliyor")
    for attempt in range(5):
        try:
            personal1_link = wait.until(
                EC.presence_of_element_located((By.ID, "Personal"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", personal1_link)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", personal1_link)
            wait.until(EC.presence_of_element_located(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_lblAPP_SURNAME")
            ))
            print(f"[BOT-{BOT_ID}] Personal 1'e gecildi")
            break
        except (StaleElementReferenceException, TimeoutException):
            print(f"[BOT-{BOT_ID}] retry {attempt+1}/5")
            time.sleep(0.5)
    else:
        raise RuntimeError("Personal 1'e gecilemedi")

    wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_lblAPP_SURNAME")
    ))
    print(f"[BOT-{BOT_ID}] Personal 1 hazir")


# =====================================================
# DAEMON
# =====================================================
if __name__ == "__main__":
    print(f"[BOT-{BOT_ID}] DS-160 BOT BASLADI (SUREKLI CALISIR)")

    while True:
        job = fetch_ds160_job()
        if not job:
            time.sleep(POLL_INTERVAL)
            continue
        try:
            run_ds160_until_captcha(job)
        except Exception as e:
            print(f"[BOT-{BOT_ID}] JOB crash: {e}")
            time.sleep(5)