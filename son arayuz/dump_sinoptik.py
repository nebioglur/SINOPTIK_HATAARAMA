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

hedef = r"C:\Users\nebio\Desktop\check"
s = os.path.join(hedef, "SinTum ocak 2026.xls")
df_sin = dm1.dosya_oku_akilli(s)
subset = df_sin[df_sin['sayfa'].str.contains('31', na=False)]
print("--- 31.01 SINOPTİK DATA ---")
print(subset[['sayfa', 'gmt', 'n', 'h', 'ww']])
