import os
with open('arayuz.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_block = """            print(f"{Colors.OKCYAN}SÜTUN DÜZELTİCİ OTOMATİK OLARAK ÇALIŞTIRILIYOR...{Colors.ENDC}")
            for dosya in (sin_dosyalari + metar_dosyalari):
                if hasattr(sutun_duzeltici, "sessiz_duzelt"):
                    try:
                        sutun_duzeltici.sessiz_duzelt(dosya)
                    except Exception as e:
                        print(f"{Colors.FAIL}Hata: {os.path.basename(dosya)} düzeltilemedi - {e}{Colors.ENDC}")
                        traceback.print_exc()
                else:
                    print(f"{Colors.WARNING}Uyarı: 'sessiz_duzelt' fonksiyonu bulunamadığı için {os.path.basename(dosya)} düzeltilmedi.{Colors.ENDC}")"""

new_block = """            print(f"{Colors.OKCYAN}SÜTUN DÜZELTİCİ İPTAL EDİLDİ (Veri kaybını önlemek için)...{Colors.ENDC}")"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('arayuz.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
