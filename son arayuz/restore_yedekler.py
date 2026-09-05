import os
import shutil

hedef = r"C:\Users\nebio\Desktop\check"
yedek_klasoru = os.path.join(hedef, "orijinal_yedekler")

if os.path.exists(yedek_klasoru):
    for dosya in os.listdir(yedek_klasoru):
        if dosya.endswith('.xlsx'):
            kaynak = os.path.join(yedek_klasoru, dosya)
            hedef_dosya = os.path.join(hedef, dosya)
            shutil.copy2(kaynak, hedef_dosya)
            print(f"Restored: {dosya}")
else:
    print("Yedek klasoru bulunamadi.")
