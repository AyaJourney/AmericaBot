import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from auto_fix import fix_country_select, fix_validation_errors, check_validation_errors
from form_fill import (
    fill_basic_identity_form,
    safe_fill_page,
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
)


def _check_photo_page(driver) -> bool:
    try:
        el = driver.find_element(By.ID, "ctl00_SiteContentPlaceHolder_btnUploadPhoto")
        return el.is_displayed()
    except Exception:
        return False


def _save_continue_next(wait, driver, label="next"):
    from auto_fix import fix_validation_errors, check_validation_errors

    click_save(wait, driver)
    time.sleep(1.5)

    # Validation hatası var mı?
    errors = check_validation_errors(driver)
    if errors:
        print(f"⚠️ {len(errors)} validation hatası, otomatik düzeltiliyor...")
        fix_validation_errors(driver, wait, {})
        time.sleep(1)
        click_save(wait, driver)
        time.sleep(1.5)

    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label=label)

def fill_ds160_full_application(driver, wait, data, on_personal1_saved=None, on_photo_page=None):
    print(f"DEBUG PRESENT_OCCUPATION: {data.get('PRESENT_OCCUPATION')}")
    print(f"DEBUG PRESENT_OCCUPATION_EXPLAIN: {data.get('PRESENT_OCCUPATION_EXPLAIN')}")
    print("🧪 DS-160 FULL FLOW BAŞLADI")
    from ds160_resume_flow import enrich_data_with_fallbacks
    data = enrich_data_with_fallbacks(data)
    print(f"🎓 EDU_00_SCHOOL_NAME: {data.get('EDU_00_SCHOOL_NAME', 'YOK')}")
    print(f"🎓 EDU_01_SCHOOL_NAME: {data.get('EDU_01_SCHOOL_NAME', 'YOK')}")
    print(f"🎓 OTHER_EDUCATION: {data.get('OTHER_EDUCATION', 'YOK')}")
    # ─── Personal 1 ───────────────────────────────────────────
    SURNAME          = data.get("SURNAME", "")
    GIVEN_NAME       = data.get("GIVEN_NAME", "")
    FULL_NAME_NATIVE = data.get("FULL_NAME_NATIVE", "")
    OTHER_NAMES      = data.get("OTHER_NAMES", "N").upper()

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

    if on_personal1_saved:
        on_personal1_saved()

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
    _save_continue_next(wait, driver, label="Travel Companions")

    # ─── Travel Companions ────────────────────────────────────
    data = parse_travel_companions(data)
    fill_travel_companions(wait, driver, data)
    _save_continue_next(wait, driver, label="Previous US Travel")

    # ─── Previous US Travel / Visa ────────────────────────────
    fill_previous_us_travel(wait, driver, data)
    fill_previous_visa(wait, driver, data)
    fill_prev_visa_refused(wait, driver, data)
    fill_iv_petition(wait, driver, data)
    _save_continue_next(wait, driver, label="Address Phone")

    # ─── Address & Phone ──────────────────────────────────────
    fill_home_address(wait, driver, data)
    fill_mailing_address(wait, driver, data)
    fill_phone_numbers(wait, driver, data)
    fill_additional_phone(wait, driver, data)
    fill_email(wait, driver, data)
    fill_additional_email(wait, driver, data)
    fill_social_media(wait, driver, data)
    fill_additional_social_media(wait, driver, data)
    _save_continue_next(wait, driver, label="Passport")

    # ─── Passport ─────────────────────────────────────────────
    fill_passport_info(wait, driver, data)
    fill_lost_passport(wait, driver, data)
    _save_continue_next(wait, driver, label="US POC")

    # ─── US Point of Contact ──────────────────────────────────
    fill_us_point_of_contact(wait, driver, data)
    _save_continue_next(wait, driver, label="Family")

    # ─── Family ───────────────────────────────────────────────
    fill_parents_info(wait, driver, data)
    fill_us_immediate_relatives(wait, driver, data)
    fill_us_other_relatives(wait, driver, data)
    _save_continue_next(wait, driver, label="Spouse")

    # ─── Spouse ───────────────────────────────────────────────
    marital_status = data.get("MARITAL_STATUS", "").upper().strip()
    if marital_status in ("MARRIED", "COMMON-LAW MARRIAGE"):
        print(f"💍 {marital_status} — eş bilgileri dolduruluyor")
        auto_fill_family_page(wait, driver, data)
        _save_continue_next(wait, driver, label="Occupation")

    elif marital_status in ("DIVORCED", "WIDOWED"):
        print(f"💍 {marital_status} — eski eş bilgileri dolduruluyor")
        auto_fill_family_page(wait, driver, data)
        _save_continue_next(wait, driver, label="Occupation")

    else:
        # SINGLE veya diğer — sayfa yine de çıkabilir
        print(f"ℹ️ {marital_status} — spouse sayfası kontrol ediliyor")
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.ID,
                    "ctl00_SiteContentPlaceHolder_FormView1_tbxSpouseSurname"
                ))
            )
            # Spouse sayfası çıktı ama SINGLE — sadece geç
            print("ℹ️ Spouse sayfası mevcut (SINGLE) — Next ile geçiliyor")
            _save_continue_next(wait, driver, label="Occupation")
        except TimeoutException:
            # Spouse sayfası yok — direkt occupation
            print("ℹ️ Spouse sayfası yok — atlanıyor")

    # ─── Present Occupation ───────────────────────────────────
    fill_present_occupation_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)

    try:
        click_nexts(WebDriverWait(driver, 3), driver, label="Prev Employment")
        print("✅ Occupation next geçildi.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Occupation next yok, atlanıyor.")

    # ─── Previous Employment / Education ──────────────────────
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblPreviouslyEmployed_0")
        ))
        fill_previous_employment(wait, driver, data)
        fill_other_education(wait, driver, data)
        _save_continue_next(wait, driver, label="Additional Work")
        print("✅ Previous Employment/Education tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Previous Employment/Education sayfası yok, atlanıyor.")

    # ─── Additional Work / Education ──────────────────────────
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_0")
        ))
        fill_additional_work_education_section(wait, driver, data)
        _save_continue_next(wait, driver, label="Health")
        print("✅ Additional Work/Education tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Additional Work/Education sayfası yok, atlanıyor.")

    # ─── Health & Security ────────────────────────────────────
    fill_health_security_section(wait, driver, data)
    _save_continue_next(wait, driver, label="Criminal")

    # ─── Criminal & Security ──────────────────────────────────
    fill_criminal_security_section(wait, driver, data)
    _save_continue_next(wait, driver, label="Security Violations")

    # ─── Security Violations ──────────────────────────────────
    fill_security_violations_section(wait, driver, data)
    _save_continue_next(wait, driver, label="Removal")

    # ─── Removal / Immigration ────────────────────────────────
    fill_removal_immigration_section(wait, driver, data)
    _save_continue_next(wait, driver, label="Misc Immigration")

    # ─── Misc Immigration Violations ──────────────────────────
    fill_misc_immigration_violations_section(wait, driver, data)
    _save_continue_next(wait, driver, label="Student POC")

    # ─── Student POC ──────────────────────────────────────────
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "ctl00_SiteContentPlaceHolder_FormView1_dtlStudentAddPOC_ctl00_tbxADD_POC_SURNAME")
        ))
        try:
            fill_student_poc_sections(wait, driver, data)
        except Exception as e:
            print(f"⚠️ Student POC doldurulamadı, devam ediliyor: {e}")
        _save_continue_next(wait, driver, label="SEVIS")
        print("✅ Student POC tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ Student POC sayfası yok (B1/B2), atlanıyor.")

    # ─── SEVIS & School ───────────────────────────────────────
    try:
        fill_sevis_and_school_if_needed(wait, driver, data)
        _save_continue_next(wait, driver, label="Photo")
        print("✅ SEVIS tamamlandı.")
    except Exception as e:
        print(f"ℹ️ SEVIS sayfası yok veya hata, atlanıyor: {e}")

    # ─── Fotoğraf Sayfası ─────────────────────────────────────
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.ID, "ctl00_SiteContentPlaceHolder_btnUploadPhoto")
            )
        )
        print("📸 Fotoğraf sayfasına gelindi")
    except Exception:
        print("⚠️ Fotoğraf butonu bulunamadı")

    if on_photo_page:
        on_photo_page()

    print("🎉 DS-160 FULL FORM TAMAMLANDI")