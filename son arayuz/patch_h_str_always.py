# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_block = """                        h_str = ""
                        if 'prev_h' in locals() and prev_h is not None and pd.notna(h):
                            try: h_str = f", Önceki h={int(prev_h)}, Güncel h={int(float(h))}"
                            except: pass"""

new_block = """                        # Her zaman h değerlerini yazalım ki kullanıcı nedenini anlasın
                        p_h_val = int(prev_h) if ('prev_h' in locals() and prev_h is not None) else "Bilinmiyor/Yok"
                        c_h_val = "Bilinmiyor/Yok"
                        if pd.notna(h):
                            try: c_h_val = int(float(h))
                            except: pass
                        h_str = f", Önceki h={p_h_val}, Güncel h={c_h_val}"
"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
