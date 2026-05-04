# -*- coding: utf-8 -*-
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import sys
import io
import argparse
import time
import requests
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager
from cleaner import clean_all

# =====================================================
# ARG PARSE
# =====================================================
parser = argparse.ArgumentParser()
parser.add_argument("--bot-id", type=int, default=1, help="Bot instance ID (1,2,3...)")
args   = parser.parse_args()
BOT_ID = args.bot_id

print(f"[BOT-{BOT_ID}] Baslatildi")
PHOTO_DIR = r"C:\Users/1275/Desktop/AMERICA BOT/america\photos"
# =====================================================
# CONFIG
# =====================================================
CRM_BASE = "https://crm.ayajourney.com/api/internal"

QUEUE_URL               = f"{CRM_BASE}/queue/ds160/start"
STATUS_URL              = f"{CRM_BASE}/job/status"
CAPTCHA_POLL_URL        = f"{CRM_BASE}/job/captcha"
CAPTCHA_REFRESH_ACK_URL = f"{CRM_BASE}/job/captcha/refresh/ack"

POLL_INTERVAL             = 3
SELENIUM_PAGELOAD_TIMEOUT = 120

# =====================================================
# DATA FLATTEN
# =====================================================
def flatten_job_data(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    if "raw_data" in data and isinstance(data["raw_data"], dict):
        for k, v in data["raw_data"].items():
            if k not in data or not data[k]:
                data[k] = v
    return data


def get_field(data: dict, key: str, default: str = "") -> str:
    val = data.get(key)
    if val:
        return str(val)
    val = data.get("raw_data", {}).get(key) if isinstance(data.get("raw_data"), dict) else None
    if val:
        return str(val)
    return default


# =====================================================
# CRM HELPERS
# =====================================================
def update_job_status(job_id: str, status: str, extra: dict | None = None):
    payload = {"job_id": job_id, "status": status}
    if extra:
        payload.update(extra)
    has_screenshot = bool(extra and extra.get("page_screenshot"))
    timeout = 60 if has_screenshot else 10
    try:
        r = requests.post(STATUS_URL, json=payload, timeout=timeout)
        print(f"[BOT-{BOT_ID}] STATUS -> {status} ({r.status_code})")
        if r.status_code != 200:
            print(f"[BOT-{BOT_ID}] STATUS ERROR: {r.text[:200]}")
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


def poll_job_status(job_id: str):
    try:
        res = requests.get(f"{CRM_BASE}/job/status?job_id={job_id}", timeout=10)
        if res.status_code != 200:
            return None
        return res.json()
    except Exception as e:
        print(f"[BOT-{BOT_ID}] poll_job_status error: {e}")
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
# SCREENSHOT HELPER
# =====================================================
def take_and_send_screenshot(driver, job_id: str):
    page_b64 = None
    try:
        rect = driver.execute_script("""
            var el = document.getElementById('content-main');
            if (!el) el = document.getElementById('content');
            if (!el) return null;
            var r = el.getBoundingClientRect();
            return { x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: el.scrollHeight }
        """)
        if rect:
            clip_x = max(0, int(rect["x"]))
            clip_y = max(0, int(rect["y"]))
            clip_w = int(rect["w"])
            clip_h = min(int(rect["h"]), 8000)
        else:
            clip_x, clip_y, clip_w, clip_h = 0, 0, 900, 4000

        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width": clip_x + clip_w + 20,
            "height": clip_y + clip_h + 20,
            "deviceScaleFactor": 1.5,
            "mobile": False,
        })
        time.sleep(0.5)
        result = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "clip": {
                "x": clip_x, "y": clip_y,
                "width": clip_w, "height": clip_h,
                "scale": 1.5,
            },
            "captureBeyondViewport": True,
        })
        page_b64 = result.get("data")
        driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
        print(f"[BOT-{BOT_ID}] Screenshot boyutu: {len(page_b64) if page_b64 else 0} chars")
    except Exception as ss_err:
        print(f"[BOT-{BOT_ID}] CDP screenshot hatasi: {ss_err}, fallback deneniyor...")
        try:
            page_b64 = driver.get_screenshot_as_base64()
            print(f"[BOT-{BOT_ID}] Fallback screenshot boyutu: {len(page_b64) if page_b64 else 0} chars")
        except Exception as ss_err2:
            print(f"[BOT-{BOT_ID}] Screenshot tamamen basarisiz: {ss_err2}")

    try:
        r2 = requests.post(
            f"{CRM_BASE}/job/screenshot",
            json={
                "job_id": job_id,
                "page_screenshot": f"data:image/png;base64,{page_b64}" if page_b64 else None
            },
            timeout=60
        )
        print(f"[BOT-{BOT_ID}] Screenshot gonderildi: {r2.status_code}")
    except Exception as se:
        print(f"[BOT-{BOT_ID}] Screenshot gonderi hatasi: {se}")


# =====================================================
# WAITING CLOSE LOOP
# =====================================================
def wait_for_close_command(driver, job_id: str):
    update_job_status(job_id, "waiting_close")
    print(f"[BOT-{BOT_ID}] Waiting close - kullanici onay bekleniyor...")
    while True:
        time.sleep(POLL_INTERVAL)
        payload = poll_captcha_state(job_id)
        if not payload:
            continue
        job_status = payload.get("status")
        print(f"[BOT-{BOT_ID}] waiting_close poll: {job_status}")
        if job_status == "close":
            print(f"[BOT-{BOT_ID}] Kapat komutu alindi, bot kapatiliyor...")
            try:
                driver.quit()
            except Exception:
                pass
            return
        if payload.get("close_ack") or job_status == "close_ack":
            print(f"[BOT-{BOT_ID}] close_ack alindi, devam ediliyor...")
            break


# =====================================================
# CHROME
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

    chrome_profile = os.path.join(os.path.expanduser("~"), f"chrome-bot-{BOT_ID}")
    options.add_argument(f"--user-data-dir={chrome_profile}")
    print(f"[BOT-{BOT_ID}] Chrome profil: {chrome_profile}")

    ua = USER_AGENTS[(BOT_ID - 1) % len(USER_AGENTS)]
    options.add_argument(f"--user-agent={ua}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_page_load_timeout(SELENIUM_PAGELOAD_TIMEOUT)

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

    # 1. Ham veriyi düzleştir
    data = flatten_job_data(data)

    # 2. Temizle — Türkçe karakter, tarih, okul/şirket isimleri
    try:
        data = clean_all(data)
        print(f"[BOT-{BOT_ID}] Veri temizlendi ({len(data)} alan)")
    except Exception as e:
        print(f"[BOT-{BOT_ID}] clean_all hatasi (devam ediliyor): {e}")

    barcode_from_crm = data.get("BARCODE") or ""
    IS_RETRIEVE      = bool(barcode_from_crm.strip())
    LOCATION         = data.get("LOCATION", "ANK")

    print(f"[BOT-{BOT_ID}] JOB: {job_id}")
    print(f"[BOT-{BOT_ID}] MODE: {'RETRIEVE' if IS_RETRIEVE else 'NEW'}")
    print(f"[BOT-{BOT_ID}] LOCATION: {LOCATION}")
    print(f"[BOT-{BOT_ID}] SURNAME: {get_field(data, 'SURNAME', '???')}")

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

        # 4. CAPTCHA INPUT + RETRY LOOP
        captcha_attempts = 0
        while True:
            captcha_attempts += 1
            if captcha_attempts > 10:
                raise RuntimeError("Captcha max deneme asildi (10)")

            captcha_input = wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ucLocation_IdentifyCaptcha1_txtCodeTextBox")
            ))
            captcha_input.clear()
            captcha_input.send_keys(captcha_value)

            if IS_RETRIEVE:
                print(f"[BOT-{BOT_ID}] Retrieve akisi (deneme {captcha_attempts})")
                wait.until(EC.element_to_be_clickable(
                    (By.ID, "ctl00_SiteContentPlaceHolder_lnkRetrieve")
                )).click()
            else:
                print(f"[BOT-{BOT_ID}] New Application (deneme {captcha_attempts})")
                wait.until(EC.element_to_be_clickable(
                    (By.ID, "ctl00_SiteContentPlaceHolder_lnkNew")
                )).click()

            time.sleep(2)
            wait_document_ready(driver, 15)

            captcha_error = False
            try:
                err_el = driver.find_element(
                    By.ID, "ctl00_SiteContentPlaceHolder_ucLocation_IdentifyCaptcha1_ValidationSummary"
                )
                if err_el.is_displayed() and err_el.text.strip():
                    captcha_error = True
                    print(f"[BOT-{BOT_ID}] Captcha hatali: {err_el.text.strip()}")
            except Exception:
                pass

            if not captcha_error:
                print(f"[BOT-{BOT_ID}] Captcha gecti (deneme {captcha_attempts})")
                break

            print(f"[BOT-{BOT_ID}] Yeni captcha aliniyor...")
            new_b64 = refresh_captcha_and_get_base64(driver)
            if new_b64:
                send_captcha_to_crm(job_id, new_b64, refreshed=True)
                update_job_status(job_id, "captcha_refresh")

            print(f"[BOT-{BOT_ID}] Yeni captcha cevabi bekleniyor...")
            time.sleep(3)
            while True:
                time.sleep(POLL_INTERVAL)
                payload = poll_captcha_state(job_id)
                if not payload:
                    continue
                answer = payload.get("captcha_answer")
                if answer and str(answer).strip():
                    captcha_value = str(answer).strip()
                    print(f"[BOT-{BOT_ID}] Yeni captcha cevabi alindi")
                    break

        update_job_status(job_id, "captcha_verified")

        # 5. RETRIEVE AKISI
        if IS_RETRIEVE:
            surname    = get_field(data, "SURNAME", "XXXXX")[:5].upper()
            birth_year = get_field(data, "BIRTH_YEAR", "1990")

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_tbxApplicationID")
            )).send_keys(barcode_from_crm)

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_btnBarcodeSubmit")
            )).click()

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_txbSurname")
            )).send_keys(surname)

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_txbDOBYear")
            )).send_keys(birth_year)

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_txbAnswer")
            )).send_keys(barcode_from_crm)

            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_btnRetrieve")
            )).click()
            print(f"[BOT-{BOT_ID}] Retrieve bitti")
            wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_ApplicationRecovery1_btnRetrieve")
        )).click()
        print(f"[BOT-{BOT_ID}] Retrieve bitti")

        # ── Sayfa tam yüklenene kadar bekle ──
        time.sleep(3)
        wait_document_ready(driver, 60)
        time.sleep(2)
        print(f"[BOT-{BOT_ID}] Retrieve sonrası URL: {driver.current_url}")
        wait_document_ready(driver, 90)

        # 6. BARCODE + PRIVACY
        barcode_value = None

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

        # 7. BARCODE CRM'E BILDIR
        update_job_status(job_id, "barcode_received", {"barcode": barcode_value})
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

        # 8. RETRIEVE ISE: Privacy + Personal1'e gec
        if IS_RETRIEVE:
            handle_privacy_and_continue(wait, driver)
            clear_personal_1_form(wait, driver)

        # 9. FORM DOLDUR — HER ZAMAN FULL FLOW
        print(f"[BOT-{BOT_ID}] FULL FLOW baslatiliyor...")
        from ds160_full_flow import fill_ds160_full_application

        def on_personal1_saved():
            print(f"[BOT-{BOT_ID}] Personal 1 kaydedildi, screenshot aliniyor...")
            take_and_send_screenshot(driver, job_id)

        def on_photo_page():
            print(f"[BOT-{BOT_ID}] Fotoğraf sayfasına gelindi")

            import urllib.request

            PHOTO_DIR = os.path.join(
                os.path.expanduser("~"),
                "OneDrive", "Desktop", "amerika bot", "AmericaBot", "photos"
            )
            os.makedirs(PHOTO_DIR, exist_ok=True)
            print(f"[BOT-{BOT_ID}] Fotoğraf klasörü: {PHOTO_DIR}")

            photo_path = None
            tmp_path   = None

            try:
                # ── Fotoğrafı bul / indir ────────────────────────────
                photo_url = data.get("PHOTO_URL") or data.get("photo_url") or ""
                print(f"[BOT-{BOT_ID}] PHOTO_URL: '{photo_url[:80] if photo_url else 'BOŞ'}'")

                if photo_url and photo_url.startswith("http"):
                    tmp_path = os.path.join(PHOTO_DIR, f"ds160_photo_{BOT_ID}.jpg")
                    print(f"[BOT-{BOT_ID}] 📥 İndiriliyor → {tmp_path}")
                    urllib.request.urlretrieve(photo_url, tmp_path)
                    size = os.path.getsize(tmp_path)
                    print(f"[BOT-{BOT_ID}] ✅ İndirildi: {size} bytes")
                    if size > 1000:
                        photo_path = tmp_path
                    else:
                        print(f"[BOT-{BOT_ID}] ⚠️ Dosya çok küçük, geçersiz")
                        os.unlink(tmp_path)
                        tmp_path = None

                if not photo_path:
                    from form_fill import _find_best_photo
                    full_name = data.get("FULL_NAME") or \
                        f"{data.get('GIVEN_NAME', '')} {data.get('SURNAME', '')}".strip()
                    print(f"[BOT-{BOT_ID}] Klasörde aranıyor: '{full_name}'")
                    fname, score = _find_best_photo(PHOTO_DIR, full_name)
                    print(f"[BOT-{BOT_ID}] Arama sonucu: fname={fname} score={score:.2f}")
                    if fname and score >= 0.70:
                        photo_path = os.path.join(PHOTO_DIR, fname)

                if not photo_path:
                    raise Exception(
                        f"Fotoğraf bulunamadı — PHOTO_URL boş ve klasörde eşleşme yok. "
                        f"Fotoğrafı {PHOTO_DIR} klasörüne koy."
                    )

                print(f"[BOT-{BOT_ID}] 📸 Kullanılacak fotoğraf: {photo_path}")

                # ── ADIM 1: Upload Photo butonuna tıkla ─────────────
                upload_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_SiteContentPlaceHolder_btnUploadPhoto")
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", upload_btn
                )
                upload_btn.click()
                print(f"[BOT-{BOT_ID}] ✅ Upload Photo tıklandı")
                time.sleep(3)
                wait_document_ready(driver, 30)
                print(f"[BOT-{BOT_ID}] Upload sayfası URL: {driver.current_url}")

                # ── ADIM 2: File input'a dosyayı gönder ─────────────
                # id = ctl00_cphMain_imageFileUpload
                file_input = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.ID, "ctl00_cphMain_imageFileUpload")
                    )
                )
                driver.execute_script("""
                    arguments[0].removeAttribute('disabled');
                    arguments[0].style.display      = 'block';
                    arguments[0].style.visibility   = 'visible';
                    arguments[0].style.opacity      = '1';
                """, file_input)
                time.sleep(0.3)

                abs_path = os.path.abspath(photo_path)
                file_input.send_keys(abs_path)
                print(f"[BOT-{BOT_ID}] ✅ Dosya seçildi: {abs_path}")
                time.sleep(1.5)

                val = file_input.get_attribute("value")
                print(f"[BOT-{BOT_ID}] Input value: '{val}'")

                # ── ADIM 3: Upload butonu tıkla ──────────────────────
                # id = ctl00_cphButtons_btnUpload  (type=image)
                upload_submit = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_cphButtons_btnUpload")
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", upload_submit
                )
                driver.execute_script("arguments[0].click();", upload_submit)
                print(f"[BOT-{BOT_ID}] ✅ Upload tıklandı, sonuç bekleniyor...")
                time.sleep(5.0)
                wait_document_ready(driver, 30)
                print(f"[BOT-{BOT_ID}] Result URL: {driver.current_url}")

                # ── ADIM 4: Result sayfası — "Use This Photo" ────────
                # id = ctl00_cphButtons_btnContinue  (type=image)
                continue_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_cphButtons_btnContinue")
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", continue_btn
                )
                driver.execute_script("arguments[0].click();", continue_btn)
                print(f"[BOT-{BOT_ID}] ✅ Use This Photo tıklandı")
                time.sleep(4.0)
                wait_document_ready(driver, 30)
                print(f"[BOT-{BOT_ID}] Confirm Photo URL: {driver.current_url}")

                # ── ADIM 5: Confirm Photo — Next: REVIEW ─────────────
                # id = ctl00_SiteContentPlaceHolder_UpdateButton3
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.ID, "ctl00_SiteContentPlaceHolder_UpdateButton3")
                    )
                )
                driver.execute_script(
                    "document.getElementById('ctl00_SiteContentPlaceHolder_UpdateButton3')"
                    ".disabled = false;"
                    "__doPostBack('ctl00$SiteContentPlaceHolder$UpdateButton3','');"
                )
                print(f"[BOT-{BOT_ID}] ✅ Next: REVIEW tıklandı — fotoğraf tamamlandı!")
                time.sleep(3.0)

            except Exception as e:
                import traceback as _tb
                print(f"[BOT-{BOT_ID}] ❌ Fotoğraf yükleme hatası: {e}")
                print(_tb.format_exc())
                take_and_send_screenshot(driver, job_id)
                wait_for_close_command(driver, job_id)

            finally:
                # Geçici dosyayı sil
                try:
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        print(f"[BOT-{BOT_ID}] 🗑️ Geçici dosya silindi: {tmp_path}")
                except Exception:
                    pass
        
        
        fill_ds160_full_application(
            driver, wait, data,
            on_personal1_saved=on_personal1_saved,
            on_photo_page=on_photo_page,
        )

        update_job_status(job_id, "completed")

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[BOT-{BOT_ID}] HATA:\n{tb}")
        update_job_status(job_id, "failed", {"error": tb[:2000]})

    finally:
        try:
            driver.quit()
        except Exception:
            pass


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

    # Önce sayfanın yüklendiğinden emin ol
    try:
        wait_document_ready(driver, 30)
    except Exception:
        pass

    # Mevcut URL'yi kontrol et
    try:
        current_url = driver.current_url
        print(f"[BOT-{BOT_ID}] Mevcut URL: {current_url}")
    except Exception as e:
        raise RuntimeError(f"Browser kapanmış: {e}")

    for attempt in range(10):  # 5'ten 10'a çıkar
        try:
            # Personal linki ara
            personal1_link = wait.until(
                EC.presence_of_element_located((By.ID, "Personal"))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", personal1_link
            )
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", personal1_link)

            # Sayfanın yüklenmesini bekle
            wait_document_ready(driver, 30)
            time.sleep(1)

            # Personal 1 sayfasında mıyız?
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((
                    By.ID,
                    "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SURNAME"
                ))
            )
            print(f"[BOT-{BOT_ID}] Personal 1'e gecildi")
            return

        except (StaleElementReferenceException, TimeoutException):
            print(f"[BOT-{BOT_ID}] retry {attempt+1}/10")
            time.sleep(1)
        except Exception as e:
            print(f"[BOT-{BOT_ID}] retry {attempt+1}/10 hata: {e}")
            time.sleep(1)

    raise RuntimeError("Personal 1'e gecilemedi")
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