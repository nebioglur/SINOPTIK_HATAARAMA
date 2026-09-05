import sys
import os
import datetime

# Yolları ayarla
base_dir = r"c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA"
sys.path.append(base_dir)

from mgm_monitor.readers.selenium_reader import fetch_and_parse_xls_with_selenium

def run_test():
    ist_kodu = 17244
    ist_isim = "KONYA MEYDAN"
    bugun = datetime.datetime.now()
    
    # Tarih aralığını belirle (Ayın 1'inden bugüne)
    bugun = datetime.datetime.now()
    bas = datetime.datetime(bugun.year, bugun.month, 1)
    bit = bugun
    
    print(f"Test basliyor: {ist_isim} ({bas.strftime('%d.%m.%Y')} - {bit.strftime('%d.%m.%Y')})")
    try:
        df_sin, df_metar = fetch_and_parse_xls_with_selenium(ist_kodu, ist_isim, bas, bit)
        if df_sin is not None:
            print(f"SİNOPTİK başarıyla çekildi! Boyut: {df_sin.shape}")
        else:
            print("SİNOPTİK verisi yok.")
            
        if df_metar is not None:
            print(f"METAR başarıyla çekildi! Boyut: {df_metar.shape}")
        else:
            print("METAR verisi yok.")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
