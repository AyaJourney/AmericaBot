from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from auto_fix import fix_country_select, fix_date, fix_text_value, fix_validation_errors, check_validation_errors
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException,
)

PAYER_MAP = {
    "SELF": "S",
    "OTHER": "O",
    "COMPANY": "C",
    "EMPLOYER": "P",
    "US_EMPLOYER": "U",
    "US_PETITIONER": "H",
}
US_POC_RELATION_MAP = {
    "RELATIVE": "R",
    "OTHER RELATIVE": "R",
    "FRIEND": "F",
    "SPOUSE": "S",
    "CHILD": "C",
    "PARENT": "P",
    "EMPLOYER": "E",
    "BUSINESS ASSOCIATE": "B",
    "OTHER": "O",

    # zaten harf gelirse
    "R": "R",
    "F": "F",
    "S": "S",
    "C": "C",
    "P": "P",
    "E": "E",
    "B": "B",
    "O": "O",
}
TRAVEL_COMPANION_REL_MAP = {
    "PARENT": "P",
    "SPOUSE": "S",
    "CHILD": "C",
    "RELATIVE": "R",
    "FRIEND": "F",
    "BUSINESS": "B",
    "OTHER": "O",
}
MONTH_TEXT = {
    "1": "JAN", "01": "JAN", "JAN": "JAN",
    "2": "FEB", "02": "FEB", "FEB": "FEB",
    "3": "MAR", "03": "MAR", "MAR": "MAR",
    "4": "APR", "04": "APR", "APR": "APR",
    "5": "MAY", "05": "MAY", "MAY": "MAY",
    "6": "JUN", "06": "JUN", "JUN": "JUN",
    "7": "JUL", "07": "JUL", "JUL": "JUL",
    "8": "AUG", "08": "AUG", "AUG": "AUG",
    "9": "SEP", "09": "SEP", "SEP": "SEP",
    "10": "OCT", "OCT": "OCT",
    "11": "NOV", "NOV": "NOV",
    "12": "DEC", "DEC": "DEC",
}
DS160_COUNTRY_MAP = {
 "AFGHANISTAN": "AFGH",
    "ALBANIA": "ALB",
    "ALGERIA": "ALGR",
    "AMERICAN SAMOA": "ASMO",
    "ANDORRA": "ANDO",
    "ANGOLA": "ANGL",
    "ANGUILLA": "ANGU",
    "ANTIGUA AND BARBUDA": "ANTI",
    "ARGENTINA": "ARG",
    "ARMENIA": "ARM",
    "ARUBA": "ARB",
    "AUSTRALIA": "ASTL",
    "AUSTRIA": "AUST",
    "AZERBAIJAN": "AZR",
    "BAHAMAS": "BAMA",
    "BAHRAIN": "BAHR",
    "BANGLADESH": "BANG",
    "BARBADOS": "BRDO",
    "BELARUS": "BYS",
    "BELGIUM": "BELG",
    "BELIZE": "BLZ",
    "BENIN": "BENN",
    "BERMUDA": "BERM",
    "BHUTAN": "BHU",
    "BOLIVIA": "BOL",
    "BONAIRE": "BON",
    "BOSNIA-HERZEGOVINA": "BIH",
    "BOSNIA AND HERZEGOVINA": "BIH",
    "BOTSWANA": "BOT",
    "BRAZIL": "BRZL",
    "BRITISH INDIAN OCEAN TERRITORY": "IOT",
    "BRUNEI": "BRNI",
    "BULGARIA": "BULG",
    "BURKINA FASO": "BURK",
    "BURMA": "BURM",
    "BURUNDI": "BRND",
    "CAMBODIA": "CBDA",
    "CAMEROON": "CMRN",
    "CANADA": "CAN",
    "CABO VERDE": "CAVI",
    "CAYMAN ISLANDS": "CAYI",
    "CENTRAL AFRICAN REPUBLIC": "CAFR",
    "CHAD": "CHAD",
    "CHILE": "CHIL",
    "CHINA": "CHIN",
    "CHRISTMAS ISLAND": "CHRI",
    "COCOS KEELING ISLANDS": "COCI",
    "COLOMBIA": "COL",
    "COMOROS": "COMO",
    "CONGO, DEMOCRATIC REPUBLIC OF THE": "COD",
    "CONGO, REPUBLIC OF THE": "CONB",
    "COOK ISLANDS": "CKIS",
    "COSTA RICA": "CSTR",
    "COTE D'IVOIRE": "IVCO",
    "CROATIA": "HRV",
    "CUBA": "CUBA",
    "CURACAO": "CUR",
    "CYPRUS": "CYPR",
    "CZECH REPUBLIC": "CZEC",
    "DENMARK": "DEN",
    "DJIBOUTI": "DJI",
    "DOMINICA": "DOMN",
    "DOMINICAN REPUBLIC": "DOMR",
    "ECUADOR": "ECUA",
    "EGYPT": "EGYP",
    "EL SALVADOR": "ELSL",
    "EQUATORIAL GUINEA": "EGN",
    "ERITREA": "ERI",
    "ESTONIA": "EST",
    "ESWATINI": "SZLD",
    "ETHIOPIA": "ETH",
    "FALKLAND ISLANDS": "FKLI",
    "FAROE ISLANDS": "FRO",
    "FIJI": "FIJI",
    "FINLAND": "FIN",
    "FRANCE": "FRAN",
    "FRENCH GUIANA": "FRGN",
    "FRENCH POLYNESIA": "FPOL",
    "FRENCH SOUTHERN AND ANTARCTIC TERRITORIES": "FSAT",
    "GABON": "GABN",
    "GAMBIA": "GAM",
    "GAZA STRIP": "XGZ",
    "GEORGIA": "GEO",
    "GERMANY": "GER",
    "GHANA": "GHAN",
    "GIBRALTAR": "GIB",
    "GREECE": "GRC",
    "GREENLAND": "GRLD",
    "GRENADA": "GREN",
    "GUADELOUPE": "GUAD",
    "GUAM": "GUAM",
    "GUATEMALA": "GUAT",
    "GUINEA": "GNEA",
    "GUINEA - BISSAU": "GUIB",
    "GUYANA": "GUY",
    "HAITI": "HAT",
    "HEARD AND MCDONALD ISLANDS": "HMD",
    "HOLY SEE": "VAT",
    "VATICAN CITY": "VAT",
    "HONDURAS": "HOND",
    "HONG KONG": "HNK",
    "HUNGARY": "HUNG",
    "ICELAND": "ICLD",
    "INDIA": "IND",
    "INDONESIA": "IDSA",
    "IRAN": "IRAN",
    "IRAQ": "IRAQ",
    "IRELAND": "IRE",
    "ISRAEL": "ISRL",
    "ITALY": "ITLY",
    "JAMAICA": "JAM",
    "JAPAN": "JPN",
    "JERUSALEM": "JRSM",
    "JORDAN": "JORD",
    "KAZAKHSTAN": "KAZ",
    "KENYA": "KENY",
    "KIRIBATI": "KIRI",
    "KOREA, DEMOCRATIC REPUBLIC OF (NORTH)": "PRK",
    "NORTH KOREA": "PRK",
    "KOREA, REPUBLIC OF (SOUTH)": "KOR",
    "SOUTH KOREA": "KOR",
    "KOSOVO": "KSV",
    "KUWAIT": "KUWT",
    "KYRGYZSTAN": "KGZ",
    "LAOS": "LAOS",
    "LATVIA": "LATV",
    "LEBANON": "LEBN",
    "LESOTHO": "LES",
    "LIBERIA": "LIBR",
    "LIBYA": "LBYA",
    "LIECHTENSTEIN": "LCHT",
    "LITHUANIA": "LITH",
    "LUXEMBOURG": "LXM",
    "MACAU": "MAC",
    "MACEDONIA, NORTH": "MKD",
    "MADAGASCAR": "MADG",
    "MALAWI": "MALW",
    "MALAYSIA": "MLAS",
    "MALDIVES": "MLDV",
    "MALI": "MALI",
    "MALTA": "MLTA",
    "MARSHALL ISLANDS": "RMI",
    "MARTINIQUE": "MART",
    "MAURITANIA": "MAUR",
    "MAURITIUS": "MRTS",
    "MAYOTTE": "MYT",
    "MEXICO": "MEX",
    "MICRONESIA": "FSM",
    "MOLDOVA": "MLD",
    "MONACO": "MON",
    "MONGOLIA": "MONG",
    "MONTENEGRO": "MTG",
    "MOROCCO": "MORO",
    "MOZAMBIQUE": "MOZ",
    "NAMIBIA": "NAMB",
    "NAURU": "NAU",
    "NEPAL": "NEP",
    "NETHERLANDS": "NETH",
    "NEW ZEALAND": "NZLD",
    "NICARAGUA": "NIC",
    "NIGER": "NIR",
    "NIGERIA": "NRA",
    "NORWAY": "NORW",
    "OMAN": "OMAN",
    "PAKISTAN": "PKST",
    "PANAMA": "PAN",
    "PERU": "PERU",
    "PHILIPPINES": "PHIL",
    "POLAND": "POL",
    "PORTUGAL": "PORT",
    "PUERTO RICO": "PR",
    "QATAR": "QTAR",
    "ROMANIA": "ROM",
    "RUSSIA": "RUS",
    "RWANDA": "RWND",
    "SAUDI ARABIA": "SARB",
    "SENEGAL": "SENG",
    "SERBIA": "SBA",
    "SINGAPORE": "SING",
    "SLOVAKIA": "SVK",
    "SLOVENIA": "SVN",
    "SOUTH AFRICA": "SAFR",
    "SPAIN": "SPN",
    "SRI LANKA": "SRL",
    "SUDAN": "SUDA",
    "SWEDEN": "SWDN",
    "SWITZERLAND": "SWTZ",
    "SYRIA": "SYR",
    "TAIWAN": "TWAN",
    "TAJIKISTAN": "TJK",
    "TANZANIA": "TAZN",
    "THAILAND": "THAI",
    "TUNISIA": "TNSA",
    "TURKEY": "TRKY",
    "TURKMENISTAN": "TKM",
    "UGANDA": "UGAN",
    "UKRAINE": "UKR",
    "UNITED ARAB EMIRATES": "UAE",
    "UNITED KINGDOM": "GRBR",
    "UNITED STATES": "USA",
    "UNITED STATES OF AMERICA": "USA",
    "URUGUAY": "URU",
    "UZBEKISTAN": "UZB",
    "VENEZUELA": "VENZ",
    "VIETNAM": "VTNM",
    "YEMEN": "YEM",
    "ZAMBIA": "ZAMB",
    "ZIMBABWE": "ZIMB",

}
def click_outside(driver):
    """
    Focus'u checkbox'tan alır.
    DS-160 postback sonrası reset sorununu çözer.
    """
    driver.execute_script("document.body.click();")
    time.sleep(0.1)

def wait_after_state_na(wait, driver):
    """
    State 'Does Not Apply' tıklandıktan sonra
    ASP.NET postback'in bitmesini bekler
    """

    country_select_id = "ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_POB_CNTRY"

    # Country dropdown tekrar clickable olana kadar bekle
    wait.until(
        EC.element_to_be_clickable((By.ID, country_select_id))
    )

    time.sleep(0.1)  # ekstra stabilite
    print("⏳ State NA postback tamamlandı")
def fill_ds160_date(wait, driver, day_id, month_id, year_id, day, month, year):
    # BOŞ TARİH → SKIP
    if not day or not month or not year:
        print(f"⚠️ Tarih atlandı (eksik): day={day}, month={month}, year={year}")
        return

    # YEAR
    year_box = wait.until(EC.element_to_be_clickable((By.ID, year_id)))
    year_box.clear()
    year_box.send_keys(str(year))
    time.sleep(0.3)

    # DAY (01 → 1 güvenli)
    try:
        day_value = str(int(day))
    except ValueError:
        raise Exception(f"❌ Geçersiz gün değeri: {day}")

    Select(wait.until(
        EC.element_to_be_clickable((By.ID, day_id))
    )).select_by_value(day_value)

    time.sleep(0.3)

    # MONTH (HER ZAMAN TEXT)
    month_key = str(month).strip().upper()
    month_text = MONTH_TEXT.get(month_key)

    if not month_text:
        raise Exception(f"❌ Geçersiz ay: {month}")

    Select(wait.until(
        EC.element_to_be_clickable((By.ID, month_id))
    )).select_by_visible_text(month_text)

    # POSTBACK
    driver.find_element(By.TAG_NAME, "body").click()
    time.sleep(1)

    print(f"✅ Tarih girildi: {day}-{month_text}-{year}")
def select_ds160_country(wait, select_id, country_name):
    country_name = country_name.strip().upper()

    if country_name not in DS160_COUNTRY_MAP:
        raise Exception(f"❌ DS-160 country map yok: {country_name}")

    country_value = DS160_COUNTRY_MAP[country_name]

    select = Select(wait.until(
        EC.element_to_be_clickable((By.ID, select_id))
    ))

    select.select_by_value(country_value)
def fill_basic_identity_form(wait, driver, surname, given_name, full_name_native):

    def js_fill(element_id, value):
        el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(value)

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SURNAME", surname)
    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_GIVEN_NAME", given_name)
    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_FULL_NAME_NATIVE", full_name_native)
def split_address(address: str, max_len: int = 40):
    """Adresi max_len karakterde kelime sınırından böler."""
    if not address:
        return "", ""
    address = address.strip()
    if len(address) <= max_len:
        return address, ""
    # max_len içinde son boşluğu bul
    cut = address.rfind(" ", 0, max_len)
    if cut == -1:
        cut = max_len  # boşluk yoksa zorla kes
    addr1 = address[:cut].strip()
    addr2 = address[cut:].strip()
    # addr2 de 40'ı geçiyorsa kırp
    if len(addr2) > max_len:
        addr2 = addr2[:max_len].strip()
    return addr1, addr2



import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def click_yes_and_wait(wait, driver, wait_seconds=3):
    """
    Other Names = YES
    Sadece YES'e tıklar ve bekler
    """

    yes_id = "ctl00_SiteContentPlaceHolder_FormView1_rblOtherNames_0"

    yes_radio = wait.until(
        EC.element_to_be_clickable((By.ID, yes_id))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        yes_radio
    )

    yes_radio.click()
    print("▶ YES tıklandı")

    time.sleep(wait_seconds)
    print(f"⏳ {wait_seconds} saniye beklendi")

def select_other_names(wait, driver, answer, wait_seconds=1):
    """
    Other Names (Have you used other names?)
    answer: YES / NO
    """

    if not answer:
        raise Exception("OTHER_NAME boş olamaz")

    answer = answer.strip().upper()

    if answer == "YES":
        radio_id = "ctl00_SiteContentPlaceHolder_FormView1_rblOtherNames_0"
    elif answer == "NO":
        radio_id = "ctl00_SiteContentPlaceHolder_FormView1_rblOtherNames_1"
    else:
        raise Exception("OTHER_NAME sadece YES veya NO olabilir")

    radio = wait.until(
        EC.element_to_be_clickable((By.ID, radio_id))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        radio
    )
    time.sleep(0.1)

    if not radio.is_selected():
        radio.click()
        print(f"✅ Other Names seçildi: {answer}")
    else:
        print(f"ℹ️ Other Names zaten seçili: {answer}")

    # 🔥 SADECE YES İSE BEKLE (postback + alan açılıyor)
    if answer == "YES":
        time.sleep(wait_seconds)
        print(f"⏳ {wait_seconds} saniye beklendi (Other Names alanları açıldı)")

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def fill_other_names(wait, driver, other_names):
    """
    other_names = [
        {"surname": "YILMAZ", "given": "AYSE"},
        {"surname": "DEMIR", "given": "FATMA"}
    ]
    """

    total = len(other_names)
    if total == 0:
        return

    def js_fill(element_id, value):
        el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(value)

    for i in range(total):
        surname_id = (
            "ctl00_SiteContentPlaceHolder_FormView1_"
            f"DListAlias_ctl{i:02d}_tbxSURNAME"
        )
        given_id = (
            "ctl00_SiteContentPlaceHolder_FormView1_"
            f"DListAlias_ctl{i:02d}_tbxGIVEN_NAME"
        )

        js_fill(surname_id, other_names[i]["surname"])
        js_fill(given_id, other_names[i]["given"])

        driver.execute_script("document.body.click();")
        time.sleep(0.1)

        print(f"✅ Other Name {i + 1} dolduruldu")

        if i < total - 1:
            postback_target = (
                "ctl00$SiteContentPlaceHolder$FormView1$DListAlias$"
                f"ctl{i:02d}$InsertButtonAlias"
            )
            driver.execute_script(f"__doPostBack('{postback_target}','')")
            print("▶ Add Another")

            next_surname_id = (
                "ctl00_SiteContentPlaceHolder_FormView1_"
                f"DListAlias_ctl{i + 1:02d}_tbxSURNAME"
            )
            wait.until(EC.presence_of_element_located((By.ID, next_surname_id)))
            time.sleep(0.1)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
import time

def select_gender(wait, driver, gender):
    """
    gender: 'M' veya 'F'
    """

    gender = gender.upper().strip()
    if gender not in ("M", "F"):
        raise ValueError("GENDER sadece 'M' veya 'F' olabilir")

    select_el = wait.until(
        EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_GENDER")
        )
    )

    select = Select(select_el)
    select.select_by_value(gender)

    # onchange="setDirty()" tetiklensin
    driver.execute_script("document.body.click();")
    time.sleep(0.1)

    print(f"✅ Gender seçildi: {gender}")
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
import time

def select_marital_status(wait, driver, marital_status_text):
    """
    marital_status_text:
    'SINGLE'
    'MARRIED'
    'DIVORCED'
    'WIDOWED'
    'LEGALLY SEPARATED'
    'COMMON LAW MARRIAGE'
    'CIVIL UNION/DOMESTIC PARTNERSHIP'
    'OTHER'
    """

    marital_status_text = marital_status_text.strip().upper()

    # Açık metin → CEAC value eşlemesi
    mapping = {
        "MARRIED": "M",
        "COMMON LAW MARRIAGE": "C",
        "CIVIL UNION/DOMESTIC PARTNERSHIP": "P",
        "SINGLE": "S",
        "WIDOWED": "W",
        "DIVORCED": "D",
        "LEGALLY SEPARATED": "L",
        "OTHER": "O",
    }

    if marital_status_text not in mapping:
        raise ValueError(
            f"Geçersiz MARITAL_STATUS: {marital_status_text}"
        )

    value = mapping[marital_status_text]

    select_el = wait.until(
        EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_MARITAL_STATUS")
        )
    )

    select = Select(select_el)
    select.select_by_value(value)

    print(f"✅ Marital Status seçildi: {marital_status_text}")

    # CEAC partial postback bekle
    time.sleep(0.1)

    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
import time



def fill_date_of_birth(wait, driver, day, month, year):
    # YEAR
    year_input = wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxDOBYear")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, year_input)
    year_input.send_keys(str(year))
    time.sleep(0.4)

    # DAY
    Select(wait.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlDOBDay")
        )
    )).select_by_value(str(day).zfill(2))
    time.sleep(0.4)

    # MONTH
    month_key = str(month).strip().upper()
    month_text = MONTH_TEXT.get(month_key)

    if not month_text:
        raise Exception(f"❌ Geçersiz ay: {month}")

    Select(wait.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlDOBMonth")
        )
    )).select_by_visible_text(month_text)

    driver.find_element(By.TAG_NAME, "body").click()
    time.sleep(1.2)

    print(f"✅ DOB girildi: {day}-{month_text}-{year}")
def fill_place_of_birth(wait, driver, city, state=None):
    # CITY
    city_input = wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_POB_CITY")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, city_input)
    city_input.send_keys(city)

    # STATE / PROVINCE
    state_input = wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_POB_ST_PROVINCE")
    ))

    if state:
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, state_input)
        state_input.send_keys(state)
    else:
        na_checkbox = driver.find_element(
            By.ID,
            "ctl00_SiteContentPlaceHolder_FormView1_cbexAPP_POB_ST_PROVINCE_NA"
        )
        if not na_checkbox.is_selected():
            na_checkbox.click()

    driver.find_element(By.TAG_NAME, "body").click()
    time.sleep(0.1)

    print("✅ Doğum yeri (şehir / eyalet) girildi")
def fill_birth_state(wait, driver, state):
    na_checkbox_id = "ctl00_SiteContentPlaceHolder_FormView1_cbexAPP_POB_ST_PROVINCE_NA"
    state_input_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_POB_ST_PROVINCE"

    if not state or state.strip().upper() in ["NA", "N/A", "NONE"]:
        na_checkbox = wait.until(EC.element_to_be_clickable((By.ID, na_checkbox_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", na_checkbox)
        time.sleep(0.1)

        if not na_checkbox.is_selected():
            na_checkbox.click()
            print("✅ Birth State: DOES NOT APPLY")

        click_outside(driver)

    else:
        state_input = wait.until(EC.presence_of_element_located((By.ID, state_input_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, state_input)
        state_input.send_keys(state)
        print(f"✅ Birth State girildi: {state}")


def select_birth_country(wait, driver, country_name):
    country_name = country_name.upper().strip()

    select_el = wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_POB_CNTRY")
    ))
    select = Select(select_el)

    found = False
    for option in select.options:
        if option.text.strip().upper() == country_name:
            select.select_by_visible_text(option.text)
            found = True
            break

    if not found:
        raise ValueError(f"Ülke bulunamadı: {country_name}")

    driver.find_element(By.TAG_NAME, "body").click()
    time.sleep(0.1)

    print(f"✅ Doğum ülkesi seçildi: {country_name}")

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def save_and_go_next(wait, driver):
    # ====================
    # SAVE
    # ====================
    save_btn = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_UpdateButton2")
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        save_btn
    )
    time.sleep(0.1)

    save_btn.click()
    print("💾 Save tıklandı")

    # 🔑 Save postback tamamlanana kadar bekle
   
    # 🔑 Yeni sayfa yüklenmesini bekle
    time.sleep(0.1)
    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def select_telecode_no(wait, driver):
    """
    Telecode sorusunu NO olarak işaretler
    """

    no_radio = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblTelecodeQuestion_1")
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        no_radio
    )
    time.sleep(0.1)

    no_radio.click()
    print("🚫 Telecode: NO seçildi")

    # 🔑 CEAC postback bekle
    time.sleep(0.1)
    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
import time

def force_continue_application(wait, driver):
    """
    Continue Application butonunu server-side postback ile tetikler
    """

    print("▶ Continue Application (FORCE)")

    driver.execute_script("""
        needToConfirm = false;
        __doPostBack('ctl00$btnContinueApp','');
    """)

    # CEAC postback bekle
    time.sleep(0.1)

    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    print("✅ Continue Application postback gönderildi")
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def wait_and_click_next_personal2(wait, driver):
    """
    Continue Application sonrası
    Next: Personal 2 butonunu bekler ve basar
    """

    print("⏳ Next: Personal 2 butonu bekleniyor...")

    next_btn = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_UpdateButton3")
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        next_btn
    )
    time.sleep(0.1)

    next_btn.click()
    print("➡ Next: Personal 2 tıklandı")

    # Yeni sayfa / postback bekle
    time.sleep(0.1)
    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

def select_nationality(wait, driver, nationality_text):
    nationality_text = nationality_text.strip().upper()

    select_el = wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlAPP_NATL")
    ))
    select = Select(select_el)

    found = False
    for option in select.options:
        if option.text.strip().upper() == nationality_text:
            select.select_by_visible_text(option.text)
            found = True
            break

    if not found:
        raise ValueError(f"Nationality bulunamadı: {nationality_text}")

    print(f"✅ Nationality seçildi: {nationality_text}")
    time.sleep(0.1)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")


def select_country_by_name(wait, select_id, country_text):
    from auto_fix import fix_country_select
    if not country_text:
        raise Exception("❌ Country boş olamaz")

    # Önce normal yolla dene
    try:
        country = country_text.strip().upper()
        select = Select(wait.until(EC.element_to_be_clickable((By.ID, select_id))))
        for option in select.options:
            if option.text.strip().upper() == country:
                select.select_by_visible_text(option.text)
                print(f"✅ Country seçildi: {option.text}")
                return
    except Exception:
        pass

    # Bulunamazsa auto_fix dene
    driver = wait._driver
    if fix_country_select(driver, select_id, country_text):
        return

    raise Exception(f"❌ Country bulunamadı: {country_text}")
def select_other_nationality(wait, driver, answer):
    answer = answer.strip().upper()

    if answer == "YES":
        radio_id = "ctl00_SiteContentPlaceHolder_FormView1_rblAPP_OTH_NATL_IND_0"
    elif answer == "NO":
        radio_id = "ctl00_SiteContentPlaceHolder_FormView1_rblAPP_OTH_NATL_IND_1"
    else:
        raise ValueError("OTHER_NATIONALITY değeri YES veya NO olmalı")

    radio = wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
    time.sleep(0.1)

    if not radio.is_selected():
        radio.click()
        print(f"✅ Other Nationality: {answer} seçildi")
    else:
        print(f"ℹ Other Nationality zaten {answer}")

    if answer == "YES":
        time.sleep(0.1)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")


def select_other_nationality_yes(wait, driver):
    yes_radio = wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblAPP_OTH_NATL_IND_0")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", yes_radio)
    time.sleep(0.1)

    if not yes_radio.is_selected():
        yes_radio.click()
        print("✅ Other Nationality: YES")
    else:
        print("ℹ Other Nationality zaten YES")

    time.sleep(0.1)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")


def fill_single_other_nationality(wait, driver, country_name, has_passport, passport_number=None):
    country_name = country_name.strip().upper()
    has_passport = has_passport.strip().upper()

    country_select = Select(wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_ddlOTHER_NATL")
    )))

    for opt in country_select.options:
        if opt.text.strip().upper() == country_name:
            country_select.select_by_visible_text(opt.text)
            break
    else:
        raise ValueError(f"Other nationality country bulunamadı: {country_name}")

    time.sleep(0.1)

    if has_passport == "YES":
        ppt_radio_id = "ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_rblOTHER_PPT_IND_0"
    elif has_passport == "NO":
        ppt_radio_id = "ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_rblOTHER_PPT_IND_1"
    else:
        raise ValueError("HAS_PASSPORT sadece YES veya NO olabilir")

    wait.until(EC.element_to_be_clickable((By.ID, ppt_radio_id))).click()
    time.sleep(0.1)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    if has_passport == "YES":
        if not passport_number:
            raise ValueError("HAS_PASSPORT=YES ise PASSPORT_NUMBER zorunlu")
        fill_other_nationality_passport_number(wait, driver, passport_number)

    time.sleep(0.1)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")


def click_add_another_other_nationality(wait, driver):
    wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_InsertButtonOTHER_NATL")
    )).click()
    print("➕ Add Another nationality")
    time.sleep(0.1)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")


def fill_other_nationality_passport_number(wait, driver, passport_number):
    passport_number = passport_number.strip()

    input_el = wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlOTHER_NATL_ctl00_tbxOTHER_PPT_NUM")
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_el)
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, input_el)
    input_el.send_keys(passport_number)

    driver.find_element(By.TAG_NAME, "body").click()
    time.sleep(0.1)
    print("✅ Other nationality passport number girildi")


def select_permanent_resident_other_country(wait, driver, answer):
    answer = answer.strip().upper()

    if answer == "YES":
        radio_id = "ctl00_SiteContentPlaceHolder_FormView1_rblPermResOtherCntryInd_0"
    elif answer == "NO":
        radio_id = "ctl00_SiteContentPlaceHolder_FormView1_rblPermResOtherCntryInd_1"
    else:
        raise ValueError("PERMANENT_RESIDENT_OTHER_COUNTRY YES veya NO olmalı")

    wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()
    time.sleep(0.1)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    print(f"✅ Permanent Resident Other Country = {answer}")


def fill_permanent_resident_country_by_index(wait, driver, country_name, index):
    country_name = country_name.strip().upper()

    select_id = (
        f"ctl00_SiteContentPlaceHolder_FormView1_"
        f"dtlOthPermResCntry_ctl{index:02d}_ddlOthPermResCntry"
    )

    select_el = Select(wait.until(EC.presence_of_element_located((By.ID, select_id))))

    for opt in select_el.options:
        if opt.text.strip().upper() == country_name:
            select_el.select_by_visible_text(opt.text)
            break
    else:
        raise ValueError(f"Permanent resident country bulunamadı: {country_name}")

    time.sleep(0.1)
    driver.find_element(By.TAG_NAME, "body").click()
    print(f"✅ Permanent resident country ({index}) girildi: {country_name}")


def click_add_another_permanent_resident(wait, driver):
    wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlOthPermResCntry_ctl00_InsertButtonOTHER_PERM_RES")
    )).click()
    time.sleep(0.1)
    print("➕ Add Another Permanent Resident tıklandı")


def fill_permanent_resident_section(wait, driver, data):
    answer = data.get("PERMANENT_RESIDENT_OTHER_COUNTRY", "NO").strip().upper()
    select_permanent_resident_other_country(wait, driver, answer)

    if answer == "NO":
        return

    index = 0
    i = 1

    while True:
        key = f"PERMANENT_RESIDENT_{i}_COUNTRY"
        if key not in data:
            break

        fill_permanent_resident_country_by_index(wait, driver, data[key], index)

        next_key = f"PERMANENT_RESIDENT_{i+1}_COUNTRY"
        if next_key in data:
            click_add_another_permanent_resident(wait, driver)
            index += 1

        i += 1


def fill_national_id(wait, driver, data):
    raw = (data.get("NATIONAL_ID") or "").strip().upper()

    input_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_NATIONAL_ID"
    na_checkbox_id = "ctl00_SiteContentPlaceHolder_FormView1_cbexAPP_NATIONAL_ID_NA"

    na_cb = wait.until(EC.presence_of_element_located((By.ID, na_checkbox_id)))
    input_el = wait.until(EC.presence_of_element_located((By.ID, input_id)))

    if raw in ("", "NA", "N/A", "NONE"):
        if not na_cb.is_selected():
            na_cb.click()
            time.sleep(0.2)
        print("✅ National ID: Does Not Apply")
        return

    if na_cb.is_selected():
        na_cb.click()
        time.sleep(0.2)

    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, input_el)
    input_el.send_keys(raw)
    print("✅ National ID girildi:", raw)


def normalize_ssn(raw):
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) != 9:
        raise ValueError("❌ SSN 9 haneli olmalı")
    return digits[:3], digits[3:5], digits[5:]


def fill_ssn(wait, driver, data):
    raw = (data.get("SSN") or "").strip()

    na_checkbox_id = "ctl00_SiteContentPlaceHolder_FormView1_cbexAPP_SSN_NA"
    ssn1_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SSN1"
    ssn2_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SSN2"
    ssn3_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SSN3"

    na_cb = wait.until(EC.presence_of_element_located((By.ID, na_checkbox_id)))

    if raw.upper() in ("", "NA", "N/A", "NONE"):
        if not na_cb.is_selected():
            na_cb.click()
            time.sleep(0.2)
        print("✅ SSN: Does Not Apply")
        return

    if na_cb.is_selected():
        na_cb.click()
        time.sleep(0.2)

    p1, p2, p3 = normalize_ssn(raw)

    for fid, val in [(ssn1_id, p1), (ssn2_id, p2), (ssn3_id, p3)]:
        el = wait.until(EC.presence_of_element_located((By.ID, fid)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(val)

    print("✅ SSN girildi:", f"{p1}-{p2}-{p3}")


def fill_tax_id(wait, driver, data):
    raw = (data.get("TAX_ID") or "").strip()

    input_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_TAX_ID"
    na_checkbox_id = "ctl00_SiteContentPlaceHolder_FormView1_cbexAPP_TAX_ID_NA"

    na_cb = wait.until(EC.presence_of_element_located((By.ID, na_checkbox_id)))
    input_el = wait.until(EC.presence_of_element_located((By.ID, input_id)))

    if raw.upper() in ("", "NA", "N/A", "NONE"):
        if not na_cb.is_selected():
            na_cb.click()
            time.sleep(0.2)
        print("✅ Tax ID: Does Not Apply")
        return

    if na_cb.is_selected():
        na_cb.click()
        time.sleep(0.2)

    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, input_el)
    input_el.send_keys(raw)
    print("✅ Tax ID girildi:", raw)


def fill_personal2_ids(wait, driver, data):
    fill_national_id(wait, driver, data)
    time.sleep(0.1)
    fill_ssn(wait, driver, data)
    time.sleep(0.1)
    fill_tax_id(wait, driver, data)
    time.sleep(0.1)
def click_save_personal2(wait, driver):
    save_btn_id = "ctl00_SiteContentPlaceHolder_UpdateButton2"

    # 1️⃣ Save butonu clickable olsun
    save_btn = wait.until(
        EC.element_to_be_clickable((By.ID, save_btn_id))
    )

    # 2️⃣ Scroll + click (CEAC bazen scroll ister)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_btn)
    time.sleep(0.1)
    save_btn.click()
    print("💾 Save butonuna basıldı")

    # 3️⃣ Postback başladı mı? (needToConfirm false oluyor)
    time.sleep(0.1)

    # 4️⃣ Sayfa stabilize olana kadar bekle
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    time.sleep(0.1)

    print("✅ Sayfa kaydedildi (Save tamam)")
def click_continue_application(wait, driver):
    continue_id = "ctl00_btnContinueApp"

    # 1️⃣ Buton görünür + tıklanabilir olsun
    continue_btn = wait.until(
        EC.element_to_be_clickable((By.ID, continue_id))
    )

    # 2️⃣ Scroll (CEAC şart)
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        continue_btn
    )
    time.sleep(0.1)

    # 3️⃣ Tıkla
    continue_btn.click()
    print("▶️ Continue Application butonuna basıldı")

    # 4️⃣ Postback + sayfa yüklenmesi
    time.sleep(0.1)
    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(0.1)

    print("✅ Continue Application tamamlandı")
def click_next_travel(wait, driver):
    next_id = "ctl00_SiteContentPlaceHolder_UpdateButton3"

    # 1️⃣ Buton gerçekten DOM'da + clickable olsun
    next_btn = wait.until(
        EC.element_to_be_clickable((By.ID, next_id))
    )

    # 2️⃣ Scroll (çok önemli)
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        next_btn
    )
    time.sleep(0.1)

    # 3️⃣ Tıkla
    next_btn.click()
    print("➡️ Next: Travel butonuna basıldı")

    # 4️⃣ Postback + yeni sayfa yüklenmesi
    time.sleep(0.1)
    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(0.1)

    print("✅ Travel sayfasına geçildi")



def select_purpose_of_trip(wait, driver, purpose_text):
    select_id = "ctl00_SiteContentPlaceHolder_FormView1_dlPrincipalAppTravel_ctl00_ddlPurposeOfTrip"
    dropdown = wait.until(EC.element_to_be_clickable((By.ID, select_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
    time.sleep(0.1)

    select = Select(dropdown)
    for option in select.options:
        if purpose_text.upper() in option.text.upper():
            select.select_by_visible_text(option.text)
            print(f"✅ Purpose seçildi: {option.text}")
            break

    time.sleep(2)


def select_purpose_subcategory_if_exists(wait, driver, sub_text):
    sub_select_id = "ctl00_SiteContentPlaceHolder_FormView1_dlPrincipalAppTravel_ctl00_ddlOtherPurpose"

    try:
        sub_dropdown = wait.until(EC.visibility_of_element_located((By.ID, sub_select_id)))
    except:
        print("ℹ️ Alt purpose yok, devam ediliyor")
        return

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sub_dropdown)
    time.sleep(0.1)

    select = Select(sub_dropdown)
    found = False
    for option in select.options:
        if sub_text.upper() in option.text.upper():
            select.select_by_visible_text(option.text)
            found = True
            print(f"✅ Alt Purpose seçildi: {option.text}")
            break

    if not found:
        raise Exception(f"❌ Alt Purpose bulunamadı: {sub_text}")

    time.sleep(2)


def select_specific_travel(wait, driver, answer):
    answer = answer.strip().upper()
    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblSpecificTravel_0"
        if answer == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblSpecificTravel_1"
    )

    try:
        radio = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, radio_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
        if not radio.is_selected():
            radio.click()
            print(f"✅ Specific travel seçildi: {answer}")
        return True
    except:
        print("ℹ️ 'Specific travel plans' sorusu bulunamadı, alt adımlar atlanıyor.")
        return False


def fill_travel_details(wait, driver, data):
    print("🧭 Travel details dolduruluyor...")

    def js_fill(element_id, value):
        el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(value)

    # ARRIVAL DATE
    fill_ds160_date(
        wait, driver,
        "ctl00_SiteContentPlaceHolder_FormView1_ddlARRIVAL_US_DTEDay",
        "ctl00_SiteContentPlaceHolder_FormView1_ddlARRIVAL_US_DTEMonth",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxARRIVAL_US_DTEYear",
        data["ARRIVAL_DAY"],
        data["ARRIVAL_MONTH"],
        data["ARRIVAL_YEAR"]
    )

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxArriveCity", data["ARRIVAL_CITY"])
    time.sleep(0.5)

    # DEPARTURE DATE
    fill_ds160_date(
        wait, driver,
        "ctl00_SiteContentPlaceHolder_FormView1_ddlDEPARTURE_US_DTEDay",
        "ctl00_SiteContentPlaceHolder_FormView1_ddlDEPARTURE_US_DTEMonth",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxDEPARTURE_US_DTEYear",
        data["DEPARTURE_DAY"],
        data["DEPARTURE_MONTH"],
        data["DEPARTURE_YEAR"]
    )

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxDepartCity", data["DEPARTURE_CITY"])
    time.sleep(1)

    # TRAVEL LOCATION
    js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_dtlTravelLoc_ctl00_tbxSPECTRAVEL_LOCATION",
        data["TRAVEL_LOCATION_1"]
    )

    print("✅ Travel details başarıyla dolduruldu")

MONTH_MAP = {
    "JAN": "1", "FEB": "2", "MAR": "3", "APR": "4",
    "MAY": "5", "JUN": "6", "JUL": "7", "AUG": "8",
    "SEP": "9", "OCT": "10", "NOV": "11", "DEC": "12",
}
STATE_MAP = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "AMERICAN SAMOA": "AS",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "DISTRICT OF COLUMBIA": "DC",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "GUAM": "GU",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "NORTHERN MARIANA ISLANDS": "MP",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "PUERTO RICO": "PR",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGIN ISLANDS": "VI",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
}
RELATIONSHIP_MAP = {
    "PARENT": "P",
    "SPOUSE": "S",
    "CHILD": "C",
    "RELATIVE": "R",
    "FRIEND": "F",
    "OTHER RELATIVE": "O",
    "OTHER PERSON": "O",
}
US_STATE_MAP = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "AMERICAN SAMOA": "AS",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "DISTRICT OF COLUMBIA": "DC",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "GUAM": "GU",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "NORTHERN MARIANA ISLANDS": "MP",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "PUERTO RICO": "PR",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY"
}
SOCIAL_MEDIA_MAP = {
    "ASK.FM": "ASKF",
    "ASKFM": "ASKF",

    "DOUBAN": "DUBN",

    "FACEBOOK": "FCBK",

    "FLICKR": "FLKR",

    "GOOGLE+": "GOGL",
    "GOOGLE PLUS": "GOGL",

    "INSTAGRAM": "INST",

    "LINKEDIN": "LINK",

    "MYSPACE": "MYSP",

    "PINTEREST": "PTST",

    "QZONE": "QZNE",
    "QZONE (QQ)": "QZNE",

    "REDDIT": "RDDT",

    "SINA WEIBO": "SWBO",
    "WEIBO": "SWBO",

    "TENCENT WEIBO": "TWBO",

    "TUMBLR": "TUMB",

    "X(TWITTER)": "TWIT",
    "X": "TWIT",

    "TWOO": "TWOO",

    "VINE": "VINE",

    "VK": "VKON",
    "VKONTAKTE": "VKON",
    "VKONTAKTE (VK)": "VKON",

    "YOUKU": "YUKU",

    "YOUTUBE": "YTUB",

    "NONE": "NONE",
    "NO": "NONE",
    "YOK": "NONE"
}

PASSPORT_TYPE_MAP = {
    "REGULAR": "R",  "R": "R",
    "OFFICIAL": "O", "O": "O",
    "DIPLOMATIC": "D", "D": "D",
    "LAISSEZ": "L",  "L": "L", "LAISSEZ-PASSER": "L",
    "OTHER": "T",    "T": "T",
}
def fill_intended_arrival_date(wait, driver, data):
    print("🛬 Intended arrival date dolduruluyor...")
    from datetime import datetime, timedelta

    day_raw  = (data.get("INTENDED_ARRIVAL_DAY") or "").strip()
    mon_raw  = str(data.get("INTENDED_ARRIVAL_MONTH") or "").strip().upper()
    year_raw = (data.get("INTENDED_ARRIVAL_YEAR") or "").strip()

    if not day_raw or not mon_raw or not year_raw:
        raise Exception("❌ INTENDED_ARRIVAL_DAY / MONTH / YEAR boş olamaz")

    MON_STR = ["JAN","FEB","MAR","APR","MAY","JUN",
               "JUL","AUG","SEP","OCT","NOV","DEC"]

    # Tarih geçmişte mi kontrol et
    try:
        if mon_raw.isdigit():
            mon_num = int(mon_raw)
        else:
            mon_num = int(MONTH_MAP.get(mon_raw, "1"))
        arrival = datetime(int(year_raw), mon_num, int(day_raw))
        today   = datetime.now()

        if arrival <= today:
            print(f"⚠️ Varış tarihi geçmişte ({day_raw}-{mon_raw}-{year_raw}), 90 gün sonrasına ayarlanıyor...")
            future   = today + timedelta(days=90)
            day_raw  = str(future.day)
            mon_raw  = MON_STR[future.month - 1]
            year_raw = str(future.year)
            print(f"✅ Yeni varış tarihi: {day_raw}-{mon_raw}-{year_raw}")
    except Exception as e:
        print(f"⚠️ Tarih kontrol hatası: {e}")

    try:
        day_val = str(int(day_raw))
    except Exception:
        day_val = day_raw

    if mon_raw.isdigit():
        mon_val  = str(int(mon_raw))
        mon_text = None
    else:
        mon_val  = MONTH_MAP.get(mon_raw)
        mon_text = mon_raw

    if not mon_val:
        raise Exception(f"❌ Geçersiz ay: {mon_raw}")

    day_dd = Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlTRAVEL_DTEDay")
    )))
    try:
        day_dd.select_by_value(day_val)
    except Exception:
        day_dd.select_by_value(day_val.zfill(2))
    time.sleep(0.2)

    month_dd = Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlTRAVEL_DTEMonth")
    )))
    try:
        month_dd.select_by_value(mon_val)
    except Exception:
        if mon_text:
            month_dd.select_by_visible_text(mon_text)
        else:
            inv = {v: k for k, v in MONTH_MAP.items()}
            month_dd.select_by_visible_text(inv.get(mon_val, mon_val))
    time.sleep(0.2)

    year_box = wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxTRAVEL_DTEYear")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, year_box)
    year_box.send_keys(str(year_raw))
    year_box.send_keys(Keys.TAB)

    driver.find_element(By.TAG_NAME, "body").click()
    time.sleep(0.6)
    print(f"✅ Intended Arrival Date: {day_val}-{mon_raw}-{year_raw}")
def fill_intended_length_of_stay(wait, driver, data):
    raw_value = str(data.get("TRAVEL_LOS_VALUE", "")).strip()
    raw_unit = str(data.get("TRAVEL_LOS_UNIT", "")).strip().upper()

    if not raw_value.isdigit():
        raw_value = "1"

    unit_map = {
        "YEAR": "Y", "YEARS": "Y", "YEAR(S)": "Y",
        "MONTH": "M", "MONTHS": "M", "MONTH(S)": "M",
        "WEEK": "W", "WEEKS": "W", "WEEK(S)": "W",
        "DAY": "D", "DAYS": "D", "DAY(S)": "D",
        "Y": "Y", "M": "M", "W": "W", "D": "D",
    }
    unit_value = unit_map.get(raw_unit, "D")
    display_unit = raw_unit if raw_unit in unit_map else "DAY (Default)"

    los_input = wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxTRAVEL_LOS")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, los_input)
    los_input.send_keys(raw_value)
    time.sleep(0.5)

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlTRAVEL_LOS_CD")
    ))).select_by_value(unit_value)

    time.sleep(1.0)
    driver.execute_script("document.body.click();")
    print(f"🎯 Intended Length of Stay TAMAM: {raw_value} {display_unit}")


def fill_us_address(wait, driver, data):

    def js_fill(element_id, value):
        if not value:
            return
        el = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(value)

    # Address — 40 karakteri geçince 2. satıra taşı
    raw_addr = clean_address(data.get("US_ADDRESS1", "").strip())
    if not raw_addr:
        raise Exception("❌ US_ADDRESS1 boş olamaz")

    addr1, addr2_overflow = split_address(raw_addr, max_len=40)
    print(f"📍 US addr1: '{addr1}' ({len(addr1)} kar)")

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxStreetAddress1", addr1)

    # Address 2 — önce overflow, yoksa data'dan al
    addr2_data = clean_address(data.get("US_ADDRESS2", "").strip())
    if addr2_data and addr2_data.upper() in ("NA", "N/A"):
        addr2_data = ""

    addr2_final = addr2_overflow or addr2_data
    if addr2_final:
        print(f"📍 US addr2: '{addr2_final}' ({len(addr2_final)} kar)")
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxStreetAddress2", addr2_final)

    # City
    us_city = data.get("US_CITY", "").strip().upper()
    if not us_city:
        raise Exception("❌ US_CITY boş olamaz")
    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxCity", us_city)

    # State
    raw_state = data.get("US_STATE", "").strip().upper()
    if not raw_state:
        raise Exception("❌ US_STATE boş olamaz")
    state_value = raw_state if len(raw_state) == 2 else STATE_MAP.get(raw_state, raw_state)
    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlTravelState")
    ))).select_by_value(state_value)

    # ZIP
    zip_value = data.get("US_ZIP", "").strip()
    if zip_value and zip_value not in ("NA", "N/A"):
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbZIPCode", zip_value)

    print("✅ U.S. Address girildi")

    wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlWhoIsPaying")
    ))
    print("🟢 Payer dropdown hazır")

def select_payer_relationship(wait, raw_value):
    if not raw_value:
        return

    raw = raw_value.strip().upper()
    value = raw if len(raw) == 1 else RELATIONSHIP_MAP.get(raw)

    if not value:
        raise Exception(f"❌ Geçersiz PAYER_RELATIONSHIP: {raw_value}")

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlPayerRelationship")
    ))).select_by_value(value)
    print(f"✅ Payer relationship seçildi: {raw} → {value}")


def fill_payer_address(wait, driver, data):

    def js_fill(element_id, value):
        if not value:
            return
        try:
            el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
            """, el)
            el.send_keys(value)
        except Exception as e:
            print(f"⚠️ {element_id} doldurulamadı, atlanıyor: {e}")

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStreetAddress1", data.get("PAYER_ADDRESS1", ""))
    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStreetAddress2", data.get("PAYER_ADDRESS2", ""))
    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerCity", data.get("PAYER_CITY", ""))

    state = data.get("PAYER_STATE", "").strip()
    if state:
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStateProvince", state)
    else:
        try:
            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxDNAPayerStateProvince")
            )).click()
        except Exception:
            pass

    zip_code = data.get("PAYER_ZIP", "").strip()
    if zip_code:
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerPostalZIPCode", zip_code)
    else:
        try:
            wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxDNAPayerPostalZIPCode")
            )).click()
        except Exception:
            pass

    payer_country = data.get("PAYER_COUNTRY", "").strip()
    if payer_country:
        try:
            select_ds160_country(
                wait,
                "ctl00_SiteContentPlaceHolder_FormView1_ddlPayerCountry",
                payer_country
            )
        except Exception as e:
            print(f"⚠️ Payer country seçilemedi: {e}")

    driver.find_element(By.TAG_NAME, "body").click()
    time.sleep(0.5)

def fill_payer_info(wait, driver, data):
    print("🟢 Payer info başladı")

    def js_fill(element_id, value):
        if not value:
            return
        try:
            el = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
            """, el)
            el.send_keys(value)
        except Exception as e:
            print(f"⚠️ {element_id} doldurulamadı, atlanıyor: {e}")

    payer_type = (data.get("PAYER_TYPE") or "SELF").strip().upper()

    if payer_type not in PAYER_MAP:
        print(f"⚠️ Geçersiz PAYER_TYPE: {payer_type}, SELF olarak ayarlanıyor")
        payer_type = "SELF"

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlWhoIsPaying")
    ))).select_by_value(PAYER_MAP[payer_type])
    print(f"✅ Paying entity seçildi: {payer_type}")

    time.sleep(1.5)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    if payer_type == "SELF":
        print("ℹ️ SELF → işlem yok")
        return

    if payer_type == "OTHER":
        print("👤 OTHER PERSON")

        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerSurname",   data.get("PAYER_SURNAME", "XXXXXXXXXX"))
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerGivenName", data.get("PAYER_GIVEN_NAME", "XXXXXXXXXX"))
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerPhone",     data.get("PAYER_PHONE", "5555555555"))

        payer_email = data.get("PAYER_EMAIL", "").strip()
        if payer_email:
            try:
                js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPAYER_EMAIL_ADDR", payer_email)
            except Exception:
                print("ℹ️ Payer Email alanı bulunamadı, geçiliyor.")

        select_payer_relationship(wait, data.get("PAYER_RELATIONSHIP", "O"))

        same = (data.get("PAYER_ADDRESS_SAME") or "YES").upper()
        radio_id = (
            "ctl00_SiteContentPlaceHolder_FormView1_rblPayerAddrSameAsInd_0"
            if same == "YES"
            else "ctl00_SiteContentPlaceHolder_FormView1_rblPayerAddrSameAsInd_1"
        )
        wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()
        time.sleep(0.4)

        if same == "NO":
            raw_addr = clean_address(
                data.get("PAYER_COMPANY_ADDRESS1") or
                data.get("PAYER_ADDRESS1") or "XXXXXXXXXX"
            )
            addr1, addr2_overflow = split_address(raw_addr, max_len=40)
            addr2_data  = clean_address(data.get("PAYER_ADDRESS2", ""))
            addr2_final = addr2_overflow or addr2_data

            city    = clean_address(data.get("PAYER_COMPANY_CITY") or data.get("PAYER_CITY") or "XXXXXXXXXX")
            country = data.get("PAYER_COUNTRY", "TURKEY") or "TURKEY"

            print(f"📍 PAYER addr1: '{addr1}' ({len(addr1)} kar)")
            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStreetAddress1", addr1)

            if addr2_final:
                print(f"📍 PAYER addr2: '{addr2_final}' ({len(addr2_final)} kar)")
                js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStreetAddress2", addr2_final)

            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerCity", city)

            state = data.get("PAYER_STATE", "").strip()
            if state:
                js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStateProvince", state)
            else:
                try:
                    state_cb = driver.find_element(
                        By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxDNAPayerStateProvince"
                    )
                    if not state_cb.is_selected():
                        driver.execute_script("arguments[0].click();", state_cb)
                        time.sleep(1)
                except Exception:
                    pass

            zip_code = data.get("PAYER_ZIP", "").strip()
            if zip_code:
                js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerPostalZIPCode", zip_code)
            else:
                try:
                    zip_cb = driver.find_element(
                        By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxDNAPayerPostalZIPCode"
                    )
                    if not zip_cb.is_selected():
                        driver.execute_script("arguments[0].click();", zip_cb)
                        time.sleep(1)
                except Exception:
                    pass

            try:
                select_ds160_country(
                    wait,
                    "ctl00_SiteContentPlaceHolder_FormView1_ddlPayerCountry",
                    country
                )
            except Exception as e:
                print(f"⚠️ Payer country seçilemedi: {e}")

            driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(0.5)

        print("✅ OTHER PERSON tamamlandı")
        return

    if payer_type in ("COMPANY", "EMPLOYER", "US_EMPLOYER"):
        print("🏢 COMPANY / EMPLOYER alanları dolduruluyor...")
        time.sleep(2)

        try:
            wait.until(EC.visibility_of_element_located(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxPayingCompany")
            ))
        except TimeoutException:
            print("⚠️ Şirket alanları açılmadı, JS postback deneniyor...")
            driver.execute_script(
                "__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$ddlWhoIsPaying', '');"
            )
            time.sleep(2)

        try:
            company_name = data.get("PAYER_COMPANY_NAME", "").strip() or "XXXXXXXXXX"
            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayingCompany", company_name)
            print("✅ Şirket adı yazıldı.")

            company_phone = data.get("PAYER_COMPANY_PHONE", "").strip() or "5555555555"
            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerPhone", company_phone)

            company_rel = data.get("PAYER_COMPANY_RELATIONSHIP", "").strip() or "EMPLOYER"
            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxCompanyRelation", company_rel)

            payer_email = data.get("PAYER_EMAIL", "").strip()
            if payer_email:
                try:
                    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPAYER_EMAIL_ADDR", payer_email)
                except Exception:
                    print("ℹ️ Company Payer Email alanı bulunamadı, geçiliyor.")

            # COMPANY ADDRESS — split_address
            raw_company_addr = clean_address(
                data.get("PAYER_COMPANY_ADDRESS1") or
                data.get("PAYER_ADDRESS1") or "XXXXXXXXXX"
            )
            company_addr1, company_addr2_overflow = split_address(raw_company_addr, max_len=40)
            company_addr2_data  = clean_address(data.get("PAYER_COMPANY_ADDRESS2", ""))
            company_addr2_final = company_addr2_overflow or company_addr2_data

            city    = clean_address(data.get("PAYER_COMPANY_CITY") or data.get("PAYER_CITY") or "XXXXXXXXXX")
            country = data.get("PAYER_COMPANY_COUNTRY") or data.get("PAYER_COUNTRY") or "TURKEY"

            print(f"📍 COMPANY addr1: '{company_addr1}' ({len(company_addr1)} kar)")
            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStreetAddress1", company_addr1)

            if company_addr2_final:
                print(f"📍 COMPANY addr2: '{company_addr2_final}' ({len(company_addr2_final)} kar)")
                js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStreetAddress2", company_addr2_final)

            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPayerCity", city)

            # State — Does Not Apply
            try:
                state_cb = driver.find_element(
                    By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxDNAPayerStateProvince"
                )
                if not state_cb.is_selected():
                    driver.execute_script("arguments[0].click();", state_cb)
                    time.sleep(1)
                print("✅ Payer State: Does Not Apply")
            except Exception:
                pass

            # ZIP — Does Not Apply
            try:
                zip_cb = driver.find_element(
                    By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxDNAPayerPostalZIPCode"
                )
                if not zip_cb.is_selected():
                    driver.execute_script("arguments[0].click();", zip_cb)
                    time.sleep(1)
                print("✅ Payer ZIP: Does Not Apply")
            except Exception:
                pass

            try:
                select_ds160_country(
                    wait,
                    "ctl00_SiteContentPlaceHolder_FormView1_ddlPayerCountry",
                    country
                )
                print(f"✅ Payer Country: {country}")
            except Exception as e:
                print(f"⚠️ Payer country seçilemedi: {e}")

            driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(0.5)
            print("✅ COMPANY bilgileri tamamlandı")

        except Exception as e:
            print(f"❌ COMPANY bilgileri doldurulamadı: {e}")
            raise

def click_save(wait, driver):
    save_btn_id = "ctl00_SiteContentPlaceHolder_UpdateButton2"

    save_btn = wait.until(
        EC.element_to_be_clickable((By.ID, save_btn_id))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        save_btn
    )
    time.sleep(0.1)

    try:
        save_btn.click()
    except:
        # bazen normal click tutmuyor
        driver.execute_script("arguments[0].click();", save_btn)

    print("💾 Save butonuna basıldı")

    # postback + validation için kısa bekleme
    time.sleep(0.1)
def click_continue_applications(wait, driver):
    btn_id = "ctl00_btnContinueApp"

    btn = wait.until(
        EC.element_to_be_clickable((By.ID, btn_id))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        btn
    )
    time.sleep(0.1)

    try:
        btn.click()
    except:
        driver.execute_script("arguments[0].click();", btn)

    print("➡️ Continue Application tıklandı")

    # postback + yeni sayfa yüklenmesi
    time.sleep(0.1)
def click_nexts(wait, driver, label=None, wait_seconds=0.1):
    btn_id = "ctl00_SiteContentPlaceHolder_UpdateButton3"

    btn = wait.until(
        EC.element_to_be_clickable((By.ID, btn_id))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        btn
    )
    time.sleep(0.1)

    try:
        btn.click()
    except:
        driver.execute_script("arguments[0].click();", btn)

    if label:
        print(f"➡️ Next tıklandı → {label}")
    else:
        print("➡️ Next tıklandı")

    # postback + yeni sayfa
    time.sleep(wait_seconds)

def parse_travel_companions(data):
    companions = []
    i = 0

    while True:
        prefix = f"TRAV_COMP_{i:02d}_"
        surname = data.get(prefix + "SURNAME", "").strip()
        given = data.get(prefix + "GIVEN", "").strip()
        relationship = data.get(prefix + "RELATIONSHIP", "").strip().upper()

        if not surname and not given:
            break

        if surname and given and relationship:
            companions.append({
                "surname": surname,
                "given": given,
                "relationship": relationship
            })
            print(f"✅ Yolcu eklendi: {given} {surname}")
        else:
            print(f"⚠️ Uyarı: {prefix} için eksik veri bulundu, atlanıyor.")

        i += 1
        if i > 20:
            break

    data["TRAVEL_COMPANIONS_LIST"] = companions
    return data


def fill_travel_companions(wait, driver, data):
    print("🧭 Travel Companions başladı")

    companions = data.get("TRAVEL_COMPANIONS", "NO").strip().upper()

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblOtherPersonsTravelingWithYou_0"
        if companions == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblOtherPersonsTravelingWithYou_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()
    print(f"✅ Traveling with others: {companions}")
    time.sleep(1.5)

    if companions == "NO":
        print("ℹ️ Travel companions yok")
        return

    group_no_id = "ctl00_SiteContentPlaceHolder_FormView1_rblGroupTravel_1"
    wait.until(EC.element_to_be_clickable((By.ID, group_no_id))).click()
    print("✅ Group Travel: NO")
    time.sleep(1)

    persons = data.get("TRAVEL_COMPANIONS_LIST", [])
    if not persons:
        print("⚠️ TRAVEL_COMPANIONS_LIST boş — NO'ya çevriliyor")
        try:
            no_radio = wait.until(EC.element_to_be_clickable((
            By.ID,
            "ctl00_SiteContentPlaceHolder_FormView1_rblOtherPersonsTravelingWithYou_1"
        )))
            driver.execute_script("arguments[0].click();", no_radio)
            print("✅ Traveling with others: NO (fallback)")
        except Exception as e:
            print(f"⚠️ NO radio tıklanamadı: {e}")
        return

    base_path = "ctl00_SiteContentPlaceHolder_FormView1_dlTravelCompanions_ctl"

    def js_fill(element_id, value):
        for attempt in range(3):
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                driver.execute_script("""
                    arguments[0].removeAttribute('disabled');
                    arguments[0].removeAttribute('readonly');
                    arguments[0].value = '';
                """, el)
                el.send_keys(value)
                return
            except StaleElementReferenceException:
                print(f"⚠️ js_fill stale retry {attempt+1}: {element_id}")
                time.sleep(0.5)

    def safe_select(element_id, value, retries=5):
        for attempt in range(retries):
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
                sel = Select(el)

                if attempt == 0:
                    opts = [(o.get_attribute("value"), o.text.strip()) for o in sel.options]
                    print(f"ℹ️ Options [{element_id.split('_')[-1]}]: {opts}")

                # Value ile dene
                try:
                    sel.select_by_value(value)
                    return
                except Exception:
                    pass

                # Visible text ile dene
                try:
                    sel.select_by_visible_text(value)
                    return
                except Exception:
                    pass

                # Fallback: boş olmayan ilk option'ı seç
                for opt in sel.options:
                    if opt.get_attribute("value") and opt.get_attribute("value") != "":
                        sel.select_by_value(opt.get_attribute("value"))
                        print(f"⚠️ Fallback option seçildi: {opt.get_attribute('value')} ({opt.text})")
                        return

                raise Exception(f"Value bulunamadı: {value}")
            except StaleElementReferenceException:
                print(f"⚠️ safe_select stale retry {attempt+1}: {element_id}")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ safe_select hata retry {attempt+1}: {e}")
                time.sleep(0.5)
        raise Exception(f"❌ safe_select başarısız: {element_id}={value}")
    
    for i, person in enumerate(persons):
        idx = f"{i:02d}"
        print(f"👤 Yolcu {i+1} işleniyor...")

        def get_id(field, _idx=idx):
            return f"{base_path}{_idx}_{field}"

        surname   = person.get("surname", "").strip()
        given     = person.get("given", "").strip()
        rel_value = person.get("relationship", "").strip().upper()

        if not surname or not given:
            raise Exception(f"❌ Companion {i+1}: isim/soyisim eksik")

        # Relationship — stale-safe
        safe_select(get_id("ddlTCRelationship"), rel_value)
        time.sleep(0.5)

        js_fill(get_id("tbxSurname"), surname)
        js_fill(get_id("tbxGivenName"), given)

        print(f"✅ Companion {i+1} dolduruldu: {given} {surname}")

        if i < len(persons) - 1:
            add_btn_id = get_id("InsertButtonPrincipalPOT")
            # Add Another — stale-safe tıklama
            for attempt in range(3):
                try:
                    add_btn = wait.until(
                        EC.element_to_be_clickable((By.ID, add_btn_id))
                    )
                    driver.execute_script("arguments[0].click();", add_btn)
                    print("➕ Add Another tıklandı")
                    break
                except StaleElementReferenceException:
                    print(f"⚠️ Add Another stale retry {attempt+1}")
                    time.sleep(0.5)

            # Yeni satırın DOM'a girmesini bekle
            next_idx = f"{i+1:02d}"
            next_rel_id = f"{base_path}{next_idx}_ddlTCRelationship"
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, next_rel_id))
                )
                print(f"✅ Yeni satır hazır: {next_idx}")
            except Exception:
                print("⚠️ Yeni satır timeout, devam ediliyor...")
            time.sleep(0.5)

    print("🟢 Travel Companions TAMAMLANDI")

def fill_single_us_visit(wait, driver, data, index=1):
    date   = data.get(f"VISIT{index}_ARRIVAL_DATE", "").strip()
    length = data.get(f"VISIT{index}_STAY_LENGTH", "").strip()

    if not date or not length:
        print(f"⚠️ VISIT{index} verisi eksik, atlanıyor")
        return

    unit_map = {
        "YEAR": "Y", "YEARS": "Y", "Y": "Y",
        "MONTH": "M", "MONTHS": "M", "M": "M",
        "WEEK": "W", "WEEKS": "W", "W": "W",
        "DAY": "D", "DAYS": "D", "D": "D",
    }
    unit = unit_map.get(str(data.get(f"VISIT{index}_STAY_UNIT", "D")).strip().upper(), "D")

    parts = date.split("-")
    if len(parts) != 3:
        print(f"⚠️ VISIT{index} tarih formatı hatalı: {date}, atlanıyor")
        return

    day, month, year = parts
    month_map = {
        "JAN": "1", "FEB": "2", "MAR": "3", "APR": "4",
        "MAY": "5", "JUN": "6", "JUL": "7", "AUG": "8",
        "SEP": "9", "OCT": "10", "NOV": "11", "DEC": "12",
        "01": "1", "02": "2", "03": "3", "04": "4",
        "05": "5", "06": "6", "07": "7", "08": "8",
        "09": "9", "10": "10", "11": "11", "12": "12",
        "1": "1", "2": "2", "3": "3", "4": "4",
        "5": "5", "6": "6", "7": "7", "8": "8",
        "9": "9",
    }

    if month.upper() not in month_map:
        print(f"⚠️ VISIT{index} ay değeri tanımsız: {month}, atlanıyor")
        return

    # index'e göre ctl ID — ilk: ctl00, ikinci: ctl01...
    ctl = f"ctl{str(index - 1).zfill(2)}"

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, f"ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_{ctl}_ddlPREV_US_VISIT_DTEDay")
    ))).select_by_value(str(int(day)))

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, f"ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_{ctl}_ddlPREV_US_VISIT_DTEMonth")
    ))).select_by_value(month_map[month.upper()])

    year_el = wait.until(EC.presence_of_element_located(
        (By.ID, f"ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_{ctl}_tbxPREV_US_VISIT_DTEYear")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, year_el)
    year_el.send_keys(year)

    los_el = wait.until(EC.presence_of_element_located(
        (By.ID, f"ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_{ctl}_tbxPREV_US_VISIT_LOS")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, los_el)
    los_el.send_keys(length)

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, f"ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_{ctl}_ddlPREV_US_VISIT_LOS_CD")
    ))).select_by_value(unit)

    print(f"✅ US Visit {index} girildi ({ctl})")


def fill_previous_us_travel(wait, driver, data):
    prev = data.get("PREV_US_TRAVEL", "NO").strip().upper()

    if prev not in ("YES", "NO"):
        raise Exception("❌ PREV_US_TRAVEL YES veya NO olmalı")

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_US_TRAVEL_IND_0"
        if prev == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_US_TRAVEL_IND_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()
    print(f"✅ Previous US Travel: {prev}")
    time.sleep(2)

    if prev == "NO":
        return

    actual_visits = 0
    while data.get(f"VISIT{actual_visits + 1}_ARRIVAL_DATE"):
        actual_visits += 1

    requested = int(data.get("PREV_US_VISITS", 1))
    visits = min(requested, actual_visits) if actual_visits > 0 else 1
    print(f"ℹ️ PREV_US_VISITS={requested}, gerçek veri={actual_visits}, kullanılan={visits}")

    # Sayfada kaç satır mevcut?
    existing_rows = 0
    while True:
        ctl = f"ctl{str(existing_rows).zfill(2)}"
        els = driver.find_elements(
            By.ID,
            f"ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_{ctl}_tbxPREV_US_VISIT_DTEYear"
        )
        if not els:
            break
        existing_rows += 1
    print(f"ℹ️ Sayfada {existing_rows} mevcut satır, {visits} gerekli")

    # Eksik kadar Insert'e tıkla
    for i in range(existing_rows, visits):
        ctl = f"ctl{str(i - 1).zfill(2)}"
        wait.until(EC.element_to_be_clickable((By.ID,
            f"ctl00_SiteContentPlaceHolder_FormView1_dtlPREV_US_VISIT_{ctl}_InsertButtonPREV_US_VISIT"
        ))).click()
        print(f"✅ Visit satırı {i + 1} eklendi")
        time.sleep(2)

    # Hepsini doldur
    for i in range(1, visits + 1):
        fill_single_us_visit(wait, driver, data, index=i)

    # Public school sorusu (varsa — F vizesiyle ilgili)
    try:
        public_school_no = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID,
                "ctl00_SiteContentPlaceHolder_FormView1_rblPUBLIC_SCHOOL_IND_1"
            ))
        )
        public_school_no.click()
        print("✅ Public School: NO")
        time.sleep(1)
    except Exception:
        print("ℹ️ Public School sorusu yok, atlanıyor")

    dl = data.get("US_DRIVER_LICENSE", "NO").strip().upper()
    if dl not in ("YES", "NO"):
        raise Exception("❌ US_DRIVER_LICENSE YES veya NO olmalı")

    dl_radio = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_US_DRIVER_LIC_IND_0"
        if dl == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_US_DRIVER_LIC_IND_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, dl_radio))).click()
    print(f"✅ US Driver License: {dl}")
    time.sleep(2)

    if dl == "YES":
        fill_us_driver_license(wait, driver, data)

def fill_us_driver_license(wait, driver, data):

    lic_no = data.get("US_DRIVER_LICENSE_NUMBER", "NA").strip().upper()
    raw_state = data.get("US_DRIVER_LICENSE_STATE", "").strip().upper()

    if lic_no in ("NA", "N/A", ""):
        na_checkbox = wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlUS_DRIVER_LICENSE_ctl00_cbxUS_DRIVER_LICENSE_NA")
        ))
        if not na_checkbox.is_selected():
            na_checkbox.click()
            time.sleep(2)
            print("ℹ️ Driver License Number: Do Not Know seçildi")
    else:
        lic_input = wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlUS_DRIVER_LICENSE_ctl00_tbxUS_DRIVER_LICENSE")
        ))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, lic_input)
        lic_input.send_keys(lic_no)
        print(f"✅ Driver License Number girildi: {lic_no}")

    if not raw_state:
        raise Exception("❌ US_DRIVER_LICENSE_STATE zorunlu")

    state_code = raw_state if len(raw_state) == 2 else US_STATE_MAP.get(raw_state)
    if not state_code:
        raise Exception(f"❌ Geçersiz eyalet adı: {raw_state}")

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlUS_DRIVER_LICENSE_ctl00_ddlUS_DRIVER_LICENSE_STATE")
    ))).select_by_value(state_code)

    print(f"✅ Driver License State seçildi: {raw_state} → {state_code}")
    click_outside(driver)


def fill_previous_visa(wait, driver, data):

    prev = data.get("PREV_VISA", "NO").strip().upper()
    if prev not in ("YES", "NO"):
        raise Exception("❌ PREV_VISA YES veya NO olmalı")

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_IND_0"
        if prev == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_IND_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()
    print(f"✅ Previous Visa: {prev}")
    time.sleep(2)

    if prev == "NO":
        return

    def js_fill(element_id, value):
        el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(value)

    # Date Last Visa Issued
    date = data["PREV_VISA_ISSUE_DATE"]
    day, month, year = date.split("-")
    month_map = {
        "JAN": "1", "FEB": "2", "MAR": "3", "APR": "4",
        "MAY": "5", "JUN": "6", "JUL": "7", "AUG": "8",
        "SEP": "9", "OCT": "10", "NOV": "11", "DEC": "12"
    }

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlPREV_VISA_ISSUED_DTEDay")
    ))).select_by_value(str(int(day)))

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlPREV_VISA_ISSUED_DTEMonth")
    ))).select_by_value(month_map[month.upper()])

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_ISSUED_DTEYear", year)

    # Visa Number
    visa_no = data.get("PREV_VISA_NUMBER", "NA").strip().upper()
    if visa_no in ("NA", "N/A"):
        wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxPREV_VISA_FOIL_NUMBER_NA")
        )).click()
    else:
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_FOIL_NUMBER", visa_no)

    # YES/NO Questions
    def yesno(key, yes_id, no_id):
        val = data[key].strip().upper()
        rid = yes_id if val == "YES" else no_id
        wait.until(EC.element_to_be_clickable((By.ID, rid))).click()
        time.sleep(1)
        return val

    yesno(
        "PREV_VISA_SAME_TYPE",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_SAME_TYPE_IND_0",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_SAME_TYPE_IND_1"
    )
    yesno(
        "PREV_VISA_SAME_COUNTRY",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_SAME_CNTRY_IND_0",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_SAME_CNTRY_IND_1"
    )
    yesno(
        "PREV_VISA_TEN_PRINTED",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_TEN_PRINT_IND_0",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_TEN_PRINT_IND_1"
    )

    # Visa Lost
    lost = yesno(
        "PREV_VISA_LOST",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_LOST_IND_0",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_LOST_IND_1"
    )
    if lost == "YES":
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_LOST_YEAR", data["PREV_VISA_LOST_YEAR"])
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_LOST_EXPL", data["PREV_VISA_LOST_EXPL"])

    # Visa Cancelled
    cancelled = yesno(
        "PREV_VISA_CANCELLED",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_CANCELLED_IND_0",
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_CANCELLED_IND_1"
    )
    if cancelled == "YES":
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_CANCELLED_EXPL", data["PREV_VISA_CANCELLED_EXPL"])

    click_outside(driver)
    print("✅ Previous Visa bölümü tamamlandı")


def fill_prev_visa_refused(wait, driver, data):

    refused = data.get("PREV_VISA_REFUSED", "NO").strip().upper()
    if refused not in ("YES", "NO"):
        raise Exception("❌ PREV_VISA_REFUSED YES veya NO olmalı")

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_REFUSED_IND_0"
        if refused == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblPREV_VISA_REFUSED_IND_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()
    print(f"✅ Previous Visa Refused: {refused}")
    time.sleep(2)

    if refused == "YES":
        explanation = data.get("PREV_VISA_REFUSED_EXPL", "").strip()
        if not explanation:
            raise Exception("❌ PREV_VISA_REFUSED_EXPL boş olamaz (YES seçildi)")

        expl_box = wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxPREV_VISA_REFUSED_EXPL")
        ))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, expl_box)
        expl_box.send_keys(explanation)
        print("📝 Visa refusal explanation girildi")
        click_outside(driver)


def fill_iv_petition(wait, driver, data):
    print("📋 IV Petition kontrol ediliyor...")

    iv_status = (data.get("IV_PETITION") or "NO").strip().upper()
    idx = "0" if iv_status == "YES" else "1"
    radio_id = f"ctl00_SiteContentPlaceHolder_FormView1_rblIV_PETITION_IND_{idx}"

    try:
        radio_el = wait.until(EC.presence_of_element_located((By.ID, radio_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio_el)
        time.sleep(0.5)

        if not radio_el.is_selected():
            driver.execute_script("arguments[0].click();", radio_el)
            print(f"🖱️ IV Petition '{iv_status}' işaretlendi.")
            time.sleep(2)
        else:
            print("⚡ IV Petition zaten doğru işaretli.")

        if iv_status == "YES":
            expl_text = data.get("IV_PETITION_EXPL", "Previous petition filed.")
            expl_box = wait.until(EC.visibility_of_element_located(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxIV_PETITION_EXPL")
            ))
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
            """, expl_box)
            expl_box.send_keys(expl_text)
            print("📝 IV Petition açıklaması girildi.")

    except Exception as e:
        print(f"❌ IV Petition hatası: {str(e)}")

def fill_esta_denial(wait, driver, data):
    print("🛂 ESTA Denial kontrol ediliyor...")

    esta_status = (data.get("ESTA_DENIED") or "NO").strip().upper()
    idx = "0" if esta_status == "YES" else "1"
    radio_id = f"ctl00_SiteContentPlaceHolder_FormView1_rblVWP_DENIAL_IND_{idx}"

    try:
        radio_el = wait.until(EC.presence_of_element_located((By.ID, radio_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio_el)
        time.sleep(0.5)

        if not radio_el.is_selected():
            driver.execute_script("arguments[0].click();", radio_el)
            print(f"🖱️ ESTA Denial '{esta_status}' işaretlendi.")
            time.sleep(2)

    except Exception as e:
        print(f"⚠️ ESTA radio bulunamadı: {str(e)}")


def split_address(address, max_len=40):
    address = address.strip()
    if len(address) <= max_len:
        return address, ""
    else:
        return address[:max_len], address[max_len:].lstrip()


def fill_home_address(wait, driver, data):

    full_address = clean_address(data.get("HOME_ADDRESS", "").strip())
    city         = clean_address(data.get("HOME_CITY", "").strip())
    state        = clean_address(data.get("HOME_STATE", "").strip())
    postal       = data.get("HOME_POSTAL_CODE", "").strip()
    country      = data.get("HOME_COUNTRY", "").strip().upper()

    if not full_address or not city or not country:
        raise Exception("❌ HOME_ADDRESS, HOME_CITY, HOME_COUNTRY zorunlu")

    addr1, addr2 = split_address(full_address, max_len=40)
    print(f"📍 HOME addr1: '{addr1}' ({len(addr1)} kar)")
    print(f"📍 HOME addr2: '{addr2}' ({len(addr2)} kar)")

    def js_fill(element_id, value):
        if not value:
            return
        try:
            el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
            """, el)
            el.send_keys(value)
        except Exception as e:
            print(f"⚠️ js_fill hata {element_id}: {e}")

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_LN1", addr1)
    time.sleep(0.2)

    # 2. satır — addr2 varsa doldur, yoksa temizle
    try:
        addr2_el = wait.until(EC.presence_of_element_located((
            By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_LN2"
        )))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, addr2_el)
        if addr2:
            addr2_el.send_keys(addr2)
            print(f"📍 HOME addr2 dolduruldu: '{addr2}'")
    except Exception as e:
        print(f"⚠️ addr2 alanı bulunamadı: {e}")

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_CITY", city)

    state_input = wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_STATE")
    ))
    state_na_checkbox = wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbexAPP_ADDR_STATE_NA")
    ))

    if state:
        if state_na_checkbox.is_selected():
            state_na_checkbox.click()
            time.sleep(0.3)
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, state_input)
        state_input.send_keys(state)
        print(f"✅ State girildi: {state}")
    else:
        if not state_na_checkbox.is_selected():
            state_na_checkbox.click()
            time.sleep(0.3)
        print("ℹ️ State/Province: Does Not Apply")

    if postal:
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_POSTAL_CD", postal)

    select_country_by_name(
        wait,
        "ctl00_SiteContentPlaceHolder_FormView1_ddlCountry",
        country
    )

    print(f"🌍 Home Address tamamlandı → {addr1} | {addr2} | {city} | {country}")
    click_outside(driver)
    time.sleep(0.5)
def fill_mailing_address(wait, driver, data):

    same = data.get("MAILING_SAME_AS_HOME", "YES").strip().upper()
    if same not in ("YES", "NO"):
        raise Exception("❌ MAILING_SAME_AS_HOME YES veya NO olmalı")

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblMailingAddrSame_0"
        if same == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblMailingAddrSame_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()
    print(f"📬 Mailing Address Same as Home: {same}")
    time.sleep(1.5)

    if same == "YES":
        return

    full_address = data.get("MAILING_ADDRESS", "").strip()
    city = data.get("MAILING_CITY", "").strip()
    state = data.get("MAILING_STATE", "").strip()
    postal = data.get("MAILING_POSTAL_CODE", "").strip()
    country = data.get("MAILING_COUNTRY", "").strip().upper()

    if not full_address or not city or not country:
        raise Exception("❌ MAILING_ADDRESS, MAILING_CITY, MAILING_COUNTRY zorunlu")

    addr1, addr2 = split_address(full_address)

    def js_fill(element_id, value):
        el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(value)

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_LN1", addr1)

    if addr2:
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_LN2", addr2)

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_CITY", city)

    state_input = wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_STATE")
    ))
    state_na_checkbox = wait.until(EC.presence_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbexMAILING_ADDR_STATE_NA")
    ))

    if state:
        if state_na_checkbox.is_selected():
            state_na_checkbox.click()
            time.sleep(0.3)
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, state_input)
        state_input.send_keys(state)
        print(f"✅ Mailing State girildi: {state}")
    else:
        if not state_na_checkbox.is_selected():
            state_na_checkbox.click()
            time.sleep(0.3)
        print("ℹ️ Mailing State: Does Not Apply")

    if postal:
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxMAILING_ADDR_POSTAL_CD", postal)

    select_country_by_name(
        wait,
        "ctl00_SiteContentPlaceHolder_FormView1_ddlMailCountry",
        country
    )

    print("✅ Mailing Address girildi")
    click_outside(driver)
    time.sleep(0.5)
def clean_phone(phone: str) -> str:
    """Telefon numarasından () - . boşluk vb karakterleri temizler, + başında kalır."""
    if not phone:
        return ""
    phone = phone.strip()
    # + varsa koru
    has_plus = phone.startswith("+")
    # Sadece rakamları al
    digits = "".join(c for c in phone if c.isdigit())
    return ("+" + digits) if has_plus else digits


def clean_address(addr: str) -> str:
    """Adres metninden noktalama işaretlerini temizler."""
    if not addr:
        return ""
    import re
    # Virgül, nokta, !, ?, ;, :, ', " gibi noktalama işaretlerini kaldır
    cleaned = re.sub(r"[.,!?;:\"\'`]", " ", addr)
    # Çoklu boşlukları tek boşluğa indir
    cleaned = re.sub(r"\s+", " ", cleaned).strip().upper()
    return cleaned




def safe_phone_fill(wait, driver, input_id, checkbox_id, value):
    try:
        cb = driver.find_element(By.ID, checkbox_id)
        if cb.is_selected():
            print(f"🔗 {checkbox_id} işareti kaldırılıyor...")
            driver.execute_script("arguments[0].click();", cb)
            time.sleep(1)

        input_field = wait.until(EC.visibility_of_element_located((By.ID, input_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_field)
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, input_field)

        if value and str(value).strip().upper() not in ("NA", ""):
            input_field.send_keys(str(value).strip())
            print(f"✅ {input_id} değer girildi: {value}")
        else:
            driver.execute_script("arguments[0].click();", cb)
            print(f"ℹ️ {input_id} için N/A işaretlendi.")

    except Exception as e:
        print(f"⚠️ {input_id} doldurulurken hata: {e}")


def fill_phone_numbers(wait, driver, data):
    print("📞 Phone bilgileri düzenleniyor...")

    primary_raw  = data.get("PRIMARY_PHONE", "").strip()
    mobile_raw   = data.get("MOBILE_PHONE", "").strip()
    work_raw     = data.get("WORK_PHONE", "").strip()

    primary = clean_phone(primary_raw)
    mobile  = clean_phone(mobile_raw)
    work    = clean_phone(work_raw)

    # Primary — zorunlu
    p_field = wait.until(EC.visibility_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_HOME_TEL")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, p_field)
    p_field.send_keys(primary or "5555555555")
    print(f"✅ Primary Phone: {primary or '5555555555'}")

    # Mobile — primary ile aynıysa veya boşsa NA işaretle
    mobile_input_id  = "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_MOBILE_TEL"
    mobile_na_id     = "ctl00_SiteContentPlaceHolder_FormView1_cbexAPP_MOBILE_TEL_NA"

    if not mobile or mobile == primary:
        # NA işaretle
        try:
            cb = driver.find_element(By.ID, mobile_na_id)
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
                time.sleep(0.5)
            print("ℹ️ Mobile Phone: Does Not Apply (boş veya primary ile aynı)")
        except Exception as e:
            print(f"⚠️ Mobile NA checkbox: {e}")
    else:
        safe_phone_fill(wait, driver, mobile_input_id, mobile_na_id, mobile)
        print(f"✅ Mobile Phone: {mobile}")

    # Work — primary ile aynıysa veya boşsa NA işaretle
    work_input_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_BUS_TEL"
    work_na_id    = "ctl00_SiteContentPlaceHolder_FormView1_cbexAPP_BUS_TEL_NA"

    if not work or work == primary:
        try:
            cb = driver.find_element(By.ID, work_na_id)
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
                time.sleep(0.5)
            print("ℹ️ Work Phone: Does Not Apply (boş veya primary ile aynı)")
        except Exception as e:
            print(f"⚠️ Work NA checkbox: {e}")
    else:
        safe_phone_fill(wait, driver, work_input_id, work_na_id, work)
        print(f"✅ Work Phone: {work}")

def fill_additional_phone(wait, driver, data):
    print("📞 Additional Phone başlıyor")

    has = data.get("HAS_ADDITIONAL_PHONE", "NO").strip().upper()

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblAddPhone_0"
        if has == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblAddPhone_1"
    )

    radio_btn = wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
    radio_btn.click()
    print(f"✅ Additional Phone seçildi: {has}")
    time.sleep(2)

    wait.until(EC.visibility_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_lblAddPhone")
    ))

    if has == "NO":
        print("ℹ️ Additional Phone yok → devam ediliyor")
        return

    phone = data.get("ADDITIONAL_PHONE_NUM", "").strip()
    if not phone:
        print("⚠️ Ek telefon seçildi ama numara boş!")
        return

    phone_input_id = "ctl00_SiteContentPlaceHolder_FormView1_dtlAddPhone_ctl00_tbxAddPhoneInfo"
    phone_field = wait.until(EC.visibility_of_element_located((By.ID, phone_input_id)))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, phone_field)
    phone_field.send_keys(phone)
    print(f"✅ Additional Phone girildi: {phone}")


def fill_email(wait, driver, data):
    email = (data.get("EMAIL") or "").strip()
    if not email:
        raise Exception("❌ EMAIL zorunlu")

    email_input = wait.until(EC.visibility_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_EMAIL_ADDR")
    ))
    driver.execute_script("""
        var el = arguments[0];
        var val = arguments[1];
        el.scrollIntoView({block:'center'});
        el.removeAttribute('disabled');
        el.removeAttribute('readonly');
        el.focus();
        el.value = '';
        el.value = val;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
    """, email_input, email)
    time.sleep(0.7)

    actual_val = email_input.get_attribute("value")
    if actual_val == email:
        print(f"✅ Email başarıyla girildi: {email}")
    else:
        print(f"⚠️ Email girildi ama kontrol edildiğinde farklı görünüyor!")


def fill_additional_email(wait, driver, data):
    print("📧 Additional Email bölümü dolduruluyor...")

    has = data.get("HAS_ADDITIONAL_EMAIL", "NO").strip().upper()

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblAddEmail_0"
        if has == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblAddEmail_1"
    )

    radio_btn = wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
    radio_btn.click()
    print(f"✅ Additional Email seçimi: {has}")
    time.sleep(1.5)

    if has == "NO":
        return

    email = data.get("ADDITIONAL_EMAIL1", "").strip()
    if not email:
        print("⚠️ HAS_ADDITIONAL_EMAIL 'YES' ama email adresi boş!")
        return

    email_input_id = "ctl00_SiteContentPlaceHolder_FormView1_dtlAddEmail_ctl00_tbxAddEmailInfo"

    try:
        email_field = wait.until(EC.visibility_of_element_located((By.ID, email_input_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, email_field)
        email_field.send_keys(email)
        print(f"✅ Ek e-posta girildi: {email}")
    except Exception as e:
        print(f"❌ E-posta kutusu doldurulamadı: {e}")


def fill_social_media(wait, driver, data):
    print("📱 Social Media başladı")

    platforms_raw = data.get("SOCIAL_MEDIA", "NONE").upper().strip()
    usernames_raw = data.get("SOCIAL_MEDIA_USERNAME", "").strip()

    if platforms_raw == "NONE" or not platforms_raw:
        ddl_none = wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlSocial_ctl00_ddlSocialMedia")
        ))
        Select(ddl_none).select_by_value("NONE")
        print("ℹ️ Social Media: NONE seçildi")
        return

    platforms = [p.strip() for p in platforms_raw.split(",")]
    usernames = [u.strip() for u in usernames_raw.split(",")]

    if len(platforms) != len(usernames):
        raise Exception(f"❌ Platform sayısı ({len(platforms)}) ile username sayısı ({len(usernames)}) uyuşmuyor!")

    base_id = "ctl00_SiteContentPlaceHolder_FormView1_dtlSocial_ctl"

    # Sayfada kaç satır mevcut?
    existing_rows = 0
    while True:
        ctl = f"{existing_rows:02d}"
        els = driver.find_elements(By.ID, f"{base_id}{ctl}_ddlSocialMedia")
        if not els:
            break
        existing_rows += 1
    print(f"ℹ️ Sayfada {existing_rows} mevcut sosyal medya satırı, {len(platforms)} gerekli")

    # Eksik kadar Add'e tıkla
    for i in range(existing_rows, len(platforms)):
        prev_ctl = f"{i - 1:02d}"
        add_btn_id = f"{base_id}{prev_ctl}_InsertButtonSOCIAL_MEDIA_INFO"
        wait.until(EC.element_to_be_clickable((By.ID, add_btn_id))).click()
        print(f"➕ Add Another tıklandı ({i}. satır için)")
        next_ctl = f"{i:02d}"
        wait.until(EC.presence_of_element_located(
            (By.ID, f"{base_id}{next_ctl}_ddlSocialMedia")
        ))
        time.sleep(1)

    # Hepsini doldur
    for i, platform_raw in enumerate(platforms):
        idx = f"{i:02d}"
        platform_value = SOCIAL_MEDIA_MAP.get(platform_raw)

        if not platform_value:
            raise Exception(f"❌ SOCIAL_MEDIA_MAP içinde bulunamadı: {platform_raw}")

        ddl_id = f"{base_id}{idx}_ddlSocialMedia"
        input_id = f"{base_id}{idx}_tbxSocialMediaIdent"

        dropdown_el = wait.until(EC.element_to_be_clickable((By.ID, ddl_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown_el)
        Select(dropdown_el).select_by_value(platform_value)
        print(f"✅ [{i+1}] {platform_raw} seçildi")

        if platform_value != "NONE":
            time.sleep(0.5)
            input_el = wait.until(EC.element_to_be_clickable((By.ID, input_id)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_el)
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
            """, input_el)
            input_el.send_keys(usernames[i])
            print(f"✅ [{i+1}] Username yazıldı: {usernames[i]}")

    click_outside(driver)
    print("🟢 Social Media TAMAMLANDI")

def fill_additional_social_media(wait, driver, data):

    answer = data.get("ADDITIONAL_SOCIAL", "NO").strip().upper()
    print(f"DEBUG ADDITIONAL_SOCIAL RAW → [{repr(answer)}]")

    yes_id = "ctl00_SiteContentPlaceHolder_FormView1_rblAddSocial_0"
    no_id  = "ctl00_SiteContentPlaceHolder_FormView1_rblAddSocial_1"

    if answer not in ("YES", "NO"):
        raise Exception("❌ ADDITIONAL_SOCIAL YES veya NO olmalı")

    wait.until(EC.element_to_be_clickable(
        (By.ID, yes_id if answer == "YES" else no_id)
    )).click()

    print(f"✅ Additional Social Media: {answer}")
    time.sleep(2)

    if answer == "NO":
        return

    platforms = [p.strip() for p in data.get("ADDITIONAL_SOCIAL_PLATFORM", "").split(",") if p.strip()]
    usernames = [u.strip() for u in data.get("ADDITIONAL_SOCIAL_USERNAME", "").split(",") if u.strip()]

    if len(platforms) != len(usernames):
        raise Exception("❌ PLATFORM ve USERNAME sayısı eşit olmalı")

    base = "ctl00_SiteContentPlaceHolder_FormView1_dtlAddSocial_ctl"

    for i, (platform, username) in enumerate(zip(platforms, usernames)):
        idx = f"{i:02d}"

        plat_id = f"{base}{idx}_tbxAddSocialPlat"
        user_id = f"{base}{idx}_tbxAddSocialHand"
        add_btn = f"{base}{idx}_InsertButtonADDL_SOCIAL_MEDIA"

        def js_fill(element_id, value):
            el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
            """, el)
            el.send_keys(value)

        js_fill(plat_id, platform)
        js_fill(user_id, username)

        print(f"✅ [{i+1}] Additional Social: {platform} / {username}")

        if i < len(platforms) - 1:
            wait.until(EC.element_to_be_clickable((By.ID, add_btn))).click()
            print("➕ Add Another (Additional Social)")
            time.sleep(2)

    click_outside(driver)




def fill_date_dd_mmm_yyyy(wait, driver, day_id, month_id, year_id, date_str):
    if not date_str:
        return

    # DD-MMM-YYYY veya DD-MM-YYYY parse et
    parts = str(date_str).strip().split("-")
    if len(parts) != 3:
        return

    day_text   = parts[0].strip().zfill(2)
    month_text = parts[1].strip().upper()
    year_text  = parts[2].strip()

    # Ay numaradan 3 harfe çevir
    _MON = {
        "01":"JAN","02":"FEB","03":"MAR","04":"APR","05":"MAY","06":"JUN",
        "07":"JUL","08":"AUG","09":"SEP","10":"OCT","11":"NOV","12":"DEC",
        "1":"JAN","2":"FEB","3":"MAR","4":"APR","5":"MAY","6":"JUN",
        "7":"JUL","8":"AUG","9":"SEP","10":"OCT","11":"NOV","12":"DEC",
    }
    if month_text.isdigit():
        month_text = _MON.get(month_text, "JAN")

    def _safe_select_day(el_id, value):
        # Disabled olabilir — JS ile force et
        for attempt in range(3):
            try:
                sel = Select(wait.until(
                    EC.presence_of_element_located((By.ID, el_id))
                ))
                # Önce normal dene
                try:
                    sel.select_by_value(value)
                    return
                except Exception:
                    pass
                # disabled option varsa JS ile seç
                driver.execute_script("""
                    var sel = arguments[0];
                    var val = arguments[1];
                    for(var i=0; i<sel.options.length; i++){
                        sel.options[i].disabled = false;
                        if(sel.options[i].value === val || 
                           sel.options[i].text.trim() === val){
                            sel.options[i].selected = true;
                            sel.dispatchEvent(new Event('change'));
                            break;
                        }
                    }
                """, driver.find_element(By.ID, el_id), value)
                return
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    print(f"⚠️ select {el_id}={value}: {e}")

    def _safe_select_month(el_id, value):
        for attempt in range(3):
            try:
                sel = Select(wait.until(
                    EC.presence_of_element_located((By.ID, el_id))
                ))
                try:
                    sel.select_by_value(value)
                    return
                except Exception:
                    pass
                driver.execute_script("""
                    var sel = arguments[0];
                    var val = arguments[1];
                    for(var i=0; i<sel.options.length; i++){
                        sel.options[i].disabled = false;
                        if(sel.options[i].value === val ||
                           sel.options[i].text.trim() === val){
                            sel.options[i].selected = true;
                            sel.dispatchEvent(new Event('change'));
                            break;
                        }
                    }
                """, driver.find_element(By.ID, el_id), value)
                return
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    print(f"⚠️ select {el_id}={value}: {e}")

    def _safe_fill_year(el_id, value):
        for attempt in range(3):
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, el_id)))
                driver.execute_script("""
                    arguments[0].removeAttribute('disabled');
                    arguments[0].removeAttribute('readonly');
                    arguments[0].value = '';
                """, el)
                el.send_keys(str(value))
                return
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    print(f"⚠️ year {el_id}={value}: {e}")

    _safe_select_day(day_id, day_text)
    time.sleep(0.2)
    _safe_select_month(month_id, month_text)
    time.sleep(0.2)
    _safe_fill_year(year_id, year_text)

def fill_passport_info(wait, driver, data):
    print("🛂 Passport section başladı")

    def js_fill(element_id, value):
        el = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(value)

    passport_type = data.get("PASSPORT_TYPE", "REGULAR").strip().upper()
    type_value = PASSPORT_TYPE_MAP.get(passport_type)
    if not type_value:
        print(f"⚠️ Geçersiz PASSPORT_TYPE: {passport_type}, REGULAR olarak devam ediliyor")
        type_value = "R"

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_TYPE")
    ))).select_by_value(type_value)
    print(f"✅ Pasaport tipi seçildi: {passport_type} → {type_value}")

    time.sleep(1.5)
    wait.until(EC.visibility_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_NUM")
    ))

    if type_value == "T":
        expl = data.get("PASSPORT_OTHER_EXPL", "").strip()
        if not expl:
            expl = "OTHER TRAVEL DOCUMENT"
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPptOtherExpl", expl)

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_NUM", str(data.get("PASSPORT_NUMBER", "")).strip())

    book_num = data.get("PASSPORT_BOOK_NUMBER", "").strip().upper()
    if book_num in ("", "NA", "N/A", "DOES NOT APPLY"):
        cb_book_na = wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbexPPT_BOOK_NUM_NA")
        ))
        if not cb_book_na.is_selected():
            cb_book_na.click()
    else:
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_BOOK_NUM", book_num)

    select_country_by_name(wait, "ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_CNTRY", data.get("PASSPORT_ISSUED_COUNTRY", "TURKEY"))
    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUED_IN_CITY", data.get("PASSPORT_ISSUED_CITY", ""))

    state = data.get("PASSPORT_ISSUED_STATE", "").strip()
    if state and state.upper() not in ("NA", "N/A"):
        try:
            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUED_IN_STATE", state)
        except Exception:
            print("⚠️ State alanı bulunamadı, atlanıyor.")

    select_country_by_name(wait, "ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_IN_CNTRY", data.get("PASSPORT_ISSUED_IN_COUNTRY", "TURKEY"))

    fill_date_dd_mmm_yyyy(
        wait, driver,
        "ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_DTEDay",
        "ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_ISSUED_DTEMonth",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUEDYear",
        data.get("PASSPORT_ISSUE_DATE", "")
    )

    exp_date = data.get("PASSPORT_EXPIRY_DATE", "").strip().upper()
    if exp_date in ("", "NA", "N/A"):
        cb_exp_na = wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxPPT_EXPIRE_NA")
        ))
        if not cb_exp_na.is_selected():
            cb_exp_na.click()
    else:
        fill_date_dd_mmm_yyyy(
            wait, driver,
            "ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_EXPIRE_DTEDay",
            "ctl00_SiteContentPlaceHolder_FormView1_ddlPPT_EXPIRE_DTEMonth",
            "ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_EXPIREYear",
            data.get("PASSPORT_EXPIRY_DATE", "")
        )

    print("🟢 Passport section TAMAMLANDI")

def fill_lost_passport(wait, driver, data):
    print("🟠 Lost Passport bölümü başladı")

    lost = data.get("PASSPORT_LOST", "NO").strip().upper()

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblLOST_PPT_IND_0"
        if lost == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblLOST_PPT_IND_1"
    )

    radio_el = wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio_el)
    radio_el.click()
    print(f"✅ Lost Passport seçildi: {lost}")
    time.sleep(1.5)

    if lost == "NO":
        return

    nums = [x.strip() for x in data.get("LOST_PPT_NUMBERS", "").split(",") if x.strip()]
    countries = [x.strip() for x in data.get("LOST_PPT_COUNTRIES", "").split(",") if x.strip()]
    explains = [x.strip() for x in data.get("LOST_PPT_EXPLAINS", "").split(",") if x.strip()]

    if not nums:
        return

    base = "ctl00_SiteContentPlaceHolder_FormView1_dtlLostPPT_ctl"

    for i, (num, country, expl) in enumerate(zip(nums, countries, explains)):
        idx = f"{i:02d}"

        num_id    = f"{base}{idx}_tbxLOST_PPT_NUM"
        unk_id    = f"{base}{idx}_cbxLOST_PPT_NUM_UNKN_IND"
        country_id = f"{base}{idx}_ddlLOST_PPT_NATL"
        expl_id   = f"{base}{idx}_tbxLOST_PPT_EXPL"
        add_btn_id = f"{base}{idx}_InsertButtonLostPPT"

        if num.upper() in ("NA", "N/A", "UNKNOWN", ""):
            cb = wait.until(EC.element_to_be_clickable((By.ID, unk_id)))
            if not cb.is_selected():
                cb.click()
        else:
            num_el = wait.until(EC.visibility_of_element_located((By.ID, num_id)))
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
            """, num_el)
            num_el.send_keys(num)

        Select(wait.until(EC.element_to_be_clickable((By.ID, country_id)))).select_by_visible_text(country.upper())

        expl_el = wait.until(EC.visibility_of_element_located((By.ID, expl_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, expl_el)
        expl_el.send_keys(expl)
        print(f"✅ [{i+1}] Kayıt girildi.")

        if i < len(nums) - 1:
            wait.until(EC.element_to_be_clickable((By.ID, add_btn_id))).click()
            print("➕ Yeni satır ekleniyor...")
            next_idx = f"{i+1:02d}"
            wait.until(EC.presence_of_element_located(
                (By.ID, f"{base}{next_idx}_tbxLOST_PPT_NUM")
            ))
            time.sleep(1)

    click_outside(driver)
    print("🟢 Lost Passport bölümü TAMAMLANDI")


def fill_us_point_of_contact(wait, driver, data):
    print("🇺🇸 U.S. Point of Contact başladı")

    def handle_checkbox(cb_id, should_check):
        cb = wait.until(EC.presence_of_element_located((By.ID, cb_id)))
        if cb.is_selected() != should_check:
            driver.execute_script("arguments[0].click();", cb)
            print(f"🔘 Checkbox ({cb_id}) durumu değiştirildi: {should_check}")
            time.sleep(2)

    def safe_js_fill(eid, val):
        if val and str(val).strip():
            el = wait.until(EC.presence_of_element_located((By.ID, eid)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
            """, el)
            el.send_keys(str(val))
            print(f"✍️ {eid} dolduruldu: {val}")

    # 1) POC NAME
    poc_surname = data.get("US_POC_SURNAME", "").strip()
    poc_given   = data.get("US_POC_GIVEN_NAME", "").strip()
    org_name    = data.get("US_POC_ORG_NAME", "").strip()

    final_surname = poc_surname if poc_surname else "UNKNOWN"
    final_given   = poc_given   if poc_given   else "UNKNOWN"
    final_org     = org_name    if org_name    else "HOTEL OR BUSINESS"

    handle_checkbox("ctl00_SiteContentPlaceHolder_FormView1_cbxUS_POC_NAME_NA", False)
    safe_js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_SURNAME", final_surname)
    safe_js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_GIVEN_NAME", final_given)
    print(f"✅ POC isim dolduruldu: {final_surname} {final_given}")

    # 2) ORGANIZATION
    handle_checkbox("ctl00_SiteContentPlaceHolder_FormView1_cbxUS_POC_ORG_NA_IND", False)
    safe_js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ORGANIZATION", final_org)
    print(f"✅ POC organizasyon dolduruldu: {final_org}")

    # 3) RELATIONSHIP
    raw_rel = (data.get("US_POC_RELATION") or "").strip().upper()
    rel_val = US_POC_RELATION_MAP.get(raw_rel, "O")
    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlUS_POC_REL_TO_APP")
    ))).select_by_value(rel_val)

    # 4) ADDRESS — 40 karakter split
    raw_poc_addr = clean_address((data.get("US_POC_ADDR1") or "").strip())
    poc_addr1, poc_addr2_overflow = split_address(raw_poc_addr, max_len=40)
    print(f"📍 POC addr1: '{poc_addr1}' ({len(poc_addr1)} kar)")

    safe_js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_LN1",
        poc_addr1
    )

    # addr2 — önce overflow, yoksa data'dan al
    poc_addr2_data  = clean_address((data.get("US_POC_ADDR2") or "").strip())
    poc_addr2_final = poc_addr2_overflow or poc_addr2_data
    if poc_addr2_final:
        print(f"📍 POC addr2: '{poc_addr2_final}' ({len(poc_addr2_final)} kar)")
        safe_js_fill(
            "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_LN2",
            poc_addr2_final
        )

    safe_js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_CITY",
        (data.get("US_POC_CITY") or "").strip().upper()
    )

    # 5) STATE
    raw_state = data.get("US_POC_STATE", "").strip().upper()
    state_val = raw_state if len(raw_state) == 2 else US_STATE_MAP.get(raw_state)

    if state_val:
        Select(wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlUS_POC_ADDR_STATE")
        ))).select_by_value(state_val)
        print(f"📍 Eyalet seçildi: {state_val}")
        time.sleep(2.5)

    # 6) ZIP & PHONE
    safe_js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_POSTAL_CD",
        data.get("US_POC_ZIP", "").strip()
    )
    safe_js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_HOME_TEL",
        data.get("US_POC_PHONE", "").strip()
    )

    # 7) EMAIL
    email = data.get("US_POC_EMAIL", "").strip()
    is_email_na = email.upper() in ("NA", "N/A", "DOES NOT APPLY", "")

    handle_checkbox(
        "ctl00_SiteContentPlaceHolder_FormView1_cbexUS_POC_EMAIL_ADDR_NA",
        is_email_na
    )

    if not is_email_na:
        safe_js_fill(
            "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_EMAIL_ADDR",
            email
        )

    click_outside(driver)
    print("🟢 U.S. Point of Contact BAŞARIYLA TAMAMLANDI")
def fill_dd_mmm_yyyy(wait, driver, day_id, month_id, year_id, date_str):
    if not date_str or "-" not in date_str:
        print(f"⚠️ Geçersiz tarih: {date_str}")
        return

    parts = date_str.strip().split("-")
    day = parts[0].zfill(2)
    mon = parts[1].upper()
    year = parts[2]

    try:
        Select(wait.until(EC.element_to_be_clickable((By.ID, day_id)))).select_by_value(day)

        mon_el = wait.until(EC.element_to_be_clickable((By.ID, month_id)))
        mon_select = Select(mon_el)
        try:
            mon_select.select_by_value(mon)
        except:
            mon_select.select_by_visible_text(mon)

        year_el = wait.until(EC.presence_of_element_located((By.ID, year_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, year_el)
        driver.execute_script("arguments[0].value = arguments[1];", year_el, year)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", year_el)
        driver.execute_script("arguments[0].dispatchEvent(new Event('blur', {bubbles:true}));", year_el)

        print(f"✅ Tarih girildi: {date_str}")

    except Exception as e:
        print(f"❌ Tarih girilirken hata ({day_id}): {str(e)}")


def fill_parents_info(wait, driver, data):
    print("👨‍👩‍👧‍👦 Parents info başladı...")

    def fill_parent(parent_type):
        if parent_type == "FATHER":
            surname_id   = "ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_SURNAME"
            cb_surname_id = "ctl00_SiteContentPlaceHolder_FormView1_cbxFATHER_SURNAME_UNK_IND"
            given_id     = "ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_GIVEN_NAME"
            cb_given_id  = "ctl00_SiteContentPlaceHolder_FormView1_cbxFATHER_GIVEN_NAME_UNK_IND"
            dob_day_id   = "ctl00_SiteContentPlaceHolder_FormView1_ddlFathersDOBDay"
            dob_month_id = "ctl00_SiteContentPlaceHolder_FormView1_ddlFathersDOBMonth"
            dob_year_id  = "ctl00_SiteContentPlaceHolder_FormView1_tbxFathersDOBYear"
            cb_dob_id    = "ctl00_SiteContentPlaceHolder_FormView1_cbxFATHER_DOB_UNK_IND"
            radio_yes_id = "ctl00_SiteContentPlaceHolder_FormView1_rblFATHER_LIVE_IN_US_IND_0"
            radio_no_id  = "ctl00_SiteContentPlaceHolder_FormView1_rblFATHER_LIVE_IN_US_IND_1"
        else:
            surname_id   = "ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_SURNAME"
            cb_surname_id = "ctl00_SiteContentPlaceHolder_FormView1_cbxMOTHER_SURNAME_UNK_IND"
            given_id     = "ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_GIVEN_NAME"
            cb_given_id  = "ctl00_SiteContentPlaceHolder_FormView1_cbxMOTHER_GIVEN_NAME_UNK_IND"
            dob_day_id   = "ctl00_SiteContentPlaceHolder_FormView1_ddlMothersDOBDay"
            dob_month_id = "ctl00_SiteContentPlaceHolder_FormView1_ddlMothersDOBMonth"
            dob_year_id  = "ctl00_SiteContentPlaceHolder_FormView1_tbxMothersDOBYear"
            cb_dob_id    = "ctl00_SiteContentPlaceHolder_FormView1_cbxMOTHER_DOB_UNK_IND"
            radio_yes_id = "ctl00_SiteContentPlaceHolder_FormView1_rblMOTHER_LIVE_IN_US_IND_0"
            radio_no_id  = "ctl00_SiteContentPlaceHolder_FormView1_rblMOTHER_LIVE_IN_US_IND_1"

        def js_fill(element_id, value):
            el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
            """, el)
            el.send_keys(value)

        # SURNAME
        surname_val = data.get(f"{parent_type}_SURNAME", "").upper().strip()
        cb = wait.until(EC.presence_of_element_located((By.ID, cb_surname_id)))
        if not surname_val or surname_val in ("NA", "UNKNOWN"):
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
        else:
            if cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.3)
            js_fill(surname_id, surname_val)

        # GIVEN NAME
        given_val = data.get(f"{parent_type}_GIVEN", "").upper().strip()
        cb = wait.until(EC.presence_of_element_located((By.ID, cb_given_id)))
        if not given_val or given_val in ("NA", "UNKNOWN"):
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
        else:
            if cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.3)
            js_fill(given_id, given_val)

        # DOB
        dob_val = data.get(f"{parent_type}_DOB", "").strip()
        dob_na  = data.get(f"{parent_type}_DOB_NA", "NO").upper()
        cb = wait.until(EC.presence_of_element_located((By.ID, cb_dob_id)))
        if dob_na == "YES" or not dob_val:
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
        else:
            if cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.3)
            fill_dd_mmm_yyyy(wait, driver, dob_day_id, dob_month_id, dob_year_id, dob_val)
            print(f"📅 {parent_type} tarihi girildi: {dob_val}")

        # IN US
        in_us_val = data.get(f"{parent_type}_IN_US", "NO").upper()
        radio_id  = radio_yes_id if in_us_val == "YES" else radio_no_id
        radio_el  = wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio_el)
        driver.execute_script("arguments[0].click();", radio_el)
        print(f"✅ {parent_type} tamamlandı")

    fill_parent("FATHER")
    time.sleep(0.5)

    wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_SURNAME")
    ))
    time.sleep(0.3)

    fill_parent("MOTHER")

    wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblUS_IMMED_RELATIVE_IND_1")
    ))
    time.sleep(0.5)

    print("🟢 Parents info TAMAMLANDI")


def fill_us_immediate_relatives(wait, driver, data):
    print("👪 Immediate Relatives başladı")

    has_rel = data.get("US_IMMEDIATE_RELATIVE", "NO").upper()

    def safe_click(element_id, retries=5):
        for attempt in range(retries):
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
                driver.execute_script("arguments[0].click();", el)
                return
            except StaleElementReferenceException:
                print(f"⚠️ safe_click stale retry {attempt+1}: {element_id}")
                time.sleep(0.5)
        raise Exception(f"❌ safe_click başarısız: {element_id}")

    def safe_select(element_id, value, retries=5):
        for attempt in range(retries):
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
                Select(el).select_by_value(value)
                return
            except StaleElementReferenceException:
                print(f"⚠️ safe_select stale retry {attempt+1}: {element_id}")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ safe_select hata retry {attempt+1}: {e}")
                time.sleep(0.5)
        raise Exception(f"❌ safe_select başarısız: {element_id}={value}")

    def js_fill(element_id, value):
        if not value:
            return
        for attempt in range(3):
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
                driver.execute_script("""
                    arguments[0].removeAttribute('disabled');
                    arguments[0].removeAttribute('readonly');
                    arguments[0].value = '';
                """, el)
                el.send_keys(str(value))
                return
            except StaleElementReferenceException:
                print(f"⚠️ js_fill stale retry {attempt+1}: {element_id}")
                time.sleep(0.5)

    # Status map — CRM'den gelen uzun değerleri DS-160 value'ya çevir
    US_REL_STATUS_MAP = {
    "CITIZEN":                   "S",
    "US CITIZEN":                "S",
    "U.S. CITIZEN":              "S",
    "LAWFUL PERMANENT RESIDENT": "C",
    "LAWFUL":                    "C",
    "LPR":                       "C",
    "NONIMMIGRANT":              "P",
    "IMMIGRANT":                 "P",
    "OTHER":                     "O",
    "I DON'T KNOW":              "O",
    # Kısa kodlar
    "S": "S",
    "C": "C",
    "P": "P",
    "O": "O",
    "N": "P",  # NONIMMIGRANT → P
    "L": "C",  # LAWFUL → C
}

    # Type map
    US_REL_TYPE_MAP = {
    "SPOUSE":   "S",    # S olabilir SP değil
    "CHILD":    "C",
    "SIBLING":  "B",    # SB değil B
    "BROTHER":  "B",
    "SISTER":   "B",
    "PARENT":   "P",
    "FIANCE":   "F",
    "RELATIVE": "O",
    "OTHER":    "O",
    # Kısa kodlar
    "SP": "S",
    "SB": "B",          # ← SB → B
    "S":  "S",
    "C":  "C",
    "B":  "B",
    "P":  "P",
    "F":  "F",
    "O":  "O",
}

    safe_click(
        "ctl00_SiteContentPlaceHolder_FormView1_rblUS_IMMED_RELATIVE_IND_0"
        if has_rel == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblUS_IMMED_RELATIVE_IND_1"
    )

    if has_rel == "NO":
        print("ℹ️ Immediate Relative yok")
        return

    time.sleep(1.5)

    # ── Veriyi oku ───────────────────────────────────────────
    persons = []

    # Format 1: US_REL_SURNAME (tekil düz key — bu data'da böyle geliyor)
    if data.get("US_REL_SURNAME"):
        status_raw = data.get("US_REL_STATUS", "O").strip().upper()
        type_raw   = data.get("US_REL_TYPE",   "SP").strip().upper()
        persons.append({
            "surname": data.get("US_REL_SURNAME", ""),
            "given":   data.get("US_REL_GIVEN",   ""),
            "type":    US_REL_TYPE_MAP.get(type_raw, "C"),
            "status":  US_REL_STATUS_MAP.get(status_raw, "O"),
        })

    # Format 2: US_REL1_SURNAME (numaralı)
    if not persons:
        i = 1
        while data.get(f"US_REL{i}_SURNAME"):
            status_raw = data.get(f"US_REL{i}_STATUS", "O").strip().upper()
            type_raw   = data.get(f"US_REL{i}_TYPE",  "SP").strip().upper()
            persons.append({
                "surname": data.get(f"US_REL{i}_SURNAME", ""),
                "given":   data.get(f"US_REL{i}_GIVEN",   ""),
                "type":    US_REL_TYPE_MAP.get(type_raw, "C"),
                "status":  US_REL_STATUS_MAP.get(status_raw, "O"),
            })
            i += 1

    # Format 3: US_RELATIVES array
    if not persons:
        import json
        relatives_raw = data.get("US_RELATIVES", [])
        if isinstance(relatives_raw, str):
            try:
                relatives_raw = json.loads(relatives_raw)
            except Exception:
                relatives_raw = []
        for r in relatives_raw:
            status_raw = (r.get("status") or r.get("STATUS") or "O").strip().upper()
            type_raw   = (r.get("type")   or r.get("TYPE")   or "SP").strip().upper()
            persons.append({
                "surname": r.get("surname") or r.get("SURNAME") or "",
                "given":   r.get("given")   or r.get("GIVEN")   or "",
                "type":    US_REL_TYPE_MAP.get(type_raw, "C"),
                "status":  US_REL_STATUS_MAP.get(status_raw, "O"),
            })

    # Hiç veri yoksa fallback
    if not persons:
        print("⚠️ YES seçildi ama relative verisi yok, fallback ile doldurulacak")
        persons = [{
            "surname": "XXXXXXXXXX",
            "given":   "XXXXXXXXXX",
            "type":    "C",
            "status":  "O",
        }]

    print(f"ℹ️ {len(persons)} relative doldurulacak: {persons}")

    # ── Doldur ───────────────────────────────────────────────
    for idx, person in enumerate(persons):
        row = f"ctl{idx:02d}"
        print(f"👤 Relative {idx+1}: {person}")

        if idx > 0:
            safe_click(
                "ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_ctl00_InsertButtonUSRelative"
            )
            time.sleep(1.5)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID,
                        f"ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_{row}_tbxUS_REL_SURNAME"
                    ))
                )
            except Exception:
                print(f"⚠️ Yeni satır timeout, devam ediliyor...")
                time.sleep(1)

        js_fill(
            f"ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_{row}_tbxUS_REL_SURNAME",
            person["surname"]
        )
        js_fill(
            f"ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_{row}_tbxUS_REL_GIVEN_NAME",
            person["given"]
        )
        safe_select(
            f"ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_{row}_ddlUS_REL_TYPE",
            person["type"]
        )
        safe_select(
            f"ctl00_SiteContentPlaceHolder_FormView1_dlUSRelatives_{row}_ddlUS_REL_STATUS",
            person["status"]
        )
        print(f"✅ Relative {idx+1} dolduruldu: {person['given']} {person['surname']}")

    print("✅ Tüm Immediate Relatives dolduruldu")
def fill_us_other_relatives(wait, driver, data):
    # ── 1. US IMMEDIATE RELATIVE ──────────────────────────────
    immed = str(data.get("US_IMMEDIATE_RELATIVE", "NO")).strip().upper()
    if immed not in ("YES", "NO"):
        immed = "NO"

    immed_yes_id = "ctl00_SiteContentPlaceHolder_FormView1_rblUS_IMMED_RELATIVE_IND_0"
    immed_no_id  = "ctl00_SiteContentPlaceHolder_FormView1_rblUS_IMMED_RELATIVE_IND_1"

    try:
        immed_radio = wait.until(EC.element_to_be_clickable(
            (By.ID, immed_yes_id if immed == "YES" else immed_no_id)
        ))
        if not immed_radio.is_selected():
            driver.execute_script("arguments[0].click();", immed_radio)
            time.sleep(1.5)  # postback bekle
        print(f"✅ US Immediate Relative: {immed}")
    except Exception as e:
        print(f"⚠️ US Immediate Relative radio: {e}")

    # ── 2. US OTHER RELATIVE ──────────────────────────────────
    other = str(data.get("US_OTHER_RELATIVE", "NO")).strip().upper()
    if other not in ("YES", "NO"):
        other = "NO"

    other_yes_id = "ctl00_SiteContentPlaceHolder_FormView1_rblUS_OTHER_RELATIVE_IND_0"
    other_no_id  = "ctl00_SiteContentPlaceHolder_FormView1_rblUS_OTHER_RELATIVE_IND_1"

    try:
        wait.until(EC.visibility_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ShowDivOtherRelatives")
        ))
        other_radio = wait.until(EC.element_to_be_clickable(
            (By.ID, other_yes_id if other == "YES" else other_no_id)
        ))
        if not other_radio.is_selected():
            driver.execute_script("arguments[0].click();", other_radio)
            time.sleep(0.5)
        print(f"✅ US Other Relative: {other}")
    except Exception as e:
        print(f"⚠️ US Other Relative radio: {e}")
def auto_fill_family_page(wait, driver, data):
    marital_status = data.get("MARITAL_STATUS", "").upper().strip()

    if marital_status == "MARRIED":
        print("➡️ Mevcut eş sayfası dolduruluyor.")
        fill_spouse_info(wait, driver, data)
    elif marital_status == "DIVORCED":
        print("➡️ Eski eş sayfası dolduruluyor.")
        fill_former_spouse(wait, driver, data)
    elif marital_status == "WIDOWED":
        print("➡️ Vefat etmiş eş sayfası dolduruluyor.")
        fill_widowed_spouse(wait, driver, data)
    elif marital_status in ("SINGLE", ""):
        print("ℹ️ Bekar — eş sayfası yok, atlanıyor.")
        return
    else:
        print(f"⚠️ Bilinmeyen medeni durum: {marital_status} — atlanıyor.")
        return


def fill_former_spouse(wait, driver, data):
    print("💍 Former Spouse başlıyor...")

    def js_fill(element_id, value):
        if not value:
            return
        el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(str(value))

    def safe_select_day(element_id, day_str):
        """Gün değerini farklı formatlarda dener: '05', '5', ' 5'"""
        day_str = str(day_str).strip()
        padded   = day_str.zfill(2)          # "05"
        unpadded = day_str.lstrip("0") or "1" # "5"
        spaced   = f" {unpadded}"             # " 5"
        el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
        for val in [padded, unpadded, spaced]:
            try:
                Select(el).select_by_value(val)
                print(f"✅ Day seçildi: {val} ({element_id})")
                return
            except Exception:
                continue
        raise Exception(f"❌ Day seçilemedi: {day_str} → {element_id}")

    def safe_select_month(element_id, month_val):
        """Ay değerini value ve text olarak dener"""
        el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
        for val in [month_val, str(month_val).lstrip("0") or "1"]:
            try:
                Select(el).select_by_value(val)
                return
            except Exception:
                continue
        try:
            Select(el).select_by_visible_text(str(month_val))
        except Exception as e:
            raise Exception(f"❌ Month seçilemedi: {month_val} → {e}")

    count_el = wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxNumberOfPrevSpouses")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, count_el)
    count_el.send_keys("1")
    count_el.send_keys(Keys.TAB)

    print("⏳ Postback bekleniyor...")
    time.sleep(3)

    prefix = "ctl00_SiteContentPlaceHolder_FormView1_DListSpouse_ctl00_"

    js_fill(prefix + "tbxSURNAME",    data.get("FORMER_SPOUSE_SURNAME"))
    js_fill(prefix + "tbxGIVEN_NAME", data.get("FORMER_SPOUSE_GIVEN"))

    def parse_ds160_date(date_str):
        if not date_str or "-" not in date_str:
            return "01", "JAN", "1900"
        parts = date_str.strip().split("-")
        month_map = {
            "01":"JAN","02":"FEB","03":"MAR","04":"APR",
            "05":"MAY","06":"JUN","07":"JUL","08":"AUG",
            "09":"SEP","10":"OCT","11":"NOV","12":"DEC"
        }
        try:
            if len(parts[0]) == 4:
                year, month, day = parts[0], parts[1], parts[2]
            else:
                day, month, year = parts[0], parts[1], parts[2]
            month = month_map.get(month.upper(), month.upper())
            return day.zfill(2), month, year
        except Exception:
            return "01", "JAN", "1900"

    month_to_number = {
        "JAN":"1","FEB":"2","MAR":"3","APR":"4",
        "MAY":"5","JUN":"6","JUL":"7","AUG":"8",
        "SEP":"9","OCT":"10","NOV":"11","DEC":"12"
    }

    # ── DOB ──────────────────────────────────────────────────
    dob_day, dob_month, dob_year = parse_ds160_date(data.get("FORMER_SPOUSE_DOB"))
    safe_select_day(prefix + "ddlDOBDay", dob_day)
    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, prefix + "ddlDOBMonth")
    ))).select_by_value(dob_month)
    js_fill(prefix + "tbxDOBYear", dob_year)

    # ── NATIONALITY ───────────────────────────────────────────
    nat_dd = Select(wait.until(EC.element_to_be_clickable(
        (By.ID, prefix + "ddlSpouseNatDropDownList")
    )))
    try:
        nat_dd.select_by_value("TRKY")
    except Exception:
        nat_dd.select_by_visible_text("TURKEY")

    # ── POB ───────────────────────────────────────────────────
    js_fill(prefix + "tbxSpousePOBCity", data.get("FORMER_SPOUSE_POB_CITY", "UNKNOWN"))
    try:
        Select(wait.until(EC.element_to_be_clickable(
            (By.ID, prefix + "ddlSpousePOBCountry")
        ))).select_by_value("TRKY")
    except Exception:
        pass

    # ── MARRIAGE DATE ─────────────────────────────────────────
    dom_day, dom_month, dom_year = parse_ds160_date(data.get("FORMER_MARRIAGE_DATE"))
    safe_select_day(prefix + "ddlDomDay", dom_day)
    safe_select_month(prefix + "ddlDomMonth", month_to_number.get(dom_month, "1"))
    js_fill(prefix + "txtDomYear", dom_year)

    # ── END DATE ──────────────────────────────────────────────
    end_day, end_month, end_year = parse_ds160_date(data.get("FORMER_MARRIAGE_END_DATE"))
    safe_select_day(prefix + "ddlDomEndDay", end_day)
    safe_select_month(prefix + "ddlDomEndMonth", month_to_number.get(end_month, "1"))
    js_fill(prefix + "txtDomEndYear", end_year)

    # ── END REASON ────────────────────────────────────────────
    reason_field = wait.until(EC.presence_of_element_located(
        (By.ID, prefix + "tbxHowMarriageEnded")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, reason_field)
    driver.execute_script(
        "arguments[0].value = arguments[1];",
        reason_field,
        data.get("FORMER_MARRIAGE_END_REASON", "DIVORCE").upper()
    )

    try:
        Select(wait.until(EC.element_to_be_clickable(
            (By.ID, prefix + "ddlMarriageEnded_CNTRY")
        ))).select_by_value("TRKY")
    except Exception:
        pass

    print("✅ Former Spouse tamamlandı.")

def fill_spouse_info(wait, driver, data):
    print("💍 Spouse bilgileri kontrol ediliyor...")

    marital_status = str(data.get("MARITAL_STATUS", "")).upper()

    if marital_status == "DIVORCED":
        print("⏭ DIVORCED — atlanıyor.")
        return
    if marital_status == "SINGLE":
        print("⏭ SINGLE — atlanıyor.")
        return
    if marital_status not in ["MARRIED", "MARRIED_DEFACTO"]:
        print(f"⏭ {marital_status} — spouse gerekmiyor.")
        return

    def js_fill(element_id, value):
        if not value:
            return
        el = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(str(value))

    try:
        print("📝 Mevcut eş bilgileri dolduruluyor...")

        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxSpouseSurname", data.get("SPOUSE_SURNAME", "").upper())
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxSpouseGivenName", data.get("SPOUSE_GIVEN_NAME", "").upper())

        raw_dob = str(data.get("SPOUSE_DOB", data.get("SPOUSE_DOB_DAY", "")))
        if "-" in raw_dob:
            parts = raw_dob.split("-")
            final_day, final_mon, final_year = parts[0].zfill(2), parts[1].upper(), parts[2]
        else:
            final_day  = str(data.get("SPOUSE_DOB_DAY", "01")).zfill(2)
            final_mon  = str(data.get("SPOUSE_DOB_MONTH", "JAN")).upper()
            final_year = str(data.get("SPOUSE_DOB_YEAR", "1990"))

        if final_day in ["00", "0", ""]:
            final_day = "01"

        Select(wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlDOBDay")
        ))).select_by_value(final_day)

        mon_dd = Select(wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlDOBMonth")
        )))
        try:
            mon_dd.select_by_value(final_mon)
        except:
            mon_dd.select_by_visible_text(final_mon)

        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxDOBYear", final_year)

        nat_dd = Select(wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlSpouseNatDropDownList")
        )))
        nat_text = data.get("SPOUSE_NATIONALITY", "TURKEY").upper()
        try:
            nat_dd.select_by_visible_text(nat_text)
        except:
            nat_dd.select_by_index(1)

        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxSpousePOBCity",
                data.get("SPOUSE_POB_CITY", "").upper())

        Select(wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlSpousePOBCountry")
        ))).select_by_visible_text(data.get("SPOUSE_POB_COUNTRY", "TURKEY").upper())

        addr_val = str(data.get("SPOUSE_ADDRESS_TYPE", "H")).upper()[0]
        Select(wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlSpouseAddressType")
        ))).select_by_value(addr_val)

        if addr_val == "O":
            time.sleep(2)
            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxSpouseAddrLine1",
                    data.get("SPOUSE_ADDR_LINE1", "").upper())
            js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxSpouseAddrCity",
                    data.get("SPOUSE_ADDR_CITY", "").upper())
            Select(wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlSpouseAddrCountry")
            ))).select_by_visible_text(data.get("SPOUSE_ADDR_COUNTRY", "TURKEY").upper())

        print("✅ Spouse bilgileri tamamlandı.")

    except Exception as e:
        print(f"❌ Spouse hatası: {str(e)}")
        raise e


def fill_widowed_spouse(wait, driver, data):
    print("⚰️ Widowed – Deceased Spouse başlıyor")

    if str(data.get("MARITAL_STATUS", "")).upper() != "WIDOWED":
        print("⏭ Widowed değil, atlandı")
        return

    def js_fill(element_id, value):
        if not value:
            return
        el = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(str(value))

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxSURNAME", data.get("DECEASED_SPOUSE_SURNAME"))
    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxGIVEN_NAME", data.get("DECEASED_SPOUSE_GIVEN"))

    raw_day = str(data.get("DECEASED_SPOUSE_DOB_DAY", "01")).strip()
    day = raw_day.zfill(2) if raw_day not in ["0", "00", ""] else "01"

    Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlDOBDay")
    ))).select_by_value(day)

    mon_val = str(data.get("DECEASED_SPOUSE_DOB_MONTH", "")).upper()
    mon_dd = Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlDOBMonth")
    )))
    try:
        mon_dd.select_by_value(mon_val)
    except:
        mon_dd.select_by_visible_text(mon_val)

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxDOBYear", data.get("DECEASED_SPOUSE_DOB_YEAR"))

    nat_dropdown = Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlSpouseNatDropDownList")
    )))
    nat_text = data.get("DECEASED_SPOUSE_NATIONALITY", "TURKEY")
    try:
        nat_dropdown.select_by_visible_text(nat_text)
    except:
        nat_dropdown.select_by_value(data.get("DECEASED_SPOUSE_NATIONALITY_VALUE", "TU"))

    pob_city = data.get("DECEASED_SPOUSE_POB_CITY")
    if pob_city and str(pob_city).upper() not in ["UNKNOWN", "NA", "N/A"]:
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxSpousePOBCity", pob_city)
    else:
        cb_city_na = wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxSPOUSE_POB_CITY_NA")
        ))
        if not cb_city_na.is_selected():
            driver.execute_script("arguments[0].click();", cb_city_na)
            time.sleep(1)

    pob_country_dd = Select(wait.until(EC.element_to_be_clickable(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlSpousePOBCountry")
    )))
    pob_country_text = data.get("DECEASED_SPOUSE_POB_COUNTRY", "TURKEY")
    try:
        pob_country_dd.select_by_visible_text(pob_country_text)
    except:
        pob_country_dd.select_by_value(data.get("DECEASED_SPOUSE_POB_COUNTRY_VALUE", "TU"))

    print("✅ Widowed – Deceased Spouse tamamlandı")
PRESENT_OCCUPATION_MAP = {
    # HTML value'ları direkt gelirse
    "A":  "A",  "B":  "B",  "CM": "CM", "CS": "CS",
    "C":  "C",  "ED": "ED", "EN": "EN", "G":  "G",
    "H":  "H",  "LP": "LP", "MH": "MH", "M":  "M",
    "NS": "NS", "N":  "N",  "PS": "PS", "RV": "RV",
    "R":  "R",  "RT": "RT", "SS": "SS", "S":  "S",
    "O":  "O",  "AP": "AP",

    # Tam isimler
    "AGRICULTURE":          "A",
    "ARTIST":               "AP",
    "ARTIST/PERFORMER":     "AP",
    "BUSINESS":             "B",
    "COMMUNICATIONS":       "CM",
    "COMPUTER SCIENCE":     "CS",
    "COMPUTER_SCIENCE":     "CS",
    "CULINARY":             "C",
    "CULINARY/FOOD SERVICES": "C",
    "EDUCATION":            "ED",
    "ENGINEERING":          "EN",
    "GOVERNMENT":           "G",
    "HOMEMAKER":            "H",
    "LEGAL":                "LP",
    "LEGAL PROFESSION":     "LP",
    "MEDICAL":              "MH",
    "MEDICAL/HEALTH":       "MH",
    "MILITARY":             "M",
    "NATURAL SCIENCE":      "NS",
    "NATURAL_SCIENCE":      "NS",
    "NOT EMPLOYED":         "N",
    "NOT_EMPLOYED":         "N",
    "PHYSICAL SCIENCE":     "PS",
    "PHYSICAL SCIENCES":    "PS",
    "PHYSICAL_SCIENCE":     "PS",
    "RELIGIOUS":            "RV",
    "RELIGIOUS VOCATION":   "RV",
    "RESEARCH":             "R",
    "RETIRED":              "RT",
    "SOCIAL SCIENCE":       "SS",
    "SOCIAL_SCIENCE":       "SS",
    "STUDENT":              "S",
    "OTHER":                "O",
}
def select_present_occupation(wait, driver, data):
    print("🧑‍💼 Present Occupation seçiliyor")

    occ = data.get("PRESENT_OCCUPATION", "NOT_EMPLOYED").strip().upper()
    if occ not in PRESENT_OCCUPATION_MAP:
        print(f"⚠️ Geçersiz PRESENT_OCCUPATION: {occ}, NOT_EMPLOYED olarak ayarlanıyor")
        occ = "NOT_EMPLOYED"

    ddl_id = "ctl00_SiteContentPlaceHolder_FormView1_ddlPresentOccupation"
    target_value = PRESENT_OCCUPATION_MAP[occ]

    # Dropdown'ı bul ve seç
    ddl = wait.until(EC.element_to_be_clickable((By.ID, ddl_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ddl)
    time.sleep(0.3)

    # Önce JS ile seç (daha güvenilir)
    driver.execute_script("""
        var sel = arguments[0];
        var val = arguments[1];
        sel.value = val;
        sel.dispatchEvent(new Event('change', {bubbles: true}));
    """, ddl, target_value)
    time.sleep(0.5)

    # Selenium ile de seç (double confirm)
    try:
        Select(wait.until(EC.element_to_be_clickable((By.ID, ddl_id)))).select_by_value(target_value)
    except Exception as e:
        print(f"⚠️ Selenium select hatası: {e}")

    # JS postback tetikle
    driver.execute_script(
        "__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$ddlPresentOccupation', '');"
    )

    print(f"✅ Present Occupation seçildi: {occ} → {target_value}")

    occ_needs_employer = occ not in ("NOT_EMPLOYED", "RETIRED", "HOMEMAKER")

    if occ_needs_employer:
        try:
            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located(
                    (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchName")
                )
            )
            print("✅ Employer alanları açıldı")
        except TimeoutException:
            print("⚠️ Employer alanları açılmadı, tekrar deneniyor...")
            driver.execute_script(
                "__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$ddlPresentOccupation', '');"
            )
            time.sleep(3)
            try:
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchName")
                    )
                )
                print("✅ Employer alanları ikinci denemede açıldı")
            except Exception:
                print("⚠️ Employer alanları hâlâ açılmadı, devam ediliyor")
    else:
        time.sleep(2)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    # Seçimin gerçekten yapıldığını doğrula
    try:
        current = Select(driver.find_element(By.ID, ddl_id)).first_selected_option.get_attribute("value")
        if current != target_value:
            print(f"⚠️ Seçim doğrulanamadı ({current} != {target_value}), tekrar deneniyor...")
            Select(wait.until(EC.element_to_be_clickable((By.ID, ddl_id)))).select_by_value(target_value)
            driver.execute_script(
                "__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$ddlPresentOccupation', '');"
            )
            time.sleep(2)
        else:
            print(f"✅ Seçim doğrulandı: {current}")
    except Exception as e:
        print(f"⚠️ Seçim doğrulama hatası: {e}")

def fill_present_occupation_explain(wait, driver, data):
    expl = (data.get("PRESENT_OCCUPATION_EXPLAIN") or "").strip() or "NOT EMPLOYED"

    textarea_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxExplainOtherPresentOccupation"

    try:
        el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, textarea_id))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.5)

        # Gerçek mouse tıklaması simüle et
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)
        actions.move_to_element(el)
        actions.click()
        actions.pause(0.5)
        
        # Karakter karakter yaz — gerçek klavye gibi
        for char in expl:
            actions.send_keys(char)
            actions.pause(0.05)
        
        actions.perform()
        time.sleep(0.5)

        current = (el.get_attribute("value") or "").strip()
        print(f"✍️ Explain girildi: {current}")

    except Exception as e:
        print(f"⚠️ fill_present_occupation_explain hata: {e}")


def fill_employer_or_school_info(wait, driver, data):
    print("🏢 Employer / School bilgileri dolduruluyor")

    from cleaner import translate_school_name

    def js_fill(element_id, value):
        if not value:
            return
        el = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(str(value))

    js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchName",
        translate_school_name(data.get("EMP_SCH_NAME", ""))[:75]
    )

    # ADDR1 — 40 karakter split
    raw_addr = clean_address(data.get("EMP_SCH_ADDR1", ""))
    addr1, addr2_overflow = split_address(raw_addr, max_len=40)
    print(f"📍 EMP addr1: '{addr1}' ({len(addr1)} kar)")
    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchAddr1", addr1)

    # ADDR2 — önce overflow, yoksa data'dan al
    addr2_data  = clean_address(data.get("EMP_SCH_ADDR2", ""))
    addr2_final = addr2_overflow or addr2_data
    if addr2_final:
        print(f"📍 EMP addr2: '{addr2_final}' ({len(addr2_final)} kar)")
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchAddr2", addr2_final)

    js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchCity",
        clean_address(data.get("EMP_SCH_CITY", ""))
    )

    state_val = str(data.get("EMP_SCH_STATE", "")).strip().upper()

    if not state_val or state_val in ("N/A", "NA", "NONE", "DOES NOT APPLY"):
        state_na_cb = wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxWORK_EDUC_ADDR_STATE_NA")
        ))
        if not state_na_cb.is_selected():
            driver.execute_script("arguments[0].click();", state_na_cb)
            time.sleep(1)
        print("ℹ️ State → Does Not Apply")
    else:
        state_na_cb = wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxWORK_EDUC_ADDR_STATE_NA")
        ))
        if state_na_cb.is_selected():
            driver.execute_script("arguments[0].click();", state_na_cb)
            time.sleep(1)
        js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxWORK_EDUC_ADDR_STATE", state_val)
        print(f"✅ State girildi: {state_val}")

    if data.get("EMP_SCH_POSTAL"):
        js_fill(
            "ctl00_SiteContentPlaceHolder_FormView1_tbxWORK_EDUC_ADDR_POSTAL_CD",
            data["EMP_SCH_POSTAL"]
        )
    else:
        wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxWORK_EDUC_ADDR_POSTAL_CD_NA")
        )).click()

    select_country_by_name(
        wait,
        "ctl00_SiteContentPlaceHolder_FormView1_ddlEmpSchCountry",
        data["EMP_SCH_COUNTRY"]
    )

    if data.get("EMP_SCH_PHONE"):
        js_fill(
            "ctl00_SiteContentPlaceHolder_FormView1_tbxWORK_EDUC_TEL",
            data["EMP_SCH_PHONE"]
        )

    fill_date_dd_mmm_yyyy(
        wait, driver,
        "ctl00_SiteContentPlaceHolder_FormView1_ddlEmpDateFromDay",
        "ctl00_SiteContentPlaceHolder_FormView1_ddlEmpDateFromMonth",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpDateFromYear",
        data["EMP_SCH_START_DATE"]
    )

    if data.get("EMP_MONTHLY_SALARY"):
        js_fill(
            "ctl00_SiteContentPlaceHolder_FormView1_tbxCURR_MONTHLY_SALARY",
            data["EMP_MONTHLY_SALARY"]
        )
    else:
        wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_cbxCURR_MONTHLY_SALARY_NA")
        )).click()

    duties = data.get("EMP_DUTIES", "").strip()
    if not duties:
        duties = "XXXXXXXXXX"

    js_fill("ctl00_SiteContentPlaceHolder_FormView1_tbxDescribeDuties", duties)

    click_outside(driver)
    print("✅ Employer / School bilgileri tamamlandı")

def fill_present_occupation_section(wait, driver, data):
    print("🔍 Present Occupation bölümü işleniyor...")

    try:
        select_present_occupation(wait, driver, data)
    except Exception as e:
        print(f"ℹ️ Present Occupation sayfası bulunamadı veya atlandı: {e}")
        return

    occ = data.get("PRESENT_OCCUPATION", "NOT_EMPLOYED").strip().upper()
    if not occ:
        occ = "NOT_EMPLOYED"

    print(f"🧑‍💼 Occupation: {occ}")

    if occ in ("RETIRED", "HOMEMAKER"):
        print(f"ℹ️ {occ} → Ekstra alan yok.")
        return

    # ── NOT_EMPLOYED ──────────────────────────────────────────
    if occ == "NOT_EMPLOYED":
        textarea_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxExplainOtherPresentOccupation"
        expl = (data.get("PRESENT_OCCUPATION_EXPLAIN") or "").strip()
        if not expl:
            expl = "XXXXX"

        try:
            el = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, textarea_id))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(1)

        # Mevcut değeri JS ile temizle
            driver.execute_script("arguments[0].value = '';", el)
            time.sleep(0.3)

            el.click()
            time.sleep(0.3)

            from selenium.webdriver.common.keys import Keys
            el.send_keys(Keys.CONTROL + "a")
            time.sleep(0.1)
            el.send_keys(Keys.DELETE)
            time.sleep(0.1)
            el.send_keys(expl)
            time.sleep(0.5)

            current = (el.get_attribute("value") or "").strip()
            print(f"✍️ NOT_EMPLOYED explain girildi: '{current}'")

        except Exception as e:
            print(f"⚠️ NOT_EMPLOYED explain hatası: {e}")
        return
    # ── OTHER ─────────────────────────────────────────────────
    if occ == "OTHER":
        textarea_id = "ctl00_SiteContentPlaceHolder_FormView1_tbxExplainOtherPresentOccupation"
        expl = (data.get("PRESENT_OCCUPATION_EXPLAIN") or "OTHER OCCUPATION").strip()

        try:
            el = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, textarea_id))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(1)

            el.click()
            time.sleep(0.5)

            from selenium.webdriver.common.keys import Keys
            el.send_keys(Keys.CONTROL + "a")
            time.sleep(0.2)
            el.send_keys(Keys.DELETE)
            time.sleep(0.2)

            el.send_keys(expl)
            time.sleep(0.5)

            current = (el.get_attribute("value") or "").strip()
            print(f"✍️ OTHER explain girildi: '{current}'")

        except Exception as e:
            print(f"⚠️ OTHER explain hatası: {e}")

        # OTHER'da işveren/okul bilgileri de dolduruluyor
        try:
            WebDriverWait(driver, 25).until(
                EC.visibility_of_element_located(
                    (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchName")
                )
            )
            time.sleep(1.0)
            fill_employer_or_school_info(wait, driver, data)
            print("✅ OTHER → İşveren/Okul bilgileri dolduruldu.")
        except Exception as e:
            print(f"⚠️ OTHER → İşveren/Okul bilgileri doldurulamadı: {e}")
        return

    # ── DİĞER TÜM MESLEKLER → işveren/okul bilgileri ─────────
    try:
        WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchName")
            )
        )
        fill_employer_or_school_info(wait, driver, data)
        print("✅ İşveren/Okul bilgileri dolduruldu.")
    except Exception as e:
        print(f"⚠️ İşveren/Okul bilgileri doldurulamadı: {e}")

def fill_previous_employment(wait, driver, data):
    print("🏢 Previous Employment bölümü başladı")

    from cleaner import translate_school_name

    prev = data.get("PREV_EMPLOYED", "NO").strip().upper()
    if prev not in ("YES", "NO"):
        prev = "NO"

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblPreviouslyEmployed_0"
        if prev == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblPreviouslyEmployed_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()
    print(f"✅ Previously Employed: {prev}")

    if prev == "NO":
        time.sleep(1)
        return

    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    time.sleep(1)

    def split(key):
        val = data.get(key, "")
        if isinstance(val, list):
            return [x.strip() for x in val]
        return [x.strip() for x in str(val).split(",")]

    def split_by_count(key, n):
        parts = split(key)
        while len(parts) < n:
            parts.append("")
        return parts

    date_from = split("PREV_EMPLOY_FROM")
    date_to   = split("PREV_EMPLOY_TO")
    count     = len(date_from)

    names       = split_by_count("PREV_EMPLOYER_NAMES", count)
    addr1       = split_by_count("PREV_EMPLOYER_ADDR1", count)
    addr2       = split_by_count("PREV_EMPLOYER_ADDR2", count)
    city        = split_by_count("PREV_EMPLOYER_CITY", count)
    state       = split_by_count("PREV_EMPLOYER_STATE", count)
    postal      = split_by_count("PREV_EMPLOYER_POSTAL", count)
    phone       = split_by_count("PREV_EMPLOYER_PHONE", count)
    title       = split_by_count("PREV_JOB_TITLE", count)
    sup_surname = split_by_count("PREV_SUPERVISOR_SURNAME", count)
    sup_given   = split_by_count("PREV_SUPERVISOR_GIVEN", count)
    duties      = split_by_count("PREV_EMPLOY_DUTIES", count)
    country     = split_by_count("PREV_EMPLOYER_COUNTRY", count)

    base = "ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEmpl_ctl"

    def fid(i, field):
        return f"{base}{i:02d}_{field}"

    def js_fill(element_id, value):
        if not value:
            return
        el = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(str(value))

    for i in range(count):
        print(f"➡️ Employment #{i+1}")

        # Satır hazır mı bekle
        wait.until(lambda d: len(d.find_elements(
            By.XPATH, "//input[contains(@id,'tbEmployerName')]"
        )) > i)

        # İşveren adı — translate_school_name ile çevir
        js_fill(fid(i, "tbEmployerName"), translate_school_name(names[i])[:75])
        js_fill(fid(i, "tbEmployerStreetAddress1"), addr1[i][:40] if addr1[i] else "")

        if addr2[i]:
            js_fill(fid(i, "tbEmployerStreetAddress2"), addr2[i][:40])

        js_fill(fid(i, "tbEmployerCity"), city[i][:20] if city[i] else "")

        # STATE
        state_val = state[i].strip().upper() if i < len(state) else ""
        if state_val and state_val not in ("NA", "N/A", "NONE", ""):
            try:
                cb = driver.find_element(By.ID, fid(i, "cbxPREV_EMPL_ADDR_STATE_NA"))
                if cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
            except Exception:
                pass
            js_fill(fid(i, "tbxPREV_EMPL_ADDR_STATE"), state_val[:20])
            print(f"✅ State [{i+1}]: {state_val}")
        else:
            try:
                cb = wait.until(EC.element_to_be_clickable(
                    (By.ID, fid(i, "cbxPREV_EMPL_ADDR_STATE_NA"))
                ))
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
                print(f"ℹ️ State [{i+1}]: Does Not Apply")
            except Exception as e:
                print(f"⚠️ State NA checkbox: {e}")

        # POSTAL
        postal_val = postal[i].strip() if i < len(postal) else ""
        if postal_val and postal_val.upper() not in ("NA", "N/A", "NONE", ""):
            try:
                cb = driver.find_element(By.ID, fid(i, "cbxPREV_EMPL_ADDR_POSTAL_CD_NA"))
                if cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
            except Exception:
                pass
            js_fill(fid(i, "tbxPREV_EMPL_ADDR_POSTAL_CD"), postal_val[:10])
        else:
            try:
                cb = wait.until(EC.element_to_be_clickable(
                    (By.ID, fid(i, "cbxPREV_EMPL_ADDR_POSTAL_CD_NA"))
                ))
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
                print(f"ℹ️ Postal [{i+1}]: Does Not Apply")
            except Exception as e:
                print(f"⚠️ Postal NA checkbox: {e}")

        # COUNTRY
        country_val = country[i].strip() if i < len(country) else "TURKEY"
        if not country_val:
            country_val = "TURKEY"
        try:
            select_country_by_name(wait, fid(i, "DropDownList2"), country_val)
        except Exception as e:
            print(f"⚠️ Country [{i+1}]: {e}")
            try:
                Select(wait.until(EC.element_to_be_clickable(
                    (By.ID, fid(i, "DropDownList2"))
                ))).select_by_value("TRKY")
            except Exception:
                pass

        js_fill(fid(i, "tbEmployerPhone"), phone[i][:15] if phone[i] else "")
        js_fill(fid(i, "tbJobTitle"), translate_school_name(title[i])[:75] if title[i] else "")

        # SUPERVISOR SURNAME
        sup_s = sup_surname[i].strip() if i < len(sup_surname) else ""
        if sup_s and sup_s.upper() not in ("NA", "N/A", "NONE", "UNKNOWN"):
            try:
                cb = driver.find_element(By.ID, fid(i, "cbxSupervisorSurname_NA"))
                if cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
            except Exception:
                pass
            js_fill(fid(i, "tbSupervisorSurname"), sup_s[:33])
        else:
            try:
                cb = wait.until(EC.element_to_be_clickable(
                    (By.ID, fid(i, "cbxSupervisorSurname_NA"))
                ))
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Supervisor Surname NA: {e}")

        # SUPERVISOR GIVEN
        sup_g = sup_given[i].strip() if i < len(sup_given) else ""
        if sup_g and sup_g.upper() not in ("NA", "N/A", "NONE", "UNKNOWN"):
            try:
                cb = driver.find_element(By.ID, fid(i, "cbxSupervisorGivenName_NA"))
                if cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
            except Exception:
                pass
            js_fill(fid(i, "tbSupervisorGivenName"), sup_g[:33])
        else:
            try:
                cb = wait.until(EC.element_to_be_clickable(
                    (By.ID, fid(i, "cbxSupervisorGivenName_NA"))
                ))
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Supervisor Given NA: {e}")

        # DATES
        fill_date_dd_mmm_yyyy(wait, driver,
            fid(i, "ddlEmpDateFromDay"),
            fid(i, "ddlEmpDateFromMonth"),
            fid(i, "tbxEmpDateFromYear"),
            date_from[i]
        )

        fill_date_dd_mmm_yyyy(wait, driver,
            fid(i, "ddlEmpDateToDay"),
            fid(i, "ddlEmpDateToMonth"),
            fid(i, "tbxEmpDateToYear"),
            date_to[i]
        )

        js_fill(fid(i, "tbDescribeDuties"), duties[i][:4000] if duties[i] else "General duties")

        print(f"✅ Previous Employment {i+1} dolduruldu")

        # Yeni satır ekle — sadece gerekiyorsa
        if i < count - 1:
            # Zaten yeterli satır var mı?
            mevcut = len(driver.find_elements(
                By.XPATH, "//input[contains(@id,'tbEmployerName')]"
            ))
            if mevcut > i + 1:
                print(f"ℹ️ Satır zaten var ({mevcut}), Add Another atlanıyor")
                continue

            insert_buttons = driver.find_elements(
                By.XPATH, "//a[contains(@id,'InsertButtonPrevEmpl')]"
            )

            if not insert_buttons:
                print("⚠️ Insert button yok → devam ediliyor")
                break

            btn = insert_buttons[-1]

            if btn.get_attribute("disabled"):
                print("⚠️ Insert button disabled → daha fazla eklenemiyor")
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", btn)

                wait.until(lambda d: len(d.find_elements(
                    By.XPATH, "//input[contains(@id,'tbEmployerName')]"
                )) > i + 1)

                time.sleep(0.5)
                print("➕ Yeni employment satırı eklendi")

            except Exception as e:
                print(f"⚠️ Insert başarısız: {e} → devam ediliyor")
                break

    click_outside(driver)
    print("🟢 Previous Employment TAMAMLANDI")

def fill_other_education(wait, driver, data):
    print("🎓 Other Education bölümü başladı")

    from cleaner import translate_school_name

    # Eğitim listesini topla
    educations_list = []
    idx = 0
    while True:
        prefix = f"EDU_{idx:02d}_"
        school_name = data.get(f"{prefix}SCHOOL_NAME")
        if not school_name:
            break
        educations_list.append({
            "school_name": school_name,
            "addr1":   data.get(f"{prefix}ADDR1", ""),
            "addr2":   data.get(f"{prefix}ADDR2", ""),
            "city":    data.get(f"{prefix}CITY", ""),
            "state":   data.get(f"{prefix}STATE", ""),
            "postal":  data.get(f"{prefix}POSTAL", ""),
            "country": data.get(f"{prefix}COUNTRY", "TURKEY"),
            "course":  data.get(f"{prefix}COURSE", ""),
            "from":    data.get(f"{prefix}DATE_FROM", ""),
            "to":      data.get(f"{prefix}DATE_TO", ""),
        })
        idx += 1

    has_edu = "YES" if educations_list else "NO"
    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblOtherEduc_0"
        if has_edu == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblOtherEduc_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio_id))).click()

    if has_edu == "NO":
        print("✅ Other Education: NO")
        return

    time.sleep(1.5)

    # En yeniden en eskiye sırala
    educations_list = list(reversed(educations_list))
    print(f"✅ Other Education: YES ({len(educations_list)} okul)")

    base = "ctl00_SiteContentPlaceHolder_FormView1_dtlPrevEduc_ctl"

    def educ_id(i, field):
        return f"{base}{i:02d}_{field}"

    def js_fill(element_id, value):
        if not value:
            return
        el = wait.until(EC.visibility_of_element_located((By.ID, element_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(str(value))

    for i, edu in enumerate(educations_list):
        print(f"➡️ Education #{i+1}: {edu['school_name']}")

        # Satır hazır mı bekle
        wait.until(lambda d: len(d.find_elements(
            By.XPATH, "//input[contains(@id,'tbxSchoolName')]"
        )) > i)

        # Okul adı — translate_school_name ile çevir
        js_fill(educ_id(i, "tbxSchoolName"),
                translate_school_name(edu["school_name"])[:75])

        js_fill(educ_id(i, "tbxSchoolAddr1"), edu["addr1"][:40] if edu["addr1"] else "")

        if edu["addr2"]:
            js_fill(educ_id(i, "tbxSchoolAddr2"), edu["addr2"][:40])

        js_fill(educ_id(i, "tbxSchoolCity"), edu["city"][:20] if edu["city"] else "")

        # STATE
        state_val = edu["state"].strip().upper() if edu["state"] else ""
        if state_val and state_val not in ("NA", "N/A", "NONE", ""):
            try:
                cb = driver.find_element(By.ID, educ_id(i, "cbxEDUC_INST_ADDR_STATE_NA"))
                if cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
            except Exception:
                pass
            js_fill(educ_id(i, "tbxEDUC_INST_ADDR_STATE"), state_val[:20])
        else:
            try:
                cb = wait.until(EC.element_to_be_clickable(
                    (By.ID, educ_id(i, "cbxEDUC_INST_ADDR_STATE_NA"))
                ))
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
                print(f"ℹ️ Education State [{i+1}]: Does Not Apply")
            except Exception as e:
                print(f"⚠️ Education State NA: {e}")

        # POSTAL
        postal_val = edu["postal"].strip() if edu["postal"] else ""
        if postal_val and postal_val.upper() not in ("NA", "N/A", "NONE", ""):
            try:
                cb = driver.find_element(By.ID, educ_id(i, "cbxEDUC_INST_POSTAL_CD_NA"))
                if cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
            except Exception:
                pass
            js_fill(educ_id(i, "tbxEDUC_INST_POSTAL_CD"), postal_val[:10])
        else:
            try:
                cb = wait.until(EC.element_to_be_clickable(
                    (By.ID, educ_id(i, "cbxEDUC_INST_POSTAL_CD_NA"))
                ))
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
                    time.sleep(0.5)
                print(f"ℹ️ Education Postal [{i+1}]: Does Not Apply")
            except Exception as e:
                print(f"⚠️ Education Postal NA: {e}")

        # COUNTRY
        country_val = edu["country"].strip() if edu["country"] else "TURKEY"
        if not country_val:
            country_val = "TURKEY"
        try:
            select_country_by_name(wait, educ_id(i, "ddlSchoolCountry"), country_val)
        except Exception as e:
            print(f"⚠️ Education Country [{i+1}]: {e}")
            try:
                Select(wait.until(EC.element_to_be_clickable(
                    (By.ID, educ_id(i, "ddlSchoolCountry"))
                ))).select_by_value("TRKY")
            except Exception:
                pass

        # COURSE
        js_fill(educ_id(i, "tbxSchoolCourseOfStudy"),
                edu["course"][:66] if edu["course"] else "ACADEMIC")

        # DATES
        fill_date_dd_mmm_yyyy(wait, driver,
            educ_id(i, "ddlSchoolFromDay"),
            educ_id(i, "ddlSchoolFromMonth"),
            educ_id(i, "tbxSchoolFromYear"),
            edu["from"]
        )

        fill_date_dd_mmm_yyyy(wait, driver,
            educ_id(i, "ddlSchoolToDay"),
            educ_id(i, "ddlSchoolToMonth"),
            educ_id(i, "tbxSchoolToYear"),
            edu["to"]
        )

        print(f"✅ Education #{i+1} dolduruldu")

        # Yeni satır ekle — sadece gerekiyorsa
        if i < len(educations_list) - 1:
            # Zaten yeterli satır var mı?
            mevcut = len(driver.find_elements(
                By.XPATH, "//input[contains(@id,'tbxSchoolName')]"
            ))
            if mevcut > i + 1:
                print(f"ℹ️ Eğitim satırı zaten var ({mevcut}), Add Another atlanıyor")
                continue

            insert_buttons = driver.find_elements(
                By.XPATH, "//a[contains(@id,'InsertButtonPrevEduc')]"
            )

            if not insert_buttons:
                print("⚠️ Insert button yok → devam ediliyor")
                break

            btn = insert_buttons[-1]

            if btn.get_attribute("disabled"):
                print("⚠️ Insert button disabled → daha fazla eklenemiyor")
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", btn)

                wait.until(lambda d: len(d.find_elements(
                    By.XPATH, "//input[contains(@id,'tbxSchoolName')]"
                )) > i + 1)

                time.sleep(0.5)
                print("➕ Yeni eğitim satırı eklendi")

            except Exception as e:
                print(f"⚠️ Insert başarısız: {e} → devam ediliyor")
                break

    click_outside(driver)
    print("🟢 Other Education TAMAMLANDI")

def fill_clan_tribe(wait, driver, data):
    val = data.get("CLAN_TRIBE", "NO").upper()

    radio = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_0"
        if val == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio))).click()

    if val == "YES":
        el = wait.until(EC.visibility_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxCLAN_TRIBE_NAME")
        ))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(data["CLAN_TRIBE_NAME"])


def fill_languages(wait, driver, data):
    langs_raw = data.get("LANGUAGES", "TURKISH")
    if isinstance(langs_raw, list):
        langs = [x.strip() for x in langs_raw if x.strip()]
    else:
        langs = [x.strip() for x in str(langs_raw).split(",") if x.strip()]
    if not langs:
        langs = ["TURKISH"]

    base = "ctl00_SiteContentPlaceHolder_FormView1_dtlLANGUAGES_ctl"

    for i, lang in enumerate(langs):
        idx    = f"{i:02d}"
        tbx_id = f"{base}{idx}_tbxLANGUAGE_NAME"
        add_id = f"{base}{idx}_InsertButtonLANGUAGE"

        # Satır hazır mı bekle
        wait.until(lambda d: len(d.find_elements(
            By.XPATH, "//input[contains(@id,'tbxLANGUAGE_NAME')]"
        )) > i)

        el = wait.until(EC.visibility_of_element_located((By.ID, tbx_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(lang)
        print(f"✅ Dil [{i+1}]: {lang}")

        # Yeni satır ekle — sadece gerekiyorsa
        if i < len(langs) - 1:
            # Zaten yeterli satır var mı?
            mevcut = len(driver.find_elements(
                By.XPATH, "//input[contains(@id,'tbxLANGUAGE_NAME')]"
            ))
            if mevcut > i + 1:
                print(f"ℹ️ Dil satırı zaten var ({mevcut}), Add Another atlanıyor")
                continue

            try:
                btn = wait.until(EC.element_to_be_clickable((By.ID, add_id)))
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", btn)

                wait.until(lambda d: len(d.find_elements(
                    By.XPATH, "//input[contains(@id,'tbxLANGUAGE_NAME')]"
                )) > i + 1)

                time.sleep(0.5)
                print("➕ Yeni dil satırı eklendi")
            except Exception as e:
                print(f"⚠️ Dil Insert hatası: {e}")
                break
def fill_countries_visited(wait, driver, data):
    val = data.get("COUNTRIES_VISITED", "").strip()

    has_countries = val and val.upper() not in ("NO", "NONE", "")
    country_list = [x.strip() for x in val.split(",") if x.strip()] if has_countries else []

    # "I HAVE NOT TRAVELLED..." ifadesini filtrele
    SKIP_PHRASES = [
        "I HAVE NOT TRAVELLED",
        "I HAVE NOT TRAVELED",
        "NO TRAVEL",
    ]
    country_list = [
        c for c in country_list
        if not any(phrase in c.upper() for phrase in SKIP_PHRASES)
    ]

    # Filtreledikten sonra gerçek ülke kalmadıysa NO seç
    if not country_list:
        has_countries = False

    if not has_countries:
        try:
            no_radio = wait.until(EC.element_to_be_clickable(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblCOUNTRIES_VISITED_IND_1")
            ))
            driver.execute_script("arguments[0].click();", no_radio)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ NO radio tıklanamadı: {e}")
        print("ℹ️ Ziyaret edilen ülke yok")
        return

    # YES radio kontrolü
    try:
        yes_radio = wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblCOUNTRIES_VISITED_IND_0")
        ))
        if not yes_radio.is_selected():
            driver.execute_script("arguments[0].click();", yes_radio)
            print("✅ YES seçildi")
            time.sleep(2)
        else:
            print("ℹ️ YES zaten seçili, postback tetikleniyor...")
            driver.execute_script(
                "__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$rblCOUNTRIES_VISITED_IND$0','');"
            )
            time.sleep(2)
    except Exception as e:
        print(f"⚠️ YES radio hatası: {e}")

    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    # Dropdown açılana kadar bekle
    ddl_id = "ctl00_SiteContentPlaceHolder_FormView1_dtlCountriesVisited_ctl00_ddlCOUNTRIES_VISITED"
    try:
        wait.until(EC.visibility_of_element_located((By.ID, ddl_id)))
        print("✅ Ülke dropdown'ı açıldı")
    except TimeoutException:
        print("⚠️ Dropdown açılmadı, tekrar postback deneniyor...")
        driver.execute_script(
            "__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$rblCOUNTRIES_VISITED_IND$0','');"
        )
        time.sleep(2)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        try:
            wait.until(EC.visibility_of_element_located((By.ID, ddl_id)))
            print("✅ Dropdown ikinci denemede açıldı")
        except Exception:
            print("❌ Dropdown açılamadı, ülkeler atlanıyor")
            return

    # Ülke map
    COUNTRY_MAP = {
       
     "USA": "UNITED STATES OF AMERICA",
    "UNITED STATES": "UNITED STATES OF AMERICA",
    "UK": "UNITED KINGDOM",
    "ENGLAND": "UNITED KINGDOM",
    "SOUTH KOREA": "KOREA, REPUBLIC OF (SOUTH)",
    "NORTH KOREA": "KOREA, DEMOCRATIC REPUBLIC OF (NORTH)",
    "MACEDONIA": "MACEDONIA, NORTH",
    "NORTH MACEDONIA": "MACEDONIA, NORTH",
    "UAE": "UNITED ARAB EMIRATES",
    "TURKEY": "TURKEY",
    "TÜRKİYE": "TURKEY",
    "VATICAN": "HOLY SEE (VATICAN CITY)",
    "BOSNIA": "BOSNIA-HERZEGOVINA",
    "BOSNIA HERZEGOVINA": "BOSNIA-HERZEGOVINA",
    "CABO VERDE": "CABO VERDE", # HTML'de "CAPE VERDE" değil, "CABO VERDE" geçiyor
    "CONGO DEMOCRATIC": "CONGO, DEMOCRATIC REPUBLIC OF THE",
    "CONGO REPUBLIC": "CONGO, REPUBLIC OF THE",
    "CZECHIA": "CZECH REPUBLIC",
    
    # Geri kalanlar HTML ile birebir örtüşüyor:
    "ALBANIA": "ALBANIA",
    "BELGIUM": "BELGIUM",
    "BULGARIA": "BULGARIA",
    "FRANCE": "FRANCE",
    "GERMANY": "GERMANY",
    "GREECE": "GREECE",
    "HUNGARY": "HUNGARY",
    "ITALY": "ITALY",
    "NETHERLANDS": "NETHERLANDS",
    "SWITZERLAND": "SWITZERLAND",
    "RUSSIA": "RUSSIA",
    "UKRAINE": "UKRAINE",
    "SPAIN": "SPAIN",
    "PORTUGAL": "PORTUGAL",
    "AUSTRIA": "AUSTRIA",
    "POLAND": "POLAND",
    "ROMANIA": "ROMANIA",
    "SERBIA": "SERBIA",
    "CROATIA": "CROATIA",
    "SWEDEN": "SWEDEN",
    "NORWAY": "NORWAY",
    "DENMARK": "DENMARK",
    "FINLAND": "FINLAND",
    "IRELAND": "IRELAND",
    "MALTA": "MALTA",
    "CYPRUS": "CYPRUS",
    "LUXEMBOURG": "LUXEMBOURG",
    "SAUDI ARABIA": "SAUDI ARABIA",
    "JORDAN": "JORDAN",
    "EGYPT": "EGYPT",
    "MOROCCO": "MOROCCO",
    "TUNISIA": "TUNISIA",
    "CHINA": "CHINA",
    "JAPAN": "JAPAN",
    "INDIA": "INDIA",
    "THAILAND": "THAILAND",
    "INDONESIA": "INDONESIA",
    "MALAYSIA": "MALAYSIA",
    "SINGAPORE": "SINGAPORE",
    "CANADA": "CANADA",
    "MEXICO": "MEXICO",
    "BRAZIL": "BRAZIL",
    "ARGENTINA": "ARGENTINA",
    "AUSTRALIA": "AUSTRALIA",
    "NEW ZEALAND": "NEW ZEALAND",
    "GEORGIA": "GEORGIA",
    "ARMENIA": "ARMENIA",
    "AZERBAIJAN": "AZERBAIJAN",
    "BELARUS": "BELARUS",
    "MOLDOVA": "MOLDOVA",
    "KOSOVO": "KOSOVO",
    "MONTENEGRO": "MONTENEGRO"
    }

    seen = set()
    unique_countries = []
    for c in country_list:
        mapped = COUNTRY_MAP.get(c.upper().strip(), c.upper().strip())
        if mapped not in seen:
            seen.add(mapped)
            unique_countries.append(mapped)

    print(f"🌍 Hedef ülkeler ({len(unique_countries)}): {unique_countries}")

    base = "ctl00_SiteContentPlaceHolder_FormView1_dtlCountriesVisited_ctl"

    # ── Sayfadaki mevcut ülkeleri oku ──────────────────────────
    existing_countries = []
    try:
        i = 0
        while True:
            idx = f"{i:02d}"
            try:
                sel_el = driver.find_element(By.ID, f"{base}{idx}_ddlCOUNTRIES_VISITED")
                selected = Select(sel_el).first_selected_option
                text = selected.text.upper().strip()
                val_attr = selected.get_attribute("value")
                if val_attr and val_attr != "":
                    existing_countries.append(text)
                i += 1
            except Exception:
                break
    except Exception:
        pass

    print(f"🔍 Sayfadaki mevcut ülkeler ({len(existing_countries)}): {existing_countries}")

    # Aynıysa atla
    if existing_countries == unique_countries:
        print("✅ Ülkeler zaten doğru, atlanıyor")
        return

    # Fazla satırları sil — sondan başa doğru
    while len(existing_countries) > 1:
        try:
            last_idx = f"{len(existing_countries)-1:02d}"
            driver.execute_script(
                f"__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$dtlCountriesVisited$ctl{last_idx}$DeleteButtonCountriesVisited','');"
            )
            time.sleep(1.5)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            existing_countries.pop()
            print(f"🗑️ Fazla satır silindi, kalan: {len(existing_countries)}")
        except Exception as e:
            print(f"⚠️ Satır silinemedi: {e}")
            break

    # ── Ülkeleri doldur ────────────────────────────────────────
    for i, country in enumerate(unique_countries):
        idx = f"{i:02d}"
        try:
            sel_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, f"{base}{idx}_ddlCOUNTRIES_VISITED"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel_el)
            time.sleep(0.5)

            sel = Select(sel_el)

            # Tam eşleşme
            matched = next((o.text for o in sel.options if o.text.upper().strip() == country), None)

            # Kısmi eşleşme
            if not matched:
                matched = next((o.text for o in sel.options if country in o.text.upper()), None)

            if matched:
                sel.select_by_visible_text(matched)
                driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                    sel_el
                )
                time.sleep(0.3)
                current = Select(sel_el).first_selected_option.text
                print(f"✅ [{i+1}/{len(unique_countries)}] Ülke seçildi: {current}")
            else:
                print(f"⚠️ Ülke bulunamadı, atlanıyor: {country}")
                continue

            # Son ülke değilse Add Another tıkla
            if i < len(unique_countries) - 1:
                try:
                    driver.execute_script(
                        f"__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$dtlCountriesVisited$ctl{idx}$InsertButtonCountriesVisited','');"
                    )
                    time.sleep(1.5)
                    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

                    next_idx = f"{i+1:02d}"
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, f"{base}{next_idx}_ddlCOUNTRIES_VISITED"))
                    )
                    print(f"➕ Yeni satır açıldı: {next_idx}")
                except Exception as e:
                    print(f"⚠️ Add Another hatası: {e}")

        except Exception as e:
            print(f"⚠️ Ülke [{i}] {country} girilemedi: {e}")

    print("✅ Ziyaret edilen ülkeler tamamlandı")

def fill_organizations(wait, driver, data):
    val = data.get("ORGANIZATION", "NO").upper()

    radio = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblORGANIZATION_IND_0"
        if val == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblORGANIZATION_IND_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio))).click()

    if val != "YES":
        return

    orgs = [x.strip() for x in data["ORGANIZATION_NAMES"].split(",")]
    base = "ctl00_SiteContentPlaceHolder_FormView1_dtlORGANIZATIONS_ctl"

    for i, o in enumerate(orgs):
        idx = f"{i:02d}"
        tbx_id = f"{base}{idx}_tbxORGANIZATION_NAME"
        add_id = f"{base}{idx}_InsertButtonORGANIZATION"

        el = wait.until(EC.visibility_of_element_located((By.ID, tbx_id)))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(o)

        if i < len(orgs) - 1:
            wait.until(EC.element_to_be_clickable((By.ID, add_id))).click()
            time.sleep(0.8)


def fill_specialized_skills(wait, driver, data):
    val = data.get("SPECIALIZED_SKILLS", "NO").upper()

    radio = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblSPECIALIZED_SKILLS_IND_0"
        if val == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblSPECIALIZED_SKILLS_IND_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio))).click()

    if val == "YES":
        el = wait.until(EC.visibility_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxSPECIALIZED_SKILLS_EXPL")
        ))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].removeAttribute('readonly');
            arguments[0].value = '';
        """, el)
        el.send_keys(data["SPECIALIZED_SKILLS_EXPL"])

def fill_military_service(wait, driver, data):
    val = data.get("MILITARY_SERVICE", "NO").upper()

    radio = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblMILITARY_SERVICE_IND_0"
        if val == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblMILITARY_SERVICE_IND_1"
    )
    wait.until(EC.element_to_be_clickable((By.ID, radio))).click()
    print(f"✅ Military Service radio: {val}")
    time.sleep(1)

    if val != "YES":
        return

    mil_country   = data.get("MIL_COUNTRY",   "TURKEY")
    mil_branch    = data.get("MIL_BRANCH",    "COMPULSORY MILITARY SERVICE")
    mil_rank      = data.get("MIL_RANK",      "INFANTRY")
    mil_specialty = data.get("MIL_SPECIALTY", "COMPULSORY MILITARY SERVICE")
    mil_from      = data.get("MIL_FROM",      "")
    mil_to        = data.get("MIL_TO",        "")

    print(f"DEBUG mil_country={mil_country}")
    print(f"DEBUG mil_branch={mil_branch}")
    print(f"DEBUG mil_rank={mil_rank}")
    print(f"DEBUG mil_specialty={mil_specialty}")
    print(f"DEBUG mil_from={mil_from}")
    print(f"DEBUG mil_to={mil_to}")

    # Ülke value map
    country_value_map = {
        "TURKEY": "TRKY",
        "UNITED STATES": "USA",
        "UNITED STATES OF AMERICA": "USA",
        "GERMANY": "GER",
        "FRANCE": "FRAN",
        "UNITED KINGDOM": "GRBR",
        "RUSSIA": "RUS",
        "CHINA": "CHIN",
        "IRAN": "IRAN",
        "IRAQ": "IRAQ",
        "SYRIA": "SYR",
        "AZERBAIJAN": "AZR",
        "GEORGIA": "GEO",
        "ARMENIA": "ARM",
        "UKRAINE": "UKR",
    }
    country_val = country_value_map.get(mil_country.upper(), "TRKY")

    # Ülke seç
    print(f"DEBUG: Ülke seçiliyor... value={country_val}")
    try:
        Select(wait.until(EC.element_to_be_clickable((
            By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_CNTRY"
        )))).select_by_value(country_val)
        print(f"✅ MIL_COUNTRY seçildi: {mil_country}")
    except Exception as e:
        print(f"⚠️ MIL_COUNTRY seçilemedi: {e}")

    # Postback bekle
    print("DEBUG: Postback bekleniyor (2s)...")
    time.sleep(2)
    print("DEBUG: Postback beklendi")

    def js_fill(element_id, value):
        if not value:
            print(f"DEBUG js_fill: value boş, atlanıyor → {element_id}")
            return
        print(f"DEBUG js_fill: element aranıyor → {element_id}")
        try:
            el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
            print(f"DEBUG js_fill: element bulundu, value yazılıyor → {value}")
            driver.execute_script("""
                var el = arguments[0];
                el.removeAttribute('disabled');
                el.removeAttribute('readonly');
                el.value = arguments[1];
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.dispatchEvent(new Event('input', {bubbles: true}));
            """, el, str(value))
            print(f"✅ js_fill tamamlandı → {element_id} = {value}")
        except Exception as e:
            print(f"⚠️ js_fill hata → {element_id}: {e}")

    # Branch
    print("DEBUG: Branch dolduruluyor...")
    js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_BRANCH",
        mil_branch
    )
    time.sleep(0.3)

    # Rank
    print("DEBUG: Rank dolduruluyor...")
    js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_RANK",
        mil_rank
    )
    time.sleep(0.3)

    # Specialty
    print("DEBUG: Specialty dolduruluyor...")
    js_fill(
        "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_SPECIALTY",
        mil_specialty
    )
    time.sleep(0.3)

    # From tarihi
    print(f"DEBUG: MIL_FROM dolduruluyor... ({mil_from})")
    if mil_from:
        try:
            fill_date_dd_mmm_yyyy(wait, driver,
                "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_FROMDay",
                "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_FROMMonth",
                "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_FROMYear",
                mil_from
            )
            print(f"✅ MIL_FROM: {mil_from}")
        except Exception as e:
            print(f"⚠️ MIL_FROM doldurulamadı: {e}")
    else:
        print("ℹ️ MIL_FROM boş, atlanıyor")

    # To tarihi
    print(f"DEBUG: MIL_TO dolduruluyor... ({mil_to})")
    if mil_to:
        try:
            fill_date_dd_mmm_yyyy(wait, driver,
                "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_TODay",
                "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_TOMonth",
                "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_TOYear",
                mil_to
            )
            print(f"✅ MIL_TO: {mil_to}")
        except Exception as e:
            print(f"⚠️ MIL_TO doldurulamadı: {e}")
    else:
        print("ℹ️ MIL_TO boş, atlanıyor")

    print("✅ Military Service dolduruldu")

def fill_insurgent_organization(wait, driver, data):
    print("🟥 Insurgent / Paramilitary Organization bölümü")

    val = data.get("INSURGENT_ORG", "NO").strip().upper()
    if val not in ("YES", "NO"):
        raise Exception("❌ INSURGENT_ORG YES veya NO olmalı")

    radio_id = (
        "ctl00_SiteContentPlaceHolder_FormView1_rblINSURGENT_ORG_IND_0"
        if val == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblINSURGENT_ORG_IND_1"
    )
    radio = wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
    radio.click()
    print(f"✅ Insurgent Organization: {val}")

    if val == "NO":
        time.sleep(0.5)
        return

    expl = data.get("INSURGENT_ORG_EXPL", "").strip()
    if not expl:
        raise Exception("❌ INSURGENT_ORG=YES ise INSURGENT_ORG_EXPL zorunlu")

    el = wait.until(EC.visibility_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxINSURGENT_ORG_EXPL")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, el)
    el.send_keys(expl)
    print("✍️ Insurgent Organization açıklaması girildi")


def fill_additional_work_education_section(wait, driver, data):
    fill_clan_tribe(wait, driver, data)
    fill_languages(wait, driver, data)
    fill_countries_visited(wait, driver, data)
    fill_organizations(wait, driver, data)
    fill_specialized_skills(wait, driver, data)
    fill_military_service(wait, driver, data)
    fill_insurgent_organization(wait, driver, data)
    print("🟢 Additional Work/Education section TAMAMLANDI")


def normalize_yes_no(value, default="NO"):
    v = (value or "").strip().upper()
    if v in ("YES", "Y", "EVET", "TRUE", "1"):
        return "YES"
    if v in ("NO", "N", "HAYIR", "FALSE", "0"):
        return "NO"
    return default


def fill_communicable_disease(wait, driver, data):
    print("🩺 Communicable Disease")

    val = normalize_yes_no(data.get("COMM_DISEASE", "NO"))

    yes_id = "ctl00_SiteContentPlaceHolder_FormView1_rblDisease_0"
    no_id  = "ctl00_SiteContentPlaceHolder_FormView1_rblDisease_1"

    radio = wait.until(EC.presence_of_element_located(
        (By.ID, yes_id if val == "YES" else no_id)
    ))
    driver.execute_script("""
        arguments[0].checked = true;
        arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
        arguments[0].dispatchEvent(new Event('click', {bubbles:true}));
    """, radio)
    print(f"✅ Communicable Disease: {val}")

    if val == "NO":
        return

    expl = data.get("COMM_DISEASE_EXPL", "").strip()
    if not expl:
        raise Exception("❌ COMM_DISEASE_EXPL zorunlu")

    box = wait.until(EC.visibility_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxDisease")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, box)
    box.send_keys(expl)


def fill_disorder(wait, driver, data):
    print("🧠 Mental / Physical Disorder")

    val = normalize_yes_no(data.get("DISORDER", "NO"))

    yes_id = "ctl00_SiteContentPlaceHolder_FormView1_rblDisorder_0"
    no_id  = "ctl00_SiteContentPlaceHolder_FormView1_rblDisorder_1"

    radio = wait.until(EC.presence_of_element_located(
        (By.ID, yes_id if val == "YES" else no_id)
    ))
    driver.execute_script("""
        arguments[0].scrollIntoView({block:'center'});
        arguments[0].checked = true;
        arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
        arguments[0].dispatchEvent(new Event('click', {bubbles:true}));
    """, radio)
    print(f"✅ Disorder: {val}")

    if val == "NO":
        return

    expl = data.get("DISORDER_EXPL", "").strip()
    if not expl:
        raise Exception("❌ DISORDER_EXPL zorunlu (YES seçildi)")

    textarea = wait.until(EC.visibility_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxDisorder")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, textarea)
    textarea.send_keys(expl)
    print("✍️ Disorder açıklaması girildi")

def fill_drug_abuse(wait, driver, data):
    print("💊 Drug Abuse / Addiction")

    val = normalize_yes_no(data.get("DRUG_ABUSE", "NO"))

    radio = wait.until(EC.presence_of_element_located((By.ID,
        "ctl00_SiteContentPlaceHolder_FormView1_rblDruguser_0"
        if val == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblDruguser_1"
    )))
    driver.execute_script("""
        arguments[0].scrollIntoView({block:'center'});
        arguments[0].checked = true;
        arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
        arguments[0].dispatchEvent(new Event('click', {bubbles:true}));
    """, radio)
    print(f"✅ Drug Abuse: {val}")

    if val == "NO":
        return

    expl = data.get("DRUG_ABUSE_EXPL", "").strip()
    if not expl:
        raise Exception("❌ DRUG_ABUSE_EXPL zorunlu (YES seçildi)")

    textarea = wait.until(EC.visibility_of_element_located(
        (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxDruguser")
    ))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, textarea)
    textarea.send_keys(expl)
    print("✍️ Drug Abuse açıklaması girildi")


def fill_health_security_section(wait, driver, data):
    print("🟥 Health / Medical Security Section")
    fill_communicable_disease(wait, driver, data)
    fill_disorder(wait, driver, data)
    fill_drug_abuse(wait, driver, data)
    print("🟢 Health / Medical Section TAMAMLANDI")


def fill_yes_no_with_expl(wait, driver, data, key, radio_yes_id, radio_no_id, expl_id, expl_key):
    val = data.get(key, "NO").strip().upper()

    if val not in ("YES", "NO"):
        raise Exception(f"❌ {key} YES veya NO olmalı")

    radio = wait.until(EC.element_to_be_clickable(
        (By.ID, radio_yes_id if val == "YES" else radio_no_id)
    ))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
    radio.click()
    print(f"✅ {key}: {val}")

    if val == "NO":
        return

    expl = data.get(expl_key, "").strip()
    if not expl:
        raise Exception(f"❌ {expl_key} zorunlu")

    textarea = wait.until(EC.visibility_of_element_located((By.ID, expl_id)))
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, textarea)
    textarea.send_keys(expl)
    print(f"✍️ {expl_key} girildi")

def fill_controlled_substances(wait, driver, data):
    fill_yes_no_with_expl(
        wait, driver, data,
        key="CONTROLLED_SUBSTANCES",
        radio_yes_id="ctl00_SiteContentPlaceHolder_FormView1_rblControlledSubstances_0",
        radio_no_id="ctl00_SiteContentPlaceHolder_FormView1_rblControlledSubstances_1",
        expl_id="ctl00_SiteContentPlaceHolder_FormView1_tbxControlledSubstances",
        expl_key="CONTROLLED_SUBSTANCES_EXPL"
    )

def fill_prostitution(wait, driver, data):
    fill_yes_no_with_expl(
        wait, driver, data,
        key="PROSTITUTION",
        radio_yes_id="ctl00_SiteContentPlaceHolder_FormView1_rblProstitution_0",
        radio_no_id="ctl00_SiteContentPlaceHolder_FormView1_rblProstitution_1",
        expl_id="ctl00_SiteContentPlaceHolder_FormView1_tbxProstitution",
        expl_key="PROSTITUTION_EXPL"
    )

def fill_human_trafficking(wait, driver, data):
    fill_yes_no_with_expl(
        wait, driver, data,
        key="HUMAN_TRAFFICKING",
        radio_yes_id="ctl00_SiteContentPlaceHolder_FormView1_rblHumanTrafficking_0",
        radio_no_id="ctl00_SiteContentPlaceHolder_FormView1_rblHumanTrafficking_1",
        expl_id="ctl00_SiteContentPlaceHolder_FormView1_tbxHumanTrafficking",
        expl_key="HUMAN_TRAFFICKING_EXPL"
    )

def fill_assisted_severe_trafficking(wait, driver, data):
    fill_yes_no_with_expl(
        wait, driver, data,
        key="ASSISTED_SEVERE_TRAFFICKING",
        radio_yes_id="ctl00_SiteContentPlaceHolder_FormView1_rblAssistedSevereTrafficking_0",
        radio_no_id="ctl00_SiteContentPlaceHolder_FormView1_rblAssistedSevereTrafficking_1",
        expl_id="ctl00_SiteContentPlaceHolder_FormView1_tbxAssistedSevereTrafficking",
        expl_key="ASSISTED_SEVERE_TRAFFICKING_EXPL"
    )

def fill_human_trafficking_related(wait, driver, data):
    fill_yes_no_with_expl(
        wait, driver, data,
        key="HUMAN_TRAFFICKING_RELATED",
        radio_yes_id="ctl00_SiteContentPlaceHolder_FormView1_rblHumanTraffickingRelated_0",
        radio_no_id="ctl00_SiteContentPlaceHolder_FormView1_rblHumanTraffickingRelated_1",
        expl_id="ctl00_SiteContentPlaceHolder_FormView1_tbxHumanTraffickingRelated",
        expl_key="HUMAN_TRAFFICKING_RELATED_EXPL"
    )

def fill_arrested(wait, driver, data):
    fill_yes_no_with_expl(
        wait, driver, data,
        key="ARRESTED",
        radio_yes_id="ctl00_SiteContentPlaceHolder_FormView1_rblArrested_0",
        radio_no_id="ctl00_SiteContentPlaceHolder_FormView1_rblArrested_1",
        expl_id="ctl00_SiteContentPlaceHolder_FormView1_tbxArrested",
        expl_key="ARRESTED_EXPL"
    )

def fill_money_laundering(wait, driver, data):
    fill_yes_no_with_expl(
        wait, driver, data,
        key="MONEY_LAUNDERING",
        radio_yes_id="ctl00_SiteContentPlaceHolder_FormView1_rblMoneyLaundering_0",
        radio_no_id="ctl00_SiteContentPlaceHolder_FormView1_rblMoneyLaundering_1",
        expl_id="ctl00_SiteContentPlaceHolder_FormView1_tbxMoneyLaundering",
        expl_key="MONEY_LAUNDERING_EXPL"
    )

def fill_criminal_security_section(wait, driver, data):
    print("🟥 Criminal / Security Section START")
    fill_arrested(wait, driver, data)
    fill_controlled_substances(wait, driver, data)
    fill_prostitution(wait, driver, data)
    fill_money_laundering(wait, driver, data)
    fill_human_trafficking(wait, driver, data)
    fill_assisted_severe_trafficking(wait, driver, data)
    fill_human_trafficking_related(wait, driver, data)
    print("🟢 Criminal / Security Section TAMAMLANDI")


def _click_radio(wait, driver, radio_id: str):
    try:
        radio = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, radio_id))
        )
    except:
        raise Exception(f"ELEMENT_NOT_FOUND: {radio_id}")
    label_list = driver.find_elements(By.XPATH, f"//label[@for='{radio_id}']")
    if label_list:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", label_list[0])
        driver.execute_script("arguments[0].click();", label_list[0])
    else:
        driver.execute_script("arguments[0].click();", radio)
    WebDriverWait(driver, 3).until(lambda d: d.find_element(By.ID, radio_id).is_selected())
    
def _fill_textarea(wait, driver, textarea_id: str, text: str):
    ta = wait.until(EC.visibility_of_element_located((By.ID, textarea_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ta)
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, ta)
    ta.send_keys(text)


def fill_yesno_with_expl(wait, driver, data, key: str, yes_radio_id: str, no_radio_id: str, textarea_id: str, label: str = ""):
    print(f"🧩 {label or key}")

    val = (data.get(key) or "NO").strip().upper()

    if val not in ("YES", "NO"):
        raise Exception(f"❌ {key} YES veya NO olmalı (gelen: {repr(val)})")

    if val == "YES":
        _click_radio(wait, driver, yes_radio_id)
    else:
        _click_radio(wait, driver, no_radio_id)

    print(f"✅ {label or key}: {val}")

    if val == "NO":
        return

    expl_key = f"{key}_EXPL"
    expl = (data.get(expl_key) or "").strip()

    if not expl:
        raise Exception(f"❌ {expl_key} zorunlu ({key}=YES)")

    _fill_textarea(wait, driver, textarea_id, expl)
    print(f"✍️ {label or key} açıklaması girildi")
# 1) Illegal Activity
def fill_illegal_activity(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="ILLEGAL_ACTIVITY",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblIllegalActivity_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblIllegalActivity_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxIllegalActivity",
        label="Illegal Activity"
    )


# 2) Terrorist Activity
def fill_terrorist_activity(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="TERRORIST_ACTIVITY",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTerroristActivity_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTerroristActivity_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxTerroristActivity",
        label="Terrorist Activity"
    )


# 3) Terrorist Support
def fill_terrorist_support(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="TERRORIST_SUPPORT",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTerroristSupport_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTerroristSupport_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxTerroristSupport",
        label="Terrorist Support"
    )


# 4) Terrorist Organization Member/Rep
def fill_terrorist_org(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="TERRORIST_ORG",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTerroristOrg_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTerroristOrg_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxTerroristOrg",
        label="Terrorist Organization"
    )


# 5) Terrorist Relative
def fill_terrorist_relative(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="TERRORIST_REL",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTerroristRel_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTerroristRel_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxTerroristRel",
        label="Terrorist Relative"
    )


# 6) Genocide
def fill_genocide(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="GENOCIDE",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblGenocide_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblGenocide_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxGenocide",
        label="Genocide"
    )


# 7) Torture
def fill_torture(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="TORTURE",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTorture_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTorture_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxTorture",
        label="Torture"
    )


# 8) Extrajudicial / Political violence
def fill_ex_violence(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="EX_VIOLENCE",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblExViolence_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblExViolence_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxExViolence",
        label="Extrajudicial/Political Violence"
    )


# 9) Child Soldier
def fill_child_soldier(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="CHILD_SOLDIER",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblChildSoldier_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblChildSoldier_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxChildSoldier",
        label="Child Soldier"
    )


# 10) Religious Freedom violations
def fill_religious_freedom(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="RELIGIOUS_FREEDOM",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblReligiousFreedom_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblReligiousFreedom_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxReligiousFreedom",
        label="Religious Freedom"
    )


# 11) Population Controls (forced abortion/sterilization)
def fill_population_controls(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="POPULATION_CONTROLS",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblPopulationControls_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblPopulationControls_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxPopulationControls",
        label="Population Controls"
    )


# 12) Transplant coercion
def fill_transplant(wait, driver, data):
    return fill_yesno_with_expl(
        wait, driver, data,
        key="TRANSPLANT",
        yes_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTransplant_0",
        no_radio_id="ctl00_SiteContentPlaceHolder_FormView1_rblTransplant_1",
        textarea_id="ctl00_SiteContentPlaceHolder_FormView1_tbxTransplant",
        label="Coercive Transplant"
    )


def fill_security_violations_section(wait, driver, data):
    print("🟥 Security / Violations Section")

    fill_illegal_activity(wait, driver, data)
    fill_terrorist_activity(wait, driver, data)
    fill_terrorist_support(wait, driver, data)
    fill_terrorist_org(wait, driver, data)
    fill_terrorist_relative(wait, driver, data)

    fill_genocide(wait, driver, data)
    fill_torture(wait, driver, data)
    fill_ex_violence(wait, driver, data)
    fill_child_soldier(wait, driver, data)

    fill_religious_freedom(wait, driver, data)
    fill_population_controls(wait, driver, data)
    fill_transplant(wait, driver, data)

    print("🟢 Security / Violations Section TAMAMLANDI")



def fill_removal_immigration_section(wait, driver, data):
    print("🚨 REMOVAL & IMMIGRATION SECTION")
    time.sleep(1.5)

    try:
        script = """
        var noButtons = document.querySelectorAll("input[type='radio'][value='N']");
        noButtons.forEach(function(btn) { btn.click(); });
        return noButtons.length;
        """
        count = driver.execute_script(script)
        print(f"✅ JavaScript ile {count} adet 'NO' butonu işaretlendi.")
    except Exception as e:
        print(f"⚠️ Toplu işaretleme hatası: {str(e)}")

    target_ids = [
        "ctl00_SiteContentPlaceHolder_FormView1_rblRemovalHearing_1",
        "ctl00_SiteContentPlaceHolder_FormView1_rblImmigrationFraud_1",
        "ctl00_SiteContentPlaceHolder_FormView1_rblFailToAttend_1",
        "ctl00_SiteContentPlaceHolder_FormView1_rblVisaViolation_1",
        "ctl00_SiteContentPlaceHolder_FormView1_rblDeport_1"
    ]

    for element_id in target_ids:
        try:
            radio = driver.find_element(By.ID, element_id)
            if not radio.is_selected():
                driver.execute_script("arguments[0].click();", radio)
                print(f"✅ Tekil kontrolle işaretlendi: {element_id}")
        except:
            continue

    time.sleep(1)
    print("✅ REMOVAL & IMMIGRATION SECTION TAMAMLANDI")


def fill_misc_immigration_violations_section(wait, driver, data):
    print("📌 MISC IMMIGRATION / LEGAL VIOLATIONS SECTION")

    no_ids = [
        "ctl00_SiteContentPlaceHolder_FormView1_rblChildCustody_1",
        "ctl00_SiteContentPlaceHolder_FormView1_rblVotingViolation_1",
        "ctl00_SiteContentPlaceHolder_FormView1_rblRenounceExp_1",
    ]

    for element_id in no_ids:
        wait.until(EC.element_to_be_clickable((By.ID, element_id))).click()
        time.sleep(0.2)

    # Public school reimbursement sorusu (varsa)
    try:
        att_wo_reimb = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID,
                "ctl00_SiteContentPlaceHolder_FormView1_rblAttWoReimb_1"
            ))
        )
        att_wo_reimb.click()
        print("✅ Att Without Reimbursement: NO")
        time.sleep(1)
    except Exception:
        print("ℹ️ AttWoReimb sorusu yok, atlanıyor")

    print("✅ MISC IMMIGRATION / LEGAL VIOLATIONS SECTION TAMAMLANDI")

def _fill_input(wait, driver, el_id, value):
    if not value:
        return
    el = wait.until(EC.visibility_of_element_located((By.ID, el_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("""
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].value = '';
    """, el)
    el.send_keys(str(value))


def _set_na_checkbox_if_empty(wait, driver, checkbox_id, value):
    if value.strip():
        return
    cb = wait.until(EC.element_to_be_clickable((By.ID, checkbox_id)))
    if not cb.is_selected():
        driver.execute_script("arguments[0].click();", cb)


def _select_country(wait, driver, select_id, country_code):
    sel = Select(wait.until(EC.element_to_be_clickable((By.ID, select_id))))
    sel.select_by_value(country_code)


def is_student_program(data):
    purpose = data.get("PURPOSE_OF_TRIP", "")
    if not purpose:
        return False
    purpose = purpose.upper()
    return any(key in purpose for key in ("STUDENT", "EXCHANGE", "F-", "M-", "J-", "F ", "M ", "J "))


def _select_country_fixed(wait, driver, element_id, country_name):
    try:
        el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
        sel = Select(el)
        try:
            sel.select_by_visible_text(country_name.upper())
        except:
            sel.select_by_value(country_name.upper())
    except Exception as e:
        print(f"⚠️ Ülke seçimi başarısız: {country_name} -> {e}")


def _click_na_if_needed(driver, checkbox_id):
    try:
        checkbox = driver.find_element(By.ID, checkbox_id)
        if not checkbox.is_selected():
            print(f"🔘 '{checkbox_id}' işaretleniyor...")
            driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(2.5)
    except Exception as e:
        print(f"⚠️ Checkbox işleminde hata: {checkbox_id}")


def fill_student_poc_sections(wait, driver, data):
    print("🎓 Student Additional POC sayfası dolduruluyor...")

    for i in range(1, 3):
        idx = f"0{i-1}"
        base = f"ctl00_SiteContentPlaceHolder_FormView1_dtlStudentAddPOC_ctl{idx}_"
        print(f"👤 POC {i} bilgileri dolduruluyor...")

        _fill_input(wait, driver, base + "tbxADD_POC_SURNAME",    data.get(f"VISAEDUSURNAME{i}"))
        _fill_input(wait, driver, base + "tbxADD_POC_GIVEN_NAME", data.get(f"VISAEDUGIVEN{i}"))
        _fill_input(wait, driver, base + "tbxADD_POC_ADDR_LN1",   data.get(f"VISAEDADDRESS{i}"))
        _fill_input(wait, driver, base + "tbxADD_POC_ADDR_CITY",  data.get(f"VISAEDUCITY{i}"))

        state_val = data.get(f"VISAEDUSTATE{i}", "").strip()
        if state_val and state_val.upper() not in ["N/A", "NONE", "DOES NOT APPLY"]:
            _fill_input(wait, driver, base + "tbxADD_POC_ADDR_STATE", state_val)
        else:
            _click_na_if_needed(driver, base + "cbxADD_POC_ADDR_STATE_NA")

        zip_val = data.get(f"VISAEDUPOSTCODE{i}", "").strip()
        if zip_val and zip_val.upper() not in ["N/A", "NONE"]:
            _fill_input(wait, driver, base + "tbxADD_POC_ADDR_POSTAL_CD", zip_val)
        else:
            _click_na_if_needed(driver, base + "cbxADD_POC_ADDR_POSTAL_CD_NA")

        country_val = data.get(f"VISAEDUCOUNTRY{i}", "TURKEY").upper()
        _select_country_fixed(wait, driver, base + "ddlADD_POC_ADDR_CTRY", country_val)

        tel_val = data.get(f"VISAEDUPHONE{i}", "").strip()
        if tel_val and tel_val.upper() not in ["N/A", "NONE"]:
            _fill_input(wait, driver, base + "tbxADD_POC_TEL", tel_val)
        else:
            _click_na_if_needed(driver, base + "cbxADD_POC_TEL_NA")

        mail_val = data.get(f"VISAEDUMAIL{i}", "").strip()
        if mail_val and mail_val.upper() not in ["N/A", "NONE"]:
            _fill_input(wait, driver, base + "tbxADD_POC_EMAIL_ADDR", mail_val)
        else:
            _click_na_if_needed(driver, base + "cbxADD_POC_EMAIL_ADDR_NA")

    print("✅ POC alanları tamamlandı.")
# --- YARDIMCI FONKSİYONLAR ---

def _select_country_fixed(wait, driver, element_id, country_name):
    """Ülkeyi hem isme hem koda göre deneyerek seçer."""
    try:
        el = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
        sel = Select(el)
        try:
            # Önce görünen metne göre dene (Örn: BAHAMAS)
            sel.select_by_visible_text(country_name.upper())
        except:
            # Metin bulunamazsa değere göre dene (Örn: BAMA)
            sel.select_by_value(country_name.upper())
    except Exception as e:
        print(f"⚠️ Ülke seçimi başarısız: {country_name} -> {e}")

def _click_na_if_needed(driver, checkbox_id):
    """Checkbox boşsa işaretler ve postback (sayfa yenileme) bekler."""
    try:
        # Sayfa yenilenmiş olabileceği için elementi her seferinde yeniden bul
        checkbox = driver.find_element(By.ID, checkbox_id)
        if not checkbox.is_selected():
            print(f"🔘 '{checkbox_id}' işaretleniyor...")
            driver.execute_script("arguments[0].click();", checkbox)
            # Kritik: DS-160 checkbox tıklandığında __doPostBack tetikler. 
            # Sayfanın kendine gelmesi için bekleme şart.
            time.sleep(2.5) 
    except Exception as e:
        print(f"⚠️ Checkbox işleminde hata: {checkbox_id}")


def fill_student_poc_row(wait, driver, data, idx):
    base = f"ctl00_SiteContentPlaceHolder_FormView1_dtlStudentAddPOC_ctl0{idx}_"

    def v(k): return data.get(k, "").strip()

    _fill_input(wait, driver, base + "tbxADD_POC_SURNAME", v(f"STUDENT_POC{idx+1}_SURNAME"))
    _fill_input(wait, driver, base + "tbxADD_POC_GIVEN_NAME", v(f"STUDENT_POC{idx+1}_GIVEN_NAME"))
    _fill_input(wait, driver, base + "tbxADD_POC_ADDR_LN1", v(f"STUDENT_POC{idx+1}_ADDR1"))
    _fill_input(wait, driver, base + "tbxADD_POC_ADDR_LN2", v(f"STUDENT_POC{idx+1}_ADDR2"))
    _fill_input(wait, driver, base + "tbxADD_POC_ADDR_CITY", v(f"STUDENT_POC{idx+1}_CITY"))

    state = v(f"STUDENT_POC{idx+1}_STATE")
    _fill_input(wait, driver, base + "tbxADD_POC_ADDR_STATE", state)
    _set_na_checkbox_if_empty(wait, driver, base + "cbxADD_POC_ADDR_STATE_NA", state)

    zipc = v(f"STUDENT_POC{idx+1}_ZIP")
    _fill_input(wait, driver, base + "tbxADD_POC_ADDR_POSTAL_CD", zipc)
    _set_na_checkbox_if_empty(wait, driver, base + "cbxADD_POC_ADDR_POSTAL_CD_NA", zipc)

    _select_country(
        wait, driver,
        base + "ddlADD_POC_ADDR_CTRY",
        v(f"STUDENT_POC{idx+1}_COUNTRY") or "TRKY"
    )

    tel = v(f"STUDENT_POC{idx+1}_TEL")
    _fill_input(wait, driver, base + "tbxADD_POC_TEL", tel)
    _set_na_checkbox_if_empty(wait, driver, base + "cbxADD_POC_TEL_NA", tel)

    email = v(f"STUDENT_POC{idx+1}_EMAIL")
    _fill_input(wait, driver, base + "tbxADD_POC_EMAIL_ADDR", email)
    _set_na_checkbox_if_empty(wait, driver, base + "cbxADD_POC_EMAIL_ADDR_NA", email)
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select

def _exists(driver, by, value) -> bool:
    return len(driver.find_elements(by, value)) > 0


def _smart_fill(driver, wait, element_id, value, na_id=None):
    """
    - Element sayfada yoksa: hiçbir şey yapmaz
    - value doluysa: yazar
    - value boşsa ve na_id varsa: NA tıklar
    """
    try:
        if not _exists(driver, By.ID, element_id):
            return

        val = str(value).strip() if value is not None else ""

        if val and val.upper() not in ["N/A", "NONE", "DOES NOT APPLY"]:
            _fill_input(wait, driver, element_id, val)
            time.sleep(0.2)
        elif na_id and _exists(driver, By.ID, na_id):
            _click_na_if_needed(driver, na_id)
            time.sleep(0.2)

    except Exception as e:
        print(f"⚠️ {_short(element_id)} atlandı: {e}")


def _select_by_text_or_value(driver, wait, select_id, desired, na_id=None):
    """
    - Select sayfada yoksa: geç
    - desired boşsa: NA varsa tıkla
    - önce visible_text, sonra value dener
    - hiçbir şey uymuyorsa index(1) fallback (isteğe bağlı)
    """
    try:
        if not _exists(driver, By.ID, select_id):
            return

        val = str(desired).strip() if desired is not None else ""

        if (not val) or (val.upper() in ["N/A", "NONE", "DOES NOT APPLY"]):
            if na_id and _exists(driver, By.ID, na_id):
                _click_na_if_needed(driver, na_id)
                time.sleep(0.2)
            return

        sel_el = wait.until(EC.element_to_be_clickable((By.ID, select_id)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel_el)
        sel = Select(sel_el)

        # visible text
        try:
            sel.select_by_visible_text(val)
            time.sleep(0.6)  # DS-160 postback ihtimali
            return
        except:
            pass

        # value
        try:
            sel.select_by_value(val)
            time.sleep(0.6)
            return
        except:
            pass

        # fallback istersen açık bırak
        # if len(sel.options) > 1:
        #     sel.select_by_index(1)
        #     time.sleep(0.6)

        print(f"⚠️ Dropdown eşleşmedi: {_short(select_id)} -> '{val}'")

    except Exception as e:
        print(f"⚠️ {_short(select_id)} select atlandı: {e}")


def _radio_yes_no_if_exists(driver, wait, base_id, yesno_value):
    """
    base_id: örn "ctl00_..._rblStudyQuestion"
    DS-160 radio id genelde base_id + "_0" (YES) ve base_id + "_1" (NO)
    """
    try:
        yes_id = base_id + "_0"
        no_id = base_id + "_1"

        if not (_exists(driver, By.ID, yes_id) or _exists(driver, By.ID, no_id)):
            return  # sayfada yoksa dokunma

        v = (yesno_value or "YES").strip().upper()
        rid = yes_id if v == "YES" else no_id

        _click_radio(wait, driver, rid)
        time.sleep(2.5)  # postback

    except Exception as e:
        print(f"⚠️ {_short(base_id)} radio atlandı: {e}")


def _short(s: str) -> str:
    # logları kısaltmak için
    return s.split("_")[-1]


# -----------------------------
# Genel: field listesi üzerinden doldurma
# -----------------------------
def fill_fields_if_present(driver, wait, data, field_specs):
    """
    field_specs örnek:
    [
      ("text",   "element_id",             "DATA_KEY", "na_id_or_None"),
      ("select", "select_id",              "DATA_KEY", "na_id_or_None"),
      ("radio",  "radio_base_id",          "DATA_KEY", None),
    ]
    """
    for ftype, eid, data_key, na_id in field_specs:
        try:
            if ftype == "text":
                _smart_fill(driver, wait, eid, data.get(data_key), na_id=na_id)

            elif ftype == "select":
                _select_by_text_or_value(driver, wait, eid, data.get(data_key), na_id=na_id)

            elif ftype == "radio":
                # YES/NO
                _radio_yes_no_if_exists(driver, wait, eid, data.get(data_key))

        except Exception as e:
            print(f"⚠️ {ftype} {_short(eid)} atlandı: {e}")
def _fill_input_verified(wait, driver, element_id, value, timeout=10):
    if value is None:
        return
    val = str(value).strip()
    if not val:
        return

    # element varsa bekle
    els = driver.find_elements(By.ID, element_id)
    if not els:
        return

    el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)

    # readonly/disabled ise kaldırmayı dene
    driver.execute_script("""
      arguments[0].removeAttribute('readonly');
      arguments[0].removeAttribute('disabled');
    """, el)

    # normal yolla dene
    try:
        el.click()
        el.clear()
        el.send_keys(val)
        time.sleep(0.3)

        # ✅ doğrula (gerçekten yazıldı mı?)
        cur = (el.get_attribute("value") or "").strip()
        if cur == val:
            return
    except:
        pass

    # ✅ JS fallback (DS-160 için çok işe yarar)
    driver.execute_script("""
      const el = arguments[0];
      const val = arguments[1];
      el.value = val;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true }));
    """, el, val)
    time.sleep(0.4)


# -----------------------------
# SEVIS + School main function
# -----------------------------
def fill_sevis_and_school_if_needed(wait, driver, data):
    print("🎓 SEVIS sayfası başlıyor (2-pass mode)")

    # -------- PASS 1 --------
    print("➡ PASS 1: Study / SEVIS / Program")

    # Study Question (varsa)
    _radio_yes_no_if_exists(
        driver,
        wait,
        "ctl00_SiteContentPlaceHolder_FormView1_rblStudyQuestion",
        data.get("STUDY_IN_US")
    )

    # SEVIS ID
    _smart_fill(
        driver,
        wait,
        "ctl00_SiteContentPlaceHolder_FormView1_tbxSevisID",
        data.get("SEVIS_ID")
    )

    # Program Number (verified)
    time.sleep(0.8)
    _fill_input_verified(
        wait,
        driver,
        "ctl00_SiteContentPlaceHolder_FormView1_tbxProgram",
        data.get("PROGRAM_NUMBER")
    )

    # -------- POSTBACK WAIT --------
    time.sleep(2.5)  # 👈 okul alanları burada DOM’a girer

    # -------- PASS 2 --------
    print("➡ PASS 2: School fields")

    school_fields = [
        ("text", "ctl00_SiteContentPlaceHolder_FormView1_tbxNameOfSchool", "SCHOOL_NAME", None),
        ("text", "ctl00_SiteContentPlaceHolder_FormView1_tbxSchoolCourseOfStudy", "COURSE_OF_STUDY", None),

        ("text", "ctl00_SiteContentPlaceHolder_FormView1_tbxSchoolStreetAddress1", "SCHOOL_ADDR1", None),
        ("text", "ctl00_SiteContentPlaceHolder_FormView1_tbxSchoolStreetAddress2", "SCHOOL_ADDR2",
         "ctl00_SiteContentPlaceHolder_FormView1_cbxSchoolStreetAddress2_NA"),

        ("text", "ctl00_SiteContentPlaceHolder_FormView1_tbxSchoolCity", "SCHOOL_CITY", None),

        ("select", "ctl00_SiteContentPlaceHolder_FormView1_ddlSchoolState", "SCHOOL_STATE",
         "ctl00_SiteContentPlaceHolder_FormView1_cbxSchoolState_NA"),

        ("text", "ctl00_SiteContentPlaceHolder_FormView1_tbxSchoolZIPCode", "SCHOOL_ZIP",
         "ctl00_SiteContentPlaceHolder_FormView1_cbxSchoolZIPCode_NA"),
    ]

    fill_fields_if_present(driver, wait, data, school_fields)

    print("🟢 SEVIS + School TAMAM (2-pass başarılı)")

def _fill_if_exists(driver, wait, element_id, value, na_id=None):
    """Element sayfada varsa doldurur, değer boşsa ve NA id varsa NA işaretler."""
    elements = driver.find_elements(By.ID, element_id)
    if elements:
        val = str(value).strip() if value else ""
        if val and val.upper() not in ["N/A", "NONE", "NAN"]:
            _fill_input(wait, driver, element_id, val)
        elif na_id:
            _click_na_if_needed(driver, na_id)
def upload_photo_from_url(wait, driver, photo_url: str) -> bool:
    """
    CRM'deki PHOTO_URL'den fotoğrafı indirip DS-160'a yükler.
    Başarılıysa True, başarısız olursa False döner.
    """
    import urllib.request
    import tempfile

    if not photo_url or not photo_url.startswith("http"):
        return False

    tmp_path = None
    try:
        # 1. İndir
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp_path = tmp.name
        print(f"📥 Fotoğraf indiriliyor: {photo_url[:80]}...")
        urllib.request.urlretrieve(photo_url, tmp_path)
        file_size = os.path.getsize(tmp_path)
        print(f"✅ İndirildi: {file_size} bytes")

        if file_size < 1000:
            print("⚠️ Dosya çok küçük, geçersiz")
            return False

        # 2. Input bul — mevcut koddan alınan ID
        file_input = wait.until(EC.presence_of_element_located((
            By.ID, "ctl00_cphMain_imageFileUpload"
        )))
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            file_input
        )

        # 3. Input'u aktif yap ve dosyayı gönder
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].style.display = 'block';
            arguments[0].style.visibility = 'visible';
        """, file_input)
        time.sleep(0.3)

        file_input.send_keys(tmp_path)
        time.sleep(1.0)
        print("✅ Fotoğraf URL'den yüklendi")
        return True

    except Exception as e:
        print(f"❌ upload_photo_from_url hatası: {e}")
        return False

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
def upload_photo_by_fullname(wait, driver, data):
    print("📷 Fotoğraf yükleme başlatıldı")

    import urllib.request

    PHOTO_DIR = os.path.join(
        os.path.expanduser("~"),
        "OneDrive", "Desktop", "amerika bot", "AmericaBot", "photos"
    )
    os.makedirs(PHOTO_DIR, exist_ok=True)
    print(f"📁 Fotoğraf klasörü: {PHOTO_DIR}")

    photo_path = None
    tmp_path   = None

    # ── 1. PHOTO_URL varsa indir ──────────────────────────
    photo_url = data.get("PHOTO_URL") or data.get("photo_url") or ""
    print(f"📎 PHOTO_URL: '{photo_url[:80] if photo_url else 'BOŞ'}'")

    if photo_url and photo_url.startswith("http"):
        tmp_path = os.path.join(PHOTO_DIR, "ds160_temp_upload.jpg")
        try:
            print(f"📥 İndiriliyor → {tmp_path}")
            urllib.request.urlretrieve(photo_url, tmp_path)
            size = os.path.getsize(tmp_path)
            print(f"✅ İndirildi: {size} bytes")
            if size > 1000:
                photo_path = tmp_path
            else:
                print("⚠️ Dosya çok küçük, geçersiz")
                os.unlink(tmp_path)
                tmp_path = None
        except Exception as e:
            print(f"⚠️ URL'den indirme başarısız: {e}")
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            tmp_path = None

    # ── 2. Klasörde isimle ara ────────────────────────────
    if not photo_path:
        full_name = data.get("FULL_NAME", "").strip()
        if not full_name:
            given   = data.get("GIVEN_NAME", "").strip()
            surname = data.get("SURNAME", "").strip()
            if not given or not surname:
                raise Exception("❌ İsim bilgisi yok → foto yüklenemez")
            full_name = f"{given} {surname}"

        print(f"🔍 Klasörde aranıyor: '{full_name}'")
        fname, score = _find_best_photo(PHOTO_DIR, full_name)
        print(f"🔍 Arama sonucu: fname={fname} score={score:.2f if fname else 0}")
        if fname and score >= 0.70:
            photo_path = os.path.join(PHOTO_DIR, fname)
            print(f"✅ Fotoğraf bulundu: {photo_path}")

    if not photo_path:
        raise Exception(
            f"❌ Fotoğraf bulunamadı — PHOTO_URL boş ve "
            f"klasörde eşleşme yok. "
            f"Fotoğrafı şu klasöre koy: {PHOTO_DIR}"
        )

    # ── 3. File input'a gönder ────────────────────────────
    # id = ctl00_cphMain_imageFileUpload
    try:
        file_input = wait.until(EC.presence_of_element_located((
            By.ID, "ctl00_cphMain_imageFileUpload"
        )))
        driver.execute_script("""
            arguments[0].removeAttribute('disabled');
            arguments[0].style.display    = 'block';
            arguments[0].style.visibility = 'visible';
            arguments[0].style.opacity    = '1';
        """, file_input)
        time.sleep(0.3)

        abs_path = os.path.abspath(photo_path)
        file_input.send_keys(abs_path)
        print(f"✅ Dosya input'a gönderildi: {abs_path}")
        time.sleep(1.0)

    finally:
        # Geçici dosyayı sil (sadece URL'den indirilenler)
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
                print(f"🗑️ Geçici dosya silindi: {tmp_path}")
        except Exception:
            pass
import os
import unicodedata
from difflib import SequenceMatcher

def _normalize(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )

def _find_best_photo(desktop_path: str, full_name: str):
    target = _normalize(full_name)

    best_match = None
    best_score = 0.0

    for fname in os.listdir(desktop_path):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        name_only = os.path.splitext(fname)[0]
        score = SequenceMatcher(
            None, target, _normalize(name_only)
        ).ratio()

        if score > best_score:
            best_score = score
            best_match = fname

    return best_match, best_score
def safe_fill_page(driver, wait, data):
    """
    Sayfadaki tüm form elementlerini tara.
    Bizde varsa doldur, yoksa güvenli default değer ver.
    Hiçbir zaman hata atmaz.
    """
    print("🛡️ safe_fill_page başladı")

    # ── ID → DATA eşlemesi ──────────────────────────────────
    ID_TO_DATA_KEY = {
        # Personal 1
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_SURNAME":           "SURNAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_GIVEN_NAME":        "GIVEN_NAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_FULL_NAME_NATIVE":  "FULL_NAME_NATIVE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxDOBYear":               "BIRTH_YEAR",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_POB_CITY":          "BIRTH_CITY",
        # Personal 2
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_NATIONAL_ID":       "NATIONAL_ID",
        # Travel
        "ctl00_SiteContentPlaceHolder_FormView1_tbxTRAVEL_LOS":            "TRAVEL_LOS_VALUE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxTRAVEL_DTEYear":        "INTENDED_ARRIVAL_YEAR",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxArriveCity":            "ARRIVAL_CITY",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxStreetAddress1":        "US_ADDRESS1",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxCity":                  "US_CITY",
        # Address
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_LN1":          "HOME_ADDRESS",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_CITY":         "HOME_CITY",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_STATE":        "HOME_STATE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_ADDR_POSTAL_CD":    "HOME_POSTAL_CODE",
        # Phone
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_HOME_TEL":          "PRIMARY_PHONE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_MOBILE_TEL":        "MOBILE_PHONE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_BUS_TEL":           "WORK_PHONE",
        # Email
        "ctl00_SiteContentPlaceHolder_FormView1_tbxAPP_EMAIL_ADDR":        "EMAIL",
        # Passport
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_NUM":               "PASSPORT_NUMBER",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUED_IN_CITY":    "PASSPORT_ISSUED_CITY",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPPT_ISSUEDYear":        "PASSPORT_ISSUE_DATE",
        # POC
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_SURNAME":        "US_POC_SURNAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_GIVEN_NAME":     "US_POC_GIVEN_NAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_LN1":       "US_POC_ADDR1",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_ADDR_CITY":      "US_POC_CITY",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_HOME_TEL":       "US_POC_PHONE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxUS_POC_EMAIL_ADDR":     "US_POC_EMAIL",
        # Family
        "ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_SURNAME":        "FATHER_SURNAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxFATHER_GIVEN_NAME":     "FATHER_GIVEN",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_SURNAME":        "MOTHER_SURNAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxMOTHER_GIVEN_NAME":     "MOTHER_GIVEN",
        # Work
        "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchName":            "EMP_SCH_NAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchAddr1":           "EMP_SCH_ADDR1",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxEmpSchCity":            "EMP_SCH_CITY",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxWORK_EDUC_TEL":         "EMP_SCH_PHONE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxDescribeDuties":        "EMP_DUTIES",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxCURR_MONTHLY_SALARY":   "EMP_MONTHLY_SALARY",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxExplainOtherPresentOccupation": "PRESENT_OCCUPATION_EXPLAIN",
        # Payer
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPayingCompany":         "PAYER_COMPANY_NAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPayerPhone":            "PAYER_COMPANY_PHONE",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxCompanyRelation":       "PAYER_COMPANY_RELATIONSHIP",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPayerStreetAddress1":   "PAYER_ADDRESS1",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPayerCity":             "PAYER_CITY",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPayerSurname":          "PAYER_SURNAME",
        "ctl00_SiteContentPlaceHolder_FormView1_tbxPayerGivenName":        "PAYER_GIVEN_NAME",
    }

    # ── Sayfadaki tüm input'ları tara ───────────────────────
    try:
        all_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
        for el in all_inputs:
            try:
                el_id = el.get_attribute("id") or ""
                if not el_id:
                    continue
                if el.get_attribute("disabled") or el.get_attribute("readonly"):
                    continue
                current_val = (el.get_attribute("value") or "").strip()
                if current_val:
                    continue  # zaten dolu, atla

                # Bizde var mı?
                if el_id in ID_TO_DATA_KEY:
                    data_key = ID_TO_DATA_KEY[el_id]
                    val = str(data.get(data_key, "")).strip()
                    if val and val.upper() not in ("N/A", "NA", "NONE"):
                        driver.execute_script("""
                            arguments[0].removeAttribute('disabled');
                            arguments[0].removeAttribute('readonly');
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
                        """, el, val)
                        print(f"✅ safe_fill: {el_id} → {val[:30]}")
                    else:
                        # Bizde yok veya boş → XXXXXXXXXX yaz
                        driver.execute_script("""
                            arguments[0].value = 'XXXXXXXXXX';
                            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
                        """, el)
                        print(f"ℹ️ safe_fill fallback: {el_id} → XXXXXXXXXX")
            except Exception as e:
                print(f"⚠️ safe_fill input skip: {e}")

    except Exception as e:
        print(f"⚠️ safe_fill inputs error: {e}")

    # ── Sayfadaki tüm select'leri tara ──────────────────────
    try:
        all_selects = driver.find_elements(By.CSS_SELECTOR, "select")
        for sel_el in all_selects:
            try:
                el_id = sel_el.get_attribute("id") or ""
                if not el_id:
                    continue
                sel = Select(sel_el)
                current = sel.first_selected_option.get_attribute("value") or ""
                if current:
                    continue  # zaten seçili

                # NO veya N seçeneği var mı?
                options = [o.get_attribute("value") for o in sel.options]
                if "N" in options:
                    sel.select_by_value("N")
                elif "NO" in options:
                    sel.select_by_value("NO")
                elif len(options) > 1:
                    sel.select_by_index(1)  # ilk anlamlı option
                print(f"ℹ️ safe_fill select default: {el_id}")
            except Exception as e:
                print(f"⚠️ safe_fill select skip: {e}")
    except Exception as e:
        print(f"⚠️ safe_fill selects error: {e}")

    # ── Does Not Apply checkbox'larını tara ─────────────────
    try:
        all_checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for cb in all_checkboxes:
            try:
                label = cb.get_attribute("id") or ""
                # Sadece NA/Does Not Apply checkbox'ları
                if any(x in label.upper() for x in ["_NA", "CBEX", "CBX"]):
                    if not cb.is_selected():
                        # İlgili input disabled ise işaretle
                        pass  # Bunları elle yönetiyoruz, burada dokunma
            except Exception:
                pass
    except Exception:
        pass

    print("🛡️ safe_fill_page tamamlandı")