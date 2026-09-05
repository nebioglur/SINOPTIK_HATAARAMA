import pandas as pd
import sys
sys.path.insert(0, r"c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA")
import arayuz

try:
    # We will instantiate the GUI but without running mainloop
    # Then we will call the worker directly.
    import tkinter as tk
    root = tk.Tk()
    app = arayuz.HataAnalizArayuzu(root)
    
    # Mock progress
    def progress_cb(x, y=None):
        pass
    
    import denetim_merkezi_1 as dm1
    import denetim_merkezi_2 as dm2
    
    df_sin = dm1.dosya_oku_akilli(r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\check\SinTum.xls")
    df_met = dm1.dosya_oku_akilli(r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\check\MetTum.xls")
    
    # Run the exact code from _aylik_rapor_olustur_worker
    df_metar_tekil = dm2.metar_tekillestir(df_met)
    
    birlesik = pd.merge(df_sin, df_metar_tekil, on=["sayfa", "gmt"], how="left", suffixes=('_sin', '_met'))
    
    def extract_metar_time(row):
        try:
            for col in ["_raw_line_met", "bulten_met", "_raw_line", "bulten"]:
                if col in row and pd.notna(row[col]):
                    import re
                    m = re.search(r" \d{2}(\d{4})Z\b", str(row[col]).upper())
                    if m: return m.group(1)
        except: pass
        try:
            gmt_val = float(row.get("gmt", 0))
            h = int(gmt_val)
            if h == 0: return "2350"
            return f"{h-1:02d}50"
        except: return "-"

    def format_sin_time(row):
        try:
            return f"{int(float(row.get('gmt', 0))):02d}00"
        except: return "-"

    if "Saat_sin" in birlesik.columns:
        birlesik["SİNOPTİK - Saat"] = birlesik["Saat_sin"]
    else:
        birlesik["SİNOPTİK - Saat"] = birlesik.apply(format_sin_time, axis=1)
        
    if "Saat_met" in birlesik.columns:
        birlesik["METAR - Saat"] = birlesik["Saat_met"]
    else:
        birlesik["METAR - Saat"] = birlesik.apply(extract_metar_time, axis=1)

    birlesik = dm2.hata_analizi_yap(birlesik, df_met, progress_callback=progress_cb)
    
    def format_saat_str(x):
        try: return f"{int(float(x)):02d}00"
        except: return str(x)
    
    birlesik["gmt"] = birlesik["gmt"].apply(format_saat_str)
    
    col_map = {
        'sayfa': 'Tarih', 'gmt': 'Saat (GMT)', 'gmt_exact_sin': 'SİNOPTİK - Saat', 'gmt_exact_metar': 'METAR - Saat',
        'ir': 'İndikatör (ir)', 'ix': 'İndikatör (ix)',
        'h': 'Bulut Yük. (h)', 'vv': 'Görüş (VV)', 'n': 'Toplam Bulut (N)',
        'dd': 'Rüzgar Yönü (dd)', 'ff': 'Rüzgar Hızı (ff)', 't': 'Sıcaklık (T)',
        'td': 'İşba (Td)', 'p0': 'Deniz Basıncı (P0)', 'p': 'İstasyon Basıncı (P)',
        'a': 'Basınç Karakteri (a)', 'ppp': 'Basınç Değişimi (ppp)',
        'ww': 'Halihazır Hava (ww)', 'ww2': 'Halihazır Hava 2 (ww2)', 'ww3': 'Halihazır Hava 3 (ww3)', 'w1': 'Geçmiş Hava 1 (W1)', 'w2': 'Geçmiş Hava 2 (W2)',
        'nh': 'Alçak/Orta Bulut (Nh)', 'cl': 'Alçak Bulut (CL)', 'cm': 'Orta Bulut (CM)',
        'ch': 'Yüksek Bulut (CH)', 'tx': 'Maks. Sıcaklık (Tx)', 'tn': 'Min. Sıcaklık (Tn)',
        'tg': 'Toprak Sıcaklığı (Tg)', 'e': 'Yerin Hali (E)', 'rrr': 'Yağış Miktarı (RRR)',
        'tr': 'Yağış Süresi (tR)', 'g910': '910 Grubu (Hamle)', 'g911': '911 Grubu (Hamle)',
        'g931': '931 Grubu (Kar)', 'g932': '932 Grubu (Taze Kar)', 'g960': '960 Grubu (Hadise)', 
        'rh': 'Bağıl Nem (%)', 'tw': 'Islak Sıcaklık (Tw)', 
        'buhar': 'Buharlaşma', 'rad_tipi': 'Radyasyon Tipi', 'radyasyon': 'Radyasyon Miktarı',
        'hata_kodu': 'Hata Kodu', 'aciklama': 'AÇIKLAMA', 'hatali_kod': 'Hatalı Kod', 'tavsiye_kod': 'Tavsiye Kod',
        'bulten_sin': 'SİNOPTİK - Şifreli Mesaj', 'bulten_met': 'METAR - Şifreli Mesaj',
        'personel_sin': 'SİNOPTİK - Nöbetçi', 'personel_met': 'METAR - Nöbetçi', 'rrr_toplam': 'SİNOPTİK - Toplam Yağış'
    }
    birlesik = birlesik.rename(columns=col_map)
    
    order = [
        'Tarih', 'Saat (GMT)', 'SİNOPTİK - Saat', 'METAR - Saat', 'SİNOPTİK - Şifreli Mesaj', 'METAR - Şifreli Mesaj',
        'İndikatör (ir)', 'İndikatör (ix)', 'Bulut Yük. (h)', 'Görüş (VV)', 'Toplam Bulut (N)',
        'Rüzgar Yönü (dd)', 'Rüzgar Hızı (ff)', '910 Grubu (Hamle)', '911 Grubu (Hamle)',
        'Sıcaklık (T)', 'İşba (Td)', 'Bağıl Nem (%)', 'Deniz Basıncı (P0)', 'İstasyon Basıncı (P)',
        'Basınç Karakteri (a)', 'Basınç Değişimi (ppp)', 'Yağış Miktarı (RRR)', 'SİNOPTİK - Toplam Yağış', 'Yağış Süresi (tR)',
        'Halihazır Hava (ww)', 'Halihazır Hava 2 (ww2)', 'Halihazır Hava 3 (ww3)', 'Geçmiş Hava 1 (W1)', 'Geçmiş Hava 2 (W2)',
        '960 Grubu (Hadise)', 'Alçak/Orta Bulut (Nh)', 'Alçak Bulut (CL)', 'Orta Bulut (CM)', 'Yüksek Bulut (CH)',
        'Maks. Sıcaklık (Tx)', 'Min. Sıcaklık (Tn)', 'Toprak Sıcaklığı (Tg)', 'Yerin Hali (E)', 
        '931 Grubu (Kar)', '932 Grubu (Taze Kar)',
        'SİNOPTİK - Nöbetçi', 'METAR - Nöbetçi',
        'Hata Kodu', 'AÇIKLAMA', 'Hatalı Kod', 'Tavsiye Kod'
    ]
    existing_cols = [c for c in order if c in birlesik.columns]
    birlesik = birlesik[existing_cols]
    
    print("SİNOPTİK - Saat in columns?", "SİNOPTİK - Saat" in birlesik.columns)
    
    first_row = birlesik.to_dict('records')[0]
    print("SİNOPTİK - Saat value:", first_row.get("SİNOPTİK - Saat"))
    print("METAR - Saat value:", first_row.get("METAR - Saat"))
    
except Exception as e:
    import traceback
    traceback.print_exc()
