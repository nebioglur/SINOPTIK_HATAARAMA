# coding: utf-8
with open('arayuz.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """    def arsiv_sutun_guncelle():
        try:
            import sutun_duzeltici
            if hasattr(sutun_duzeltici, "arsivleri_toplu_duzelt"):
                sutun_duzeltici.arsivleri_toplu_duzelt()
            else:
                from tkinter import messagebox
                messagebox.showerror("Hata", "sutun_duzeltici modülünde arsivleri_toplu_duzelt fonksiyonu bulunamadı.")
        except ImportError:
            from tkinter import messagebox
            messagebox.showerror("Hata", "sutun_duzeltici modülü bulunamadı.")

    btn_arsiv_duzelt = tk.Button(main_frame, text="ARŞİV SÜTUNLARINI GÜNCELLE", command=arsiv_sutun_guncelle, font=("Segoe UI", 10, "bold"), bg="#FF9800", fg="black", activebackground="#F57C00", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_arsiv_duzelt.pack(fill="x", pady=(0, 8))"""

new_block = """    # ARŞİV SÜTUNLARINI GÜNCELLE butonu kaldırıldı"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('arayuz.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
