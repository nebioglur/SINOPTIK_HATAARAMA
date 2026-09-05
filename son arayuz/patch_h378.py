import re

with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace block
old_block = r'''                    if not p_row.empty:
                        for n_key in ["n_metar", "n_sin", "n", "T. Kp."]:
                            if n_key in p_row.columns:
                                val = p_row[n_key].values[0]
                                if pd.notna(val) and str(val).strip().lower() not in ["nan", "none", ""]:
                                    try: prev_n = float(val); break
                                    except: pass
                        if prev_n is not None: break

                if prev_n is not None:
                    if ww == 1 and n >= prev_n:
                        kodlar.append("h378")
                        aciklamalar.append(f"ww=01 (Bulutlar azalýyor) kodlanmýþ ancak önceki rasata göre bulutluluk azalmamýþ (Önceki N={int(prev_n)}, Güncel N={int(n)}).")
                    elif ww == 2 and n != prev_n:
                        kodlar.append("h378")
                        aciklamalar.append(f"ww=02 (Deðiþiklik yok) kodlanmýþ ancak önceki rasata göre bulutluluk deðiþmiþ (Önceki N={int(prev_n)}, Güncel N={int(n)}).")
                    elif ww == 3 and n <= prev_n:
                        kodlar.append("h378")
                        aciklamalar.append(f"ww=03 (Bulutlar artýyor) kodlanmýþ ancak önceki rasata göre bulutluluk artmamýþ (Önceki N={int(prev_n)}, Güncel N={int(n)}).")'''

new_block = r'''                    if not p_row.empty:
                        for n_key in ["n_metar", "n_sin", "n", "T. Kp."]:
                            if n_key in p_row.columns:
                                val = p_row[n_key].values[0]
                                if pd.notna(val) and str(val).strip().lower() not in ["nan", "none", ""]:
                                    try: prev_n = float(val); break
                                    except: pass
                        for h_key in ["h"]:
                            if h_key in p_row.columns:
                                val_h = p_row[h_key].values[0]
                                if pd.notna(val_h) and str(val_h).strip().lower() not in ["nan", "none", ""]:
                                    try: prev_h = float(val_h); break
                                    except: pass
                        if prev_n is not None: break

                if prev_n is not None:
                    expected_ww = 2
                    if n < prev_n: expected_ww = 1
                    elif n > prev_n: expected_ww = 3
                    else:
                        if prev_h is not None and pd.notna(h):
                            try:
                                h_val = float(h)
                                if h_val > prev_h: expected_ww = 1
                                elif h_val < prev_h: expected_ww = 3
                            except: pass

                    if ww != expected_ww and ww in [1, 2, 3]:
                        kodlar.append("h378")
                        if expected_ww == 1:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmýþ ancak önceki rasata göre bulutluluk azalmýþ veya yüksekliði artmýþ (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=01]")
                        elif expected_ww == 2:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmýþ ancak önceki rasata göre bulutluluk deðiþmemiþ (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=02]")
                        elif expected_ww == 3:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmýþ ancak önceki rasata göre bulutluluk artmýþ veya yüksekliði azalmýþ (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=03]")'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("OLD BLOCK NOT FOUND")
