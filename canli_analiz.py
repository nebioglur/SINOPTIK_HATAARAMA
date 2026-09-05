import time
import threading
import datetime
import logging
from typing import Callable, Optional
import pandas as pd
import sys
import os

# mgm_monitor modÃ¼llerini dahil et
from mgm_monitor.config import ConfigLoader
from mgm_monitor.readers import AspNetReader
from mgm_monitor.parsers.html_parser import parse_sinoptik_html, parse_metar_html

# Global zamanlayÄ±cÄ± bayraÄŸÄ±
_OTO_ANALIZ_CALISIYOR = False
_OTO_ANALIZ_THREAD = None

def get_config():
    """YapÄ±landÄ±rma nesnesini yÃ¼kler."""
    config_dir = os.path.join(os.path.dirname(__file__), "mgm_monitor", "config")
    return ConfigLoader(config_dir)

def html_veri_cek(ist_kodu: int, ist_isim: str, baslangic: datetime.datetime, bitis: datetime.datetime, p_callback=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Belirtilen istasyon ve tarih aralÄ±ÄŸÄ± iÃ§in Kardelen'den Selenium aracÄ±lÄ±ÄŸÄ±yla
    verileri arka planda geÃ§ici olarak indirir, okur ve siler.
    """
    if p_callback: p_callback(10, f"Selenium tarayÄ±cÄ±sÄ± baÅŸlatÄ±lÄ±yor: {ist_isim}...")
    
    try:
        from mgm_monitor.readers.selenium_reader import fetch_and_parse_xls_with_selenium
        
        if p_callback: p_callback(30, "Kardelen sunucusundan veriler Ã§ekiliyor (LÃ¼tfen bekleyin)...")
        df_sin, df_metar = fetch_and_parse_xls_with_selenium(ist_kodu, ist_isim, baslangic, bitis)
        
        if p_callback: p_callback(80, "Veriler okundu ve tablolar ayrÄ±ÅŸtÄ±rÄ±ldÄ±.")
        
        return df_sin, df_metar
    except Exception as e:
        logging.error(f"Veri Ã§ekme hatasÄ±: {e}")
        raise

def dataframe_hazirla(df: pd.DataFrame) -> pd.DataFrame:
    """ArayÃ¼z'Ã¼n beklediÄŸi formata (sayfa sÃ¼tunu vs) Ã§evirir."""
    if df is None or df.empty:
        return df
        
    # EÄŸer 'tarih' sÃ¼tunu varsa, onu 'sayfa' olarak ayarla ki arayuz.py bunu Excel sayfasÄ± gibi algÄ±lasÄ±n
    if 'tarih' in df.columns:
        df['sayfa'] = df['tarih']
    else:
        # Tarih sÃ¼tunu yoksa, gÃ¼ncel tarihi varsayalÄ±m (hata vermemesi iÃ§in)
        df['sayfa'] = datetime.datetime.now().strftime("%d.%m.%Y")
        
    return df

def manuel_analiz(ist_kodu: int, baslangic: datetime.datetime, bitis: datetime.datetime, arayuz_guncelle_callback: Callable):
    """KullanÄ±cÄ±nÄ±n seÃ§tiÄŸi tarihlerde bir kerelik manuel analiz baÅŸlatÄ±r."""
    try:
        ist_isim = str(ist_kodu)
        # Ä°smi bul (eÄŸer stations.yaml'da varsa)
        cfg = get_config()
        for s in cfg.get_enabled_stations():
            if str(s.get('id', '')) == str(ist_kodu):
                ist_isim = s.get('name', str(ist_kodu))
                break
                
        arayuz_guncelle_callback(10, f"HTML verileri Ã§ekiliyor: {ist_isim}...")
        df_sin, df_metar = html_veri_cek(ist_kodu, ist_isim, baslangic, bitis, p_callback=arayuz_guncelle_callback)
        
        arayuz_guncelle_callback(50, "Tablolar ayrÄ±ÅŸtÄ±rÄ±ldÄ±. Analiz baÅŸlÄ±yor...")
        
        df_sin = dataframe_hazirla(df_sin)
        df_metar = dataframe_hazirla(df_metar)
        
        return df_sin, df_metar, bitis.year, bitis.month, ist_isim
    except Exception as e:
        logging.error(f"CanlÄ± analiz hatasÄ±: {e}", exc_info=True)
        raise e

def otomatik_dongu(ist_kodu: int, baslangic_offset_gun: int, trigger_callback: Callable, durum_callback: Callable):
    """Arka planda Ã§alÄ±ÅŸan otomatik zamanlayÄ±cÄ± dÃ¶ngÃ¼sÃ¼ (her saat 55 geÃ§e Ã§alÄ±ÅŸÄ±r)."""
    global _OTO_ANALIZ_CALISIYOR
    
    cfg = get_config()
    ist_isim = str(ist_kodu)
    for s in cfg.get_enabled_stations():
        if str(s.get('id', '')) == str(ist_kodu):
            ist_isim = s.get('name', str(ist_kodu))
            break
            
    durum_callback(f"Oto Analiz AKTÄ°F: Her saat :55 geÃ§e ({ist_isim})")
    
    ilk_calisma = True
    while _OTO_ANALIZ_CALISIYOR:
        now = datetime.datetime.now()
        
        # Saat 55 geÃ§e mi veya ilk Ã§alÄ±ÅŸma mÄ±?
        if now.minute == 55 or ilk_calisma:
            ilk_calisma = False
            durum_callback(f"Oto Analiz BAÅLADI: {now.strftime('%H:%M')} ({ist_isim})")
            
            # BitiÅŸ: BugÃ¼n, BaÅŸlangÄ±Ã§: DÃ¼n (-1 gÃ¼n)
            bitis = now
            baslangic = now - datetime.timedelta(days=abs(baslangic_offset_gun))
            
            try:
                # Arka planda veriyi Ã§ek
                df_sin, df_metar = html_veri_cek(ist_kodu, ist_isim, baslangic, bitis)
                df_sin = dataframe_hazirla(df_sin)
                df_metar = dataframe_hazirla(df_metar)
                
                # ArayÃ¼zÃ¼ (islem_yurut) tetikle
                trigger_callback(df_sin, df_metar, bitis.year, bitis.month, ist_isim, f"Oto-Analiz: {ist_isim}")
                
            except Exception as e:
                logging.error(f"Otomatik analiz hatasÄ±: {e}"); print(f"WEB_SERVER_LOG: Otomatik analiz hatasi: Ä±: {e}")
                durum_callback(f"Hata: {e}")
                
            # AynÄ± dakika iÃ§inde birden fazla Ã§alÄ±ÅŸmasÄ±nÄ± Ã¶nlemek iÃ§in 61 saniye uyu
            time.sleep(61)
        else:
            # 55 geÃ§meyi bekle
            time.sleep(10)

def otomatik_analiz_baslat(ist_kodu: int, trigger_callback: Callable, durum_callback: Callable):
    """Otomatik (zamanlanmÄ±ÅŸ) analizi baÅŸlatÄ±r."""
    global _OTO_ANALIZ_CALISIYOR, _OTO_ANALIZ_THREAD
    
    if _OTO_ANALIZ_CALISIYOR:
        return
        
    _OTO_ANALIZ_CALISIYOR = True
    
    # VarsayÄ±lan baÅŸlangÄ±Ã§: -1 gÃ¼n
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

