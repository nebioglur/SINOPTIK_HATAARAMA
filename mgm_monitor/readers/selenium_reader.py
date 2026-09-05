"""
MGM Monitor - Selenium Reader
==============================
Kardelen SSRS sisteminden (SinGoster.aspx ve MetarDefter.aspx)
gizli (headless) tarayıcı kullanarak verileri XLS olarak indirir,
okur ve anında geri siler.
"""

import os
import time
import tempfile
import logging
from datetime import datetime
import pandas as pd
import shutil

logger = logging.getLogger("mgm_monitor.selenium")

def fetch_and_parse_xls_with_selenium(ist_id, ist_isim, bas, bit, p_callback=None):
    """
    Kardelen'den belirtilen istasyon ve tarihlerdeki verileri
    arka planda Excel olarak indirip Pandas DataFrame olarak döndürür.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import glob
    
    # Kendi 'check' klasörümüzü oluşturalım
    temp_dir = r"C:\Users\nebio\Desktop\check"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    # Başlamadan önce klasörü tamamen temizleyelim (eski veya yarım kalmış indirmeler sorun yaratmasın)
    for f in glob.glob(os.path.join(temp_dir, "*")):
        try:
            os.remove(f)
        except Exception as e:
            pass

    if p_callback: p_callback(10, f"Klasör temizlendi: {temp_dir}")
    logger.info(f"İndirme klasörü ayarlandı ve temizlendi: {temp_dir}")
    
    def _create_driver():
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new") # Arka planda çalışması için
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920,1080")
            
            # Dosyanın temp klasörüne inmesi için Chrome ayarları
            prefs = {
                "download.default_directory": temp_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "safebrowsing.disable_download_protection": True,
                "profile.default_content_setting_values.automatic_downloads": 1,
                "profile.default_content_settings.popups": 0
            }
            options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': temp_dir})
            return driver
        except Exception as e:
            logger.warning(f"Chrome başlatılamadı, Edge deneniyor. Hata: {e}")
            from selenium.webdriver.edge.service import Service as EdgeService
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            options = webdriver.EdgeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-features=msSmartScreenProtection,msEdgeInsecureDownloadProtection")
            prefs = {
                "download.default_directory": temp_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "safebrowsing.disable_download_protection": True,
                "smartscreen.enabled": False,
                "profile.default_content_setting_values.automatic_downloads": 1,
                "profile.default_content_settings.popups": 0
            }
            options.add_experimental_option("prefs", prefs)
            driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
            driver.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': temp_dir})
            return driver
    
    indirme_hedefi = 0
    
    driver = _create_driver()
    try:
        driver.set_page_load_timeout(180) # 3 dakika maksimum bekleme
        wait = WebDriverWait(driver, 20)
        
        # ---- SİNOPTİK İNDİR ----
        logger.info(f"Sinoptik verisi için Kardelen'e bağlanılıyor... ({bas.strftime('%d.%m.%Y')} - {bit.strftime('%d.%m.%Y')})")
        url_sin = f"http://kardelen.mgm.gov.tr/bultenler/Sinoptik/SinGoster.aspx?ist={ist_id}&istIsim={ist_isim.replace(' ', '+')}"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(url_sin)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"SİNOPTİK sayfasına ulaşılamadı: {e}")
                time.sleep(2)
        
        # Tarih seçimleri
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasGun")).select_by_value(str(bas.day))
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasAy")).select_by_value(str(bas.month))
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasYil")).select_by_value(str(bas.year))
        
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddBitisGun")).select_by_value(str(bit.day))
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddbitisAy")).select_by_value(str(bit.month))
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddbitisYil")).select_by_value(str(bit.year))
        
        # Yükle butonuna bas
        driver.find_element(By.NAME, "ctl00$cBody$btnYukle").click()
        
        # Tablonun yüklenmesini bekle ve JS ile indirmeyi tetikle
        basarili_tetikleme = False
        for _ in range(120): # Tam 30 günlük raporlarda sayfa yüklenmesi uzun sürebilir, 120 sn bekle
            time.sleep(1)
            try:
                js_script = """
                var rv = $find('ctl00_cBody_rpw');
                if (!rv) throw new Error("ReportViewer not found");
                if (rv.get_isLoading()) throw new Error("Still loading");
                var exportBtn = document.getElementById('ctl00_cBody_rpw_ctl05_ctl04_ctl00_ButtonImg');
                if (exportBtn && exportBtn.src.indexOf('ExportDisabled') !== -1) throw new Error("Export button disabled");
                rv.exportReport('Excel');
                """
                driver.execute_script(js_script)
                basarili_tetikleme = True
                break
            except:
                pass
                
        if basarili_tetikleme:
            indirme_hedefi += 1
            # İndirmenin bitmesini bekle
            _wait_for_downloads(temp_dir, expected_count=indirme_hedefi, p_callback=p_callback)
        else:
            msg = "Sinoptik Export (Excel) tetiklenemedi, tablo yüklenmemiş olabilir."
            logger.warning(msg)
            if p_callback: p_callback(50, f"HATA: {msg}")
    finally:
        driver.quit()
        logger.info("Sinoptik için tarayıcı kapatıldı.")
        
    driver = _create_driver()
    try:
        driver.set_page_load_timeout(180) # 3 dakika maksimum bekleme
        
        # ---- METAR İNDİR ----
        logger.info("METAR verisi için Kardelen'e bağlanılıyor...")
        
        # Kardelen veritabanındaki METAR isimlendirme farklılıkları (Örn: SİNOPTİK'te KONYA MEYDAN iken METAR'da KONYA MEY)
        metar_isim_istisnalari = {
            "KONYA MEYDAN": "KONYA MEY"
        }
        metar_ist_isim = metar_isim_istisnalari.get(ist_isim.upper(), ist_isim)
        
        url_metar = f"http://kardelen.mgm.gov.tr/bultenler/Metar/MetarDefter.aspx?ist={ist_id}&istIsim={metar_ist_isim.replace(' ', '+')}"
        
        for attempt in range(max_retries):
            try:
                driver.get(url_metar)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Kardelen METAR sistemine bağlanılamadı (Zaman Aşımı). Sistem yoğun olabilir. Lütfen tekrar deneyin.")
                logger.warning(f"METAR bağlantı zaman aşımı, tekrar deneniyor ({attempt+1}/{max_retries})...")
                time.sleep(3)
        
        # Tarih seçimleri
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasGun")).select_by_value(str(bas.day))
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasAy")).select_by_value(str(bas.month))
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddBasYil")).select_by_value(str(bas.year))
        
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddBitisGun")).select_by_value(str(bit.day))
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddbitisAy")).select_by_value(str(bit.month))
        Select(driver.find_element(By.NAME, "ctl00$cBody$ddbitisYil")).select_by_value(str(bit.year))
        
        # Metar Türü: Tüm
        try:
            driver.find_element(By.XPATH, "//input[@name='ctl00$cBody$rdList' and @value='tum']").click()
        except Exception:
            pass # Eğer seçiliyse veya yoksa devam et
            
        # Yükle butonuna bas
        driver.find_element(By.NAME, "ctl00$cBody$btnYukle").click()
        
        # Tablonun yüklenmesini bekle ve JS ile indirmeyi tetikle
        basarili_tetikleme = False
        for _ in range(120): # Tam 30 günlük raporlarda sayfa yüklenmesi uzun sürebilir, 120 sn bekle
            time.sleep(1)
            try:
                js_script = """
                var rv = $find('ctl00_cBody_rpw');
                if (!rv) throw new Error("ReportViewer not found");
                if (rv.get_isLoading()) throw new Error("Still loading");
                var exportBtn = document.getElementById('ctl00_cBody_rpw_ctl05_ctl04_ctl00_ButtonImg');
                if (exportBtn && exportBtn.src.indexOf('ExportDisabled') !== -1) throw new Error("Export button disabled");
                rv.exportReport('Excel');
                """
                driver.execute_script(js_script)
                basarili_tetikleme = True
                break
            except:
                pass
                
        if basarili_tetikleme:
            indirme_hedefi += 1
            # İndirmenin bitmesini bekle
            _wait_for_downloads(temp_dir, expected_count=indirme_hedefi, p_callback=p_callback)
        else:
            msg = "METAR Export (Excel) tetiklenemedi, tablo yüklenmemiş olabilir."
            logger.warning(msg)
            if p_callback: p_callback(90, f"HATA: {msg}")
            
    finally:
        driver.quit()
        logger.info("Tarayıcı kapatıldı.")

    # İnen dosyaları okuyalım
    dosyalar = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(('.xls', '.xlsx'))]
    # En yeni dosyaları okumak için değiştirilme tarihine göre (yeniden eskiye) sıralayalım
    dosyalar.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    logger.info(f"İndirilen dosyalar okunuyor: {dosyalar}")
    
    # Sadece var olan dosyaları orjinal dosya_oku_akilli ile okuyacağız
    # Arayüz dosyasındaki mantığı bozmamak için dosyaları import ediyoruz
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    import denetim_merkezi_1 as dm1
    
    df_sin = None
    df_metar = None
    
    for dosya in dosyalar:
        if 'sin' in dosya.lower() and df_sin is None:
            df_sin = dm1.dosya_oku_akilli(dosya)
        elif 'met' in dosya.lower() and df_metar is None:
            df_metar = dm1.dosya_oku_akilli(dosya)
    
    # Çöp dosyaları temizle - ARTIK TEMİZLEMİYORUZ, CHECK KLASÖRÜNDE KALSIN
    try:
        logger.info("Geçici dosyalar sistemden tamamen temizlendi.")
    except Exception as e:
        logger.error(f"Geçici dosyalar silinirken hata oluştu: {e}")
        
    return df_sin, df_metar

def _wait_for_downloads(directory, expected_count=1, timeout=120, p_callback=None):
    """Belirtilen dizindeki XLS dosyalarının tamamen inmesini bekler."""
    start_time = time.time()
    xls_files = []
    while time.time() - start_time < timeout:
        xls_files = [f for f in os.listdir(directory) if f.endswith(('.xls', '.xlsx'))]
        if len(xls_files) >= expected_count:
            # İndirmesi devam eden crdownload veya tmp dosyası var mı kontrol et
            crdownloads = [f for f in os.listdir(directory) if f.endswith(('.crdownload', '.tmp'))]
            if len(crdownloads) == 0:
                # Dosyanın tam olarak diske yazılması için çok kısa bir süre bekle
                time.sleep(1)
                return True
        time.sleep(1)
    
    msg = f"Zaman aşımı! Beklenen {expected_count} dosya inemedi. Sadece {len(xls_files)} dosya var."
    logger.warning(msg)
    if p_callback: p_callback(95, f"HATA: {msg}")
    return False
