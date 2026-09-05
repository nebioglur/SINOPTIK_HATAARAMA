# coding: utf-8
with open('arayuz.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "def dosyalari_indir_ac():" in line:
        skip = True
        # add the replacement
        new_lines.append("    def dosyalari_indir_ac():\n")
        new_lines.append("        import datetime\n")
        new_lines.append("        simdi = datetime.datetime.now()\n")
        new_lines.append("        v_ay = simdi.month\n")
        new_lines.append("        v_yil = simdi.year\n")
        new_lines.append("\n")
        new_lines.append("        indirme_yili = simpledialog.askinteger('Dosya Adının Yılı', 'Kardelen\\'den dosyaları indirirken kaydedeceğiniz dosyanın YILINI giriniz:\\n(Örn: 2026)', initialvalue=v_yil, minvalue=2000, maxvalue=2050, parent=root)\n")
        new_lines.append("        if not indirme_yili: return\n")
        new_lines.append("        indirme_ayi = simpledialog.askinteger('Dosya Adının Ayı', f'İndireceğiniz dosyaları {indirme_yili} yılı için kaydederken,\\ndosya adında kullanacağınız AYI giriniz:\\n(Örn: 1)', initialvalue=v_ay, minvalue=1, maxvalue=12, parent=root)\n")
        new_lines.append("        if not indirme_ayi: return\n")
        new_lines.append("\n")
        new_lines.append("        messagebox.showinfo('Dosya İsimlendirme', f'Kardelen açıldığında dosyaları tam olarak şu isimlerle indirmelisiniz:\\n\\nSİNOPTİK: {indirme_ayi:02d}{indirme_yili}-sinoptik.xls\\nMETAR: {indirme_ayi:02d}{indirme_yili}-metar.xls', parent=root)\n")
        new_lines.append("\n")
        new_lines.append("        dosya_oneki = f\"{indirme_ayi:02d}{indirme_yili}-\"\n")
        continue

    if skip and "dosya_oneki = f" in line:
        skip = False
        continue
    
    if not skip:
        new_lines.append(line)

with open('arayuz.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("SUCCESS")
