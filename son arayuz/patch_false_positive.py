# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# We will just replace the "if ww != expected_ww and ww in [1, 2, 3]:" line
old_line = "if ww != expected_ww and ww in [1, 2, 3]:"
new_line = """h_kiyas_yapilabildi = ('prev_h' in locals() and prev_h is not None and pd.notna(h))
                    hata_var = (ww != expected_ww and ww in [1, 2, 3])
                    # Eğer N aynıysa ve geçmiş h yoksa, kullanıcının girdiği ww=01 veya 03 değerini YANLIŞ sayma!
                    if hata_var and n == prev_n and not h_kiyas_yapilabildi and ww in [1, 3]:
                        hata_var = False

                    if hata_var:"""

if old_line in content:
    content = content.replace(old_line, new_line)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
