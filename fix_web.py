import os

arayuz_path = 'c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\arayuz.py'
with open(arayuz_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('Sonuçüları', 'Sonuçları')
content = content.replace('Sonuüları', 'Sonuçları')
content = content.replace('Sonuçlarü', 'Sonuçları')
content = content.replace('Sonuülar', 'Sonuçlar')

with open(arayuz_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('arayuz.py web page title fixed')
