import os

arayuz_path = 'c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\arayuz.py'
with open(arayuz_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                    display_cols = ["GÜN", "SAAT", "HATA KODU", "AÇIKLAMA"]
                    mevcut_cols = [c for c in display_cols if c in hatali_kayitlar.columns]
                    html_df = hatali_kayitlar[mevcut_cols] if mevcut_cols else hatali_kayitlar'''

replacement = '''                    # Kullanıcı İncele sekmesindeki tüm detayları görmek istediği için filtreyi kaldırdık
                    html_df = hatali_kayitlar.copy()
                    
                    # Fazla gereksiz veya kafa karıştırıcı sütunları gizleyelim
                    cols_to_drop = ["Seç"]
                    for c in cols_to_drop:
                        if c in html_df.columns:
                            html_df = html_df.drop(columns=[c])'''

if target in content:
    content = content.replace(target, replacement)
    with open(arayuz_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Web report columns expanded!")
else:
    # try uppercase backup or different spacing
    import re
    content = re.sub(
        r'display_cols = \["GÜN", "SAAT", "HATA KODU", "AÇIKLAMA"\].*?html_df = hatali_kayitlar\[mevcut_cols\] if mevcut_cols else hatali_kayitlar',
        replacement,
        content,
        flags=re.DOTALL
    )
    with open(arayuz_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Web report columns expanded using regex!")
