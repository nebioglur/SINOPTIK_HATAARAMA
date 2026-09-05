import time
import threading
import datetime
import logging
from typing import Callable, Optional
import pandas as pd
import sys
import os

# mgm_monitor modüllerini dahil et
from mgm_monitor.config import ConfigLoader
from mgm_monitor.readers import AspNetReader
from mgm_monitor.parsers.html_parser import parse_sinoptik_html, parse_metar_html

# Global zamanlayıcı bayrağı
_OTO_ANALIZ_CALISIYOR = False
_OTO_ANALIZ_THREAD = None

def get_config():
    """Yapılandırma nesnesini yükler."""
    config_dir = os.path.join(os.path.dirname(__file__), "mgm_monitor", "config")
    return ConfigLoader(config_dir)

def html_veri_cek(ist_kodu: int, ist_isim: str, baslangic: datetime.datetime, bitis: datetime.datetime, p_callback=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Belirtilen istasyon ve tarih aralığı için Kardelen'den Selenium aracılığıyla
    verileri arka planda geçici olarak indirir, okur ve siler.
    """
    if p_callback: p_callback(10, f"Selenium tarayıcısı başlatılıyor: {ist_isim}...")
    
    try:
        from mgm_monitor.readers.selenium_reader import fetch_and_parse_xls_with_selenium
        
        if p_callback: p_callback(30, "Kardelen sunucusundan veriler çekiliyor (Lütfen bekleyin)...")
        df_sin, df_metar = fetch_and_parse_xls_with_selenium(ist_kodu, ist_isim, baslangic, bitis)
        
        if p_callback: p_callback(80, "Veriler okundu ve tablolar ayrıştırıldı.")
        
        return df_sin, df_metar
    except Exception as e:
        logging.error(f"Veri çekme hatası: {e}")
        raise

def dataframe_hazirla(df: pd.DataFrame) -> pd.DataFrame:
    """Arayüz'ün beklediği formata (sayfa sütunu vs) çevirir."""
    if df is None or df.empty:
        return df
        
    # Eğer 'tarih' sütunu varsa, onu 'sayfa' olarak ayarla ki arayuz.py bunu Excel sayfası gibi algılasın
    if 'tarih' in df.columns:
        df['sayfa'] = df['tarih']
    else:
        # Tarih sütunu yoksa, güncel tarihi varsayalım (hata vermemesi için)
        df['sayfa'] = datetime.datetime.now().strftime("%d.%m.%Y")
        
    return df

def manuel_analiz(ist_kodu: int, baslangic: datetime.datetime, bitis: datetime.datetime, arayuz_guncelle_callback: Callable):
    """Kullanıcının seçtiği tarihlerde bir kerelik manuel analiz başlatır."""
    try:
        ist_isim = str(ist_kodu)
        # İsmi bul (eğer stations.yaml'da varsa)
        cfg = get_config()
        for s in cfg.get_enabled_stations():
            if str(s.get('id', '')) == str(ist_kodu):
                ist_isim = s.get('name', str(ist_kodu))
                break
                
        arayuz_guncelle_callback(10, f"HTML verileri çekiliyor: {ist_isim}...")
        df_sin, df_metar = html_veri_cek(ist_kodu, ist_isim, baslangic, bitis, p_callback=arayuz_guncelle_callback)
        
        arayuz_guncelle_callback(50, "Tablolar ayrıştırıldı. Analiz başlıyor...")
        
        df_sin = dataframe_hazirla(df_sin)
        df_metar = dataframe_hazirla(df_metar)
        
        return df_sin, df_metar, bitis.year, bitis.month, ist_isim
    except Exception as e:
        logging.error(f"Canlı analiz hatası: {e}", exc_info=True)
        raise e

def otomatik_dongu(ist_kodu: int, baslangic_offset_gun: int, trigger_callback: Callable, durum_callback: Callable):
    """Arka planda çalışan otomatik zamanlayıcı döngüsü (her saat 55 geçe çalışır)."""
    global _OTO_ANALIZ_CALISIYOR
    
    cfg = get_config()
    ist_isim = str(ist_kodu)
    for s in cfg.get_enabled_stations():
        if str(s.get('id', '')) == str(ist_kodu):
            ist_isim = s.get('name', str(ist_kodu))
            break
            
    durum_callback(f"Oto Analiz AKTİF: Her saat :55 geçe ({ist_isim})")
    
    while _OTO_ANALIZ_CALISIYOR:
        now = datetime.datetime.now()
        
        # Saat 55 geçe mi?
        if now.minute == 55:
            durum_callback(f"Oto Analiz BAŞLADI: {now.strftime('%H:%M')} ({ist_isim})")
            
            # Bitiş: Bugün, Başlangıç: Dün (-1 gün)
            bitis = now
            baslangic = now - datetime.timedelta(days=abs(baslangic_offset_gun))
            
            try:
                # Arka planda veriyi çek
                df_sin, df_metar = html_veri_cek(ist_kodu, ist_isim, baslangic, bitis)
                df_sin = dataframe_hazirla(df_sin)
                df_metar = dataframe_hazirla(df_metar)
                
                # Arayüzü (islem_yurut) tetikle
                trigger_callback(df_sin, df_metar, bitis.year, bitis.month, ist_isim, f"Oto-Analiz: {ist_isim}")
                
            except Exception as e:
                logging.error(f"Otomatik analiz hatası: {e}")
                durum_callback(f"Hata: {e}")
                
            # Aynı dakika içinde birden fazla çalışmasını önlemek için 61 saniye uyu
            time.sleep(61)
        else:
            # 55 geçmeyi bekle
            time.sleep(10)

def otomatik_analiz_baslat(ist_kodu: int, trigger_callback: Callable, durum_callback: Callable):
    """Otomatik (zamanlanmış) analizi başlatır."""
    global _OTO_ANALIZ_CALISIYOR, _OTO_ANALIZ_THREAD
    
    if _OTO_ANALIZ_CALISIYOR:
        return
        
    _OTO_ANALIZ_CALISIYOR = True
    
    # Varsayılan başlangıç: -1 gün
    baslangic_offset_gun = 1
    
    _OTO_ANALIZ_THREAD = threading.Thread(
        target=otomatik_dongu,
        args=(ist_kodu, baslangic_offset_gun, trigger_callback, durum_callback),
        daemon=True
    )
    _OTO_ANALIZ_THREAD.start()
    
def otomatik_analiz_durdur(durum_callback: Callable):
    """Otomatik analizi durdurur."""
    global _OTO_ANALIZ_CALISIYOR
    _OTO_ANALIZ_CALISIYOR = False
    durum_callback("Oto Analiz DURDURULDU.")
