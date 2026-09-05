import codecs
lines = codecs.open('c:/Windows.old.000/Users/nebio/Desktop/tum/HATARAMA/arayuz.py', 'r', 'utf-8').readlines()

out = []
i = 0
while i < len(lines):
    if i == 2376:
        out.append(
'''                'tg': 'Toprak Sıcaklığı (Tg)', 'e': 'Yerin Hali (E)', 'rrr': 'Yağış Miktarı (RRR)',
                'tr': 'Yağış Süresi (tR)', 'g910': '910 Grubu (Hamle)', 'g911': '911 Grubu (Hamle)',
                'g931': '931 Grubu (Kar)', 'g932': '932 Grubu (Taze Kar)', 'g960': '960 Grubu (Hadise)', 
                'rh': 'Bağıl Nem (%)', 'tw': 'Islak Sıcaklık (Tw)', 
                'buhar': 'Buharlaşma', 'rad_tipi': 'Radyasyon Tipi', 'radyasyon': 'Radyasyon Miktarı',
                'gunes': 'Güneşlenme Süresi', 'deniz_suyu': 'Deniz Suyu Sıc.', 'rrr_toplam': 'Toplam Yağış',
                'buh_alet_tipi': 'Buhar Aleti Tipi', 'e_kar': 'Yerin Hali (Kar)',
                'top_ustu_min': 'Toprak Üstü Min.',
                'mak_deger': 'Mak',
                '1. bulut kap': '1. Bulut Kap.', '1. bulut cins': '1. Bulut Cinsi', '1. bulut yuk': '1. Bulut Yük.',
                '2. bulut kap': '2. Bulut Kap.', '2. bulut cins': '2. Bulut Cinsi', '2. bulut yuk': '2. Bulut Yük.',
                '3. bulut kap': '3. Bulut Kap.', '3. bulut cins': '3. Bulut Cinsi', '3. bulut yuk': '3. Bulut Yük.',
                '4. bulut kap': '4. Bulut Kap.', '4. bulut cins': '4. Bulut Cinsi', '4. bulut yuk': '4. Bulut Yük.',
                'ww_hesaplanan': 'RE/GEÇMİŞ HADİSE',
                'ANALİZ_SONUCU': 'DURUM', 'HATA_KODLARI': 'HATA KODU', 'HATA_ACIKLAMALARI': 'AÇIKLAMA',
                'RASATLAR': 'SİNOPTİK - Şifreli Mesaj', 'g924': '924 Grubu', 'hadise_kayit': 'Hadise Kayıtları',
                'personel': 'Personel',
                'bulten': 'METAR - Şifreli Mesaj'
            }

            new_columns = {}
            for c in birlesik.columns:
                if c == "bulten_sin":
                    new_columns[c] = "SİNOPTİK - Şifreli Mesaj"
                    continue
                if c == "bulten_metar":
                    new_columns[c] = "METAR - Şifreli Mesaj"
                    continue
                if c == "bulten":
                    new_columns[c] = "SİNOPTİK - Şifreli Mesaj"
                    continue

                base = c.replace('_sin', '').replace('_metar', '')
                suffix = '_sin' if '_sin' in c else ('_metar' if '_metar' in c else '')
                if base in col_map:
                    new_name = col_map[base]
                    if new_name.startswith("SİNOPTİK") or new_name.startswith("METAR"):
                        new_columns[c] = new_name
                    elif suffix == '_sin': new_name = f"SİNOPTİK - {new_name}"
                    elif suffix == '_metar': new_name = f"METAR - {new_name}"
                    new_columns[c] = new_name
                else:
                    if suffix == '_sin': new_columns[c] = f"SİNOPTİK - {base.upper()}"
'''
        )
        while i < len(lines) and "if suffix == '_sin': new_columns[c]" not in lines[i]:
            i += 1
        i += 1
    else:
        out.append(lines[i])
        i += 1

with codecs.open('c:/Windows.old.000/Users/nebio/Desktop/tum/HATARAMA/arayuz.py', 'w', 'utf-8') as f:
    f.writelines(out)
