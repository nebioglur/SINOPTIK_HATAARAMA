import os

# Fix detail view format
arayuz_path = 'c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\arayuz.py'
with open(arayuz_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('f"ş {str(col).upper()}', 'f"• {str(col).upper()}')

with open(arayuz_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('arayuz.py detail format fixed')

# Fix h378 logic
dm2_path = 'c:\\Windows.old.000\\Users\\nebio\\Desktop\\tum\\HATARAMA\\denetim_merkezi_2.py'
with open(dm2_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                    if hata_var and n == prev_n and not h_kiyas_yapilabildi and ww in [1, 3]:
                        hata_var = False'''
replacement = '''                    if hata_var and n == prev_n and not h_kiyas_yapilabildi and ww in [1, 3]:
                        hata_var = False
                    
                    # N ve h değişmese bile, bulut tipi değişimi (CB->CU vs) nedeniyle
                    # ww=01 (incelme) veya ww=03 (artma) girilmesi meteorolojik olarak mümkündür.
                    if hata_var and n == prev_n and h_kiyas_yapilabildi:
                        try:
                            if float(h) == prev_h and ww in [1, 3]:
                                hata_var = False
                        except:
                            pass'''

if target in content:
    content = content.replace(target, replacement)
    with open(dm2_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('denetim_merkezi_2.py h378 fixed')
else:
    print('Could not find target in denetim_merkezi_2.py')
