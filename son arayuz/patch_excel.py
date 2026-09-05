# coding: utf-8
with open('arayuz.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """        df_export = pd.DataFrame(veri, columns=cols[1:])
        df_export.to_excel(dosya_yolu, index=False)"""

new_block = """        df_export = pd.DataFrame(veri, columns=cols[1:])
        
        with pd.ExcelWriter(dosya_yolu, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Hata Raporu')
            
            workbook  = writer.book
            worksheet = writer.sheets['Hata Raporu']
            
            # Format tanimlari
            header_format = workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
                'fg_color': '#4F81BD', 'font_color': 'white', 'border': 1
            })
            
            cell_format = workbook.add_format({
                'border': 1, 'valign': 'vcenter', 'text_wrap': True
            })
            
            # Ust basliklari formatla
            for col_num, value in enumerate(df_export.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Hucre formatlarini uygula
            for row in range(1, len(df_export) + 1):
                worksheet.set_row(row, 25)
                for col_num in range(len(df_export.columns)):
                    val = df_export.iloc[row-1, col_num]
                    # Nan check and replace
                    if pd.isna(val): val = ""
                    worksheet.write(row, col_num, str(val), cell_format)
                    
            worksheet.set_row(0, 30) # Baslik satiri genis
            
            # Sutun genislikleri
            worksheet.set_column(0, 0, 11) # Tarih
            worksheet.set_column(1, 1, 6)  # Saat
            worksheet.set_column(2, 2, 8)  # Hata Kodu
            worksheet.set_column(3, 3, 35) # Aciklama
            worksheet.set_column(4, 4, 12) # Hatali Kod
            worksheet.set_column(5, 5, 12) # Tavsiye Kod
            worksheet.set_column(6, 6, 40) # Sinoptik
            worksheet.set_column(7, 7, 40) # Metar
            worksheet.set_column(8, 8, 10) # Aksiyon (varsa)
            
            # Yazdirma ayarlari: Yatay A4, kenar bosluklari
            worksheet.set_paper(9) # 9 = A4 paper
            worksheet.set_landscape()
            worksheet.set_margins(left=0.3, right=0.3, top=0.5, bottom=0.5)
            worksheet.fit_to_pages(1, 0) # Genisligi 1 sayfaya sigdir, uzunluk ne kadarsa o kadar
            worksheet.repeat_rows(0) # Her sayfada ust basligi tekrarla"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('arayuz.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
