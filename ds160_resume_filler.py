def enrich_data_with_fallbacks(data: dict) -> dict:
    """
    Resume senaryosunda eksik/boş alanları otomatik fallback değerlerle doldurur.
    - YES/NO alanlar → "NO"
    - Phone alanlar → "5555555555"
    - Email alanlar → "noreply@example.com"
    - Diğer text → "XXXXXXXXXX"
    """
    d = data.copy()

    def fb(key, value):
        """Sadece boş/eksik ise doldur."""
        if not str(d.get(key, "")).strip():
            d[key] = value

    # ─── YES/NO ALANLAR ───────────────────────────────────────
    yesno_fields = [
        "OTHER_NAME", "OTHER_NATIONALITY", "PERMANENT_RESIDENT_OTHER_COUNTRY",
        "PREV_US_TRAVEL", "US_DRIVER_LICENSE", "PREV_VISA",
        "PREV_VISA_SAME_TYPE", "PREV_VISA_SAME_COUNTRY", "PREV_VISA_TEN_PRINTED",
        "PREV_VISA_LOST", "PREV_VISA_CANCELLED", "PREV_VISA_REFUSED",
        "IV_PETITION", "ESTA_DENIED",
        "MAILING_SAME_AS_HOME", "HAS_ADDITIONAL_PHONE", "HAS_ADDITIONAL_EMAIL",
        "ADDITIONAL_SOCIAL", "PASSPORT_LOST",
        "TRAVEL_COMPANIONS", "PREV_EMPLOYED",
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

    # ─── PHONE ALANLAR ────────────────────────────────────────
    phone_fields = [
        "PRIMARY_PHONE", "MOBILE_PHONE", "WORK_PHONE",
        "ADDITIONAL_PHONE_NUM", "EMP_SCH_PHONE",
        "PAYER_PHONE", "PAYER_COMPANY_PHONE",
        "US_POC_PHONE",
    ]
    for f in phone_fields:
        fb(f, "5555555555")

    # ─── EMAIL ALANLAR ────────────────────────────────────────
    email_fields = [
        "EMAIL", "ADDITIONAL_EMAIL1",
        "PAYER_EMAIL", "US_POC_EMAIL",
    ]
    for f in email_fields:
        fb(f, "noreply@example.com")

    # ─── TEXT ALANLAR ─────────────────────────────────────────
    text_fields = [
        # Kimlik
        "SURNAME", "GIVEN_NAME", "FULL_NAME_NATIVE",
        "BIRTH_CITY", "BIRTH_COUNTRY", "BIRTH_STATE",
        "NATIONALITY",
        # Pasaport
        "PASSPORT_TYPE", "PASSPORT_NUMBER", "PASSPORT_ISSUED_COUNTRY",
        "PASSPORT_ISSUED_CITY", "PASSPORT_ISSUED_IN_COUNTRY",
        "PASSPORT_ISSUE_DATE",
        # Adres
        "HOME_ADDRESS", "HOME_CITY", "HOME_COUNTRY",
        "US_ADDRESS1", "US_CITY", "US_STATE",
        # İş/Okul
        "PRESENT_OCCUPATION",
        "EMP_SCH_NAME", "EMP_SCH_ADDR1", "EMP_SCH_CITY",
        "EMP_SCH_COUNTRY", "EMP_SCH_START_DATE", "EMP_DUTIES",
        # Seyahat
        "PURPOSE_OF_TRIP",
        "INTENDED_ARRIVAL_DAY", "INTENDED_ARRIVAL_MONTH", "INTENDED_ARRIVAL_YEAR",
        "TRAVEL_LOS_VALUE",
        # POC
        "US_POC_ADDR1", "US_POC_CITY",
        # Aile
        "FATHER_SURNAME", "FATHER_GIVEN",
        "MOTHER_SURNAME", "MOTHER_GIVEN",
        # Sosyal medya
        "SOCIAL_MEDIA",
        # Diller
        "LANGUAGES",
        # Payer
        "PAYER_TYPE",
    ]
    for f in text_fields:
        fb(f, "XXXXXXXXXX")

    # ─── ÖZEL FALLBACK'LER ────────────────────────────────────
    fb("TRAVEL_LOS_UNIT",   "D")          # Days
    fb("MARITAL_STATUS",    "SINGLE")
    fb("GENDER",            "M")
    fb("BIRTH_DAY",         "1")
    fb("BIRTH_MONTH",       "JAN")
    fb("BIRTH_YEAR",        "1990")
    fb("PAYER_TYPE",        "SELF")
    fb("SOCIAL_MEDIA",      "NONE")
    fb("LANGUAGES",         "ENGLISH")
    fb("PREV_US_VISITS",    "0")
    fb("US_POC_RELATION",   "OTHER")
    fb("US_STATE",          "NY")
    fb("PASSPORT_TYPE",     "REGULAR")
    fb("PRESENT_OCCUPATION","NOT_EMPLOYED")
    occ = str(d.get("PRESENT_OCCUPATION", "")).strip().upper()
    if not str(d.get("PRESENT_OCCUPATION_EXPLAIN", "")).strip():
        if occ == "NOT_EMPLOYED":
            d["PRESENT_OCCUPATION_EXPLAIN"] = "NOT EMPLOYED"
        elif occ == "OTHER":
            d["PRESENT_OCCUPATION_EXPLAIN"] = "OTHER OCCUPATION"
        else:
            d["PRESENT_OCCUPATION_EXPLAIN"] = "NOT EMPLOYED"
    fb("OTHER_NAME",        "NO")
    fb("PAYER_ADDRESS1",  "XXXXXXXXXX")
    fb("PAYER_CITY",      "XXXXXXXXXX")
    fb("PAYER_COUNTRY",   "TURKEY")
    fb("PAYER_COMPANY_ADDRESS1", "XXXXXXXXXX")
    fb("PAYER_COMPANY_CITY",     "XXXXXXXXXX")
    fb("PAYER_COMPANY_COUNTRY",  "TURKEY")
    fb("PAYER_COMPANY_RELATIONSHIP", "EMPLOYER")
    fb("PAYER_COMPANY_NAME", "XXXXXXXXXX")
    fb("PAYER_COMPANY_PHONE", "5555555555")

    print("✅ enrich_data_with_fallbacks tamamlandı")
    return d