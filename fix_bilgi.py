import os

arayuz_path = 'c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\arayuz.py'
with open(arayuz_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('values=("-", "-", "-", "-", "BİLGİ",', 'values=("", "-", "-", "-", "BİLGİ",')

with open(arayuz_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('arayuz.py BİLGİ row fixed')
