import pandas as pd
import sys
import datetime
sys.path.insert(0, r"c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA")
import denetim_merkezi_1 as dm1

try:
    df = dm1.dosya_oku_akilli(r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\check\SinTum.xls")
    df = df[df['sayfa'].str.match(r'\d{2}\.\d{2}\.\d{4}', na=False)]
    
    df['gmt'] = pd.to_numeric(df['gmt'], errors='coerce')
    # Simulate arayuz.py logic for NaN
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            df[col] = df[col].replace(['nan', 'NAN', 'NaN', 'None', 'NONE', '-', ' - '], "")
            df[col] = df[col].fillna("")
            
    df['dt'] = pd.to_datetime(df['sayfa'], format="%d.%m.%Y") + pd.to_timedelta(df['gmt'], unit='h')
    df = df.sort_values('dt').reset_index(drop=True)
    
    count = 0
    for i in range(1, len(df)):
        s = df.iloc[i]
        
        # Simulate get_dt_suan
        dt_s = s['dt']
        dt_prev = dt_s - datetime.timedelta(hours=3)
        p_str = dt_prev.strftime('%d.%m.%Y')
        sonuc = df[(df["sayfa"] == p_str) & (df["gmt"] == dt_prev.hour)]
        
        # Now simulate _check_pressure
        data = {
            'p': float(s['p']) if s['p'] != "" else None,
            'p0': float(s['p0']) if s['p0'] != "" else None,
            'a': float(s['a']) if s['a'] != "" else None,
            'ppp': float(s['ppp']) if s['ppp'] != "" else None
        }
        
        p, p0, a, ppp = (data.get(k) for k in ['p', 'p0', 'a', 'ppp'])
        
        if not sonuc.empty:
            prev_data = sonuc
            p_prev = prev_data["p0"].values[0] if "p0" in prev_data.columns else None
            if pd.isna(p_prev) or p_prev == "": p_prev = prev_data["p"].values[0] if "p" in prev_data.columns else None
            
            p_curr = p0
            if pd.isna(p_curr): p_curr = p
            
            if pd.notna(p_curr) and pd.notna(p_prev) and p_prev != "" and pd.notna(a) and pd.notna(ppp):
                try:
                    diff = round(float(p_curr) - float(p_prev), 1)
                    diff_abs = abs(diff)
                    
                    if abs(diff_abs - float(ppp)) >= 0.3:
                        print(f"HATA! dt: {dt_s}, p_curr: {p_curr}, p_prev: {p_prev}, diff: {diff}, ppp: {ppp}")
                        count += 1
                except Exception as ex:
                    print(f"Error on dt {dt_s}: {ex}")
                    
    print(f"Total h65 using dm2 logic: {count}")

except Exception as e:
    import traceback
    traceback.print_exc()
