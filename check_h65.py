import pandas as pd
import sys
import datetime
sys.path.insert(0, r"c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA")
import denetim_merkezi_1 as dm1

try:
    df = dm1.dosya_oku_akilli(r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\check\SinTum.xls")
    df = df[df['sayfa'].str.match(r'\d{2}\.\d{2}\.\d{4}', na=False)]
    df['dt'] = pd.to_datetime(df['sayfa'], format="%d.%m.%Y") + pd.to_timedelta(df['gmt'], unit='h')
    df = df.sort_values('dt').reset_index(drop=True)
    
    count = 0
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        if row['dt'] - prev_row['dt'] == datetime.timedelta(hours=3):
            p0 = float(row.get('p0', float('nan')))
            p = float(row.get('p', float('nan')))
            prev_p0 = float(prev_row.get('p0', float('nan')))
            prev_p = float(prev_row.get('p', float('nan')))
            a = row.get('a')
            ppp = float(row.get('ppp', float('nan')))
            
            p_curr = p0 if not pd.isna(p0) else p
            p_prev = prev_p0 if not pd.isna(prev_p0) else prev_p
            
            if pd.notna(p_curr) and pd.notna(p_prev) and pd.notna(a) and pd.notna(ppp):
                diff = round(p_curr - p_prev, 1)
                diff_abs = abs(diff)
                
                if abs(diff_abs - ppp) >= 0.3:
                    print(f"HATA! dt: {row['dt']}, p_curr: {p_curr}, p_prev: {p_prev}, diff: {diff}, ppp: {ppp}, a: {a}")
                    count += 1
                    
    print(f"Total h65 in dataset: {count}")
except Exception as e:
    import traceback
    traceback.print_exc()
