with open('c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\arayuz.py', 'r', encoding='utf-8') as f:
    content = f.read()

fixes = {
    'text="ü"': 'text="☐"',
    '== "ü"': '== "☐"',
    '"ş" if current': '"☑" if current',
    '"ü" if secili_mi else ""': '"☑" if secili_mi else "☐"',
    '"ü⚡': '"🔍',
    'ü⚡ ': '🔍 ',
    'Aİşklama': 'Açıklama',
    'Kural Aİşklaması': 'Kural Açıklaması',
    'values=("ü",': 'values=("☐",',
    'values=("ş",': 'values=("☑",',
    '"ü" if secili': '"☑" if secili',
    'else "ü"': 'else "☐"'
}

for k, v in fixes.items():
    content = content.replace(k, v)

with open('c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\arayuz.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Checkboxes!")
