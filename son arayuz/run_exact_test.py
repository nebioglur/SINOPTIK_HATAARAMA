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
s = os.path.join(hedef, "SinTum ocak 2026.xls")
m = os.path.join(hedef, "MetarTum ocak 2026.xls")
df_sin = dm1.dosya_oku_akilli(s)
df_metar = dm1.dosya_oku_akilli(m)

birlesik = pd.concat([df_sin, df_metar], ignore_index=True)
beklenen_sutunlar = ['p_sin', 'ff_sin', 'n_sin', 'p_metar', 'ff_metar', 'n_metar', 't_sin', 't_metar', 'td_sin', 'td_metar', 'p0_sin', 'p0_metar', 'dd_sin', 'dd_metar', 'vv_sin', 'vv_metar', 'w1_sin', 'w2_sin', 'ww_sin', 'ww_metar', 'rrr_sin', 'tr_sin', 'tx_sin', 'tn_sin', 'tg_sin', 'a_sin', 'ppp_sin']
for b in beklenen_sutunlar:
    if b not in birlesik.columns: birlesik[b] = float('nan')
    else: birlesik[b] = pd.to_numeric(birlesik[b], errors='coerce')

bdf_result = dm2.hata_analizi_yap(birlesik, df_metar)
subset = bdf_result[(bdf_result['sayfa'].str.contains('31', na=False)) & (bdf_result['gmt'] == 18.0)]
for idx, row in subset.iterrows():
    print(f"Hatalar for 31.01 1800: {row.get('hata_kodlari')}")
    print(f"Aciklama: {row.get('hata_aciklamalari')}")
