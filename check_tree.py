import pandas as pd
import sys
sys.path.insert(0, r"c:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA")
import denetim_merkezi_1 as dm1
import denetim_merkezi_2 as dm2

try:
    df_sin = dm1.dosya_oku_akilli(r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\check\SinTum.xls")
    df_met = dm1.dosya_oku_akilli(r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\check\MetTum.xls")
except:
    df_met = pd.DataFrame(columns=["sayfa", "gmt"])

if not df_sin.empty:
    birlesik = pd.merge(df_sin, df_met, on=["sayfa", "gmt"], how="left", suffixes=('_sin', '_met'))
    
    def extract_metar_time(row):
        try:
            for col in ["_raw_line_met", "bulten_met", "_raw_line", "bulten"]:
                if col in row and pd.notna(row[col]):
                    import re
                    m = re.search(r" \d{2}(\d{4})Z\b", str(row[col]).upper())
                    if m: return m.group(1)
        except: pass
        return "-"

    def format_sin_time(row):
        try:
            return f"{int(float(row.get('gmt', 0))):02d}00"
        except: return "-"

    if "Saat_sin" in birlesik.columns: birlesik["SİNOPTİK - Saat"] = birlesik["Saat_sin"]
    else: birlesik["SİNOPTİK - Saat"] = birlesik.apply(format_sin_time, axis=1)
        
    if "Saat_met" in birlesik.columns: birlesik["METAR - Saat"] = birlesik["Saat_met"]
    else: birlesik["METAR - Saat"] = birlesik.apply(extract_metar_time, axis=1)
    
    # After hata_analizi_yap
    # birlesik = dm2.hata_analizi_yap(birlesik, df_met)
    
    # Just check columns directly
    col_map = {
        'sayfa': 'Tarih', 'gmt': 'Saat (GMT)', 'gmt_exact_sin': 'SİNOPTİK - Saat', 'gmt_exact_metar': 'METAR - Saat',
    }
    birlesik = birlesik.rename(columns=col_map)
    order = ['Tarih', 'Saat (GMT)', 'SİNOPTİK - Saat', 'METAR - Saat']
    existing_cols = [c for c in order if c in birlesik.columns]
    birlesik = birlesik[existing_cols]
    
    recs = birlesik.to_dict('records')
    print("SİNOPTİK - Saat in first record:", recs[0].get("SİNOPTİK - Saat"))
