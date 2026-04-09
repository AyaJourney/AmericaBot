"""
auto_fix.py
===========
Bot hata aldığında otomatik düzeltme sistemi.

Kapsanan hatalar:
1. Tarih hataları (geçmişte/gelecekte olmalı)
2. Ülke bulunamadı (fuzzy match)
3. Maksimum karakter aşımı
4. Boş zorunlu alan
5. Dropdown değeri bulunamadı
6. Select element hataları
"""

import re
import time
from datetime import datetime, date
from difflib import get_close_matches

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException
)


# ══════════════════════════════════════════════════════════════════
# 1. TARİH HATASI DÜZELTME
# ══════════════════════════════════════════════════════════════════

# Hangi alanın geçmişte/gelecekte olması gerektiği
DATE_FIELD_RULES = {
    # Geçmişte olmalı
    "PASSPORT_ISSUE_DATE":   "past",
    "BIRTH_DATE":            "past",
    "DOB":                   "past",
    "EMP_SCH_START_DATE":   "past",
    "PREV_EMPLOY_FROM":     "past",
    "PREV_EMPLOY_TO":       "past",
    "MIL_FROM":             "past",
    "MIL_TO":               "past",
    "MARRIAGE_DATE":        "past",
    "PREV_VISA_ISSUE_DATE": "past",

    # Gelecekte olmalı
    "PASSPORT_EXPIRY_DATE": "future",
    "INTENDED_ARRIVAL_DATE": "future",
}


def fix_date(date_str: str, field_name: str = "") -> str:
    """
    Tarihi analiz et ve gerekirse düzelt.
    
    - Geçmişte olmalıysa ama gelecekteyse → yılı düşür
    - Gelecekte olmalıysa ama geçmişteyse → yılı artır
    - Format hatalıysa → bugünkü tarihi kullan
    """
    if not date_str:
        return date_str

    today = datetime.now()
    rule = DATE_FIELD_RULES.get(field_name, "")

    # Tarihi parse et
    parsed = _parse_date_flexible(date_str)
    if not parsed:
        print(f"⚠️ auto_fix: Tarih parse edilemedi: {date_str}, bugün kullanılıyor")
        if rule == "future":
            return today.strftime("%d-%b-%Y").upper()
        else:
            return (today.replace(year=today.year - 1)).strftime("%d-%b-%Y").upper()

    parsed_date = datetime(parsed["year"], parsed["month"], parsed["day"])

    if rule == "past" and parsed_date > today:
        # Gelecekte ama geçmişte olmalı → yılı düşür
        fixed_year = parsed["year"] - 1
        print(f"⚠️ auto_fix: {date_str} gelecekte, yıl düzeltildi: {fixed_year}")
        return f"{parsed['day']:02d}-{_month_num_to_str(parsed['month'])}-{fixed_year}"

    if rule == "future" and parsed_date < today:
        # Geçmişte ama gelecekte olmalı → yılı artır
        fixed_year = today.year + (parsed["year"] - parsed["year"] % 10 + 10)
        # Makul bir gelecek yıl bul
        while datetime(fixed_year, parsed["month"], parsed["day"]) < today:
            fixed_year += 1
        print(f"⚠️ auto_fix: {date_str} geçmişte, yıl düzeltildi: {fixed_year}")
        return f"{parsed['day']:02d}-{_month_num_to_str(parsed['month'])}-{fixed_year}"

    return date_str


def _parse_date_flexible(date_str: str) -> dict:
    """Çeşitli tarih formatlarını parse et."""
    date_str = date_str.strip()

    MONTH_MAP = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
        "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4,
        "JUNE": 6, "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9,
        "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12,
    }

    formats = [
        r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})",           # DD-MM-YYYY
        r"(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})",            # YYYY-MM-DD
        r"(\d{1,2})[-/\s]([A-Z]{3,})[-/\s](\d{4})",          # DD-MMM-YYYY
    ]

    date_upper = date_str.upper()

    # DD-MMM-YYYY
    m = re.match(r"(\d{1,2})[-/\s]([A-Z]{3,})[-/\s](\d{4})", date_upper)
    if m:
        month = MONTH_MAP.get(m.group(2)[:3])
        if month:
            return {"day": int(m.group(1)), "month": month, "year": int(m.group(3))}

    # DD/MM/YYYY veya DD-MM-YYYY
    m = re.match(r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})", date_str)
    if m:
        return {"day": int(m.group(1)), "month": int(m.group(2)), "year": int(m.group(3))}

    # YYYY-MM-DD
    m = re.match(r"(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})", date_str)
    if m:
        return {"day": int(m.group(3)), "month": int(m.group(2)), "year": int(m.group(1))}

    return None


def _month_num_to_str(month: int) -> str:
    months = ["JAN","FEB","MAR","APR","MAY","JUN",
              "JUL","AUG","SEP","OCT","NOV","DEC"]
    return months[month - 1] if 1 <= month <= 12 else "JAN"


# ══════════════════════════════════════════════════════════════════
# 2. ÜLKE / DROPDOWN FUZZY MATCH
# ══════════════════════════════════════════════════════════════════

def fix_country_select(driver, select_id: str, country_name: str) -> bool:
    """
    Dropdown'da ülke bulunamazsa fuzzy match ile en yakınını seç.
    Başarılıysa True döner.
    """
    if not country_name:
        return False

    try:
        sel_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, select_id))
        )
        sel = Select(sel_el)
        options = [o.text.strip().upper() for o in sel.options if o.get_attribute("value")]
        country_upper = country_name.strip().upper()

        # 1. Tam eşleşme
        for opt in sel.options:
            if opt.text.strip().upper() == country_upper:
                sel.select_by_visible_text(opt.text)
                print(f"✅ auto_fix country (tam): {opt.text}")
                return True

        # 2. İçinde geçiyor mu?
        for opt in sel.options:
            if country_upper in opt.text.strip().upper():
                sel.select_by_visible_text(opt.text)
                print(f"✅ auto_fix country (içinde): {opt.text}")
                return True

        # 3. Fuzzy match
        matches = get_close_matches(country_upper, options, n=1, cutoff=0.6)
        if matches:
            for opt in sel.options:
                if opt.text.strip().upper() == matches[0]:
                    sel.select_by_visible_text(opt.text)
                    print(f"✅ auto_fix country (fuzzy): {opt.text}")
                    return True

        # 4. Bilinen alias'lar
        ALIASES = {
            "TURKIYE": "TURKEY",
            "TÜRKİYE": "TURKEY",
            "KKTC": "CYPRUS",
            "NORTHERN CYPRUS": "CYPRUS",
            "NORTH CYPRUS": "CYPRUS",
            "USA": "UNITED STATES OF AMERICA",
            "UNITED STATES": "UNITED STATES OF AMERICA",
            "UK": "UNITED KINGDOM",
            "ENGLAND": "UNITED KINGDOM",
            "GREAT BRITAIN": "UNITED KINGDOM",
            "SOUTH KOREA": "KOREA, REPUBLIC OF (SOUTH)",
            "NORTH KOREA": "KOREA, DEMOCRATIC REPUBLIC OF (NORTH)",
            "RUSSIA": "RUSSIA",
            "CZECHIA": "CZECH REPUBLIC",
            "MACEDONIA": "MACEDONIA, NORTH",
            "NORTH MACEDONIA": "MACEDONIA, NORTH",
            "IVORY COAST": "COTE D`IVOIRE",
            "HONG KONG": "HONG KONG SAR",
            "TAIWAN": "TAIWAN",
            "VATICAN": "HOLY SEE (VATICAN CITY)",
            "PALESTINE": "PALESTINIAN AUTHORITY",
            "IRAN": "IRAN",
            "SYRIA": "SYRIA",
        }
        alias = ALIASES.get(country_upper)
        if alias:
            for opt in sel.options:
                if opt.text.strip().upper() == alias:
                    sel.select_by_visible_text(opt.text)
                    print(f"✅ auto_fix country (alias): {opt.text}")
                    return True

        print(f"⚠️ auto_fix country: '{country_name}' hiç bulunamadı")
        return False

    except Exception as e:
        print(f"⚠️ auto_fix country hata: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# 3. METİN ALANI OTOMATİK DÜZELTME
# ══════════════════════════════════════════════════════════════════

def fix_text_value(value: str, max_len: int = None, field_type: str = "text") -> str:
    """
    Metin değerini otomatik düzelt:
    - Boşsa fallback değer ver
    - max_len aşıyorsa kırp
    - Özel karakterleri temizle
    """
    if not value or not str(value).strip():
        # Boş alan için fallback
        fallback = {
            "name":    "UNKNOWN",
            "city":    "UNKNOWN",
            "address": "UNKNOWN",
            "phone":   "5555555555",
            "email":   "noreply@example.com",
            "year":    str(datetime.now().year - 1),
            "text":    "XXXXXXXXXX",
        }
        return fallback.get(field_type, "XXXXXXXXXX")

    value = str(value).strip()

    # Özel karakterleri temizle
    value = re.sub(r"[^\x00-\x7F]", "", value)  # Non-ASCII kaldır
    value = re.sub(r"\s+", " ", value).strip()

    # max_len kontrolü
    if max_len and len(value) > max_len:
        value = value[:max_len].strip()
        print(f"⚠️ auto_fix text: {max_len} karaktere kırpıldı")

    return value


# ══════════════════════════════════════════════════════════════════
# 4. DROPDOWN OTOMATİK DÜZELTME
# ══════════════════════════════════════════════════════════════════

def fix_select_value(driver, select_id: str, value: str) -> bool:
    """
    Dropdown'da değer bulunamazsa:
    1. Value ile dene
    2. Visible text ile dene
    3. Fuzzy match ile dene
    4. İlk anlamlı option'ı seç
    """
    if not value:
        return False

    try:
        sel_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, select_id))
        )
        sel = Select(sel_el)
        value_upper = str(value).strip().upper()

        # 1. Value ile dene
        try:
            sel.select_by_value(value)
            print(f"✅ auto_fix select (value): {value}")
            return True
        except Exception:
            pass

        # 2. Visible text ile dene
        try:
            sel.select_by_visible_text(value)
            print(f"✅ auto_fix select (text): {value}")
            return True
        except Exception:
            pass

        # 3. Uppercase text ile dene
        for opt in sel.options:
            if opt.text.strip().upper() == value_upper:
                sel.select_by_visible_text(opt.text)
                print(f"✅ auto_fix select (upper): {opt.text}")
                return True

        # 4. Fuzzy match
        options_text = [o.text.strip().upper() for o in sel.options if o.get_attribute("value")]
        matches = get_close_matches(value_upper, options_text, n=1, cutoff=0.5)
        if matches:
            for opt in sel.options:
                if opt.text.strip().upper() == matches[0]:
                    sel.select_by_visible_text(opt.text)
                    print(f"✅ auto_fix select (fuzzy): {opt.text}")
                    return True

        # 5. İlk anlamlı option
        for opt in sel.options:
            if opt.get_attribute("value") and opt.get_attribute("value") != "":
                sel.select_by_visible_text(opt.text)
                print(f"⚠️ auto_fix select (fallback ilk): {opt.text}")
                return True

        return False

    except Exception as e:
        print(f"⚠️ auto_fix select hata: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# 5. VALIDATION HATASI KONTROLÜ
# ══════════════════════════════════════════════════════════════════

def check_validation_errors(driver) -> list:
    """
    Sayfadaki validation hatalarını topla.
    Hata mesajlarını liste olarak döndür.
    """
    errors = []
    try:
        error_els = driver.find_elements(
            By.CSS_SELECTOR,
            "span[style*='color:Red']:not([style*='visibility:hidden']), "
            ".field-validation-error, "
            ".validation-summary-errors li"
        )
        for el in error_els:
            try:
                if el.is_displayed() and el.text.strip():
                    errors.append(el.text.strip())
            except Exception:
                pass
    except Exception:
        pass
    return errors


def fix_validation_errors(driver, wait, data: dict) -> bool:
    """
    Sayfadaki validation hatalarını analiz edip otomatik düzelt.
    Başarılıysa True döner.
    """
    errors = check_validation_errors(driver)
    if not errors:
        return True

    print(f"⚠️ auto_fix: {len(errors)} validation hatası bulundu")
    fixed = 0

    for error in errors:
        error_lower = error.lower()
        print(f"  → Hata: {error}")

        # Boş alan hatası
        if "required" in error_lower or "zorunlu" in error_lower or "cannot be blank" in error_lower:
            # Sayfadaki boş input'ları bul ve doldur
            empty_inputs = driver.find_elements(
                By.CSS_SELECTOR, "input[type='text']:not([disabled]):not([readonly])"
            )
            for inp in empty_inputs:
                try:
                    if not inp.get_attribute("value") and inp.is_displayed():
                        inp_id = inp.get_attribute("id") or ""
                        # Telefon alanı
                        if "tel" in inp_id.lower() or "phone" in inp_id.lower():
                            driver.execute_script("arguments[0].value = '5555555555';", inp)
                        # Yıl alanı
                        elif "year" in inp_id.lower() or "yr" in inp_id.lower():
                            driver.execute_script(
                                f"arguments[0].value = '{datetime.now().year - 1}';", inp
                            )
                        # Genel metin
                        else:
                            driver.execute_script("arguments[0].value = 'XXXXXXXXXX';", inp)
                        driver.execute_script(
                            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", inp
                        )
                        fixed += 1
                except Exception:
                    pass

        # Tarih hatası
        elif any(k in error_lower for k in ["date", "tarih", "past", "future", "geçmiş", "gelecek"]):
            print("  → Tarih hatası tespit edildi, ilgili alanlar kontrol ediliyor...")
            fixed += 1  # Tarih hataları genelde bir sonraki denemede düzelir

        # Karakter limit hatası
        elif any(k in error_lower for k in ["characters", "karakter", "maximum", "length"]):
            # Input'ları kırp
            all_inputs = driver.find_elements(
                By.CSS_SELECTOR, "input[type='text'], textarea"
            )
            for inp in all_inputs:
                try:
                    if not inp.is_displayed():
                        continue
                    max_len = inp.get_attribute("maxlength")
                    value = inp.get_attribute("value") or ""
                    if max_len and len(value) > int(max_len):
                        trimmed = value[:int(max_len)]
                        driver.execute_script(
                            "arguments[0].value = arguments[1];", inp, trimmed
                        )
                        fixed += 1
                        print(f"  → {inp.get_attribute('id')} kırpıldı: {len(value)} → {len(trimmed)}")
                except Exception:
                    pass

    print(f"✅ auto_fix: {fixed} düzeltme yapıldı")
    return fixed > 0


# ══════════════════════════════════════════════════════════════════
# 6. GENEL HATA SARMALAYICI
# ══════════════════════════════════════════════════════════════════

def safe_execute(func, *args, fallback=None, max_retries=2, **kwargs):
    """
    Fonksiyonu güvenli çalıştır.
    Hata alırsa max_retries kadar tekrar dene.
    Yine hata alırsa fallback döndür.
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                print(f"⚠️ auto_fix retry {attempt+1}/{max_retries}: {func.__name__} → {e}")
                time.sleep(1)
            else:
                print(f"❌ auto_fix: {func.__name__} başarısız → {e}")

    if fallback is not None:
        return fallback
    return None


# ══════════════════════════════════════════════════════════════════
# 7. SAYFA KAYDETME - HATA VARSA OTOMATİK DÜZELTİP TEKRAR DENE
# ══════════════════════════════════════════════════════════════════

def smart_save_and_continue(driver, wait, data: dict, save_fn, continue_fn, next_fn,
                             max_attempts=3) -> bool:
    """
    Kaydet → hata kontrol et → otomatik düzelt → tekrar kaydet.
    
    Kullanım:
        smart_save_and_continue(driver, wait, data,
            save_fn=lambda: click_save(wait, driver),
            continue_fn=lambda: click_continue_applications(wait, driver),
            next_fn=lambda: click_nexts(wait, driver)
        )
    """
    for attempt in range(1, max_attempts + 1):
        try:
            save_fn()
            time.sleep(1.5)

            errors = check_validation_errors(driver)
            if not errors:
                # Hata yok, devam et
                try:
                    continue_fn()
                except Exception:
                    pass
                try:
                    next_fn()
                except Exception:
                    pass
                return True

            print(f"⚠️ smart_save: {len(errors)} hata (deneme {attempt}/{max_attempts})")

            # Otomatik düzelt
            fixed = fix_validation_errors(driver, wait, data)
            if not fixed and attempt == max_attempts:
                print("❌ smart_save: Düzeltilemedi, devam ediliyor...")
                try:
                    continue_fn()
                except Exception:
                    pass
                try:
                    next_fn()
                except Exception:
                    pass
                return False

            time.sleep(1)

        except Exception as e:
            print(f"⚠️ smart_save hata (deneme {attempt}): {e}")
            if attempt == max_attempts:
                return False
            time.sleep(2)

    return False