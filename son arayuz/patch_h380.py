import os

fpath = r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\son arayuz\denetim_merkezi_2.py"
with open(fpath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "METAR'da Alçak veya Orta bulut katmanı var ancak SİNOPTİK Nh (Alçak/Orta Kapalılık) 0 kodlanmış." in line:
        new_lines.append(
"""
                # 6. SİNOPTİK N ile Önceki Saat METAR N Çapraz Kontrolü (h380)
                if pd.notna(n):
                    dt_s = get_dt_suan()
                    if dt_s:
                        dt_prev_metar = dt_s - datetime.timedelta(hours=1)
                        prev_sayfa_m = dt_prev_metar.strftime('%d.%m.%Y')
                        prev_gmt_m = float(dt_prev_metar.hour)
                        
                        m_row = birlesik_df[(birlesik_df["sayfa"] == prev_sayfa_m) & (birlesik_df["gmt"] == prev_gmt_m)]
                        if "mesaj_tipi" in m_row.columns:
                            m_row = m_row[m_row["mesaj_tipi"].notna()]
                            
                        if not m_row.empty:
                            m_n_val = None
                            n_col_to_check = "n_metar" if "n_metar" in m_row.columns else "n"
                            for val in m_row[n_col_to_check].values:
                                if pd.notna(val) and str(val).strip().lower() not in ["nan", "none", ""]:
                                    try:
                                        m_n_val = float(val)
                                        break
                                    except: pass
                            
                            if m_n_val is not None and n != m_n_val:
                                kodlar.append("h380")
                                aciklamalar.append(f"Güncel SİNOPTİK N ({int(n)}) değeri ile 1 saat önceki METAR'dan hesaplanan N ({int(m_n_val)}) değeri uyuşmuyor.")
"""
        )

with open(fpath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Patch applied successfully.")
