# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """                    if ww != expected_ww and ww in [1, 2, 3]:
                        kodlar.append('h378')
                        if expected_ww == 1:
                            aciklamalar.append(f'ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk azalmış veya yüksekliği artmış (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=01]')
                        elif expected_ww == 2:
                            aciklamalar.append(f'ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk değişmemiş (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=02]')
                        elif expected_ww == 3:
                            aciklamalar.append(f'ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk artmış veya yüksekliği azalmış (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=03]')"""

new_block = """                    if ww != expected_ww and ww in [1, 2, 3]:
                        kodlar.append('h378')
                        h_str = ""
                        if 'prev_h' in locals() and prev_h is not None and pd.notna(h):
                            try: h_str = f", Önceki h={int(prev_h)}, Güncel h={int(float(h))}"
                            except: pass
                            
                        if expected_ww == 1:
                            aciklamalar.append(f'ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk azalmış veya yüksekliği artmış (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=01]')
                        elif expected_ww == 2:
                            aciklamalar.append(f'ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk değişmemiş (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=02]')
                        elif expected_ww == 3:
                            aciklamalar.append(f'ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk artmış veya yüksekliği azalmış (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=03]')"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
