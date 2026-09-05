# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I will replace or h_key in ["h"]: with or h_key in ["h_sin", "h", "h_metar", "alcak_bulut_yuksekligi"]:
old_line = 'for h_key in ["h"]:'
new_line = 'for h_key in ["h_sin", "h", "h_metar", "alcak_bulut_yuksekligi"]:'

if old_line in content:
    content = content.replace(old_line, new_line)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
