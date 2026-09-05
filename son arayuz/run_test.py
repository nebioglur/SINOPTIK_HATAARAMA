import os
import sys
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

CURRENT_DIR = r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\son arayuz"
PARENT_DIR = r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA"

if CURRENT_DIR not in sys.path: sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path: sys.path.append(PARENT_DIR)

import denetim_merkezi_1 as dm1
import denetim_merkezi_2 as dm2

hedef = r"C:\Users\nebio\Desktop\check"
sin_dosyalar = [os.path.join(hedef, f) for f in os.listdir(hedef) if f.lower().endswith('.xls') or f.lower().endswith('.xlsx')]
sin_dosyalar = [f for f in sin_dosyalar if 'sin' in os.path.basename(f).lower() or 'synop' in os.path.basename(f).lower() or 'sinoptik' in os.path.basename(f).lower()]

metar_dosyalar = [os.path.join(hedef, f) for f in os.listdir(hedef) if f.lower().endswith('.xls') or f.lower().endswith('.xlsx')]
metar_dosyalar = [f for f in metar_dosyalar if 'metar' in os.path.basename(f).lower()]

bdf = None
try:
    from concurrent.futures import ThreadPoolExecutor
    bdf_list = []
    with ThreadPoolExecutor() as executor:
        for s in sin_dosyalar:
            bdf_list.append(executor.submit(dm1.dosya_oku_akilli, s).result())
        for m in metar_dosyalar:
            bdf_list.append(executor.submit(dm1.dosya_oku_akilli, m).result())
    bdf = pd.concat([df for df in bdf_list if df is not None and not df.empty], ignore_index=True)
    yeni_kolonlar = [dm1.sutun_adi_normalize_et(c) for c in bdf.columns]
    bdf.columns = yeni_kolonlar
    if 'sayfa' in bdf.columns: bdf['sayfa'] = bdf['sayfa'].astype(str)
    if 'gmt' in bdf.columns: bdf['gmt'] = bdf['gmt'].astype(str)
except Exception as e:
    pass

if bdf is not None:
    if 'dosya_turu' in bdf.columns:
        df_metar = bdf[bdf['dosya_turu'] == 'metar'].copy()
    else:
        df_metar = pd.DataFrame()

    try:
        # hata_analizi_yap mutates and returns the DataFrame with 'hata_kodlari' and 'hata_aciklamalari'
        bdf_result = dm2.hata_analizi_yap(bdf, df_metar)
        
        found = False
        # Let's inspect the row for sayfa containing '31' and gmt '1800'
        subset = bdf_result[(bdf_result['sayfa'].str.contains('31', na=False)) & (bdf_result['gmt'] == '1800')]
        
        for idx, row in subset.iterrows():
            kodlar = str(row.get('hata_kodlari', ''))
            aciklama = str(row.get('hata_aciklamalari', ''))
            if 'h378' in kodlar:
                print(f"FOUND h378 at {row.get('sayfa')} 1800:")
                print(aciklama)
                found = True
        
        if not found:
            print("\nNO h378 error at 1800 on 31.01.2026 found in the current run! YAY!")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

