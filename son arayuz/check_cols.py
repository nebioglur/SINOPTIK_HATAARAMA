import os
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
import denetim_merkezi_1 as dm1
hedef = r"C:\Users\nebio\Desktop\check"
s = dm1.dosya_oku_akilli(os.path.join(hedef, "SinTum ocak 2026.xls"))
m = dm1.dosya_oku_akilli(os.path.join(hedef, "MetarTum ocak 2026.xls"))
print("SINOPTİK SÜTUNLAR:", s.columns.tolist())
print("METAR SÜTUNLAR:", m.columns.tolist())
