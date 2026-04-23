import requests
import time
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ============================================================
# CRM API YAPILANDIRMASI
# ============================================================

# --- PRODUCTION (deploy sonrasi bunu ac) ---
CRM_BASE = "https://crm.ayajourney.com/api/internal"

# --- LOCAL TEST ---
# CRM_BASE = "http://localhost:3000/api/internal"

QUEUE_URL    = f"{CRM_BASE}/queue/uk-visa/start"
STATUS_URL   = f"{CRM_BASE}/job/uk-visa/status"
COMPLETE_URL = f"{CRM_BASE}/job/uk-visa/complete"
ERROR_URL    = f"{CRM_BASE}/job/uk-visa/error"
SAVE_LINK_URL = f"{CRM_BASE}/job/uk-visa/save-link"

POLL_INTERVAL             = 3
SELENIUM_PAGELOAD_TIMEOUT = 120

# ============================================================
# CRM FONKSIYONLARI
# ============================================================

def fetch_next_job():
    """Kuyruktan siradaki UK vize isini al"""
    try:
        resp = requests.post(QUEUE_URL, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                print(f"[CRM] Yeni is alindi: {data.get('job_id', 'N/A')}")
                return data
            else:
                print("[CRM] Kuyrukta is yok.")
                return None
        else:
            print(f"[CRM] Kuyruk hatasi: {resp.status_code}")
            return None
    except Exception as e:
        print(f"[CRM] Baglanti hatasi: {e}")
        return None


def update_job_status(job_id, status, message=""):
    try:
        requests.post(STATUS_URL, json={"job_id": job_id, "status": status, "message": message}, timeout=10)
        print(f"[CRM] Durum: {status} - {message}")
    except Exception as e:
        print(f"[CRM] Durum guncelleme hatasi: {e}")


def complete_job(job_id, result_data=None):
    try:
        requests.post(COMPLETE_URL, json={"job_id": job_id, "result": result_data or {}}, timeout=10)
        print(f"[CRM] Is tamamlandi: {job_id}")
    except Exception as e:
        print(f"[CRM] Tamamlama hatasi: {e}")


def report_error(job_id, error_message):
    try:
        resp = requests.post(ERROR_URL, json={"job_id": job_id, "error": error_message}, timeout=10)
        data = resp.json()
        print(f"[CRM] Hata bildirildi. Retry: {data.get('will_retry', False)}")
    except Exception as e:
        print(f"[CRM] Hata bildirme hatasi: {e}")


def save_resume_link(job_id, resume_link):
    """Resume linkini CRM'e kaydet"""
    try:
        resp = requests.post(SAVE_LINK_URL, json={"job_id": job_id, "resume_link": resume_link}, timeout=10)
        if resp.status_code == 200:
            print(f"[CRM] Resume link kaydedildi: {resume_link}")
            return True
        else:
            print(f"[CRM] Resume link kaydetme hatasi: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[CRM] Resume link hatasi: {e}")
        return False


# ============================================================
# VISA_FORMS VERİ PARSER
# ============================================================

class VisaFormData:
    """visa_forms tablosundan gelen veriyi parse eder"""

    def __init__(self, raw_data):
        """
        raw_data: visa_forms.data alani
        Yapi: { "1": {...kisisel}, "2": {...aile}, "3": {...pasaport}, "4": {...is}, "5": {...seyahat}, "6": {...dosyalar} }
        """
        self.raw = raw_data or {}
        self.step1 = self.raw.get("1", {})  # Kisisel bilgiler
        self.step2 = self.raw.get("2", {})  # Aile bilgileri
        self.step3 = self.raw.get("3", {})  # Pasaport bilgileri
        self.step4 = self.raw.get("4", {})  # Is/Finans bilgileri
        self.step5 = self.raw.get("5", {})  # Seyahat bilgileri
        self.step6 = self.raw.get("6", {})  # Dosyalar

    # --- Step 1: Kisisel Bilgiler ---
    @property
    def full_name(self):
        return self.step1.get("fullName", "").strip()

    @property
    def first_name(self):
        parts = self.full_name.split()
        return parts[0] if parts else ""

    @property
    def last_name(self):
        parts = self.full_name.split()
        return " ".join(parts[1:]) if len(parts) > 1 else ""

    @property
    def email(self):
        return self.step1.get("email", "").strip()

    @property
    def email2(self):
        return self.step1.get("email2", "").strip()

    @property
    def gender(self):
        return self.step1.get("gender", "").strip()

    @property
    def birth_date(self):
        return self.step1.get("birthDate", "")

    @property
    def birth_place(self):
        return self.step1.get("birthPlace", "").strip()

    @property
    def nationality(self):
        return self.step1.get("nationality", "").strip()

    @property
    def phone(self):
        return self.step1.get("phone_number", "").strip()

    @property
    def marital_status(self):
        return self.step1.get("maritalStatus", "").strip()

    @property
    def home_address(self):
        return self.step1.get("home_address", "").strip()

    @property
    def home_city(self):
        return self.step1.get("home_city", "").strip()

    @property
    def post_code(self):
        return self.step1.get("post_code", "").strip()

    @property
    def home_district(self):
        return self.step1.get("home_district", "").strip()

    @property
    def home_neighborhood(self):
        return self.step1.get("home_neighborhood", "").strip()

    @property
    def home_owner(self):
        val = self.step1.get("home_owner", "").strip()
        if not val:
            val = self.step1.get("ownership_status", "").strip()
        if not val:
            val = self.step1.get("ev_durumu", "").strip()
        return val

    @property
    def residence_duration(self):
        val = self.step1.get("residence_duration", "").strip()
        if not val:
            val = self.step1.get("home_duration", "").strip()
        if not val:
            val = self.step1.get("oturma_suresi", "").strip()
        if not val:
            # step2'den de dene
            val = self.step2.get("residence_duration", "").strip()
        return val

    @property
    def residence_months_total(self):
        total = int(self.step1.get("residence_months_total", 0) or 0)
        if total > 0:
            return total
        # Fallback: residence_duration stringinden parse et
        dur = self.residence_duration.upper()
        if not dur:
            return 0
        # "5 YIL", "5 YIL 6 AY", "10 AY", "3 YEARS", "2 YEARS 4 MONTHS"
        import re
        years = 0
        months = 0
        year_match = re.search(r"(\d+)\s*(YIL|YEAR|SENE)", dur)
        if year_match:
            years = int(year_match.group(1))
        month_match = re.search(r"(\d+)\s*(AY|MONTH)", dur)
        if month_match:
            months = int(month_match.group(1))
        # Eger hicbir birim bulunamadiysa ama sayi varsa, yil varsay
        if years == 0 and months == 0:
            num_match = re.search(r"(\d+)", dur)
            if num_match:
                years = int(num_match.group(1))
        return years * 12 + months

    @property
    def residence_years(self):
        return self.residence_months_total // 12

    @property
    def residence_months(self):
        return self.residence_months_total % 12

    @property
    def past_addresses(self):
        return self.step1.get("past_addresses", "").strip()

    @property
    def maiden_name(self):
        return self.step1.get("maidenName", "").strip()

    @property
    def has_other_nationality(self):
        return self.step1.get("other_nationality", "").strip().upper() == "EVET"

    @property
    def other_nationality_country(self):
        return self.step1.get("other_nationality_country", "").strip()

    @property
    def other_nationality_start_date(self):
        return self.step1.get("other_nationality_start_date", "")

    @property
    def other_nationality_end_date(self):
        return self.step1.get("other_nationality_end_date", "")

    @property
    def has_name_changed(self):
        return self.step1.get("bool_last_fullname", "").strip().upper() == "EVET"

    # --- Partner ---
    @property
    def partner_name(self):
        return self.step1.get("partner_full_name", "").strip()

    @property
    def partner_birth_date(self):
        return self.step1.get("partner_birth_date", "")

    @property
    def partner_nationality(self):
        return self.step1.get("partner_nationality", "").strip()

    @property
    def partner_passport(self):
        return self.step1.get("partner_passport_number", "").strip()

    @property
    def partner_lives_with(self):
        return self.step1.get("partner_lives_with_you", "").strip().upper() == "EVET"

    @property
    def partner_travels_with(self):
        return self.step1.get("partner_travel_with_you", "").strip().upper() == "EVET"

    # --- Step 2: Aile ---
    @property
    def father_name(self):
        return self.step2.get("father_full_name", "").strip()

    @property
    def mother_name(self):
        return self.step2.get("mother_full_name", "").strip()

    @property
    def father_birth_date(self):
        return self.step2.get("father_birth_date", "")

    @property
    def mother_birth_date(self):
        return self.step2.get("mother_birth_date", "")

    @property
    def father_nationality(self):
        return self.step2.get("father_nationality", "").strip()

    @property
    def mother_nationality(self):
        return self.step2.get("mother_nationality", "").strip()

    @property
    def has_children(self):
        return self.step2.get("boolean_child", "").strip().upper() == "EVET"

    @property
    def child_count(self):
        return int(self.step2.get("child_count", "0") or "0")

    @property
    def children(self):
        """Cocuk bilgilerini liste olarak dondur"""
        names = self.step2.get("child_names", [])
        result = []
        for i, name in enumerate(names):
            result.append({
                "name": name.strip(),
                "birth_date": self.step2.get("child_birth_date", {}).get(str(i), ""),
                "lives_with": self.step2.get("child_live", {}).get(str(i), "").upper() == "EVET",
                "travels_with": self.step2.get("child_travel_with_you", {}).get(str(i), "").upper() == "EVET",
                "has_visa": self.step2.get("child_visa", {}).get(str(i), "").upper() == "EVET",
                "address": self.step2.get("child_address", [""])[i] if i < len(self.step2.get("child_address", [])) else "",
            })
        return result

    # --- Step 3: Pasaport ---
    @property
    def passport_number(self):
        return self.step3.get("passport_number", "").strip()

    @property
    def tc_id(self):
        return self.step3.get("tcId", "").strip()

    @property
    def passport_start_date(self):
        return self.step3.get("Passport_start_date", "")

    @property
    def passport_end_date(self):
        return self.step3.get("Passport_end_date", "")

    @property
    def passport_authority(self):
        return self.step3.get("passport_issuing_authority", "").strip()

    @property
    def tc_card_end_date(self):
        return self.step3.get("tc_card_end_date", "")

    # --- Step 4: Is/Finans ---
    @property
    def is_working(self):
        return self.step4.get("boolean_work", "").strip().upper() == "CALISIYOR"

    @property
    def is_own_business(self):
        return self.step4.get("own_work", "").strip().upper() == "EVET"

    @property
    def work_name(self):
        return self.step4.get("work_name", "").strip()

    @property
    def work_title(self):
        return self.step4.get("worker_title", "").strip()

    @property
    def work_phone(self):
        return self.step4.get("work_phone", "").strip()

    @property
    def work_address(self):
        return self.step4.get("work_address", "").strip()

    @property
    def work_start_date(self):
        return self.step4.get("work_year", "")

    @property
    def monthly_salary(self):
        return self.step4.get("monthly_salary", "").strip()

    @property
    def monthly_income(self):
        return self.step4.get("monthly_money", "").strip()

    @property
    def monthly_expenses(self):
        return self.step4.get("monthly_expenditure_amount", "").strip()

    @property
    def has_savings(self):
        savings_val = self.step4.get("savings", "").strip()
        if savings_val.upper() == "VAR":
            return True
        # Eger rakam ise ve > 0 ise birikimi var demek
        try:
            amount = int(savings_val.replace(".", "").replace(",", ""))
            return amount > 0
        except:
            return False

    @property
    def savings_amount(self):
        savings_val = self.step4.get("savings", "").strip()
        try:
            return int(savings_val.replace(".", "").replace(",", ""))
        except:
            return 0

    @property
    def savings_type(self):
        return self.step4.get("savings_type", "").strip()

    @property
    def dependents(self):
        return self.step4.get("dependents", [])

    # --- Step 5: Seyahat ---
    @property
    def travel_reason(self):
        return self.step5.get("travel_reason", "").strip()

    @property
    def travel_start_date(self):
        return self.step5.get("travel_start_date", "")

    @property
    def travel_end_date(self):
        return self.step5.get("travel_end_date", "")

    @property
    def spend_pounds(self):
        return self.step5.get("spend_pound", "").strip()

    @property
    def has_uk_visit_last10(self):
        return self.step5.get("uk_visited_last10", "").strip().upper() == "EVET"

    @property
    def has_uk_visa_last10(self):
        return self.step5.get("uk_visa_last10", "").strip().upper() == "EVET"

    @property
    def visa_refused(self):
        return self.step5.get("boolean_refused_visa", "").strip().upper() == "EVET"

    @property
    def has_invitation(self):
        return self.step5.get("have_invitation", "").strip().upper() == "EVET"

    @property
    def has_family_in_uk(self):
        return self.step5.get("has_family_in_uk", "").strip().upper() == "EVET"

    @property
    def traveled_abroad(self):
        return self.step5.get("boolean_traveled_adroad", "").strip().upper() == "EVET"

    @property
    def abroad_countries(self):
        return self.step5.get("abroad_country", [])

    @property
    def last_travels(self):
        """CRM'den son seyahat listesi"""
        travels = self.step5.get("lastTravels", [])
        # Bos kayitlari filtrele
        return [t for t in travels if t.get("country", "").strip()]

    @property
    def travels_with_non_family(self):
        return self.step5.get("travel_with_non_family", "").strip().upper() == "EVET"

    @property
    def non_family_companion_name(self):
        return self.step5.get("travel_non_family_fullname", "").strip()

    @property
    def non_family_companion_relation(self):
        return self.step5.get("travel_non_family_relation", "").strip()

    @property
    def non_family_companion_passport(self):
        return self.step5.get("travel_non_family_passport_number", "").strip()

    @property
    def covers_own_expenses(self):
        return self.step5.get("boolean_cover_expenses", "").strip().upper() == "EVET"

    @property
    def medical_treatment(self):
        return self.step5.get("medical_treatment_uk", "").strip().upper() == "EVET"

    @property
    def uk_public_funds(self):
        return self.step5.get("uk_public_funds", "").strip().upper() == "EVET"

    def summary(self):
        """Ozet bilgi yazdir"""
        return (
            f"Ad: {self.full_name} | Cinsiyet: {self.gender} | Dogum: {self.birth_date}\n"
            f"Pasaport: {self.passport_number} | TC: {self.tc_id}\n"
            f"Telefon: {self.phone} | Email: {self.email}\n"
            f"Seyahat: {self.travel_start_date} - {self.travel_end_date} | Amac: {self.travel_reason}\n"
            f"Is: {self.work_name} ({self.work_title})\n"
            f"Medeni: {self.marital_status} | Cocuk: {self.child_count}"
        )


# ============================================================
# SELENIUM YARDIMCI FONKSIYONLARI
# ============================================================

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(SELENIUM_PAGELOAD_TIMEOUT)
    return driver


def safe_click(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


# ============================================================
# YARDIMCI FONKSIYONLAR (tekrar eden islemleri birlestir)
# ============================================================

def wait_for_page(driver, keyword, timeout=10):
    """Form action veya URL keyword icerene kadar bekle."""
    kw = keyword.lower()
    for _ in range(timeout):
        try:
            found = driver.execute_script(f"""
                var url = window.location.href.toLowerCase();
                if (url.includes('{kw}')) return true;
                var forms = document.querySelectorAll('form');
                for (var i = 0; i < forms.length; i++) {{
                    if ((forms[i].getAttribute('action') || '').toLowerCase().includes('{kw}')) return true;
                }}
                return false;
            """)
            if found:
                return True
        except:
            pass
        time.sleep(1)
    return False


def set_radio(driver, radio_id):
    """JS ile radio sec - en guvenilir yontem."""
    driver.execute_script(f"""
        var r = document.getElementById('{radio_id}');
        if (r) {{
            r.scrollIntoView({{block: 'center'}});
            r.checked = true;
            r.click();
            r.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
    """)
    time.sleep(0.3)


def set_input(driver, field_id, value, wait_obj=None):
    """Text/number input'a deger yaz - send_keys + JS fallback."""
    if not value:
        return
    val = str(value)
    try:
        if wait_obj:
            el = wait_obj.until(EC.presence_of_element_located((By.ID, field_id)))
        else:
            el = driver.find_element(By.ID, field_id)
        
        # Number input ise JS ile yaz (send_keys number'da sorunlu)
        input_type = el.get_attribute("type") or "text"
        if input_type == "number":
            driver.execute_script(f"""
                var el = document.getElementById('{field_id}');
                if (el) {{
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, '{val}');
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
            """)
        else:
            driver.execute_script("arguments[0].value = '';", el)
            safe_click(driver, el)
            time.sleep(0.1)
            el.send_keys(val)
        time.sleep(0.1)
    except:
        driver.execute_script(f"""
            var e = document.getElementById('{field_id}');
            if (e) {{
                var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(e, '{val.replace("'", "")}');
                e.dispatchEvent(new Event('input', {{bubbles: true}}));
                e.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        """)


def set_select(driver, select_id, value, ui_text=None):
    """Select/dropdown'a deger ata - hidden select + UI input."""
    driver.execute_script(f"""
        var s = document.getElementById('{select_id}');
        if (s) {{
            // Onceki selected'i kaldir
            var opts = s.querySelectorAll('option');
            opts.forEach(function(o) {{ o.removeAttribute('selected'); }});
            // Yeni degeri sec
            s.value = '{value}';
            var target = s.querySelector('option[value="{value}"]');
            if (target) target.setAttribute('selected', 'selected');
            s.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
        var ui = document.getElementById('{select_id}_ui');
        if (ui) ui.value = '{ui_text or value}';
    """)
    time.sleep(0.3)


def set_date(driver, prefix, date_obj):
    """Tarih alanlarini doldur (prefix_day, prefix_month, prefix_year)."""
    for suffix, val in [("day", date_obj.day), ("month", date_obj.month), ("year", date_obj.year)]:
        field_id = f"{prefix}_{suffix}"
        set_input(driver, field_id, str(val))


def unhide_toggled(driver, toggled_by_id):
    """data-toggled-by ile gizlenen icerigi ac."""
    driver.execute_script(f"""
        var el = document.querySelector('[data-toggled-by="{toggled_by_id}"]');
        if (el) {{
            el.removeAttribute('hidden');
            el.removeAttribute('aria-hidden');
            el.style.display = '';
        }}
    """)
    time.sleep(0.5)


# ============================================================
# PRE-FILL (sadece validation hatasi sonrasi calisir)
# ============================================================

SAFE_RADIO_DEFAULTS = {
    'convictionTypeRef': 'none',
    'bandRef': '0',
    'countryRef': 'usa',
    'reasonRef': 'tourist',
    'reasonForVisit': 'tourism',
    'locationOfTreatment': 'doctor',
}

def emergency_fill(driver):
    """Validation hatasi sonrasi bos zorunlu alanlari doldur. SADECE hata varsa cagrilir."""
    return driver.execute_script("""
        var filled = [];
        
        // RADIO
        var allRadios = document.querySelectorAll('input[type="radio"]');
        var groups = {};
        allRadios.forEach(function(r) {
            if (!groups[r.name]) groups[r.name] = [];
            groups[r.name].push(r);
        });
        var safeDefaults = """ + json.dumps(SAFE_RADIO_DEFAULTS) + """;
        Object.keys(groups).forEach(function(name) {
            var g = groups[name];
            if (g.some(function(r){return r.checked;})) return;
            var target = null;
            if (safeDefaults[name]) {
                for (var i=0;i<g.length;i++) { if (g[i].value===safeDefaults[name]) {target=g[i];break;} }
            }
            if (!target) {
                for (var i=0;i<g.length;i++) { if (g[i].value==='false'||g[i].value==='no'||g[i].value==='none'||g[i].value==='0') {target=g[i];break;} }
            }
            if (!target) target = g[g.length-1];
            if (target) { target.checked=true; target.click(); target.dispatchEvent(new Event('change',{bubbles:true})); filled.push('r:'+name+'='+target.value); }
        });
        
        // TEXT/NUMBER INPUTS
        var inputs = document.querySelectorAll('input[aria-required="true"]:not([type="radio"]):not([type="checkbox"]):not([type="hidden"]):not([type="submit"])');
        inputs.forEach(function(inp) {
            if (inp.value && inp.value.trim()) return;
            if (inp.closest('[hidden],[aria-hidden="true"]')) return;
            if (inp.classList.contains('ui-autocomplete-input')) return;
            var id = (inp.id||'').toLowerCase(), val='N/A';
            if (inp.type==='number') {
                if (id.includes('day')) val='15'; else if (id.includes('month')) val='6'; else if (id.includes('year')) val='2020';
                else if (id.includes('amount')) val='1000'; else if (id==='yearslived') val='5'; else if (id==='monthslived') val='0';
                else if (id.includes('duration')||id.includes('times')) val='1'; else val='1000';
            } else {
                if (id.includes('postcode')||id.includes('postalcode')||id.includes('lookuppostcode')) val='SW1A 1AA';
                else if (id.includes('phone')||id.includes('telephone')||inp.type==='tel') val=id.includes('code')?'90':'5555555555';
                else if (id.includes('email')) val='noreply@example.com';
                else if (id.includes('town')||id.includes('city')) val='Istanbul';
                else if (id.includes('province')||id.includes('state')) val='Istanbul';
                else if (id.includes('jobtitle')) val='Employee';
                else if (id.includes('hospital')) val='General Hospital';
                else if (id.includes('name')||id.includes('employer')) val='UNKNOWN';
                else if (id.includes('number')||id.includes('passport')||id.includes('licence')) val='5555555555';
                else if (id.includes('address')||id.includes('line')) val='Unknown Address';
                else val='N/A';
            }
            var setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            setter.call(inp,val); inp.dispatchEvent(new Event('input',{bubbles:true})); inp.dispatchEvent(new Event('change',{bubbles:true}));
            filled.push('i:'+inp.id+'='+val);
        });
        
        // SELECTS
        document.querySelectorAll('select[aria-required="true"]').forEach(function(s) {
            if (s.value) return;
            if (s.closest('[hidden],[aria-hidden="true"]')) return;
            var id=(s.id||'').toLowerCase(), val='';
            if (id.includes('country')||id.includes('nationality')) { if(s.querySelector('option[value="TUR"]')) val='TUR'; }
            else if (id.includes('currency')) { val=s.querySelector('option[value="TRY"]')?'TRY':(s.querySelector('option[value="GBP"]')?'GBP':''); }
            else if (id.includes('unit')||id.includes('duration')) { val='days'; }
            else if (id.includes('relationship')) { val=s.querySelector('option[value="Fr"]')?'Fr':''; }
            if (!val) { var opts=s.querySelectorAll('option'); for(var i=0;i<opts.length;i++){if(opts[i].value){val=opts[i].value;break;}} }
            if (val) { s.value=val; s.dispatchEvent(new Event('change',{bubbles:true}));
                var ui=document.getElementById(s.id+'_ui'); if(ui&&!ui.value){var o=s.querySelector('option[value="'+val+'"]');if(o)ui.value=o.textContent.trim();}
                filled.push('s:'+s.id+'='+val); }
        });
        
        // TEXTAREAS
        document.querySelectorAll('textarea[aria-required="true"]').forEach(function(t) {
            if (t.value&&t.value.trim()) return;
            if (t.closest('[hidden],[aria-hidden="true"]')) return;
            t.value='N/A'; t.dispatchEvent(new Event('change',{bubbles:true})); filled.push('t:'+t.id);
        });
        
        // CHECKBOXES (readAll, confirm, none)
        document.querySelectorAll('input[type="checkbox"]').forEach(function(c) {
            if (c.checked) return;
            if (c.closest('[hidden],[aria-hidden="true"]')) return;
            var id=(c.id||'').toLowerCase(), nm=(c.name||'').toLowerCase();
            if (id.includes('readall')||id.includes('confirm')||id.includes('none_none')||nm.includes('readall')||nm.includes('confirm')) {
                c.checked=true; c.click(); c.dispatchEvent(new Event('change',{bubbles:true})); filled.push('c:'+c.id);
            }
        });
        
        return filled;
    """)


def click_submit(driver, wait):
    """Submit butonuna bas. Validation hatasi varsa emergency_fill ile doldur ve tekrar dene."""
    time.sleep(1)
    
    try:
        url_before = driver.current_url
    except:
        url_before = ""

    for attempt in range(7):
        # Submit butonuna bas - 3 farkli yontem dene
        submitted = False
        try:
            btn = wait.until(EC.element_to_be_clickable((By.ID, "submit")))
            safe_click(driver, btn)
            submitted = True
        except:
            pass
        
        if not submitted:
            try:
                driver.execute_script("""
                    var btn = document.getElementById('submit');
                    if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
                    else {
                        var btns = document.querySelectorAll('input[type="submit"]');
                        if (btns.length > 0) btns[0].click();
                    }
                """)
                submitted = True
            except:
                pass
        
        if not submitted:
            try:
                driver.execute_script("""
                    var form = document.querySelector('form');
                    if (form) HTMLFormElement.prototype.submit.call(form);
                """)
            except:
                return
        
        time.sleep(3)
        
        # Sayfa degisti mi?
        try:
            if driver.current_url != url_before:
                return
        except:
            pass
        
        # Validation hatasi var mi?
        has_error = driver.execute_script("""
            var errs = document.querySelectorAll('.validation-message, .error-message, .validation, .field-error, .error-summary');
            for (var i=0;i<errs.length;i++) {
                if (errs[i].offsetParent !== null && errs[i].textContent.trim().length > 3) return true;
            }
            return false;
        """)
        
        if has_error and attempt < 2:
            print(f"[RETRY-{attempt+1}] Validation hatasi, emergency_fill calistiriliyor...")
            filled = emergency_fill(driver)
            if filled:
                print(f"[RETRY-{attempt+1}] Dolduruldu: {filled[:5]}")
            time.sleep(1)
        else:
            return


# ============================================================
# NAVIGASYON (Start Now'a kadar)
# ============================================================

def navigate_to_form(driver, wait):
    print("[1] gov.uk sayfasina gidiliyor...")
    driver.get("https://www.gov.uk/apply-to-come-to-the-uk")
    time.sleep(3)

    print("[2] 'Standard Visitor visa' tiklaniyor...")
    safe_click(driver, wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/standard-visitor-visa']"))))
    time.sleep(3)

    print("[3] 'Apply for a Standard Visitor visa' tiklaniyor...")
    safe_click(driver, wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/standard-visitor/apply-standard-visitor-visa']"))))
    time.sleep(3)

    print("[4] 'Apply now' tiklaniyor...")
    safe_click(driver, wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.gem-c-button.govuk-button--start"))))
    time.sleep(4)

    print("[5] Turkce seciliyor...")
    safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "languageCode_tr"))))
    time.sleep(1)
    click_submit(driver, wait)
    time.sleep(3)

    print("[6] Yes - Turkce ve Ingilizce seciliyor...")
    safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "translationConfirmed_true"))))
    time.sleep(1)
    click_submit(driver, wait)
    time.sleep(3)

    print("[7] Turkey seciliyor...")
    country_input = wait.until(EC.presence_of_element_located((By.ID, "countryCode_ui")))
    safe_click(driver, country_input)
    time.sleep(0.5)
    country_input.clear()
    country_input.send_keys("Turkey")
    time.sleep(2)
    try:
        safe_click(driver, wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.ui-autocomplete li.ui-menu-item"))))
    except Exception:
        country_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.5)
        country_input.send_keys(Keys.ENTER)
    time.sleep(1)

    val = driver.execute_script("return document.getElementById('countryCode').value;")
    if val != "TUR":
        driver.execute_script("""
            var s = document.getElementById('countryCode');
            s.value = 'TUR';
            s.dispatchEvent(new Event('change', {bubbles: true}));
            document.getElementById('countryCode_ui').value = 'Turkey Türkiye';
        """)
        time.sleep(1)

    click_submit(driver, wait)
    time.sleep(3)

    print("[8] VAC onayi seciliyor...")
    safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "vacAvailabilityConfirmed_true"))))
    time.sleep(1)
    click_submit(driver, wait)
    time.sleep(3)

    print("[9] 'Start now' tiklaniyor...")
    safe_click(driver, wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#submit[value='Start now']"))))
    time.sleep(3)

    print("[OK] Form acildi!")
    return True


# ============================================================
# FORM DOLDURMA (visa_forms verisi ile)
# ============================================================

def detect_current_page(driver):
    """Mevcut sayfayi tespit et - URL once, sonra element ID kontrolu"""
    # ONCE URL'den kontrol et (en guvenilir)
    url = driver.current_url.lower()
    # Form action'lari da kontrol et
    try:
        form_action = driver.execute_script("""
            var f = document.querySelector('form[action]');
            return f ? f.getAttribute('action').toLowerCase() : '';
        """) or ""
    except:
        form_action = ""
    
    combined = url + " " + form_action
    
    if "monthlyoutgoings" in combined:
        return "monthly_outgoings"
    if "employmentstatus" in combined:
        return "employment_status"
    if "plannedspendonvisit" in combined:
        return "planned_spend"
    if "plannedtravelinformation" in combined:
        return "travel_dates"
    if "payingforyourvisit" in combined and "details" not in combined:
        return "paying_visit"
    if "fundingemploymentjobdetails" in combined:
        return "job_details"
    if "fundingemploymentemployerdetails" in combined:
        return "employer_details"
    if "fundingselfemployment" in combined:
        return "employer_details"  # self-employed de employer_details altinda
    if "fundingotherincome" in combined:
        return "other_income"
    if "standardworldtravelhistory" in combined:
        return "world_travel"
    if "standardimmigrationproblems" in combined:
        return "immigration_problems"
    if "standardimmigrationbreach" in combined:
        return "immigration_breach"
    if "standardnationalinsurance" in combined:
        return "national_insurance"
    if "standardpublicfunds" in combined:
        return "public_funds"
    if "accommodationarrangements" in combined:
        return "accommodation"
    if "accommodationplans" in combined:
        return "accommodation"
    if "otheraccommodationdetails" in combined:
        return "accommodation"
    if "previousukvisagranted" in combined:
        return "previous_uk_visa"
    if "previousleavetoremain" in combined:
        return "leave_to_remain"
    if "standardcriminalconvictions" in combined:
        return "criminal_convictions"
    if "standardwarcrimes" in combined:
        return "war_crimes"
    if "standardterroristactivities" in combined:
        return "terrorist_activities"
    if "standardextremistactivities" in combined:
        return "extremist_activities"
    if "standardpersonofgoodcharacter" in combined:
        return "good_character"
    if "standardemploymenthistory" in combined:
        return "employment_history"
    if "otherinformation" in combined:
        return "other_information"
    if "spokenlanguagepreference" in combined:
        return "language_pref"
    if combined.endswith("/partner") or "application.0.partner" in combined:
        return "partner"
    if "standardmedicaltreatment" in combined:
        return "medical_treatment"
    if "standarddrivinglicence" in combined:
        return "driving_licence"
    if "standardtimestravelledtouk" in combined or "previoustraveltouk" in combined:
        return "uk_travel_history"
    if "timestravelledtoothercountries" in combined:
        return "other_countries"
    if "travellingwithotherpeople" in combined:
        return "travelling_companion"
    if "hasdependants" in combined:
        return "has_dependants"
    
    # ELEMENT ID'lere bak
    page_checks = [
        # (element_id, sayfa_adı)
        ("email", "email_register"),
        ("emailOwner_you", "email_owner"),
        ("telephoneNumber", "phone"),
        ("contactByTelephone_callAndText", "contact_preference"),
        ("givenName", "name"),
        ("addAnother_true", "other_names"),
        ("gender_1", "gender_marital"),
        ("relationshipStatus", "gender_marital"),
        ("givenName", "partner"),
        ("liveWithYou_true", "partner"),
        ("outOfCountryAddress_line1", "address"),
        ("overseasAddress_line1", "previous_address"),
        ("isCorrespondenceAddress_true", "correspondence"),
        ("yearsLived", "home_duration"),
        ("travelDocumentNumber", "passport"),
        ("hasValidIdCard_true", "id_card"),
        ("nationalIdCardNo", "id_card_details"),
        ("nationality_ui", "nationality_dob"),
        ("placeOfBirth", "nationality_dob"),
        ("dob_day", "nationality_dob"),
        ("hasOtherNationality_true", "other_nationality"),
        ("otherNationality_ui", "other_nationality"),
        ("status_employed", "employment_status"),
        ("employer", "employer_details"),
        ("earnings_amount", "job_details"),
        ("jobDescription", "job_details"),
        ("jobTitle", "employer_details"),
        ("typeOfIncomeRefs_regularIncome", "other_income"),
        ("hasNoOtherIncome", "other_income"),
        ("value_currencyRef", "planned_spend"),
        ("value_amount", "planned_spend"),
        ("dateOfArrival_day", "travel_dates"),
        ("dateOfLeave_day", "travel_dates"),
        ("whoIsPayingRef_someoneIKnow", "paying_visit"),
        ("payeeName", "paying_visit"),
        ("preferredLanguage_english", "language_pref"),
        ("purposeRef_tourism", "visit_purpose"),
        ("purposeRef_tourist", "visit_sub_purpose"),
        ("purposeRef_meeting", "visit_sub_purpose"),
        ("purposeRef_research", "visit_sub_purpose"),
        ("enrolledInUKCourse_true", "visit_sub_purpose"),
        ("purposeRef_visitorInTransit", "visit_sub_purpose"),
        ("hasDependants", "has_dependants"),
        ("parent_relationshipRef_mother", "parent_one"),
        ("parent_relationshipRef_father", "parent_one"),
        ("parent_givenName", "parent_one"),
        ("familyInUk_described", "family_in_uk"),
        ("isTravellingWithOtherPeople_true", "travelling_group"),
        ("isTravellingWithSomeOneNotPartnerOrSpouse_true", "travelling_companion"),
        ("accommodationArrangements", "accommodation"),
        ("accommodationDetails_address_line1", "accommodation"),
        ("haveBeenToTheUK_true", "uk_travel_history"),
        ("reasonRef_tourist", "uk_travel_history"),
        ("bandRef_0", "other_countries"),
        ("haveYouHadTreatment_true", "medical_treatment"),
        ("haveYouHadTreatment_false", "medical_treatment"),
        ("standardNationalInsuranceNumber", "national_insurance"),
        ("doYouHaveADrivingLicence_true", "driving_licence"),
        ("standardPublicFunds", "public_funds"),
        ("previousUkVisaGranted", "previous_uk_visa"),
        ("previouslyApplied_true", "leave_to_remain"),
        ("convictionTypeRef_none", "criminal_convictions"),
        ("warCrimesInvolvement_false", "war_crimes"),
        ("terroristActivitiesInvolvement_false", "terrorist_activities"),
        ("extremistOrganisationsInvolvement_false", "extremist_activities"),
        ("personOfGoodCharacter_false", "good_character"),
        ("standardWorldTravelHistory", "world_travel"),
        ("standardImmigrationProblems", "immigration_problems"),
        ("standardImmigrationBreach", "immigration_breach"),
        ("armedForcesCareer_armedForcesCareer", "employment_history"),
        ("none_none", "employment_history"),
        ("otherInformation", "other_information"),
    ]

    for elem_id, page_name in page_checks:
        try:
            driver.find_element(By.ID, elem_id)
            return page_name
        except:
            continue

    # URL'den de anlamaya calis
    url = driver.current_url.lower()
    if "monthlyoutgoings" in url:
        return "monthly_outgoings"
    if "plannedspend" in url or "plannedspendonvisit" in url:
        return "planned_spend"
    if "plannedtravelinformation" in url:
        return "travel_dates"
    if "payingforyourvisit" in url:
        return "paying_visit"
    if "telephone" in url:
        return "phone"
    if "name" in url:
        return "name"
    if "address" in url:
        return "address"
    if "passport" in url or "traveldocument" in url:
        return "passport"
    if "identity" in url:
        return "id_card"

    return "unknown"


def resume_from_link(driver, wait, resume_link, form):
    """
    Kayitli resume linkinden devam et.
    Giris yap -> kaldigi sayfayi tespit et -> oradan devam et.
    """
    PASSWORD = "!!Adana508919"
    clean_email = fix_email(form.email)

    print(f"[RESUME] Resume linkine gidiliyor: {resume_link}")
    driver.get(resume_link)
    time.sleep(4)

    # Email girisi
    print("[RESUME] Email giriliyor...")
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.clear()
        email_input.send_keys(clean_email)
        time.sleep(0.5)
    except:
        print("[RESUME] Email alani bulunamadi, zaten giris yapilmis olabilir")

    # Parola girisi
    print("[RESUME] Parola giriliyor...")
    try:
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        password_input.clear()
        password_input.send_keys(PASSWORD)
        time.sleep(0.5)

        print("[RESUME] Giris yapiliyor...")
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input#submit[type='submit']"))
        )
        safe_click(driver, submit_btn)
        time.sleep(4)
    except:
        print("[RESUME] Parola alani bulunamadi, zaten giris yapilmis olabilir")

    # Kaldigi sayfayi tespit et
    current_page = detect_current_page(driver)
    print(f"[RESUME] Giris basarili! Kaldigi sayfa: {current_page}")
    print(f"[RESUME] URL: {driver.current_url}")
    return current_page


def save_and_exit(driver, wait, job_id):
    """
    Save for later linkine tikla, resume linkini al, CRM'e kaydet, mail gonder ve kapat.
    Hata durumunda veya form bittiginde cagirilir.
    """
    try:
        print("[SAVE] 'Save for later' linkine tiklaniyor...")
        save_link = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-track='save-for-later']"))
        )
        safe_click(driver, save_link)
        time.sleep(3)

        # Resume linkini al
        print("[SAVE] Resume link aliniyor...")
        resume_div = wait.until(
            EC.presence_of_element_located((By.ID, "resumeLink"))
        )
        resume_url = resume_div.text.strip()
        print(f"[SAVE] Resume link: {resume_url}")

        # CRM'e kaydet
        if resume_url and job_id:
            save_resume_link(job_id, resume_url)

        # Email link butonuna tikla
        print("[SAVE] Email link gonderiliyor...")
        try:
            email_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "emailLink"))
            )
            safe_click(driver, email_btn)
            time.sleep(3)
            print("[SAVE] Email gonderildi!")
        except Exception:
            print("[SAVE] Email butonu bulunamadi, atlanıyor...")

        return resume_url

    except Exception as e:
        print(f"[SAVE] Save for later hatasi: {e}")
        return None


def fix_email(email):
    """Turkce karakterleri ve email regex sorunlarini duzelt"""
    replacements = {
        'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C',
    }
    fixed = email.strip()
    for tr_char, en_char in replacements.items():
        fixed = fixed.replace(tr_char, en_char)
    return fixed


def clean_phone(phone_str):
    """Telefon numarasini temizle - +, bosluk, tire kaldir. Ulke kodu ayri girildigi icin 90 basini kaldir."""
    if not phone_str:
        return ""
    digits = ''.join(c for c in phone_str if c.isdigit())
    # Basinda 90 varsa ve 12+ hane ise kaldir (ulke kodu formda ayri)
    if digits.startswith("90") and len(digits) > 10:
        digits = digits[2:]
    # Basinda 0 varsa kaldir
    if digits.startswith("0") and len(digits) > 10:
        digits = digits[1:]
    return digits


def fill_form(driver, wait, form: VisaFormData, start_from=None):
    """
    Start now'dan sonra acilan formu visa_forms verisi ile doldur.
    start_from: resume'dan devam ederken hangi sayfadan baslanacagi.
    None ise en bastan baslar.
    """
    print(f"[FORM] Kullanici: {form.full_name}")
    print(f"[FORM] {form.summary()}")
    if start_from:
        print(f"[FORM] Kaldigi yerden devam ediliyor: {start_from}")

    PASSWORD = "!!Adana508919"

    # Tarih parse yardimcisi
    def parse_date_safe(date_str, field_name):
        if not date_str:
            print(f"[UYARI] {field_name} bos, varsayilan tarih kullanilacak")
            return datetime.now()
        date_str = date_str.strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.year < 1900:
                    dt = dt.replace(year=2020)
                if dt.year > 2040:
                    dt = dt.replace(year=2035)
                return dt
            except ValueError:
                continue
        print(f"[UYARI] {field_name} parse edilemedi: {date_str}")
        return datetime.now()

    # Adim sirasi - resume'dan devam ederken atlama icin
    STEP_ORDER = [
        "email_register",      # 1
        "email_owner",         # 2
        "no_other_person",     # 3
        "phone",               # 4
        "phone_add_another",   # 4b
        "contact_preference",  # 5
        "name",                # 6
        "other_names",         # 7
        "gender_marital",      # 8
        "partner",             # 8b
        "address",             # 9
        "correspondence",      # 10
        "home_duration",       # 11
        "previous_address",    # 11b
        "passport",            # 12
        "id_card",             # 13
        "id_card_details",     # 13b
        "nationality_dob",     # 14
        "other_nationality",   # 15
        "employment_status",   # 16
        "employer_details",    # 17
        "job_details",         # 17b
        "monthly_outgoings",   # 17c
        "other_income",        # 18
        "planned_spend",       # 19
        "travel_dates",        # 20
        "paying_visit",        # 21
        "language_pref",       # 22
        "visit_purpose",       # 23
        "visit_sub_purpose",   # 24
        "about_visit",         # 25
        "has_dependants",      # 26
        "parent_one",          # 27
        "parent_two",          # 28
        "family_in_uk",        # 29
        "travelling_group",    # 30
        "travelling_companion",# 31
        "accommodation",       # 32
        "uk_travel_history",   # 33
        "other_countries",     # 34
        "medical_treatment",   # 35
        "national_insurance",  # 36
        "driving_licence",     # 37
        "public_funds",        # 38
        "previous_uk_visa",    # 39
        "leave_to_remain",     # 40
        "criminal_convictions",# 41
        "war_crimes",          # 42
        "terrorist_activities",# 43
        "extremist_activities",# 44
        "good_character",      # 45
        "world_travel",        # 46
        "immigration_problems",# 47
        "immigration_breach",  # 48
        "employment_history",  # 49
        "other_information",   # 50
    ]

    # Baslangic adimini bul
    if start_from and start_from in STEP_ORDER:
        start_index = STEP_ORDER.index(start_from)
        print(f"[FORM] Adim {start_index + 1}'den ({start_from}) devam ediliyor, onceki adimlar atlaniyor.")
    elif start_from == "unknown":
        # Bilinmeyen sayfa - tarayici acik tut
        print("[FORM] Sayfa tespit edilemedi, tarayici acik tutuluyor.")
        input("[BEKLE] Sayfayi kontrol edip Enter'a bas...")
        start_index = 0
    else:
        start_index = 0

    def should_run(step_name):
        """Bu adim calistirilmali mi?"""
        if step_name not in STEP_ORDER:
            return True
        return STEP_ORDER.index(step_name) >= start_index

    # ===== SAYFA 1: Email ve Parola =====
    if should_run("email_register"):
        print("[FORM-1] Email ve parola giriliyor...")
        clean_email = fix_email(form.email)
        print(f"[FORM-1] Orijinal email: {form.email} -> Duzeltilmis: {clean_email}")

        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.clear()
        email_input.send_keys(clean_email)
        time.sleep(0.5)

        password1 = wait.until(EC.presence_of_element_located((By.ID, "password1")))
        password1.clear()
        password1.send_keys(PASSWORD)
        time.sleep(0.5)

        password2 = wait.until(EC.presence_of_element_located((By.ID, "password2")))
        password2.clear()
        password2.send_keys(PASSWORD)
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-1] Email/Parola tamamlandi!")

    # ===== SAYFA 2: Email sahibi - You =====
    if should_run("email_owner"):
        print("[FORM-2] Email sahibi seciliyor (You)...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "emailOwner_you"))))
        time.sleep(0.5)
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-2] Email sahibi tamamlandi!")

    # ===== SAYFA 3: Baska birisi var mi - No =====
    if should_run("no_other_person"):
        print("[FORM-3] 'No' seciliyor...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_false"))))
        time.sleep(0.5)
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-3] Tamamlandi!")

    # ===== SAYFA 4: Telefon numarasi =====
    if should_run("phone"):
        print("[FORM-4] Telefon numarasi giriliyor...")

        phone_input = wait.until(EC.presence_of_element_located((By.ID, "telephoneNumber")))
        phone_input.clear()
        clean = clean_phone(form.phone)
        phone_input.send_keys(clean)
        print(f"[FORM-4a] Telefon girildi: {clean}")
        time.sleep(0.5)

        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "telephoneNumberPurpose_outsideUK"))))
        time.sleep(0.3)

        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "telephoneNumberType_mobile"))))
        time.sleep(0.3)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-4] Telefon sayfasi tamamlandi!")

    # ===== SAYFA 4b: Baska numara ekle - No =====
    if should_run("phone_add_another"):
        print("[FORM-4b] Baska numara ekleme - No seciliyor...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "addAnother_false"))))
        time.sleep(0.5)
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-4b] Tamamlandi!")

    # ===== SAYFA 5: Iletisim tercihi - Call and Text =====
    if should_run("contact_preference"):
        print("[FORM-5] Iletisim tercihi seciliyor (Call and Text)...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "contactByTelephone_callAndText"))))
        time.sleep(0.5)
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-5] Iletisim tercihi tamamlandi!")

    # ===== SAYFA 6: Isim ve Soyisim =====
    if should_run("name"):
        print("[FORM-6] Isim ve soyisim giriliyor...")

        given_name = wait.until(EC.presence_of_element_located((By.ID, "givenName")))
        given_name.clear()
        given_name.send_keys(form.first_name)
        print(f"[FORM-6a] Isim girildi: {form.first_name}")
        time.sleep(0.5)

        family_name = wait.until(EC.presence_of_element_located((By.ID, "familyName")))
        family_name.clear()
        family_name.send_keys(form.last_name)
        print(f"[FORM-6b] Soyisim girildi: {form.last_name}")
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-6] Isim/Soyisim tamamlandi!")

    # ===== SAYFA 7: Baska isim var mi (Maiden name) =====
    if should_run("other_names"):
        if form.maiden_name:
            print(f"[FORM-7] Kizlik soyadi var: {form.maiden_name}, Yes seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "addAnother_true"))))
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)

            print("[FORM-7a] Kizlik soyadi bilgileri giriliyor...")
            other_given = wait.until(EC.presence_of_element_located((By.ID, "givenName")))
            other_given.clear()
            other_given.send_keys(form.first_name)
            time.sleep(0.3)

            other_family = wait.until(EC.presence_of_element_located((By.ID, "familyName")))
            other_family.clear()
            other_family.send_keys(form.maiden_name)
            print(f"[FORM-7b] Kizlik soyadi girildi: {form.maiden_name}")
            time.sleep(0.3)

            click_submit(driver, wait)
            time.sleep(3)

            print("[FORM-7c] Baska isim yok, No seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "addAnother_false"))))
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
        else:
            print("[FORM-7] Kizlik soyadi yok, No seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "addAnother_false"))))
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)

        print("[FORM-7] Baska isim sayfasi tamamlandi!")

    # ===== SAYFA 8: Cinsiyet ve Medeni Durum =====
    if should_run("gender_marital"):
        print("[FORM-8] Cinsiyet seciliyor...")

        gender_val = form.gender.upper()
        if gender_val == "ERKEK":
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "gender_1"))))
            print("[FORM-8a] Erkek secildi")
        elif gender_val in ("KADIN", "KADIM"):
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "gender_2"))))
            print("[FORM-8a] Kadin secildi")
        else:
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "gender_9"))))
            print("[FORM-8a] Unspecified secildi")
        time.sleep(0.5)

        print("[FORM-8b] Medeni durum seciliyor...")
        marital_map = {
            "BEKAR": "S",
            "EVLI": "M",
            "BOSANMIS": "D",
            "BOŞANMIŞ": "D",
            "DUL": "W",
            "AYRILMIS": "P",
            "AYRILMIŞ": "P",
            "PARTNER": "U",
        }
        marital_value = marital_map.get(form.marital_status.upper(), "S")
        marital_select = wait.until(EC.presence_of_element_located((By.ID, "relationshipStatus")))
        driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            marital_select, marital_value
        )
        print(f"[FORM-8b] Medeni durum secildi: {form.marital_status} -> {marital_value}")
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-8] Cinsiyet/Medeni durum tamamlandi!")

    # ===== SAYFA 8b: Partner/Es bilgileri =====
    if should_run("partner"):
        time.sleep(2)
        is_correct_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var forms = document.querySelectorAll('form');
            var foundForm = false;
            for (var i = 0; i < forms.length; i++) {
                var action = (forms[i].getAttribute('action') || '').toLowerCase();
                if (action.includes('.partner') && !action.includes('partnertravel')) {
                    foundForm = true;
                    break;
                }
            }
            var container = document.getElementById('partner');
            var hasLiveWith = document.getElementById('liveWithYou_true') !== null;
            return foundForm || (container !== null && hasLiveWith);
        """)

        if not is_correct_page:
            print("[FORM-8b] Partner sayfasi degil, atlaniyor...")
        else:
            print("[FORM-8b] Partner/es bilgileri giriliyor...")

            # Isim ve soyisim ayir
            partner_full = form.partner_name
            if partner_full:
                parts = partner_full.split()
                given = " ".join(parts[:-1]) if len(parts) > 1 else parts[0]
                family = parts[-1] if len(parts) > 1 else "UNKNOWN"
            else:
                given = "UNKNOWN"
                family = "UNKNOWN"

            given_input = wait.until(EC.presence_of_element_located((By.ID, "givenName")))
            given_input.clear()
            given_input.send_keys(given[:255])
            print(f"[FORM-8b.1] Isim: {given}")
            time.sleep(0.3)

            family_input = wait.until(EC.presence_of_element_located((By.ID, "familyName")))
            family_input.clear()
            family_input.send_keys(family[:255])
            print(f"[FORM-8b.2] Soyisim: {family}")
            time.sleep(0.3)

            # Dogum tarihi - send_keys ile (number input icin guvenilir)
            partner_dob = parse_date_safe(form.partner_birth_date, "Partner dogum")
            dob_fields = [
                ("dateOfBirth_day", str(partner_dob.day)),
                ("dateOfBirth_month", str(partner_dob.month)),
                ("dateOfBirth_year", str(partner_dob.year)),
            ]
            for field_id, val in dob_fields:
                try:
                    el = wait.until(EC.presence_of_element_located((By.ID, field_id)))
                    driver.execute_script("arguments[0].value = '';", el)
                    safe_click(driver, el)
                    time.sleep(0.1)
                    el.send_keys(val)
                    time.sleep(0.2)
                except Exception as e:
                    # JS fallback
                    driver.execute_script(f"""
                        var el = document.getElementById('{field_id}');
                        if (el) {{ el.value = '{val}'; el.dispatchEvent(new Event('change', {{bubbles:true}})); }}
                    """)
            print(f"[FORM-8b.3] Dogum: {partner_dob.day}/{partner_dob.month}/{partner_dob.year}")
            time.sleep(0.3)

            # Uyruk - TUR
            nat = form.partner_nationality.upper()
            nat_code = "TUR"
            if "TURKEY" in nat or "TURK" in nat or "TR" in nat:
                nat_code = "TUR"
            driver.execute_script(f"""
                var s = document.getElementById('nationalityRef');
                if (s) {{
                    s.value = '{nat_code}';
                    s.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                var ui = document.getElementById('nationalityRef_ui');
                if (ui) ui.value = 'Turkey Türkiye';
            """)
            print(f"[FORM-8b.4] Uyruk: {nat_code}")
            time.sleep(0.3)

            # Sizinle yasiyor mu?
            if form.partner_lives_with:
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "liveWithYou_true"))))
                print("[FORM-8b.5] Birlikte yasiyor: Yes")
            else:
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "liveWithYou_false"))))
                print("[FORM-8b.5] Birlikte yasiyor: No")
                time.sleep(2)

                # Hidden icerigi JS ile ac
                driver.execute_script("""
                    var indented = document.querySelector('[data-toggled-by="liveWithYou_false"]');
                    if (indented) {
                        indented.removeAttribute('hidden');
                        indented.removeAttribute('aria-hidden');
                        indented.style.display = '';
                    }
                """)
                time.sleep(1)

                # Adres alanlari - JS ile doldur (hidden'dan yeni acildi, send_keys calismayabilir)
                addr_text = form.home_address[:255] if form.home_address else "Unknown Address"
                city_text = form.home_city if form.home_city else "Istanbul"
                province_text = form.home_district if form.home_district else form.home_city or "Istanbul"
                postal_text = form.post_code if form.post_code else "34000"

                driver.execute_script(f"""
                    function setField(id, val) {{
                        var el = document.getElementById(id);
                        if (!el) return;
                        el.value = val;
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    setField('address_line1', '{addr_text[:80].replace("'", "")}');
                    setField('address_townCity', '{city_text.replace("'", "")}');
                    setField('address_province', '{province_text.replace("'", "")}');
                    setField('address_postalCode', '{postal_text}');

                    var s = document.getElementById('address_countryRef');
                    if (s) {{
                        s.value = 'TUR';
                        s.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    var ui = document.getElementById('address_countryRef_ui');
                    if (ui) ui.value = 'Turkey Türkiye';
                """)
                print("[FORM-8b.6] Partner adresi JS ile girildi")

            time.sleep(0.5)

            # Sizinle seyahat edecek mi?
            if form.partner_travels_with:
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "travellingWithYou_true"))))
                print("[FORM-8b.7] Birlikte seyahat: Yes")
                time.sleep(2)
                # Hidden icerigi ac
                driver.execute_script("""
                    var indented = document.querySelector('[data-toggled-by="travellingWithYou_true"]');
                    if (indented) {
                        indented.removeAttribute('hidden');
                        indented.removeAttribute('aria-hidden');
                    }
                """)
                time.sleep(0.5)
                # Pasaport numarasi
                pp_num = form.partner_passport if form.partner_passport else "UNKNOWN"
                driver.execute_script(f"""
                    var el = document.getElementById('passportNumber');
                    if (el) {{
                        el.value = '{pp_num[:255]}';
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                """)
                print(f"[FORM-8b.8] Pasaport: {pp_num}")
            else:
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "travellingWithYou_false"))))
                print("[FORM-8b.7] Birlikte seyahat: No")

            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-8b] Partner bilgileri tamamlandi!")

    # ===== SAYFA 9: Adres bilgileri =====
    if should_run("address"):
        print("[FORM-9] Adres bilgileri giriliyor...")

        addr1 = wait.until(EC.presence_of_element_located((By.ID, "outOfCountryAddress_line1")))
        addr1.clear()
        addr1.send_keys(form.home_address[:80] if form.home_address else "")
        print(f"[FORM-9a] Adres satir 1 girildi")
        time.sleep(0.3)

        addr2 = driver.find_element(By.ID, "outOfCountryAddress_line2")
        addr2.clear()
        if len(form.home_address) > 80:
            addr2.send_keys(form.home_address[80:160])
        time.sleep(0.3)

        town = wait.until(EC.presence_of_element_located((By.ID, "outOfCountryAddress_townCity")))
        town.clear()
        town.send_keys(form.home_city)
        print(f"[FORM-9b] Sehir girildi: {form.home_city}")
        time.sleep(0.3)

        province = wait.until(EC.presence_of_element_located((By.ID, "outOfCountryAddress_province")))
        province.clear()
        province.send_keys(form.home_district if form.home_district else form.home_city)
        print(f"[FORM-9c] Bolge girildi: {form.home_district or form.home_city}")
        time.sleep(0.3)

        postcode = wait.until(EC.presence_of_element_located((By.ID, "outOfCountryAddress_postCode")))
        postcode.clear()
        postcode.send_keys(form.post_code)
        print(f"[FORM-9d] Posta kodu girildi: {form.post_code}")
        time.sleep(0.3)

        print("[FORM-9e] Ulke seciliyor (Turkey)...")
        country_input = wait.until(EC.presence_of_element_located((By.ID, "outOfCountryAddress_countryRef_ui")))
        safe_click(driver, country_input)
        time.sleep(0.5)
        country_input.clear()
        country_input.send_keys("Turkey")
        time.sleep(2)

        try:
            turkey_opt = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.ui-autocomplete li.ui-menu-item")))
            safe_click(driver, turkey_opt)
        except Exception:
            country_input.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.5)
            country_input.send_keys(Keys.ENTER)
        time.sleep(1)

        val = driver.execute_script("return document.getElementById('outOfCountryAddress_countryRef').value;")
        if val != "TUR":
            driver.execute_script("""
                var s = document.getElementById('outOfCountryAddress_countryRef');
                s.value = 'TUR';
                s.dispatchEvent(new Event('change', {bubbles: true}));
                document.getElementById('outOfCountryAddress_countryRef_ui').value = 'Turkey Türkiye';
            """)
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-9] Adres bilgileri tamamlandi!")

    # ===== SAYFA 10: Correspondence address - Yes =====
    if should_run("correspondence"):
        print("[FORM-10] Yazisma adresi ayni mi - Yes seciliyor...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "isCorrespondenceAddress_true"))))
        time.sleep(0.5)
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-10] Yazisma adresi tamamlandi!")

    # ===== SAYFA 11: Evde oturma suresi ve ev sahipligi =====
    if should_run("home_duration"):
        print("[FORM-11] Oturma suresi ve ev sahipligi giriliyor...")

        years = form.residence_years
        months = form.residence_months
        # Eger hala 0 ise varsayilan 5 yil
        if years == 0 and months == 0:
            years = 5
            months = 0
            print(f"[UYARI] Oturma suresi bos, varsayilan 5 yil kullanilacak")

        # JS ile degerleri at (number input send_keys guvenilir degil)
        driver.execute_script(f"""
            function setVal(id, val) {{
                var el = document.getElementById(id);
                if (!el) return;
                var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, val);
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
            setVal('yearsLived', '{years}');
            setVal('monthsLived', '{months}');
        """)
        print(f"[FORM-11a] Yil: {years}")
        print(f"[FORM-11b] Ay: {months}")
        time.sleep(0.5)

        # Dogrulama
        y_val = driver.execute_script("return document.getElementById('yearsLived').value;")
        m_val = driver.execute_script("return document.getElementById('monthsLived').value;")
        print(f"[FORM-11] Dogrulama: Yil={y_val}, Ay={m_val}")

        # send_keys fallback - "0" gecerli bir deger, sadece None/empty kontrol et
        if y_val is None or y_val == '' or m_val is None or m_val == '':
            print("[FORM-11] JS ile girilemedi, send_keys deneniyor...")
            years_input = wait.until(EC.presence_of_element_located((By.ID, "yearsLived")))
            safe_click(driver, years_input)
            years_input.clear()
            years_input.send_keys(str(years))
            time.sleep(0.3)

            months_input = wait.until(EC.presence_of_element_located((By.ID, "monthsLived")))
            safe_click(driver, months_input)
            months_input.clear()
            months_input.send_keys(str(months))
            time.sleep(0.3)

        # Ev sahipligi - daima Other + sabit metin
        set_radio(driver, "ownershipCategory_other")
        time.sleep(1)
        unhide_toggled(driver, "ownershipCategory_other")
        set_input(driver, "otherCategoryDetails", "THE PROPERTY BELONGS TO MY FAMILY", wait)
        print("[FORM-11c] Ev sahipligi: Other - THE PROPERTY BELONGS TO MY FAMILY")
        time.sleep(0.3)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-11] Oturma suresi tamamlandi!")

    # ===== SAYFA 11b: Onceki adres (2 yildan az oturma) =====
    if should_run("previous_address"):
        time.sleep(1)
        # Bu sayfa sadece 2 yildan az oturmada gosterilebilir
        # URL kontrolu yap
        is_prev_addr_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var forms = document.querySelectorAll('form');
            var foundForm = false;
            for (var i = 0; i < forms.length; i++) {
                var action = (forms[i].getAttribute('action') || '').toLowerCase();
                if (action.includes('addresshistory') && !action.includes('list')) {
                    foundForm = true;
                    break;
                }
            }
            var hasOverseas = document.getElementById('overseasAddress_line1') !== null;
            var hasUkAddr = document.getElementById('isUkAddress_false') !== null;
            return foundForm || hasOverseas || hasUkAddr;
        """)

        if not is_prev_addr_page:
            print("[FORM-11b] Onceki adres sayfasi degil, atlaniyor...")
        else:
            print("[FORM-11b] Onceki adres giriliyor...")

            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "isUkAddress_false"))))
            time.sleep(2)

            prev_address = form.past_addresses if form.past_addresses else form.home_address

            prev_addr1 = wait.until(EC.presence_of_element_located((By.ID, "overseasAddress_line1")))
            prev_addr1.clear()
            prev_addr1.send_keys(prev_address[:80] if prev_address else "")
            time.sleep(0.3)

            prev_addr2 = driver.find_element(By.ID, "overseasAddress_line2")
            prev_addr2.clear()
            if len(prev_address) > 80:
                prev_addr2.send_keys(prev_address[80:160])
            time.sleep(0.3)

            prev_town = wait.until(EC.presence_of_element_located((By.ID, "overseasAddress_townCity")))
            prev_town.clear()
            prev_town.send_keys(form.home_city)
            time.sleep(0.3)

            prev_province = wait.until(EC.presence_of_element_located((By.ID, "overseasAddress_province")))
            prev_province.clear()
            prev_province.send_keys(form.home_district if form.home_district else form.home_city)
            time.sleep(0.3)

            prev_postcode = wait.until(EC.presence_of_element_located((By.ID, "overseasAddress_postCode")))
            prev_postcode.clear()
            prev_postcode.send_keys(form.post_code)
            time.sleep(0.3)

            driver.execute_script("""
                var s = document.getElementById('overseasAddress_countryRef');
                s.value = 'TUR';
                s.dispatchEvent(new Event('change', {bubbles: true}));
            """)
            time.sleep(0.5)

            now = datetime.now()
            current_move_in = now - relativedelta(months=form.residence_months_total)
            prev_move_in = current_move_in - relativedelta(months=3)
            prev_move_out = current_move_in

            driver.execute_script(f"""
                function setVal(id, val) {{
                    var el = document.getElementById(id);
                    if (!el) return;
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, String(val));
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                setVal('startDateAtAddress_month', {prev_move_in.month});
                setVal('startDateAtAddress_year', {prev_move_in.year});
                setVal('endDateAtAddress_month', {prev_move_out.month});
                setVal('endDateAtAddress_year', {prev_move_out.year});
            """)

            print(f"[FORM-11b] Onceki adres girildi. Giris: {prev_move_in.month}/{prev_move_in.year} Cikis: {prev_move_out.month}/{prev_move_out.year}")

            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-11b] Onceki adres tamamlandi!")

        # Baska adres ekle? - No
        try:
            time.sleep(1)
            is_add_another = driver.execute_script("""
                var forms = document.querySelectorAll('form');
                for (var i = 0; i < forms.length; i++) {
                    var action = (forms[i].getAttribute('action') || '').toLowerCase();
                    if (action.includes('addresshistory')) return true;
                }
                return document.getElementById('addAnother_false') !== null;
            """)
            if is_add_another:
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "addAnother_false"))))
                print("[FORM-11c] Baska adres ekle: No")
                time.sleep(0.5)
                click_submit(driver, wait)
                time.sleep(3)
                print("[FORM-11c] Tamamlandi!")
            else:
                print("[FORM-11c] addAnother sayfasi yok, devam ediliyor.")
        except Exception as e:
            print(f"[FORM-11c] addAnother hatasi: {e}")

    # ===== SAYFA 12: Pasaport bilgileri =====
    if should_run("passport"):
        print("[FORM-12] Pasaport bilgileri giriliyor...")

        passport_input = wait.until(EC.presence_of_element_located((By.ID, "travelDocumentNumber")))
        passport_input.clear()
        passport_input.send_keys(form.passport_number)
        print(f"[FORM-12a] Pasaport no: {form.passport_number}")
        time.sleep(0.3)

        issuing_country = wait.until(EC.presence_of_element_located((By.ID, "issuingCountry")))
        issuing_country.clear()
        issuing_country.send_keys("MINISTRY OF INTERIOR - DIRECTORATE GENERAL FOR CIVIL REGISTRY AND CITIZENSHIP")
        print("[FORM-12b] Verildigi yer: MINISTRY OF INTERIOR (sabit)")
        time.sleep(0.3)

        issue_date = parse_date_safe(form.passport_start_date, "Pasaport verilis tarihi")
        if issue_date > datetime.now():
            issue_date = datetime.now()

        expiry_date = parse_date_safe(form.passport_end_date, "Pasaport bitis tarihi")
        if expiry_date <= issue_date:
            expiry_date = issue_date + relativedelta(years=10)
        if expiry_date < datetime.now():
            expiry_date = datetime.now() + relativedelta(years=10)

        # JS ile tum tarihleri yaz
        driver.execute_script(f"""
            function setVal(id, val) {{
                var el = document.getElementById(id);
                if (!el) return;
                var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, String(val));
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                el.dispatchEvent(new Event('blur', {{bubbles: true}}));
            }}
            setVal('dateOfIssue_day', {issue_date.day});
            setVal('dateOfIssue_month', {issue_date.month});
            setVal('dateOfIssue_year', {issue_date.year});
            setVal('expiryDate_day', {expiry_date.day});
            setVal('expiryDate_month', {expiry_date.month});
            setVal('expiryDate_year', {expiry_date.year});
        """)
        time.sleep(0.5)
        print(f"[FORM-12c] Verilis tarihi: {issue_date.day}/{issue_date.month}/{issue_date.year}")
        print(f"[FORM-12d] Bitis tarihi: {expiry_date.day}/{expiry_date.month}/{expiry_date.year}")

        # Dogrulama + send_keys fallback
        vals = driver.execute_script("""
            return {
                id: document.getElementById('dateOfIssue_day').value,
                im: document.getElementById('dateOfIssue_month').value,
                iy: document.getElementById('dateOfIssue_year').value,
                ed: document.getElementById('expiryDate_day').value,
                em: document.getElementById('expiryDate_month').value,
                ey: document.getElementById('expiryDate_year').value
            };
        """)
        all_filled = all([vals.get('id'), vals.get('im'), vals.get('iy'), vals.get('ed'), vals.get('em'), vals.get('ey')])
        if not all_filled:
            print("[FORM-12] JS tarih basarisiz, send_keys deneniyor...")
            date_fields = [
                ("dateOfIssue_day", str(issue_date.day)),
                ("dateOfIssue_month", str(issue_date.month)),
                ("dateOfIssue_year", str(issue_date.year)),
                ("expiryDate_day", str(expiry_date.day)),
                ("expiryDate_month", str(expiry_date.month)),
                ("expiryDate_year", str(expiry_date.year)),
            ]
            for field_id, val in date_fields:
                try:
                    el = driver.find_element(By.ID, field_id)
                    safe_click(driver, el)
                    el.clear()
                    time.sleep(0.1)
                    el.send_keys(val)
                    time.sleep(0.2)
                except Exception as e:
                    print(f"[FORM-12] {field_id} hatasi: {e}")

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-12] Pasaport bilgileri tamamlandi!")

    # ===== SAYFA 13: Kimlik karti var mi =====
    if should_run("id_card"):
        print("[FORM-13] Kimlik karti sorgusu...")
        if form.tc_id:
            print(f"[FORM-13] TC kimlik var ({form.tc_id}), Yes seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "hasValidIdCard_true"))))
        else:
            print("[FORM-13] TC kimlik yok, No seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "hasValidIdCard_false"))))
        time.sleep(0.5)
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-13] Kimlik karti tamamlandi!")

    # ===== SAYFA 13b: Kimlik karti detaylari (sadece tc_id varsa) =====
    if should_run("id_card_details") and form.tc_id:
        print("[FORM-13b] Kimlik karti detaylari giriliyor...")

        id_number = wait.until(EC.presence_of_element_located((By.ID, "nationalIdCardNo")))
        id_number.clear()
        id_number.send_keys(form.tc_id)
        print(f"[FORM-13b] Kimlik no: {form.tc_id}")
        time.sleep(0.3)

        issuing_auth = wait.until(EC.presence_of_element_located((By.ID, "issuingAuthority")))
        issuing_auth.clear()
        auth_text = form.passport_authority if form.passport_authority else "NUFUS MUDURLUGU"
        issuing_auth.send_keys(auth_text)
        print(f"[FORM-13b] Veren makam: {auth_text}")
        time.sleep(0.3)

        if form.birth_date:
            id_issue = parse_date_safe(form.birth_date, "Kimlik verilis (dogum tarihi)")
        else:
            id_issue = datetime.now() - relativedelta(years=18)

        id_issue_day = wait.until(EC.presence_of_element_located((By.ID, "issueDate_day")))
        id_issue_day.clear()
        id_issue_day.send_keys(str(id_issue.day))
        time.sleep(0.2)
        id_issue_month = wait.until(EC.presence_of_element_located((By.ID, "issueDate_month")))
        id_issue_month.clear()
        id_issue_month.send_keys(str(id_issue.month))
        time.sleep(0.2)
        id_issue_year = wait.until(EC.presence_of_element_located((By.ID, "issueDate_year")))
        id_issue_year.clear()
        id_issue_year.send_keys(str(id_issue.year))
        time.sleep(0.3)
        print(f"[FORM-13b] Verilis tarihi: {id_issue.day}/{id_issue.month}/{id_issue.year}")

        if form.tc_card_end_date:
            id_expiry = parse_date_safe(form.tc_card_end_date, "Kimlik bitis tarihi")
            if id_expiry < datetime.now():
                id_expiry = datetime.now() + relativedelta(years=1)
        else:
            id_expiry = datetime.now() + relativedelta(years=1)

        id_expiry_day = wait.until(EC.presence_of_element_located((By.ID, "expiryDate_day")))
        id_expiry_day.clear()
        id_expiry_day.send_keys(str(id_expiry.day))
        time.sleep(0.2)
        id_expiry_month = wait.until(EC.presence_of_element_located((By.ID, "expiryDate_month")))
        id_expiry_month.clear()
        id_expiry_month.send_keys(str(id_expiry.month))
        time.sleep(0.2)
        id_expiry_year = wait.until(EC.presence_of_element_located((By.ID, "expiryDate_year")))
        id_expiry_year.clear()
        id_expiry_year.send_keys(str(id_expiry.year))
        time.sleep(0.3)
        print(f"[FORM-13b] Bitis tarihi: {id_expiry.day}/{id_expiry.month}/{id_expiry.year}")

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-13b] Kimlik karti detaylari tamamlandi!")

    # ===== SAYFA 14: Uyruk, Dogum Yeri, Dogum Tarihi =====
    if should_run("nationality_dob"):
        print("[FORM-14] Uyruk, dogum yeri ve tarihi giriliyor...")

        # --- Uyruk - JS ile direkt set (autocomplete cakismasi onlenir) ---
        print("[FORM-14a] Uyruk seciliyor (Turkey)...")
        driver.execute_script("""
            var s = document.getElementById('nationality');
            s.value = 'TUR';
            s.dispatchEvent(new Event('change', {bubbles: true}));
            var ui = document.getElementById('nationality_ui');
            if (ui) ui.value = 'Turkey Türkiye';
            if (typeof countryOnChange === 'function') countryOnChange();
        """)
        time.sleep(1)
        print("[FORM-14a] Uyruk secildi: TUR")

        # --- Dogum ulkesi - JS ile direkt set ---
        print("[FORM-14b] Dogum ulkesi seciliyor (Turkey)...")
        driver.execute_script("""
            var s = document.getElementById('countryOfBirth');
            s.value = 'TUR';
            s.dispatchEvent(new Event('change', {bubbles: true}));
            var ui = document.getElementById('countryOfBirth_ui');
            if (ui) ui.value = 'Turkey Türkiye';
        """)
        time.sleep(1)
        print("[FORM-14b] Dogum ulkesi secildi: TUR")

        # --- Dogum yeri ---
        place_input = wait.until(EC.presence_of_element_located((By.ID, "placeOfBirth")))
        place_input.clear()
        birth_place = form.birth_place if form.birth_place else form.home_city
        place_input.send_keys(birth_place[:30])
        print(f"[FORM-14c] Dogum yeri girildi: {birth_place[:30]}")
        time.sleep(0.5)

        # --- Dogum tarihi ---
        dob = parse_date_safe(form.birth_date, "Dogum tarihi")

        # Fallback: parse edilemediyse veya sacma bir tarih geldiyse
        age = (datetime.now() - dob).days // 365
        if age < 18 or age > 100:
            print(f"[UYARI] Yas gecersiz ({age}), varsayilan 1985-01-15 kullanilacak")
            dob = datetime(1985, 1, 15)
            age = (datetime.now() - dob).days // 365

        print(f"[FORM-14d] Dogum tarihi girilecek: {dob.day}/{dob.month}/{dob.year} (Yas: {age})")

        # JS ile degerleri at (send_keys number input'larda bazen calismaz)
        driver.execute_script(f"""
            var dayEl = document.getElementById('dob_day');
            var monthEl = document.getElementById('dob_month');
            var yearEl = document.getElementById('dob_year');
            
            function setVal(el, val) {{
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(el, val);
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            
            setVal(dayEl, '{dob.day}');
            setVal(monthEl, '{dob.month}');
            setVal(yearEl, '{dob.year}');
        """)
        time.sleep(1)

        # Dogrulama: degerler girildi mi?
        day_val = driver.execute_script("return document.getElementById('dob_day').value;")
        month_val = driver.execute_script("return document.getElementById('dob_month').value;")
        year_val = driver.execute_script("return document.getElementById('dob_year').value;")
        print(f"[FORM-14d] Dogrulama - Gun: {day_val}, Ay: {month_val}, Yil: {year_val}")

        # Hala bos ise son care: tiklayip send_keys
        if not day_val or not month_val or not year_val:
            print("[FORM-14d] JS ile girilemedi, send_keys deneniyor...")
            dob_day = driver.find_element(By.ID, "dob_day")
            safe_click(driver, dob_day)
            dob_day.clear()
            dob_day.send_keys(str(dob.day))
            time.sleep(0.5)

            dob_month = driver.find_element(By.ID, "dob_month")
            safe_click(driver, dob_month)
            dob_month.clear()
            dob_month.send_keys(str(dob.month))
            time.sleep(0.5)

            dob_year = driver.find_element(By.ID, "dob_year")
            safe_click(driver, dob_year)
            dob_year.clear()
            dob_year.send_keys(str(dob.year))
            time.sleep(1)

        print(f"[FORM-14d] Dogum tarihi girildi: {dob.day}/{dob.month}/{dob.year}")

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-14] Uyruk/Dogum bilgileri tamamlandi!")

    # ===== SAYFA 15: Baska uyruk var mi =====
    if should_run("other_nationality"):
        if form.has_other_nationality and form.other_nationality_country:
            print(f"[FORM-15] Baska uyruk VAR: {form.other_nationality_country}")

            # Yes sec
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "hasOtherNationality_true"))))
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)

            # --- Diger uyruk detay sayfasi ---
            print("[FORM-15a] Diger uyruk detaylari giriliyor...")

            # Ulke sec - JS ile
            country_code = form.other_nationality_country.upper()
            # Eger TURKEY gibi isim geldiyse TUR'a cevir
            country_name_to_code = {"TURKEY": "TUR", "TURKIYE": "TUR"}
            if country_code in country_name_to_code:
                country_code = country_name_to_code[country_code]

            driver.execute_script(f"""
                var s = document.getElementById('otherNationality');
                s.value = '{country_code}';
                s.dispatchEvent(new Event('change', {{bubbles: true}}));
                var ui = document.getElementById('otherNationality_ui');
                if (ui) {{
                    var opt = s.querySelector('option[value="{country_code}"]');
                    if (opt) ui.value = opt.textContent.trim();
                }}
            """)
            time.sleep(1)
            print(f"[FORM-15a] Uyruk ulkesi secildi: {country_code}")

            # Baslangic tarihi
            start_date = parse_date_safe(form.other_nationality_start_date, "Diger uyruk baslangic")
            # Bos ise dogum tarihi kullan
            if not form.other_nationality_start_date:
                start_date = parse_date_safe(form.birth_date, "Diger uyruk baslangic (dogum)")

            driver.execute_script(f"""
                function setVal(id, val) {{
                    var el = document.getElementById(id);
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                setVal('otherNatHeldFrom_day', '{start_date.day}');
                setVal('otherNatHeldFrom_month', '{start_date.month}');
                setVal('otherNatHeldFrom_year', '{start_date.year}');
            """)
            time.sleep(0.5)
            print(f"[FORM-15b] Baslangic tarihi: {start_date.day}/{start_date.month}/{start_date.year}")

            # Bitis tarihi
            if form.other_nationality_end_date:
                end_date = parse_date_safe(form.other_nationality_end_date, "Diger uyruk bitis")
                driver.execute_script(f"""
                    function setVal(id, val) {{
                        var el = document.getElementById(id);
                        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        setter.call(el, val);
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    setVal('otherNatHeldTo_day', '{end_date.day}');
                    setVal('otherNatHeldTo_month', '{end_date.month}');
                    setVal('otherNatHeldTo_year', '{end_date.year}');
                """)
                print(f"[FORM-15c] Bitis tarihi: {end_date.day}/{end_date.month}/{end_date.year}")
            else:
                # Hala gecerli ise checkbox isaretle, bitis tarihi bos birak
                try:
                    still_held = driver.find_element(By.ID, "confirmNatStillHeld_confirmNatStillHeld")
                    safe_click(driver, still_held)
                    print("[FORM-15c] 'Hala bu uyruktayim' isaretlendi")
                except:
                    print("[FORM-15c] Checkbox bulunamadi, bitis tarihi bos birakiliyor")
            time.sleep(0.5)

            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-15] Diger uyruk detaylari tamamlandi!")

            # Baska uyruk daha var mi - No
            try:
                no_more = wait.until(EC.presence_of_element_located((By.ID, "addAnother_false")))
                safe_click(driver, no_more)
                time.sleep(0.5)
                click_submit(driver, wait)
                time.sleep(3)
                print("[FORM-15] Baska uyruk yok, devam ediliyor.")
            except:
                print("[FORM-15] addAnother sayfasi yok, devam ediliyor.")

        else:
            print("[FORM-15] Baska uyruk YOK, No seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "hasOtherNationality_false"))))
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-15] Tamamlandi!")

    # ===== SAYFA 16: Is durumu =====
    if should_run("employment_status"):
        print("[FORM-16] Is durumu seciliyor...")

        work_status = form.step4.get("boolean_work", "").strip().upper()
        is_own = form.step4.get("own_work", "").strip().upper() == "EVET"
        worker_title = form.work_title.upper()

        if work_status == "CALISIYOR":
            if is_own:
                cb_id = "status_self-employed"
            else:
                cb_id = "status_employed"
        elif "EMEKLI" in worker_title or "RETIRED" in worker_title:
            cb_id = "status_retired"
        elif "OGRENCI" in worker_title or "STUDENT" in worker_title:
            cb_id = "status_student"
        else:
            cb_id = "status_employed"  # varsayilan

        # JS ile checkbox sec
        driver.execute_script(f"""
            var cb = document.getElementById('{cb_id}');
            if (cb && !cb.checked) {{ cb.scrollIntoView({{block:'center'}}); cb.click(); }}
        """)
        print(f"[FORM-16] Secildi: {cb_id}")
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-16] Tamamlandi!")

    # ===== SAYFA 17: Isveren / Serbest meslek detaylari =====
    if should_run("employer_details"):
        work_status = form.step4.get("boolean_work", "").strip().upper()
        is_own = form.step4.get("own_work", "").strip().upper() == "EVET"
        time.sleep(3)

        # Hangi sayfadayiz tespit et - birden fazla deneme
        page_type = "unknown"
        for _try in range(5):
            page_type = driver.execute_script("""
                var url = window.location.href.toLowerCase();
                var f = document.querySelector('form[action]');
                var action = f ? f.getAttribute('action').toLowerCase() : '';
                var combined = url + ' ' + action;
                
                // URL/action'dan tespit
                if (combined.includes('fundingemploymentemployerdetails')) return 'employed';
                if (combined.includes('fundingselfemployment')) return 'self_employed';
                if (combined.includes('fundingretired')) return 'retired';
                if (combined.includes('fundingstudent')) return 'student';
                if (combined.includes('fundingunemployed')) return 'unemployed';
                
                // Element'lerden tespit
                if (document.getElementById('employer')) return 'employed';
                if (document.getElementById('income_currencyRef') || document.getElementById('income_amount')) return 'self_employed';
                if (document.getElementById('jobTitle') && !document.getElementById('employer')) return 'self_employed';
                return 'unknown';
            """)
            if page_type != "unknown":
                break
            time.sleep(2)
        
        print(f"[FORM-17] Sayfa tipi: {page_type}")

        if page_type == "employed":
            print("[FORM-17] Isveren bilgileri giriliyor (Employed)...")

            set_input(driver, "employer", form.work_name or "COMPANY", wait)
            set_input(driver, "address_line1", (form.work_address or form.home_address or "Istanbul")[:80], wait)
            set_input(driver, "address_townCity", form.home_city or "Istanbul", wait)
            set_input(driver, "address_province", form.home_district or form.home_city or "Istanbul", wait)
            set_input(driver, "address_postalCode", form.post_code or "34000", wait)
            set_select(driver, "address_countryRef", "TUR", "Turkey Türkiye")

            # Telefon
            phone_number = clean_phone(form.work_phone or form.phone)
            set_input(driver, "phone_code", "90", wait)
            set_input(driver, "phone_number", phone_number, wait)
            print(f"[FORM-17] Telefon: 90 {phone_number}")

            # Ise baslama tarihi
            start_date = parse_date_safe(form.work_start_date, "Ise baslama")
            if start_date > datetime.now():
                start_date = datetime.now() - relativedelta(years=2)
            set_input(driver, "jobStartDate_month", str(start_date.month))
            set_input(driver, "jobStartDate_year", str(start_date.year))
            print(f"[FORM-17] Ise baslama: {start_date.month}/{start_date.year}")

            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-17] Isveren tamamlandi!")

        elif page_type == "self_employed":
            print("[FORM-17] Serbest meslek bilgileri giriliyor...")

            set_input(driver, "jobTitle", form.work_title or form.work_name or "Business Owner", wait)

            # Gelir - TRY
            set_select(driver, "income_currencyRef", "TRY")
            monthly = form.monthly_income if form.monthly_income else form.monthly_salary
            try:
                yearly = int(str(monthly).replace(".", "").replace(",", "").strip()) * 12
            except:
                yearly = 300000
            if yearly < 1:
                yearly = 300000
            set_input(driver, "income_amount", str(yearly))
            print(f"[FORM-17] Yillik gelir: {yearly} TRY")

            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-17] Serbest meslek tamamlandi!")

        elif page_type in ("retired", "student", "unemployed"):
            print(f"[FORM-17] {page_type} sayfasi, doldurup geciliyor...")
            # Bu sayfalarda genellikle sadece submit yeterli veya minimal alan var
            click_submit(driver, wait)
            time.sleep(3)

        else:
            print("[FORM-17] Bilinmeyen sayfa, tum alanlari doldurup gecmeye calisiliyor...")
            # Sayfadaki tum alanlari doldur
            all_inputs = driver.execute_script("""
                var inputs = document.querySelectorAll('input[type="text"], input[type="number"], input[type="tel"]');
                var ids = [];
                inputs.forEach(function(i) { if (i.id && !i.value) ids.push(i.id); });
                return ids;
            """)
            print(f"[FORM-17] Bos alanlar: {all_inputs}")
            click_submit(driver, wait)
            time.sleep(3)

    # ===== SAYFA 17b: Is tanimi ve aylik kazanc =====
    if should_run("job_details"):
        time.sleep(2)
        if wait_for_page(driver, "fundingEmploymentJobDetails", timeout=5):
            print("[FORM-17b] Is tanimi ve kazanc giriliyor...")

            set_input(driver, "jobTitle", form.work_title or "Employee", wait)
            set_select(driver, "earnings_currencyRef", "TRY")

            monthly = form.monthly_income if form.monthly_income else form.monthly_salary
            try:
                monthly_val = int(str(monthly).replace(".", "").replace(",", "").strip())
                if monthly_val < 1: monthly_val = 25000
            except:
                monthly_val = 25000
            set_input(driver, "earnings_amount", str(monthly_val))

            # Is tanimi
            desc = form.work_title or "Employee"
            if form.work_name:
                desc = f"{desc} at {form.work_name}"
            set_input(driver, "jobDescription", desc[:250], wait)
            print(f"[FORM-17b] Kazanc: {monthly_val} TRY, Tanim: {desc[:50]}")

            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-17b] Tamamlandi!")
        else:
            print("[FORM-17b] Job details sayfasi degil, atlaniyor...")

    # ===== SAYFA 17c: Aylik harcama =====
    if should_run("monthly_outgoings"):
        time.sleep(3)

        # Sayfayi kontrol et
        current_action = driver.execute_script("""
            var f = document.querySelector('form[action]');
            return f ? f.getAttribute('action').toLowerCase() : '';
        """) or ""

        if "monthlyoutgoings" in current_action:
            print("[FORM-17c] Aylik harcama giriliyor...")

            driver.execute_script("""
                var s = document.getElementById('value_currencyRef');
                if (s) {
                    s.value = 'TRY';
                    var opt = s.querySelector('option[value="TRY"]');
                    if (opt) opt.selected = true;
                    s.dispatchEvent(new Event('change', {bubbles: true}));
                }
            """)
            time.sleep(0.5)

            expenditure = form.monthly_expenses
            if expenditure:
                try:
                    outgoing_val = int(str(expenditure).replace(".", "").replace(",", "").strip())
                except:
                    outgoing_val = 15000
            else:
                monthly = form.monthly_income if form.monthly_income else form.monthly_salary
                try:
                    outgoing_val = int(int(str(monthly).replace(".", "").replace(",", "").strip()) * 0.6)
                except:
                    outgoing_val = 15000
            if outgoing_val < 1:
                outgoing_val = 15000

            driver.execute_script(f"""
                var el = document.getElementById('value_amount');
                if (el) {{
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, '{outgoing_val}');
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
            """)
            time.sleep(0.5)
            print(f"[FORM-17c] Harcama: {outgoing_val} TRY")

            url_before = driver.current_url
            driver.execute_script("""
                var form = document.querySelector('form');
                if (form) HTMLFormElement.prototype.submit.call(form);
            """)
            time.sleep(3)
            try:
                if driver.current_url == url_before:
                    click_submit(driver, wait)
                    time.sleep(3)
            except:
                pass
            print("[FORM-17c] Tamamlandi!")
        else:
            # Site bu sayfalari atladi, FORM-18 (otherIncome) sayfasindayiz
            print(f"[FORM-17c] Site monthlyOutgoings atlamis (mevcut: {current_action[-40:]}), devam ediliyor...")

    # ===== SAYFA 18: Ek gelir / Birikim =====
    if should_run("other_income"):
        print("[FORM-18] Ek gelir ve birikim bilgileri giriliyor...")

        has_savings = form.has_savings
        savings_type = form.savings_type.upper()
        monthly_income = form.monthly_income
        monthly_salary = form.monthly_salary
        sideline = form.step4.get("sideline", "").strip().upper()

        # En az bir sey secilecek mi?
        will_select_something = False

        # --- 1) Regular income (yan gelir / yatirim / kira) ---
        has_sideline = sideline in ("VAR", "EVET")
        has_investment = savings_type in ("YATIRIM", "INVESTMENTS", "KIRA GELIRI", "RENT", "KIRA")

        if has_sideline or has_investment:
            will_select_something = True
            print("[FORM-18a] Ek duzeli gelir var, 'Regular income' seciliyor...")
            reg_cb = wait.until(EC.presence_of_element_located((By.ID, "typeOfIncomeRefs_regularIncome")))
            if not reg_cb.is_selected():
                safe_click(driver, reg_cb)
            time.sleep(1)

            # Gelir turunu sec
            if has_investment:
                inv_cb = wait.until(EC.presence_of_element_located((By.ID, "sourceRefs_investments")))
                if not inv_cb.is_selected():
                    safe_click(driver, inv_cb)
                print("[FORM-18a] Investments secildi")
            elif has_sideline:
                other_cb = wait.until(EC.presence_of_element_located((By.ID, "sourceRefs_other")))
                if not other_cb.is_selected():
                    safe_click(driver, other_cb)
                print("[FORM-18a] Another income secildi")
            time.sleep(0.5)

            # Para birimi TRY ve yillik gelir
            driver.execute_script("""
                var s = document.getElementById('income_currencyRef');
                s.value = 'TRY';
                s.dispatchEvent(new Event('change', {bubbles: true}));
            """)
            time.sleep(0.3)

            # Yillik ek gelir hesapla
            income_source = monthly_income if monthly_income else monthly_salary
            try:
                monthly_val = int(str(income_source).replace(".", "").replace(",", "").strip())
                yearly_extra = monthly_val * 12
            except:
                yearly_extra = 100000

            driver.execute_script(f"""
                var el = document.getElementById('income_amount');
                var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, '{yearly_extra}');
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            """)
            print(f"[FORM-18b] Yillik ek gelir: {yearly_extra} TRY")
            time.sleep(0.5)

        # --- 2) Savings (birikim) ---
        if has_savings:
            will_select_something = True
            print("[FORM-18c] Birikim var, 'Savings' seciliyor...")
            savings_cb = wait.until(EC.presence_of_element_located((By.ID, "typeOfIncomeRefs_moneyInBank")))
            if not savings_cb.is_selected():
                safe_click(driver, savings_cb)
            time.sleep(1)

            # GBP sec
            driver.execute_script("""
                var s = document.getElementById('moneyInBankAmount_currencyRef');
                s.value = 'GBP';
                s.dispatchEvent(new Event('change', {bubbles: true}));
            """)
            time.sleep(0.3)

            # Birikim miktari - CRM'den al veya hesapla
            actual_savings = form.savings_amount  # JSON'dan gelen gercek birikim
            if actual_savings > 0:
                # TRY->GBP kabaca 1/30
                savings_gbp = int(actual_savings / 30)
            else:
                income_source = monthly_income if monthly_income else monthly_salary
                try:
                    monthly_val = int(str(income_source).replace(".", "").replace(",", "").strip())
                    savings_gbp = int(monthly_val * 6 / 30)  # Kabaca TRY->GBP
                except:
                    savings_gbp = 5000

            if savings_gbp < 1000:
                savings_gbp = 5000

            driver.execute_script(f"""
                var el = document.getElementById('moneyInBankAmount_amount');
                var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, '{savings_gbp}');
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            """)
            print(f"[FORM-18d] Birikim: {savings_gbp} GBP")
            time.sleep(0.5)

        # --- 3) Hicbir sey yoksa ---
        if not will_select_something:
            print("[FORM-18] Gelir/birikim yok, 'No other income' seciliyor...")
            no_income = wait.until(EC.presence_of_element_located((By.ID, "hasNoOtherIncome")))
            if not no_income.is_selected():
                safe_click(driver, no_income)
            time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-18] Ek gelir/birikim tamamlandi!")

    # ===== SAYFA 19: UK'da harcama plani =====
    if should_run("planned_spend"):
        time.sleep(2)
        
        # Dogru sayfada miyiz?
        current_action = driver.execute_script("""
            var f = document.querySelector('form[action]');
            return f ? f.getAttribute('action').toLowerCase() : '';
        """) or ""
        
        if "plannedspendonvisit" in current_action or "plannedspend" in current_action:
            print("[FORM-19] UK harcama plani giriliyor...")

            # Para birimi GBP - JS ile
            driver.execute_script("""
                var s = document.getElementById('value_currencyRef');
                if (s) {
                    s.value = 'GBP';
                    var opt = s.querySelector('option[value="GBP"]');
                    if (opt) opt.selected = true;
                    s.dispatchEvent(new Event('change', {bubbles: true}));
                }
            """)
            time.sleep(0.5)

            # Sabit 750 GBP - JS nativeInputValueSetter ile
            driver.execute_script("""
                var el = document.getElementById('value_amount');
                if (el) {
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, '750');
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                }
            """)
            time.sleep(0.5)
            print("[FORM-19] Harcama: 750 GBP (sabit)")

            # Submit - HTMLFormElement.prototype.submit
            url_before = driver.current_url
            driver.execute_script("""
                var form = document.querySelector('form');
                if (form) HTMLFormElement.prototype.submit.call(form);
            """)
            time.sleep(3)
            
            try:
                if driver.current_url == url_before:
                    click_submit(driver, wait)
                    time.sleep(3)
            except:
                pass
            print("[FORM-19] Harcama plani tamamlandi!")
        else:
            print(f"[FORM-19] plannedSpend sayfasi degil (mevcut: {current_action[-40:]}), atlaniyor...")

    # ===== SAYFA 20: Seyahat tarihleri =====
    if should_run("travel_dates"):
        time.sleep(3)
        
        # Sayfa kontrolu
        found_page = wait_for_page(driver, "plannedTravelInformation", timeout=5)
        if not found_page:
            found_page = driver.execute_script("return document.getElementById('dateOfArrival_day') !== null;")
        
        if found_page:
            print("[FORM-20] Seyahat tarihleri giriliyor...")

            now = datetime.now()

            # Varis tarihi
            arrival = parse_date_safe(form.travel_start_date, "Varis tarihi")
            if arrival < now + relativedelta(days=14):
                arrival = now + relativedelta(months=1)
            max_arrival = now + relativedelta(months=5)
            if arrival > max_arrival:
                arrival = now + relativedelta(months=1)

            # Cikis tarihi
            departure = parse_date_safe(form.travel_end_date, "Cikis tarihi")
            if departure <= arrival + relativedelta(days=1):
                departure = arrival + relativedelta(days=7)
            max_departure = arrival + relativedelta(months=5, days=28)
            if departure > max_departure:
                departure = arrival + relativedelta(days=14)

            print(f"[FORM-20] Hedef: Varis={arrival.day}/{arrival.month}/{arrival.year} Cikis={departure.day}/{departure.month}/{departure.year}")

            # YONTEM: send_keys ile yaz (number input icin en guvenilir)
            date_fields = [
                ("dateOfArrival_day", str(arrival.day)),
                ("dateOfArrival_month", str(arrival.month)),
                ("dateOfArrival_year", str(arrival.year)),
                ("dateOfLeave_day", str(departure.day)),
                ("dateOfLeave_month", str(departure.month)),
                ("dateOfLeave_year", str(departure.year)),
            ]
            for field_id, val in date_fields:
                try:
                    el = wait.until(EC.presence_of_element_located((By.ID, field_id)))
                    # Once JS ile temizle
                    driver.execute_script("arguments[0].value = '';", el)
                    time.sleep(0.1)
                    # Click + focus
                    safe_click(driver, el)
                    time.sleep(0.1)
                    # send_keys
                    el.send_keys(val)
                    time.sleep(0.2)
                except Exception as e:
                    print(f"[FORM-20] {field_id} send_keys hatasi: {e}")
                    # JS fallback
                    try:
                        driver.execute_script(f"""
                            var el = document.getElementById('{field_id}');
                            if (el) {{
                                el.value = '{val}';
                                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                            }}
                        """)
                    except:
                        pass

            time.sleep(0.5)

            # Dogrulama
            vals = driver.execute_script("""
                return [
                    document.getElementById('dateOfArrival_day').value,
                    document.getElementById('dateOfArrival_month').value,
                    document.getElementById('dateOfArrival_year').value,
                    document.getElementById('dateOfLeave_day').value,
                    document.getElementById('dateOfLeave_month').value,
                    document.getElementById('dateOfLeave_year').value
                ];
            """)
            print(f"[FORM-20] Dogrulama: {vals}")

            # Hala bos alanlar varsa, direkt value= ile dene
            for i, (field_id, val) in enumerate(date_fields):
                if not vals[i]:
                    print(f"[FORM-20] {field_id} bos, direkt value ataniyor...")
                    driver.execute_script(f"""
                        var el = document.getElementById('{field_id}');
                        el.value = '{val}';
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                        el.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    """)

            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-20] Seyahat tarihleri tamamlandi!")
        else:
            cur = driver.execute_script("var f=document.querySelector('form[action]'); return f?f.getAttribute('action'):'';") or ""
            print(f"[FORM-20] Seyahat tarihleri sayfasi degil (mevcut: {cur[-50:]}), atlaniyor...")

    # ===== SAYFA 21: Masraflari baskasi odeyecek mi =====
    if should_run("paying_visit"):
        time.sleep(2)

        # Dogru sayfada miyiz kontrol et - yoksa bekle
        for _wait_attempt in range(5):
            is_correct_page = driver.execute_script("""
                var forms = document.querySelectorAll('form');
                for (var i = 0; i < forms.length; i++) {
                    var action = (forms[i].getAttribute('action') || '').toLowerCase();
                    if (action.includes('payingforyourvisit')) return true;
                }
                var container = document.getElementById('payingForYourVisit');
                return container !== null;
            """)
            if is_correct_page:
                break
            print(f"[FORM-21] Sayfa yuklenmedi, bekleniyor... ({_wait_attempt+1}/5)")
            time.sleep(2)

        if not is_correct_page:
            print("[FORM-21] Masraf odeme sayfasi degil, atlaniyor...")
        else:
            print("[FORM-21] Masraf odeme durumu...")

            # CRM verilerini kontrol et
            boolean_cover = form.step5.get("boolean_cover_expenses", "").strip().upper()
            who_covers = form.step5.get("who_cover_expenses", "").strip()
            cover_reason = form.step5.get("cover_expenses_reason", "").strip()
            cover_address = form.step5.get("cover_expenses_address", "").strip()

            # Baskasi oduyor senaryosu: explicit HAYIR + sponsor bilgisi varsa
            someone_else_pays = (
                boolean_cover == "HAYIR" and
                (who_covers or cover_reason or cover_address)
            )

            if not someone_else_pays:
                # VARSAYILAN: Kendisi oduyor - No (guvenli)
                print("[FORM-21] Kendisi oduyor (varsayilan), 'No' seciliyor...")
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_false"))))
                time.sleep(0.5)
                click_submit(driver, wait)
                time.sleep(3)
            else:
                # Baskasi oduyor - Yes + detaylar
                print("[FORM-21] Baskasi oduyor, 'Yes' seciliyor...")
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_true"))))
                time.sleep(0.5)
                click_submit(driver, wait)
                time.sleep(3)

                # Sponsor detaylari sayfasi
                print("[FORM-21a] Sponsor detaylari giriliyor...")

                # Kim oduyor
                who_upper = who_covers.upper()
                if who_upper in ("ISVEREN", "EMPLOYER", "SIRKET", "COMPANY"):
                    safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "whoIsPayingRef_myEmployerOrCompany"))))
                    print("[FORM-21a] Isveren/Sirket secildi")
                else:
                    safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "whoIsPayingRef_someoneIKnow"))))
                    print("[FORM-21a] Tanidik biri secildi")
                    time.sleep(1)

                # Sponsor isim
                sponsor_name = form.step5.get("cover_expenses_reason", "").strip()
                if not sponsor_name:
                    sponsor_name = form.partner_name if form.partner_name else form.full_name

                payee_name = wait.until(EC.presence_of_element_located((By.ID, "payeeName")))
                payee_name.clear()
                payee_name.send_keys(sponsor_name[:255])
                print(f"[FORM-21b] Sponsor ismi: {sponsor_name}")
                time.sleep(0.3)

                # Sponsor adres
                sponsor_addr = form.step5.get("cover_expenses_address", "").strip()
                if not sponsor_addr:
                    sponsor_addr = form.home_address

                addr1 = wait.until(EC.presence_of_element_located((By.ID, "address_line1")))
                addr1.clear()
                addr1.send_keys(sponsor_addr[:80])
                time.sleep(0.3)

                town = wait.until(EC.presence_of_element_located((By.ID, "address_townCity")))
                town.clear()
                town.send_keys(form.home_city)
                time.sleep(0.3)

                province = wait.until(EC.presence_of_element_located((By.ID, "address_province")))
                province.clear()
                province.send_keys(form.home_district if form.home_district else form.home_city)
                time.sleep(0.3)

                postal = wait.until(EC.presence_of_element_located((By.ID, "address_postalCode")))
                postal.clear()
                postal.send_keys(form.post_code)
                time.sleep(0.3)

                # Ulke Turkey - JS
                driver.execute_script("""
                    var s = document.getElementById('address_countryRef');
                    s.value = 'TUR';
                    s.dispatchEvent(new Event('change', {bubbles: true}));
                    var ui = document.getElementById('address_countryRef_ui');
                    if (ui) ui.value = 'Turkey Türkiye';
                """)
                time.sleep(0.5)

                # Miktar - GBP
                driver.execute_script("""
                    var s = document.getElementById('amount_currencyRef');
                    s.value = 'GBP';
                    s.dispatchEvent(new Event('change', {bubbles: true}));
                """)
                time.sleep(0.3)

                spend = form.spend_pounds
                try:
                    amount_val = int(str(spend).replace(".", "").replace(",", "").replace("£", "").replace("GBP", "").strip())
                except:
                    amount_val = 1000

                driver.execute_script(f"""
                    var el = document.getElementById('amount_amount');
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, '{amount_val}');
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                """)
                print(f"[FORM-21c] Miktar: {amount_val} GBP")
                time.sleep(0.3)

                # Neden oduyorlar
                reason_input = wait.until(EC.presence_of_element_located((By.ID, "reason")))
                reason_input.clear()
                reason_text = form.step5.get("cover_expenses_reason", "").strip()
                if not reason_text:
                    reason_text = "Family member supporting my visit"
                reason_input.send_keys(reason_text[:500])
                print(f"[FORM-21d] Neden: {reason_text[:50]}...")
                time.sleep(0.3)

                click_submit(driver, wait)
                time.sleep(3)

        print("[FORM-21] Masraf odeme tamamlandi!")

    # ===== SAYFA 22: Dil tercihi =====
    if should_run("language_pref"):
        try:
            print("[FORM-22] Dil tercihi seciliyor...")
            set_radio(driver, "preferredLanguage_english")
            print("[FORM-22] Dil: English")
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-22] Dil tercihi tamamlandi!")
        except Exception as e:
            print(f"[FORM-22] Hata: {e} - devam ediliyor...")

    # ===== SAYFA 23: Ziyaret amaci =====
    if should_run("visit_purpose"):
        try:
            print("[FORM-23] Ziyaret amaci seciliyor...")

            travel_reason = form.travel_reason.upper()

            purpose_map = {
                "TURISTIK": "purposeRef_tourism",
                "TOURISM": "purposeRef_tourism",
                "TURIZM": "purposeRef_tourism",
                "IS": "purposeRef_business",
                "BUSINESS": "purposeRef_business",
                "ISAYAHAT": "purposeRef_business",
                "FUAR": "purposeRef_business",
                "TRANSIT": "purposeRef_transit",
                "AKADEMIK": "purposeRef_academic",
                "ACADEMIC": "purposeRef_academic",
                "EVLILIK": "purposeRef_marriage",
                "MARRIAGE": "purposeRef_marriage",
                "TEDAVI": "purposeRef_medicalTreatment",
                "MEDICAL": "purposeRef_medicalTreatment",
                "EGITIM": "purposeRef_study",
                "STUDY": "purposeRef_study",
                "DIGER": "purposeRef_other",
                "OTHER": "purposeRef_other",
            }

            radio_id = purpose_map.get(travel_reason, "purposeRef_tourism")
            set_radio(driver, radio_id)
            print(f"[FORM-23] Amac secildi: {travel_reason} -> {radio_id}")

            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-23] Ziyaret amaci tamamlandi!")
        except Exception as e:
            print(f"[FORM-23] Hata: {e} - devam ediliyor...")

    # ===== SAYFA 24: Ziyaret alt amaci (amaca gore degisir) =====
    if should_run("visit_sub_purpose"):
        try:
            travel_reason = form.travel_reason.upper()
            print(f"[FORM-24] Ziyaret alt amaci seciliyor (ana amac: {travel_reason})...")

            if travel_reason in ("TURISTIK", "TOURISM", "TURIZM"):
                if form.has_family_in_uk:
                    set_radio(driver, "purposeRef_visitingFamily")
                    print("[FORM-24] Visiting family secildi")
                elif form.has_invitation:
                    set_radio(driver, "purposeRef_visitingFriends")
                    print("[FORM-24] Visiting friends secildi")
                else:
                    set_radio(driver, "purposeRef_tourist")
                    print("[FORM-24] Tourist secildi")

            elif travel_reason in ("IS", "BUSINESS", "FUAR", "ISAYAHAT"):
                set_radio(driver, "purposeRef_meeting")
                print("[FORM-24] Business meeting secildi")

            elif travel_reason == "TRANSIT":
                set_radio(driver, "purposeRef_visitorInTransit")
                print("[FORM-24] Transit secildi")

            elif travel_reason in ("AKADEMIK", "ACADEMIC"):
                set_radio(driver, "purposeRef_research")
                print("[FORM-24] Research secildi")

            elif travel_reason in ("EGITIM", "STUDY"):
                set_radio(driver, "enrolledInUKCourse_false")
                time.sleep(1)
                set_radio(driver, "courseNotLongerThan30Days_true")
                print("[FORM-24] Study <= 30 days secildi")

            elif travel_reason in ("EVLILIK", "MARRIAGE"):
                print("[FORM-24] Evlilik bilgileri giriliyor...")
                partner_parts = form.partner_name.split() if form.partner_name else ["PARTNER"]
                set_input(driver, "givenName", partner_parts[0], wait)
                set_input(driver, "familyName", " ".join(partner_parts[1:]) if len(partner_parts) > 1 else "UNKNOWN", wait)
                set_input(driver, "passportNumber", form.partner_passport or "UNKNOWN", wait)
                set_select(driver, "nationalityRef", "TUR", "Turkey Türkiye")

            else:
                set_radio(driver, "purposeRef_tourist")
                print("[FORM-24] Varsayilan: Tourist")

            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-24] Alt amac tamamlandi!")
        except Exception as e:
            print(f"[FORM-24] Hata: {e} - devam ediliyor...")

    # ===== SAYFA 25: Ziyaret hakkinda detay =====
    if should_run("about_visit"):
        print("[FORM-25] Ziyaret detayi giriliyor...")
        try:
            details = wait.until(EC.presence_of_element_located((By.ID, "details")))
            details.clear()
            details.send_keys("I WANT TO MAKE A TOURISTIC TRIP TO LONDON")
            print("[FORM-25] Detay: I WANT TO MAKE A TOURISTIC TRIP TO LONDON")
            time.sleep(0.3)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-25] Tamamlandi!")
        except:
            print("[FORM-25] Detay sayfasi bulunamadi, atlaniyor...")

    # ===== SAYFA 26: Bakmakla yukumlu kisi var mi =====
    if should_run("has_dependants"):
        time.sleep(2)

        # Sayfa bekleme dongusu
        for _w in range(5):
            is_correct_page = driver.execute_script("""
                var forms = document.querySelectorAll('form');
                for (var i = 0; i < forms.length; i++) {
                    var action = (forms[i].getAttribute('action') || '').toLowerCase();
                    if (action.includes('hasdependants')) return true;
                }
                return document.getElementById('hasDependants') !== null;
            """)
            if is_correct_page:
                break
            time.sleep(2)

        if not is_correct_page:
            print("[FORM-26] Dependants sayfasi degil, atlaniyor...")
        else:
            print("[FORM-26] Bakmakla yukumlu kisi sorgusu...")

            # CRM'den dependents kontrolu
            has_deps = form.step4.get("hasDependents", "").strip().upper() == "EVET"
            dep_count = form.step4.get("dependentCount", 0)
            has_children = form.has_children

            if has_deps or has_children or (dep_count and int(dep_count) > 0):
                radio_id = "value_true"
                print("[FORM-26] Bakmakla yukumlu kisi VAR, Yes seciliyor...")
            else:
                radio_id = "value_false"
                print("[FORM-26] Bakmakla yukumlu kisi YOK, No seciliyor...")

            # JS ile radio sec (safe_click bazen calismaz)
            driver.execute_script(f"""
                var radio = document.getElementById('{radio_id}');
                if (radio) {{
                    radio.scrollIntoView({{block: 'center'}});
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change', {{bubbles: true}}));
                    radio.click();
                }}
            """)
            time.sleep(0.5)

            # Dogrulama
            is_selected = driver.execute_script(f"return document.getElementById('{radio_id}').checked;")
            if not is_selected:
                print(f"[FORM-26] JS ile secilemedi, safe_click deneniyor...")
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, radio_id))))
                time.sleep(0.5)

            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-26] Bakmakla yukumlu kisi tamamlandi!")

            # Eger Yes secildiyse dependant detay sayfasi acilir - doldur
            try:
                time.sleep(1)
                is_dep_detail = driver.execute_script("""
                    var forms = document.querySelectorAll('form');
                    for (var i = 0; i < forms.length; i++) {
                        var action = (forms[i].getAttribute('action') || '').toLowerCase();
                        if (action.includes('dependantslist')) return true;
                    }
                    return document.getElementById('dependantDetails') !== null;
                """)
                if is_dep_detail:
                    print("[FORM-26b] Dependant detay sayfasi acildi, dolduruluyor...")

                    # Iliski
                    driver.execute_script("""
                        var el = document.getElementById('relationship');
                        if (el) { el.value = 'Spouse'; el.dispatchEvent(new Event('change', {bubbles: true})); }
                    """)

                    # Isim soyisim - partner bilgilerini kullan
                    partner_full = form.partner_name if form.partner_name else "UNKNOWN UNKNOWN"
                    parts = partner_full.split()
                    given = " ".join(parts[:-1]) if len(parts) > 1 else parts[0]
                    family = parts[-1] if len(parts) > 1 else "UNKNOWN"

                    driver.execute_script(f"""
                        var g = document.getElementById('givenName');
                        if (g) {{ g.value = '{given}'; g.dispatchEvent(new Event('change', {{bubbles: true}})); }}
                        var f = document.getElementById('familyName');
                        if (f) {{ f.value = '{family}'; f.dispatchEvent(new Event('change', {{bubbles: true}})); }}
                    """)

                    # Dogum tarihi
                    partner_dob = parse_date_safe(form.partner_birth_date, "Dep dogum")
                    for fid, val in [("dateOfBirth_day", str(partner_dob.day)), ("dateOfBirth_month", str(partner_dob.month)), ("dateOfBirth_year", str(partner_dob.year))]:
                        try:
                            el = driver.find_element(By.ID, fid)
                            driver.execute_script("arguments[0].value = '';", el)
                            safe_click(driver, el)
                            el.send_keys(val)
                            time.sleep(0.1)
                        except:
                            driver.execute_script(f"var e=document.getElementById('{fid}'); if(e){{e.value='{val}'; e.dispatchEvent(new Event('change',{{bubbles:true}}));}}")

                    # Birlikte yasiyor - Yes
                    driver.execute_script("""
                        var r = document.getElementById('livingWithApplicant_true');
                        if (r) { r.checked = true; r.click(); r.dispatchEvent(new Event('change', {bubbles: true})); }
                    """)
                    time.sleep(0.5)

                    # Seyahat - No
                    driver.execute_script("""
                        var r = document.getElementById('travelling_false');
                        if (r) { r.checked = true; r.click(); r.dispatchEvent(new Event('change', {bubbles: true})); }
                    """)
                    time.sleep(0.5)

                    click_submit(driver, wait)
                    time.sleep(3)
                    print("[FORM-26b] Dependant detay tamamlandi!")

                    # Baska dependant ekle - No
                    try:
                        time.sleep(1)
                        has_add = driver.find_element(By.ID, "addAnother_false")
                        if has_add:
                            driver.execute_script("""
                                var r = document.getElementById('addAnother_false');
                                if (r) { r.checked = true; r.click(); r.dispatchEvent(new Event('change', {bubbles: true})); }
                            """)
                            time.sleep(0.5)
                            click_submit(driver, wait)
                            time.sleep(3)
                            print("[FORM-26c] Baska dependant: No")
                    except:
                        pass
            except:
                pass

    # ===== SAYFA 27: Ebeveyn 1 (Baba) =====
    if should_run("parent_one"):
        print("[FORM-27] Ebeveyn 1 (Baba) bilgileri giriliyor...")

        # Iliski - Father (JS ile)
        driver.execute_script("""
            var r = document.getElementById('parent_relationshipRef_father');
            if (r) { r.checked = true; r.click(); r.dispatchEvent(new Event('change', {bubbles: true})); }
        """)
        time.sleep(0.5)

        # Isim
        father_name = form.father_name
        if father_name:
            parts = father_name.split()
            given = parts[0] if parts else "UNKNOWN"
            family = " ".join(parts[1:]) if len(parts) > 1 else form.last_name
        else:
            given = "UNKNOWN"
            family = form.last_name

        given_input = wait.until(EC.presence_of_element_located((By.ID, "parent_givenName")))
        given_input.clear()
        given_input.send_keys(given)
        time.sleep(0.3)

        family_input = wait.until(EC.presence_of_element_located((By.ID, "parent_familyName")))
        family_input.clear()
        family_input.send_keys(family)
        print(f"[FORM-27a] Baba: {given} {family}")
        time.sleep(0.3)

        # Dogum tarihi - send_keys ile
        father_dob = parse_date_safe(form.father_birth_date, "Baba dogum tarihi")
        for fid, val in [("parent_dateOfBirth_day", str(father_dob.day)), ("parent_dateOfBirth_month", str(father_dob.month)), ("parent_dateOfBirth_year", str(father_dob.year))]:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, fid)))
                driver.execute_script("arguments[0].value = '';", el)
                safe_click(driver, el)
                time.sleep(0.1)
                el.send_keys(val)
                time.sleep(0.2)
            except:
                driver.execute_script(f"var e=document.getElementById('{fid}'); if(e){{e.value='{val}'; e.dispatchEvent(new Event('change',{{bubbles:true}}));}}")
        print(f"[FORM-27b] Baba dogum: {father_dob.day}/{father_dob.month}/{father_dob.year}")
        time.sleep(0.5)

        # Uyruk - Turkey JS
        father_nat = form.father_nationality.upper()
        nat_code = "TUR" if father_nat in ("TURKEY", "TURKIYE", "TUR", "") else father_nat
        driver.execute_script(f"""
            var s = document.getElementById('parent_nationalityRef');
            s.value = '{nat_code}';
            s.dispatchEvent(new Event('change', {{bubbles: true}}));
            var ui = document.getElementById('parent_nationalityRef_ui');
            if (ui) {{
                var opt = s.querySelector('option[value="{nat_code}"]');
                if (opt) ui.value = opt.textContent.trim();
                else ui.value = 'Turkey Türkiye';
            }}
        """)
        print(f"[FORM-27c] Baba uyruk: {nat_code}")
        time.sleep(0.5)

        # Hep ayni uyruk mu - Yes (JS ile)
        driver.execute_script("""
            var r = document.getElementById('parent_hadAlwaysSameNationality_true');
            if (r) { r.checked = true; r.click(); r.dispatchEvent(new Event('change', {bubbles: true})); }
        """)
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-27] Ebeveyn 1 (Baba) tamamlandi!")

    # ===== SAYFA 28: Ebeveyn 2 (Anne) =====
    if should_run("parent_two"):
        print("[FORM-28] Ebeveyn 2 (Anne) bilgileri giriliyor...")

        # Iliski - Mother (JS ile)
        driver.execute_script("""
            var r = document.getElementById('parent_relationshipRef_mother');
            if (r) { r.checked = true; r.click(); r.dispatchEvent(new Event('change', {bubbles: true})); }
        """)
        time.sleep(0.5)

        # Isim
        mother_name = form.mother_name
        if mother_name:
            parts = mother_name.split()
            given = parts[0] if parts else "UNKNOWN"
            family = " ".join(parts[1:]) if len(parts) > 1 else form.last_name
        else:
            given = "UNKNOWN"
            family = form.last_name

        given_input = wait.until(EC.presence_of_element_located((By.ID, "parent_givenName")))
        given_input.clear()
        given_input.send_keys(given)
        time.sleep(0.3)

        family_input = wait.until(EC.presence_of_element_located((By.ID, "parent_familyName")))
        family_input.clear()
        family_input.send_keys(family)
        print(f"[FORM-28a] Anne: {given} {family}")
        time.sleep(0.3)

        # Dogum tarihi - send_keys ile
        mother_dob = parse_date_safe(form.mother_birth_date, "Anne dogum tarihi")
        for fid, val in [("parent_dateOfBirth_day", str(mother_dob.day)), ("parent_dateOfBirth_month", str(mother_dob.month)), ("parent_dateOfBirth_year", str(mother_dob.year))]:
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, fid)))
                driver.execute_script("arguments[0].value = '';", el)
                safe_click(driver, el)
                time.sleep(0.1)
                el.send_keys(val)
                time.sleep(0.2)
            except:
                driver.execute_script(f"var e=document.getElementById('{fid}'); if(e){{e.value='{val}'; e.dispatchEvent(new Event('change',{{bubbles:true}}));}}")
        print(f"[FORM-28b] Anne dogum: {mother_dob.day}/{mother_dob.month}/{mother_dob.year}")
        time.sleep(0.5)

        # Uyruk - Turkey JS
        mother_nat = form.mother_nationality.upper()
        nat_code = "TUR" if mother_nat in ("TURKEY", "TURKIYE", "TUR", "") else mother_nat
        driver.execute_script(f"""
            var s = document.getElementById('parent_nationalityRef');
            s.value = '{nat_code}';
            s.dispatchEvent(new Event('change', {{bubbles: true}}));
            var ui = document.getElementById('parent_nationalityRef_ui');
            if (ui) {{
                var opt = s.querySelector('option[value="{nat_code}"]');
                if (opt) ui.value = opt.textContent.trim();
                else ui.value = 'Turkey Türkiye';
            }}
        """)
        print(f"[FORM-28c] Anne uyruk: {nat_code}")
        time.sleep(0.5)

        # Hep ayni uyruk mu - Yes (JS ile)
        driver.execute_script("""
            var r = document.getElementById('parent_hadAlwaysSameNationality_true');
            if (r) { r.checked = true; r.click(); r.dispatchEvent(new Event('change', {bubbles: true})); }
        """)
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-28] Ebeveyn 2 (Anne) tamamlandi!")

    # ===== SAYFA 29: UK'da aile var mi =====
    if should_run("family_in_uk"):
        print("[FORM-29] UK'da aile var mi...")

        has_family = form.has_family_in_uk

        if has_family:
            print("[FORM-29] UK'da aile VAR, Yes seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_true"))))
        else:
            print("[FORM-29] UK'da aile YOK, No seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_false"))))
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-29] UK'da aile tamamlandi!")

    # ===== SAYFA 30: Grup seyahati =====
    if should_run("travelling_group"):
        print("[FORM-30] Grup seyahati sorusu...")

        # Hayir sec
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "isTravellingWithOtherPeople_false"))))
        print("[FORM-30] Grup seyahati: No")
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-30] Grup seyahati tamamlandi!")

    # ===== SAYFA 31: Baska biriyle seyahat =====
    if should_run("travelling_companion"):
        print("[FORM-31] Baska biriyle seyahat sorusu...")

        # No sec
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "isTravellingWithSomeOneNotPartnerOrSpouse_false"))))
        print("[FORM-31] Baska biriyle seyahat: No")
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-31] Baska biriyle seyahat tamamlandi!")

    # ===== SAYFA 32: Konaklama =====
    if should_run("accommodation"):
        print("[FORM-32] Konaklama bilgileri...")

        # UK'da konaklama adresi var mi?
        uk_address = form.step5.get("uk_address", "").strip()
        uk_hotel = form.step5.get("uk_hotel", "").strip()
        
        # Gercek bir adres mi yoksa sadece sehir mi? (en az 2 kelime ve numara icermeli)
        import re
        is_real_address = False
        check_addr = uk_hotel if uk_hotel else uk_address
        if check_addr:
            word_count = len(check_addr.split())
            has_number = bool(re.search(r'\d', check_addr))
            # En az 3 kelime veya icerisinde numara varsa gercek adres sayalim
            is_real_address = word_count >= 3 or has_number

        if is_real_address:
            # Evet - adres var
            print("[FORM-32a] Konaklama adresi VAR, Yes seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_true"))))
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)

            # Konaklama detay sayfasi
            print("[FORM-32b] Konaklama detaylari giriliyor...")

            # Nerede kalacak
            stay_name = uk_hotel if uk_hotel else uk_address[:40]
            name_input = wait.until(EC.presence_of_element_located((By.ID, "name")))
            name_input.clear()
            name_input.send_keys(stay_name[:255])
            print(f"[FORM-32b] Konaklama yeri: {stay_name}")
            time.sleep(0.3)

            # Adres
            addr1 = wait.until(EC.presence_of_element_located((By.ID, "accommodationDetails_address_line1")))
            addr1.clear()
            addr1.send_keys(uk_address[:44] if uk_address else stay_name[:44])
            time.sleep(0.3)

            # Sehir
            uk_city = form.step5.get("uk_city", "").strip()
            town = wait.until(EC.presence_of_element_located((By.ID, "accommodationDetails_address_townCity")))
            town.clear()
            town.send_keys(uk_city[:44] if uk_city else "London")
            time.sleep(0.3)

            # Posta kodu
            uk_postcode = form.step5.get("uk_postcode", "").strip()
            postcode = wait.until(EC.presence_of_element_located((By.ID, "accommodationDetails_address_postCode")))
            postcode.clear()
            postcode.send_keys(uk_postcode[:10] if uk_postcode else "SW1A 1AA")
            time.sleep(0.3)

            # Varis tarihi
            arrival = parse_date_safe(form.travel_start_date, "Konaklama varis")
            if arrival < datetime.now():
                arrival = datetime.now() + relativedelta(months=1)

            departure = parse_date_safe(form.travel_end_date, "Konaklama cikis")
            if departure <= arrival:
                departure = arrival + relativedelta(days=7)

            driver.execute_script(f"""
                function setVal(id, val) {{
                    var el = document.getElementById(id);
                    if (!el) return;
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                setVal('accommodationDetails_dateRange_from_day', '{arrival.day}');
                setVal('accommodationDetails_dateRange_from_month', '{arrival.month}');
                setVal('accommodationDetails_dateRange_from_year', '{arrival.year}');
                setVal('accommodationDetails_dateRange_to_day', '{departure.day}');
                setVal('accommodationDetails_dateRange_to_month', '{departure.month}');
                setVal('accommodationDetails_dateRange_to_year', '{departure.year}');
            """)
            print(f"[FORM-32c] Tarih: {arrival.day}/{arrival.month}/{arrival.year} - {departure.day}/{departure.month}/{departure.year}")
            time.sleep(0.5)

            click_submit(driver, wait)
            time.sleep(3)

            # Baska konaklama ekle - No
            try:
                no_more = wait.until(EC.presence_of_element_located((By.ID, "addAnother_false")))
                safe_click(driver, no_more)
                time.sleep(0.5)
                click_submit(driver, wait)
                time.sleep(3)
                print("[FORM-32d] Baska konaklama yok.")
            except:
                print("[FORM-32d] addAnother sayfasi yok, devam ediliyor.")

        else:
            # Hayir - adres yok, plan yaz
            print("[FORM-32a] Konaklama adresi YOK, No seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_false"))))
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)

            # Plan sayfasi
            print("[FORM-32b] Konaklama plani yaziliyor...")
            try:
                plans = wait.until(EC.presence_of_element_located((By.ID, "plans")))
                plans.clear()
                plans.send_keys("IF MY VISA IS APPROVED, I WILL ARRANGE MY ACCOMMODATION")
                print("[FORM-32b] Plan: IF MY VISA IS APPROVED, I WILL ARRANGE MY ACCOMMODATION")
                time.sleep(0.3)
                click_submit(driver, wait)
                time.sleep(3)
            except:
                print("[FORM-32b] Plans sayfasi bulunamadi, devam ediliyor.")

        print("[FORM-32] Konaklama tamamlandi!")

    # ===== SAYFA 33: Son 10 yilda UK'ya gittin mi =====
    if should_run("uk_travel_history"):
        print("[FORM-33] UK seyahat gecmisi...")

        # CRM'den UK ziyaret bilgisi
        has_uk_visit = form.step5.get("uk_visited_last10", "").strip().upper() == "EVET"
        uk_visit_count = form.step5.get("uk_visited_count", "").strip()

        if has_uk_visit:
            print("[FORM-33] UK'ya gitmis, Yes seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "haveBeenToTheUK_true"))))
            time.sleep(1)

            # Kac kez
            count = uk_visit_count if uk_visit_count else "1"
            try:
                count_val = int(count)
            except:
                count_val = 1

            times_input = wait.until(EC.presence_of_element_located((By.ID, "numberOfTimes")))
            times_input.clear()
            times_input.send_keys(str(count_val))
            print(f"[FORM-33a] UK ziyaret sayisi: {count_val}")
            time.sleep(0.5)

            click_submit(driver, wait)
            time.sleep(3)

            # En son UK ziyaret detayi
            print("[FORM-33b] Son UK ziyaret detaylari...")

            # Sebep - Tourist varsayilan
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "reasonRef_tourist"))))
            time.sleep(0.5)

            # Tarih (ay/yil)
            uk_visit_date = form.step5.get("uk_visit_date", "").strip()
            if uk_visit_date:
                visit_dt = parse_date_safe(uk_visit_date, "UK ziyaret tarihi")
            else:
                visit_dt = datetime.now() - relativedelta(years=2)

            driver.execute_script(f"""
                function setVal(id, val) {{
                    var el = document.getElementById(id);
                    if (!el) return;
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                setVal('date_month', '{visit_dt.month}');
                setVal('date_year', '{visit_dt.year}');
            """)
            print(f"[FORM-33c] Ziyaret tarihi: {visit_dt.month}/{visit_dt.year}")
            time.sleep(0.3)

            # Sure - varsayilan 1 hafta
            driver.execute_script("""
                var s = document.getElementById('durationOfStayUnit');
                s.value = 'weeks';
                s.dispatchEvent(new Event('change', {bubbles: true}));
            """)
            time.sleep(0.3)

            duration_input = wait.until(EC.presence_of_element_located((By.ID, "durationOfStay")))
            duration_input.clear()
            duration_input.send_keys("1")
            print("[FORM-33d] Sure: 1 hafta")
            time.sleep(0.5)

            click_submit(driver, wait)
            time.sleep(3)

            # Baska UK ziyaret ekle - No (addAnother sayfasi varsa)
            try:
                no_more = wait.until(EC.presence_of_element_located((By.ID, "addAnother_false")))
                safe_click(driver, no_more)
                time.sleep(0.5)
                click_submit(driver, wait)
                time.sleep(3)
                print("[FORM-33e] Baska UK ziyaret yok.")
            except:
                print("[FORM-33e] addAnother sayfasi yok, devam ediliyor.")

        else:
            print("[FORM-33] UK'ya gitmemis, No seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "haveBeenToTheUK_false"))))
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)

        print("[FORM-33] UK seyahat gecmisi tamamlandi!")

    # ===== SAYFA 34: AU/CA/NZ/USA/CH/EEA ulkelere seyahat =====
    if should_run("other_countries"):
        print("[FORM-34] AU/CA/NZ/USA/CH/EEA seyahat...")

        # lastTravels'dan EEA/US/CA/AU/NZ/CH ulkelerini ayikla
        eea_countries = {"austria","belgium","bulgaria","croatia","cyprus","czechia","czech republic",
            "denmark","estonia","finland","france","germany","greece","hungary","iceland","ireland",
            "italy","latvia","liechtenstein","lithuania","luxembourg","malta","netherlands","norway",
            "poland","portugal","romania","slovakia","slovenia","spain","sweden","switzerland",
            "usa","america","united states","canada","australia","new zealand","newzealand"}
        
        country_to_radio = {
            "usa": "usa", "america": "usa", "united states": "usa",
            "canada": "canada", "australia": "australia",
            "new zealand": "newzealand", "newzealand": "newzealand",
        }
        # Geri kalan EEA -> schengen

        travels = form.last_travels
        eea_travels = []
        other_travels = []
        
        for t in travels:
            c = t.get("country", "").strip().lower()
            if any(ec in c for ec in eea_countries):
                eea_travels.append(t)
            elif c:
                other_travels.append(t)

        # Kac kez EEA ulkelere gitmis
        eea_count = len(eea_travels)
        
        if eea_count >= 6:
            radio_id = "bandRef_6"
        elif eea_count >= 2:
            radio_id = "bandRef_2"
        elif eea_count >= 1:
            radio_id = "bandRef_1"
        else:
            radio_id = "bandRef_0"

        # Radio sec
        driver.execute_script(f"""
            var radios = document.querySelectorAll('input[name="bandRef"]');
            radios.forEach(function(r) {{ r.checked = false; }});
            var target = document.getElementById('{radio_id}');
            if (target) {{ target.checked = true; target.click(); target.dispatchEvent(new Event('change', {{bubbles: true}})); }}
        """)
        print(f"[FORM-34] EEA ziyaret sayisi: {eea_count} -> {radio_id}")
        time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)

        # Detay sayfalari - son 2 seyahati gir (site max 3 istiyor)
        if eea_count > 0:
            entries_to_fill = eea_travels[:2]  # Son 2 seyahat
            for idx, travel in enumerate(entries_to_fill):
                try:
                    time.sleep(1)
                    is_detail = driver.execute_script("""
                        return document.getElementById('countryRef_usa') !== null ||
                               document.getElementById('countryRef_schengen') !== null;
                    """)
                    if not is_detail:
                        break

                    country = travel.get("country", "").strip().lower()
                    purpose = travel.get("purpose", "tourist").strip().lower()
                    month_year = travel.get("monthYear", "").strip()
                    duration = travel.get("durationDays", "7").strip()

                    # Hangi radio secilecek
                    matched_radio = None
                    for key, val in country_to_radio.items():
                        if key in country:
                            matched_radio = f"countryRef_{val}"
                            break
                    if not matched_radio:
                        matched_radio = "countryRef_schengen"

                    # Ulke sec
                    set_radio(driver, matched_radio)
                    time.sleep(0.5)

                    # Schengen secildiyse ulke dropdown doldur
                    if matched_radio == "countryRef_schengen":
                        unhide_toggled(driver, "countryRef_schengen")
                        # Schengen ulke kodunu bul
                        schengen_map = {"germany":"DEU","france":"FRA","spain":"ESP","italy":"ITA","netherlands":"NLD",
                            "greece":"GRC","portugal":"PRT","austria":"AUT","belgium":"BEL","sweden":"SWE",
                            "norway":"NOR","denmark":"DNK","finland":"FIN","poland":"POL","czech":"CZE",
                            "hungary":"HUN","romania":"ROU","croatia":"HRV","bulgaria":"BGR","switzerland":"CHE",
                            "ireland":"IRL","iceland":"ISL","slovakia":"SVK","slovenia":"SVN","estonia":"EST",
                            "latvia":"LVA","lithuania":"LTU","luxembourg":"LUX","malta":"MLT","cyprus":"CYP"}
                        code = "DEU"  # varsayilan Germany
                        for key, val in schengen_map.items():
                            if key in country:
                                code = val
                                break
                        set_select(driver, "schengenCountry", code)

                    # Sebep
                    reason_map = {"tourist":"tourist","turist":"tourist","is":"business","business":"business",
                                  "work":"business","study":"study","transit":"transit"}
                    reason_radio = "reasonRef_tourist"
                    for key, val in reason_map.items():
                        if key in purpose:
                            reason_radio = f"reasonRef_{val}"
                            break
                    set_radio(driver, reason_radio)

                    # Tarih (MM YYYY)
                    if month_year:
                        try:
                            visit_dt = parse_date_safe(month_year, "EEA ziyaret")
                        except:
                            visit_dt = datetime.now() - relativedelta(years=1)
                    else:
                        visit_dt = datetime.now() - relativedelta(years=1)
                    set_input(driver, "date_month", str(visit_dt.month))
                    set_input(driver, "date_year", str(visit_dt.year))

                    # Sure
                    try:
                        dur_days = int(duration) if duration else 7
                    except:
                        dur_days = 7
                    if dur_days <= 7:
                        set_select(driver, "durationOfStayUnit", "days")
                        set_input(driver, "durationOfStay", str(dur_days if dur_days > 0 else 7))
                    elif dur_days <= 30:
                        set_select(driver, "durationOfStayUnit", "weeks")
                        set_input(driver, "durationOfStay", str(max(1, dur_days // 7)))
                    else:
                        set_select(driver, "durationOfStayUnit", "months")
                        set_input(driver, "durationOfStay", str(max(1, dur_days // 30)))

                    print(f"[FORM-34b] Seyahat {idx+1}: {country} / {purpose} / {visit_dt.month}/{visit_dt.year} / {dur_days} gun")
                    click_submit(driver, wait)
                    time.sleep(3)

                    # Baska ekle?
                    if idx < len(entries_to_fill) - 1:
                        set_radio(driver, "addAnother_true")
                        click_submit(driver, wait)
                        time.sleep(3)
                    else:
                        set_radio(driver, "addAnother_false")
                        click_submit(driver, wait)
                        time.sleep(3)
                except Exception as e:
                    print(f"[FORM-34b] Seyahat {idx+1} hatasi: {e}")
                    # Hata olursa No sec ve devam et
                    try:
                        set_radio(driver, "addAnother_false")
                        click_submit(driver, wait)
                        time.sleep(3)
                    except:
                        pass
                    break

        print("[FORM-34] EEA seyahat tamamlandi!")

    # ===== SAYFA 35: UK'da tibbi tedavi =====
    if should_run("medical_treatment"):
        time.sleep(1)
        is_correct_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var form = document.querySelector('form[action*="MedicalTreatment" i]');
            return url.includes('medicaltreatment') || form !== null;
        """)
        if not is_correct_page:
            print("[FORM-35] Tibbi tedavi sayfasi degil, atlaniyor...")
        else:
            print("[FORM-35] UK'da tibbi tedavi sorusu...")
            # Varsayilan: Hayir (cogu basvuruda tedavi yok)
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "haveYouHadTreatment_false"))))
            print("[FORM-35] Tibbi tedavi: No")
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-35] Tibbi tedavi tamamlandi!")

    # ===== SAYFA 36: UK National Insurance numarasi =====
    if should_run("national_insurance"):
        time.sleep(1)
        is_correct_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var form = document.querySelector('form[action*="NationalInsurance" i]');
            return url.includes('nationalinsurance') || form !== null;
        """)
        if not is_correct_page:
            print("[FORM-36] National Insurance sayfasi degil, atlaniyor...")
        else:
            print("[FORM-36] UK National Insurance numarasi...")
            has_ni = form.step5.get("national_insurance_number_exist", "").strip().upper() == "EVET"
            ni_number = form.step5.get("national_insurance_number", "").strip()

            if has_ni and ni_number:
                print(f"[FORM-36] NI numara VAR: {ni_number}")
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_true"))))
                time.sleep(1)
                # NI numarasini gir
                try:
                    ni_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='nationalInsuranceNumber'], input[id*='nationalInsurance'], input[type='text']")))
                    ni_input.clear()
                    ni_input.send_keys(ni_number[:20])
                    print(f"[FORM-36a] NI numarasi girildi: {ni_number}")
                except Exception as e:
                    print(f"[FORM-36a] NI input bulunamadi: {e}")
            else:
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_false"))))
                print("[FORM-36] National Insurance: No")

            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-36] National Insurance tamamlandi!")

    # ===== SAYFA 37: UK ehliyet =====
    if should_run("driving_licence"):
        time.sleep(1)
        is_correct_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var form = document.querySelector('form[action*="DrivingLicence" i]');
            return url.includes('drivinglicence') || form !== null;
        """)
        if not is_correct_page:
            print("[FORM-37] Ehliyet sayfasi degil, atlaniyor...")
        else:
            print("[FORM-37] UK ehliyet sorusu...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "doYouHaveADrivingLicence_false"))))
            print("[FORM-37] UK ehliyet: No")
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-37] UK ehliyet tamamlandi!")

    # ===== SAYFA 38: UK kamu fonlari =====
    if should_run("public_funds"):
        time.sleep(1)
        is_correct_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var form = document.querySelector('form[action*="PublicFunds" i]');
            return url.includes('publicfunds') || form !== null;
        """)
        if not is_correct_page:
            print("[FORM-38] Kamu fonlari sayfasi degil, atlaniyor...")
        else:
            print("[FORM-38] UK kamu fonlari sorusu...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_false"))))
            print("[FORM-38] Kamu fonlari: No")
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-38] Kamu fonlari tamamlandi!")

    # ===== SAYFA 39: Son 10 yilda UK vizesi aldin mi =====
    if should_run("previous_uk_visa"):
        print("[FORM-39] Onceki UK vizesi sorusu...")

        has_uk_visa = form.step5.get("uk_visa_last10", "").strip().upper() == "EVET"

        if has_uk_visa:
            print("[FORM-39] UK vizesi VAR, Yes seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "yesNo_true"))))
            time.sleep(1)

            # Vize verilis tarihi
            uk_visa_date = form.step5.get("uk_visa_date", "").strip()
            if uk_visa_date:
                visa_dt = parse_date_safe(uk_visa_date, "UK vize tarihi")
            else:
                visa_dt = datetime.now() - relativedelta(years=2)

            driver.execute_script(f"""
                function setVal(id, val) {{
                    var el = document.getElementById(id);
                    if (!el) return;
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, val);
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                setVal('applicationDetails_dateOfIssue_month', '{visa_dt.month}');
                setVal('applicationDetails_dateOfIssue_year', '{visa_dt.year}');
            """)
            print(f"[FORM-39a] Vize tarihi: {visa_dt.month}/{visa_dt.year}")
            time.sleep(0.5)
        else:
            print("[FORM-39] UK vizesi YOK, No seciliyor...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "yesNo_false"))))
            time.sleep(0.5)

        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-39] Onceki UK vizesi tamamlandi!")

    # ===== SAYFA 40: UK'da kalma izni basvurusu =====
    if should_run("leave_to_remain"):
        print("[FORM-40] UK kalma izni basvurusu...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "previouslyApplied_false"))))
        print("[FORM-40] Kalma izni: No")
        time.sleep(0.5)
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-40] Tamamlandi!")

    # ===== SAYFA 41: Sabika kaydi =====
    if should_run("criminal_convictions"):
        time.sleep(2)
        is_correct_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var forms = document.querySelectorAll('form');
            var foundForm = false;
            for (var i = 0; i < forms.length; i++) {
                var action = (forms[i].getAttribute('action') || '').toLowerCase();
                if (action.includes('criminalconviction')) {
                    foundForm = true;
                    break;
                }
            }
            var container = document.getElementById('standardCriminalConvictionType');
            return url.includes('criminalconviction') || foundForm || container !== null;
        """)
        if not is_correct_page:
            print("[FORM-41] Sabika kaydi sayfasi degil, atlaniyor...")
        else:
            print("[FORM-41] Sabika kaydi...")
            # Once yanlis secilmis olabilecek radiolari temizle
            driver.execute_script("""
                var radios = document.querySelectorAll('input[name="convictionTypeRef"]');
                radios.forEach(function(r) {
                    r.checked = false;
                    var label = document.querySelector('label[for="' + r.id + '"]');
                    if (label) label.classList.remove('selected');
                });
            """)
            time.sleep(0.3)

            # None radio'yu sec (scrollIntoView + JS click)
            driver.execute_script("""
                var noneRadio = document.getElementById('convictionTypeRef_none');
                if (noneRadio) {
                    noneRadio.scrollIntoView({block: 'center'});
                    noneRadio.checked = true;
                    noneRadio.dispatchEvent(new Event('change', {bubbles: true}));
                    noneRadio.dispatchEvent(new Event('click', {bubbles: true}));
                    var label = document.querySelector('label[for="convictionTypeRef_none"]');
                    if (label) label.classList.add('selected');
                }
            """)
            time.sleep(0.5)

            # Dogrulama + safe_click fallback
            is_none_selected = driver.execute_script("""
                var r = document.getElementById('convictionTypeRef_none');
                return r && r.checked;
            """)
            if not is_none_selected:
                print("[FORM-41] JS ile secilemedi, safe_click deneniyor...")
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "convictionTypeRef_none"))))

            print("[FORM-41] Sabika: None secildi")
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-41] Tamamlandi!")

    # ===== SAYFA 42: Savas suclari =====
    if should_run("war_crimes"):
        print("[FORM-42] Savas suclari...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "warCrimesInvolvement_false"))))
        time.sleep(0.5)
        # Onay checkbox'i
        try:
            confirm = driver.find_element(By.ID, "readAllInfo_iConfirm")
            if not confirm.is_selected():
                safe_click(driver, confirm)
        except:
            pass
        time.sleep(0.5)
        print("[FORM-42] Savas suclari: No + onay")
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-42] Tamamlandi!")

    # ===== SAYFA 43: Teror faaliyetleri =====
    if should_run("terrorist_activities"):
        print("[FORM-43] Teror faaliyetleri...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "terroristActivitiesInvolvement_false"))))
        time.sleep(0.5)
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "terroristOrganisationsInvolvement_false"))))
        time.sleep(0.5)
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "terroristViewsExpressed_false"))))
        time.sleep(0.5)
        # Onay checkbox'i
        try:
            confirm = driver.find_element(By.ID, "readAllInfo_iConfirm")
            if not confirm.is_selected():
                safe_click(driver, confirm)
        except:
            pass
        time.sleep(0.5)
        print("[FORM-43] Teror: No x3 + onay")
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-43] Tamamlandi!")

    # ===== SAYFA 44: Asiri gorusler =====
    if should_run("extremist_activities"):
        print("[FORM-44] Asiri gorusler...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "extremistOrganisationsInvolvement_false"))))
        time.sleep(0.5)
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "extremistViewsExpressed_false"))))
        time.sleep(0.5)
        # Onay checkbox'i
        try:
            confirm = driver.find_element(By.ID, "readAllInfo_iConfirm")
            if not confirm.is_selected():
                safe_click(driver, confirm)
        except:
            pass
        time.sleep(0.5)
        print("[FORM-44] Asirilik: No x2 + onay")
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-44] Tamamlandi!")

    # ===== SAYFA 45: Iyi karakter =====
    if should_run("good_character"):
        print("[FORM-45] Iyi karakter...")
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "personOfGoodCharacter_false"))))
        time.sleep(0.5)
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "otherActivities_false"))))
        time.sleep(0.5)
        safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "anyOtherInfo_false"))))
        time.sleep(0.5)
        print("[FORM-45] Karakter: No x3")
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-45] Tamamlandi!")

    # ===== SAYFA 46: Son 10 yilda baska ulkelere seyahat (UK/US/CA/AU/NZ/CH/EEA HARIC) =====
    if should_run("world_travel"):
        time.sleep(2)
        is_correct_page = driver.execute_script("""
            var forms = document.querySelectorAll('form');
            for (var i = 0; i < forms.length; i++) {
                var action = (forms[i].getAttribute('action') || '').toLowerCase();
                if (action.includes('worldtravelhistory') && !action.includes('detail')) return true;
            }
            return document.getElementById('standardWorldTravelHistory') !== null;
        """)
        if not is_correct_page:
            print("[FORM-46] Dunya seyahat sayfasi degil, atlaniyor...")
        else:
            # lastTravels'dan EEA/US/CA/AU/NZ/CH/UK OLMAYAN ulkeleri bul
            excluded = {"usa","america","united states","canada","australia","new zealand","newzealand",
                "uk","united kingdom","england","switzerland",
                "austria","belgium","bulgaria","croatia","cyprus","czechia","czech republic",
                "denmark","estonia","finland","france","germany","greece","hungary","iceland","ireland",
                "italy","latvia","liechtenstein","lithuania","luxembourg","malta","netherlands","norway",
                "poland","portugal","romania","slovakia","slovenia","spain","sweden"}

            travels = form.last_travels
            other_travels = [t for t in travels if not any(ex in t.get("country","").strip().lower() for ex in excluded)]

            if other_travels:
                print(f"[FORM-46] {len(other_travels)} diger ulke ziyareti var, Yes seciliyor...")
                driver.execute_script("""
                    var radios = document.querySelectorAll('input[name="value"]');
                    radios.forEach(function(r) { r.checked = false; });
                    var yes = document.getElementById('value_true');
                    if (yes) { yes.checked = true; yes.click(); yes.dispatchEvent(new Event('change', {bubbles: true})); }
                """)
                time.sleep(0.5)
                click_submit(driver, wait)
                time.sleep(3)

                # Son 2 seyahati gir
                entries = other_travels[:2]
                for idx, travel in enumerate(entries):
                    try:
                        time.sleep(1)
                        is_detail = driver.execute_script("return document.getElementById('whichCountry') !== null;")
                        if not is_detail:
                            break

                        country = travel.get("country", "").strip()
                        purpose = travel.get("purpose", "tourism").strip().lower()
                        month_year = travel.get("monthYear", "").strip()
                        duration = travel.get("durationDays", "7").strip()

                        # Ulke sec - ISO kodu bul
                        country_lower = country.lower()
                        country_codes = {"china":"CHN","japan":"JPN","korea":"KOR","russia":"RUS",
                            "brazil":"BRA","mexico":"MEX","india":"IND","thailand":"THA","malaysia":"MYS",
                            "indonesia":"IDN","singapore":"SGP","egypt":"EGY","morocco":"MAR",
                            "south africa":"ZAF","turkey":"TUR","pakistan":"PAK","iran":"IRN",
                            "iraq":"IRQ","saudi":"SAU","qatar":"QAT","uae":"ARE","dubai":"ARE",
                            "georgia":"GEO","azerbaijan":"AZE","ukraine":"UKR","tunisia":"TUN",
                            "jordan":"JOR","lebanon":"LBN","israel":"ISR","vietnam":"VNM",
                            "philippines":"PHL","sri lanka":"LKA","nepal":"NPL","bangladesh":"BGD",
                            "argentina":"ARG","chile":"CHL","colombia":"COL","peru":"PER",
                            "cuba":"CUB","dominican":"DOM","jamaica":"JAM","kenya":"KEN",
                            "tanzania":"TZA","nigeria":"NGA","ghana":"GHA","senegal":"SEN"}
                        code = "CHN"  # varsayilan
                        for key, val in country_codes.items():
                            if key in country_lower:
                                code = val
                                break
                        set_select(driver, "whichCountry", code, country)

                        # Sebep
                        reason_map = {"tourism":"tourism","tourist":"tourism","turist":"tourism",
                                      "business":"business","is":"business","work":"business",
                                      "study":"study","transit":"transit"}
                        reason_val = "tourism"
                        for key, val in reason_map.items():
                            if key in purpose:
                                reason_val = val
                                break
                        set_radio(driver, f"reasonForVisit_{reason_val}")

                        # Tarihler
                        if month_year:
                            try:
                                visit_dt = parse_date_safe(month_year, "Diger ulke ziyaret")
                            except:
                                visit_dt = datetime.now() - relativedelta(years=1)
                        else:
                            visit_dt = datetime.now() - relativedelta(years=1)

                        try:
                            dur_days = int(duration) if duration else 7
                        except:
                            dur_days = 7
                        end_dt = visit_dt + relativedelta(days=max(dur_days, 1))

                        set_date(driver, "visitStartDate", visit_dt)
                        set_date(driver, "visitEndDate", end_dt)

                        print(f"[FORM-46b] Seyahat {idx+1}: {country} / {reason_val} / {visit_dt.day}/{visit_dt.month}/{visit_dt.year}")
                        click_submit(driver, wait)
                        time.sleep(3)

                        # Baska ekle?
                        if idx < len(entries) - 1:
                            set_radio(driver, "addAnother_true")
                            click_submit(driver, wait)
                            time.sleep(3)
                        else:
                            set_radio(driver, "addAnother_false")
                            click_submit(driver, wait)
                            time.sleep(3)
                    except Exception as e:
                        print(f"[FORM-46b] Seyahat {idx+1} hatasi: {e}")
                        try:
                            set_radio(driver, "addAnother_false")
                            click_submit(driver, wait)
                            time.sleep(3)
                        except:
                            pass
                        break
            else:
                print("[FORM-46] Diger ulke ziyareti yok, No seciliyor...")
                driver.execute_script("""
                    var radios = document.querySelectorAll('input[name="value"]');
                    radios.forEach(function(r) { r.checked = false; });
                    var no = document.getElementById('value_false');
                    if (no) { no.checked = true; no.click(); no.dispatchEvent(new Event('change', {bubbles: true})); }
                """)
                time.sleep(0.5)
                click_submit(driver, wait)
                time.sleep(3)

            print("[FORM-46] Tamamlandi!")

    # ===== SAYFA 47: Gocmenlik problemleri =====
    if should_run("immigration_problems"):
        time.sleep(2)
        is_correct_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var forms = document.querySelectorAll('form');
            var foundForm = false;
            for (var i = 0; i < forms.length; i++) {
                var action = (forms[i].getAttribute('action') || '').toLowerCase();
                if (action.includes('immigrationproblems')) {
                    foundForm = true;
                    break;
                }
            }
            var container = document.getElementById('standardImmigrationProblems');
            return url.includes('immigrationproblems') || foundForm || container !== null;
        """)
        if not is_correct_page:
            print("[FORM-47] Gocmenlik problemleri sayfasi degil, atlaniyor...")
        else:
            print("[FORM-47] Gocmenlik problemleri...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_false"))))
            print("[FORM-47] Gocmenlik sorunlari: No")
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-47] Tamamlandi!")

    # ===== SAYFA 48: Gocmenlik ihlali =====
    if should_run("immigration_breach"):
        time.sleep(2)
        is_correct_page = driver.execute_script("""
            var url = window.location.href.toLowerCase();
            var forms = document.querySelectorAll('form');
            var foundForm = false;
            for (var i = 0; i < forms.length; i++) {
                var action = (forms[i].getAttribute('action') || '').toLowerCase();
                if (action.includes('immigrationbreach')) {
                    foundForm = true;
                    break;
                }
            }
            var container = document.getElementById('standardImmigrationBreach');
            return url.includes('immigrationbreach') || foundForm || container !== null;
        """)
        if not is_correct_page:
            print("[FORM-48] Gocmenlik ihlali sayfasi degil, atlaniyor...")
        else:
            print("[FORM-48] Gocmenlik ihlali...")
            safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "value_false"))))
            print("[FORM-48] Gocmenlik ihlali: No")
            time.sleep(0.5)
            click_submit(driver, wait)
            time.sleep(3)
            print("[FORM-48] Tamamlandi!")

    # ===== SAYFA 49: Istihdam gecmisi (silahli kuvvetler vb) =====
    if should_run("employment_history"):
        print("[FORM-49] Istihdam gecmisi (guvenlik kuruluslari)...")
        # Hicbirinde calismadim
        none_cb = wait.until(EC.presence_of_element_located((By.ID, "none_none")))
        if not none_cb.is_selected():
            safe_click(driver, none_cb)
        print("[FORM-49] Hicbirinde calismadim secildi")
        time.sleep(0.5)
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-49] Tamamlandi!")

    # ===== SAYFA 50: Ek bilgi =====
    if should_run("other_information"):
        print("[FORM-50] Ek bilgi...")
        # Bos birak, direkt kaydet
        click_submit(driver, wait)
        time.sleep(3)
        print("[FORM-50] Ek bilgi tamamlandi!")

    # ===== FORM TAMAMLANDI =====
    print("=" * 60)
    print("  FORM DOLDURMA TAMAMLANDI!")
    print("=" * 60)


# ============================================================
# ANA DONGU
# ============================================================

def main():
    print("=" * 60)
    print("  UK VIZE BOTU - CRM Kuyruk Dinleyici")
    print("=" * 60)

    while True:
        job = fetch_next_job()

        if not job:
            print(f"[BOT] {POLL_INTERVAL}s sonra tekrar denenecek...")
            time.sleep(POLL_INTERVAL)
            continue

        job_id = job.get("job_id")
        raw_form_data = job.get("data", {})
        resume_link = job.get("resume_link")

        # visa_forms verisini parse et
        form = VisaFormData(raw_form_data)

        driver = None
        try:
            update_job_status(job_id, "processing", "Tarayici baslatiliyor")
            driver = create_driver()
            wait = WebDriverWait(driver, 20)

            if resume_link:
                # Resume linkten devam et - bastan doldur
                update_job_status(job_id, "processing", f"Resume linkten devam ediliyor: {form.full_name}")
                start_page = resume_from_link(driver, wait, resume_link, form)
                update_job_status(job_id, "processing", f"Kaldigi sayfa: {start_page}, devam ediliyor")

                # Isim sayfasindan bastan doldur (arada degisen bilgiler guncellenir)
                fill_form(driver, wait, form, start_from=start_page)

                # Save for later yap
                print("[BOT] Resume devam tamamlandi, kaydediliyor...")
                resume_url = save_and_exit(driver, wait, job_id)
                complete_job(job_id, {"url": driver.current_url, "resume_link": resume_url or resume_link})
                print(f"[OK] Form kaydedildi! Resume: {resume_url}")

                input("[BEKLE] Tarayici acik. Kapatmak icin Enter'a bas...")
            else:
                # Sifirdan basla
                update_job_status(job_id, "processing", f"Form aciliyor: {form.full_name}")
                navigate_to_form(driver, wait)

                update_job_status(job_id, "processing", "Form dolduruluyor")
                fill_form(driver, wait, form)

                # Form doldurma bitti - save for later yap
                print("[BOT] Form doldurma tamamlandi, kaydediliyor...")
                resume_url = save_and_exit(driver, wait, job_id)
                complete_job(job_id, {"url": driver.current_url, "resume_link": resume_url})
                print(f"[OK] Form kaydedildi! Resume: {resume_url}")

                input("[BEKLE] Tarayici acik. Kapatmak icin Enter'a bas...")

        except Exception as e:
            error_msg = str(e)
            print(f"[HATA] {error_msg}")

            # Hata durumunda save for later dene
            if driver:
                try:
                    print("[BOT] Hata sonrasi save for later deneniyor...")
                    resume_url = save_and_exit(driver, wait, job_id)
                    if resume_url:
                        print(f"[BOT] Hata sonrasi basariyla kaydedildi: {resume_url}")
                except Exception as save_err:
                    print(f"[BOT] Save for later de basarisiz: {save_err}")

            report_error(job_id, error_msg)

            if driver:
                try:
                    driver.save_screenshot(f"hata_{job_id}.png")
                    print(f"[i] Screenshot kaydedildi: hata_{job_id}.png")
                    print(f"[i] Mevcut URL: {driver.current_url}")
                    print(f"[i] Sayfa basligi: {driver.title}")
                except:
                    pass

            input("[BEKLE] Hata olustu! Tarayici acik. Kapatmak icin Enter'a bas...")

        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

        print(f"[BOT] Sonraki is icin {POLL_INTERVAL}s bekleniyor...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()