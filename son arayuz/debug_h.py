# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

inject = """
                if prev_n is not None:
                    # Let's print out all column names of p_row that contain 'h' to see what they are!
                    h_cols = [c for c in p_row.columns if 'h' in str(c).lower()]
                    with open('h_cols_debug.txt', 'a', encoding='utf-8') as fdbg:
                        fdbg.write(f"p_row cols with h: {h_cols}\\n")
"""

old_block = """                if prev_n is not None:
                    expected_ww = 2"""

if old_block in content:
    content = content.replace(old_block, inject + "                    expected_ww = 2")
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
