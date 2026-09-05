# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_block = """                        for h_key in ["h_sin", "h", "h_metar", "alcak_bulut_yuksekligi"]:
                            if h_key in p_row.columns:
                                val_h = p_row[h_key].values[0]
                                if pd.notna(val_h) and str(val_h).strip().lower() not in ["nan", "none", ""]:
                                    try: prev_h = float(val_h); break
                                    except: pass"""

new_block = """                        for h_key in ["h_sin", "h", "h_metar", "alcak_bulut_yuksekligi"]:
                            if h_key in p_row.columns:
                                # p_row'da birden fazla satır olabilir (METAR ve SINOPTİK).
                                # Sadece ilk satıra değil, tüm satırlara bakalım, dolu olanı alalım!
                                for val_h in p_row[h_key].values:
                                    if pd.notna(val_h) and str(val_h).strip().lower() not in ["nan", "none", ""]:
                                        try: 
                                            prev_h = float(val_h)
                                            break
                                        except: pass
                                if prev_h is not None: break"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS (h_key)")
else:
    print("NOT FOUND (h_key)")

old_block_n = """                        for n_key in ["n_sin", "n", "n_metar", "T. Kp."]:
                            if n_key in p_row.columns:
                                val = p_row[n_key].values[0]
                                if pd.notna(val) and str(val).strip().lower() not in ["nan", "none", ""]:
                                    try: prev_n = float(val); break
                                    except: pass"""

new_block_n = """                        for n_key in ["n_sin", "n", "n_metar", "T. Kp."]:
                            if n_key in p_row.columns:
                                for val in p_row[n_key].values:
                                    if pd.notna(val) and str(val).strip().lower() not in ["nan", "none", ""]:
                                        try: 
                                            prev_n = float(val)
                                            break
                                        except: pass
                                if prev_n is not None: break"""

if old_block_n in content:
    content = content.replace(old_block_n, new_block_n)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS (n_key)")
else:
    print("NOT FOUND (n_key)")

