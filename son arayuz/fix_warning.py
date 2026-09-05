import re
with open('arayuz.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(r"str.contains(r'\b(SPECI|SP|S)\b', case=False, na=False)", r"str.contains(r'\b(?:SPECI|SP|S)\b', case=False, na=False)")
content = content.replace(r"str.contains(r'\bSPECI\b', case=False, na=False)", r"str.contains(r'\b(?:SPECI)\b', case=False, na=False)")

with open('arayuz.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
