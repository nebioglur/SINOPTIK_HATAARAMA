# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_block = """                        if n == prev_n and not h_kiyas_yapilabildi and ww in [1, 3]:
                            hata_var = False # h'yi bilmediğimiz için kullanıcının ww=01 veya 03 kodunu doğru kabul ediyoruz

                    if hata_var:
                        kodlar.append("h378")
                        
                        # Her zaman h değerlerini yazalım ki kullanıcı nedenini anlasın
                        p_h_val = int(prev_h) if ('prev_h' in locals() and prev_h is not None) else "Bilinmiyor/Yok"
                        c_h_val = "Bilinmiyor/Yok"
                        if pd.notna(h):
                            try: c_h_val = int(float(h))
                            except: pass
                        h_str = f", Önceki h={p_h_val}, Güncel h={c_h_val}"
                        
                        if expected_ww == 1:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk azalmış veya yüksekliği artmış (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=01]")
                        elif expected_ww == 2:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk değişmemiş (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=02]")
                        elif expected_ww == 3:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk artmış veya yüksekliği azalmış (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=03]")"""

new_block = """                        if n == prev_n and not h_kiyas_yapilabildi and ww in [1, 3]:
                            hata_var = False # h'yi bilmediğimiz için kullanıcının ww=01 veya 03 kodunu doğru kabul ediyoruz

                    if hata_var:
                        kodlar.append("h378")
                        
                        # Her zaman h değerlerini yazalım ki kullanıcı nedenini anlasın
                        p_h_val = int(prev_h) if ('prev_h' in locals() and prev_h is not None) else "Bilinmiyor/Yok"
                        c_h_val = "Bilinmiyor/Yok"
                        if pd.notna(h):
                            try: c_h_val = int(float(h))
                            except: pass
                        h_str = f", Önceki h={p_h_val}, Güncel h={c_h_val}"
                        
                        # GEÇMİŞ SİNOPTİK BİLGİSİNİ MESAJIN ALTINA EKLEYELİM
                        gecmis_sinoptik_ek = f"\\n\\n💡 İLGİLİ GEÇMİŞ SİNOPTİK ({prev_gmt}Z):\\nSistem tarafından arşivden okunan geçmiş değerler -> N: {int(prev_n)}, h: {p_h_val}"
                        if '_raw_line' in p_row.columns:
                            for raw_val in p_row['_raw_line'].values:
                                if pd.notna(raw_val) and str(raw_val).strip() != "":
                                    gecmis_sinoptik_ek += f"\\nŞifre: {str(raw_val).strip()}"
                                    break
                        
                        if expected_ww == 1:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk azalmış veya yüksekliği artmış (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=01]" + gecmis_sinoptik_ek)
                        elif expected_ww == 2:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk değişmemiş (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=02]" + gecmis_sinoptik_ek)
                        elif expected_ww == 3:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk artmış veya yüksekliği azalmış (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=03]" + gecmis_sinoptik_ek)"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
