with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# We want to replace lines 1298 to 1306 (0-indexed 1297 to 1305)
# Wait, let's just find the index of "if prev_n is not None:\n" that is followed by the bad code
bad_idx = -1
for i, line in enumerate(lines):
    if "if prev_n is not None:" in line and "aciklamalar.append" in lines[i+1] and "elif" in lines[i+2]:
        bad_idx = i
        break

if bad_idx != -1:
    new_block = [
        "                if prev_n is not None:\n",
        "                    expected_ww = 2\n",
        "                    if n < prev_n: expected_ww = 1\n",
        "                    elif n > prev_n: expected_ww = 3\n",
        "                    else:\n",
        "                        if 'prev_h' in locals() and prev_h is not None and pd.notna(h):\n",
        "                            try:\n",
        "                                h_val = float(h)\n",
        "                                if h_val > prev_h: expected_ww = 1\n",
        "                                elif h_val < prev_h: expected_ww = 3\n",
        "                            except: pass\n",
        "                    if ww != expected_ww and ww in [1, 2, 3]:\n",
        "                        kodlar.append('h378')\n",
        "                        if expected_ww == 1:\n",
        "                            aciklamalar.append(f'ww={int(ww):02d} kodlanmýþ ancak önceki rasata göre bulutluluk azalmýþ veya yüksekliði artmýþ (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=01]')\n",
        "                        elif expected_ww == 2:\n",
        "                            aciklamalar.append(f'ww={int(ww):02d} kodlanmýþ ancak önceki rasata göre bulutluluk deðiþmemiþ (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=02]')\n",
        "                        elif expected_ww == 3:\n",
        "                            aciklamalar.append(f'ww={int(ww):02d} kodlanmýþ ancak önceki rasata göre bulutluluk artmýþ veya yüksekliði azalmýþ (Önceki N={int(prev_n)}, Güncel N={int(n)}). [TAVSIYE_WW=03]')\n"
    ]
    lines = lines[:bad_idx] + new_block + lines[bad_idx+8:]
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("FIXED")
else:
    print("NOT FOUND")
