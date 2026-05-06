import re
import time
from selenium.webdriver.support.ui import WebDriverWait, Select as SeleniumSelect
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from form_fill import (
    fill_basic_identity_form,
    wait_after_state_na,
    fill_date_dd_mmm_yyyy,
    select_other_names,
    fill_birth_state,
    click_next_travel,
    click_continue_application,
    click_save_personal2,
    fill_personal2_ids,
    fill_permanent_resident_section,
    select_other_nationality_yes,
    fill_single_other_nationality,
    click_add_another_other_nationality,
    select_other_nationality,
    select_nationality,
    fill_other_names,
    select_gender,
    select_marital_status,
    fill_date_of_birth,
    fill_place_of_birth,
    select_birth_country,
    save_and_go_next,
    select_telecode_no,
    force_continue_application,
    wait_and_click_next_personal2,
    click_nexts,
    click_continue_applications,
    click_save,
    fill_payer_info,
    parse_travel_companions,
    fill_intended_length_of_stay,
    fill_intended_arrival_date,
    select_purpose_of_trip,
    fill_us_address,
    select_purpose_subcategory_if_exists,
    select_specific_travel,
    fill_travel_details,
    fill_travel_companions,
    fill_previous_us_travel,
    fill_previous_visa,
    fill_prev_visa_refused,
    fill_iv_petition,
    fill_additional_social_media,
    fill_home_address,
    fill_mailing_address,
    fill_phone_numbers,
    fill_additional_phone,
    fill_email,
    fill_additional_email,
    fill_social_media,
    fill_passport_info,
    fill_lost_passport,
    fill_us_point_of_contact,
    fill_parents_info,
    fill_us_immediate_relatives,
    fill_us_other_relatives,
    auto_fill_family_page,
    fill_former_spouse,
    fill_widowed_spouse,
    fill_spouse_info,
    fill_student_poc_sections,
    fill_present_occupation_section,
    fill_previous_employment,
    fill_other_education,
    fill_additional_work_education_section,
    fill_health_security_section,
    fill_criminal_security_section,
    fill_security_violations_section,
    fill_removal_immigration_section,
    fill_misc_immigration_violations_section,
    fill_sevis_and_school_if_needed,
    upload_photo_by_fullname,
    PRESENT_OCCUPATION_MAP,
    fill_present_occupation_explain,
    fill_employer_or_school_info,
)


# =====================================================
# PHOTO PAGE CHECK
# =====================================================
def _check_photo_page(driver) -> bool:
    """Fotoğraf yükleme sayfasında mıyız?"""
    photo_ids = [
        "ctl00_SiteContentPlaceHolder_FormView1_btnUploadPhoto",
        "ctl00_SiteContentPlaceHolder_btnUploadPhoto",
        "ctl00_cphMain_imageFileUpload",
        "ctl00_SiteContentPlaceHolder_FormView1_fileUpload",
    ]
    for pid in photo_ids:
        try:
            el = driver.find_element(By.ID, pid)
            if el.is_displayed():
                return True
        except Exception:
            continue
    # URL kontrolü
    try:
        if "Photo" in driver.current_url or "photo" in driver.current_url:
            return True
    except Exception:
        pass
    return False

def _scn(wait, driver, on_photo_page=None, label="Travel Companions") -> bool:
    click_save(wait, driver)
    if on_photo_page and _check_photo_page(driver):
        print("📸 Fotoğraf sayfası tespit edildi (save sonrası)")
        on_photo_page()
        return True

    try:
        click_continue_applications(wait, driver)
    except Exception as e:
        print(f"⚠️ Continue butonu bulunamadı, atlanıyor: {e}")
    if on_photo_page and _check_photo_page(driver):
        print("📸 Fotoğraf sayfası tespit edildi (continue sonrası)")
        on_photo_page()
        return True

    try:
        click_nexts(wait, driver, label=label)
    except Exception as e:
        print(f"⚠️ Next butonu bulunamadı, atlanıyor: {e}")
    if on_photo_page and _check_photo_page(driver):
        print("📸 Fotoğraf sayfası tespit edildi (next sonrası)")
        on_photo_page()
        return True

    return False
# =====================================================
# FALLBACK
# =====================================================
def enrich_data_with_fallbacks(data: dict) -> dict:
    d = data.copy()
    raw = d.get("raw_data", {})
    if isinstance(raw, dict):
        for k, v in raw.items():
            if k not in d or not str(d.get(k, "")).strip():
                d[k] = v
    def fb(key, value):
        if not str(d.get(key, "")).strip():
            d[key] = value

    yesno_fields = [
        "OTHER_NAME", "OTHER_NATIONALITY", "PERMANENT_RESIDENT_OTHER_COUNTRY",
        "PREV_US_TRAVEL", "US_DRIVER_LICENSE", "PREV_VISA",
        "PREV_VISA_SAME_TYPE", "PREV_VISA_SAME_COUNTRY", "PREV_VISA_TEN_PRINTED",
        "PREV_VISA_LOST", "PREV_VISA_CANCELLED", "PREV_VISA_REFUSED",
        "IV_PETITION", "ESTA_DENIED",
        "HAS_ADDITIONAL_PHONE", "HAS_ADDITIONAL_EMAIL",
        "ADDITIONAL_SOCIAL", "PASSPORT_LOST",
        "TRAVEL_COMPANIONS",
        "PREV_EMPLOYED",
        "CLAN_TRIBE", "COUNTRIES_VISITED", "ORGANIZATION",
        "SPECIALIZED_SKILLS", "MILITARY_SERVICE", "INSURGENT_ORG",
        "COMM_DISEASE", "DISORDER", "DRUG_ABUSE",
        "CONTROLLED_SUBSTANCES", "PROSTITUTION", "HUMAN_TRAFFICKING",
        "ASSISTED_SEVERE_TRAFFICKING", "HUMAN_TRAFFICKING_RELATED",
        "ARRESTED", "MONEY_LAUNDERING",
        "ILLEGAL_ACTIVITY", "TERRORIST_ACTIVITY", "TERRORIST_SUPPORT",
        "TERRORIST_ORG", "TERRORIST_REL", "GENOCIDE", "TORTURE",
        "EX_VIOLENCE", "CHILD_SOLDIER", "RELIGIOUS_FREEDOM",
        "POPULATION_CONTROLS", "TRANSPLANT",
        "US_IMMEDIATE_RELATIVE", "US_OTHER_RELATIVE",
        "FATHER_IN_US", "MOTHER_IN_US",
        "FATHER_DOB_NA", "MOTHER_DOB_NA",
        "HAS_SPECIFIC_TRAVEL_PLANS",
        "PAYER_ADDRESS_SAME",
        "STUDY_IN_US",
    ]
    for f in yesno_fields:
        fb(f, "NO")

    fb("MAILING_SAME_AS_HOME", "YES")
    fb("MAILING_ADDRESS",      "XXXXXXXXXX")
    fb("MAILING_CITY",         "XXXXXXXXXX")
    fb("MAILING_COUNTRY",      "Turkey")

    fb("PRIMARY_PHONE",        "5555555555")
    fb("MOBILE_PHONE",         "")
    fb("WORK_PHONE",           "")
    fb("MOBILE_PHONE_NA",      "YES")
    fb("WORK_PHONE_NA",        "YES")
    fb("ADDITIONAL_PHONE_NUM", "5555555555")
    fb("EMP_SCH_PHONE",        "5555555555")
    fb("PAYER_PHONE",          "5555555555")
    fb("PAYER_COMPANY_PHONE",  "5555555555")
    fb("US_POC_PHONE",         "5555555555")

    for f in ["EMAIL", "ADDITIONAL_EMAIL1", "PAYER_EMAIL", "US_POC_EMAIL"]:
        fb(f, "noreply@example.com")

    text_fields = [
        "SURNAME", "GIVEN_NAME", "FULL_NAME_NATIVE",
        "BIRTH_CITY",
        "HOME_ADDRESS", "HOME_CITY",
        "US_ADDRESS1", "US_CITY",
        "EMP_SCH_NAME", "EMP_SCH_ADDR1", "EMP_SCH_CITY",
        "EMP_SCH_START_DATE", "EMP_DUTIES",
        "PURPOSE_OF_TRIP",
        "INTENDED_ARRIVAL_DAY", "INTENDED_ARRIVAL_MONTH", "INTENDED_ARRIVAL_YEAR",
        "TRAVEL_LOS_VALUE",
        "US_POC_ADDR1", "US_POC_CITY",
        "FATHER_SURNAME", "FATHER_GIVEN",
        "MOTHER_SURNAME", "MOTHER_GIVEN",
        "PRESENT_OCCUPATION_EXPLAIN",
        "PASSPORT_ISSUED_CITY",
    ]
    for f in text_fields:
        fb(f, "XXXXXXXXXX")

    fb("US_POC_STATE", "New York")
    fb("NATIONALITY", "Turkey")
    fb("PASSPORT_NUMBER",      "U123124124")
    fb("PASSPORT_ISSUE_DATE",  "01-JAN-2020")
    fb("PASSPORT_EXPIRY_DATE", "01-JAN-2030")

    fb("BIRTH_COUNTRY",              "Turkey")
    fb("HOME_COUNTRY",               "Turkey")
    fb("PASSPORT_ISSUED_COUNTRY",    "Turkey")
    fb("PASSPORT_ISSUED_IN_COUNTRY", "Turkey")
    fb("EMP_SCH_COUNTRY",            "Turkey")
    fb("US_POC_COUNTRY",             "Turkey")
    fb("PAYER_COUNTRY",              "Turkey")

    fb("LANGUAGES", "Turkish")

    # ─── Askerlik sabit değerleri ─────────────────────────────
    fb("MIL_COUNTRY",   "TURKEY")
    fb("MIL_BRANCH",    "COMPULSORY MILITARY SERVICE")
    fb("MIL_RANK",      "INFANTRY")
    fb("MIL_SPECIALTY", "COMPULSORY MILITARY SERVICE")

    fb("TRAVEL_LOS_UNIT",    "D")
    fb("MARITAL_STATUS",     "SINGLE")
    fb("GENDER",             "M")
    fb("BIRTH_DAY",          "1")
    fb("BIRTH_MONTH",        "JAN")
    fb("BIRTH_YEAR",         "1990")
    fb("PAYER_TYPE",         "SELF")
    fb("SOCIAL_MEDIA",       "NONE")
    fb("PREV_US_VISITS",     "0")
    fb("US_POC_RELATION",    "OTHER")
    fb("US_STATE",           "NY")
    fb("PASSPORT_TYPE",      "REGULAR")
    fb("PRESENT_OCCUPATION", "NOT_EMPLOYED")
    fb("OTHER_NAME",         "NO")

    # ─── VISIT1 verisi yoksa ARRIVAL bilgilerinden oluştur ────
    if not str(d.get("VISIT1_ARRIVAL_DATE", "")).strip():
        arrival_day   = str(d.get("ARRIVAL_DAY", "")).strip().zfill(2)
        arrival_month = str(d.get("ARRIVAL_MONTH", "")).strip().upper()
        arrival_year  = str(d.get("ARRIVAL_YEAR", "")).strip()
        if arrival_day and arrival_month and arrival_year:
            d["VISIT1_ARRIVAL_DATE"] = f"{arrival_day}-{arrival_month}-{arrival_year}"
            print(f"ℹ️ VISIT1_ARRIVAL_DATE oluşturuldu: {d['VISIT1_ARRIVAL_DATE']}")

    if not str(d.get("VISIT1_STAY_LENGTH", "")).strip():
        d["VISIT1_STAY_LENGTH"] = str(d.get("TRAVEL_LOS_VALUE", "30")).strip() or "30"
        print(f"ℹ️ VISIT1_STAY_LENGTH oluşturuldu: {d['VISIT1_STAY_LENGTH']}")

    if not str(d.get("VISIT1_STAY_UNIT", "")).strip():
        unit_raw = str(d.get("TRAVEL_LOS_UNIT", "D")).strip().upper()
        unit_map = {
            "DAY(S)": "D", "DAYS": "D", "DAY": "D",
            "MONTH(S)": "M", "MONTHS": "M", "MONTH": "M",
            "WEEK(S)": "W", "WEEKS": "W", "WEEK": "W",
            "YEAR(S)": "Y", "YEARS": "Y", "YEAR": "Y",
            "D": "D", "M": "M", "W": "W", "Y": "Y",
        }
        d["VISIT1_STAY_UNIT"] = unit_map.get(unit_raw, "D")
        print(f"ℹ️ VISIT1_STAY_UNIT oluşturuldu: {d['VISIT1_STAY_UNIT']}")

    print("✅ enrich_data_with_fallbacks tamamlandı")
    return d


# =====================================================
# PRESENT OCCUPATION – RESUME FIX
# =====================================================
def _fill_present_occupation_resume(driver, wait, data):
    occ_raw = data.get("PRESENT_OCCUPATION", "NOT_EMPLOYED").strip().upper()
    target  = PRESENT_OCCUPATION_MAP.get(occ_raw, "N")

    ddl_id = "ctl00_SiteContentPlaceHolder_FormView1_ddlPresentOccupation"
    ddl = wait.until(EC.presence_of_element_located((By.ID, ddl_id)))
    sel = SeleniumSelect(ddl)
    current = sel.first_selected_option.get_attribute("value")

    if current == target:
        print(f"ℹ️ Present Occupation zaten seçili ({occ_raw}), JS postback tetikleniyor...")
        driver.execute_script(
            "__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$ddlPresentOccupation', '');"
        )
        time.sleep(1.5)
    else:
        print(f"🔄 Present Occupation değiştiriliyor: {current} → {target}")
        SeleniumSelect(
            wait.until(EC.element_to_be_clickable((By.ID, ddl_id)))
        ).select_by_value(target)
        time.sleep(1.5)

    if occ_raw in ("NOT_EMPLOYED", "OTHER"):
        try:
            fill_present_occupation_explain(wait, driver, data)
            print(f"✅ {occ_raw} açıklaması dolduruldu.")
        except Exception as e:
            print(f"⚠️ Açıklama alanı doldurulamadı: {e}")
    elif occ_raw not in ("RETIRED", "HOMEMAKER"):
        try:
            fill_employer_or_school_info(wait, driver, data)
            print("✅ İşveren/Okul bilgileri dolduruldu.")
        except Exception as e:
            print(f"⚠️ İşveren/Okul bilgileri doldurulamadı: {e}")

    print(f"✅ Present Occupation tamamlandı: {occ_raw}")


# =====================================================
# ADDITIONAL WORK/EDUCATION – RESUME FIX
# =====================================================
def _js_click_radio(driver, wait, radio_id, do_postback=False):
    el = wait.until(EC.presence_of_element_located((By.ID, radio_id)))
    driver.execute_script("""
        var el = arguments[0];
        el.checked = true;
        el.dispatchEvent(new Event('change', {bubbles: true}));
        el.click();
    """, el)
    if do_postback:
        onclick = el.get_attribute("onclick") or ""
        if "__doPostBack" in onclick:
            match = re.search(r"__doPostBack\('([^']+)','([^']*)'\)", onclick)
            if match:
                arg1 = match.group(1)
                arg2 = match.group(2)
                driver.execute_script(
                    f"__doPostBack('{arg1}','{arg2}');"
                )
    time.sleep(1.0)

from selenium.webdriver.support.ui import Select
def _fill_additional_work_education_resume(driver, wait, data):
    print("📋 Additional Work/Education (RESUME) kontrol ediliyor...")

    # Language dolu mu kontrol et
    lang_already_filled = False
    try:
        lang_el = driver.find_element(
            By.ID,
            "ctl00_SiteContentPlaceHolder_FormView1_dtlLANGUAGES_ctl00_tbxLANGUAGE_NAME"
        )
        lang_val = lang_el.get_attribute("value").strip()
        if lang_val:
            print(f"ℹ️ Language zaten dolu ({lang_val}), dil/clan/countries kısmı atlanıyor.")
            lang_already_filled = True
    except Exception:
        pass

    if not lang_already_filled:
        print("📝 Sayfa boş, dil/clan/countries dolduruluyor...")

        # 1. CLAN / TRIBE
        clan = data.get("CLAN_TRIBE", "NO").upper()
        _js_click_radio(driver, wait,
            "ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_0" if clan == "YES"
            else "ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_1",
            do_postback=(clan == "YES")
        )
        if clan == "YES":
            el = wait.until(EC.visibility_of_element_located(
                (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_tbxCLAN_TRIBE_NAME")
            ))
            driver.execute_script("arguments[0].value='';", el)
            el.send_keys(data.get("CLAN_TRIBE_NAME", ""))
        print(f"✅ CLAN_TRIBE: {clan}")

        # 2. LANGUAGES
        langs = [x.strip() for x in data.get("LANGUAGES", "Turkish").split(",") if x.strip()]
        if not langs:
            langs = ["Turkish"]
        base_lang = "ctl00_SiteContentPlaceHolder_FormView1_dtlLANGUAGES_ctl"
        for i, lang in enumerate(langs):
            idx    = f"{i:02d}"
            tbx_id = f"{base_lang}{idx}_tbxLANGUAGE_NAME"
            add_id = f"{base_lang}{idx}_InsertButtonLANGUAGE"
            el = wait.until(EC.visibility_of_element_located((By.ID, tbx_id)))
            driver.execute_script("""
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = '';
                arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            """, el)
            el.send_keys(lang)
            driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", el
            )
            if i < len(langs) - 1:
                wait.until(EC.element_to_be_clickable((By.ID, add_id))).click()
                time.sleep(0.8)
        print(f"✅ LANGUAGES: {langs}")

        # 3. COUNTRIES VISITED
        countries_raw = data.get("COUNTRIES_VISITED", "").strip()
        if (
            countries_raw and
            countries_raw.upper() not in ("NO", "NONE", "") and
            not countries_raw.upper().startswith("I HAVE NOT")
        ):
            time.sleep(1)

            countries = [c.strip().upper() for c in countries_raw.split(",") if c.strip()]

            country_map = {
                "TURKEY": "TRKY", "GERMANY": "GER", "FRANCE": "FRAN",
                "UNITED KINGDOM": "GRBR", "UNITED STATES": "USA",
                "UNITED STATES OF AMERICA": "USA", "ITALY": "ITLY",
                "SPAIN": "SPN", "NETHERLANDS": "NETH", "GREECE": "GRC",
                "RUSSIA": "RUS", "UKRAINE": "UKR", "GEORGIA": "GEO",
                "AZERBAIJAN": "AZR", "ARMENIA": "ARM", "IRAN": "IRAN",
                "IRAQ": "IRAQ", "SYRIA": "SYR", "SAUDI ARABIA": "SARB",
                "UAE": "UAE", "UNITED ARAB EMIRATES": "UAE",
                "QATAR": "QTAR", "KUWAIT": "KUWT", "JORDAN": "JORD",
                "EGYPT": "EGYP", "MOROCCO": "MORO", "TUNISIA": "TNSA",
                "JAPAN": "JPN", "CHINA": "CHIN", "SOUTH KOREA": "KOR",
                "KOREA, REPUBLIC OF (SOUTH)": "KOR", "INDIA": "IND",
                "THAILAND": "THAI", "MALAYSIA": "MLAS", "SINGAPORE": "SING",
                "INDONESIA": "IDSA", "VIETNAM": "VTNM", "PHILIPPINES": "PHIL",
                "AUSTRALIA": "ASTL", "NEW ZEALAND": "NZLD",
                "CANADA": "CAN", "MEXICO": "MEX", "BRAZIL": "BRZL",
                "ARGENTINA": "ARG", "COLOMBIA": "COL",
                "SWITZERLAND": "SWTZ", "AUSTRIA": "AUST", "BELGIUM": "BELG",
                "SWEDEN": "SWDN", "NORWAY": "NORW", "DENMARK": "DEN",
                "FINLAND": "FIN", "POLAND": "POL", "CZECH REPUBLIC": "CZEC",
                "HUNGARY": "HUNG", "ROMANIA": "ROM", "BULGARIA": "BULG",
                "CROATIA": "HRV", "SERBIA": "SBA", "ALBANIA": "ALB",
                "ISRAEL": "ISRL", "LEBANON": "LEBN", "PAKISTAN": "PKST",
                "AFGHANISTAN": "AFGH", "KAZAKHSTAN": "KAZ", "UZBEKISTAN": "UZB",
                "PORTUGAL": "PORT", "IRELAND": "IRE", "LUXEMBOURG": "LXM",
                "ICELAND": "ICLD", "ESTONIA": "EST", "LATVIA": "LATV",
                "LITHUANIA": "LITH", "SLOVAKIA": "SVK", "SLOVENIA": "SVN",
                "MALTA": "MLTA", "CYPRUS": "CYPR", "BOSNIA-HERZEGOVINA": "BIH",
                "NORTH MACEDONIA": "MKD", "MOLDOVA": "MLD", "BELARUS": "BYS",
                "MONGOLIA": "MONG", "TAJIKISTAN": "TJK", "KYRGYZSTAN": "KGZ",
                "TURKMENISTAN": "TKM", "BAHRAIN": "BAHR", "OMAN": "OMAN",
                "ISRAEL": "ISRL", "IRAQ": "IRAQ", "YEMEN": "YEM",
                "NIGERIA": "NRA", "SOUTH AFRICA": "SAFR", "KENYA": "KENY",
                "ETHIOPIA": "ETH", "GHANA": "GHAN", "TANZANIA": "TAZN",
                "UGANDA": "UGAN", "ALGERIA": "ALGR", "LIBYA": "LBYA",
                "SUDAN": "SUDA", "SOMALIA": "SOMA", "CAMEROON": "CMRN",
            }

            base_cv = "ctl00_SiteContentPlaceHolder_FormView1_dtlCountriesVisited_ctl"

            # Sayfada kaç satır var?
            existing_cv = 0
            while True:
                els = driver.find_elements(By.ID, f"{base_cv}{existing_cv:02d}_ddlCOUNTRIES_VISITED")
                if not els:
                    break
                existing_cv += 1
            print(f"ℹ️ Countries Visited: {existing_cv} mevcut satır, {len(countries)} gerekli")

            # Eksik kadar Add Another tıkla
            for i in range(existing_cv, len(countries)):
                driver.execute_script(
                    f"__doPostBack('ctl00$SiteContentPlaceHolder$FormView1$dtlCountriesVisited$ctl{(i-1):02d}$InsertButtonCountriesVisited','');"
                )
                time.sleep(1)

            # Hepsini doldur
            for i, country in enumerate(countries):
                cv_val = country_map.get(country)
                if not cv_val:
                    print(f"⚠️ Ülke map'te bulunamadı: {country}, atlanıyor")
                    continue
                try:
                    Select(wait.until(EC.element_to_be_clickable(
                        (By.ID, f"{base_cv}{i:02d}_ddlCOUNTRIES_VISITED")
                    ))).select_by_value(cv_val)
                    print(f"✅ Countries Visited [{i+1}]: {country}")
                except Exception as e:
                    print(f"⚠️ Countries Visited [{i+1}] seçilemedi: {e}")
        else:
            _js_click_radio(driver, wait,
                "ctl00_SiteContentPlaceHolder_FormView1_rblCOUNTRIES_VISITED_IND_1",
                do_postback=False
            )
            print("ℹ️ Countries Visited: NO")

        # 4. ORGANIZATION
        org = data.get("ORGANIZATION", "NO").upper()
        _js_click_radio(driver, wait,
            "ctl00_SiteContentPlaceHolder_FormView1_rblORGANIZATION_IND_0" if org == "YES"
            else "ctl00_SiteContentPlaceHolder_FormView1_rblORGANIZATION_IND_1",
            do_postback=(org == "YES")
        )
        print(f"✅ ORGANIZATION: {org}")

        # 5. SPECIALIZED SKILLS
        skills = data.get("SPECIALIZED_SKILLS", "NO").upper()
        _js_click_radio(driver, wait,
            "ctl00_SiteContentPlaceHolder_FormView1_rblSPECIALIZED_SKILLS_IND_0" if skills == "YES"
            else "ctl00_SiteContentPlaceHolder_FormView1_rblSPECIALIZED_SKILLS_IND_1",
            do_postback=False
        )
        print(f"✅ SPECIALIZED_SKILLS: {skills}")

    # 6. MILITARY SERVICE — her zaman doldur
    mil = data.get("MILITARY_SERVICE", "NO").upper()
    print(f"🪖 Military Service: {mil}")
    _js_click_radio(driver, wait,
        "ctl00_SiteContentPlaceHolder_FormView1_rblMILITARY_SERVICE_IND_0" if mil == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblMILITARY_SERVICE_IND_1",
        do_postback=(mil == "YES")
    )
    time.sleep(1)

    if mil == "YES":
        mil_country   = data.get("MIL_COUNTRY",   "TURKEY")
        mil_branch    = data.get("MIL_BRANCH",    "COMPULSORY MILITARY SERVICE")
        mil_rank      = data.get("MIL_RANK",      "INFANTRY")
        mil_specialty = data.get("MIL_SPECIALTY", "COMPULSORY MILITARY SERVICE")
        mil_from      = data.get("MIL_FROM",      "")
        mil_to        = data.get("MIL_TO",        "")

        print(f"DEBUG mil_branch={mil_branch}, mil_rank={mil_rank}, mil_from={mil_from}, mil_to={mil_to}")

        country_value_map = {
            "TURKEY": "TRKY", "UNITED STATES": "USA", "UNITED STATES OF AMERICA": "USA",
            "GERMANY": "GER", "FRANCE": "FRAN", "UNITED KINGDOM": "GRBR",
            "RUSSIA": "RUS", "CHINA": "CHIN", "IRAN": "IRAN", "IRAQ": "IRAQ",
            "SYRIA": "SYR", "AZERBAIJAN": "AZR", "GEORGIA": "GEO",
            "ARMENIA": "ARM", "UKRAINE": "UKR",
        }
        country_val = country_value_map.get(mil_country.upper(), "TRKY")

        # Ülke seç
        try:
            Select(wait.until(EC.element_to_be_clickable((
                By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_ddlMILITARY_SVC_CNTRY"
            )))).select_by_value(country_val)
            print(f"✅ MIL_COUNTRY: {mil_country}")
        except Exception as e:
            print(f"⚠️ MIL_COUNTRY seçilemedi: {e}")

        # Postback bekle
        time.sleep(2)

        def js_fill_mil(element_id, value):
            if not value:
                print(f"DEBUG js_fill_mil: boş, atlanıyor → {element_id}")
                return
            print(f"DEBUG js_fill_mil: yazılıyor → {element_id} = {value}")
            try:
                el = wait.until(EC.presence_of_element_located((By.ID, element_id)))
                driver.execute_script("""
                    var el = arguments[0];
                    el.removeAttribute('disabled');
                    el.removeAttribute('readonly');
                    el.value = arguments[1];
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                """, el, str(value))
                print(f"✅ js_fill_mil tamamlandı → {value}")
            except Exception as e:
                print(f"⚠️ js_fill_mil hata → {element_id}: {e}")

        js_fill_mil(
            "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_BRANCH",
            mil_branch
        )
        time.sleep(0.3)
        js_fill_mil(
            "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_RANK",
            mil_rank
        )
        time.sleep(0.3)
        js_fill_mil(
            "ctl00_SiteContentPlaceHolder_FormView1_dtlMILITARY_SERVICE_ctl00_tbxMILITARY_SVC_SPECIALTY",
            mil_specialty
        )
        time.sleep(0.3)

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

        print("✅ Military Service detayları dolduruldu")

    # 7. INSURGENT ORG — her zaman doldur
    insurgent = data.get("INSURGENT_ORG", "NO").upper()
    _js_click_radio(driver, wait,
        "ctl00_SiteContentPlaceHolder_FormView1_rblINSURGENT_ORG_IND_0" if insurgent == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblINSURGENT_ORG_IND_1",
        do_postback=False
    )
    print(f"✅ INSURGENT_ORG: {insurgent}")

    print("✅ Additional Work/Education (RESUME) tamamlandı")



# =====================================================
# MAIN RESUME FLOW
# =====================================================
def fill_ds160_resume_application(driver, wait, data, on_photo_page=None):
    print("🔄 DS-160 RESUME FLOW BAŞLADI")

    data = enrich_data_with_fallbacks(data)

    SURNAME          = data.get("SURNAME", "")
    GIVEN_NAME       = data.get("GIVEN_NAME", "")
    FULL_NAME_NATIVE = data.get("FULL_NAME_NATIVE", "")
    OTHER_NAMES      = data.get("OTHER_NAMES", "N").upper()

    # ─── Personal 1 ───────────────────────────────────────────
    fill_basic_identity_form(wait, driver, SURNAME, GIVEN_NAME, FULL_NAME_NATIVE)
    time.sleep(0.1)

    select_other_names(wait, driver, data.get("OTHER_NAME"))

    if OTHER_NAMES == "N":
        other_names_list = []
        i = 1
        while True:
            s = data.get(f"OTHER_SURNAME_{i}")
            g = data.get(f"OTHER_GIVEN_NAME_{i}")
            if s and g:
                other_names_list.append({"surname": s, "given": g})
                i += 1
            else:
                break
        if other_names_list:
            fill_other_names(wait, driver, other_names_list)

    select_telecode_no(wait, driver)

    if data.get("GENDER"):
        select_gender(wait, driver, data["GENDER"])

    if data.get("MARITAL_STATUS"):
        select_marital_status(wait, driver, data["MARITAL_STATUS"])

    fill_date_of_birth(wait, driver, data["BIRTH_DAY"], data["BIRTH_MONTH"], data["BIRTH_YEAR"])
    fill_place_of_birth(wait, driver, data["BIRTH_CITY"])
    select_birth_country(wait, driver, data["BIRTH_COUNTRY"])
    fill_birth_state(wait, driver, data.get("BIRTH_STATE"))

    save_and_go_next(wait, driver)
    force_continue_application(wait, driver)
    wait_and_click_next_personal2(wait, driver)

    # ─── Personal 2 ───────────────────────────────────────────
    select_nationality(wait, driver, data["NATIONALITY"])
    select_other_nationality(wait, driver, data["OTHER_NATIONALITY"])

    if data["OTHER_NATIONALITY"] == "YES":
        select_other_nationality_yes(wait, driver)
        index = 1
        while True:
            key = f"OTHER_NATIONALITY_{index}_COUNTRY"
            if key not in data:
                break
            fill_single_other_nationality(
                wait, driver,
                data[f"OTHER_NATIONALITY_{index}_COUNTRY"],
                data[f"OTHER_NATIONALITY_{index}_HAS_PASSPORT"],
                data.get(f"OTHER_NATIONALITY_{index}_PASSPORT_NUMBER"),
            )
            if f"OTHER_NATIONALITY_{index+1}_COUNTRY" in data:
                click_add_another_other_nationality(wait, driver)
            index += 1

    fill_permanent_resident_section(wait, driver, data)
    fill_personal2_ids(wait, driver, data)
    click_save_personal2(wait, driver)
    click_continue_application(wait, driver)
    click_next_travel(wait, driver)

    # ─── Travel ───────────────────────────────────────────────
    select_purpose_of_trip(wait, driver, data.get("PURPOSE_OF_TRIP"))
    if data.get("PURPOSE_OF_TRIP_SUB"):
        select_purpose_subcategory_if_exists(wait, driver, data["PURPOSE_OF_TRIP_SUB"])

    soru_mevcut = select_specific_travel(wait, driver, data.get("HAS_SPECIFIC_TRAVEL_PLANS", "NO"))
    if soru_mevcut:
        cevap = data.get("HAS_SPECIFIC_TRAVEL_PLANS", "NO").upper()
        if cevap == "YES":
            fill_travel_details(wait, driver, data)
        else:
            fill_intended_arrival_date(wait, driver, data)
            fill_intended_length_of_stay(wait, driver, data)
    else:
        fill_intended_arrival_date(wait, driver, data)
        fill_intended_length_of_stay(wait, driver, data)

    fill_us_address(wait, driver, data)
    fill_payer_info(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Travel Companions ────────────────────────────────────
    data = parse_travel_companions(data)
    fill_travel_companions(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Previous US Travel / Visa ────────────────────────────
    fill_previous_us_travel(wait, driver, data)
    fill_previous_visa(wait, driver, data)
    fill_prev_visa_refused(wait, driver, data)
    fill_iv_petition(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Address & Phone ──────────────────────────────────────
    fill_home_address(wait, driver, data)
    fill_mailing_address(wait, driver, data)
    fill_phone_numbers(wait, driver, data)
    fill_additional_phone(wait, driver, data)
    fill_email(wait, driver, data)
    fill_additional_email(wait, driver, data)
    fill_social_media(wait, driver, data)
    fill_additional_social_media(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Passport ─────────────────────────────────────────────
    fill_passport_info(wait, driver, data)
    fill_lost_passport(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── US Point of Contact ──────────────────────────────────
    fill_us_point_of_contact(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Family ───────────────────────────────────────────────
    fill_parents_info(wait, driver, data)
    fill_us_immediate_relatives(wait, driver, data)
    fill_us_other_relatives(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Spouse ───────────────────────────────────────────────
    marital_status = data.get("MARITAL_STATUS", "").upper().strip()
    if marital_status in ("MARRIED", "COMMON-LAW MARRIAGE", "DIVORCED", "WIDOWED"):
        print(f"💍 {marital_status} — eş sayfası dolduruluyor")
        auto_fill_family_page(wait, driver, data)
        if _scn(wait, driver, on_photo_page): return
    else:
        print(f"ℹ️ {marital_status} — eş sayfası atlanıyor")

    # ─── Present Occupation (RESUME FIX) ──────────────────────
    try:
        wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlPresentOccupation")
        ))
        _fill_present_occupation_resume(driver, wait, data)
        click_save(wait, driver)
        if _check_photo_page(driver):
            print("📸 Fotoğraf sayfası tespit edildi (occupation save sonrası)")
            if on_photo_page: on_photo_page()
            return
        click_continue_applications(wait, driver)
        if _check_photo_page(driver):
            print("📸 Fotoğraf sayfası tespit edildi (occupation continue sonrası)")
            if on_photo_page: on_photo_page()
            return
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Present Occupation sayfası bulunamadı, atlanıyor.")

    try:
        short_wait = WebDriverWait(driver, 3)
        click_nexts(short_wait, driver, label="Travel Companions")
        if _check_photo_page(driver):
            print("📸 Fotoğraf sayfası tespit edildi (occupation next sonrası)")
            if on_photo_page: on_photo_page()
            return
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Next butonu bulunamadı, atlanıyor.")
    except Exception as e:
        print(f"⚠️ Next hatası: {e}")

    # ─── Previous Employment / Education ──────────────────────
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblPreviouslyEmployed_0")
        ))
        fill_previous_employment(wait, driver, data)
        fill_other_education(wait, driver, data)
        if _scn(wait, driver, on_photo_page): return
        print("✅ Previous Employment/Education tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Previous Employment/Education sayfası yok, atlanıyor.")

    # ─── Additional Work / Education (RESUME FIX) ─────────────
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_0")
        ))
        _fill_additional_work_education_resume(driver, wait, data)
        if _scn(wait, driver, on_photo_page): return
        print("✅ Additional Work/Education tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Additional Work/Education sayfası yok, atlanıyor.")

    # ─── Health & Security ────────────────────────────────────
    fill_health_security_section(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Criminal & Security ──────────────────────────────────
    fill_criminal_security_section(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Security Violations ──────────────────────────────────
    fill_security_violations_section(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Removal / Immigration ────────────────────────────────
    fill_removal_immigration_section(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Misc Immigration Violations ──────────────────────────
    fill_misc_immigration_violations_section(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # ─── Student POC ──────────────────────────────────────────
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlStudentAddPOC_ctl00_tbxADD_POC_SURNAME")
        ))
        try:
            fill_student_poc_sections(wait, driver, data)
        except Exception as e:
            print(f"⚠️ Student POC doldurulamadı, devam ediliyor: {e}")
        if _scn(wait, driver, on_photo_page): return
        print("✅ Student POC tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Student POC sayfası yok (B1/B2), atlanıyor.")

    # ─── SEVIS & School ───────────────────────────────────────
    fill_sevis_and_school_if_needed(wait, driver, data)
    if _scn(wait, driver, on_photo_page): return

    # Buraya kadar geldiyse fotoğraf sayfası hiç tespit edilmedi
    print("⚠️ Fotoğraf sayfası tespit edilemedi, flow tamamlandı.")
    print("🎉 DS-160 RESUME FLOW TAMAMLANDI")