import pandas as pd
import sys
sys.path.insert(0, r"c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA")
import denetim_merkezi_1 as dm1
import os

try:
    df = dm1.dosya_oku_akilli(r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\check\SinTum.xls")
    
    # Filter for the relevant dates and GMT
    # 24.07.2026 2100Z -> gmt=21
    # 25.07.2026 0000Z -> gmt=0
    
    mask24 = (df['sayfa'].str.contains('24.07.2026') & (df['gmt'] == 21.0))
    mask25 = (df['sayfa'].str.contains('25.07.2026') & (df['gmt'] == 0.0))
    
    rows = df[mask24 | mask25]
    
    for idx, row in rows.iterrows():
        print(f"\nTarih: {row['sayfa']} GMT: {row['gmt']}")
        print(f"SİNOPTİK Mesajı: {row.get('_raw_line')}")
        print(f"a: {row.get('a')}")
        print(f"ppp: {row.get('ppp')}")
        print(f"P0: {row.get('p0')}")
        print(f"P: {row.get('p')}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
