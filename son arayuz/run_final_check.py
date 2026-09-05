import os
import sys

CURRENT_DIR = r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\son arayuz"
PARENT_DIR = r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA"
if CURRENT_DIR not in sys.path: sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path: sys.path.append(PARENT_DIR)

import denetim_merkezi_2 as dm2
import denetim_merkezi_1 as dm1
import pandas as pd

hedef = r"C:\Users\nebio\Desktop\check"
s = dm1.dosya_oku_akilli(os.path.join(hedef, "SinTum ocak 2026.xls"))
m = dm1.dosya_oku_akilli(os.path.join(hedef, "MetarTum ocak 2026.xls"))
birlesik = pd.merge(s, m, on=["sayfa", "gmt"], how="outer", suffixes=('_sin', '_metar'))

errors = []
def mock_callback(*args):
    pass

# We will patch the dm2.hata_analizi_yap to print out if h378 is generated
def my_islem_tamamlandi(hatalar, sayi, gecen_sure, u_hatalar):
    for h in hatalar:
        if h.get('hata_kodu') == 'h378' and '31.01.2026' in h.get('sayfa', ''):
            print(f"FOUND h378 in 31.01.2026! Saat: {h.get('saat')}, Aciklama: {h.get('aciklama')}")
    print(f"Total h378 in 31 Jan: {sum(1 for h in hatalar if h.get('hata_kodu') == 'h378' and '31.01.2026' in h.get('sayfa', ''))}")

dm2.hata_analizi_yap(birlesik, {}, mock_callback, my_islem_tamamlandi)
