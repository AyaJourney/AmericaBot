import re
import time
from selenium.webdriver.support.ui import WebDriverWait, Select as SeleniumSelect
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from form_fill import (
    fill_basic_identity_form,
    wait_after_state_na,
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
# FALLBACK
# =====================================================
def enrich_data_with_fallbacks(data: dict) -> dict:
    d = data.copy()

    def fb(key, value):
        if not str(d.get(key, "")).strip():
            d[key] = value

    # ─── YES/NO alanlar ───────────────────────────────────────
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

    # ─── Mailing ──────────────────────────────────────────────
    fb("MAILING_SAME_AS_HOME", "YES")
    fb("MAILING_ADDRESS",      "XXXXXXXXXX")
    fb("MAILING_CITY",         "XXXXXXXXXX")
    fb("MAILING_COUNTRY",      "Turkey")

    # ─── Telefon ──────────────────────────────────────────────
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

    # ─── Email ────────────────────────────────────────────────
    for f in ["EMAIL", "ADDITIONAL_EMAIL1", "PAYER_EMAIL", "US_POC_EMAIL"]:
        fb(f, "noreply@example.com")

    # ─── Genel text alanlar ───────────────────────────────────
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

    # ─── US POC State ─────────────────────────────────────────
    fb("US_POC_STATE", "New York")
    fb("NATIONALITY", "Turkey")
    # ─── Pasaport ─────────────────────────────────────────────
    fb("PASSPORT_NUMBER",      "U123124124")
    fb("PASSPORT_ISSUE_DATE",  "01-JAN-2020")
    fb("PASSPORT_EXPIRY_DATE", "01-JAN-2030")

    # ─── Country → Turkey ─────────────────────────────────────
    fb("BIRTH_COUNTRY",              "Turkey")
    fb("HOME_COUNTRY",               "Turkey")
    fb("PASSPORT_ISSUED_COUNTRY",    "Turkey")
    fb("PASSPORT_ISSUED_IN_COUNTRY", "Turkey")
    fb("EMP_SCH_COUNTRY",            "Turkey")
    fb("US_POC_COUNTRY",             "Turkey")
    fb("PAYER_COUNTRY",              "Turkey")

    # ─── Dil → Turkish ───────────────────────────────────────
    fb("LANGUAGES", "Turkish")

    # ─── Özel fallback'ler ────────────────────────────────────
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

    print("✅ enrich_data_with_fallbacks tamamlandı")
    return d


# =====================================================
# PRESENT OCCUPATION – RESUME FIX
# =====================================================
def _fill_present_occupation_resume(driver, wait, data):
    """
    Resume senaryosunda dropdown zaten seçili olabilir.
    Aynı değer tekrar seçilirse postback tetiklenmez → staleness_of timeout.
    Bu fonksiyon: zaten seçiliyse JS ile postback'i zorla tetikler.
    """
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

    # Explain alanı gerekiyorsa doldur
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
    """
    Radio'yu JS ile force-click yapar.
    Zaten seçili olsa bile checked=true + click() + dispatchEvent çalıştırır.
    """
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
            match = re.search(r"__doPostBack\([^)]+\)", onclick)
            if match:
                driver.execute_script(match.group(0) + ";")
    time.sleep(1.0)


def _fill_additional_work_education_resume(driver, wait, data):
    """
    Resume senaryosu için Additional Work/Education sayfası.
    Sayfa dolu ise language input kontrol edilir, doluysa atlanır.
    Boşsa JS force-click ile doldurulur.
    """
    print("📋 Additional Work/Education (RESUME) kontrol ediliyor...")

    # Language input dolu mu kontrol et
    try:
        lang_el = driver.find_element(
            By.ID,
            "ctl00_SiteContentPlaceHolder_FormView1_dtlLANGUAGES_ctl00_tbxLANGUAGE_NAME"
        )
        lang_val = lang_el.get_attribute("value").strip()
        if lang_val:
            print(f"ℹ️ Sayfa zaten dolu (Language: {lang_val}), atlanıyor.")
            return
    except Exception:
        pass

    print("📝 Sayfa boş, dolduruluyor...")

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

    # 2. LANGUAGES
    langs = [x.strip() for x in data.get("LANGUAGES", "Turkish").split(",") if x.strip()]
    if not langs:
        langs = ["Turkish"]
    base = "ctl00_SiteContentPlaceHolder_FormView1_dtlLANGUAGES_ctl"
    for i, lang in enumerate(langs):
        idx    = f"{i:02d}"
        tbx_id = f"{base}{idx}_tbxLANGUAGE_NAME"
        add_id = f"{base}{idx}_InsertButtonLANGUAGE"
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
    print(f"✅ Languages: {langs}")

    # 3. COUNTRIES VISITED
    visited = data.get("COUNTRIES_VISITED", "NO").upper()
    _js_click_radio(driver, wait,
        "ctl00_SiteContentPlaceHolder_FormView1_rblCOUNTRIES_VISITED_IND_0" if visited == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblCOUNTRIES_VISITED_IND_1",
        do_postback=(visited == "YES")
    )

    # 4. ORGANIZATION
    org = data.get("ORGANIZATION", "NO").upper()
    _js_click_radio(driver, wait,
        "ctl00_SiteContentPlaceHolder_FormView1_rblORGANIZATION_IND_0" if org == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblORGANIZATION_IND_1",
        do_postback=(org == "YES")
    )

    # 5. SPECIALIZED SKILLS
    skills = data.get("SPECIALIZED_SKILLS", "NO").upper()
    _js_click_radio(driver, wait,
        "ctl00_SiteContentPlaceHolder_FormView1_rblSPECIALIZED_SKILLS_IND_0" if skills == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblSPECIALIZED_SKILLS_IND_1",
        do_postback=False
    )

    # 6. MILITARY SERVICE
    mil = data.get("MILITARY_SERVICE", "NO").upper()
    _js_click_radio(driver, wait,
        "ctl00_SiteContentPlaceHolder_FormView1_rblMILITARY_SERVICE_IND_0" if mil == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblMILITARY_SERVICE_IND_1",
        do_postback=(mil == "YES")
    )

    # 7. INSURGENT ORG
    insurgent = data.get("INSURGENT_ORG", "NO").upper()
    _js_click_radio(driver, wait,
        "ctl00_SiteContentPlaceHolder_FormView1_rblINSURGENT_ORG_IND_0" if insurgent == "YES"
        else "ctl00_SiteContentPlaceHolder_FormView1_rblINSURGENT_ORG_IND_1",
        do_postback=False
    )

    print("✅ Additional Work/Education (RESUME) tamamlandı")


# =====================================================
# MAIN RESUME FLOW
# =====================================================
def fill_ds160_resume_application(driver, wait, data):
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
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Travel Companions ────────────────────────────────────
    data = parse_travel_companions(data)
    fill_travel_companions(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Previous US Travel / Visa ────────────────────────────
    fill_previous_us_travel(wait, driver, data)
    fill_previous_visa(wait, driver, data)
    fill_prev_visa_refused(wait, driver, data)
    fill_iv_petition(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Address & Phone ──────────────────────────────────────
    fill_home_address(wait, driver, data)
    fill_mailing_address(wait, driver, data)
    fill_phone_numbers(wait, driver, data)
    fill_additional_phone(wait, driver, data)
    fill_email(wait, driver, data)
    fill_additional_email(wait, driver, data)
    fill_social_media(wait, driver, data)
    fill_additional_social_media(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Passport ─────────────────────────────────────────────
    fill_passport_info(wait, driver, data)
    fill_lost_passport(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── US Point of Contact ──────────────────────────────────
    fill_us_point_of_contact(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Family ───────────────────────────────────────────────
    fill_parents_info(wait, driver, data)
    fill_us_immediate_relatives(wait, driver, data)
    fill_us_other_relatives(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Spouse ───────────────────────────────────────────────
    marital_status = data.get("MARITAL_STATUS", "").upper().strip()
    if marital_status in ("MARRIED", "COMMON-LAW MARRIAGE", "DIVORCED", "WIDOWED"):
        print(f"💍 {marital_status} — eş sayfası dolduruluyor")
        auto_fill_family_page(wait, driver, data)
        click_save(wait, driver)
        click_continue_applications(wait, driver)
        click_nexts(wait, driver, label="Travel Companions")
    else:
        print(f"ℹ️ {marital_status} — eş sayfası atlanıyor")

    # ─── Present Occupation (RESUME FIX) ──────────────────────
    try:
        wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_ddlPresentOccupation")
        ))
        _fill_present_occupation_resume(driver, wait, data)
        click_save(wait, driver)
        click_continue_applications(wait, driver)
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Present Occupation sayfası bulunamadı, atlanıyor.")

    try:
        short_wait = WebDriverWait(driver, 3)
        click_nexts(short_wait, driver, label="Travel Companions")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Next butonu bulunamadı, atlanıyor.")
    except Exception as e:
        print(f"⚠️ Next hatası: {e}")

    # ─── Previous Employment / Education ──────────────────────
    # rblPreviouslyEmployed her zaman sayfada var (NO seçili olsa bile)
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblPreviouslyEmployed_0")
        ))
        fill_previous_employment(wait, driver, data)
        fill_other_education(wait, driver, data)
        click_save(wait, driver)
        click_continue_applications(wait, driver)
        click_nexts(wait, driver, label="Travel Companions")
        print("✅ Previous Employment/Education tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Previous Employment/Education sayfası yok, atlanıyor.")

    # ─── Additional Work / Education (RESUME FIX) ─────────────
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_0")
        ))
        _fill_additional_work_education_resume(driver, wait, data)
        click_save(wait, driver)
        click_continue_applications(wait, driver)
        click_nexts(wait, driver, label="Travel Companions")
        print("✅ Additional Work/Education tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Additional Work/Education sayfası yok, atlanıyor.")

    # ─── Health & Security ────────────────────────────────────
    fill_health_security_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Criminal & Security ──────────────────────────────────
    fill_criminal_security_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Security Violations ──────────────────────────────────
    fill_security_violations_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Removal / Immigration ────────────────────────────────
    fill_removal_immigration_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Misc Immigration Violations ──────────────────────────
    fill_misc_immigration_violations_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── Student POC ──────────────────────────────────────────
    fill_student_poc_sections(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # ─── SEVIS & School ───────────────────────────────────────
    fill_sevis_and_school_if_needed(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    # upload_photo_by_fullname(wait, driver, data)

    print("🎉 DS-160 RESUME FLOW TAMAMLANDI")