# coding: utf-8
with open('arayuz.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """    def arsiv_sutun_guncelle():
        if sutun_duzeltici:
            sutun_duzeltici.arsivleri_toplu_duzelt()"""

new_block = """    def arsiv_sutun_guncelle():
        try:
            import sutun_duzeltici
            if hasattr(sutun_duzeltici, "arsivleri_toplu_duzelt"):
                sutun_duzeltici.arsivleri_toplu_duzelt()
            else:
                from tkinter import messagebox
                messagebox.showerror("Hata", "sutun_duzeltici modülünde arsivleri_toplu_duzelt fonksiyonu bulunamadı.")
        except ImportError:
            from tkinter import messagebox
            messagebox.showerror("Hata", "sutun_duzeltici modülü bulunamadı.")"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('arayuz.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
