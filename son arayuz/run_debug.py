import os
import sys

CURRENT_DIR = r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\son arayuz"
PARENT_DIR = r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA"
if CURRENT_DIR not in sys.path: sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path: sys.path.append(PARENT_DIR)

import arayuz

# Make it non-blocking if possible? Or just call the function manually!
import denetim_merkezi_2 as dm2
import denetim_merkezi_1 as dm1
import pandas as pd

hedef = r"C:\Users\nebio\Desktop\check"
s = dm1.dosya_oku_akilli(os.path.join(hedef, "SinTum ocak 2026.xls"))
m = dm1.dosya_oku_akilli(os.path.join(hedef, "MetarTum ocak 2026.xls"))
birlesik = pd.merge(s, m, on=["sayfa", "gmt"], how="outer", suffixes=('_sin', '_metar'))

# Set up dummy values required by hata_analizi_yap
from types import SimpleNamespace
# To capture the print output and avoid UI crashes
print("Running hata_analizi_yap...")

if os.path.exists('p_row_DEBUG.txt'):
    os.remove('p_row_DEBUG.txt')

dm2.hata_analizi_yap(birlesik, {}, lambda *args: None)
