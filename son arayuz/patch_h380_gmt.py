import os

fpath = r"C:\Windows.old.000\Users\nebio\Desktop\tum\HATARAMA\son arayuz\denetim_merkezi_2.py"
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """
                        m_row = birlesik_df[(birlesik_df["sayfa"] == prev_sayfa_m) & (birlesik_df["gmt"] == prev_gmt_m)]
"""

new_code = """
                        def get_m_hour(x):
                            try:
                                s_val = str(x).strip().replace('.0', '')
                                if len(s_val) >= 3 and s_val.isdigit():
                                    if len(s_val) == 3: return float(s_val[0])
                                    return float(s_val[:2])
                                return float(x)
                            except: return -1
                            
                        m_row = birlesik_df[(birlesik_df["sayfa"] == prev_sayfa_m) & (birlesik_df["gmt"].apply(get_m_hour) == prev_gmt_m)]
"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patch applied successfully.")
else:
    print("Old code not found.")
