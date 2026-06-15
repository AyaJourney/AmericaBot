import time
import random
import getpass  # Şifreyi terminalde gizli yazmak için
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def insansi_yaz(element, metin):
    """
    Hedef input alanını temizler, bir süre bekler ve harfleri 
    Cloudflare'i şüphelendirmeyecek kadar yavaş ve değişken hızda yazar.
    """
    element.clear()
    time.sleep(random.uniform(0.6, 1.2)) # Yazmaya başlamadan önce insansı duraksama
    for harf in metin:
        element.send_keys(harf)
        time.sleep(random.uniform(0.15, 0.35)) # Harfler arası bekleme süresi uzatıldı

def botu_calistir(kullanici_adi, sifre):
    # 1. ANTI-BOT TARAYICI AYARLARI
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=tr-TR')
    
    # Gerçek bir kullanıcı tarayıcısı gibi görünmek için User-Agent maskesi
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    print("\n[Bot] Tarayıcı güvenli modda başlatılıyor, lütfen bekleyin...")
    driver = uc.Chrome(options=options)
    
    # Güvenlik soruları cevap havuzunuz
    CEVAP_HAVUZU = {
        "spouse": "OTOBUS",   
        "city": "ANKARA",    
        "road": "SOKAK"       
    }

    try:
        # 2. GİRİŞ SAYFASINA GİDİŞ
        print("[Bot] Giriş sayfasına gidiliyor...")
        driver.get("https://www.usvisascheduling.com/tr-TR/SignIn")
        
        # Akıllı bekleme süresini 20 saniyeye çıkardık (Yoğun saatlerde site yavaş açılabilir)
        wait = WebDriverWait(driver, 20)
        
        # 3. İLK GİRİŞ EKRANI
        print("[Bot] Giriş formu bekleniyor...")
        
        # Kullanıcı adı alanını doldur
        username_input = wait.until(EC.element_to_be_clickable((By.ID, "signInName")))
        print("[Bot] Kullanıcı adı yazılıyor...")
        insansi_yaz(username_input, kullanici_adi) 
        
        time.sleep(random.uniform(0.8, 1.8))
        
        # Parola alanını doldur
        password_input = wait.until(EC.element_to_be_clickable((By.ID, "password")))
        print("[Bot] Parola yazılıyor...")
        insansi_yaz(password_input, sifre) 
        
        time.sleep(random.uniform(1.2, 2.2))
        
        # Giriş butonuna tıkla
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
        login_button.click()
        print("[Bot] İlk giriş yapıldı. Güvenlik soruları sayfası aranıyor...")
        
        # 4. GÜVENLİK SORULARI SAYFASI
        wait.until(EC.presence_of_element_located((By.ID, "attributeVerification")))
        time.sleep(3) # Sayfa içi scriptlerin tam yüklenmesi için güvenli duraksama
        
        # --- GÜVENLİK SORUSU 1 ---
        try:
            soru_1_element = driver.find_element(By.ID, "kbq2aReadOnly")
            soru_1_metni = soru_1_element.text.lower()
            cevap_1_input = driver.find_element(By.ID, "kba2_response")
            
            print(f"\n[Soru 1]: {soru_1_element.text}")
            
            cevap_1 = None
            if "spouse" in soru_1_metni:
                cevap_1 = CEVAP_HAVUZU["spouse"]
            elif "city" in soru_1_metni or "town" in soru_1_metni or "born" in soru_1_metni:
                cevap_1 = CEVAP_HAVUZU["city"]
            elif "road" in soru_1_metni or "street" in soru_1_metni:
                cevap_1 = CEVAP_HAVUZU["road"]
                
            if cevap_1:
                print(f"-> Cevap yazılıyor: {cevap_1}")
                insansi_yaz(cevap_1_input, cevap_1)
            else:
                print("🚨 UYARI: 1. Soru havuzdaki kelimelerle eşleşmedi!")
                
        except Exception as e_soru1:
            print(f"[Hata] Soru 1 alanları okunurken sorun çıktı: {e_soru1}")

        time.sleep(random.uniform(1.0, 2.5)) # İki soru formu doldurma arasında beklemeyi uzattık

        # --- GÜVENLİK SORUSU 2 ---
        try:
            soru_2_element = driver.find_element(By.ID, "kbq3ReadOnly")
            soru_2_metni = soru_2_element.text.lower()
            cevap_2_input = driver.find_element(By.ID, "kba3_response")
            
            print(f"\n[Soru 2]: {soru_2_element.text}")
            
            cevap_2 = None
            if "spouse" in soru_2_metni:
                cevap_2 = CEVAP_HAVUZU["spouse"]
            elif "city" in soru_2_metni or "town" in soru_2_metni or "born" in soru_2_metni:
                cevap_2 = CEVAP_HAVUZU["city"]
            elif "road" in soru_2_metni or "street" in soru_2_metni:
                cevap_2 = CEVAP_HAVUZU["road"]
                
            if cevap_2:
                print(f"-> Cevap yazılıyor: {cevap_2}")
                insansi_yaz(cevap_2_input, cevap_2)
            else:
                print("🚨 UYARI: 2. Soru havuzdaki kelimelerle eşleşmedi!")
                
        except Exception as e_soru2:
            print(f"[Hata] Soru 2 alanları okunurken sorun çıktı: {e_soru2}")

        # 5. ONAYLA VE DEVAM ET
        time.sleep(random.uniform(2.0, 4.0)) # Form bittikten sonra insan gibi bekleme/düşünme simülasyonu
        continue_button = wait.until(EC.element_to_be_clickable((By.ID, "continue")))
        continue_button.click()
        print("\n[Bot] Güvenlik soruları onaylandı. İçeriye yönlendiriliyorsunuz...")
        
        # İçerideki işlemlerin veya takvimin yüklenmesi için ana bekleme süresi
        time.sleep(20)

    except Exception as ana_hata:
        print(f"\n🚨 Bot çalışırken bir hata oluştu (IP engellenmiş veya sayfa yapısı değişmiş olabilir): {ana_hata}")
        
    finally:
        print("[Bot] Tarayıcı kapatılıyor.")
        driver.quit()

if __name__ == "__main__":
    print("=========================================")
    print("     US VISA SCHEDULING BOT PANELİ       ")
    print("=========================================")
    
    kullanici = input("Kullanıcı Adınızı Girin: ")
    # Yazarken karakterler ekranda gizlenir
    sifre = getpass.getpass("Şifrenizi Girin (Yazarken gizlenir): ")
    
    if kullanici and sifre:
        botu_calistir(kullanici, sifre)
    else:
        print("Hata: Kullanıcı adı veya şifre boş geçilemez.")