import os
import sys
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

sys.path.append(r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\son arayuz")
import denetim_merkezi_1 as dm1

hedef = r"C:\Users\nebio\Desktop\check"
sin_dosyalar = [os.path.join(hedef, f) for f in os.listdir(hedef) if f.lower().endswith('.xlsx') and 'sinoptik' in f.lower()]
metar_dosyalar = [os.path.join(hedef, f) for f in os.listdir(hedef) if f.lower().endswith('.xlsx') and 'metar' in f.lower()]

try:
    bdf, summary = dm1.dosyalari_oku_ve_birlestir(sin_dosyalar, metar_dosyalar)
    
    # Check what we have for sayfa "31.01.2026" or "31" and gmt "1500"
    for s in bdf['sayfa'].unique():
        if "31" in str(s):
            print(f"Found sayfa: {s}")
            subset = bdf[(bdf['sayfa'] == s)]
            print("All GMTs in this sayfa:")
            print(subset['gmt'].unique())
            
            p_row = subset[subset['gmt'] == '1500']
            print("\nRows for 1500:")
            print(p_row[['sayfa', 'gmt', 'n_sin', 'h_sin', 'n_metar', 'h_metar', 'dosya_turu', 'n', 'h']])
except Exception as e:
    import traceback
    traceback.print_exc()
