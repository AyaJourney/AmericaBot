import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

# =====================================================
# CONFIG
# =====================================================
CRM_BASE_URL = "https://crm-domain.com"
FETCH_JOB_URL = f"{CRM_BASE_URL}/api/internal/queue/ds160"
JOB_RESULT_URL = f"{CRM_BASE_URL}/api/internal/job-result"

WORKER_KEY = "SECRET_WORKER_KEY"

DS160_URL = "https://ceac.state.gov/GenNIV/"

# =====================================================
# CRM COMMUNICATION
# =====================================================
def fetch_job_from_crm():
    print("🔍 CRM'den iş aranıyor...")

    res = requests.get(
        FETCH_JOB_URL,
        headers={
            "x-worker-key": WORKER_KEY
        },
        timeout=30
    )

    if res.status_code != 200:
        print("❌ CRM erişilemedi")
        return None

    payload = res.json()
    job = payload.get("job")

    if not job:
        print("ℹ️ Bekleyen iş yok")
        return None

    print("✅ İş alındı:", job["id"])
    return job


def send_job_result(job_id, status, reference=None, error=None):
    payload = {
        "id": job_id,
        "status": status,
        "reference": reference,
        "error": error
    }

    requests.post(
        JOB_RESULT_URL,
        headers={
            "Content-Type": "application/json",
            "x-worker-key": WORKER_KEY
        },
        json=payload,
        timeout=30
    )

# =====================================================
# SELENIUM SETUP
# =====================================================
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # gerekirse aç

    driver = webdriver.Chrome(options=options)
    return driver

# =====================================================
# DS-160 FIELD MAP
# =====================================================
FIELD_MAP = {
    "SURNAME": ("name", "ctl00_SiteContentPlaceHolder_txtSurname"),
    "GIVEN_NAME": ("name", "ctl00_SiteContentPlaceHolder_txtGivenName"),
    "BIRTH_DAY": ("id", "ddlDOBDay"),
    "BIRTH_MONTH": ("id", "ddlDOBMonth"),
    "BIRTH_YEAR": ("id", "txtDOBYear"),
    "BIRTH_CITY": ("name", "ctl00_SiteContentPlaceHolder_txtBirthCity"),
    "NATIONALITY": ("id", "ddlNationality"),
    "NATIONAL_ID": ("name", "ctl00_SiteContentPlaceHolder_txtNatID"),
}

# =====================================================
# FORM FILLER
# =====================================================
def fill_text(driver, by, selector, value):
    if not value:
        return
    el = driver.find_element(getattr(By, by.upper()), selector)
    el.clear()
    el.send_keys(value)


def fill_select(driver, by, selector, value):
    if not value:
        return
    select = Select(driver.find_element(getattr(By, by.upper()), selector))
    select.select_by_visible_text(value)

# =====================================================
# MAIN AUTOMATION
# =====================================================
def run_ds160_automation(job):
    data = job["data"]
    job_id = job["id"]

    driver = setup_driver()

    try:
        print("🌐 DS-160 sitesi açılıyor...")
        driver.get(DS160_URL)
        time.sleep(5)

        print("✍️ Form dolduruluyor...")

        for key, (by, selector) in FIELD_MAP.items():
            value = data.get(key)

            if not value:
                continue

            if "ddl" in selector:
                fill_select(driver, by, selector, value)
            else:
                fill_text(driver, by, selector, value)

            time.sleep(0.3)

        print("✅ Form doldurma tamamlandı")

        # ⚠️ CAPTCHA burada çıkar – MANUEL veya STRATEJİ eklenir
        print("⚠️ CAPTCHA bekleniyor...")
        input("Devam etmek için ENTER'a bas")

        # burada submit vs yapılabilir

        reference_number = "DS160-OK"

        send_job_result(
            job_id,
            status="done",
            reference=reference_number
        )

        print("🎉 İş başarıyla tamamlandı")

    except Exception as e:
        print("❌ HATA:", e)

        send_job_result(
            job_id,
            status="error",
            error=str(e)
        )

    finally:
        driver.quit()

# =====================================================
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    job = fetch_job_from_crm()

    if not job:
        exit()

    run_ds160_automation(job)
