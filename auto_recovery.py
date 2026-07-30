# -*- coding: utf-8 -*-
"""
auto_recovery.py — DS-160 GENEL validation recovery

Mantik:
  CEAC "Next"te hata verince, sabit hata-listesi yerine
  Page_Validators dizisinden isvalid=false olan TUM input'lari bulur.
  Her hatali input icin sirayla dener:
    1) input_id + "_NA" (Do Not Know / Does Not Apply) kutusu → isaretle
    2) tipe gore doldur (radio→NO, tarih→gecerli tarih, dropdown→ilk gecerli, text→N/A)
  Boylece HER input'a calisir, yeni hata tipinde elle kod eklemeye gerek kalmaz.

Kullanim (form_fill.py icinde):
    from auto_recovery import fix_active_validators
    ...
    genel = fix_active_validators(driver)
    if genel:
        # tekrar Save/Next dene
"""

from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


# ── Aktif (isvalid=false) validator'lari oku ──────────────────────────────
_JS_GET_ACTIVE = """
if (!window.Page_Validators) return [];
var out = [];
for (var i = 0; i < Page_Validators.length; i++) {
    var v = Page_Validators[i];
    if (v && v.isvalid === false) {
        var t = v.controltovalidate;
        var tid = (typeof t === 'string') ? t : (t && t.id ? t.id : '');
        out.push({
            target: tid,
            msg: (v.errormessage || '').trim()
        });
    }
}
return out;
"""


def get_active_validators(driver):
    """Sayfadaki isvalid=false validator'larin listesini dondurur."""
    try:
        res = driver.execute_script(_JS_GET_ACTIVE)
        return res or []
    except Exception as e:
        print(f"   ⚠️ validator okuma hatasi: {e}")
        return []


# ── Yardimci: _NA (Do Not Know / Does Not Apply) kutusu ───────────────────
def _try_na_box(driver, input_id):
    """
    input_id + '_NA' checkbox'i varsa isaretler.
    DS-160'ta cogu zorunlu alanin yaninda bu 'kacis' kutusu var.
    Basarili olursa True.
    """
    for suffix in ("_NA", "NA"):
        try:
            box = driver.find_element(By.ID, input_id + suffix)
            if box.get_attribute("type") == "checkbox":
                if not box.is_selected():
                    driver.execute_script("arguments[0].click();", box)
                return True
        except Exception:
            continue
    return False


# ── Yardimci: radio (rbl) → NO sec ────────────────────────────────────────
def _set_radio(driver, rbl_id, prefer_no=True):
    """
    rbl grubunda NO (_1) ya da ilk secenegi (_0) sec.
    DS-160'ta _0=YES, _1=NO tipik.
    """
    order = ("_1", "_0") if prefer_no else ("_0", "_1")
    for sfx in order:
        try:
            el = driver.find_element(By.ID, rbl_id + sfx)
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            continue
    # bazi rbl'ler farkli indexli olabilir; ilk radio'yu bul
    try:
        radios = driver.find_elements(By.CSS_SELECTOR, f"input[type='radio'][id^='{rbl_id}']")
        if radios:
            driver.execute_script("arguments[0].click();", radios[-1])  # sonuncu genelde NO
            return True
    except Exception:
        pass
    return False


# ── Yardimci: tarih grubu (Day/Month/Year) doldur ─────────────────────────
def _fix_date_group(driver, year_id, msg):
    """
    year_id sonu 'Year'. Ayni base'de Day (select) ve Month (select) var.
    Mesaja gore mantikli gecerli bir tarih koyar (bot gecsin, insan duzeltir).
    """
    if not year_id.endswith("Year"):
        return False
    base = year_id[:-4]  # 'Year' at
    day_id = base + "Day"
    month_id = base + "Month"

    low = msg.lower()
    # varsayilan: 1 yil once (guvenli, gecmis)
    d = datetime.now() - timedelta(days=365)
    if "later than today" in low or "equal to or later" in low or "in the future" in low:
        d = datetime.now() - timedelta(days=1)         # bugunden once olmali
    elif "earlier than" in low or "cannot be earlier" in low:
        d = datetime.now() - timedelta(days=1)          # makul bir gecmis

    ok = False
    try:
        Select(driver.find_element(By.ID, day_id)).select_by_value(f"{d.day:02d}")
        ok = True
    except Exception:
        pass
    try:
        Select(driver.find_element(By.ID, month_id)).select_by_value(f"{d.month:02d}")
        ok = True
    except Exception:
        # bazi aylar text degeri (JAN/FEB) ile
        try:
            Select(driver.find_element(By.ID, month_id)).select_by_index(d.month)
            ok = True
        except Exception:
            pass
    try:
        yr = driver.find_element(By.ID, year_id)
        yr.clear()
        yr.send_keys(str(d.year))
        ok = True
    except Exception:
        pass
    return ok


# ── Yardimci: dropdown → ilk gecerli option ───────────────────────────────
def _pick_first_option(driver, ddl_id):
    try:
        sel = Select(driver.find_element(By.ID, ddl_id))
        for opt in sel.options:
            val = (opt.get_attribute("value") or "").strip()
            txt = (opt.text or "").strip().upper()
            if val and val.upper() not in ("", "NONE") and txt not in ("", "- SELECT ONE -", "SELECT"):
                sel.select_by_value(val)
                return True
    except Exception:
        pass
    return False


# ── Yardimci: text → guvenli default ──────────────────────────────────────
def _fill_text(driver, txt_id):
    try:
        el = driver.find_element(By.ID, txt_id)
        tag = el.tag_name.lower()
        if tag == "select":
            return _pick_first_option(driver, txt_id)
        cur = (el.get_attribute("value") or "").strip()
        if not cur:
            el.clear()
            # yil alani gibi gorunuyorsa gecerli yil, degilse N/A
            if txt_id.endswith("Year"):
                el.send_keys(str(datetime.now().year - 1))
            else:
                el.send_keys("N/A")
        return True
    except Exception:
        return False


# ── ANA FONKSIYON ─────────────────────────────────────────────────────────
def fix_active_validators(driver):
    """
    Sayfadaki tum aktif (isvalid=false) validator'lari bulur ve
    her hatali input'u genel yontemle duzeltir.
    Kac alan duzeltildigini dondurur (0 = duzeltilecek bir sey yok / basarisiz).
    """
    actives = get_active_validators(driver)
    if not actives:
        return 0

    print(f"🔬 {len(actives)} aktif validator bulundu, genel duzeltme baslıyor...")
    fixed = 0
    seen = set()

    for v in actives:
        tid = v.get("target", "")
        msg = v.get("msg", "")
        if not tid or tid in seen:
            continue
        seen.add(tid)

        try:
            # 1) EN ONCE: Do Not Know / Does Not Apply kutusu
            if _try_na_box(driver, tid):
                print(f"   ☑️ Do Not Know: {tid}")
                fixed += 1
                continue

            # 2) Tipe gore (ID deseninden anla)
            low_id = tid.lower()
            if "rbl" in low_id:                       # radio list
                if _set_radio(driver, tid, prefer_no=True):
                    print(f"   🔘 Radio NO: {tid}")
                    fixed += 1
            elif tid.endswith("Year"):                # tarih grubu
                if _fix_date_group(driver, tid, msg):
                    print(f"   📅 Tarih duzeltildi: {tid} ({msg[:40]})")
                    fixed += 1
            elif "ddl" in low_id:                      # dropdown
                if _pick_first_option(driver, tid):
                    print(f"   🔽 Dropdown ilk secenek: {tid}")
                    fixed += 1
            else:                                      # text / diger
                if _fill_text(driver, tid):
                    print(f"   ✏️ Text default: {tid}")
                    fixed += 1
        except Exception as e:
            print(f"   ⚠️ Duzeltilemedi {tid}: {str(e)[:80]}")

    print(f"🔧 Genel duzeltme: {fixed}/{len(actives)} alan")
    return fixed
