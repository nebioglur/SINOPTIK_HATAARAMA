# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                if prev_n is not None:
                    expected_ww = 2
                    if n < prev_n: expected_ww = 1
                    elif n > prev_n: expected_ww = 3
                    else:
                        if 'prev_h' in locals() and prev_h is not None and pd.notna(h):
                            try:
                                h_val = float(h)
                                if h_val > prev_h: expected_ww = 1
                                elif h_val < prev_h: expected_ww = 3
                            except: pass

                    if ww != expected_ww and ww in [1, 2, 3]:"""

new_block = """                if prev_n is not None:
                    expected_ww = 2
                    h_kiyas_yapilabildi = False
                    if n < prev_n: 
                        expected_ww = 1
                    elif n > prev_n: 
                        expected_ww = 3
                    else:
                        if 'prev_h' in locals() and prev_h is not None and pd.notna(h):
                            try:
                                h_val = float(h)
                                h_kiyas_yapilabildi = True
                                if h_val > prev_h: expected_ww = 1
                                elif h_val < prev_h: expected_ww = 3
                            except: pass

                    # Eğer N değişmemişse ve h kıyası yapılamıyorsa (geçmiş h yoksa), ww=01 veya 03 için hata verme!
                    hata_var = False
                    if ww != expected_ww and ww in [1, 2, 3]:
                        hata_var = True
                        if n == prev_n and not h_kiyas_yapilabildi and ww in [1, 3]:
                            hata_var = False # h'yi bilmediğimiz için kullanıcının ww=01 veya 03 kodunu doğru kabul ediyoruz

                    if hata_var:"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
