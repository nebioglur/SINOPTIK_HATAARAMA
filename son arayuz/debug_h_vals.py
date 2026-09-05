# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

inject = """
                    h_cols = [c for c in p_row.columns if 'h' in str(c).lower()]
                    with open('h_cols_debug.txt', 'a', encoding='utf-8') as fdbg:
                        for col in h_cols:
                            fdbg.write(f"val in {col}: {p_row[col].values[0]}\\n")
"""

old_block = """                    h_cols = [c for c in p_row.columns if 'h' in str(c).lower()]
                    with open('h_cols_debug.txt', 'a', encoding='utf-8') as fdbg:
                        fdbg.write(f"p_row cols with h: {h_cols}\\n")"""

if old_block in content:
    content = content.replace(old_block, inject)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
