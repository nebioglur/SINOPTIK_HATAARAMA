# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

inject = """
                        # P_ROW DUMP
                        if not p_row.empty:
                            with open('p_row_dump.txt', 'a', encoding='utf-8') as fdbg:
                                fdbg.write(f"\\n--- P_ROW for {prev_sayfa} {prev_gmt} ---\\n")
                                for _, r in p_row.iterrows():
                                    for col in ['dosya_turu', 'n', 'n_sin', 'n_metar', 'h', 'h_sin', 'h_metar', 'sayfa', 'gmt']:
                                        if col in r:
                                            fdbg.write(f"{col}: {r[col]} | ")
                                    fdbg.write("\\n")
"""

old_block = """                        if "sayfa" in df_arsiv.columns and "gmt" in df_arsiv.columns:
                            p_row = df_arsiv[(df_arsiv["sayfa"] == prev_sayfa) & (df_arsiv["gmt"] == prev_gmt)]"""

if old_block in content:
    content = content.replace(old_block, old_block + inject)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
