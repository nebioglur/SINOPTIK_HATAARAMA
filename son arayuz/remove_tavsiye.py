# coding: utf-8
with open('arayuz.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'if str(col).upper() == "AÇIKLAMA":' in line:
        skip = True
    if skip and 'text_alan.insert("1.0"' in line:
        skip = False
    
    if not skip:
        new_lines.append(line)

if len(new_lines) != len(lines):
    with open('arayuz.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("SUCCESS, removed", len(lines) - len(new_lines), "lines")
else:
    print("NOT FOUND")
