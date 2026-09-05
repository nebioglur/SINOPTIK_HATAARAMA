import pandas as pd
from io import StringIO
import re
import logging
from bs4 import BeautifulSoup
import warnings

# denetim_merkezi_1.py modülünü sys.path'den bulabilmek için:
import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import denetim_merkezi_1 as dm1

# Pandas'ın lxml ve html5lib gereksinimleri vardır
warnings.simplefilter(action='ignore', category=UserWarning)

def html_to_dataframe(html_content: str) -> pd.DataFrame:
    """
    Kardelen'den gelen HTML içeriğini pandas DataFrame'e dönüştürür.
    Sütun başlıklarını otomatik tespit eder ve normalleştirir.
    """
    # 1. HTML'i parse et
    try:
        # Pandas ile doğrudan tüm tabloları çek
        dfs = pd.read_html(StringIO(html_content))
        if not dfs:
            raise ValueError("HTML içerisinde tablo bulunamadı.")
        
        # En çok satırı olan tabloyu ana veri tablosu olarak kabul et
        df = max(dfs, key=len)
    except Exception as e:
        logging.error(f"HTML ayrıştırma hatası (pandas): {e}")
        # Pandas başarısız olursa (örneğin bozuk HTML), BeautifulSoup ile manuel dene
        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.find("table")
        if not table:
            raise ValueError("HTML içerisinde <table> etiketi bulunamadı (BeautifulSoup).")
        
        # Sadece basit listeler halinde satırları çıkar
        rows = []
        for tr in table.find_all("tr"):
            row = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if any(row):  # Tamamen boş satırları atla
                rows.append(row)
        
        if not rows:
            raise ValueError("Tablo içi boş.")
            
        df = pd.DataFrame(rows)

    # DataFrame'i temizle
    df = df.dropna(how='all')
    df = df.reset_index(drop=True)
    
    # 2. Header'ı bul
    h_idx = dm1.header_bul(df)
    if h_idx is not None:
        # Sütun isimlerini birleştir (multi-line başlıklar için)
        sutunlar = dm1.multi_header_olustur(df, h_idx)
        df.columns = sutunlar
        
        # Sütun isimlerini normalize et
        yeni_sutunlar = [dm1.sutun_adi_normalize_et(c) for c in df.columns]
        df.columns = yeni_sutunlar
        
        # Header ve üstündeki satırları sil
        df = df.iloc[h_idx + 1:].reset_index(drop=True)
    else:
        logging.warning("HTML tablosunda header satırı tespit edilemedi!")
    
    return df

def parse_sinoptik_html(html_content: str) -> pd.DataFrame:
    """Sinoptik rapor HTML'ini parse eder."""
    df = html_to_dataframe(html_content)
    logging.info(f"Sinoptik tablosu başarıyla parse edildi. {len(df)} satır.")
    return df

def parse_metar_html(html_content: str) -> pd.DataFrame:
    """METAR/SPECI rapor HTML'ini parse eder."""
    # METAR HTML tablosunda bazen kolon yapıları karmaşık olabilir
    df = html_to_dataframe(html_content)
    logging.info(f"METAR tablosu başarıyla parse edildi. {len(df)} satır.")
    return df
