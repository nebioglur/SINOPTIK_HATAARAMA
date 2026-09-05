# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block1 = """                        if expected_ww == 1:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk azalmış veya yüksekliği artmış (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=01]")
                        elif expected_ww == 2:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk değişmemiş (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=02]")
                        elif expected_ww == 3:
                            aciklamalar.append(f"ww={int(ww):02d} kodlanmış ancak önceki rasata göre bulutluluk artmış veya yüksekliği azalmış (Önceki N={int(prev_n)}, Güncel N={int(n)}{h_str}). [TAVSIYE_WW=03]")"""

new_block1 = """                        # GEÇMİŞ SİNOPTİK BİLGİSİNİ MESAJIN ALTINA EKLEYELİM
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

if old_block1 in content:
    content = content.replace(old_block1, new_block1)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
