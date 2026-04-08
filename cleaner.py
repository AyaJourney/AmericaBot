"""
DS-160 — Input Cleaning Layer
JSON/API'den gelen ham veriyi DS-160'a uygun formata çevirir.

Her alan için ayrı fonksiyon.
Tüm fonksiyonlar clean_all(raw: dict) -> dict üzerinden çağrılır.

Desteklenen ham formatlar:
  Tarih : "01/05/1990", "1 Mayıs 1990", "01-05-1990",
          "01-MAY-1990", "1990-05-01", "May 1, 1990",
          "01.05.1990", "1 may 1990", "20 FEB 1993"
  Telefon: "+90 532 123 45 67", "05321234567", "532-123-4567",
           "(532) 123 4567", "+905321234567", "00905321234567"
  Adres  : "Atatürk Mah., No:5/3", "123 Main St." vb.
  İsim   : "Şevket", "İbrahim", "Özgür" → ASCII büyük harf
"""

import re
import unicodedata
from typing import Optional


# ══════════════════════════════════════════════
# TEMEL YARDIMCILAR
# ══════════════════════════════════════════════

def to_ascii_upper(text: str) -> str:
    """
    Türkçe/özel karakterleri ASCII'ye çevirir ve büyük harf yapar.
    Ş→S, İ→I, Ü→U, Ö→O, Ç→C, Ğ→G
    """
    if not text:
        return ""
    # Önce Türkçe özel harfleri manuel map et
    TR_MAP = str.maketrans(
        "şŞıİğĞüÜöÖçÇ",
        "sSiIgGuUoOcC"
    )
    text = text.translate(TR_MAP)
    # Geri kalan unicode karakterleri normalize et
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.upper().strip()


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ══════════════════════════════════════════════
# 1. İSİM / SOYİSİM
# ══════════════════════════════════════════════

def clean_name(raw: str, max_len: int = 33) -> str:
    """
    - Türkçe → ASCII büyük harf
    - Sadece harf, boşluk, tire kalır
    - maxlength: Surnames/Given Names = 33
    """
    if not raw:
        return ""
    text = to_ascii_upper(raw)
    text = re.sub(r"[^A-Z \-]", "", text)
    text = collapse_spaces(text)
    return text[:max_len]


def clean_native_name(raw: str, max_len: int = 100) -> str:
    """
    Full Name in Native Alphabet — Türkçe karakterler KORUNUR.
    maxlength = 100
    """
    if not raw:
        return ""
    return raw.strip()[:max_len]


# ══════════════════════════════════════════════
# 2. TARİH
# ══════════════════════════════════════════════

TR_MONTHS = {
    "ocak": "01", "şubat": "02", "mart": "03", "nisan": "04",
    "mayıs": "05", "haziran": "06", "temmuz": "07", "ağustos": "08",
    "eylül": "09", "ekim": "10", "kasım": "11", "aralık": "12",
    # normalize edilmiş hali
    "ocak": "01", "subat": "02", "mart": "03", "nisan": "04",
    "mayis": "05", "haziran": "06", "temmuz": "07", "agustos": "08",
    "eylul": "09", "ekim": "10", "kasim": "11", "aralik": "12",
}

EN_MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "january": "01", "february": "02", "march": "03", "april": "04",
    "june": "06", "july": "07", "august": "08", "september": "09",
    "october": "10", "november": "11", "december": "12",
}

# DS-160'da ay gösterim formatları
NUM_TO_MON3 = {
    "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR",
    "05": "MAY", "06": "JUN", "07": "JUL", "08": "AUG",
    "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC",
}


def _normalize_month(raw_month: str) -> Optional[str]:
    """Herhangi bir ay ifadesini "01".."12" formatına çevirir."""
    m = raw_month.strip().lower()
    # Sayısal
    if m.isdigit():
        val = int(m)
        if 1 <= val <= 12:
            return f"{val:02d}"
        return None
    # Türkçe (normalize)
    m_norm = unicodedata.normalize("NFKD", m).encode("ascii", "ignore").decode("ascii")
    if m_norm in TR_MONTHS:
        return TR_MONTHS[m_norm]
    # İngilizce
    for k, v in EN_MONTHS.items():
        if m.startswith(k[:3]):
            return v
    return None


def parse_date(raw: str) -> Optional[dict]:
    """
    Herhangi formattaki tarihi parse eder.

    Dönüş: {
        "day":   "15",       # sıfırsız (Travel için)
        "day_padded": "15",  # zero-padded (Personal 1 için)
        "month_num": "06",   # "01".."12"
        "month3": "JUN",     # "JAN".."DEC"
        "year":  "1990",
    }
    veya None (parse edilemezse)
    """
    if not raw:
        return None

    raw = raw.strip()

    # ── Format 1: DD/MM/YYYY veya DD-MM-YYYY veya DD.MM.YYYY
    m = re.match(r"^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$", raw)
    if m:
        d, mo, y = m.groups()
        month = _normalize_month(mo)
        if month:
            return _date_dict(d, month, y)

    # ── Format 2: YYYY-MM-DD (ISO)
    m = re.match(r"^(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})$", raw)
    if m:
        y, mo, d = m.groups()
        month = _normalize_month(mo)
        if month:
            return _date_dict(d, month, y)

    # ── Format 3: DD-MON-YYYY (01-MAY-1990, 20 FEB 1993)
    m = re.match(r"^(\d{1,2})[\s\-\.]([A-Za-zÇçĞğİıÖöŞşÜü]+)[\s\-\.](\d{4})$", raw)
    if m:
        d, mo, y = m.groups()
        month = _normalize_month(mo)
        if month:
            return _date_dict(d, month, y)

    # ── Format 4: MON DD YYYY veya Month DD, YYYY
    m = re.match(r"^([A-Za-zÇçĞğİıÖöŞşÜü]+)[\s\-\.](\d{1,2}),?\s*(\d{4})$", raw)
    if m:
        mo, d, y = m.groups()
        month = _normalize_month(mo)
        if month:
            return _date_dict(d, month, y)

    # ── Format 5: DD Ay YYYY (Türkçe: "1 Mayıs 1990")
    m = re.match(
        r"^(\d{1,2})\s+([A-Za-zÇçĞğİıÖöŞşÜü]+)\s+(\d{4})$", raw
    )
    if m:
        d, mo, y = m.groups()
        month = _normalize_month(mo)
        if month:
            return _date_dict(d, month, y)

    # ── Format 6: Sadece yıl-ay (YYYY-MM) → gün=1
    m = re.match(r"^(\d{4})[\/\-\.](\d{1,2})$", raw)
    if m:
        y, mo = m.groups()
        month = _normalize_month(mo)
        if month:
            return _date_dict("1", month, y)

    return None


def _date_dict(day: str, month_num: str, year: str) -> dict:
    d = int(day)
    return {
        "day":        str(d),           # "1".."31"  (Travel dropdown)
        "day_padded": f"{d:02d}",       # "01".."31" (Personal 1 dropdown)
        "month_num":  month_num,        # "01".."12" (Travel dropdown)
        "month3":     NUM_TO_MON3[month_num],  # "JAN".."DEC"
        "year":       year.strip(),
    }


def clean_date_fields(raw: str, prefix: str) -> dict:
    """
    Ham tarihi parse edip prefix ile dict döndürür.
    prefix="BIRTH" → BIRTH_DAY, BIRTH_DAY_PADDED, BIRTH_MONTH, BIRTH_MONTH3, BIRTH_YEAR
    prefix="INTENDED_ARRIVAL" → INTENDED_ARRIVAL_DAY, ...

    Kullanım:
      data.update(clean_date_fields("01/05/1990", "BIRTH"))
    """
    parsed = parse_date(raw)
    if not parsed:
        raise ValueError(f"❌ Tarih parse edilemedi: {raw!r}")

    return {
        f"{prefix}_DAY":        parsed["day"],
        f"{prefix}_DAY_PADDED": parsed["day_padded"],
        f"{prefix}_MONTH":      parsed["month_num"],
        f"{prefix}_MONTH3":     parsed["month3"],
        f"{prefix}_YEAR":       parsed["year"],
    }


# ══════════════════════════════════════════════
# 3. TELEFON
# ══════════════════════════════════════════════

def clean_phone(raw: str, default_country_code: str = "90") -> str:
    """
    Telefon numarasını DS-160 için temizler.

    DS-160 kuralları:
    - Sadece rakam (+ işareti başta opsiyonel)
    - Türkiye numaraları: +90XXXXXXXXXX veya 0XXXXXXXXXX → sadece rakam

    Desteklenen formatlar:
      "+90 532 123 45 67" → "05321234567"
      "0532 123 45 67"   → "05321234567"
      "532-123-4567"     → "5321234567"
      "(532) 123 4567"   → "5321234567"
      "+905321234567"    → "05321234567"
      "00905321234567"   → "05321234567"

    DS-160 telefon alanına yazılacak format:
      Türkiye: "05321234567" veya "5321234567"
      (site ülke kodunu ayrı soruyor, numara kısmı yazılıyor)
    """
    if not raw:
        return ""

    # Sadece rakam al
    digits = re.sub(r"\D", "", raw.strip())

    if not digits:
        return ""

    # 0090 ile başlıyorsa → 00'ı kaldır, 90 ile başlıyor
    if digits.startswith("0090"):
        digits = digits[2:]  # "90..." kalır

    # +90 veya 90 ile başlıyorsa Türkiye numarası
    if digits.startswith("90") and len(digits) >= 11:
        # 90XXXXXXXXXX → 0XXXXXXXXXX
        digits = "0" + digits[2:]

    return digits


def clean_phone_international(raw: str) -> str:
    """
    Uluslararası format için: ülke kodu dahil, sadece rakam.
    DS-160'da bazı alanlarda tam numara isteniyor.
    """
    if not raw:
        return ""
    # + işareti varsa koru, geri kalanı rakam
    raw = raw.strip()
    has_plus = raw.startswith("+")
    digits = re.sub(r"\D", "", raw)
    return ("+" + digits) if has_plus else digits


# ══════════════════════════════════════════════
# 4. ADRES
# ══════════════════════════════════════════════

def clean_address_line(raw: str, max_len: int = 40) -> str:
    """
    Adres satırı temizleme:
    - Türkçe → ASCII büyük harf
    - Noktalama (virgül, nokta, ünlem vb.) → boşluk
    - Tire, slash, # korunur (adres numarası için)
    - Çift boşluk → tek boşluk
    - maxlength

    Örnekler:
      "Atatürk Mah., No:5/3"  → "ATATURK MAH  NO 5/3"
      "123 Main St."           → "123 MAIN ST"
      "Apt. 4B, Floor 2"       → "APT  4B  FLOOR 2"
    """
    if not raw:
        return ""
    text = to_ascii_upper(raw)
    # Noktalama → boşluk (tire ve slash hariç)
    text = re.sub(r"[,\.!?;:\"\'`@\(\)]", " ", text)
    text = collapse_spaces(text)
    return text[:max_len]


def clean_city(raw: str, max_len: int = 20) -> str:
    """
    Şehir: sadece harf, boşluk, tire — maxlength değişken
    """
    if not raw:
        return ""
    text = to_ascii_upper(raw)
    text = re.sub(r"[^A-Z \-]", "", text)
    text = collapse_spaces(text)
    return text[:max_len]


def clean_zip(raw: str) -> str:
    """
    ZIP code: sadece rakam ve tire, maxlength=10
    Format: "12345" veya "12345-1234"
    """
    if not raw:
        return ""
    cleaned = re.sub(r"[^\d\-]", "", raw.strip())
    return cleaned[:10]


def clean_postal_code(raw: str, max_len: int = 10) -> str:
    """Genel posta kodu (Türkiye 5 hane vb.)"""
    if not raw:
        return ""
    return re.sub(r"\s+", "", raw.strip())[:max_len]


def clean_state_province(raw: str, max_len: int = 20) -> str:
    """
    State/Province metin alanı (Türkiye il adı vb.)
    """
    if not raw:
        return ""
    text = to_ascii_upper(raw)
    text = re.sub(r"[^A-Z \-]", "", text)
    text = collapse_spaces(text)
    return text[:max_len]


# ══════════════════════════════════════════════
# 5. ÜLKE / NATIONALITY
# ══════════════════════════════════════════════

# Türkçe ülke isimlerini İngilizce karşılığına çevirir
TR_COUNTRY_MAP = {
    "TÜRKİYE": "TURKEY",
    "TURKİYE": "TURKEY",
    "TÜRKIYE": "TURKEY",
    "TURKIYE": "TURKEY",   # ASCII normalize sonrası
    "TURKIYE": "TURKEY",
    "ABD": "UNITED STATES",
    "AMERİKA": "UNITED STATES",
    "AMERİKA BİRLEŞİK DEVLETLERİ": "UNITED STATES",
    "İNGİLTERE": "UNITED KINGDOM",
    "ALMANYA": "GERMANY",
    "FRANSA": "FRANCE",
    "İTALYA": "ITALY",
    "İSPANYA": "SPAIN",
    "YUNANİSTAN": "GREECE",
    "RUS": "RUSSIA",
    "RUSYA": "RUSSIA",
    "ÇİN": "CHINA",
    "JAPONYA": "JAPAN",
    "GÜNEY KORE": "SOUTH KOREA",
    "KUZEY KORE": "NORTH KOREA",
    "HOLLANDA": "NETHERLANDS",
    "BELÇİKA": "BELGIUM",
    "İSVİÇRE": "SWITZERLAND",
    "AVUSTURYA": "AUSTRIA",
    "AVUSTRALYA": "AUSTRALIA",
    "YENİ ZELANDA": "NEW ZEALAND",
    "MİSIR": "EGYPT",
    "MISIR": "EGYPT",
    "IRAK": "IRAQ",
    "İRAN": "IRAN",
    "SUUDİ ARABİSTAN": "SAUDI ARABIA",
    "BİRLEŞİK ARAP EMİRLİKLERİ": "UNITED ARAB EMIRATES",
    "BAE": "UNITED ARAB EMIRATES",
    "HİNDİSTAN": "INDIA",
    "PAKİSTAN": "PAKISTAN",
    "BREZILYA": "BRAZIL",
    "ARJANTIN": "ARGENTINA",
    "MEKSİKA": "MEXICO",
    "KANADA": "CANADA",
    "POLONYA": "POLAND",
    "ROMANYA": "ROMANIA",
    "UKRAYNA": "UKRAINE",
    "BULGARISTAN": "BULGARIA",
    "SIRBISTAN": "SERBIA",
    "HIRVATISTAN": "CROATIA",
    "BOSNA HERSEK": "BOSNIA-HERZEGOVINA",
    "KARADAĞ": "MONTENEGRO",
    "AZERBAYCAN": "AZERBAIJAN",
    "GÜRCİSTAN": "GEORGIA",
    "ERMENİSTAN": "ARMENIA",
    "ÖZBEKISTAN": "UZBEKISTAN",
    "KAZAKISTAN": "KAZAKHSTAN",
    "GÜNEY AFRİKA": "SOUTH AFRICA",
    "NIJERYA": "NIGERIA",
    "ETİYOPYA": "ETHIOPIA",
    "FİLİPİNLER": "PHILIPPINES",
    "ENDONEZYA": "INDONESIA",
    "MALEZYA": "MALAYSIA",
    "TAYLAND": "THAILAND",
    "VİETNAM": "VIETNAM",
    "TAYVAN": "TAIWAN",
}


def clean_country(raw: str) -> str:
    """
    Ülke adını DS-160 map'te aranabilir hale getirir.
    - Türkçe → İngilizce
    - ASCII büyük harf
    """
    if not raw:
        return ""
    text = to_ascii_upper(raw)
    # Türkçe → İngilizce map (normalize edilmiş hali)
    tr_norm = unicodedata.normalize("NFKD", raw.strip().upper())
    tr_norm = tr_norm.encode("ascii", "ignore").decode("ascii")
    if tr_norm in TR_COUNTRY_MAP:
        return TR_COUNTRY_MAP[tr_norm]
    if text in TR_COUNTRY_MAP:
        return TR_COUNTRY_MAP[text]
    return text


# ══════════════════════════════════════════════
# 6. YES / NO NORMALİZASYON
# ══════════════════════════════════════════════

def clean_yes_no(raw: str, default: str = "NO") -> str:
    """
    "evet", "yes", "y", "1", "true" → "YES"
    "hayır", "no", "n", "0", "false" → "NO"
    """
    if not raw:
        return default
    v = to_ascii_upper(raw)
    if v in ("YES", "Y", "EVET", "E", "TRUE", "1", "VAR"):
        return "YES"
    if v in ("NO", "N", "HAYIR", "H", "FALSE", "0", "YOK"):
        return "NO"
    return default


# ══════════════════════════════════════════════
# 7. PASAPORT NUMARASI
# ══════════════════════════════════════════════

def clean_passport_number(raw: str) -> str:
    """
    Pasaport numarası: alfanumerik, büyük harf, tire/boşluk kaldır
    Türk pasaportu: U12345678 formatı
    """
    if not raw:
        return ""
    # Sadece harf ve rakam
    cleaned = re.sub(r"[^A-Z0-9]", "", to_ascii_upper(raw))
    return cleaned[:20]


# ══════════════════════════════════════════════
# 8. E-POSTA
# ══════════════════════════════════════════════

def clean_email(raw: str) -> str:
    """
    Email: boşluk kaldır, küçük harf kabul (DS-160 büyük/küçük duyarsız)
    """
    if not raw:
        return ""
    return raw.strip().lower()[:100]


# ══════════════════════════════════════════════
# 9. GENEL METİN (açıklama, meslek vb.)
# ══════════════════════════════════════════════

def clean_explanation(raw: str, max_len: int = 250) -> str:
    """
    Serbest metin alanları (explanation, duties vb.)
    - Türkçe → ASCII
    - Büyük harf
    - Noktalama korunur (explanation alanlarında gerekli)
    - maxlength
    """
    if not raw:
        return ""
    text = to_ascii_upper(raw)
    text = collapse_spaces(text)
    return text[:max_len]


def clean_employer_name(raw: str, max_len: int = 50) -> str:
    """İşveren/okul adı: Türkçe → ASCII, noktalama → boşluk"""
    if not raw:
        return ""
    text = to_ascii_upper(raw)
    text = re.sub(r"[,\.!?;:\"\'`@]", " ", text)
    text = collapse_spaces(text)
    return text[:max_len]


# ══════════════════════════════════════════════
# 10. MARITAL STATUS NORMALİZASYON
# ══════════════════════════════════════════════

def clean_marital_status(raw: str) -> str:
    """
    Türkçe veya İngilizce medeni durum → DS-160 değeri
    """
    TR_MARITAL = {
        "BEKAR": "SINGLE",
        "BEKÂR": "SINGLE",
        "EVLI": "MARRIED",
        "EVLİ": "MARRIED",
        "BOŞANMIŞ": "DIVORCED",
        "BOSANMIS": "DIVORCED",
        "DUL": "WIDOWED",
        "AYRILMIŞ": "LEGALLY SEPARATED",
        "AYRILMIS": "LEGALLY SEPARATED",
    }
    if not raw:
        return "SINGLE"
    text = to_ascii_upper(raw)
    return TR_MARITAL.get(text, text)


# ══════════════════════════════════════════════
# 11. GENDER NORMALİZASYON
# ══════════════════════════════════════════════

def clean_gender(raw: str) -> str:
    """
    "erkek", "male", "m", "bay" → "M"
    "kadın", "female", "f", "bayan" → "F"
    """
    if not raw:
        return ""
    v = to_ascii_upper(raw)
    if v in ("M", "MALE", "ERKEK", "BAY", "MAN", "ADAM"):
        return "M"
    if v in ("F", "FEMALE", "KADIN", "BAYAN", "WOMAN"):
        return "F"
    return v[:1]  # ilk harfi dön


# ══════════════════════════════════════════════
# ANA CLEANING FONKSİYONU
# ══════════════════════════════════════════════

def clean_all(raw: dict) -> dict:
    """
    JSON'dan gelen ham dict'i DS-160 bot için hazırlar.
    Tüm alanları tek seferde temizler.

    Kullanım:
        raw = {
            "SURNAME": "Parlak",
            "GIVEN_NAME": "Şevket Metehan",
            "BIRTH_DATE": "20/02/1993",
            "PRIMARY_PHONE": "+90 532 123 45 67",
            "HOME_ADDRESS": "Atatürk Mah., No:5/3, Daire:7",
            ...
        }
        data = clean_all(raw)
        fill_personal1_page(wait, driver, data)
    """
    data = {}

    # ── KİMLİK BİLGİLERİ ──────────────────────────────────
    data["SURNAME"]          = clean_name(raw.get("SURNAME", ""), 33)
    data["GIVEN_NAME"]       = clean_name(raw.get("GIVEN_NAME", ""), 33)
    data["FULL_NAME_NATIVE"] = clean_native_name(raw.get("FULL_NAME_NATIVE", ""), 100)
    data["GENDER"]           = clean_gender(raw.get("GENDER", ""))
    data["MARITAL_STATUS"]   = clean_marital_status(raw.get("MARITAL_STATUS", ""))
    data["OTHER_NAME"]       = clean_yes_no(raw.get("OTHER_NAME", "NO"))
    data["NATIONALITY"]      = clean_country(raw.get("NATIONALITY", ""))
    data["OTHER_NATIONALITY"]= clean_yes_no(raw.get("OTHER_NATIONALITY", "NO"))
    data["PERM_RES_OTHER"]   = clean_yes_no(raw.get("PERM_RES_OTHER", "NO"))

    # ── DOĞUM TARİHİ ──────────────────────────────────────
    birth_raw = raw.get("BIRTH_DATE") or raw.get("DATE_OF_BIRTH") or ""
    if birth_raw:
        try:
            bd = clean_date_fields(birth_raw, "BIRTH")
            data.update(bd)
        except ValueError as e:
            print(f"⚠️  BIRTH_DATE: {e}")
    # Ayrı ayrı verilmişse
    if raw.get("BIRTH_DAY"):
        data["BIRTH_DAY"]   = str(int(raw["BIRTH_DAY"]))
        data["BIRTH_DAY_PADDED"] = f"{int(raw['BIRTH_DAY']):02d}"
    if raw.get("BIRTH_MONTH"):
        m = _normalize_month(str(raw["BIRTH_MONTH"]))
        if m:
            data["BIRTH_MONTH"] = m
            data["BIRTH_MONTH3"] = NUM_TO_MON3[m]
    if raw.get("BIRTH_YEAR"):
        data["BIRTH_YEAR"] = str(raw["BIRTH_YEAR"]).strip()

    # ── DOĞUM YERİ ────────────────────────────────────────
    data["BIRTH_CITY"]    = clean_city(raw.get("BIRTH_CITY", ""), 20)
    data["BIRTH_STATE"]   = clean_state_province(raw.get("BIRTH_STATE", ""), 20)
    data["BIRTH_COUNTRY"] = clean_country(raw.get("BIRTH_COUNTRY", ""))

    # ── KİMLİK NUMARALARI ─────────────────────────────────
    national_id = raw.get("NATIONAL_ID", "")
    data["NATIONAL_ID"] = re.sub(r"\s+", "", str(national_id).strip())[:20] if national_id else ""

    data["SSN"]    = raw.get("SSN", "")    # normalize SSN ayrı yapılıyor
    data["TAX_ID"] = raw.get("TAX_ID", "")

    # ── SEYAHAT TARİHİ ────────────────────────────────────
    arrival_raw = (
        raw.get("INTENDED_ARRIVAL_DATE") or
        raw.get("ARRIVAL_DATE") or ""
    )
    if arrival_raw:
        try:
            ad = clean_date_fields(arrival_raw, "INTENDED_ARRIVAL")
            data.update(ad)
        except ValueError as e:
            print(f"⚠️  ARRIVAL_DATE: {e}")
    # Ayrı ayrı
    for k in ("INTENDED_ARRIVAL_DAY", "INTENDED_ARRIVAL_MONTH", "INTENDED_ARRIVAL_YEAR"):
        if raw.get(k):
            data[k] = str(raw[k]).strip()

    # ── SEYAHAT BİLGİLERİ ─────────────────────────────────
    data["PURPOSE_OF_TRIP"]     = to_ascii_upper(raw.get("PURPOSE_OF_TRIP", ""))
    data["PURPOSE_SUBCATEGORY"] = to_ascii_upper(raw.get("PURPOSE_SUBCATEGORY", ""))
    data["SPECIFIC_TRAVEL"]     = clean_yes_no(raw.get("SPECIFIC_TRAVEL", "NO"))
    data["TRAVEL_LOS_VALUE"]    = str(raw.get("TRAVEL_LOS_VALUE", "1")).strip()
    data["TRAVEL_LOS_UNIT"]     = to_ascii_upper(raw.get("TRAVEL_LOS_UNIT", "D"))

    # ── ABD ADRESİ ────────────────────────────────────────
    data["US_ADDRESS1"] = clean_address_line(raw.get("US_ADDRESS1", ""), 40)
    data["US_ADDRESS2"] = clean_address_line(raw.get("US_ADDRESS2", ""), 40)
    data["US_CITY"]     = clean_city(raw.get("US_CITY", ""), 20)
    data["US_STATE"]    = to_ascii_upper(raw.get("US_STATE", ""))
    data["US_ZIP"]      = clean_zip(raw.get("US_ZIP", ""))

    # ── EV ADRESİ ─────────────────────────────────────────
    data["HOME_ADDRESS"]     = clean_address_line(raw.get("HOME_ADDRESS", ""), 40)
    data["HOME_CITY"]        = clean_city(raw.get("HOME_CITY", ""), 20)
    data["HOME_STATE"]       = clean_state_province(raw.get("HOME_STATE", ""), 20)
    data["HOME_POSTAL_CODE"] = clean_postal_code(raw.get("HOME_POSTAL_CODE", ""))
    data["HOME_COUNTRY"]     = clean_country(raw.get("HOME_COUNTRY", ""))
    data["MAILING_SAME_AS_HOME"] = clean_yes_no(raw.get("MAILING_SAME_AS_HOME", "YES"))

    # ── TELEFON (maxlength=15, minlength=5) ──────────────
    def _clean_phone_15(raw_p):
        """DS-160 telefon: + korunur, rakamlar alınır, maxlength=15"""
        if not raw_p:
            return ""
        raw_p = str(raw_p).strip()
        has_plus = raw_p.startswith("+")
        digits = re.sub(r"\D", "", raw_p)
        result = ("+" + digits) if has_plus else digits
        return result[:15]

    data["PRIMARY_PHONE"]       = _clean_phone_15(raw.get("PRIMARY_PHONE", ""))
    data["MOBILE_PHONE"]        = _clean_phone_15(raw.get("MOBILE_PHONE", ""))
    data["WORK_PHONE"]          = _clean_phone_15(raw.get("WORK_PHONE", ""))
    data["HAS_ADDITIONAL_PHONE"]= clean_yes_no(raw.get("HAS_ADDITIONAL_PHONE", "NO"))
    data["ADDITIONAL_PHONE_NUM"]= _clean_phone_15(raw.get("ADDITIONAL_PHONE_NUM", ""))

    # ── E-POSTA (maxlength=50) ────────────────────────────
    data["EMAIL"]               = (raw.get("EMAIL","") or "").strip().lower()[:50]
    data["HAS_ADDITIONAL_EMAIL"]= clean_yes_no(raw.get("HAS_ADDITIONAL_EMAIL", "NO"))
    data["ADDITIONAL_EMAIL1"]   = (raw.get("ADDITIONAL_EMAIL1","") or "").strip().lower()[:50]

    # ── SOSYAL MEDYA ──────────────────────────────────────
    _SM_MAP = {
        "ASK.FM":"ASKF","ASKFM":"ASKF","DOUBAN":"DUBN","FACEBOOK":"FCBK",
        "FLICKR":"FLKR","GOOGLE+":"GOGL","GOOGLE PLUS":"GOGL","INSTAGRAM":"INST",
        "LINKEDIN":"LINK","MYSPACE":"MYSP","PINTEREST":"PTST",
        "QZONE (QQ)":"QZNE","QZONE":"QZNE","REDDIT":"RDDT",
        "SINA WEIBO":"SWBO","WEIBO":"SWBO","TENCENT WEIBO":"TWBO","TUMBLR":"TUMB",
        "TWITTER":"TWIT","X":"TWIT","X(TWITTER)":"TWIT",
        "TWOO":"TWOO","VINE":"VINE","VKONTAKTE (VK)":"VKON","VK":"VKON",
        "YOUKU":"YUKU","YOUTUBE":"YTUB","NONE":"NONE","NO":"NONE","YOK":"NONE",
    }
    sm_list = raw.get("SOCIAL_MEDIA_LIST", [])
    cleaned_sm = []
    for entry in sm_list:
        plat = _SM_MAP.get(to_ascii_upper(entry.get("platform","")), "NONE")
        user = (entry.get("username") or "").strip()[:50]
        cleaned_sm.append({"platform": plat, "username": user})
    data["SOCIAL_MEDIA_LIST"] = cleaned_sm

    # Eski format (virgülle ayrılmış)
    if raw.get("SOCIAL_MEDIA") and not sm_list:
        plats = [p.strip() for p in raw["SOCIAL_MEDIA"].split(",") if p.strip()]
        users = [u.strip() for u in (raw.get("SOCIAL_MEDIA_USERNAME","") or "").split(",")]
        while len(users) < len(plats):
            users.append("")
        data["SOCIAL_MEDIA_LIST"] = [
            {"platform": _SM_MAP.get(to_ascii_upper(p), "NONE"), "username": u[:50]}
            for p, u in zip(plats, users)
        ]

    data["ADDITIONAL_SOCIAL"] = clean_yes_no(raw.get("ADDITIONAL_SOCIAL", "NO"))
    add_sm = raw.get("ADDITIONAL_SOCIAL_LIST", [])
    data["ADDITIONAL_SOCIAL_LIST"] = [
        {"platform": to_ascii_upper(e.get("platform",""))[:50],
         "username": (e.get("username","") or "").strip()[:50]}
        for e in add_sm
    ]

    # ── PASAPORT ──────────────────────────────────────────
    _PPT_TYPE = {
        "R":"R","REGULAR":"R","O":"O","OFFICIAL":"O","D":"D","DIPLOMATIC":"D",
        "L":"L","LAISSEZ-PASSER":"L","LAISSEZ":"L","LAISSEZ PASSER":"L",
        "T":"T","OTHER":"T",
    }
    ppt_type_raw = to_ascii_upper(raw.get("PASSPORT_TYPE","REGULAR"))
    data["PASSPORT_TYPE"] = _PPT_TYPE.get(ppt_type_raw, "R")

    data["PASSPORT_NUMBER"] = re.sub(r"[^A-Z0-9]","", to_ascii_upper(
        raw.get("PASSPORT_NUMBER","")
    ))[:20]
    data["PASSPORT_BOOK_NUMBER"] = re.sub(r"[^A-Z0-9]","", to_ascii_upper(
        raw.get("PASSPORT_BOOK_NUMBER","")
    ))[:20]
    data["PASSPORT_ISSUED_COUNTRY"]    = clean_country(raw.get("PASSPORT_ISSUED_COUNTRY",""))
    data["PASSPORT_ISSUED_CITY"]       = clean_city(raw.get("PASSPORT_ISSUED_CITY",""), 25)  # maxlength=25
    data["PASSPORT_ISSUED_STATE"]      = clean_state_province(raw.get("PASSPORT_ISSUED_STATE",""), 25)
    data["PASSPORT_ISSUED_IN_COUNTRY"] = clean_country(raw.get("PASSPORT_ISSUED_IN_COUNTRY","")
                                                        or raw.get("PASSPORT_ISSUED_COUNTRY",""))

    issue_raw = raw.get("PASSPORT_ISSUE_DATE", "")
    if issue_raw:
        try:
            pid = clean_date_fields(issue_raw, "PASSPORT_ISSUE")
            data["PASSPORT_ISSUE_DATE"] = (
                f"{pid['PASSPORT_ISSUE_DAY_PADDED']}-"
                f"{pid['PASSPORT_ISSUE_MONTH3']}-"
                f"{pid['PASSPORT_ISSUE_YEAR']}"
            )
        except ValueError as e:
            print(f"⚠️  PASSPORT_ISSUE_DATE: {e}")
            data["PASSPORT_ISSUE_DATE"] = issue_raw

    expiry_raw = raw.get("PASSPORT_EXPIRY_DATE", "")
    if expiry_raw:
        try:
            ped = clean_date_fields(expiry_raw, "PASSPORT_EXPIRY")
            data["PASSPORT_EXPIRY_DATE"] = (
                f"{ped['PASSPORT_EXPIRY_DAY_PADDED']}-"
                f"{ped['PASSPORT_EXPIRY_MONTH3']}-"
                f"{ped['PASSPORT_EXPIRY_YEAR']}"
            )
        except ValueError as e:
            print(f"⚠️  PASSPORT_EXPIRY_DATE: {e}")
            data["PASSPORT_EXPIRY_DATE"] = expiry_raw

    data["PASSPORT_LOST"] = clean_yes_no(raw.get("PASSPORT_LOST", "NO"))

    # ── İŞ / EĞİTİM ──────────────────────────────────────
    _OCC_MAP = {
        "A":"A","AGRICULTURE":"A",
        "AP":"AP","ARTIST":"AP","ARTIST/PERFORMER":"AP","PERFORMER":"AP","SANATCI":"AP",
        "B":"B","BUSINESS":"B",
        "CM":"CM","COMMUNICATIONS":"CM",
        "CS":"CS","COMPUTER SCIENCE":"CS","IT":"CS","BILISIM":"CS",
        "C":"C","CULINARY":"C","CULINARY/FOOD SERVICES":"C",
        "ED":"ED","EDUCATION":"ED","TEACHER":"ED","OGRETMEN":"ED",
        "EN":"EN","ENGINEERING":"EN","ENGINEER":"EN","MUHENDIS":"EN",
        "G":"G","GOVERNMENT":"G",
        "H":"H","HOMEMAKER":"H",
        "LP":"LP","LEGAL":"LP","LEGAL PROFESSION":"LP","LAWYER":"LP","AVUKAT":"LP",
        "MH":"MH","MEDICAL":"MH","MEDICAL/HEALTH":"MH","DOCTOR":"MH","HEALTH":"MH",
        "M":"M","MILITARY":"M",
        "NS":"NS","NATURAL SCIENCE":"NS","NATURAL_SCIENCE":"NS",
        "N":"N","NOT EMPLOYED":"N","NOT_EMPLOYED":"N","UNEMPLOYED":"N","ISSIZ":"N",
        "PS":"PS","PHYSICAL SCIENCES":"PS","PHYSICAL SCIENCE":"PS","PHYSICAL_SCIENCE":"PS",
        "RV":"RV","RELIGIOUS":"RV","RELIGIOUS VOCATION":"RV",
        "R":"R","RESEARCH":"R",
        "RT":"RT","RETIRED":"RT","EMEKLI":"RT",
        "SS":"SS","SOCIAL SCIENCE":"SS","SOCIAL_SCIENCE":"SS",
        "S":"S","STUDENT":"S","OGRENCI":"S",
        "O":"O","OTHER":"O","DIGER":"O",
    }
    occ_raw = to_ascii_upper(raw.get("PRESENT_OCCUPATION","NOT_EMPLOYED"))
    data["PRESENT_OCCUPATION"] = _OCC_MAP.get(occ_raw, "O")
    data["PRESENT_OCCUPATION_EXPLAIN"] = to_ascii_upper(
        raw.get("PRESENT_OCCUPATION_EXPLAIN","")
    )[:4000]
    data["EMP_SCH_NAME"]    = re.sub(r"\s+", " ", re.sub(
        r"[,\.!?;:\"\'`@]", " ",
        to_ascii_upper(raw.get("EMP_SCH_NAME",""))
    )).strip()[:75]   # maxlength=75 (eski 50 yanlıştı)
    data["EMP_SCH_ADDR1"]   = clean_address_line(raw.get("EMP_SCH_ADDR1",""), 40)
    data["EMP_SCH_ADDR2"]   = clean_address_line(raw.get("EMP_SCH_ADDR2",""), 40)
    data["EMP_SCH_CITY"]    = clean_city(raw.get("EMP_SCH_CITY",""), 20)
    data["EMP_SCH_STATE"]   = clean_state_province(raw.get("EMP_SCH_STATE",""), 20)
    data["EMP_SCH_POSTAL"]  = clean_postal_code(raw.get("EMP_SCH_POSTAL",""))
    data["EMP_SCH_COUNTRY"] = clean_country(raw.get("EMP_SCH_COUNTRY",""))
    data["EMP_SCH_PHONE"]   = _clean_phone_15(raw.get("EMP_SCH_PHONE",""))
    data["EMP_MONTHLY_SALARY"] = re.sub(r"\D","", str(raw.get("EMP_MONTHLY_SALARY","") or ""))[:15]
    data["EMP_DUTIES"]      = to_ascii_upper(raw.get("EMP_DUTIES",""))[:4000]

    emp_start = raw.get("EMP_SCH_START_DATE","")
    if emp_start:
        # Ham bırak — work_education.py parse_date ile işler
        data["EMP_SCH_START_DATE"] = str(emp_start).strip()

    # ── AİLE ──────────────────────────────────────────────
    _US_STATUS = {
        "S":"S","US CITIZEN":"S","CITIZEN":"S","VATANDAS":"S",
        "C":"C","LPR":"C","LEGAL PERMANENT RESIDENT":"C","GREEN CARD":"C",
        "P":"P","NONIMMIGRANT":"P","VIZE":"P",
        "O":"O","OTHER":"O","DONT KNOW":"O","BILMIYORUM":"O",
    }
    _US_REL_TYPE = {
        "S":"S","SPOUSE":"S","ES":"S",
        "F":"F","FIANCE":"F","FIANCEE":"F","NISANLI":"F",
        "C":"C","CHILD":"C","COCUK":"C",
        "B":"B","SIBLING":"B","KARDES":"B",
    }

    data["FATHER_SURNAME"] = clean_name(raw.get("FATHER_SURNAME", ""), 33)
    data["FATHER_GIVEN"]   = clean_name(raw.get("FATHER_GIVEN", ""), 33)
    data["MOTHER_SURNAME"] = clean_name(raw.get("MOTHER_SURNAME", ""), 33)
    data["MOTHER_GIVEN"]   = clean_name(raw.get("MOTHER_GIVEN", ""), 33)

    for parent in ("FATHER", "MOTHER"):
        dob_raw = raw.get(f"{parent}_DOB", "")
        if dob_raw:
            try:
                pd = clean_date_fields(dob_raw, f"{parent}_DOB")
                data[f"{parent}_DOB"] = (
                    f"{pd[f'{parent}_DOB_DAY_PADDED']}-"
                    f"{pd[f'{parent}_DOB_MONTH3']}-"
                    f"{pd[f'{parent}_DOB_YEAR']}"
                )
            except ValueError:
                data[f"{parent}_DOB"] = dob_raw
        data[f"{parent}_DOB_NA"]   = clean_yes_no(raw.get(f"{parent}_DOB_NA", "NO"))
        data[f"{parent}_IN_US"]    = clean_yes_no(raw.get(f"{parent}_IN_US", "NO"))
        data[f"{parent}_US_STATUS"]= _US_STATUS.get(
            to_ascii_upper(raw.get(f"{parent}_US_STATUS", "OTHER")), "O"
        )

    # US Immediate Relatives
    data["US_IMMEDIATE_RELATIVE"] = clean_yes_no(raw.get("US_IMMEDIATE_RELATIVE","NO"))
    rels_raw = raw.get("US_RELATIVES",[])
    cleaned_rels = []
    for r in rels_raw:
        cleaned_rels.append({
            "surname": clean_name(r.get("surname",""), 33),
            "given":   clean_name(r.get("given",""),   33),
            "type":    _US_REL_TYPE.get(to_ascii_upper(r.get("type","C")),   "C"),
            "status":  _US_STATUS.get( to_ascii_upper(r.get("status","OTHER")),"O"),
        })
    data["US_RELATIVES"] = cleaned_rels

    # Numaralı key formatı
    for i in range(1, 20):
        if not raw.get(f"US_REL{i}_SURNAME"):
            break
        data[f"US_REL{i}_SURNAME"] = clean_name(raw[f"US_REL{i}_SURNAME"], 33)
        data[f"US_REL{i}_GIVEN"]   = clean_name(raw.get(f"US_REL{i}_GIVEN",""), 33)
        data[f"US_REL{i}_TYPE"]    = _US_REL_TYPE.get(to_ascii_upper(raw.get(f"US_REL{i}_TYPE","C")),"C")
        data[f"US_REL{i}_STATUS"]  = _US_STATUS.get(to_ascii_upper(raw.get(f"US_REL{i}_STATUS","O")),"O")

    # ── EŞ (varsa) ────────────────────────────────────────
    _SPOUSE_ADDR_TYPE = {
        "H":"H","HOME":"H","SAME AS HOME":"H","EV":"H",
        "M":"M","MAILING":"M",
        "U":"U","US CONTACT":"U",
        "D":"D","DO NOT KNOW":"D","UNKNOWN":"D",
        "O":"O","OTHER":"O","DIGER":"O",
    }
    data["SPOUSE_SURNAME"]       = clean_name(raw.get("SPOUSE_SURNAME",""), 33)
    data["SPOUSE_GIVEN_NAME"]    = clean_name(raw.get("SPOUSE_GIVEN_NAME",""), 33)
    data["SPOUSE_NATIONALITY"]   = clean_country(raw.get("SPOUSE_NATIONALITY",""))
    data["SPOUSE_POB_CITY"]      = clean_city(raw.get("SPOUSE_POB_CITY",""), 20)
    data["SPOUSE_POB_COUNTRY"]   = clean_country(raw.get("SPOUSE_POB_COUNTRY",""))
    data["SPOUSE_ADDRESS_TYPE"]  = _SPOUSE_ADDR_TYPE.get(
        to_ascii_upper(raw.get("SPOUSE_ADDRESS_TYPE","HOME")), "H"
    )

    spouse_dob = raw.get("SPOUSE_DOB","")
    if spouse_dob:
        try:
            sd = clean_date_fields(spouse_dob, "SPOUSE_DOB")
            data["SPOUSE_DOB"] = (
                f"{sd['SPOUSE_DOB_DAY_PADDED']}-"
                f"{sd['SPOUSE_DOB_MONTH3']}-"
                f"{sd['SPOUSE_DOB_YEAR']}"
            )
        except ValueError:
            data["SPOUSE_DOB"] = spouse_dob

    # Deceased spouse (WIDOWED)
    data["DECEASED_SPOUSE_SURNAME"]    = clean_name(raw.get("DECEASED_SPOUSE_SURNAME",""), 33)
    data["DECEASED_SPOUSE_GIVEN"]      = clean_name(raw.get("DECEASED_SPOUSE_GIVEN",""), 33)
    data["DECEASED_SPOUSE_NATIONALITY"]= clean_country(raw.get("DECEASED_SPOUSE_NATIONALITY",""))
    data["DECEASED_SPOUSE_POB_CITY"]   = clean_city(raw.get("DECEASED_SPOUSE_POB_CITY",""), 20)
    data["DECEASED_SPOUSE_POB_COUNTRY"]= clean_country(raw.get("DECEASED_SPOUSE_POB_COUNTRY",""))
    dec_dob = raw.get("DECEASED_SPOUSE_DOB","")
    if dec_dob:
        try:
            dd = clean_date_fields(dec_dob,"DECEASED_SPOUSE_DOB")
            data["DECEASED_SPOUSE_DOB"] = (
                f"{dd['DECEASED_SPOUSE_DOB_DAY_PADDED']}-"
                f"{dd['DECEASED_SPOUSE_DOB_MONTH3']}-"
                f"{dd['DECEASED_SPOUSE_DOB_YEAR']}"
            )
        except ValueError:
            data["DECEASED_SPOUSE_DOB"] = dec_dob

    # Former spouse (DIVORCED)
    data["NUM_PREV_SPOUSES"] = str(raw.get("NUM_PREV_SPOUSES","1"))[:2]
    data["FORMER_SPOUSE_SURNAME"]  = clean_name(raw.get("FORMER_SPOUSE_SURNAME",""), 33)
    data["FORMER_SPOUSE_GIVEN"]    = clean_name(raw.get("FORMER_SPOUSE_GIVEN",""), 33)
    data["FORMER_SPOUSE_NATL"]     = clean_country(raw.get("FORMER_SPOUSE_NATL","") or raw.get("FORMER_SPOUSE_NATIONALITY",""))
    data["FORMER_SPOUSE_POB_CITY"] = clean_city(raw.get("FORMER_SPOUSE_POB_CITY",""), 20)
    data["FORMER_SPOUSE_POB_COUNTRY"] = clean_country(raw.get("FORMER_SPOUSE_POB_COUNTRY",""))
    data["FORMER_MARRIAGE_END_REASON"] = to_ascii_upper(raw.get("FORMER_MARRIAGE_END_REASON","DIVORCE"))[:4000]
    data["FORMER_MARRIAGE_END_COUNTRY"]= clean_country(raw.get("FORMER_MARRIAGE_END_COUNTRY",""))
    # Tarihler ham bırakılıyor — spouse.py parse_date ile işler
    for dk in ("FORMER_SPOUSE_DOB","FORMER_MARRIAGE_DATE","FORMER_MARRIAGE_END_DATE"):
        if raw.get(dk):
            data[dk] = str(raw[dk]).strip()

    # ── PAYER ─────────────────────────────────────────────
    data["PAYER_TYPE"]          = to_ascii_upper(raw.get("PAYER_TYPE", "SELF"))
    data["PAYER_SURNAME"]       = clean_name(raw.get("PAYER_SURNAME", ""), 33)
    data["PAYER_GIVEN_NAME"]    = clean_name(raw.get("PAYER_GIVEN_NAME", ""), 33)
    data["PAYER_PHONE"]         = _clean_phone_15(raw.get("PAYER_PHONE", ""))
    data["PAYER_EMAIL"]         = (raw.get("PAYER_EMAIL","") or "").strip().lower()[:50]
    data["PAYER_RELATIONSHIP"]  = to_ascii_upper(raw.get("PAYER_RELATIONSHIP", ""))
    data["PAYER_ADDRESS_SAME"]  = clean_yes_no(raw.get("PAYER_ADDRESS_SAME", "YES"))
    data["PAYER_ADDRESS1"]      = clean_address_line(raw.get("PAYER_ADDRESS1", ""), 40)
    data["PAYER_ADDRESS2"]      = clean_address_line(raw.get("PAYER_ADDRESS2", ""), 40)
    data["PAYER_CITY"]          = clean_city(raw.get("PAYER_CITY", ""), 20)
    data["PAYER_STATE"]         = clean_state_province(raw.get("PAYER_STATE", ""), 20)
    data["PAYER_ZIP"]           = clean_zip(raw.get("PAYER_ZIP", ""))
    data["PAYER_COUNTRY"]       = clean_country(raw.get("PAYER_COUNTRY", ""))
    data["PAYER_COMPANY_NAME"]  = clean_employer_name(raw.get("PAYER_COMPANY_NAME", ""), 50)
    data["PAYER_COMPANY_PHONE"] = _clean_phone_15(raw.get("PAYER_COMPANY_PHONE", ""))
    data["PAYER_COMPANY_RELATIONSHIP"] = to_ascii_upper(raw.get("PAYER_COMPANY_RELATIONSHIP", ""))

    # ── US POINT OF CONTACT ───────────────────────────────
    _POC_REL = {
        # HTML values (C=FRIEND, P=EMPLOYER, H=SCHOOL OFFICIAL!)
        "R":"R","RELATIVE":"R","AKRABA":"R",
        "S":"S","SPOUSE":"S","ES":"S",
        "C":"C","FRIEND":"C","ARKADAS":"C",       # C=FRIEND (F değil!)
        "B":"B","BUSINESS ASSOCIATE":"B",
        "P":"P","EMPLOYER":"P","ISVEREN":"P",      # P=EMPLOYER (E değil!)
        "H":"H","SCHOOL OFFICIAL":"H","OKUL":"H",
        "O":"O","OTHER":"O","DIGER":"O",
        # Eski kod hatalarını düzelt
        "F":"C",  # Eski F=FRIEND → Doğru C
        "E":"P",  # Eski E=EMPLOYER → Doğru P
    }
    data["US_POC_SURNAME"]    = clean_name(raw.get("US_POC_SURNAME",""), 33)
    data["US_POC_GIVEN_NAME"] = clean_name(raw.get("US_POC_GIVEN_NAME",""), 33)

    org_raw = to_ascii_upper(raw.get("US_POC_ORG_NAME","") or raw.get("US_POC_ORGANIZATION",""))
    org_clean = re.sub(r"[,\.!?;:\"\'`@]"," ", org_raw)
    data["US_POC_ORG_NAME"]  = re.sub(r"\s+"," ", org_clean).strip()[:33]

    poc_rel_raw = to_ascii_upper(raw.get("US_POC_RELATION","OTHER"))
    data["US_POC_RELATION"]  = _POC_REL.get(poc_rel_raw, "O")

    data["US_POC_ADDR1"]     = clean_address_line(raw.get("US_POC_ADDR1",""), 40)
    data["US_POC_ADDR2"]     = clean_address_line(raw.get("US_POC_ADDR2",""), 40)
    data["US_POC_CITY"]      = clean_city(raw.get("US_POC_CITY",""), 20)
    data["US_POC_STATE"]     = to_ascii_upper(raw.get("US_POC_STATE",""))
    data["US_POC_ZIP"]       = clean_zip(raw.get("US_POC_ZIP",""))
    data["US_POC_PHONE"]     = _clean_phone_15(raw.get("US_POC_PHONE",""))
    data["US_POC_EMAIL"]     = (raw.get("US_POC_EMAIL","") or "").strip().lower()[:50]

    # ── TRAVEL COMPANIONS ────────────────────────────────
    _COMPANION_REL_MAP = {
        "SPOUSE":"S","ES":"S","EŞ":"S","EÃ":"S",
        "CHILD":"C","COCUK":"C","ÇOCUK":"C",
        "PARENT":"P","EBEVEYN":"P","ANNE":"P","BABA":"P",
        "RELATIVE":"R","AKRABA":"R",
        "FRIEND":"F","ARKADAS":"F","ARKADAŞ":"F",
        "BUSINESS":"B","IS":"B","İŞ":"B",
        "OTHER":"O","DIGER":"O","DİĞER":"O",
        "S":"S","C":"C","P":"P","R":"R","F":"F","B":"B","O":"O",
    }
    data["TRAVEL_COMPANIONS"] = clean_yes_no(raw.get("TRAVEL_COMPANIONS","NO"))
    data["GROUP_TRAVEL"]      = clean_yes_no(raw.get("GROUP_TRAVEL","NO"))
    gn = to_ascii_upper(raw.get("GROUP_NAME",""))
    gn = re.sub(r"[,\.!?;:\"\'`@]"," ",gn)
    data["GROUP_NAME"] = re.sub(r"\s+"," ",gn).strip()[:75]

    companions_raw = raw.get("TRAVEL_COMPANIONS_LIST",[])
    cleaned_comp = []
    for entry in companions_raw:
        sn  = clean_name(entry.get("surname",""),33)
        giv = clean_name(entry.get("given",""),33)
        rel = _COMPANION_REL_MAP.get(to_ascii_upper(entry.get("relationship","OTHER")),"O")
        if sn or giv:
            cleaned_comp.append({"surname":sn,"given":giv,"relationship":rel})
    data["TRAVEL_COMPANIONS_LIST"] = cleaned_comp

    for i in range(20):
        px = f"TRAV_COMP_{i:02d}_"
        sn  = raw.get(f"{px}SURNAME","")
        giv = raw.get(f"{px}GIVEN","")
        if not sn and not giv:
            break
        rel = _COMPANION_REL_MAP.get(to_ascii_upper(raw.get(f"{px}RELATIONSHIP","OTHER")),"O")
        data[f"{px}SURNAME"]      = clean_name(sn,33)
        data[f"{px}GIVEN"]        = clean_name(giv,33)
        data[f"{px}RELATIONSHIP"] = rel

    # ── ÖNCEKİ ABD SEYAHATİ ──────────────────────────────
    data["PREV_US_TRAVEL"]      = clean_yes_no(raw.get("PREV_US_TRAVEL", "NO"))
    data["US_DRIVER_LICENSE"]   = clean_yes_no(raw.get("US_DRIVER_LICENSE", "NO"))
    data["PREV_VISA"]           = clean_yes_no(raw.get("PREV_VISA", "NO"))
    data["PREV_VISA_SAME_TYPE"]    = clean_yes_no(raw.get("PREV_VISA_SAME_TYPE", "YES"))
    data["PREV_VISA_SAME_COUNTRY"] = clean_yes_no(raw.get("PREV_VISA_SAME_COUNTRY", "YES"))
    data["PREV_VISA_TEN_PRINTED"]  = clean_yes_no(raw.get("PREV_VISA_TEN_PRINTED", "YES"))
    data["PREV_VISA_LOST"]         = clean_yes_no(raw.get("PREV_VISA_LOST", "NO"))
    data["PREV_VISA_CANCELLED"]    = clean_yes_no(raw.get("PREV_VISA_CANCELLED", "NO"))
    data["PREV_VISA_REFUSED"]      = clean_yes_no(raw.get("PREV_VISA_REFUSED", "NO"))
    data["IV_PETITION"]            = clean_yes_no(raw.get("IV_PETITION", "NO"))

    # Visa number: maxlength=12, alfanumerik
    vn = re.sub(r"[^A-Z0-9]", "", to_ascii_upper(raw.get("PREV_VISA_NUMBER", "")))[:12]
    data["PREV_VISA_NUMBER"] = vn

    # Lost year: 4 hane
    ly = re.sub(r"\D", "", str(raw.get("PREV_VISA_LOST_YEAR", "")))[:4]
    data["PREV_VISA_LOST_YEAR"] = ly

    # Explanation alanları (maxlength=4000)
    for expl_key in ("PREV_VISA_LOST_EXPL", "PREV_VISA_CANCELLED_EXPL",
                     "PREV_VISA_REFUSED_EXPL", "IV_PETITION_EXPL"):
        data[expl_key] = clean_explanation(raw.get(expl_key, ""), 4000)

    # Ziyaret listesi
    visits_raw = raw.get("PREV_VISITS", [])
    cleaned_visits = []
    for v in visits_raw:
        date_raw = v.get("date", "") or f"{v.get('day','')}/{v.get('month','')}/{v.get('year','')}"
        parsed = parse_date(date_raw)
        if parsed:
            los_val = str(v.get("los_value", "1")).strip()
            los_unit_raw = to_ascii_upper(v.get("los_unit", "D"))
            _LOS = {"Y":"Y","YEAR":"Y","YEARS":"Y","M":"M","MONTH":"M","MONTHS":"M",
                    "W":"W","WEEK":"W","WEEKS":"W","D":"D","DAY":"D","DAYS":"D",
                    "H":"H","GUN":"D","HAFTA":"W","AY":"M","YIL":"Y"}
            cleaned_visits.append({
                "day":       parsed["day"],
                "month":     parsed["month_num"],
                "year":      parsed["year"],
                "los_value": los_val[:3] if los_val.isdigit() else "1",
                "los_unit":  _LOS.get(los_unit_raw, "D"),
            })
    data["PREV_VISITS"] = cleaned_visits

    # Numaralı visit formatı
    for i in range(1, 6):
        d = raw.get(f"VISIT{i}_ARRIVAL_DATE", "")
        if not d:
            break
        data[f"VISIT{i}_ARRIVAL_DATE"] = d
        data[f"VISIT{i}_STAY_LENGTH"]  = str(raw.get(f"VISIT{i}_STAY_LENGTH", "1"))[:3]
        data[f"VISIT{i}_STAY_UNIT"]    = to_ascii_upper(raw.get(f"VISIT{i}_STAY_UNIT", "D"))

    # Driver license listesi
    dl_list = raw.get("US_DRIVER_LICENSE_LIST", [])
    cleaned_dl = []
    for lic in dl_list:
        number = re.sub(r"[^A-Z0-9]", "", to_ascii_upper(lic.get("number", "")))[:20]
        state  = to_ascii_upper(lic.get("state", ""))
        cleaned_dl.append({"number": number, "state": state})
    data["US_DRIVER_LICENSE_LIST"] = cleaned_dl

    # Tek lisans formatı
    if raw.get("US_DRIVER_LICENSE_NUMBER"):
        data["US_DRIVER_LICENSE_NUMBER"] = re.sub(
            r"[^A-Z0-9]", "", to_ascii_upper(raw["US_DRIVER_LICENSE_NUMBER"])
        )[:20]
    if raw.get("US_DRIVER_LICENSE_STATE"):
        data["US_DRIVER_LICENSE_STATE"] = to_ascii_upper(raw["US_DRIVER_LICENSE_STATE"])

    # ── ÖNCEKİ İŞ / EĞİTİM ───────────────────────────────
    data["PREV_EMPLOYED"]  = clean_yes_no(raw.get("PREV_EMPLOYED", "NO"))
    data["PREV_EDUCATION"] = clean_yes_no(raw.get("PREV_EDUCATION", "YES"))

    def _clean_empl_entry(e):
        return {
            "name":               re.sub(r"\s+"," ", re.sub(r"[,\.!?;:\"\'`@]"," ", to_ascii_upper(e.get("name","")))).strip()[:75],
            "addr1":              clean_address_line(e.get("addr1",""), 40),
            "addr2":              clean_address_line(e.get("addr2",""), 40),
            "city":               clean_city(e.get("city",""), 20),
            "state":              clean_state_province(e.get("state",""), 20),
            "postal":             clean_postal_code(e.get("postal","")),
            "country":            clean_country(e.get("country","")),
            "phone":              _clean_phone_15(e.get("phone","")),
            "job_title":          to_ascii_upper(e.get("job_title",""))[:75],
            "supervisor_surname": clean_name(e.get("supervisor_surname",""), 33),
            "supervisor_given":   clean_name(e.get("supervisor_given",""), 33),
            "date_from":          str(e.get("date_from","")).strip(),
            "date_to":            str(e.get("date_to","")).strip(),
            "duties":             to_ascii_upper(e.get("duties",""))[:4000],
        }

    def _clean_school_entry(e):
        return {
            "name":      re.sub(r"\s+"," ", re.sub(r"[,\.!?;:\"\'`@]"," ", to_ascii_upper(e.get("name","")))).strip()[:75],
            "addr1":     clean_address_line(e.get("addr1",""), 40),
            "addr2":     clean_address_line(e.get("addr2",""), 40),
            "city":      clean_city(e.get("city",""), 20),
            "state":     clean_state_province(e.get("state",""), 20),
            "postal":    clean_postal_code(e.get("postal","")),
            "country":   clean_country(e.get("country","")),
            "course":    to_ascii_upper(e.get("course",""))[:66],  # maxlength=66!
            "date_from": str(e.get("date_from","")).strip(),
            "date_to":   str(e.get("date_to","")).strip(),
        }

    data["PREV_EMPLOYERS"] = [_clean_empl_entry(e) for e in raw.get("PREV_EMPLOYERS", [])]
    data["PREV_SCHOOLS"]   = [_clean_school_entry(e) for e in raw.get("PREV_SCHOOLS", [])]

    # Tekil key formatı
    for key in ("PREV_EMPL_NAME","PREV_EMPL_ADDR1","PREV_EMPL_CITY","PREV_EMPL_COUNTRY",
                "PREV_EMPL_JOB_TITLE","PREV_EMPL_DATE_FROM","PREV_EMPL_DATE_TO","PREV_EMPL_DUTIES"):
        if raw.get(key):
            data[key] = to_ascii_upper(str(raw[key])).strip()[:4000]

    for key in ("PREV_SCH_NAME","PREV_SCH_ADDR1","PREV_SCH_CITY","PREV_SCH_COUNTRY",
                "PREV_SCH_COURSE","PREV_SCH_DATE_FROM","PREV_SCH_DATE_TO"):
        if raw.get(key):
            data[key] = to_ascii_upper(str(raw[key])).strip()[:4000]

    # ── ADDITIONAL WORK/EDUC ──────────────────────────────
    data["CLAN_TRIBE"] = clean_yes_no(raw.get("CLAN_TRIBE", "NO"))
    data["CLAN_NAME"]  = to_ascii_upper(raw.get("CLAN_NAME", ""))[:100]

    langs_raw = raw.get("LANGUAGES", ["TURKISH"])
    if isinstance(langs_raw, str):
        langs_raw = [l.strip() for l in langs_raw.split(",") if l.strip()]
    data["LANGUAGES"] = [to_ascii_upper(l)[:66] for l in langs_raw if l.strip()]
    if not data["LANGUAGES"]:
        data["LANGUAGES"] = ["TURKISH"]

    data["COUNTRIES_VISITED"] = clean_yes_no(raw.get("COUNTRIES_VISITED", "NO"))
    vis_raw = raw.get("VISITED_COUNTRIES", [])
    if isinstance(vis_raw, str):
        vis_raw = [c.strip() for c in vis_raw.split(",") if c.strip()]
    data["VISITED_COUNTRIES"] = [clean_country(c) for c in vis_raw if c.strip()]

    data["ORGANIZATION"] = clean_yes_no(raw.get("ORGANIZATION", "NO"))
    org_raw = raw.get("ORGANIZATION_LIST", [])
    if isinstance(org_raw, str):
        org_raw = [o.strip() for o in org_raw.split(",") if o.strip()]
    data["ORGANIZATION_LIST"] = [
        re.sub(r"\s+"," ", re.sub(r"[,\.!?;:\"\'`@]"," ", to_ascii_upper(o))).strip()[:66]
        for o in org_raw if o.strip()
    ]

    data["SPECIALIZED_SKILLS"]         = clean_yes_no(raw.get("SPECIALIZED_SKILLS", "NO"))
    data["SPECIALIZED_SKILLS_EXPLAIN"] = to_ascii_upper(raw.get("SPECIALIZED_SKILLS_EXPLAIN",""))[:4000]

    data["MILITARY_SERVICE"] = clean_yes_no(raw.get("MILITARY_SERVICE", "NO"))
    mil_raw = raw.get("MILITARY_LIST", [])
    def _clean_mil(m):
        return {
            "country":   clean_country(m.get("country","")),
            "branch":    to_ascii_upper(m.get("branch",""))[:40],
            "rank":      to_ascii_upper(m.get("rank",""))[:40],
            "specialty": to_ascii_upper(m.get("specialty",""))[:40],
            "date_from": str(m.get("date_from","")).strip(),
            "date_to":   str(m.get("date_to","")).strip(),
        }
    data["MILITARY_LIST"] = [_clean_mil(m) for m in mil_raw]

    data["INSURGENT_ORG"]         = clean_yes_no(raw.get("INSURGENT_ORG", "NO"))
    data["INSURGENT_ORG_EXPLAIN"] = to_ascii_upper(raw.get("INSURGENT_ORG_EXPLAIN",""))[:4000]

    # ── GERİ KALAN HAM VERİYİ AKTAR ──────────────────────
    # (temizlenmeyen alanlar olduğu gibi geçer)
    for k, v in raw.items():
        if k not in data:
            data[k] = v

    return data


# ══════════════════════════════════════════════
# KULLANIM ÖRNEĞİ
# ══════════════════════════════════════════════

if __name__ == "__main__":
    # Test
    raw_input = {
        "SURNAME":        "Parlak",
        "GIVEN_NAME":     "Şevket Metehan",
        "FULL_NAME_NATIVE": "Şevket Metehan Parlak",
        "GENDER":         "erkek",
        "MARITAL_STATUS": "evli",
        "BIRTH_DATE":     "20/02/1993",
        "BIRTH_CITY":     "Ankara",
        "BIRTH_COUNTRY":  "Türkiye",
        "NATIONALITY":    "Türkiye",
        "NATIONAL_ID":    "25 070 607 546",
        "PRIMARY_PHONE":  "+90 532 123 45 67",
        "MOBILE_PHONE":   "0532-123-45-67",
        "HOME_ADDRESS":   "Atatürk Mah., Cumhuriyet Cad. No:5/3",
        "HOME_CITY":      "İstanbul",
        "HOME_STATE":     "İstanbul",
        "HOME_POSTAL_CODE": "34000",
        "HOME_COUNTRY":   "Türkiye",
        "EMAIL":          "sevket@example.com",
        "PASSPORT_NUMBER": "U 123 456 78",
        "PASSPORT_ISSUE_DATE":  "15.03.2020",
        "PASSPORT_EXPIRY_DATE": "15/03/2030",
        "INTENDED_ARRIVAL_DATE": "20 Haziran 2025",
        "TRAVEL_LOS_VALUE": "30",
        "TRAVEL_LOS_UNIT":  "gün",
        "US_ADDRESS1":    "123 Main Street, Apt. 4B",
        "US_CITY":        "New York",
        "US_STATE":       "NY",
        "US_ZIP":         "10001",
        "PAYER_TYPE":     "self",
        "OTHER_NAME":     "hayır",
        "SPECIFIC_TRAVEL": "no",
    }

    cleaned = clean_all(raw_input)

    print("\n=== CLEANED DATA ===")
    for k, v in sorted(cleaned.items()):
        if v:
            print(f"  {k:35s}: {v}")