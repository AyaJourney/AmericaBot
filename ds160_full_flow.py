from concurrent.futures import wait
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# form_fill importları – SENDE NE VARSA AYNI
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
    click_nexts,
    click_continue_applications,
    click_save,
    # fill_payer_address,
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
    fill_esta_denial,
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
    # fill_student_additional_poc_if_needed,
    fill_sevis_and_school_if_needed,
    upload_photo_by_fullname,
)

# =====================================================
# DS-160 FULL FORM FLOW (BARCODE SONRASI)
# =====================================================
def fill_ds160_full_application(driver, wait, data, on_personal1_saved=None, on_photo_page=None):
    print("🧪 DS-160 FULL FLOW BAŞLADI")

    SURNAME = data.get("SURNAME", "")
    GIVEN_NAME = data.get("GIVEN_NAME", "")
    FULL_NAME_NATIVE = data.get("FULL_NAME_NATIVE", "")
    OTHER_NAMES = data.get("OTHER_NAMES", "N").upper()

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
    # ... geri kalanı aynı

    # =====================================================
    # NATIONALITY
    # =====================================================
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
                wait,
                driver,
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

    # =====================================================
    # TRAVEL
    # =====================================================
    select_purpose_of_trip(wait, driver, data.get("PURPOSE_OF_TRIP"))
    if data.get("PURPOSE_OF_TRIP_SUB"):
        select_purpose_subcategory_if_exists(wait, driver, data["PURPOSE_OF_TRIP_SUB"])

    # 1. Fonksiyonu çağır ve sonucunu al
    # 1. Önce soruyu seçmeyi dene ve sonucunu bir değişkene ata
    soru_mevcut = select_specific_travel(wait, driver, data.get("HAS_SPECIFIC_TRAVEL_PLANS", "NO"))

# 2. EĞER SORU SAYFADA VARSA (soru_mevcut == True), detayları doldurmaya çalış
    if soru_mevcut:
    # 'cevap' değişkenini sadece soru varsa tanımlıyoruz
        cevap = data.get("HAS_SPECIFIC_TRAVEL_PLANS", "NO").upper()
    
        if cevap == "YES":
            fill_travel_details(wait, driver, data)
        elif cevap == "NO":
            fill_intended_arrival_date(wait, driver, data)
            fill_intended_length_of_stay(wait, driver, data)
    else:
    # Soru yoksa bu blok tamamen atlanır ve hata almadan bir sonraki soruya geçer
            fill_intended_arrival_date(wait, driver, data)
            fill_intended_length_of_stay(wait, driver, data)
    fill_us_address(wait, driver, data)
    fill_payer_info(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    data = parse_travel_companions(data)
    fill_travel_companions(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    # =====================================================
    # DEVAMI – SENİN KODUNDAKİ SIRA BOZULMADI
    # =====================================================
    fill_previous_us_travel(wait, driver, data)
    fill_previous_visa(wait, driver, data)
    fill_prev_visa_refused(wait, driver, data)
    fill_iv_petition(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    # fill_esta_denial(wait, driver, data)
    
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
    fill_passport_info(wait, driver, data)
    fill_lost_passport(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    fill_us_point_of_contact(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    fill_parents_info(wait, driver, data)
    fill_us_immediate_relatives(wait, driver, data)
    fill_us_other_relatives(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")

    marital_status = data.get("MARITAL_STATUS", "").upper().strip()
    if marital_status in ("MARRIED", "COMMON-LAW MARRIAGE", "DIVORCED", "WIDOWED"):
        print(f"💍 {marital_status} — eş sayfası dolduruluyor")
        auto_fill_family_page(wait, driver, data)
        click_save(wait, driver)
        click_continue_applications(wait, driver)
        click_nexts(wait, driver, label="Travel Companions")
    else:
        print(f"ℹ️ {marital_status} — eş sayfası atlanıyor")
   # 1. Mevcut bölümü doldur ve kaydet
    fill_present_occupation_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)

# 2. "Travel Companions" sayfasına geçiş (VARSA YAP, YOKSA GEÇ)
    try:
        print("🔍 'Travel Companions' aşaması kontrol ediliyor...")
    # Kısa bir bekleme süresi tanımlıyoruz (örneğin 3 saniye)
    # Eğer buton 3 saniye içinde gelmezse sayfada yoktur.
        short_wait = WebDriverWait(driver, 3)
    
    # click_nexts fonksiyonunun içinde wait.until varsa, 
    # fonksiyonu çağırmadan önce butonun varlığını burada kontrol edebiliriz:
        click_nexts(short_wait, driver, label="Travel Companions")
        print("✅ 'Travel Companions' sayfasına geçildi.")

    except (TimeoutException, NoSuchElementException):
        print("ℹ️ 'Travel Companions' adımı bu akışta görünmedi veya zaten geçildi, atlanıyor.")
    except Exception as e:
        print(f"⚠️ 'Travel Companions' geçilirken beklenmedik bir durum oluştu: {e}")

# Kod buradan itibaren akmaya devam eder...


# 1. PREVIOUS EMPLOYMENT & EDUCATION BÖLÜMÜ
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
        print("ℹ️ 'Previous Employment/Education' sayfası bu başvuru için mevcut değil, geçiliyor.")

# ---------------------------------------------------------

# 2. ADDITIONAL WORK / EDUCATION / TRAINING BÖLÜMÜ
    try:
        print("🔍 'Additional Work/Education' bölümü kontrol ediliyor...")
    # Bu sayfaya özgü bir element kontrolü (Örn: 'Have you traveled to any countries...' sorusu)
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "ctl00_SiteContentPlaceHolder_FormView1_rblCLAN_TRIBE_IND_0")))
    
        fill_additional_work_education_section(wait, driver, data)
        click_save(wait, driver)
        click_continue_applications(wait, driver)
    # Bir sonraki aşamaya geç
        click_nexts(wait, driver, label="Travel Companions")
        print("✅ Additional Work/Education tamamlandı.")
    except (TimeoutException, NoSuchElementException):
        print("ℹ️ 'Additional Work/Education' sayfası bulunamadı, geçiliyor.")
    fill_health_security_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    fill_criminal_security_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    fill_security_violations_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    fill_removal_immigration_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    fill_misc_immigration_violations_section(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    fill_student_poc_sections(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    fill_sevis_and_school_if_needed(wait, driver, data)
    click_save(wait, driver)
    click_continue_applications(wait, driver)
    click_nexts(wait, driver, label="Travel Companions")
    # upload_photo_by_fullname(wait, driver, data)
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "ctl00_SiteContentPlaceHolder_btnUploadPhoto"))
        )
        print("📸 Fotoğraf sayfasına gelindi")
    except Exception:
        print("⚠️ Fotoğraf butonu bulunamadı, devam ediliyor")

    if on_photo_page:
        on_photo_page()

    print("🎉 DS-160 FULL FORM TAMAMLANDI")