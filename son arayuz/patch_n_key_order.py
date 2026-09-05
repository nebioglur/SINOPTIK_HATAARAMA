# coding: utf-8
with open('denetim_merkezi_2.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# We will replace the n_key loop to prioritize SYNOP N
old_line = 'for n_key in ["n_metar", "n_sin", "n", "T. Kp."]:'
new_line = 'for n_key in ["n_sin", "n", "n_metar", "T. Kp."]:'

if old_line in content:
    content = content.replace(old_line, new_line)
    with open('denetim_merkezi_2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
