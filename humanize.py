# -*- coding: utf-8 -*-
import random
import time as _time_module
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement


def human_delay(min_s=0.4, max_s=1.2):
    _time_module.sleep(random.uniform(min_s, max_s))


def human_click(driver, element):
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", element
    )
    human_delay(0.2, 0.5)
    ActionChains(driver).move_to_element(element).pause(
        random.uniform(0.1, 0.3)
    ).click().perform()
    human_delay(0.3, 0.8)


# ── MONKEY-PATCH: tüm dosyada tek tek değişiklik yapmadan
# send_keys ve time.sleep'i insansılaştırır ──────────────────

_original_send_keys = WebElement.send_keys
_original_sleep = _time_module.sleep
_patched = False


def _human_send_keys(self, *value):
    # Keys.TAB gibi özel tuşları (string olmayan) olduğu gibi bırak
    if len(value) == 1 and isinstance(value[0], str) and len(value[0]) > 0:
        text = value[0]
        # Tek karakterlik özel tuşlar (\ue000 ile başlayan Selenium Keys) hariç
        if not text.startswith("\ue0"):
            for ch in text:
                _original_send_keys(self, ch)
                _original_sleep(random.uniform(0.035, 0.12))
                if random.random() < 0.04:
                    _original_sleep(random.uniform(0.2, 0.45))
            return
    _original_send_keys(self, *value)


def _jittered_sleep(seconds):
    if seconds <= 0:
        return
    jitter = seconds * random.uniform(0.75, 1.6)
    _original_sleep(jitter)


def enable_human_behavior():
    """Uygulama başlarken BİR KERE çağır. send_keys ve time.sleep'i
    tüm codebase genelinde (form_fill.py, ds160_full_flow.py dahil)
    insansılaştırır — hiçbir başka dosyayı değiştirmeye gerek yok."""
    global _patched
    if _patched:
        return
    WebElement.send_keys = _human_send_keys
    _time_module.sleep = _jittered_sleep
    _patched = True
    print("🧑 Human behavior patch aktif (send_keys + sleep insansılaştırıldı)")