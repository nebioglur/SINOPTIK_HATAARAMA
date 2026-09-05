# -*- coding: utf-8 -*-
import sys
import subprocess
def ensure_lxml():
    try:
        import lxml
        import html5lib
    except ImportError:
        print("HTML AyrÄ°ÅtÃ¼rma motorlarÄ± (lxml, html5lib) eksik. Otomatik yÃ¼kleniyor...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "lxml", "html5lib"])
            print("YÃ¼kleme baÃ§arÃ¼lÃ¼!")
        except Exception as e:
            print(f"YÃ¼kleme hatasÄ±: {e}")
ensure_lxml()

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import threading
import datetime
import calendar
import os
import re
import traceback
import glob
import logging
import json
import shutil
import time

# --- MODÃœL YOLU DÃœZELTMESÄ° ---
# Bu script bir alt klasÃ¶rde ise, ana dizini Python path'ine ekle
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

import sys
import zipfile
import canli_analiz

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

# --- HEDEF KLASÃ–RÃœ DÄ°NAMÄ°K OLARAK BELÃ¼RLE (DÄ°ÅER PC'LER Ã¼Ã¼N) ---
HEDEF_KLASOR = os.path.join(os.path.expanduser("~"), "Desktop", "check")
ARSIV_KLASORU = os.path.join(HEDEF_KLASOR, "Arsiv")

# EÃ¼er klasÃ¶rler mevcut deÄŸilse otomatik olarak oluÅŸtur
try:
    if not os.path.exists(HEDEF_KLASOR):
        os.makedirs(HEDEF_KLASOR)
    if not os.path.exists(ARSIV_KLASORU):
        os.makedirs(ARSIV_KLASORU)
except Exception:
    pass
# -----------------------------------------------------------------

# --- BAD CRC-32 (BOZUK EXCEL) BYPASS HACK ---
# BazÄ± kurumsal sistemlerin Ã¼rettiÃ§i Excel dosyalarÄ±nÄ±n iÅŸ yapÄ±sÄ±nda (docProps/core.xml vb.) CRC hatalarÄ± olabilir.
# Python'un zipfile kÃ¼tÃ¼phanesinin bu durumda Ä°Åkmesini engellemek iÃ§in CRC kontrolÃ¼nÅŸ esnetiyoruz.
try:
    if hasattr(zipfile, 'ZipExtFile') and hasattr(zipfile.ZipExtFile, '_update_crc'):
        if not getattr(zipfile.ZipExtFile, '_crc_patched', False):
            _orig_update_crc = zipfile.ZipExtFile._update_crc
            def _patched_update_crc(self, newdata):
                self._expected_crc = None  # Zorla CRC kontrolÃ¼nÅŸ kapat (BadZipFile hatasÄ±nÅŸ Ã¶nler)
                return _orig_update_crc(self, newdata)
            zipfile.ZipExtFile._update_crc = _patched_update_crc
            zipfile.ZipExtFile._crc_patched = True
except Exception:
    pass
# --------------------------------------------

# --- RENKLÄ° KONSOL Ã‡IKTISI Ã¼Ã¼N ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- SYNOP_DECODER ENTEGRASYONU ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
try:
    from synop_decoder import SynopDecoder
except ImportError:
    SynopDecoder = None

try:
    from metar_decoder import MetarDecoder
except ImportError:
    MetarDecoder = None
# ----------------------------------

# --- DOSYA ONARIM SÄ°STEMÅŸ (JOKER / GENEL Ä°ÅZÃ¼M) ---
def repair_duplicate_blocks():
    if getattr(sys, 'frozen', False):
        return # EXE olarak Ã¼alÃ¼Ã¼rken .py dosyalarÄ± yoktur, bu adÄ±mÄ± atla.
    # Kontrol edilecek dosyalar ve aranan anahtar kelimeler
    files_to_check = [
        ('validator.py', 'class WeatherLogValidator'),
        ('validator.py', 'def run_all_checks(self'),
        ('denetim_merkezi_2.py', 'def hata_analizi_yap'),
        ('synop_decoder.py', 'class SynopDecoder'),
        ('metar_decoder.py', 'class MetarDecoder'),
        ('kurallar.py', 'HATA_SOZLUGU = {')
    ]
    
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        repaired_any = False
        
        for file_name, marker in files_to_check:
            file_path = os.path.join(base_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Marker'Ã¼n (sÃ¼nÃ¼f/fonksiyon tanÄ±mÄ±) geÃ¼tiÃ§i satÄ±rlarÄ± bul
                defs = [i for i, line in enumerate(lines) if marker in line and not line.strip().startswith('#')]
                
                if len(defs) > 1:
                    # OnarÄ±mdan Ã¼nce bozuk dosyanÃ¼n yedeÄŸini al (.bak uzantÃ¼lÃ¼)
                    backup_path = os.path.join(base_dir, f"{file_name}.bak")
                    shutil.copy2(file_path, backup_path)
                    
                    # Ä°kinci kopyadan sonrasÄ±nÄ± tamamen silerek dosyayÄ± onar
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines[:defs[1]])
                    repaired_any = True
        
        if repaired_any:
            # EÃ¼er herhangi bir dosya onarÄ±ldÄ±ysa Ã¶nbelleÄŸi zorla temizle
            cache_dir = os.path.join(base_dir, '__pycache__')
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir, ignore_errors=True)
    except: pass
repair_duplicate_blocks()
# -------------------------------------------------

# --- Ã¼NBELLEK TEMÄ°ZLEME SÄ°STEMÅŸ ---
def clear_pycache_on_startup():
    """Program her baÃ¼ladÄ±ÅŸÄ±nda eski .pyc Ã–nbellek dosyalarÄ±nÄ± otomatik temizler."""
    if getattr(sys, 'frozen', False):
        return # EXE olarak Ã¼alÃ¼Ã¼rken pycache temizliÃ§ine gerek yoktur.
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, '__pycache__')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir, ignore_errors=True)
    except Exception:
        pass
clear_pycache_on_startup()
# -------------------------------------------------

# --- ESKÄ° GEÄ°ÅCÅŸ DOSYALARI TEMÄ°ZLEME SÄ°STEMÅŸ ---
def cleanup_old_temp_files():
    """Eski .bak yedeklerini, log arÅŸivlerini ve geÃ¼ici Excel (TEMP_, ~$) dosyalarÄ±nÄ± otomatik temizler."""
    try:
        now = time.time()
        otuz_gun = 30 * 24 * 60 * 60
        yedi_gun = 7 * 24 * 60 * 60
        
        # 1. Uygulama dizinindeki 30 gÃ¼nden eski .bak ve log dosyalarÄ±
        base_dir = os.path.dirname(os.path.abspath(__file__))
        for f in os.listdir(base_dir):
            if f.endswith('.bak') or '.log.' in f:
                f_path = os.path.join(base_dir, f)
                if os.path.isfile(f_path) and os.stat(f_path).st_mtime < now - otuz_gun:
                    try: os.remove(f_path)
                    except: pass
                    
        # 2. Ã¼alÄ°Åma klasÃ¶rÃ¼ndeki (check) 7 gÃ¼nden eski geÃ¼ici dosyalar
        check_dir = HEDEF_KLASOR
        if os.path.exists(check_dir):
            for f in os.listdir(check_dir):
                f_path = os.path.join(check_dir, f)
                if os.path.isfile(f_path) and (f.startswith("~$") or f.upper().startswith("TEMP_")):
                    if os.stat(f_path).st_mtime < now - yedi_gun:
                        try: os.remove(f_path)
                        except: pass

        # 3. ArÅŸiv klasÃ¶rÃ¼ndeki (check\Arsiv) 90 gÃ¼nden eski arÅŸiv raporlarÄ±nÄ± otomatik temizle
        arsiv_dir = ARSIV_KLASORU
        doksan_gun = 90 * 24 * 60 * 60
        if os.path.exists(arsiv_dir):
            for root_d, dirs, files in os.walk(arsiv_dir, topdown=False):
                for f in files:
                    f_path = os.path.join(root_d, f)
                    if os.stat(f_path).st_mtime < now - doksan_gun:
                        try: os.remove(f_path)
                        except: pass
                # Ä°Åi boÅŸalan arÅŸiv klasÃ¶rlerini (YYYY_MM) sil
                if not os.listdir(root_d) and root_d != arsiv_dir:
                    try: os.rmdir(root_d)
                    except: pass
    except Exception:
        pass
cleanup_old_temp_files()
# -------------------------------------------------

# --- ESKÄ° XLS DOSYALARINI SÃ¼LME (SADECE EN YENÄ°LERÄ° TUT) ---
def sadece_en_yeni_dosyalari_tut():
    """CHECK klasÃ¶rÃ¼ndeki eski tarihli METAR ve SÄ°NOPTÄ°K dosyalarÄ±nÄ± program aÄ°ÅlÃ¼Ã¼nda siler."""
    hedef_klasor = HEDEF_KLASOR
    if not os.path.exists(hedef_klasor): return
    
    try:
        sin_dosyalari = []
        metar_dosyalari = []
        
        for f in os.listdir(hedef_klasor):
            tam_yol = os.path.join(hedef_klasor, f)
            if not os.path.isfile(tam_yol): continue
            
            f_upper = f.upper()
            if f_upper.startswith("~$") or f_upper.startswith("TEMP_"): continue
            
            if f_upper.endswith('.XLS') or f_upper.endswith('.XLSX') or f_upper.endswith('.HTML') or f_upper.endswith('.CSV'):
                if "SIN" in f_upper or "SÄ°N" in f_upper:
                    sin_dosyalari.append(tam_yol)
                elif "METAR" in f_upper:
                    metar_dosyalari.append(tam_yol)
                    
        # En yenileri bulmak iÃ§in tarihe gÃ¶re sÄ±rala
        sin_dosyalari.sort(key=os.path.getmtime, reverse=True)
        metar_dosyalari.sort(key=os.path.getmtime, reverse=True)
        
        # En yeni 1 SÄ°NOPTÄ°K hariÃ§ diÄŸerlerini sil
        for eski_f in sin_dosyalari[1:]:
            try: os.remove(eski_f)
            except: pass
            
        # En yeni 1 METAR hariÃ§ diÄŸerlerini sil
        for eski_f in metar_dosyalari[1:]:
            try: os.remove(eski_f)
            except: pass
    except: pass

sadece_en_yeni_dosyalari_tut()
# -------------------------------------------------

try:
    import validator
    import kurallar
    import importlib
    importlib.reload(validator)
    importlib.reload(kurallar)
except ImportError:
    validator = None
    kurallar = None

console_mode = os.environ.get("HEADLESS_MODE", "0") == "1"
iptal_istendi = False
btn_cancel = None

def safe_showerror(title, message):
    try:
        if console_mode:
            print(f"ERROR - {title}: {message}")
        else:
            messagebox.showerror(title, message)
    except Exception:
        print(f"ERROR - {title}: {message}")


def safe_showinfo(title, message):
    try:
        if console_mode:
            print(f"INFO - {title}: {message}")
        else:
            messagebox.showinfo(title, message)
    except Exception:
        print(f"INFO - {title}: {message}")

def safe_askinteger(title, prompt, initialvalue):
    if console_mode:
        return initialvalue
    
    result = [None]
    event = threading.Event()
    
    def _ask():
        import tkinter.simpledialog as simpledialog
        result[0] = simpledialog.askinteger(title, prompt, initialvalue=initialvalue, parent=root)
        event.set()
        
    try:
        root.after(0, _ask)
        event.wait()
        return result[0]
    except Exception as e:
        print(f"Error asking integer: {e}")
        return initialvalue

# EXE UYUMLULUÄU: Yetki hatalarÄ±nÄ± Ã¶nlemek iÃ§in Log ve Ayar dosyalarÄ±nÄ± AppData/KullanÄ±cÄ± dizinine al
import config_manager
log_dosyasi = config_manager.setup_logging("denetim_merkezi.log", level=logging.DEBUG)

# Geriye dÃ¶nÃ¼k uyumluluk iÃ§in active handler referansÄ± (flush iÅŸlemleri iÃ§in)
logging_handler = logging.getLogger().handlers[0] if logging.getLogger().handlers else logging.NullHandler()

def thread_exception_handler(args):
    logging.error("ARKA PLAN Ä°ÅLEM HATASI (THREAD CRASH):", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
threading.excepthook = thread_exception_handler
# -------------------------------------------------------------------------

SETTINGS_FILE = os.path.join(config_manager.USER_DATA_DIR, 'ayarlar.json')

def ayarlari_yukle():
    """KayÄ±tlÅŸ ayarlarÅŸ json dosyasÄ±ndan okur."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Ayarlar dosyasÄ± okunamadÄ±: {e}")
    return {}

def ayarlari_kaydet(ayarlar):
    """Mevcut seÃ§imleri json dosyasÄ±na kaydeder."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(ayarlar, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.warning(f"Ayarlar dosyasÄ± kaydedilemedi: {e}")

def get_button_text():
    return "RAPOR OLUÅTUR"

def safe_after(delay, func):
    """Python 3.13 ve Threading kaynaklÄ± 'main thread is not in main loop' hatasÄ±nÅŸ Ã¶nler."""
    try:
        if not console_mode and 'root' in globals() and root:
            root.after(delay, func)
    except RuntimeError:
        try: func() # Olay dÃ¶ngÃ¼sÅŸ dÄ±ÅŸÄ±nda kalÄ±ndÄ±ysa doÄŸrudan Ã¼alÄ°ÅtÃ¼r
        except: pass

def arayuzde_goster(birlesik, hatali_kayitlar, sinoptik_sayisi, metar_normal_sayisi, speci_sayisi, ay, yil):
    if iptal_istendi: return
    pencere = tk.Toplevel(root)
    pencere.title(f"DetaylÄ± Test Raporu - {ay}/{yil}")
    pencere.geometry("1200x650")
    pencere.configure(bg="#F8F9FA")
                
    top_ctrl = tk.Frame(pencere, bg="#ECEFF1", pady=5)
    top_ctrl.pack(fill="x", side="top")
    tk.Label(top_ctrl, text="  SÄ°NOPTÄ°K / METAR ANALÄ°Z ARAYÃœZÃœ", font=("Segoe UI", 11, "bold"), bg="#ECEFF1", fg="#37474F").pack(side="left")
    tk.Button(top_ctrl, text="âœ– KAPAT", command=pencere.destroy, bg="#D32F2F", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10).pack(side="right", padx=5)
    tk.Button(top_ctrl, text="âš¡ TAM EKRAN", command=lambda: pencere.state('zoomed') if pencere.state() != 'zoomed' else pencere.state('normal'), bg="#90A4AE", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10).pack(side="right", padx=5)
    tk.Button(top_ctrl, text="ğŸ—• SÄ°MGE DURUMU", command=pencere.iconify, bg="#90A4AE", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10).pack(side="right", padx=5)
                
    def ekrandakileri_excele_aktar():
        dosya_yolu = filedialog.asksaveasfilename(
            parent=pencere,
            defaultextension=".xlsx",
            filetypes=[("Excel DosyasÄ±", "*.xlsx")],
            initialfile=f"Filtrelenmis_Rapor_{ay}_{yil}.xlsx",
            title="Excel Olarak Kaydet"
        )
        if not dosya_yolu: return
                    
        try:
            veri = []
            for item in tree.get_children():
                vals = tree.item(item, "values")
                if vals[0] == "â˜":
                    veri.append(vals[1:])
                        
            if not veri:
                if messagebox.askyesno("UyarÃ¼", "HiÃ§bir kayÄ±t seÃ§ilmemiÅŸ (Ã¼). Ekranda gÃ¶rÃ¼nen TÃœM kayÄ±tlar dÄ°Åa aktarÄ±lsÄ±n mÃ¼", parent=pencere):
                    for item in tree.get_children():
                        veri.append(tree.item(item, "values")[1:])
                else:
                    return
                        
            if not veri:
                messagebox.showwarning("UyarÃ¼", "AktarÄ±lacak veri yok.", parent=pencere)
                return
                        
            df_export = pd.DataFrame(veri, columns=cols[1:])
            
            with pd.ExcelWriter(dosya_yolu, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Hata Raporu')
                
                workbook  = writer.book
                worksheet = writer.sheets['Hata Raporu']
                
                # Format tanÃ¼mlarÃ¼
                header_format = workbook.add_format({
                    'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
                    'fg_color': '#4F81BD', 'font_color': 'white', 'border': 1
                })
                
                cell_format = workbook.add_format({
                    'border': 1, 'valign': 'vcenter', 'text_wrap': True
                })
                
                # Ã¼st baÄŸlÄ±klarÅŸ formatla
                for col_num, value in enumerate(df_export.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    
                # HÃ¼cre formatlarÃ¼nÅŸ uygula
                for row in range(1, len(df_export) + 1):
                    worksheet.set_row(row, 35) # SatÄ±r yÃ¼ksekliÃ§ini artÃ¼rdÃ¼m
                    for col_num in range(len(df_export.columns)):
                        val = df_export.iloc[row-1, col_num]
                        if pd.isna(val): val = ""
                        worksheet.write(row, col_num, str(val), cell_format)
                        
                worksheet.set_row(0, 30) # BaÅŸlÄ±k satÄ±rÄ± yÃ¼ksekliÃ§i
                
                # SÃ¼tun geniÅŸlikleri (A4'e sÄ±ÄŸacak ÅŸekilde optimize edildi)
                worksheet.set_column(0, 0, 11) # Tarih
                worksheet.set_column(1, 1, 6)  # Saat
                worksheet.set_column(2, 2, 8)  # Hata Kodu
                worksheet.set_column(3, 3, 35) # AÄ°Åklama
                worksheet.set_column(4, 4, 12) # HatalÄ± Kod
                worksheet.set_column(5, 5, 12) # Tavsiye Kod
                worksheet.set_column(6, 6, 40) # Sinoptik
                worksheet.set_column(7, 7, 40) # Metar
                if len(df_export.columns) > 8:
                    worksheet.set_column(8, 8, 10) # Aksiyon
                
                # YazdÄ±rma ayarlarÃ¼: Yatay A4, kenar boÅŸluklarÅŸ dar
                worksheet.set_paper(9) # 9 = A4 paper
                worksheet.set_landscape()
                worksheet.set_margins(left=0.3, right=0.3, top=0.5, bottom=0.5)
                worksheet.fit_to_pages(1, 0) # GeniÃ¼liÃ§i 1 sayfaya sÄ°ÅdÃ¼r
                worksheet.repeat_rows(0) # Her sayfada Ã¼st baÃ¼lâš™ tekrarla
                
                # Sayfa dÃ¼zeni gÃ¶rÃ¼nÃ¼mÅŸ (isteÄŸe baÄŸlÄ±, normal gÃ¶rÃ¼nÃ¼m daha iyidir)
                # worksheet.set_page_view()
            messagebox.showinfo("BaÅŸarÄ±lÄ±", f"{len(veri)} kayÄ±t Excel'e aktarÄ±ldÄ±:\n{dosya_yolu}", parent=pencere)
            os.startfile(dosya_yolu)
        except Exception as ex:
            messagebox.showerror("Hata", f"DÄ°Åa aktarÄ±m sÄ±rasÄ±nda hata:\n{ex}", parent=pencere)

    tk.Button(top_ctrl, text="âš¡ EKRANDAKÄ°LERÄ° EXCEL'E AKTAR", command=ekrandakileri_excele_aktar, bg="#107C41", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10).pack(side="right", padx=5)

    # --- BÄ°LGÄ° PANELÄ° ---
    info_frame = tk.Frame(pencere, bg="#F8F9FA")
    info_frame.pack(fill="x", padx=15, pady=10)
                
    def create_info_card(parent, title, value, bg_color):
        card = tk.Frame(parent, bg=bg_color, bd=0, relief="flat", padx=10, pady=10)
        card.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(card, text=title, font=("Segoe UI", 11, "bold"), bg=bg_color, fg="white").pack()
        tk.Label(card, text=value, font=("Segoe UI", 20, "bold"), bg=bg_color, fg="white").pack()

    create_info_card(info_frame, "SÄ°NOPTÄ°K", str(sinoptik_sayisi), "#0066CC")
    create_info_card(info_frame, "METAR", str(metar_normal_sayisi), "#107C41")
    create_info_card(info_frame, "SPECI", str(speci_sayisi), "#673AB7")
    create_info_card(info_frame, "HatalÄ± KayÄ±t", str(len(hatali_kayitlar)), "#D32F2F")
                
    # Sekmeli yapÄ± (Notebook) oluÅŸtur
    notebook = ttk.Notebook(pencere)
    notebook.pack(fill="both", expand=True, padx=15, pady=5)
                
    # --- SÃœTUN SIRALAMA FONKSÄ°YONU ---
    def treeview_sort_column(tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
                    
        def try_float(val):
            try:
                # Ã–zel formatlar (h1, h2) iÃ§in sÄ±ralama
                match = re.search(r'\d+', str(val))
                if match and "h" in str(val).lower() and len(str(val)) < 6:
                    return float(match.group())
                return float(val)
            except:
                return str(val).lower()
                            
        l.sort(key=lambda t: try_float(t[0]), reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

    # --- SEÄ°ÅM (CHECKBOX) VE SÃ¼LME FONKSÄ°YONLARI ---
    def tree_toggle_checkbox(event, tv):
        region = tv.identify("region", event.x, event.y)
        if region == "heading":
            col = tv.identify_column(event.x)
            if col == "#1":
                current = tv.heading(col)["text"]
                new_val = "[x]" if current == "[ ]" else "[ ]"
                tv.heading(col, text=new_val)
                for item in tv.get_children():
                    vals = list(tv.item(item, "values"))
                    vals[0] = new_val
                    tv.item(item, values=vals)
                return "break"
        elif region == "cell":
            col = tv.identify_column(event.x)
            if col == "#1":
                item = tv.identify_row(event.y)
                if item:
                    vals = list(tv.item(item, "values"))
                    vals[0] = "[x]" if vals[0] == "[ ]" else "[ ]"
                    tv.item(item, values=vals)
                    return "break"
            else:
                item = tv.identify_row(event.y)
                if item:
                    vals = list(tv.item(item, "values"))
                    if len(vals) > 9 and ("DETAY" in str(vals[-1]) or "Ä°NCELE" in str(vals[-1])):
                        if tv == tree: satir_detay_goster(event, tv, "Rasat Hata DetayÄ±")
                        return "break"

    def to_csv_value(v):
        s = str(v)
        if ';' in s or '"' in s or '\n' in s:
            return '"' + s.replace('"', '""') + '"'
        return s

    def secilenleri_sil(tv):
        silinecekler = [item for item in tv.get_children() if tv.item(item, "values")[0] == "[x]"]
        if not silinecekler:
            messagebox.showwarning("UyarÃ¼", "Silinecek/Gizlenecek kayÄ±t seÃ§ilmedi.", parent=pencere)
            return
        if messagebox.askyesno("Onay", f"SeÃ§ili {len(silinecekler)} kaydÄ± gizlemek/silmek istediÃ§inize emin misiniz?", parent=pencere):
            for item in silinecekler:
                tv.delete(item)

    def secilileri_panoya_kopyala(tv, kolonlar):
        secililer = [item for item in tv.get_children() if tv.item(item, "values")[0] == "â˜"]
        if not secililer:
            messagebox.showwarning("UyarÃ¼", "Kopyalanacak kayÄ±t seÃ§ilmedi.", parent=pencere)
            return
                    
        basliklar = [str(col) for col in kolonlar if col != "SeÃ§"]
        metin = ";".join(to_csv_value(b) for b in basliklar) + "\n"
                    
        for item in secililer:
            vals = tv.item(item, "values")[1:]
            metin += ";".join(to_csv_value(v) for v in vals) + "\n"
                        
        pencere.clipboard_clear()
        pencere.clipboard_append(metin)
        messagebox.showinfo("BaÅŸarÄ±lÄ±", f"{len(secililer)} kayÄ±t panoya kopyalandÄ±.", parent=pencere)

    # --- ORTAK Ä°ÅFRE Ä°ÅZÃ¼MLEYÃ¼CÅŸ PENCERELERÄ° ---
    def goster_sinoptik_cozumleyici(sinoptik_sifresi, parent_widget):
        if SynopDecoder is None:
            messagebox.showerror("Hata", "SynopDecoder modÃ¼lÅŸ yÃ¼klenemedi.", parent=parent_widget)
            return
                        
        if not sinoptik_sifresi or sinoptik_sifresi.lower() in ["-", "nan", ""]:
            messagebox.showinfo("Bilgi", "Ä°ÅzÃ¼mlenecek geÃ§erli bir SÄ°NOPTÄ°K Åifresi bulunamadÄ±.", parent=parent_widget)
            return
                        
        try:
            decoder = SynopDecoder()
            ayiklanan_veri = decoder.decode_line(sinoptik_sifresi)
            # anakardelenden temizlik mantÃ¼Ã¼
            temiz_sifre = re.sub(r'^(?:SÄ°NOPTÄ°K|SYNOP|SINOPTIK|KAYIT:.*?BULTEN\s*:|BULTEN\s*:|.*GELDÄ°:|.*YENÄ° RASAT)\s*', '', sinoptik_sifresi, flags=re.IGNORECASE|re.DOTALL).strip()
            ayiklanan_veri = decoder.decode_line(temiz_sifre)
            is_valid = decoder.validate()
            hatalar = decoder.get_errors() if hasattr(decoder, 'get_errors') else []
                        
            cozum_pop = tk.Toplevel(parent_widget)
            cozum_pop.title("SÄ°NOPTÄ°K Åifre Ä°ÅzÃ¼mleyici")
            cozum_pop.geometry("600x450")
            cozum_pop.geometry("750x550")
            cozum_pop.configure(bg="#F8F9FA")
                        
            # Dikey ve Yatay KaydÄ±rma Ã‡ubuklarÄ± (Scrollbar)
            f_txt = tk.Frame(cozum_pop, bg="#37474F")
            f_txt.pack(expand=True, fill="both", padx=15, pady=15)
                        
            v_scroll = tk.Scrollbar(f_txt, orient="vertical")
            v_scroll.pack(side="right", fill="y")
            h_scroll = tk.Scrollbar(f_txt, orient="horizontal")
            h_scroll.pack(side="bottom", fill="x")
                        
            txt = tk.Text(f_txt, wrap="none", font=("Consolas", 11), bg="#37474F", fg="#69F0AE", padx=15, pady=15, xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
            txt.pack(expand=True, fill="both")
                        
            v_scroll.config(command=txt.yview)
            h_scroll.config(command=txt.xview)
                        
            sonuc = f"--- ORÄ°JÄ°NAL Ä°ÅFRE ---\n{sinoptik_sifresi}\n\n"
            sonuc = f"--- ORÄ°JÄ°NAL Ä°ÅFRE ---\n{temiz_sifre}\n\n"
            sonuc += f"Format GeÃ§erli mi? : {'EVET Ã¼' if is_valid else 'HAYIR Ã¼'}\n"
                        
            if hatalar:
                sonuc += "\nTespit Edilen Format HatalarÄ±:\n"
                for h in hatalar: sonuc += f" - {h}\n"
                                
            sonuc += "\n--- AYIKLANAN VERÄ°LER ---\n"
            if ayiklanan_veri:
                if hasattr(decoder, 'generate_human_readable'):
                    sonuc += decoder.generate_human_readable(ayiklanan_veri) + "\n"
                else:
                    for k, v in ayiklanan_veri.items():
                        if not k.startswith('_') and k not in ['errors', 'raw_line', 'raw_groups', 'ham_veri']:
                            sonuc += f"{str(k).upper():<20}: {v}\n"
            else:
                sonuc += "Ä°ÅzÃ¼mlenebilecek geÃ§erli bir veri bulunamadÄ±.\n"
                                
            txt.insert("1.0", sonuc)
            txt.config(state=tk.DISABLED)
                        
            def metni_kopyala():
                cozum_pop.clipboard_clear()
                cozum_pop.clipboard_append(sonuc)
                messagebox.showinfo("BaÅŸarÄ±lÄ±", "Ä°ÅzÃ¼mlenen veriler panoya kopyalandÄ±!", parent=cozum_pop)
                            
            def metni_kaydet():
                dosya_yolu = filedialog.asksaveasfilename(
                    parent=cozum_pop,
                    title="SÄ°NOPTÄ°K Ä°ÅzÃ¼mÃ¼nÅŸ Kaydet",
                    defaultextension=".txt",
                    filetypes=[("Metin Belgesi", "*.txt"), ("TÃ¼m Dosyalar", "*.*")],
                    initialfile="SINOPTIK_Cozum_Raporu.txt"
                )
                if dosya_yolu:
                    try:
                        with open(dosya_yolu, "w", encoding="utf-8") as f:
                            f.write(sonuc)
                        messagebox.showinfo("BaÅŸarÄ±lÄ±", f"Dosya kaydedildi:\n{dosya_yolu}", parent=cozum_pop)
                    except Exception as ex:
                        messagebox.showerror("Hata", f"KayÄ±t sÄ±rasÄ±nda hata oluÅŸtu:\n{ex}", parent=cozum_pop)
                                    
            btn_frame = tk.Frame(cozum_pop, bg="#F8F9FA")
            btn_frame.pack(pady=(0, 15))
                            
            btn_kopyala = tk.Button(btn_frame, text="Panoya Kopyala", command=metni_kopyala, font=("Segoe UI", 10, "bold"), bg="#0066CC", fg="white", activebackground="#0052A3", activeforeground="white", cursor="hand2", padx=20, pady=5)
            btn_kopyala.pack(side=tk.LEFT, padx=10)
                        
            btn_kaydet = tk.Button(btn_frame, text="TXT Kaydet", command=metni_kaydet, font=("Segoe UI", 10, "bold"), bg="#107C41", fg="white", activebackground="#0C5D31", activeforeground="white", cursor="hand2", padx=20, pady=5)
            btn_kaydet.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            messagebox.showerror("Hata", f"Ä°ÅzÃ¼mleme HatasÄ±:\n{e}", parent=parent_widget)

    def goster_metar_cozumleyici(metar_sifresi, parent_widget):
        if MetarDecoder is None:
            messagebox.showerror("Hata", "MetarDecoder modÃ¼lÅŸ yÃ¼klenemedi.", parent=parent_widget)
            return

        if not metar_sifresi or metar_sifresi.lower() in ["-", "nan", ""]:
            messagebox.showinfo("Bilgi", "Ä°ÅzÃ¼mlenecek geÃ§erli bir METAR Åifresi bulunamadÄ±.", parent=parent_widget)
            return
                        
        try:
            decoder = MetarDecoder()
            ayiklanan_veri = decoder.decode_line(metar_sifresi)
            # anakardelenden temizlik mantÃ¼Ã¼
            temiz_sifre = re.sub(r'^(?:KAYIT:.*?BULTEN\s*:|BULTEN\s*:|.*GELDÄ°:|.*YENÄ° RASAT)\s*', '', metar_sifresi, flags=re.IGNORECASE|re.DOTALL).strip()
            m_match = re.search(r'(METAR|SPECI|SATT\d*|SA[A-Z0-9]{2}|SP[A-Z0-9]{2})', temiz_sifre)
            if m_match: temiz_sifre = temiz_sifre[m_match.start():]
                        
            ayiklanan_veri = decoder.decode_line(temiz_sifre)
                        
            metar_pop = tk.Toplevel(parent_widget)
            metar_pop.title("METAR Åifre Ä°ÅzÃ¼mleyici")
            metar_pop.geometry("600x450")
            metar_pop.geometry("750x550")
            metar_pop.configure(bg="#F8F9FA")
                        
            f_txt_m = tk.Frame(metar_pop, bg="#37474F")
            f_txt_m.pack(expand=True, fill="both", padx=15, pady=15)
                        
            v_scroll_m = tk.Scrollbar(f_txt_m, orient="vertical")
            v_scroll_m.pack(side="right", fill="y")
            h_scroll_m = tk.Scrollbar(f_txt_m, orient="horizontal")
            h_scroll_m.pack(side="bottom", fill="x")
                        
            txt = tk.Text(f_txt_m, wrap="none", font=("Consolas", 11), bg="#37474F", fg="#81D4FA", padx=15, pady=15, xscrollcommand=h_scroll_m.set, yscrollcommand=v_scroll_m.set)
            txt.pack(expand=True, fill="both")
                        
            v_scroll_m.config(command=txt.yview)
            h_scroll_m.config(command=txt.xview)
                        
            if ayiklanan_veri:
                sonuc = decoder.generate_human_readable(ayiklanan_veri)
            else:
                sonuc = f"--- ORÄ°JÄ°NAL METAR Ä°ÅFRESÅŸ ---\n{metar_sifresi}\n\nÄ°ÅzÃ¼mlenebilecek geÃ§erli bir veri bulunamadÄ±."
                sonuc = f"--- ORÄ°JÄ°NAL METAR Ä°ÅFRESÅŸ ---\n{temiz_sifre}\n\nÄ°ÅzÃ¼mlenebilecek geÃ§erli bir veri bulunamadÄ±."
                            
            txt.insert("1.0", sonuc)
            txt.config(state=tk.DISABLED)
                        
            def metni_kopyala():
                metar_pop.clipboard_clear()
                metar_pop.clipboard_append(sonuc)
                messagebox.showinfo("BaÅŸarÄ±lÄ±", "METAR verileri panoya kopyalandÄ±!", parent=metar_pop)
                            
            def metni_kaydet():
                dosya_yolu = filedialog.asksaveasfilename(
                    parent=metar_pop,
                    title="METAR Ä°ÅzÃ¼mÃ¼nÅŸ Kaydet",
                    defaultextension=".txt",
                    filetypes=[("Metin Belgesi", "*.txt"), ("TÃ¼m Dosyalar", "*.*")],
                    initialfile="METAR_Cozum_Raporu.txt"
                )
                if dosya_yolu:
                    try:
                        with open(dosya_yolu, "w", encoding="utf-8") as f:
                            f.write(sonuc)
                        messagebox.showinfo("BaÅŸarÄ±lÄ±", f"Dosya kaydedildi:\n{dosya_yolu}", parent=metar_pop)
                    except Exception as ex:
                        messagebox.showerror("Hata", f"KayÄ±t sÄ±rasÄ±nda hata oluÅŸtu:\n{ex}", parent=metar_pop)
                                    
            btn_frame = tk.Frame(metar_pop, bg="#F8F9FA")
            btn_frame.pack(pady=(0, 15))
                            
            btn_kopyala = tk.Button(btn_frame, text="Panoya Kopyala", command=metni_kopyala, font=("Segoe UI", 10, "bold"), bg="#0066CC", fg="white", activebackground="#0052A3", activeforeground="white", cursor="hand2", padx=20, pady=5)
            btn_kopyala.pack(side=tk.LEFT, padx=10)
                        
            btn_kaydet = tk.Button(btn_frame, text="TXT Kaydet", command=metni_kaydet, font=("Segoe UI", 10, "bold"), bg="#107C41", fg="white", activebackground="#0C5D31", activeforeground="white", cursor="hand2", padx=20, pady=5)
            btn_kaydet.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            messagebox.showerror("Hata", f"Ä°ÅzÃ¼mleme HatasÄ±:\n{e}", parent=parent_widget)

    # --- SAÄ TIK MENÃœSÃœ FONKSÄ°YONU ---
    def show_context_menu(event, tv):
        # SaÄŸ tÄ±klanan satÄ±rÄ± seÃ§
        iid = tv.identify_row(event.y)
        if iid and iid not in tv.selection():
            tv.selection_set(iid)
                        
        menu = tk.Menu(tv, tearoff=0)
                    
        def copy_selection():
            selected = tv.selection()
            if not selected: return
            text_to_copy = ""
            for item in selected:
                vals = tv.item(item, "values")
                if tv["columns"][0] == "SeÃ§":
                    vals = vals[1:]
                text_to_copy += ";".join(to_csv_value(v) for v in vals) + "\n"
            tv.clipboard_clear()
            tv.clipboard_append(text_to_copy.strip())
                        
        def select_all():
            tv.selection_set(tv.get_children())
                        
        def tr_lower(metin):
            if not metin: return ""
            return str(metin).replace("I", "Ã¼").replace("Ã¼", "i").replace("Ã¼", "Ã¼").replace("Ã¼", "Ã¼").replace("Ã¼", "Ã¼").replace("Ã¼", "Ã¼").replace("Ã¼", "Ã¼").lower()

        def find_text():
            search_term = simpledialog.askstring("Bul", "Aranacak kelime(ler):", parent=tv)
            if not search_term: return
                        
            # KullanÄ±cÄ±nÄ±n girdiÃ§i kelimeleri boÅŸluklara gÃ¶re ayÄ±r (Ã–rn: "h37 06:00")
            arananlar = tr_lower(search_term.strip()).split()
            tv.selection_remove(tv.selection())
            found = False
            for item in tv.get_children():
                values = tv.item(item, "values")
                satir_metni = tr_lower(" ".join(str(v) for v in values))
                            
                # Aranan TÃœM kelimeler bu satÄ±rda geÃ§iyorsa seÃ§ (AkÄ±llÄ± Ã§oklu arama)
                if all(kelime in satir_metni for kelime in arananlar):
                    tv.selection_add(item)
                    if not found:
                        tv.see(item)
                        found = True
                                    
            if not found:
                messagebox.showinfo("BulunamadÄ±", "EÅŸleÅŸen kayÄ±t bulunamadÄ±.", parent=tv)

        def cozumle_sinoptik():
            selected = tv.selection()
            if not selected: return
            degerler = tv.item(selected[0], "values")
            kolonlar = tv["columns"]
            s_idx = list(kolonlar).index("SÄ°NOPTÄ°K Åifresi") if "SÄ°NOPTÄ°K Åifresi" in kolonlar else -1
            if s_idx != -1:
                sinoptik_sifresi = str(degerler[s_idx]).strip() 
                goster_sinoptik_cozumleyici(sinoptik_sifresi, tv)

        def cozumle_metar():
            selected = tv.selection()
            if not selected: return
            degerler = tv.item(selected[0], "values")
            kolonlar = tv["columns"]
            m_idx = list(kolonlar).index("METAR Åifresi") if "METAR Åifresi" in kolonlar else -1
            if m_idx != -1:
                metar_sifresi = str(degerler[m_idx]).strip() 
                goster_metar_cozumleyici(metar_sifresi, tv)

        menu.add_command(label="SatÄ±rÅŸ Kopyala", command=copy_selection)
        menu.add_command(label="Hepsini SeÃ§", command=select_all)
        menu.add_separator()
        menu.add_command(label="SÄ°NOPTÄ°K Åifresini Ä°ÅzÃ¼mle", command=cozumle_sinoptik)
        menu.add_command(label="METAR Åifresini Ä°ÅzÃ¼mle", command=cozumle_metar)
        menu.add_separator()
        menu.add_command(label="Bul...", command=find_text)
                    
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # --- YENÄ°: Ã‡ift tÄ±klama ile detay okuma fonksiyonu ---
    def satir_detay_goster(event, tree_widget, pencere_baslik):
        item = tree_widget.identify_row(event.y)
        if not item:
            secili = tree_widget.selection()
            if not secili: return
            item = secili[0]
                    
        degerler = tree_widget.item(item, "values")
        kolonlar = tree_widget["columns"]
                    
        detay_pop = tk.Toplevel(pencere)
        detay_pop.title(pencere_baslik)
        detay_pop.geometry("600x450")
        detay_pop.geometry("750x550")
        detay_pop.configure(bg="#F8F9FA")
                    
        f_txt_d = tk.Frame(detay_pop, bg="white")
        f_txt_d.pack(expand=True, fill="both", padx=15, pady=15)
        v_scroll_d = tk.Scrollbar(f_txt_d, orient="vertical")
        v_scroll_d.pack(side="right", fill="y")
                    
        text_alan = tk.Text(f_txt_d, wrap="word", font=("Segoe UI", 11), bg="white", yscrollcommand=v_scroll_d.set)
        text_alan.pack(expand=True, fill="both")
        v_scroll_d.config(command=text_alan.yview)
                    
        detay_metni = ""
        for col, val in zip(kolonlar, degerler):
            if str(col).upper() == "SEÃ‡" or str(col).upper() == "AKSÄ°YON": continue
            detay_metni += f"â€¢ {str(col).upper()}:\n{val}\n\n"
            
        text_alan.insert("1.0", detay_metni.strip())
        text_alan.config(state=tk.DISABLED) # Sadece okunabilir yapar

        # --- SaÄŸ TÄ±k MenÃ¼sÅŸ (Detay Penceresi Ä°Åin) ---
        sag_tik_menu = tk.Menu(text_alan, tearoff=0)
                    
        def kopyala():
            try:
                secili_metin = text_alan.selection_get()
                detay_pop.clipboard_clear()
                detay_pop.clipboard_append(secili_metin)
            except tk.TclError:
                pass
                            
        def tumunu_kopyala():
            tum_metin = text_alan.get("1.0", tk.END).strip()
            detay_pop.clipboard_clear()
            detay_pop.clipboard_append(tum_metin)

        def hepsini_sec():
            text_alan.tag_add("sel", "1.0", "end")
            return 'break'

        sag_tik_menu.add_command(label="Kopyala", command=kopyala)
        sag_tik_menu.add_command(label="TÃ¼mÃ¼nÅŸ Kopyala", command=tumunu_kopyala)
        sag_tik_menu.add_separator()
        sag_tik_menu.add_command(label="Hepsini SeÃ§", command=hepsini_sec)

        # Åifre Ä°ÅzÃ¼mleme butonlarÃ¼nÅŸ detay penceresinde saÄŸ tÄ±ka ekle
        sinoptik_idx = -1
        metar_idx = -1
        for i, col in enumerate(kolonlar):
            col_str = str(col).upper()
            if "SÄ°NOPTÄ°K" in col_str and "Ä°ÅFRE" in col_str:
                sinoptik_idx = i
            elif "METAR" in col_str and "Ä°ÅFRE" in col_str:
                metar_idx = i
                            
        if sinoptik_idx != -1 or metar_idx != -1:
            sag_tik_menu.add_separator()
                        
            if sinoptik_idx != -1:
                def detay_cozumle_sinoptik():
                    goster_sinoptik_cozumleyici(str(degerler[sinoptik_idx]).strip(), detay_pop)
                sag_tik_menu.add_command(label="SÄ°NOPTÄ°K Åifresini Ä°ÅzÃ¼mle", command=detay_cozumle_sinoptik)
                            
            if metar_idx != -1:
                def detay_cozumle_metar():
                    goster_metar_cozumleyici(str(degerler[metar_idx]).strip(), detay_pop)
                sag_tik_menu.add_command(label="METAR Åifresini Ä°ÅzÃ¼mle", command=detay_cozumle_metar)

        text_alan.bind("<Button-3>", lambda e: sag_tik_menu.tk_popup(e.x_root, e.y_root))

    # --- 1. SEKME: HATALI RASATLAR ---
    tree_frame = tk.Frame(notebook, bg="white")
    notebook.add(tree_frame, text="âš¡ Rasatlar (HatalÄ± / TÃ¼m)")
                
    # FÃ¼LTRELEME ALANI
    filter_frame = tk.Frame(tree_frame, bg="white")
    filter_frame.pack(fill="x", padx=5, pady=5)
                
    btn_sil = tk.Button(filter_frame, text="ğŸ—‘ï¸ SeÃ§ili OlanlarÄ± Gizle/Sil", command=lambda: secilenleri_sil(tree), bg="#D32F2F", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10)
    btn_sil.pack(side="right", padx=5)

    btn_kopyala = tk.Button(filter_frame, text="âš¡ SeÃ§ilileri Kopyala", command=lambda: secilileri_panoya_kopyala(tree, cols), bg="#008CBA", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10)
    btn_kopyala.pack(side="right", padx=5)

    tk.Label(filter_frame, text="âš¡ GÃ¼sterim Filtresi:", bg="white", font=("Segoe UI", 11, "bold"), fg="#343A40").pack(side="left", padx=5)
    filtre_combo = ttk.Combobox(filter_frame, values=["HatalÄ± Rasatlar (TÃ¼mÃ¼)", "TÃ¼m KayÄ±tlar (HatalÄ± + DoÄŸru)", "TÃ¼m METAR/SPECI RasatlarÄ±", "TÃ¼m SÄ°NOPTÄ°K RasatlarÄ±", "Sadece Ã‡apraz Kontrol HatalarÄ±", "Sadece WMO / Standart Hatalar", "Veri Yok / Eksik HatalarÄ±", "Sadece 7. Grup (HalihazÄ±r/GeÃ¼miÅŸ Hava) HatalarÄ±", "Sadece 8. Grup (Bulut) HatalarÄ±"], state="readonly", width=45, font=("Segoe UI", 11))
    filtre_combo.set("HatalÄ± Rasatlar (TÃ¼mÃ¼)")
    filtre_combo.pack(side="left", padx=5)
                
    cols = ("SeÃ§", "Tarih", "Saat", "GMT", "Hata Kodu", "AÄ°Åklama", "HatalÄ± Kod", "Tavsiye Kod", "SÄ°NOPTÄ°K Åifresi", "METAR Åifresi", "Aksiyon")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Treeview", displaycolumns=("SeÃ§", "Tarih", "Saat", "GMT", "Hata Kodu", "HatalÄ± Kod", "Tavsiye Kod", "Aksiyon"))
                
    tree.heading("SeÃ§", text="[ ]")
    tree.heading("Tarih", text="Tarih")
    tree.heading("Saat", text="Saat")
    tree.heading("GMT", text="GMT")
    tree.heading("Hata Kodu", text="Hata Kodu")
    tree.heading("AÄ°Åklama", text="AÄ°Åklama")
    tree.heading("HatalÄ± Kod", text="HatalÄ± Kod")
    tree.heading("Tavsiye Kod", text="Tavsiye Kod")
    tree.heading("SÄ°NOPTÄ°K Åifresi", text="SÄ°NOPTÄ°K Åifresi")
    tree.heading("METAR Åifresi", text="METAR Åifresi")
    tree.heading("Aksiyon", text="Detay")
                
    tree.column("SeÃ§", width=40, anchor="center")
    tree.column("Tarih", width=90, anchor="center")
    tree.column("Saat", width=60, anchor="center")
    tree.column("GMT", width=60, anchor="center")
    tree.column("Hata Kodu", width=120, anchor="center")
    tree.column("AÄ°Åklama", width=350, anchor="w")
    tree.column("HatalÄ± Kod", width=100, anchor="center")
    tree.column("Tavsiye Kod", width=100, anchor="center")
    tree.column("SÄ°NOPTÄ°K Åifresi", width=0, stretch=False)
    tree.column("METAR Åifresi", width=0, stretch=False)
    tree.column("Aksiyon", width=80, anchor="center")
                
    yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    yscroll.pack(side="right", fill="y")
    xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    xscroll.pack(side="bottom", fill="x")
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
    tree.pack(side="left", fill="both", expand=True)
                
    tree.bind("<Button-1>", lambda e: tree_toggle_checkbox(e, tree))
    tree.bind("<Double-1>", lambda e: satir_detay_goster(e, tree, "Rasat Hata DetayÄ±"))
    tree.bind("<Button-3>", lambda e: show_context_menu(e, tree))
    for col in cols:
        if col != "SeÃ§":
            tree.heading(col, command=lambda c=col: treeview_sort_column(tree, c, False))
                
    def populate_tree(filter_type="HatalÄ± Rasatlar (TÃ¼mÃ¼)"):
        for item in tree.get_children():
            tree.delete(item)

        if filter_type in ["TÃ¼m KayÄ±tlar (HatalÄ± + DoÄŸru)", "TÃ¼m METAR/SPECI RasatlarÄ±", "TÃ¼m SÄ°NOPTÄ°K RasatlarÄ±"]:
            hedef_df = birlesik
        else:
            hedef_df = hatali_kayitlar

        if hedef_df.empty:
            tree.insert("", tk.END, values=("", "-", "-", "-", "BÄ°LGÄ°", "GÃ¶sterilecek kayÄ±t bulunamadÄ±.", "-", "-"))
            return

        def safe_tree_str(val):
            if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "na", "<na>", ""]:
                return "-"
            return str(val).strip()

        hazirlanan_veriler = []

        for _, row in hedef_df.iterrows():
            hata_kodu = str(row.get("HATA KODU", ""))
            if not hata_kodu and row.get("DURUM") == "Veri Yok":
                hata_kodu = "Veri Yok"
            elif not hata_kodu:
                hata_kodu = "Hata Yok"

            hk_upper = hata_kodu.upper()
            is_capraz = "Ã‡APRAZ" in hk_upper or "UYUM" in hk_upper or "VAL_" in hk_upper
            is_veri_yok = "VERÄ° YOK" in hk_upper or "VERI YOK" in hk_upper

            if filter_type == "Sadece Ã‡apraz Kontrol HatalarÄ±" and not is_capraz:
                continue
            if filter_type == "Sadece WMO / Standart Hatalar" and (is_capraz or is_veri_yok or hata_kodu == "Hata Yok"):
                continue
            if filter_type == "Veri Yok / Eksik HatalarÄ±" and not is_veri_yok:
                continue
                            
            # 7. Grup (ww, W1, W2) filtreleme mantÃ¼Ã¼
            is_7_grup = False
            aciklama = str(row.get("AÃ‡IKLAMA", "")).upper()
            hk_list = [k.strip() for k in hk_upper.split(",")]
            for hk in hk_list:
                if hk.startswith("H"):
                    try:
                        import re
                        num = int(re.sub(r'\D', '', hk))
                        if 76 <= num <= 118 or 286 <= num <= 289 or 318 <= num <= 339 or 361 <= num <= 374 or num in [378, 379]:
                            is_7_grup = True
                            break
                    except: pass
            if not is_7_grup and any(k in aciklama for k in ["WW=", "W1", "W2", "HALÄ°HAZIR", "GEÃ¼Mâš¡ HAVA", "7. GRUP", "Ä°ÅMÃ¼EK", "ORAJ", "SÄ°S", "PUS", "KAR ", "YAÄMUR"]):
                is_7_grup = True

            if filter_type == "Sadece 7. Grup (HalihazÄ±r/GeÃ¼miÅŸ Hava) HatalarÄ±" and not is_7_grup:
                continue
                            
            # 8. Grup (N, Nh, CL, CM, CH, h) filtreleme mantÃ¼Ã¼
            is_8_grup = False
            if filter_type == "Sadece 8. Grup (Bulut) HatalarÄ±":
                for hk in hk_list:
                    if hk.startswith("H"):
                        try:
                            import re
                            num = int(re.sub(r'\D', '', hk))
                            if 26 <= num <= 36 or 120 <= num <= 172 or 278 <= num <= 280 or 284 <= num <= 285 or 311 <= num <= 314 or 353 <= num <= 358:
                                is_8_grup = True
                                break
                        except: pass
                if not is_8_grup and any(k in aciklama for k in ["BULUT", "TAVAN", "DÃ¼KEY", "KAPALILIK", "CÃ¼NS", "8. GRUP", "N=", "NH=", "CL=", "CM=", "CH="]):
                    is_8_grup = True
                if not is_8_grup:
                    continue
                            
            sin_msg = safe_tree_str(row.get("SÄ°NOPTÄ°K - Åifreli Mesaj"))
            met_msg = safe_tree_str(row.get("METAR - Åifreli Mesaj"))
                        
            if filter_type == "TÃ¼m SÄ°NOPTÄ°K RasatlarÄ±" and sin_msg == "-":
                continue
            if filter_type == "TÃ¼m METAR/SPECI RasatlarÄ±" and met_msg == "-":
                continue

            hatali_kod = "-"
            tavsiye_kod = "-"
            if hata_kodu == "h378":
                try:
                    import re
                    aciklama_str = safe_tree_str(row.get("AÃ‡IKLAMA"))
                    m_ww = re.search(r"\[TAVSIYE_WW=(\d{2})\]", aciklama_str)
                    if m_ww:
                        hedef_ww = m_ww.group(1)
                        
                        m7 = re.search(r"\b(70[0-3]\d{2})\b", sin_msg)
                        if m7:
                            hatali_kod = m7.group(1)
                            tavsiye_kod = "7" + hedef_ww + hatali_kod[3:]
                except: pass

            if "h197" in hata_kodu:
                try:
                    import re
                    m_1 = re.search(r"\b(11\d{3})\b", sin_msg)
                    if m_1:
                        hatali_kod = m_1.group(1)
                        tavsiye_kod = "10" + hatali_kod[2:]
                except: pass

            hazirlanan_veriler.append((
                "Ã¼",
                safe_tree_str(row.get("Tarih")),
                safe_tree_str(row.get("Saat (GMT)")),
                safe_tree_str(row.get("SÄ°NOPTÄ°K - GMT_EXACT", row.get("METAR - GMT_EXACT", ""))),
                hata_kodu,
                safe_tree_str(row.get("AÃ‡IKLAMA")),
                hatali_kod,
                tavsiye_kod,
                sin_msg,
                met_msg,
                " ğŸ” Ä°NCELE "
            ))
                        
        if not hazirlanan_veriler:
            tree.insert("", tk.END, values=("", "-", "-", "BÄ°LGÄ°", "GÃ¶sterilecek kayÄ±t bulunamadÄ±.", "-", "-", "-", "-", "-"))
            return

        def chunk_insert(index=0, chunk_size=100):
            for i in range(index, min(index + chunk_size, len(hazirlanan_veriler))):
                tree.insert("", tk.END, values=hazirlanan_veriler[i])
                        
            if index + chunk_size < len(hazirlanan_veriler):
                tree.after(10, chunk_insert, index + chunk_size, chunk_size)

        chunk_insert()

    filtre_combo.bind("<<ComboboxSelected>>", lambda e: populate_tree(filtre_combo.get()))
    populate_tree()
                        
    # --- 2. SEKME: TÃœM KURAL TESTLERÄ° DETAYI ---
    kural_frame = tk.Frame(notebook, bg="white")
    notebook.add(kural_frame, text="âœ… Test Edilen TÃ¼m Kurallar (h1..h267)")
                
    kural_top_frame = tk.Frame(kural_frame, bg="white")
    kural_top_frame.pack(fill="x", padx=5, pady=5)
                
    btn_sil_k = tk.Button(kural_top_frame, text="ğŸ—‘ï¸ SeÃ§ili OlanlarÄ± Gizle/Sil", command=lambda: secilenleri_sil(tree_k), bg="#D32F2F", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10)
    btn_sil_k.pack(side="right", padx=5)

    btn_kopyala_k = tk.Button(kural_top_frame, text="âš¡ SeÃ§ilileri Kopyala", command=lambda: secilileri_panoya_kopyala(tree_k, cols_k), bg="#008CBA", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10)
    btn_kopyala_k.pack(side="right", padx=5)

    cols_k = ("SeÃ§", "Kural", "Durum", "Hata SayÄ±sÄ±", "Kural AÄ°ÅklamasÃ¼")
    tree_k = ttk.Treeview(kural_frame, columns=cols_k, show="headings", style="Treeview")
    tree_k.heading("SeÃ§", text="â˜")
    tree_k.heading("Kural", text="Kural Kodu")
    tree_k.heading("Durum", text="Test Durumu")
    tree_k.heading("Hata SayÄ±sÄ±", text="Tespit Edilen Hata")
    tree_k.heading("Kural AÄ°ÅklamasÃ¼", text="Kural AÄ°ÅklamasÃ¼")
                
    tree_k.column("SeÃ§", width=40, anchor="center")
    tree_k.column("Kural", width=100, anchor="center")
    tree_k.column("Durum", width=130, anchor="center")
    tree_k.column("Hata SayÄ±sÄ±", width=110, anchor="center")
    tree_k.column("Kural AÄ°ÅklamasÃ¼", width=600, anchor="w")
                
    yscroll_k = ttk.Scrollbar(kural_frame, orient="vertical", command=tree_k.yview)
    yscroll_k.pack(side="right", fill="y")
    xscroll_k = ttk.Scrollbar(kural_frame, orient="horizontal", command=tree_k.xview)
    xscroll_k.pack(side="bottom", fill="x")
    tree_k.configure(yscrollcommand=yscroll_k.set, xscrollcommand=xscroll_k.set)
    tree_k.pack(side="left", fill="both", expand=True)
                
    tree_k.bind("<Button-1>", lambda e: tree_toggle_checkbox(e, tree_k))
    tree_k.bind("<Double-1>", lambda e: satir_detay_goster(e, tree_k, "Kural Test DetayÄ±"))
    tree_k.bind("<Button-3>", lambda e: show_context_menu(e, tree_k))
    for col in cols_k:
        if col != "SeÃ§":
            tree_k.heading(col, command=lambda c=col: treeview_sort_column(tree_k, c, False))
                
    # TÃ¼m kurallarÄ±n dÃ¶kÃ¼mÃ¼nÅŸ listele
    from collections import Counter
    tum_kodlar = []
    if not hatali_kayitlar.empty:
        for k in hatali_kayitlar["HATA KODU"].dropna():
            tum_kodlar.extend([x.strip() for x in str(k).split(",") if x.strip()])
    kod_sayilari = Counter(tum_kodlar)
                
    tum_kural_listesi = []
                
    # 1. SÃ¶zlÃ¼kte tanÄ±mlÄ± olan tÃ¼m gÃ¼ncel kurallarÄ± ekle
    for k_kod, k_aciklama in kurallar.HATA_SOZLUGU.items():
        adet = kod_sayilari.get(k_kod, 0)
        tum_kural_listesi.append((k_kod, adet, k_aciklama))
                    
    # 2. SÃ¶zlÃ¼kte olmayan ancak analizde tespit edilen sistem iÃ§i Ã‡apraz kontrolleri ekle
    mevcut_kodlar = [x[0] for x in tum_kural_listesi]
    for k_kod, adet in kod_sayilari.items():
        if k_kod not in mevcut_kodlar:
            k_aciklama = kurallar.HATA_SOZLUGU.get(k_kod, "Sistem Ä°Åi Dinamik Ã‡apraz Kontrol")
            if k_kod == "Veri Yok":
                k_aciklama = "Ä°lgili ana/ara sinoptik saatinde rasat verisi bulunamadÄ± (TÃ¼m zorunlu parametreler eksik)."
            elif k_kod == "Ara Rasat":
                k_aciklama = "Sadece METAR bulunur, SÄ°NOPTÄ°K beklenmez."
            tum_kural_listesi.append((k_kod, adet, k_aciklama))
                        
    # SÄ±ralama: h1, h2, h3... ve ardÄ±ndan diÃ§erleri
    def sort_key(x):
        match = re.search(r'\d+', x[0])
        if x[0].startswith('h') and match: return (0, int(match.group()))
        elif x[0].startswith('VAL'): return (1, x[0])
        else: return (2, x[0])
                
    tum_kural_listesi.sort(key=sort_key)
                
    for k_kod, adet, k_aciklama in tum_kural_listesi:
        durum = "BAÃ‡ARISIZ Ã¼" if adet > 0 else "BAÅARILI (GeÃ§ti) Ã¼"
        hata_metni = f"{adet} Defa" if adet > 0 else "0"
        tree_k.insert("", tk.END, values=("â˜", k_kod, durum, hata_metni, k_aciklama))
            

def aylik_rapor_olustur(run_async=True, load_from_cache=False, df_sin_param=None, df_metar_param=None, override_yil=None, override_ay=None, custom_title=None):
    ayarlar = ayarlari_yukle()
    global iptal_istendi
    iptal_istendi = False

    
    # --- UI Geri Bildirimini BaÅŸlat ---
    if not console_mode:
        try:
            btn_run.config(state=tk.DISABLED, text="Ã¼alÃ¼Ã¼yor...")
            if btn_cancel: btn_cancel.config(state=tk.NORMAL)
            lbl_status.config(text="Ä°Ålem baÅŸlatÄ±lÄ±yor...")
            root.config(cursor="watch")
                        
        except Exception as e:
            print(f"Progress window creation error: {e}")

    def islem_yurut(load_from_cache=False, df_sin_param=None, df_metar_param=None, override_yil=None, override_ay=None, custom_title=None):
        # --- OPTÄ°MÄ°ZASYON (Gecikmeli YÃ¼kleme / Lazy Loading) ---
        # ArayÃ¼zÃ¼n donmasÄ±nÄ± Ã¶nlemek iÃ§in aÄ°År kÃ¼tÃ¼phaneleri arka plan iÅŸ parÃ¼acÃ¼Ã¼nda iÃ§e aktarÄ±yoruz.
        global pd, dm1, dm2, dm3, sutun_duzeltici, btn_run, btn_cancel
        import pandas as pd
        import warnings
        warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
        import denetim_merkezi_1 as dm1
        import denetim_merkezi_2 as dm2
        import denetim_merkezi_3 as dm3
        import sutun_duzeltici
        import time

        sin_yolu = None
        metar_yolu = None
        start_time = time.time()

        def update_overall_progress(pct, status_text):
            if console_mode:
                print(f"[{pct}%] {status_text}")
            else:
                def run_update():
                    if btn_run:
                        btn_run.config(text=f"Ã‡ALIÅIYOR... %{int(pct)}")
                    if lbl_status:
                        elapsed = time.time() - start_time
                        if pct > 0:
                            total_est = elapsed / (pct / 100.0)
                            remaining = max(0.0, total_est - elapsed)
                            rem_str = f" | Kalan: {int(remaining)} sn" if pct < 100 else ""
                        else:
                            rem_str = ""
                        lbl_status.config(text=f"{status_text} (%{pct}){rem_str}")
                safe_after(0, run_update)
        try:
            if load_from_cache:
                update_overall_progress(10, "Ã–nbellek aranÄ±yor...")
                cache_path = os.path.join(os.path.expanduser("~"), "Desktop", "check", ".kardelen_cache.pkl")
                if os.path.exists(cache_path):
                    try:
                        import pickle
                        update_overall_progress(40, "Ã–nbellek dosyasÄ± yÃ¼kleniyor...")
                        with open(cache_path, 'rb') as f:
                            cache_data = pickle.load(f)
                        birlesik = cache_data["birlesik"]
                        sinoptik_sayisi = cache_data["sinoptik_sayisi"]
                        metar_normal_sayisi = cache_data["metar_normal_sayisi"]
                        speci_sayisi = cache_data["speci_sayisi"]
                        ay = cache_data["ay"]
                        yil = cache_data["yil"]
                        hatali_kayitlar = birlesik[~birlesik["DURUM"].isin(["Hata Yok", "Ara Rasat"])]
                        
                        update_overall_progress(100, "ArayÃ¼z gÃ¼ncelleniyor...")
                        # Ekranda gÃ¶ster
                        safe_after(0, lambda: arayuzde_goster(birlesik, hatali_kayitlar, sinoptik_sayisi, metar_normal_sayisi, speci_sayisi, ay, yil))
                        return
                    except Exception as ce:
                        print(f"Cache okuma hatasÄ±: {ce}")
                        safe_showerror("Hata", f"Ã–nbellek dosyasÄ± okunamadÄ±, normal analize geÃ§iliyor.\nHata: {ce}")
                else:
                    safe_showerror("Hata", "Daha Ã¼nce kaydedilmiÅŸ bir analiz bulunamadÄ±. LÃ¼tfen Ã¼nce normal bir analiz Ã¼alÄ°ÅtÃ¼rÃ¼n.")
                    # UI temizle
                    def finalize_ui():
                        if btn_run: btn_run.config(state=tk.NORMAL, text=get_button_text())
                        if btn_cancel: btn_cancel.config(state=tk.DISABLED)
                        if lbl_status: lbl_status.config(text="HazÃ¼r")
                        if root: root.config(cursor="")
                        try:
                            if 'progress_win' in globals() and progress_win and progress_win.winfo_exists():
                                progress_win.grab_release()
                                progress_win.destroy()
                        except:
                            pass
                    safe_after(0, finalize_ui)
                    return

            update_overall_progress(5, "Ä°Ålem baÅŸlatÄ±lÄ±yor...")
            # Raporlamaya baÅŸlamadan hemen Ã¼nce, eski dosyalarÄ± silip sadece en son inen 1 Metar ve 1 Sinoptik bÃ¼rak:
            sadece_en_yeni_dosyalari_tut()
            update_overall_progress(10, "Eski geÃ¼ici dosyalar temizlendi.")

            # --- Dosya Arama ve Ã¼n Ä°Åleme ---
            update_overall_progress(15, "KlasÃ¶r taranÄ±yor ve dosyalar aranÄ±yor...")

            if iptal_istendi: raise InterruptedError("Ä°Ålem kullanÄ±cÄ± tarafÃ¼ndan iptal edildi.")

            if custom_title is not None and "GÃœNCEL" in custom_title.upper():
                # We are in Live Analysis mode (canli_analiz.py injected this)
                if df_sin_param is None or df_metar_param is None:
                    error_msg = "SÄ°NOPTÄ°K veya METAR verisi Kardelen'den indirilemedi! LÃ¼tfen baÃ¼lantÃ¼nÃ¼zÅŸ veya istasyon kodunu kontrol edin."
                    print(f"{Colors.FAIL}{error_msg}{Colors.ENDC}")
                    safe_showerror("Hata", error_msg)
                    return
                
                df_sin = df_sin_param.copy()
                df_metar = df_metar_param.copy()
                sin_yolu = "CANLI_HTML_SÄ°NOPTÄ°K"
                metar_yolu = "CANLI_HTML_METAR"
                hedef_klasor = HEDEF_KLASOR
                sin_dosyalari = []
                metar_dosyalari = []
            elif df_sin_param is not None and df_metar_param is not None:
                df_sin = df_sin_param.copy()
                df_metar = df_metar_param.copy()
                sin_yolu = "CANLI_HTML_SÄ°NOPTÄ°K"
                metar_yolu = "CANLI_HTML_METAR"
                hedef_klasor = HEDEF_KLASOR
                sin_dosyalari = []
                metar_dosyalari = []
                update_overall_progress(20, "Veriler doÄŸrudan bellekten (HTML) alÃ¼ndÃ¼.")
            else:
                hedef_klasor = HEDEF_KLASOR
                if not os.path.exists(hedef_klasor):
                    error_msg = f"Hata: Hedef klasÃ¶r bulunamadÄ±:\n{hedef_klasor}"
                    print(f"{Colors.FAIL}{error_msg}{Colors.ENDC}")
                    safe_showerror("Hata", error_msg)
                    return

                tum_dosyalar = glob.glob(os.path.join(hedef_klasor, "*"))
                
                # DosyalarÅŸ deÃ¼iÃ¼tirilme tarihine gÃ¶re sÄ±rala (en yeni en Ã¼stte)
                try:
                    tum_dosyalar.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
                except: pass
                
                sin_dosyalari = [f for f in tum_dosyalar if "sin" in os.path.basename(f).lower() and f.endswith((".xls", ".xlsx")) and not os.path.basename(f).startswith("~$")]
                metar_dosyalari = [f for f in tum_dosyalar if "met" in os.path.basename(f).lower() and f.endswith((".xls", ".xlsx")) and not os.path.basename(f).startswith("~$")]

                if len(sin_dosyalari) == 0 or len(metar_dosyalari) == 0:
                    bulunan_dosyalar = [os.path.basename(f) for f in tum_dosyalar if f.endswith((".xls", ".xlsx")) and not os.path.basename(f).startswith("~$")]
                    bulunan_str = "\n".join(bulunan_dosyalar) if bulunan_dosyalar else "Yok"
                    
                    if not sin_dosyalari:
                        error_msg = f"SÄ°NOPTÄ°K dosyasÄ± bulunamadÄ±!\n\nKlasÃ¶rde isminde 'sinoptik' veya 'sÃ¼noptÃ¼k' (veya sadece 'sin') geÃ¼en bir dosya bulunamadÄ±.\n\nKlasÃ¶rdeki Mevcut Dosyalar:\n{bulunan_str}"
                        print(f"{Colors.FAIL}{error_msg}{Colors.ENDC}")
                        safe_showerror("Hata", error_msg)
                        return
                    if not metar_dosyalari:
                        error_msg = f"METAR dosyasÄ± bulunamadÄ±!\n\nKlasÃ¶rde isminde 'METAR' geÃ¼en bir dosya bulunamadÄ±.\n\nKlasÃ¶rdeki Mevcut Dosyalar:\n{bulunan_str}"
                        print(f"{Colors.FAIL}{error_msg}{Colors.ENDC}")
                        safe_showerror("Hata", error_msg)
                        return

                sin_yolu = sin_dosyalari[0]
                metar_yolu = metar_dosyalari[0]

            # --- OTOMATÄ°K SÃœTUN DÃœZELTÄ°CÄ° ENTEGRASYONU ---
            if not console_mode:
                root.after(0, lambda: lbl_status.config(text="Dosyalar dÃ¼zeltiliyor..."))

            print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")

            yedek_klasoru = os.path.join(hedef_klasor, "orijinal_yedekler")
            if not os.path.exists(yedek_klasoru):
                os.makedirs(yedek_klasoru)

            print(f"{Colors.OKBLUE}Orijinal dosyalar '{yedek_klasoru}' klasÃ¶rÃ¼ne yedekleniyor...{Colors.ENDC}")
            for dosya in (sin_dosyalari + metar_dosyalari):
                try:
                    shutil.copy2(dosya, yedek_klasoru)
                except Exception as e:
                    print(f"{Colors.FAIL}Yedekleme HatasÄ± ({os.path.basename(dosya)}): {e}{Colors.ENDC}")
                    traceback.print_exc()

            print(f"{Colors.OKCYAN}SÃœTUN DÃœZELTÄ°CÄ° Ä°PTAL EDÄ°LDÄ° (Veri kaybÄ±nÄ± Ã¶nlemek iÃ§in)...{Colors.ENDC}")
            print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

            # --- Ana Ä°Ålem ---
            if not console_mode:
                root.after(0, lambda: lbl_status.config(text="Veriler okunuyor..."))

            import concurrent.futures
            
            if df_sin_param is None or df_metar_param is None:
                # 1. Veri Okuma (Threading ile Paralel Ä°Ålem - Performans ArtÃ¼Ã¼)
                print(f"\n{Colors.OKCYAN}Veriler paralel (eÅŸzamanlÄ±) olarak okunuyor, lÃ¼tfen bekleyin...{Colors.ENDC}")
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    future_sin = executor.submit(dm1.dosya_oku_akilli, sin_yolu)
                    future_metar = executor.submit(dm1.dosya_oku_akilli, metar_yolu)
                    
                    df_sin = future_sin.result()
                    df_metar = future_metar.result()

            # Terminal ekranÄ±nÄ±n taÅŸmasÄ±nÄ± Ã¶nlemek iÃ§in sadece ilk 15 satÄ±rÄ± gÃ¶ster
            pd.set_option('display.max_rows', 15)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)

            # Okunan verilerin boyutlarÄ±nÄ± ve ilk satÄ±rlarÄ±nÅŸ konsola yazdÄ±r
            print(f"\n{Colors.HEADER}{'='*50}{Colors.ENDC}")
            print(f"{Colors.BOLD}>>> SÄ°NOPTÄ°K VERÄ°SÅŸ OKUNDU <<<{Colors.ENDC}")
            print(f"Boyut: {len(df_sin)} SatÄ±r, {len(df_sin.columns)} SÃ¼tun")
            print(df_sin)
            print(f"\n{Colors.BOLD}>>> METAR VERÄ°SÅŸ OKUNDU <<<{Colors.ENDC}")
            print(f"Boyut: {len(df_metar)} SatÄ±r, {len(df_metar.columns)} SÃ¼tun")
            print(df_metar)
            print(f"{Colors.HEADER}{'='*50}{Colors.ENDC}\n")

            # DiÃ§er iÅŸlemlerde performansÄ± etkilememesi iÃ§in ayarlarÅŸ sÄ±fÄ±rla
            pd.reset_option('display.max_rows')
            pd.reset_option('display.max_columns')

            # --- YIL VE AY TESPÄ°TÄ° ---
            yil, ay = None, None
            
            if override_yil and override_ay:
                yil = override_yil
                ay = override_ay
            else:
                # 1. AdÃ¼m: Orijinal dosyanÃ¼n iÃ§inden (J1, K1 vb. hÃ¼crelerden) kesin tarihi bul (KullanÄ±cÄ± Ä°steÄŸi)
                for yol in [sin_yolu, metar_yolu]:
                    try:
                        # Sadece ilk 10 satÄ±rÄ± okuyarak hÃ¼crelerde tarih/ay ara
                        raw = pd.read_excel(yol, sheet_name=0, header=None, nrows=10)
                        for r in range(len(raw)):
                            for c in range(len(raw.columns)):
                                val = str(raw.iloc[r, c]).strip().upper()
                                # GG.AA.YYYY veya GG/AA/YYYY
                                m1 = re.search(r'\b\d{2}[\./-](\d{2})[\./-](\d{4})\b', val)
                                if m1: yil, ay = int(m1.group(2)), int(m1.group(1)); break
                                
                                # YYYY-AA-GG
                                m2 = re.search(r'\b(\d{4})[\./-](\d{2})[\./-]\d{2}\b', val)
                                if m2: yil, ay = int(m2.group(1)), int(m2.group(2)); break
                            if yil and ay: break
                    except: pass
                    if yil and ay: break
    
                # 2. AdÃ¼m: Dosya isimlerinden (Ã¶rneÄŸin 2026_01 veya 01_2026) tespit etmeye Ã¼alÄ°Å
                if not yil or not ay:
                    for yol in [sin_yolu, metar_yolu]:
                        yol_str = os.path.basename(yol).upper()
                        m1 = re.search(r'\b(20[0-2]\d)[_-](0[1-9]|1[0-2])\b', yol_str) # Ã–rn: 2023_05
                        if m1: yil, ay = int(m1.group(1)), int(m1.group(2)); break
                        
                        m2 = re.search(r'\b(0[1-9]|1[0-2])[_-](20[0-2]\d)\b', yol_str) # Ã–rn: 05-2023
                        if m2: ay, yil = int(m2.group(1)), int(m2.group(2)); break

                        m3 = re.search(r'\b(0[1-9]|1[0-2])(20[0-2]\d)\b', yol_str) # Ã–rn: 072026
                        if m3: ay, yil = int(m3.group(1)), int(m3.group(2)); break
                        
                        aylar_sz = {"OCAK":1, "SUBAT":2, "ÅUBAT":2, "MART":3, "NISAN":4, "NÄ°SAN":4, "MAYIS":5, "HAZIRAN":6, "HAZÃ¼RAN":6, "TEMMUZ":7, "AGUSTOS":8, "AÄUSTOS":8, "EYLUL":9, "EYLÃœL":9, "EKIM":10, "EKÄ°M":10, "KASIM":11, "ARALIK":12}
                        y_match = re.search(r'\b(20[0-2]\d)\b', yol_str)
                        if y_match:
                            for ay_isim, ay_no in aylar_sz.items():
                                if ay_isim in yol_str: yil, ay = int(y_match.group(1)), ay_no; break
                        if yil and ay: break
    
                # 3. AdÃ¼m: Dosya isminden bulunamazsa veri iÃ§inden (GG.AA.YYYY) en Ã§ok tekrar eden tarihi bul
                if not yil or not ay:
                    olasi_tarihler = []
                    hedef_sutunlar = ['sayfa', 'tarih', 'kayit', 'kayÄ±t', 'date', 'zaman']
                    
                    for df in [df_metar, df_sin]:
                        for col in df.columns:
                            if not any(hs in str(col).lower() for hs in hedef_sutunlar):
                                continue
                                
                            # GG.AA.YYYY, GG/AA/YYYY, GG-AA-YYYY formatÄ±
                            sample = df[col].astype(str).str.extract(r'\b\d{2}[\./-](\d{2})[\./-](\d{4})\b').dropna()
                            if not sample.empty:
                                for _, r in sample.iterrows():
                                    if 1 <= int(r[0]) <= 12 and 2000 <= int(r[1]) <= 2050:
                                        olasi_tarihler.append((int(r[1]), int(r[0])))
                                
                            # YYYY.AA.GG, YYYY-AA-GG, YYYY/AA/GG formatÄ±
                            sample_rev = df[col].astype(str).str.extract(r'\b(\d{4})[\./-](\d{2})[\./-]\d{2}\b').dropna()
                            if not sample_rev.empty:
                                for _, r in sample_rev.iterrows():
                                    if 1 <= int(r[1]) <= 12 and 2000 <= int(r[0]) <= 2050:
                                        olasi_tarihler.append((int(r[0]), int(r[1])))
                    
                    if olasi_tarihler:
                        from collections import Counter
                        en_cok_gecen = Counter(olasi_tarihler).most_common(1)[0][0]
                        yil, ay = en_cok_gecen[0], en_cok_gecen[1]
    
                # 4. AdÃ¼m: HiÃ§bir ÅŸekilde bulunamazsa varsayÄ±lan olarak kullanÄ±cÄ±ya sor
                if not yil or not ay:
                    if not console_mode:
                        simdi = datetime.datetime.now()
                        yil = safe_askinteger("Tarih BulunamadÄ±", "Dosyalardan YIL tespit edilemedi.\nLÃ¼tfen verilerin ait olduÅŸu YILI girin:", initialvalue=simdi.year)
                        ay = safe_askinteger("Tarih BulunamadÄ±", "Dosyalardan AY tespit edilemedi.\nLÃ¼tfen verilerin ait olduÅŸu AYI girin:", initialvalue=simdi.month)
                    
                    if not yil or not ay:
                        error_msg = "Hata: Verilerin hangi yÄ±la ve aya ait olduÅŸu tespit edilemedi!\nÄ°Ålem iptal edildi."
                        print(f"{Colors.FAIL}{error_msg}{Colors.ENDC}")
                        if not console_mode:
                            safe_showerror("Tarih HatasÄ±", error_msg)
                        return
    
            print(f"\n{Colors.OKGREEN}>>> KULLANILACAK RAPOR DÃ–NEMÄ°: {ay:02d}/{yil} <<<{Colors.ENDC}")
            
            if not console_mode and btn_run is not None:
                try:
                    root.after(0, lambda: btn_run.config(text=f"Ä°Åleniyor... ({ay:02d}/{yil})"))
                    root.after(0, lambda: lbl_status.config(text=f"DÃ¶nem: {ay:02d}/{yil} - Veriler iÅŸleniyor..."))
                except Exception:
                    pass

            # dm1.tarih_olustur_helper fonksiyonu kullanÄ±larak 1, 2, 3 gibi gÃ¼nlerin
            # kaybolmasÄ± ve sheet2, sheet4 gibi isimlerin doÄŸru ayrÄ°ÅtÃ¼rÃ¼lmasÅŸ saÄŸlanÃ¼r.

            # Okuma Raporu
            okuma_raporu = ""
            try:
                if not df_sin.empty and "sayfa" in df_sin.columns:
                    sheets = sorted(df_sin["sayfa"].unique().astype(str), key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 0)
                    mapped = []
                    for s in sheets:
                        t = dm1.tarih_olustur_helper(s, yil, ay)
                        if t: mapped.append(f"[{s}] -> {t}")
                    okuma_raporu = "SÄ°NOPTÄ°K SAYFA - TARÄ°H EÅLEÅMELERÄ°:\n" + "-"*40 + "\n" + ("\n".join(mapped) if mapped else "âš™ EÅŸleÅŸme yok")
            except: pass

            # GMT KontrolÅŸ (SÃ¼tun Ä°simlendirme - Temizlikten Ã¼nce YapÄ±lmalÄ±)
            if "gmt" not in df_sin.columns:
                # 1. AdÃ¼m: BirleÅŸik Tarih-Saat (Datetime) sÃ¼tunu varsa saati oradan ayÄ±kla
                gmt_extracted = False
                for col in list(df_sin.columns):
                    col_str = str(col).lower()
                    if col_str in ["kayÄ±t", "kayit", "kayÄ±t zamanÄ±", "kayit zamani", "tarih", "date", "sayfa"]:
                        try:
                            # SÃ¼tunun gerÃ§ekten bir saat barÄ±ndÄ±rÄ±p barÃ¼ndÃ¼rmadÃ¼Ã¼nÅŸ test et
                            ornek = pd.to_datetime(df_sin[col].dropna().astype(str), errors='coerce')
                            if not ornek.isna().all():
                                if len(ornek.dt.hour.unique()) > 1 or (ornek.dt.hour > 0).any():
                                    df_sin["gmt"] = ornek.dt.hour
                                    gmt_extracted = True
                                    break
                        except: pass

                # 2. AdÃ¼m: AkÄ±llÄ± GMT SÃ¼tunu Bulma (EÃ¼er datetime'dan Ä°ÅkarÃ¼lamadÃ¼ysa)
                gmt_col_found = None
                if not gmt_extracted:
                    for col in df_sin.columns:
                        try:
                            vals = df_sin[col].dropna().unique()
                            target_hours = {0, 3, 6, 9, 12, 15, 18, 21, '00', '03', '06', '09', '12', '15', '18', '21'}
                            match_count = sum(1 for v in vals if v in target_hours)
                            
                            # SayÄ±sal AralÄ±k KontrolÅŸ (0-23 arasÄ± mÃ¼) - Ã¼stasyon No (17xxx) karÄ°ÅmasÃ¼nÅŸ Ã¶nler
                            is_valid_range = False
                            try:
                                nums = pd.to_numeric(vals, errors='coerce')
                                nums = nums[~pd.isna(nums)]
                                if len(nums) > 0 and nums.min() >= 0 and nums.max() <= 23:
                                    is_valid_range = True
                            except: pass
    
                            if match_count >= 2 or (is_valid_range and len(vals) >= 2):
                                gmt_col_found = col; break
                        except: pass
                
                if gmt_col_found: 
                    df_sin.rename(columns={gmt_col_found: "gmt"}, inplace=True)
                elif not gmt_extracted:
                    # Fallback: Bilinen sÃ¼tunlarÅŸ atla, ilk uygun sÃ¼tunu GMT yap
                    known_cols = ['istasyon_no', 'sayfa', 'tarih', 'personel', 'rasatci']
                    for col in df_sin.columns:
                        if str(col).lower() not in known_cols:
                            df_sin.rename(columns={col: "gmt"}, inplace=True)
                            break
            if "gmt" not in df_metar.columns:
                gmt_found = False
                
                # Ã¼nce METAR iÃ§in Datetime saat ayÄ±klama dene
                for col in list(df_metar.columns):
                    col_str = str(col).lower()
                    if col_str in ["kayÄ±t", "kayit", "kayÄ±t zamanÄ±", "kayit zamani", "tarih", "date", "sayfa"]:
                        try:
                            ornek = pd.to_datetime(df_metar[col].dropna().astype(str), errors='coerce')
                            if not ornek.isna().all() and (len(ornek.dt.hour.unique()) > 1 or (ornek.dt.hour > 0).any()):
                                df_metar["gmt"] = ornek.dt.hour
                                gmt_found = True
                                break
                        except: pass

                if not gmt_found and "sayfa" in df_metar.columns:
                    extracted = df_metar["sayfa"].astype(str).str.extract(r'(\d{2}:\d{2}Z?)')[0]
                    if not extracted.isna().all():
                        df_metar["gmt"] = extracted
                        df_metar["sayfa"] = df_metar["sayfa"].astype(str).str.split().str[0]
                        gmt_found = True
                        
                if not gmt_found and len(df_metar.columns) > 0:
                    # Rastgele ilk sÃ¼tunu almak yerine, gerÃ§ekten saat formatÄ±na (13:50 veya 1350Z) benzeyen bir sÃ¼tun bul
                    for col in df_metar.columns:
                        if col == 'sayfa': continue
                        sample = df_metar[col].dropna().astype(str).head(20)
                        if sample.str.contains(r'\d{2}:\d{2}').any() or sample.str.match(r'^\d{3,4}Z?$', flags=re.IGNORECASE).any():
                            df_metar.rename(columns={col: "gmt"}, inplace=True); break
                            
                # YENÄ° EKLENEN GÃœVENLÄ°K: Hala GMT bulunamadÄ±ysa Ä°Åkmemesi iÃ§in boÅŸ oluÅŸtur
                if "gmt" not in df_metar.columns:
                    df_metar["gmt"] = "00:00"

            # Veri TemizliÃ§i ve HazÄ±rlÄ±ÄŸÄ±
            for i, df in enumerate([df_sin, df_metar]):
                is_metar = (i == 1) # 1. indeks METAR
                
                # METAR BÃ¼lteninden GÃ¼râš¡ ve Hadise AyÄ±klama
                if is_metar:
                    # EÃ¼er "bulten" sÃ¼tunu yanlÄ°ÅlÃ¼kla "M" veya "S" gibi tip harflerini aldÄ±ysa dÃ¼zelt
                    if "bulten" in df.columns:
                        bulten_sample = df["bulten"].dropna().astype(str)
                        if not bulten_sample.empty and bulten_sample.map(len).max() < 10:
                            df.rename(columns={"bulten": "mesaj_tipi"}, inplace=True)

                    if "bulten" not in df.columns:
                        # GerÃ§ek bÃ¼lten sÃ¼tununu bul (Ä°ÅeriÃ§i en uzun olan metin sÃ¼tunu)
                        best_col = None
                        max_len = 0
                        for c in df.columns:
                            if c not in ["sayfa", "gmt", "tarih", "saat"]:
                                sample = df[c].replace(['nan', 'NAN', 'NaN', 'None', 'NONE'], pd.NA).dropna().astype(str)
                                if not sample.empty:
                                    avg_len = sample.map(len).mean()
                                    if avg_len > max_len:
                                        max_len = avg_len
                                        best_col = c
                        if best_col and max_len > 15:
                            df.rename(columns={best_col: "bulten"}, inplace=True)
                                
                    if "bulten" in df.columns:
                        def extract_vis(b):
                            m = re.search(r"\s(\d{4})\s", str(b))
                            return float(m.group(1)) if m else None
                        if "vv" not in df.columns:
                            df["vv"] = df["bulten"].apply(extract_vis)
                        if "ww" not in df.columns:
                            df["ww"] = df["bulten"]

                # GÃ¼venlik KontrolÃ¼: sayfa (GÃ¼n/Tarih) sÃ¼tunu yoksa oluÅŸtur
                if "sayfa" not in df.columns:
                    for col in df.columns:
                        if col not in ["gmt", "bulten", "tarih", "saat"]:
                            df.rename(columns={col: "sayfa"}, inplace=True); break
                    if "sayfa" not in df.columns: df["sayfa"] = "1"

                # GÃœVENLÄ°K: Excel sayfa ismi yerine, gerÃ§ekten bir Tarih/KayÄ±t sÃ¼tunu varsa daima onu kullan
                for col in list(df.columns):
                    col_str = str(col).lower()
                    if col_str in ["kayÄ±t", "kayit", "kayÄ±t zamanÄ±", "kayit zamani", "tarih", "date"]:
                        df["sayfa"] = df[col]
                        break

                # Ã¼nce Tarih FormatÄ±nÄ± DÃ¼zenle (Tarih kaydÄ±rma iÃ§in gerekli)
                df["sayfa"] = df["sayfa"].astype(str)
                df["sayfa"] = df["sayfa"].apply(lambda x: dm1.tarih_olustur_helper(x, yil, ay))
                
                # KESÄ°N Ä°ÅZÃ¼M: Dosyadan gelen yÄ±l/ay ile kullanÄ±cÄ±nÃ¼n girdiÃ§i yÄ±l/ay uyuÅŸmazsa 
                # SÄ°NOPTÄ°K verisi ÅŸablonla eÅŸleÅŸemez ve tamamen BOÅ Ä°Åkar.
                # Bu yÃ¼zden tÃ¼m tarihleri kullanÄ±cÄ±nÃ¼n arayÃ¼zde girdiÃ§i YIL ve AYA zorluyoruz!
                def yili_ayi_zorla(tarih_str):
                    if pd.isna(tarih_str): return tarih_str
                    try:
                        dt = pd.to_datetime(tarih_str, format='%d.%m.%Y', errors='coerce')
                        if pd.notna(dt):
                            _, max_gun = calendar.monthrange(yil, ay)
                            safe_day = min(dt.day, max_gun)
                            return pd.Timestamp(year=yil, month=ay, day=safe_day).strftime('%d.%m.%Y')
                    except: pass
                    return tarih_str
                    
                df["sayfa"] = df["sayfa"].apply(yili_ayi_zorla)
                df.dropna(subset=["sayfa"], inplace=True)

                if "gmt" in df.columns:
                    # Saat TemizliÃ§i ve AyrÄ°ÅtÃ¼rma
                    if "gmt_raw" not in df.columns:
                        df["gmt_raw"] = df["gmt"].astype(str).str.upper().str.replace('Z', '').str.strip()
                    
                    # Kardelen raporlarÄ±nÄ±n altÃ¼ndaki ham Åifre kÃ¼sÃ¼mlarÅŸ bazen veri tablosuna sÃ¼zabilir.
                    # Bu satÄ±rlarÄ± saat (gmt) formatÄ±nda olmadÃ¼klarÅŸ iÃ§in ayÄ±kla
                    mask_uzun = df["gmt_raw"].str.len() > 10
                    mask_cop = df["gmt_raw"].str.contains(r'(=|CAVOK|RASATLAR|17244)', regex=True, case=False, na=False)
                    # Orijinal referansÄ± (df_sin/df_metar) bozmamak iÃ§in in-place drop kullanmalÃ¼yÃ¼z!
                    df.drop(df[mask_uzun | mask_cop].index, inplace=True)

                    
                    if is_metar:
                        # METAR iÃ§in en yakÄ±n Sinoptik saatini bul (0050 -> 00, 2350 -> 00 ertesi gÃ¼n)
                        def match_time(row):
                            val = str(row.get("gmt_exact", row.get("gmt_raw", row["gmt"]))).strip()
                            if val.endswith('.0'): val = val[:-2]
                            date_val = row["sayfa"]
                            h, m = 0, 0
                            try:
                                time_match = re.search(r'(\d{1,2}):(\d{2})', val)
                                if time_match: h, m = int(time_match.group(1)), int(time_match.group(2))
                                else:
                                    if ' ' in val:
                                        last_part = val.split()[-1]
                                        if last_part.isdigit() or re.match(r'\d{3,4}Z?', last_part):
                                            val = last_part
                                        
                                    val = re.sub(r'[^0-9]', '', val)
                                    if len(val) >= 4: h, m = int(val[-4:-2]), int(val[-2:])
                                    elif len(val) == 3: h, m = int(val[:1]), int(val[1:])
                                    elif val.isdigit() and len(val) <= 2: h, m = int(val), 0
                                    else: return None, None, None
                            except: return None, None, None

                            orig_h, orig_m = h, m

                            # Dakika 40'tan bÃ¼yÃ¼kse bir sonraki saate yuvarla (Ã–rn: 23:50 -> 24:00)
                            if m >= 40:
                                h += 1
                                
                            if h >= 24:
                                h = 0
                                try:
                                    dt = pd.to_datetime(date_val, format="%d.%m.%Y") + datetime.timedelta(days=1)
                                    date_val = dt.strftime("%d.%m.%Y")
                                except: pass
                            
                            exact_gmt = f"{orig_h:02d}{orig_m:02d}"
                            return float(h), date_val, exact_gmt

                        if not df.empty:
                            res = df.apply(match_time, axis=1, result_type='expand')
                            if isinstance(res, pd.DataFrame) and 0 in res.columns and 1 in res.columns:
                                df["gmt"] = res[0]
                                df["sayfa"] = res[1]
                                df["gmt_exact"] = res[2] if 2 in res.columns else float('nan')
                    else:
                        # Sinoptik
                        def fix_sinoptik_time(row):
                            v = str(row.get("gmt_exact", row.get("gmt_raw", row["gmt"]))).strip()
                            date_val = row["sayfa"]
                            if not v or v.upper() == 'NAN' or v.upper() == 'NONE':
                                return float('nan'), date_val, float('nan')

                            h = None
                            m = 0
                            time_match = re.search(r'\b(\d{1,2}):(\d{2})', v)
                            if time_match:
                                h = int(time_match.group(1))
                                m = int(time_match.group(2))
                            else:
                                if ' ' in v:
                                    last_part = v.split()[-1]
                                    if last_part.isdigit() or re.match(r'\d{3,4}Z?', last_part):
                                        v = last_part
                                
                                match = re.match(r'^\d+', v)
                                if match:
                                    ext = match.group(0)
                                    if len(ext) == 6: h = int(ext[2:4])
                                    elif len(ext) == 5: h = int(ext[2:4])
                                    elif len(ext) >= 3: h = int(ext[:2]); m = int(ext[2:4]) if len(ext)>=4 else 0
                                    else: h = int(ext)
                                else:
                                    try: h = int(float(v))
                                    except: return float('nan'), date_val, float('nan')

                            if h is not None:
                                orig_h = h
                                orig_m = m
                                if h >= 24:
                                    h = 0
                                    try:
                                        dt = pd.to_datetime(date_val, format="%d.%m.%Y") + datetime.timedelta(days=1)
                                        date_val = dt.strftime("%d.%m.%Y")
                                    except: pass
                                exact_gmt = f"{orig_h:02d}{orig_m:02d}"
                                return float(h), date_val, exact_gmt
                            return float('nan'), date_val, float('nan')

                        if not df.empty:
                            res = df.apply(fix_sinoptik_time, axis=1, result_type='expand')
                            if isinstance(res, pd.DataFrame) and 0 in res.columns and 1 in res.columns:
                                df["gmt"] = res[0]
                                df["sayfa"] = res[1]
                                df["gmt_exact"] = res[2] if 2 in res.columns else float('nan')

                    df.dropna(subset=["gmt"], inplace=True)
                
                numeric_cols = ['ir', 'ix', 'rrr', 'ww', 'w1', 'w2', 't', 'td', 'n', 'nh', 'cl', 'cm', 'ch', 'dd', 'ff', 'vv', 'a', 'ppp', 'tx', 'tn', 'tg', 'p', 'p0', 'e', 'h', 'tr', 'g924', 'g910', 'g911', 'g931', 'g932', 'g960', 'rh']
                for col in numeric_cols:
                    # EÃ¼er zorunlu bir meteorolojik sÃ¼tun veride hiÃ§ yoksa Ã§Ã¶kmeyi Ã¶nlemek iÃ§in boÅŸ olarak ekle
                    if col not in df.columns:
                        df[col] = float('nan')

                    if col in df.columns:
                        if df[col].dtype == 'object':
                            # 1. GÃ¶rÃ¼nmez karakterleri (non-breaking space vb.) ve boÅŸluklarÅŸ temizle
                            df[col] = df[col].astype(str).str.replace(r'[\xa0\u200b]', '', regex=True).str.strip()
                            # 2. VirgÃ¼lÅŸ noktaya Ã§evir
                            df[col] = df[col].str.replace(',', '.', regex=False)
                            # 3. 'nan' metinlerini gerÃ§ek NaN'a dÃ¼nÄ°ÅtÃ¼r
                            df[col] = df[col].replace(['nan', 'NAN', 'None', 'NONE', '', '-', ' - '], float('nan'))
                        
                        if is_metar and col in ['ww', 'ww2', 'ww3']:
                            pass # METAR'da halihazÄ±r hava metin (RA, BR vb.) olabilir, sayÄ±sal deÄŸere zorlama
                        else:
                            if df[col].dtype == 'object':
                                # 4. HÃ¼creye yanlÄ°ÅlÃ¼kla "15 C" veya "1012 hPa" gibi metin girilmiÃ¼se sadece sayÄ±yÄ± kurtar
                                mask = df[col].notna()
                                df.loc[mask, col] = df.loc[mask, col].astype(str).str.extract(r'([+-]?\d+\.?\d*)', expand=False)
                                
                            df[col] = pd.to_numeric(df[col], errors="coerce")

            # EÅŸleÅŸme sorunlarÄ±nÄ± (Veri Yok hatasÄ±nÃ¼) Ã¶nlemek iÃ§in tarih formatlarÃ¼nÅŸ (%d.%m.%Y) ve saat tiplerini (float) GARANTÄ°YE alÄ±yoruz
            df_sin["sayfa"] = pd.to_datetime(df_sin["sayfa"], format='%d.%m.%Y', errors='coerce').dt.strftime('%d.%m.%Y')
            df_sin["gmt"] = pd.to_numeric(df_sin["gmt"], errors='coerce').astype(float)
            
            df_metar["sayfa"] = pd.to_datetime(df_metar["sayfa"], format='%d.%m.%Y', errors='coerce').dt.strftime('%d.%m.%Y')
            df_metar["gmt"] = pd.to_numeric(df_metar["gmt"], errors='coerce').astype(float)

            # Gruplama esnasÄ±nda first() metodunun boÅŸ stringleri alÄ±p asÄ±l metni ezmemesi iÃ§in boÅŸ hÃ¼creleri gerÃ§ek NaN yap
            df_metar.replace(r'^\s*-\s*$', pd.NA, regex=True, inplace=True)
            df_metar.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
            df_sin.replace(r'^\s*-\s*$', pd.NA, regex=True, inplace=True)
            df_sin.replace(r'^\s*$', pd.NA, regex=True, inplace=True)

            if '_raw_line' in df_sin.columns:
                df_sin['_raw_line'] = df_sin['_raw_line'].apply(lambda x: float('nan') if pd.isna(x) or str(x).strip().lower() in ['', 'nan', 'none'] else str(x).strip())

            if '_raw_line' in df_metar.columns:
                df_metar['_raw_line'] = df_metar['_raw_line'].apply(lambda x: float('nan') if pd.isna(x) or str(x).strip().lower() in ['', 'nan', 'none'] else str(x).strip())
                if 'bulten' in df_metar.columns:
                    df_metar['bulten'] = df_metar['bulten'].replace(['nan', 'NAN', 'NaN', 'None', 'NONE'], float('nan'))
                    df_metar['bulten'] = df_metar['bulten'].fillna(df_metar['_raw_line'])
                else:
                    df_metar['bulten'] = df_metar['_raw_line']

            if df_sin.empty:
                raise ValueError("Sinoptik verileri iÅŸlendikten sonra boÅŸ kaldÄ±! Tarih veya Saat sÃ¼tunlarÅŸ okunamamâš¡ olabilir.\nLÃ¼tfen Excel sayfa isimlerinin (1, 2, 3...) veya tarih formatÄ±nÃ¼n doÄŸru olduÅŸundan emin olun.")

            # Rasatlar SÃ¼tunu
            if not df_sin.empty:
                def raw_rasat_olustur(row):
                    if 'bulten' in row and pd.notna(row['bulten']) and str(row['bulten']).strip().lower() not in ["", "nan", "none"]:
                        return str(row['bulten'])
                    if '_raw_line' in row and pd.notna(row['_raw_line']) and str(row['_raw_line']).strip().lower() not in ["", "nan", "none"]:
                        return str(row['_raw_line'])

                    items = []
                    exclude = ['sayfa', 'gmt', 'tarih', 'istasyon_no', 'personel', 'g924', 'hadise_kayit', 'gmt_raw', '_raw_line', 'bulten']
                    for col in df_sin.columns:
                        if col not in exclude:
                            val = row.get(col)
                            if pd.notna(val):
                                val_str = str(val).strip()
                                if val_str:
                                    col_name = str(col).upper()
                                    if "UNNAMED" in col_name: items.append(val_str)
                                    else: items.append(f"{col_name}:{val_str}")
                    return " ".join(items)
                df_sin["RASATLAR"] = df_sin.apply(raw_rasat_olustur, axis=1)

            # Sadece geÃ§erli Sinoptik saatlerini filtrele ve tekrarlarÄ± temizle
            df_sin = df_sin[df_sin["gmt"].isin([0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0])]
            df_sin = df_sin.drop_duplicates(subset=["sayfa", "gmt"])

            sinoptik_sayisi = len(df_sin)
            metar_sayisi = len(df_metar)
            
            # SPECI ve METAR ayrÄ±mÄ±
            speci_sayisi = 0
            metar_normal_sayisi = metar_sayisi
            
            speci_mask = pd.Series(False, index=df_metar.index)
            if "mesaj_tipi" in df_metar.columns:
                speci_mask = speci_mask | df_metar["mesaj_tipi"].astype(str).str.contains(r'\b(?:SPECI|SP|S)\b', case=False, na=False)
            
            b_col_m = "bulten" if "bulten" in df_metar.columns else "_raw_line"
            if b_col_m in df_metar.columns:
                speci_mask = speci_mask | df_metar[b_col_m].astype(str).str.contains(r'\b(?:SPECI)\b', case=False, na=False)
                
            # YENÄ°: DakikasÄ± 50, 20 veya 00 olmayan rasatlarÄ± da SPECI (Ã–zel Rasat) kabul et
            if 'gmt_exact' in df_metar.columns:
                gmt_exact_str = df_metar['gmt_exact'].astype(str).str.upper().str.replace('Z', '', regex=False).str.strip()
                dakika_mask = ~gmt_exact_str.str.endswith(('50', '20', '00', 'NAN', 'NONE', '.0'))
                speci_mask = speci_mask | dakika_mask
                
            speci_sayisi = int(speci_mask.sum())
            metar_normal_sayisi = metar_sayisi - speci_sayisi

            # Ã¼ablon ve BirleÅŸtirme
            _, son_gun = calendar.monthrange(yil, ay)
            sablon_data = []
            for d in range(1, son_gun + 1):
                t_str = pd.Timestamp(year=yil, month=ay, day=d).strftime('%d.%m.%Y')
                for h in range(24): # 23:50'ler ertesi gÃ¼n 0'a devredeceÄŸi iÃ§in Ã¼ablon tekrar standart 24 saate (0-23) dÃ¶ndÃ¼rÃ¼ldÃ¼
                    sablon_data.append({"sayfa": t_str, "gmt": float(h)})
            df_sablon = pd.DataFrame(sablon_data)

            # --- KESÄ°N Ä°ÅZÃ¼M (REINDEXING HATASI Ã¼Ã¼N): SÃœTUNLARI VE Ä°NDEKSLERÄ° TEMÄ°ZLE ---
            for df_temp in [df_sin, df_metar]:
                df_temp.reset_index(drop=True, inplace=True) # Ä°ndeks Ã¼akÄ°ÅmalarÃ¼nÅŸ Ã¶nler
                if any(df_temp.columns.duplicated()):
                    cols = pd.Series(df_temp.columns)
                    for dup in cols[cols.duplicated()].unique():
                        dup_indices = cols[cols == dup].index.tolist()
                        for idx_num, idx in enumerate(dup_indices):
                            if idx_num != 0:
                                cols[idx] = f"{dup}_{idx_num}"
                    df_temp.columns = cols
            # ----------------------------------------------------------------------------

            df_sin = pd.merge(df_sablon, df_sin, on=["sayfa", "gmt"], how="left")
            
            # KESÄ°N Ä°ÅZÃ¼M: METAR verisindeki saat tekrarlarÄ±nÅŸ (Ham mesajlar ve Meteorolojik veriler ayrÄ± satÃ¼rlardadÃ¼r) ezmeden birleÃ¼tir
            df_metar['is_speci'] = speci_mask
            df_metar = df_metar.sort_values(by=['sayfa', 'gmt', 'is_speci'], ascending=[True, True, True]) # Rutin METAR'lar (False) Ã¼stte olsun
            
            # BoÅŸ stringleri None yapÄ±yoruz ki .first() metodu boÅŸ stringi gÃ¼rÃ¼p asÄ±l Åifreli mesajÅŸ ezmesin
            df_metar.replace(r'^\s*$', None, regex=True, inplace=True)
            df_metar.replace('-', None, inplace=True)
            
            df_metar_tekil = df_metar.groupby(["sayfa", "gmt"], as_index=False).first()
            df_metar_tekil.drop(columns=['is_speci'], inplace=True, errors='ignore')
            
            # YENÄ°: SÄ°NOPTÄ°K VE METAR SÃœTUNLARINI BÄ°RLEÅTÄ°RME VE RAPORLAMA Ã¼Ã¼N GARANTÄ°LEME
            # _sin ve _metar eklerinin Ã§iftlenmesini Ã¶nlemek iÃ§in replace yapÄ±yoruz
            df_sin.columns = [str(c) if str(c) in ['sayfa', 'gmt', 'RASATLAR'] else ("gmt_exact_sin" if c == "gmt_exact" else f"{str(c).replace('_sin', '')}_sin") for c in df_sin.columns]
            df_metar_tekil.columns = [str(c) if str(c) in ['sayfa', 'gmt', 'RASATLAR'] else ("gmt_exact_metar" if c == "gmt_exact" else f"{str(c).replace('_metar', '')}_metar") for c in df_metar_tekil.columns]
            
            # DEBUG: Merge Ã¶ncesi sÃ¼tunlarÅŸ gÃ¶ster
            print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
            print(f"{Colors.BOLD}MERGE Ã–NCESI SÃœTUNLar:{Colors.ENDC}")
            print(f"df_sin sÃ¼tun sayÄ±sÄ±: {len(df_sin.columns)}")
            print(f"df_sin ilk 10 sÃ¼tun: {list(df_sin.columns)[:10]}")
            print(f"\ndf_metar_tekil sÃ¼tun sayÄ±sÄ±: {len(df_metar_tekil.columns)}")
            print(f"df_metar_tekil ilk 10 sÃ¼tun: {list(df_metar_tekil.columns)[:10]}")
            print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
            
            birlesik = pd.merge(df_sin, df_metar_tekil, on=["sayfa", "gmt"], how="left", suffixes=('_sin', '_metar'))
            
            def extract_metar_time(row):
                try:
                    for col in ["_raw_line_met", "bulten_met", "_raw_line", "bulten"]:
                        if col in row and pd.notna(row[col]):
                            import re
                            m = re.search(r" \d{2}(\d{4})Z\b", str(row[col]).upper())
                            if m: return m.group(1)
                except: pass
                # Fallback to gmt - 10 minutes if we can't extract (typical metar time)
                try:
                    gmt_val = float(row.get("gmt", 0))
                    h = int(gmt_val)
                    if h == 0: return "2350"
                    return f"{h-1:02d}50"
                except: return "-"

            def format_sin_time(row):
                try:
                    return f"{int(float(row.get('gmt', 0))):02d}00"
                except: return "-"

            birlesik["SÄ°NOPTÄ°K - Saat"] = birlesik.apply(format_sin_time, axis=1)
            if "Saat_sin" in birlesik.columns:
                mask = birlesik["Saat_sin"].notna() & (birlesik["Saat_sin"].astype(str).str.strip() != "")
                birlesik.loc[mask, "SÄ°NOPTÄ°K - Saat"] = birlesik.loc[mask, "Saat_sin"]
                
            if "Saat_met" in birlesik.columns:
                birlesik["METAR - Saat"] = birlesik["Saat_met"]
            else:
                birlesik["METAR - Saat"] = birlesik.apply(extract_metar_time, axis=1)
            
            # DEBUG: Merge sonrasÅŸ sÃ¼tunlarÅŸ gÃ¶ster
            print(f"\n{Colors.BOLD}MERGE SONRASI SÃœTUNLar:{Colors.ENDC}")
            print(f"BirleÅŸik sÃ¼tun sayÄ±sÄ±: {len(birlesik.columns)}")
            print(f"BirleÅŸik ilk 20 sÃ¼tun: {list(birlesik.columns)[:20]}")
            print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
            
            # --- YENÄ° EKLENEN: PANDAS NaN DAVRANIÅLARINI GÃœVENLÄ° HALE GETÄ°RME ---
            # Metin (Object) sÃ¼tunlarÃ¼ndaki NaN deÄŸerlerini boÅŸ stringe ("") Ã§eviriyoruz.
            # Bu sayede validator ve analiz tarafÃ¼nda str(NaN) sonucu oluÅŸan "nan" kelimesinin
            # sahte hadise eÅŸleÅŸmelerine (Ã–rn: FG, N vb.) yol aÃ§masÄ±nÄ± kesin olarak Ã¶nlÃ¼yoruz.
            for col in birlesik.columns:
                if birlesik[col].dtype == 'object' or birlesik[col].dtype.name == 'category':
                    birlesik[col] = birlesik[col].replace(['nan', 'NAN', 'NaN', 'None', 'NONE', '-', ' - '], "")
                    birlesik[col] = birlesik[col].fillna("")
            
            # GeÃ¼miÅŸ METAR aramalarÄ±nda 'nan' kelimesi oluÅŸmasÄ±nÄ± Ã¶nlemek iÃ§in aynÄ± iÅŸlemi df_metar'a da uygula
            for col in df_metar.columns:
                if df_metar[col].dtype == 'object' or df_metar[col].dtype.name == 'category':
                    df_metar[col] = df_metar[col].replace(['nan', 'NAN', 'NaN', 'None', 'NONE', '-', ' - '], "")
                    df_metar[col] = df_metar[col].fillna("")
            # ------------------------------------------------------------------

            

# --- YENÄ° EKLENEN: HIZLI METAR CACHE SÄ°STEMÅŸ ---
            metar_cache = {}
            df_metar_records = df_metar.to_dict('records')
            for m_row in df_metar_records:
                m_tarih = str(m_row.get("sayfa", ""))
                m_saat = float(m_row.get("gmt")) if pd.notna(m_row.get("gmt")) else -1
                m_exact = m_row.get("gmt_exact")
                if m_tarih and m_tarih.lower() != 'nan' and m_saat >= 0:
                    try:
                        mg, ma, my = map(int, m_tarih.split('.'))
                        if pd.notna(m_exact):
                            exact_str = str(m_exact).replace('.0', '').zfill(4)
                            e_h, e_m = int(exact_str[:2]), int(exact_str[2:])
                            if e_h == 23 and int(m_saat) == 0:
                                m_dt = datetime.datetime(my, ma, mg) - datetime.timedelta(days=1)
                                m_dt = m_dt.replace(hour=e_h, minute=e_m)
                            else:
                                m_dt = datetime.datetime(my, ma, mg, e_h, e_m)
                        else:
                            m_dt = datetime.datetime(my, ma, mg, int(m_saat))
                        m_row['_m_dt'] = m_dt
                        d_key = m_dt.date()
                        if d_key not in metar_cache:
                            metar_cache[d_key] = []
                        metar_cache[d_key].append(m_row)
                    except: pass
            
            dt_hedef_list = []
            for row in birlesik.itertuples():
                try:
                    gmt_s = float(getattr(row, "gmt", 0))
                    dt_s_str = str(getattr(row, "sayfa", ""))
                    g, a, y = map(int, dt_s_str.split('.'))
                    dt_hedef = datetime.datetime(y, a, g, int(gmt_s))
                except:
                    dt_hedef = None
                dt_hedef_list.append(dt_hedef)
            birlesik['_dt_hedef'] = dt_hedef_list

            hesaplanan_ww_list = []
            for i, row in enumerate(birlesik.itertuples()):
                dt_hedef = dt_hedef_list[i]
                if dt_hedef is None:
                    hesaplanan_ww_list.append(float('nan'))
                    continue
                
                try:
                    gmt_s = float(getattr(row, "gmt", 0))
                    lb = 6 if gmt_s in [0.0, 6.0, 12.0, 18.0] else 3
                    dt_bas = dt_hedef - datetime.timedelta(hours=lb)
                    
                    d_keys = list(set([dt_bas.date(), dt_hedef.date()]))
                    relevant_metars = []
                    for dk in d_keys: relevant_metars.extend(metar_cache.get(dk, []))
                    
                    hadiseler = []
                    latest_prev_m_row = None
                    latest_prev_m_dt = None
                    
                    for m_row in relevant_metars:
                        m_dt = m_row['_m_dt']
                        if m_dt <= dt_bas:
                            if latest_prev_m_dt is None or m_dt > latest_prev_m_dt:
                                if dt_bas - m_dt <= datetime.timedelta(hours=1, minutes=15):
                                    latest_prev_m_dt = m_dt
                                    latest_prev_m_row = m_row
                        
                        if dt_bas < m_dt <= dt_hedef:
                            if pd.notna(m_row.get("ww")): hadiseler.append(str(m_row["ww"]))
                            if pd.notna(m_row.get("ww2")): hadiseler.append(str(m_row["ww2"]))
                            if pd.notna(m_row.get("ww3")): hadiseler.append(str(m_row["ww3"]))
                    
                    if latest_prev_m_row is not None:
                        if pd.notna(latest_prev_m_row.get("ww")): hadiseler.append(str(latest_prev_m_row["ww"]))
                        if pd.notna(latest_prev_m_row.get("ww2")): hadiseler.append(str(latest_prev_m_row["ww2"]))
                        if pd.notna(latest_prev_m_row.get("ww3")): hadiseler.append(str(latest_prev_m_row["ww3"]))
                        
                    hesaplanan_ww_list.append(get_ww_logic(hadiseler))
                except:
                    hesaplanan_ww_list.append(float('nan'))
            
            birlesik["ww_hesaplanan"] = hesaplanan_ww_list
            # ----------------------------------------------------------------

            # 2. Hata Analizi
            beklenen_sutunlar = [
                'p_sin', 'ff_sin', 'n_sin', 'p_metar', 'ff_metar', 'n_metar', 
                't_sin', 't_metar', 'td_sin', 'td_metar', 'p0_sin', 'p0_metar', 
                'dd_sin', 'dd_metar', 'vv_sin', 'vv_metar', 'w1_sin', 'w2_sin', 
                'ww_sin', 'ww_metar', 'rrr_sin', 'tr_sin', 'tx_sin', 'tn_sin', 
                'tg_sin', 'a_sin', 'ppp_sin'
            ]
            for b in beklenen_sutunlar:
                if b not in birlesik.columns: birlesik[b] = float('nan')
                else: birlesik[b] = pd.to_numeric(birlesik[b], errors='coerce')
                    
            if iptal_istendi: raise InterruptedError("Ä°Ålem kullanÄ±cÄ± tarafÃ¼ndan iptal edildi.")
            update_overall_progress(75, "Hata denetimi baÅŸlatÄ±lÄ±yor...")
            
            def progress_cb(completed, total, pct, remaining):
                overall_pct = int(75 + (pct * 0.25))
                if console_mode:
                    print(f"\rAnaliz ediliyor: {completed}/{total} (%{overall_pct})", end="", flush=True)
                    if pct >= 100: print()
                else:
                    def update_widgets():
                        if btn_run:
                            btn_run.config(text=f"ANALÄ°Z EDÄ°LÄ°YOR... %{overall_pct}")
                        elapsed = time.time() - start_time
                        if overall_pct > 0:
                            total_est = elapsed / (overall_pct / 100.0)
                            rem = max(0.0, total_est - elapsed)
                            rem_str = f" | Kalan: {int(rem)} sn" if overall_pct < 100 else ""
                        else: rem_str = ""
                        if lbl_status: lbl_status.config(text=f"Analiz ediliyor: {completed}/{total} (%{overall_pct}){rem_str}")
                    safe_after(0, update_widgets)
                return not iptal_istendi

            birlesik = dm2.hata_analizi_yap(birlesik, df_metar, progress_callback=progress_cb, df_sinoptik=df_sin_param)
            
            print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
            print(f"{Colors.BOLD}HATA ANALÄ°ZÄ° SONRASI - SÃœTUNLAR:{Colors.ENDC}")
            print(f"Toplam satÄ±r: {len(birlesik)}")
            print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

            # --- HIZLANDIRILMIÅ TEK DÃ–NGÃœ VE KONTROLLER ---
            b_col = "bulten_metar" if "bulten_metar" in birlesik.columns else "bulten"
            bulten_col_m = "bulten" if "bulten" in df_metar.columns else None
            
            if 'ANALÄ°Z_SONUCU' not in birlesik.columns and 'DURUM' in birlesik.columns:
                birlesik['ANALÄ°Z_SONUCU'] = birlesik['DURUM']
            if 'HATA_KODLARI' not in birlesik.columns: birlesik['HATA_KODLARI'] = ""
            if 'HATA_ACIKLAMALARI' not in birlesik.columns: birlesik['HATA_ACIKLAMALARI'] = ""
            if b_col not in birlesik.columns: birlesik[b_col] = ""

            analiz_sonucu_list = birlesik['ANALÄ°Z_SONUCU'].astype(str).tolist()
            hata_kodlari_list = birlesik['HATA_KODLARI'].astype(str).tolist()
            hata_aciklama_list = birlesik['HATA_ACIKLAMALARI'].astype(str).tolist()
            bulten_list = [str(x) if pd.notna(x) else "" for x in birlesik[b_col]]
            
            def add_error(i, kod, aciklama):
                mevcut = str(analiz_sonucu_list[i])
                if mevcut in ["Hata Yok", "Veri Yok", "Ara Rasat", "nan", "None"]:
                    analiz_sonucu_list[i] = "HatalÄ±"
                    hata_kodlari_list[i] = kod
                    hata_aciklama_list[i] = aciklama
                else:
                    if kod not in str(hata_kodlari_list[i]):
                        hata_kodlari_list[i] = str(hata_kodlari_list[i]) + f", {kod}"
                    hata_aciklama_list[i] = str(hata_aciklama_list[i]) + f" | {aciklama}"
            
            b_records = birlesik.to_dict('records')
            for i, row in enumerate(b_records):
                rasatlar_str = str(row.get('RASATLAR', ''))
                gmt = float(row.get("gmt")) if pd.notna(row.get("gmt")) else -1.0
                dt_hedef = dt_hedef_list[i]
                
                # 1. W1/W2 Uyumsuzluk KontrolÃ¼
                w1_ok_in_raw = False
                if ":" not in rasatlar_str and len(rasatlar_str.strip()) > 5 and SynopDecoder is not None:
                    decoder_tmp = SynopDecoder()
                    s_data_tmp = decoder_tmp.decode_line(rasatlar_str)
                    if s_data_tmp and ('gecmis_hava1' in s_data_tmp or 'gecmis_hava2' in s_data_tmp):
                        w1_ok_in_raw = True
                
                ww_calc = row.get("ww_hesaplanan")
                if gmt in [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0] and pd.notna(ww_calc) and not w1_ok_in_raw:
                    c = int(ww_calc)
                    expected_W1 = None
                    if c >= 90: expected_W1 = 9
                    elif 80 <= c <= 89: expected_W1 = 8
                    elif 70 <= c <= 79: expected_W1 = 7
                    elif 60 <= c <= 69: expected_W1 = 6
                    elif 50 <= c <= 59: expected_W1 = 5
                    elif 40 <= c <= 49: expected_W1 = 4
                    elif 30 <= c <= 39: expected_W1 = 3
                    
                    if expected_W1 is not None:
                        match = False
                        w1, w2 = row.get("w1_sin"), row.get("w2_sin")
                        if pd.notna(w1) and str(w1).strip() != "":
                            try:
                                w1_int = int(float(w1))
                                w2_int = int(float(w2)) if pd.notna(w2) and str(w2).strip() != "" else -1
                                if expected_W1 in [w1_int, w2_int]: match = True
                                elif expected_W1 == 6 and w1_int == 8: match = True
                                elif expected_W1 == 8 and w1_int == 6: match = True
                                elif expected_W1 == 7 and w1_int == 8: match = True
                                elif expected_W1 == 9 and w1_int == 8: match = True
                            except: pass
                        if not match:
                            saat_tipi = "6" if gmt in [0.0, 6.0, 12.0, 18.0] else "3"
                            add_error(i, "h361", f"Son {saat_tipi} saatlik METAR'da hadise var ancak SÄ°NOPTÄ°K GeÃ§miÅŸ Hava (W1/W2) eksik veya uyumsuz (Beklenen W1: {expected_W1}).")

                # 2. GeÃ§miÅŸ MetarlarÄ± Garantileme
                if "Veri Yok" not in str(analiz_sonucu_list[i]):
                    mevcut_bulten = str(bulten_list[i])
                    if mevcut_bulten.replace('"', '').replace("'", "").strip().lower() in ['nan', 'none', '<na>', '-', '']:
                        mevcut_bulten = ""
                    if dt_hedef and "Ä°LGÄ°LÄ° METAR GEÃ‡MÄ°ÅÄ°:" not in mevcut_bulten and bulten_col_m:
                        lb = 12 if gmt in [6.0, 18.0] else (6 if gmt in [0.0, 12.0] else 3)
                        dt_bas = dt_hedef - datetime.timedelta(hours=lb)
                        d_keys = list(set([dt_bas.date(), dt_hedef.date()]))
                        if dt_bas.date() != dt_hedef.date() and lb > 6:
                            d_keys.append((dt_hedef - datetime.timedelta(days=1)).date())
                        
                        relevant_metars = []
                        for dk in d_keys: relevant_metars.extend(metar_cache.get(dk, []))
                        
                        m_list = []
                        for m_row in relevant_metars:
                            m_dt = m_row['_m_dt']
                            gecerli = (dt_bas - datetime.timedelta(minutes=10)) <= m_dt <= dt_hedef
                            if gecerli:
                                m_raw = str(m_row.get(bulten_col_m, "")).strip()
                                if m_raw and m_raw.replace('"', '').replace("'", "").strip().lower() not in ['nan', 'none', '<na>', '-', '']:
                                    if mevcut_bulten and (m_raw in mevcut_bulten or mevcut_bulten in m_raw): continue
                                    if m_dt <= dt_bas:
                                        m_raw = re.sub(r' RE[A-Z]{2,} ', '', m_raw)
                                        m_raw = re.sub(r'\s+', ' ', m_raw).strip()
                                    z_match = re.search(r' \d{2}(\d{4}Z?) ', m_raw)
                                    z_saat = z_match.group(1) if z_match else f"{int(m_row.get('gmt', 0)):02d}00Z"
                                    m_list.append((m_dt, f"[{z_saat}] {m_raw}"))
                        
                        if m_list:
                            m_list.sort(key=lambda x: x[0], reverse=True)
                            ek_metar_bilgisi = "Ä°LGÄ°LÄ° METAR GEÃ‡MÄ°ÅÄ°:\n" + "\n".join([x[1] for x in m_list])
                            if not mevcut_bulten:
                                m_reg = re.match(r'^\[.*?\]\s*(.*)', m_list[0][1])
                                if m_reg: mevcut_bulten = m_reg.group(1)
                            if mevcut_bulten:
                                if ek_metar_bilgisi not in mevcut_bulten:
                                    bulten_list[i] = mevcut_bulten + "\n\n" + ek_metar_bilgisi
                                else: bulten_list[i] = mevcut_bulten
                            else: bulten_list[i] = ek_metar_bilgisi

                # 3. Validator Entegrasyonu
                if validator is not None:
                    sin_dict = {
                        'T': row.get('t_sin'), 'Td': row.get('td_sin'), 'Rh': row.get('rh_sin'),
                        'ff': row.get('ff_sin'), 'dd': row.get('dd_sin'), 
                        '4P': row.get('p_sin'), '3Po': row.get('p0_sin'), 'N': row.get('n_sin'),
                        'h': row.get('h_sin'), 'Nh': row.get('nh_sin'),
                        'Bg1': row.get('bg1_sin', row.get('cl_sin')), 'Bg2': row.get('bg2_sin', row.get('cm_sin')),
                        'Bg3': row.get('bg3_sin', row.get('ch_sin')), 'Bg4': row.get('bg4_sin'),
                        '910': row.get('g910_sin'), '911': row.get('g911_sin'), '924': row.get('g924_sin'),
                        'VV': row.get('vv_sin'), 'ww': row.get('ww_sin'), 'w1': row.get('w1_sin'), 'w2': row.get('w2_sin'),
                        'istasyon_no': row.get('istasyon_no_sin'), '960': row.get('g960_sin'),
                        'RASATLAR': rasatlar_str
                    }
                    met_dict = {
                        'Kuru': row.get('t_metar'), 'Ä°ÅŸba': row.get('td_metar'), '%': row.get('rh_metar'),
                        'HÄ±z': row.get('ff_metar'), 'YÃ¶n': row.get('dd_metar'), 
                        'QFE': row.get('p_metar'), 'QNH': row.get('p0_metar'), 'T. Kp.': row.get('n_metar'),
                        '1. BULUT Cins': row.get('1. bulut cins_metar', row.get('1. bulut_cins_metar')),
                        '2. BULUT Cins': row.get('2. bulut cins_metar', row.get('2. bulut_cins_metar')),
                        '3. BULUT Cins': row.get('3. bulut cins_metar', row.get('3. bulut_cins_metar')),
                        '4. BULUT Cins': row.get('4. bulut cins_metar', row.get('4. bulut_cins_metar')),
                        'Hakim': row.get('vv_metar'), 'Hadise': row.get('ww_metar'), 'WS': row.get('ws_metar'),
                        'Bulten': row.get('bulten_metar', '')
                    }
                    
                    if ":" not in rasatlar_str and len(rasatlar_str.strip()) > 5 and SynopDecoder is not None:
                        dec_tmp = SynopDecoder()
                        s_data_val = dec_tmp.decode_line(rasatlar_str)
                        if s_data_val:
                            def is_empty(v): return pd.isna(v) or str(v).strip() in ["", "nan", "None"]
                            if not is_empty(sin_dict.get('w1')):
                                try:
                                    w1_v = int(float(sin_dict['w1']))
                                    if w1_v > 9:
                                        w1_s = str(w1_v)
                                        if len(w1_s) == 2:
                                            sin_dict['w1'] = float(w1_s[0])
                                            sin_dict['w2'] = float(w1_s[1])
                                except: pass
                            if is_empty(sin_dict.get('w1')) and 'gecmis_hava1' in s_data_val: sin_dict['w1'] = s_data_val['gecmis_hava1']
                            if is_empty(sin_dict.get('w2')) and 'gecmis_hava2' in s_data_val: sin_dict['w2'] = s_data_val['gecmis_hava2']
                            if is_empty(sin_dict.get('ww')) and 'halihazir_hava' in s_data_val: sin_dict['ww'] = s_data_val['halihazir_hava']
                            if is_empty(sin_dict.get('960')) and 'halihazir_hava_2' in s_data_val: sin_dict['960'] = s_data_val['halihazir_hava_2']
                            if is_empty(sin_dict.get('910')) and 'hamle_hizi' in s_data_val: sin_dict['910'] = s_data_val['hamle_hizi']
                            if is_empty(sin_dict.get('911')) and 'max_ruzgar_hizi' in s_data_val: sin_dict['911'] = s_data_val['max_ruzgar_hizi']
                            if is_empty(sin_dict.get('924')) and 'raw_groups' in s_data_val and 'deniz_durumu' in s_data_val['raw_groups']: sin_dict['924'] = s_data_val['raw_groups']['deniz_durumu']

                    val_instance = validator.WeatherLogValidator(
                        sin_dict, met_dict,
                        metar_gmt=row.get('gmt_exact_metar', row.get('gmt')),
                        sinoptik_gmt=row.get('gmt_exact_sin', row.get('gmt'))
                    )
                    try:
                        if not hasattr(val_instance, 'check_cloud_base_crosscheck'): setattr(val_instance, 'check_cloud_base_crosscheck', lambda: None)
                        v_hatalar = val_instance.run_all_checks()
                    except: v_hatalar = val_instance.errors
                    
                    if v_hatalar:
                        for h_dict in v_hatalar:
                            hata_kod_ek = h_dict["kod"]
                            if hata_kod_ek in ["VAL_MANTIK_SPREAD", "h307"]: continue
                            
                            ww_error_codes = [f"h{k}" for k in range(78, 112)] + [f"h{k}" for k in range(364, 374)] + ["h380", "h381", "h382"]
                            w1w2_error_codes = ["h116", "h117", "h118"]
                            if hata_kod_ek in ww_error_codes + w1w2_error_codes:
                                n_val = sin_dict.get('N')
                                if pd.notna(n_val) and int(float(n_val)) == 7 and pd.notna(sin_dict.get('dd')) and pd.notna(sin_dict.get('ff')):
                                    if hata_kod_ek in ww_error_codes and (pd.isna(sin_dict.get('ww')) or float(sin_dict.get('ww')) != float(sin_dict.get('dd'))): continue
                                    if hata_kod_ek in w1w2_error_codes: continue
                            add_error(i, hata_kod_ek, h_dict["mesaj"])

                # 4. SynopDecoder (Format)
                if SynopDecoder is not None and ":" not in rasatlar_str and len(rasatlar_str.strip()) >= 5:
                    decoder = SynopDecoder()
                    decoder.decode_line(rasatlar_str)
                    if not decoder.validate():
                        for err in decoder.get_errors(): add_error(i, "h362", f"SÄ°NOPTÄ°K Format HatasÄ±: {err}")

                # 5. Taze/Toplam Kar KontrolÃ¼
                m_333 = re.search(r' 333 ', rasatlar_str)
                has_4e = False
                if m_333:
                    try:
                        bolum_3 = rasatlar_str[m_333.end():]
                        m_4e = re.search(r' 4(\d)(\d{3}) ', bolum_3)
                        if m_4e:
                            has_4e = True
                            sss = int(m_4e.group(2))
                            if sss == 0: add_error(i, "h245", "Kar erimiÅŸ (0 cm) ise 4E'sss grubu (Toplam Kar) rapora dahil edilmemelidir.")
                            elif 500 < sss < 997: add_error(i, "h243", f"Toplam kar kalÄ±nlÄ±ÄŸÄ± iÃ§in aÅŸÄ±rÄ± yÃ¼ksek bir deÄŸer ({sss} cm)")
                            
                        m_931 = re.search(r' 931(\d{2}) ', bolum_3)
                        if m_931:
                            ss = int(m_931.group(1))
                            gercek_kar_mm = -1
                            if 0 <= ss <= 55: gercek_kar_mm = ss * 10
                            elif 56 <= ss <= 90: gercek_kar_mm = (ss - 50) * 100
                            elif 91 <= ss <= 96: gercek_kar_mm = ss - 90
                            if gercek_kar_mm >= 900: add_error(i, "h242", f"Taze kar iÃ§in yÃ¼ksek bir deÄŸer")
                    except: pass
                if gmt == 6.0 and re.search(r' 931\d{2} ', rasatlar_str) and not has_4e and not re.search(r' 93100 ', rasatlar_str):
                    add_error(i, "h244", "0600 GMT rasadÄ±nda taze kar (931) bildirilmiÅŸ ancak toplam kar kalÄ±nlÄ±ÄŸÄ± (4E'sss) grubu eksik.")

                # 6. Metar Decoder
                b_col_metar_raw = "METAR - Åifreli Mesaj" if "METAR - Åifreli Mesaj" in row else ("bulten_metar" if "bulten_metar" in row else "bulten")
                metar_str = str(row.get(b_col_metar_raw, ''))
                if MetarDecoder is not None and metar_str and len(metar_str.strip()) >= 10:
                    try:
                        decoder = MetarDecoder()
                        decoder.decode_line(metar_str)
                        if hasattr(decoder, 'errors') and decoder.errors:
                            for err in decoder.errors: add_error(i, "h363", f"METAR Format HatasÄ±: {err}")
                    except Exception as e:
                        add_error(i, "h363", f"METAR Ä°ÅzÃ¼mleme HatasÄ±: Beklenmeyen format veya karakter ({e})")
                        
                # 7. Scrub Spread Error (hata listesinden silme)
                kod_metni = str(hata_kodlari_list[i])
                if 'VAL_MANTIK_SPREAD' in kod_metni:
                    yeni_kodlar = [x.strip() for x in kod_metni.split(',') if x.strip() and x.strip() != 'VAL_MANTIK_SPREAD']
                    hata_kodlari_list[i] = ', '.join(yeni_kodlar)
                    yeni_aciklamalar = [x.strip() for x in str(hata_aciklama_list[i]).split('|') if 'SÄ±caklÄ±k ve Ä°Åba' not in x and 'VAL_MANTIK_SPREAD' not in x]
                    hata_aciklama_list[i] = ' | '.join(yeni_aciklamalar)
                    if not yeni_kodlar and analiz_sonucu_list[i] == 'HatalÄ±':
                        analiz_sonucu_list[i] = 'Hata Yok'

            # Listeleri DataFrame'e geri yaz
            birlesik['ANALÄ°Z_SONUCU'] = analiz_sonucu_list
            birlesik['HATA_KODLARI'] = hata_kodlari_list
            
            rasatlar_list = birlesik.get('RASATLAR', pd.Series([''] * len(birlesik))).astype(str).tolist()
            for i in range(len(birlesik)):
                if 'ğŸ’¡ Ä°LGÄ°LÄ° GEÃ‡MÄ°Å SÄ°NOPTÄ°K:' in str(hata_aciklama_list[i]):
                    parts = str(hata_aciklama_list[i]).split('ğŸ’¡ Ä°LGÄ°LÄ° GEÃ‡MÄ°Å SÄ°NOPTÄ°K:')
                    hata_aciklama_list[i] = parts[0].strip()
                    ek = 'Ä°LGÄ°LÄ° GEÃ‡MÄ°Å SÄ°NOPTÄ°K:' + parts[1]
                    if ek not in rasatlar_list[i]:
                        rasatlar_list[i] = rasatlar_list[i] + '\n\n' + ek if rasatlar_list[i].strip() else ek
            birlesik['RASATLAR'] = rasatlar_list
            birlesik['HATA_ACIKLAMALARI'] = hata_aciklama_list
            
            birlesik[b_col] = bulten_list
            
            # --- METAR HALÄ°HAZIR HAVA (1, 2 ve 3. GRUP) SÃœTUNLARINI BÄ°RLEÅTÄ°R ---
            ww_metar_cols = [c for c in ['ww_metar', 'ww2_metar', 'ww3_metar'] if c in birlesik.columns]
            if len(ww_metar_cols) > 1:
                def metar_ww_birlestir(row):
                    vals = []
                    for c in ww_metar_cols:
                        val = str(row[c]).strip()
                        if val and val.lower() != 'nan':
                            if val not in vals: # AynÄ± hadise tekrarlanmasÃ¼n (Ã–rn: RA RA -> RA)
                                vals.append(val)
                    return " ".join(vals) if vals else float('nan')
                
                birlesik['ww_metar'] = birlesik.apply(metar_ww_birlestir, axis=1)
                birlesik.drop(columns=[c for c in ww_metar_cols if c != 'ww_metar'], inplace=True, errors='ignore')
                
            # SAAT YAZIMLARINI 0000, 1500, 1200 ÅEKLÄ°NDE GÃ–STER
            def format_saat_str(x):
                try: return f"{int(float(x)):02d}00"
                except: return str(x)
            
            birlesik["gmt"] = birlesik["gmt"].apply(format_saat_str)

            # SÃ¼tun Ä°simlendirme ve SÄ±ralama
            col_map = {
                'sayfa': 'Tarih', 'gmt': 'Saat (GMT)', 'gmt_exact_sin': 'SÄ°NOPTÄ°K - Saat', 'gmt_exact_metar': 'METAR - Saat',
                'ir': 'Ä°ndikatÃ¶r (ir)', 'ix': 'Ä°ndikatÃ¶r (ix)',
                'h': 'Bulut YÃ¼k. (h)', 'vv': 'GÃ¼râš¡ (VV)', 'n': 'Toplam Bulut (N)',
                'dd': 'RÃ¼zgar YÃ¶nÅŸ (dd)', 'ff': 'RÃ¼zgar HÄ±zÄ± (ff)', 't': 'SÄ±caklÄ±k (T)',
                'td': 'Ä°Åba (Td)', 'p0': 'Deniz BasÄ±ncÄ± (P0)', 'p': 'Ã¼stasyon BasÄ±ncÄ± (P)',
                'a': 'BasÄ±nÃ§ Karakteri (a)', 'ppp': 'BasÄ±nÃ§ DeÃ¼iÃ§imi (ppp)',
                'nh': 'AlÃ§ak/Orta Bulut (Nh)', 'cl': 'AlÃ§ak Bulut (CL)', 'cm': 'Orta Bulut (CM)',
                'ch': 'YÃ¼ksek Bulut (CH)', 'tx': 'Maks. SÄ±caklÄ±k (Tx)', 'tn': 'Min. SÄ±caklÄ±k (Tn)',
                'tg': 'Toprak SÄ±caklâš™ (Tg)', 'e': 'Yerin Hali (E)', 'rrr': 'Yaâš™ MiktarÄ± (RRR)',
                'tr': 'Yaâš™ SÃ¼resi (tR)', 'g910': '910 Grubu (Hamle)', 'g911': '911 Grubu (Hamle)',
                'g931': '931 Grubu (Kar)', 'g932': '932 Grubu (Taze Kar)', 'g960': '960 Grubu (Hadise)', 
                'rh': 'BaÄ°Ål Nem (%)', 'tw': 'Islak SÄ±caklÄ±k (Tw)', 
                'buhar': 'BuharlaÅŸma', 'rad_tipi': 'Radyasyon Tipi', 'radyasyon': 'Radyasyon MiktarÄ±',
                'gunes': 'GÃ¼neÃ¼lenme SÃ¼resi', 'deniz_suyu': 'Deniz Suyu SÄ±c.', 'rrr_toplam': 'Toplam YaÃ¼Ã¼',
                'buh_alet_tipi': 'Buhar Aleti Tipi', 'e_kar': 'Yerin Hali (Kar)',
                'top_ustu_min': 'Toprak ÃœstÅŸ Min.',
                'mak_deger': 'Mak',
                '1. bulut kap': '1. Bulut Kap.', '1. bulut cins': '1. Bulut Cinsi', '1. bulut yuk': '1. Bulut YÃ¼k.',
                '2. bulut kap': '2. Bulut Kap.', '2. bulut cins': '2. Bulut Cinsi', '2. bulut yuk': '2. Bulut YÃ¼k.',
                '3. bulut kap': '3. Bulut Kap.', '3. bulut cins': '3. Bulut Cinsi', '3. bulut yuk': '3. Bulut YÃ¼k.',
                '4. bulut kap': '4. Bulut Kap.', '4. bulut cins': '4. Bulut Cinsi', '4. bulut yuk': '4. Bulut YÃ¼k.',
                'ww_hesaplanan': 'RE/GEÃ¼Mâš¡ HADÄ°SE',
                'ANALÄ°Z_SONUCU': 'DURUM', 'HATA_KODLARI': 'HATA KODU', 'HATA_ACIKLAMALARI': 'AÃ‡IKLAMA',
                'RASATLAR': 'SÄ°NOPTÄ°K - Åifreli Mesaj', 'g924': '924 Grubu', 'hadise_kayit': 'Hadise KayÄ±tlarÃ¼',
                'personel': 'Personel',
                'bulten': 'METAR - Åifreli Mesaj'
            }

            if "bulten" in birlesik.columns and "bulten_metar" in birlesik.columns:
                birlesik.drop(columns=["bulten"], inplace=True)
                birlesik.rename(columns={"bulten_metar": "bulten"}, inplace=True)
            elif "bulten_metar" in birlesik.columns:
                birlesik.rename(columns={"bulten_metar": "bulten"}, inplace=True)

            new_columns = {}
            for c in birlesik.columns:
                base = c.replace('_sin', '').replace('_metar', '')
                suffix = '_sin' if '_sin' in c else ('_metar' if '_metar' in c else '')
                if base in col_map:
                    new_name = col_map[base]
                    if new_name.startswith("SÄ°NOPTÄ°K") or new_name.startswith("METAR"):
                        new_columns[c] = new_name
                    elif suffix == '_sin': new_name = f"SÄ°NOPTÄ°K - {new_name}"
                    elif suffix == '_metar': new_name = f"METAR - {new_name}"
                    new_columns[c] = new_name
                else: 
                    if suffix == '_sin': new_columns[c] = f"SÄ°NOPTÄ°K - {base.upper()}"
                    elif suffix == '_metar': new_columns[c] = f"METAR - {base.upper()}"
                    else: new_columns[c] = c.upper()
            birlesik.rename(columns=new_columns, inplace=True)

            # AynÄ± isme sahip sÃ¼tunlar oluÅŸursa (Ã–rn: iki tane PERSONEL) Pandas'Ã¼n Ä°Åkmesini engellemek iÃ§in tekilleÅŸtir
            if any(birlesik.columns.duplicated()):
                cols = pd.Series(birlesik.columns)
                for dup in cols[cols.duplicated()].unique():
                    dup_indices = cols[cols == dup].index.tolist()
                    for idx_num, idx in enumerate(dup_indices):
                        if idx_num != 0:
                            cols[idx] = f"{dup}_{idx_num}"
                birlesik.columns = cols

            # --- Ä°STENEN KESÄ°N SÃœTUN SIRALAMASI ---
            istenen_siralama = [
                'Tarih', 'Saat (GMT)', 'SÄ°NOPTÄ°K - Saat', 'METAR - Saat', 'SÄ°NOPTÄ°K - Åifreli Mesaj', 'METAR - Åifreli Mesaj', 'DURUM', 'HATA KODU', 'AÃ‡IKLAMA',
                'SÄ°NOPTÄ°K - Ä°ndikatÃ¶r (ir)', 'SÄ°NOPTÄ°K - Ä°ndikatÃ¶r (ix)', 'SÄ°NOPTÄ°K - Bulut YÃ¼k. (h)', 'SÄ°NOPTÄ°K - GÃ¼râš¡ (VV)', 'METAR - GÃ¼râš¡ (VV)',
                'SÄ°NOPTÄ°K - Toplam Bulut (N)', 'METAR - Toplam Bulut (N)', 'SÄ°NOPTÄ°K - RÃ¼zgar YÃ¶nÅŸ (dd)', 'METAR - RÃ¼zgar YÃ¶nÅŸ (dd)',
                'SÄ°NOPTÄ°K - RÃ¼zgar HÄ±zÄ± (ff)', 'METAR - RÃ¼zgar HÄ±zÄ± (ff)', 'SÄ°NOPTÄ°K - SÄ±caklÄ±k (T)', 'METAR - SÄ±caklÄ±k (T)',
                'SÄ°NOPTÄ°K - Ä°Åba (Td)', 'METAR - Ä°Åba (Td)', 'SÄ°NOPTÄ°K - Deniz BasÄ±ncÄ± (P0)', 'METAR - Deniz BasÄ±ncÄ± (P0)',
                'SÄ°NOPTÄ°K - Ã¼stasyon BasÄ±ncÄ± (P)', 'METAR - Ã¼stasyon BasÄ±ncÄ± (P)', 'SÄ°NOPTÄ°K - BasÄ±nÃ§ Karakteri (a)', 'SÄ°NOPTÄ°K - BasÄ±nÃ§ DeÃ¼iÃ§imi (ppp)',
                'SÄ°NOPTÄ°K - HalihazÄ±r Hava (ww)', 'METAR - HalihazÄ±r Hava (ww)', 'SÄ°NOPTÄ°K - GeÃ¼miÅŸ Hava 1 (W1)', 'SÄ°NOPTÄ°K - GeÃ¼miÅŸ Hava 2 (W2)',
                'SÄ°NOPTÄ°K - AlÃ§ak/Orta Bulut (Nh)', 'SÄ°NOPTÄ°K - AlÃ§ak Bulut (CL)', 'SÄ°NOPTÄ°K - Orta Bulut (CM)', 'SÄ°NOPTÄ°K - YÃ¼ksek Bulut (CH)',
                'SÄ°NOPTÄ°K - Maks. SÄ±caklÄ±k (Tx)', 'SÄ°NOPTÄ°K - Min. SÄ±caklÄ±k (Tn)', 'SÄ°NOPTÄ°K - Toprak SÄ±caklâš™ (Tg)', 'SÄ°NOPTÄ°K - Yerin Hali (E)',
                'SÄ°NOPTÄ°K - Yaâš™ MiktarÄ± (RRR)', 'SÄ°NOPTÄ°K - Yaâš™ SÃ¼resi (tR)', 'SÄ°NOPTÄ°K - 910 Grubu (Hamle)', 'SÄ°NOPTÄ°K - 911 Grubu (Hamle)',
                'SÄ°NOPTÄ°K - 924 Grubu', 'SÄ°NOPTÄ°K - 931 Grubu (Kar)', 'SÄ°NOPTÄ°K - 932 Grubu (Taze Kar)', 'SÄ°NOPTÄ°K - 960 Grubu (Hadise)',
                'SÄ°NOPTÄ°K - BaÄ°Ål Nem (%)', 'METAR - BaÄ°Ål Nem (%)', 'METAR - Islak SÄ±caklÄ±k (Tw)', 'SÄ°NOPTÄ°K - Toplam YaÃ¼Ã¼', 'SÄ°NOPTÄ°K - Yerin Hali (Kar)',
                'METAR - 1. Bulut Kap.', 'METAR - 1. Bulut Cinsi', 'METAR - 1. Bulut YÃ¼k.', 'METAR - 2. Bulut Kap.', 'METAR - 2. Bulut Cinsi', 'METAR - 2. Bulut YÃ¼k.',
                'METAR - 3. Bulut Kap.', 'METAR - 3. Bulut Cinsi', 'METAR - 3. Bulut YÃ¼k.', 'METAR - 4. Bulut Kap.', 'METAR - 4. Bulut Cinsi', 'METAR - 4. Bulut YÃ¼k.',
                'RE/GEÃ¼Mâš¡ HADÄ°SE', 'SÄ°NOPTÄ°K - Personel', 'METAR - Personel', 'SÄ°NOPTÄ°K - BG4', 'METAR - DIKINE_GORUS', 'SÄ°NOPTÄ°K - GMT_RAW', 'METAR - INCH'
            ]
            
            mevcut_istenen = [c for c in istenen_siralama if c in birlesik.columns]

            # UNNAMED, NAN veya isimsiz anlamsÄ±z sÃ¼tunlarÅŸ nihai Excel raporundan tamamen gizle (Zaten RASATLAR sÃ¼tununa eklendiler)
            def anlamsiz_mi(kolon_adi):
                k_str = str(kolon_adi).upper()
                if "UNNAMED" in k_str or "NAN" == k_str.strip():
                    return True
                if "METAR - " in k_str:
                    istenmeyen_metar_sutunlari = [
                        "911 GRUBU", "MÄ°N. SICAKLIK", "MIN. SICAKLIK", "BULUT YÃœK. (H)", "2. GRUP", "GMT_RAW", "Ä°NDÄ°KATÃ–R", "INDIKATOR",
                        "YAÄIÅ MÄ°KTARI", "GEÃ¼Mâš¡ HAVA", "GECMIS HAVA", "ALÃ¼AK/ORTA BULUT", "ALCAK/ORTA BULUT", "ALÃ¼AK BULUT", "ALCAK BULUT",
                        "ORTA BULUT", "YÃœKSEK BULUT", "YUKSEK BULUT", "BASINÃ‡ KARAKTERÃ¼", "BASINC KARAKTERI", "BASINÃ‡ DEÃ¼Ã¼Ã¼MÃ¼", "BASINC DEGISIMI",
                        "MAKS. SICAKLIK", "TOPRAK SICAKLIÄI", "TOPRAK SICAKLIGI", "YERÄ°N HALÃ¼", "YERIN HALI", "YAÄIÅ SÃœRESÄ°", "YAGIS SURESI",
                        "924 GRUBU", "910 GRUBU", "931 GRUBU", "932 GRUBU", "960 GRUBU", "3. GRUP"
                    ]
                    if any(istenmeyen in k_str for istenmeyen in istenmeyen_metar_sutunlari):
                        return True
                # Eksiksiz tam dÃ¶kÃ¼m iÃ§in METAR veri alanlarÃ¼nÃ¼n filtrelenerek gizlenmesi iptal edildi.
                return False
                
            digerleri = [c for c in birlesik.columns if c not in mevcut_istenen and not anlamsiz_mi(c)]
            
            # Geriye kalan ve listede olmayan ekstra sÃ¼tunlarÅŸ da isim benzerliÃ§ine gÃ¶re yan yana getir
            kalan_gruplar = {}
            for c in digerleri:
                base = str(c).replace("SÄ°NOPTÄ°K - ", "").replace("METAR - ", "")
                if base not in kalan_gruplar:
                    kalan_gruplar[base] = []
                kalan_gruplar[base].append(c)
                
            sirali_digerleri = []
            for base in sorted(kalan_gruplar.keys()):
                # Alfabetik ters sÄ±ralama ile (S)Ä°NOPTÄ°K'in (M)ETAR'dan Ã¼nce gelmesini saÄŸlar
                sirali_grup = sorted(kalan_gruplar[base], reverse=True) 
                sirali_digerleri.extend(sirali_grup)

            birlesik = birlesik[mevcut_istenen + sirali_digerleri]
            # -------------------------------------------------------------------------------------

            # LOG DOSYASI Ã‡IKTISI: Ä°Ålem Ã–zeti ve Hatalar
            print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
            print(f"{Colors.BOLD}Ä°ÅLEM Ã–ZETÄ° VE HATALI RASATLAR ({ay}/{yil}){Colors.ENDC}")
            print(f"{Colors.HEADER}{'-' * 60}{Colors.ENDC}")
            print(f"Okunan SÄ°NOPTÄ°K SayÄ±sÄ± : {Colors.OKBLUE}{sinoptik_sayisi}{Colors.ENDC}")
            print(f"Okunan METAR SayÄ±sÄ±    : {Colors.OKBLUE}{metar_sayisi}{Colors.ENDC}")
            print(f"Ã¼ablon KayÄ±t SayÄ±sÄ±    : {Colors.OKBLUE}{len(birlesik)}{Colors.ENDC}")

            logging.info("="*60)
            logging.info(f"Ä°ÅLEM Ã–ZETÄ° VE HATALI RASATLAR ({ay}/{yil})")
            logging.info("-" * 60)
            logging.info(f"Okunan SÄ°NOPTÄ°K SayÄ±sÄ± : {sinoptik_sayisi}")
            logging.info(f"Okunan METAR SayÄ±sÄ±    : {metar_sayisi}")
            logging.info(f"Ã¼ablon KayÄ±t SayÄ±sÄ±    : {len(birlesik)}")
            
            hatali_kayitlar = birlesik[~birlesik["DURUM"].isin(["Hata Yok", "Ara Rasat"])]
            print(f"HatalÄ± KayÄ±t SayÄ±sÄ±    : {Colors.FAIL}{len(hatali_kayitlar)}{Colors.ENDC}")
            print(f"{Colors.HEADER}{'-' * 60}{Colors.ENDC}")
            logging.info(f"HatalÄ± KayÄ±t SayÄ±sÄ±    : {len(hatali_kayitlar)}")
            logging.info("-" * 60)
            
            # --- YENI ALARM MANTIGI ---
            try:
                ayarlar = ayarlari_yukle()
                if ayarlar.get("alarm_aktif", False):
                    global previous_error_codes
                    if 'previous_error_codes' not in globals():
                        previous_error_codes = set()
                    
                    current_error_codes = set()
                    for codes in hatali_kayitlar["HATA KODU"].dropna():
                        for code in str(codes).split(','):
                            code = code.strip()
                            if code: current_error_codes.add(code)
                            
                    new_errors = current_error_codes - previous_error_codes
                    if new_errors:
                        import winsound
                        winsound.Beep(1000, 1000) # 1000Hz 1 saniye
                        logging.info(f"YENÄ° HATA BULUNDU! Alarm Ã¼alÃ¼ndÃ¼. Yeni Hatalar: {new_errors}")
                    previous_error_codes = current_error_codes
            except Exception as e:
                logging.error(f"Alarm hatasÄ±: {e}")

            # --- YENI HTML REPORT ---
            try:
                ayarlar = ayarlari_yukle()
                if ayarlar.get("web_server_aktif", False):
                    display_cols = ["GÃ¼N", "SAAT", "HATA KODU", "AÃ‡IKLAMA"]
                    mevcut_cols = [c for c in display_cols if c in hatali_kayitlar.columns]
                    html_df = hatali_kayitlar[mevcut_cols] if mevcut_cols else hatali_kayitlar
                    html_str = html_df.to_html(classes='table table-striped table-bordered table-hover', index=False, justify='center')
                    
                    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>HATA RAMA - GÃ¼ncel Analiz</title>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
    <style>
        body {{ padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }}
        .container-fluid {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class='container-fluid'>
        <h2 class='mb-4 text-primary'>GÃ¼ncel SÄ°NOPTÄ°K Analiz SonuÃ§larÄ±</h2>
        <div class='mb-3 text-muted'>Son GÃ¼ncellenme: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</div>
        <div class='table-responsive'>
            {html_str}
        </div>
    </div>

    <!-- Bootstrap Modal -->
    <div class="modal fade" id="detailModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title text-danger fw-bold">ğŸ” Hata Detay Ä°ncelemesi</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" id="modalContent" style="font-family: monospace; white-space: pre-wrap;">
          </div>
        </div>
      </div>
    </div>

    <script src='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            var table = document.querySelector(".table");
            if(table) {{
                var thead = table.querySelector("thead tr");
                var tbody = table.querySelector("tbody");
                
                if (thead && tbody) {{
                    var th = document.createElement("th");
                    th.innerHTML = "Aksiyon";
                    thead.appendChild(th);
                    
                    var headers = Array.from(thead.querySelectorAll("th")).map(th => th.innerText);
                    
                    Array.from(tbody.querySelectorAll("tr")).forEach(function(tr) {{
                        var td = document.createElement("td");
                        var btn = document.createElement("button");
                        btn.className = "btn btn-primary btn-sm fw-bold";
                        btn.innerHTML = "ğŸ” Ä°NCELE";
                        btn.onclick = function() {{
                            var cells = tr.querySelectorAll("td");
                            var content = "";
                            for(var i=0; i<cells.length-1; i++) {{
                                content += "â€¢ " + headers[i].toUpperCase() + ":
" + cells[i].innerText + "

";
                            }}
                            document.getElementById("modalContent").innerText = content;
                            var myModal = new bootstrap.Modal(document.getElementById('detailModal'));
                            myModal.show();
                        }};
                        td.appendChild(btn);
                        tr.appendChild(td);
                    }});
                }}
            }}
            setTimeout(function(){{ location.reload(); }}, 30000);
        }});
    </script>
</body>
</html>"""
                    page = html_template
                    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "latest_report.html"), "w", encoding="utf-8") as f:
                        f.write(page)
            except Exception as e:
                logging.error(f"HTML Rapor hatasÄ±: {e}")
            
            if iptal_istendi: raise InterruptedError("Ä°Ålem kullanÄ±cÄ± tarafÃ¼ndan iptal edildi.")
            if not hatali_kayitlar.empty:
                print(f"{Colors.BOLD}{'TARÄ°H':<15} {'SAAT':<10} {'HATA KODU'}{Colors.ENDC}")
                print(f"{Colors.HEADER}{'-' * 60}{Colors.ENDC}")
                print(f"{Colors.BOLD}HATALI KAYIT DETAYLARI:{Colors.ENDC}")
                print(f"{Colors.HEADER}{'-' * 80}{Colors.ENDC}")
                logging.info("HATALI KAYIT DETAYLARI:")
                logging.info("-" * 80)
                for _, row in hatali_kayitlar.iterrows():
                    tarih = str(row.get('Tarih', ''))
                    saat = str(row.get('Saat (GMT)', ''))
                    hata_kodu = str(row.get('HATA KODU', ''))
                    aciklama = str(row.get('AÃ‡IKLAMA', ''))
                    sin_ham = str(row.get('SÄ°NOPTÄ°K - Åifreli Mesaj', ''))
                    met_ham = str(row.get('METAR - Åifreli Mesaj', ''))
                    personel = str(row.get('SÄ°NOPTÄ°K - Personel', row.get('Personel', 'Bilinmiyor/BelirtilmemiÅŸ')))
                    
                    print(f"{tarih: <15} {saat: <10} {Colors.FAIL}{hata_kodu}{Colors.ENDC}")
                    logging.info(f"[{tarih} - {saat} GMT] HATA: {hata_kodu}")
                    logging.info(f" -> AÃ‡IKLAMA : {aciklama}")
                    logging.info(f" -> SÄ°NOPTÄ°K : {sin_ham}")
                    logging.info(f" -> METAR    : {met_ham}")
                    logging.info(f" -> PERSONEL : {personel}")
                    logging.info("-" * 80)
            else:
                print(f"{Colors.OKGREEN}Tebrikler! HiÃ§bir hata bulunamadÄ±.{Colors.ENDC}")
                logging.info("Tebrikler! HiÃ§bir hata bulunamadÄ±.")
            print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
            logging.info("="*60)
            
            # LOG HANDLER'INI FLUSH ET (Verilerin disk'e yazÄ±lmasÄ± iÃ§in)
            logging_handler.flush()
            
            # --- YENÄ°: EXCEL YERÄ°NE EKRANDA HIZLI GÃ–STERÄ°M ---
            # --- Ã¼NBELLEÃ¼E KAYDET ---
            try:
                cache_path = os.path.join(os.path.expanduser("~"), "Desktop", "check", ".kardelen_cache.pkl")
                import pickle
                cache_data = {
                    "birlesik": birlesik,
                    "sinoptik_sayisi": sinoptik_sayisi,
                    "metar_normal_sayisi": metar_normal_sayisi,
                    "speci_sayisi": speci_sayisi,
                    "ay": ay,
                    "yil": yil
                }
                with open(cache_path, 'wb') as f:
                    pickle.dump(cache_data, f)
                print("Analiz baÅŸarÄ±yla Ã¶nbelleÄŸe kaydedildi.")
            except Exception as ce:
                print(f"Ã–nbellek kaydetme hatasÄ±: {ce}")

            safe_after(0, lambda: arayuzde_goster(birlesik, hatali_kayitlar, sinoptik_sayisi, metar_normal_sayisi, speci_sayisi, ay, yil))
            # ------------------------------------------------

            if iptal_istendi: raise InterruptedError("Ä°Ålem kullanÄ±cÄ± tarafÃ¼ndan iptal edildi.")
            # 3. Rapor Kaydetme
            islenen_dosyalar = {
                "sinoptik": os.path.basename(sin_yolu),
                "metar": os.path.basename(metar_yolu)
            }
            cikti_yolu = dm3.raporu_excel_olarak_kaydet(birlesik, yil, ay, okuma_raporu, hedef_klasor, islenen_dosyalar)

            # --- YENÄ°: Ä°ÅLEMÄ° BÄ°TEN DOSYALARI ARÅÄ°VLE ---
            final_message = f"Ä°Ålem TamamlandÄ±!\nSonuÃ§lar ekrana yansÄ±tÄ±ldÄ±.\n(Yedek Excel: {cikti_yolu})"
            try:
                arsiv_klasoru = os.path.join(hedef_klasor, "Arsiv")
                if not os.path.exists(arsiv_klasoru):
                    os.makedirs(arsiv_klasoru)

                aylik_arsiv_klasoru = os.path.join(arsiv_klasoru, f"{yil}_{ay:02d}")
                if not os.path.exists(aylik_arsiv_klasoru):
                    os.makedirs(aylik_arsiv_klasoru)

                print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
                print(f"{Colors.OKBLUE}OluÅŸturulan rapor '{os.path.basename(aylik_arsiv_klasoru)}' klasÃ¶rÃ¼ne arÅŸivleniyor...{Colors.ENDC}")
                for f_path in [cikti_yolu]:
                    if os.path.exists(f_path):
                        base_name = os.path.basename(f_path)
                        dest_path = os.path.join(aylik_arsiv_klasoru, base_name)
                        
                        if os.path.exists(dest_path):
                            name, ext = os.path.splitext(base_name)
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            dest_path = os.path.join(aylik_arsiv_klasoru, f"{name}_{timestamp}{ext}")
                            
                        shutil.move(f_path, dest_path)
                        print(f" - {Colors.OKGREEN}{os.path.basename(dest_path)} taÄ°ÅndÃ¼.{Colors.ENDC}")
                final_message = f"Ä°Ålem TamamlandÄ±!\nSonuÃ§lar ekrana yansÄ±tÄ±ldÄ±.\n\nRapor dosyasÄ± '{os.path.basename(aylik_arsiv_klasoru)}' klasÃ¶rÃ¼ne arÅŸivlendi."
            except Exception as e:
                logging.error(f"ArÅŸivleme hatasÄ±: {e}", exc_info=True)
                logging_handler.flush()  # ArÅŸivleme hatasÄ±nÅŸ disk'e yaz
                print(f"{Colors.FAIL}ARÅÄ°VLEME HATASI: {e}{Colors.ENDC}")
                traceback.print_exc()
                final_message = f"Ä°Ålem TamamlandÄ±!\n(Yedek Excel: {cikti_yolu})\n\nUYARI: Dosyalar arÅŸivlenemedi!"

            safe_showinfo("BaÅŸarÄ±lÄ±", final_message)
        except Exception as e:
            if isinstance(e, InterruptedError):
                logging.info("Ä°Ålem kullanÄ±cÄ± tarafÃ¼ndan iptal edildi.")
                safe_showinfo("Ä°ptal", "Ä°Ålem iptal edildi.")
                print(f"\n{Colors.WARNING}Ä°Ålem kullanÄ±cÄ± tarafÃ¼ndan iptal edildi!{Colors.ENDC}")
            else:
                logging.error("Ä°Ålem sÄ±rasÄ±nda hata oluÅŸtu", exc_info=True)
                logging_handler.flush()
                print("\n--- DETAYLI HATA RAPORU ---")
                traceback.print_exc()
                safe_showerror("Hata", f"Bir hata oluÅŸtu:\n{e}")
        finally:
            # --- UI Geri Bildirimini SonlandÄ±r ---
            if not console_mode:
                try:
                    def finalize_ui():
                        if btn_run: btn_run.config(state=tk.NORMAL, text=get_button_text())
                        if btn_cancel: btn_cancel.config(state=tk.DISABLED)
                        if lbl_status: lbl_status.config(text="HazÃ¼r")
                        if root: root.config(cursor="")
                        try:
                            if 'progress_win' in globals() and progress_win and progress_win.winfo_exists():
                                progress_win.grab_release()
                                progress_win.destroy()
                        except:
                            pass
                    safe_after(0, finalize_ui)
                except Exception:
                    pass

    if run_async and not console_mode:
        threading.Thread(target=lambda: islem_yurut(load_from_cache, df_sin_param, df_metar_param, override_yil, override_ay, custom_title), daemon=True).start()
    else:
        islem_yurut(load_from_cache, df_sin_param, df_metar_param, override_yil, override_ay, custom_title)

def arayuz_arka_plan_tetikleyici(df_sin, df_metar, yil, ay, ist_isim, baslik):
    """Otomatik analizden (timer) gelen veriyi UI'da Ã¼alÄ°ÅtÃ¼rmak iÃ§in."""
    if console_mode: return
    # UI'yi sÄ±fÄ±rlayÃ¼p iÅŸlemi baÃ¼lat
    btn_run.config(state=tk.DISABLED, text="Oto Analiz Ã¼alÃ¼Ã¼yor...")
    if btn_cancel: btn_cancel.config(state=tk.NORMAL)
    lbl_status.config(text=baslik)
    aylik_rapor_olustur(run_async=True, load_from_cache=False, df_sin_param=df_sin, df_metar_param=df_metar, override_yil=yil, override_ay=ay, custom_title=baslik)

def aylik_rapor_olustur_inject_mode():
    global INJECT_SIN, INJECT_MET, INJECT_Y, INJECT_A
    aylik_rapor_olustur(run_async=False, load_from_cache=False, df_sin_param=INJECT_SIN, df_metar_param=INJECT_MET, override_yil=INJECT_Y, override_ay=INJECT_A, custom_title="GÃœNCEL SÄ°NOPTÄ°K ANALÄ°Z")

def aylik_rapor_olustur_html_icin(df_sin, df_metar, yil, ay, title):
    # Backward compatibility for earlier logic
    aylik_rapor_olustur(run_async=False, load_from_cache=False, df_sin_param=df_sin, df_metar_param=df_metar, override_yil=yil, override_ay=ay, custom_title=title)




if not console_mode:
    root = tk.Tk()
    root.title("SÄ°NOPTÄ°K VERÄ° DENETLEME")
    root.geometry("500x360")
    root.geometry("500x420")
    root.geometry("500x500")
    root.configure(bg="#F8F9FA")
    
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
        
    style.configure("TNotebook", background="#F8F9FA", borderwidth=0)
    style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=[15, 8], background="#E9ECEF", foreground="#495057", borderwidth=0)
    style.map("TNotebook.Tab", background=[('selected', '#FFFFFF')], foreground=[('selected', '#0066CC')])
    
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#343A40", foreground="white", borderwidth=0, padding=8)
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, background="#FFFFFF", fieldbackground="#FFFFFF", borderwidth=0)
    style.map("Treeview", background=[('selected', '#0066CC')], foreground=[('selected', 'white')])

    main_frame = tk.Frame(root, padx=35, pady=30, bg="#F8F9FA")
    main_frame.pack(expand=True, fill="both")
    
    lbl_title = tk.Label(main_frame, text="SÄ°NOPTÄ°K VERÄ° DENETLEME", font=("Segoe UI", 16, "bold"), bg="#F8F9FA", fg="#212529")
    lbl_title.pack(pady=(0, 20))

    btn_run = tk.Button(main_frame, text=get_button_text(), command=aylik_rapor_olustur, font=("Segoe UI", 12, "bold"), bg="#0066CC", fg="white", activebackground="#0052A3", activeforeground="white", height=2, cursor="hand2", relief="flat", borderwidth=0)
    btn_run.pack(expand=True, fill="both", pady=(0, 10))
    
    def iptal_et():
        global iptal_istendi
        iptal_istendi = True
        if lbl_status: lbl_status.config(text="Ä°Ålem durduruluyor, lÃ¼tfen bekleyin...")
        if btn_cancel: btn_cancel.config(state=tk.DISABLED)

    def guncel_canli_analiz_baslat():
        def arkaplan():
            try:
                import mgm_monitor.config as cfg
                import os
                config = cfg.ConfigLoader(os.path.join(os.path.dirname(__file__), "mgm_monitor", "config"))
                stations = config.get_enabled_stations()
                ist_kodu = 17244
                if stations:
                    bulundu = False
                    for s in stations:
                        if str(s.get('id', '')) == '17244':
                            ist_kodu = 17244
                            bulundu = True
                            break
                    if not bulundu:
                        ist_kodu = int(stations[0]['id'])

                
                import datetime
                now = datetime.datetime.now()
                # Run for current month up to now
                b = datetime.datetime(now.year, now.month, 1)
                bt = now
                
                def ui_cb(progress, msg):
                    def update_ui(p=progress, m=msg):
                        lbl_status.config(text=m)
                        try: btn_live.config(text=f"ÅŸ %{int(p)} - {m}")
                        except: pass
                    safe_after(0, update_ui)
                
                safe_after(0, lambda: btn_run.config(state=tk.DISABLED))
                safe_after(0, lambda: btn_cancel.config(state=tk.NORMAL))
                safe_after(0, lambda: btn_live.config(state=tk.DISABLED))
                ui_cb(0, "GÃ¼ncel CanlÅŸ Analiz BaÅŸlatÃ¼lÃ¼yor...")
                
                import canli_analiz
                df_sin, df_metar, y, a, isim = canli_analiz.manuel_analiz(ist_kodu, b, bt, ui_cb)
                
                global iptal_istendi, INJECT_SIN, INJECT_MET, INJECT_Y, INJECT_A
                iptal_istendi = False
                INJECT_SIN = df_sin
                INJECT_MET = df_metar
                INJECT_Y = y
                INJECT_A = a
                
                ui_cb(100, "HTML verileri iÃ¼lendi, Excel oluÅŸturuluyor...")
                
                import threading
                threading.Thread(target=aylik_rapor_olustur_inject_mode, daemon=True).start()
                
            except Exception as e:
                safe_after(0, lambda err=str(e): messagebox.showerror("Hata", f"CanlÅŸ analiz hatasÄ±: {err}"))
                safe_after(0, lambda: lbl_status.config(text="Hata oluÅŸtu."))
            finally:
                safe_after(0, lambda: btn_run.config(state=tk.NORMAL))
                safe_after(0, lambda: btn_cancel.config(state=tk.DISABLED))
                safe_after(0, lambda: btn_live.config(text="âš¡ GÃœNCEL SÄ°NOPTÄ°K ANALÄ°Z YÃœKLE", state=tk.NORMAL))

        import threading
        threading.Thread(target=arkaplan, daemon=True).start()

    btn_cancel = tk.Button(main_frame, text="Ä°ÅLEMÄ° DURDUR / Ä°PTAL ET", command=iptal_et, state=tk.DISABLED, font=("Segoe UI", 10, "bold"), bg="#D32F2F", fg="white", activebackground="#B71C1C", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_cancel.pack(fill="x", pady=(0, 8))
    btn_load_cache = tk.Button(main_frame, text="âš¡ SON ANALÄ°ZÄ° YÃœKLE", command=lambda: aylik_rapor_olustur(run_async=True, load_from_cache=True), font=("Segoe UI", 10, "bold"), bg="#009688", fg="white", activebackground="#00796B", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_load_cache.pack(fill="x", pady=(0, 8))
    
    live_frame = tk.Frame(main_frame, bg="#F8F9FA")
    live_frame.pack(fill="x", pady=(0, 8))
    
    btn_live = tk.Button(live_frame, text="âš¡ GÃœNCEL SÄ°NOPTÄ°K ANALÄ°Z YÃœKLE", command=guncel_canli_analiz_baslat, font=("Segoe UI", 10, "bold"), bg="#1E88E5", fg="white", activebackground="#1565C0", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_live.pack(side="left", expand=True, fill="x")
    
    oto_var = tk.BooleanVar(value=False)
    chk_oto = tk.Checkbutton(live_frame, text="Otomatik", variable=oto_var, font=("Segoe UI", 9, "bold"), bg="#F8F9FA", activebackground="#F8F9FA", cursor="hand2")
    chk_oto.pack(side="right", padx=(5, 0))

    def ayarlar_penceresi_ac():
        ayarlar_pop = tk.Toplevel(root)
        ayarlar_pop.title("âš™ Ayarlar")
        ayarlar_pop.geometry("400x300")
        ayarlar_pop.configure(bg="#F8F9FA")
        
        ayarlar = ayarlari_yukle()
        
        tk.Label(ayarlar_pop, text="Otomatik Analiz DakikasÄ±:", bg="#F8F9FA", font=("Segoe UI", 10)).pack(pady=(10,0))
        dakika_var = tk.StringVar(value=str(ayarlar.get("oto_dakika", 55)))
        ttk.Entry(ayarlar_pop, textvariable=dakika_var, font=("Segoe UI", 10), justify="center").pack()
        
        alarm_var = tk.BooleanVar(value=ayarlar.get("alarm_aktif", False))
        tk.Checkbutton(ayarlar_pop, text="Yeni hata Ä°Åkarsa alarm Ã¼al", variable=alarm_var, font=("Segoe UI", 10), bg="#F8F9FA", activebackground="#F8F9FA").pack(pady=5)
        
        arkaplan_var = tk.BooleanVar(value=ayarlar.get("arka_planda_calis", False))
        tk.Checkbutton(ayarlar_pop, text="Arka planda Ã¼alÄ°Å", variable=arkaplan_var, font=("Segoe UI", 10), bg="#F8F9FA", activebackground="#F8F9FA").pack(pady=5)
        
        web_var = tk.BooleanVar(value=ayarlar.get("web_server_aktif", False))
        tk.Checkbutton(ayarlar_pop, text="Web Server Aktif", variable=web_var, font=("Segoe UI", 10), bg="#F8F9FA", activebackground="#F8F9FA").pack(pady=5)
        
        def kaydet():
            ayarlar["oto_dakika"] = int(dakika_var.get())
            ayarlar["alarm_aktif"] = alarm_var.get()
            ayarlar["arka_planda_calis"] = arkaplan_var.get()
            ayarlar["web_server_aktif"] = web_var.get()
            ayarlari_kaydet(ayarlar)
            ayarlar_pop.destroy()
            
        tk.Button(ayarlar_pop, text="KAYDET", command=kaydet, bg="#28A745", fg="white", font=("Segoe UI", 10, "bold"), pady=5).pack(pady=20, fill="x", padx=40)

    btn_ayarlar = tk.Button(main_frame, text="âš™ AYARLAR", command=ayarlar_penceresi_ac, font=("Segoe UI", 10, "bold"), bg="#6C757D", fg="white", activebackground="#5A6268", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_ayarlar.pack(fill="x", pady=(0, 8))

    web_process = None
    
    def oto_tetikleyici_dongu():
        global web_process
        import time
        import datetime
        import subprocess
        import os
        
        son_calisma_dakikasi = -1
        while True:
            time.sleep(5)
            try:
                ayarlar = ayarlari_yukle()
                
                # Web Server YÃ¼netimi
                web_aktif = ayarlar.get("web_server_aktif", False)
                if web_aktif:
                    if web_process is None or web_process.poll() is not None:
                        try:
                            # Start Flask silently
                            si = subprocess.STARTUPINFO()
                            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            web_process = subprocess.Popen(
                                ["python", "web_server.py"], 
                                cwd=os.path.dirname(os.path.abspath(__file__)),
                                startupinfo=si,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                        except: pass
                else:
                    if web_process is not None and web_process.poll() is None:
                        web_process.terminate()
                        web_process = None

                # Otomatik Analiz Tetikleyici
                if not oto_var.get():
                    continue
                    
                hedef_dk = int(ayarlar.get("oto_dakika", 55))
                now = datetime.datetime.now()
                
                if now.minute == hedef_dk and son_calisma_dakikasi != hedef_dk:
                    son_calisma_dakikasi = hedef_dk
                    if btn_run['state'] == tk.NORMAL:
                        safe_after(0, guncel_canli_analiz_baslat)
                
                if now.minute != hedef_dk:
                    son_calisma_dakikasi = -1
            except Exception as e:
                pass

    import threading
    threading.Thread(target=oto_tetikleyici_dongu, daemon=True).start()


    def kurallari_goster():
        kural_pop = tk.Toplevel(root)
        kural_pop.title("Sinoptik Veri Denetleme KurallarÄ±")
        kural_pop.geometry("950x650")
        kural_pop.configure(bg="#F8F9FA")
        
        lbl = tk.Label(kural_pop, text="Sistemde Aktif Olan Kurallar", font=("Segoe UI", 14, "bold"), bg="#F8F9FA", fg="#212529")
        lbl.pack(pady=(15, 10))
        
        search_frame = tk.Frame(kural_pop, bg="#F8F9FA")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        tk.Label(search_frame, text="âš¡ Kural Ara:", font=("Segoe UI", 11, "bold"), bg="#F8F9FA", fg="#495057").pack(side="left", padx=(0, 10))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, font=("Segoe UI", 11), width=40)
        search_entry.pack(side="left")
        
        columns = ("Kural Kodu", "AÄ°Åklama")
        tree = ttk.Treeview(kural_pop, columns=columns, show="headings", style="Treeview")
        tree.heading("Kural Kodu", text="Kural Kodu")
        tree.heading("AÄ°Åklama", text="Kural AÄ°ÅklamasÃ¼")
        
        tree.column("Kural Kodu", width=150, anchor="center")
        tree.column("AÄ°Åklama", width=750, anchor="w")
        
        yscroll = ttk.Scrollbar(kural_pop, orient="vertical", command=tree.yview)
        yscroll.pack(side="right", fill="y")
        tree.configure(yscrollcommand=yscroll.set)
        tree.pack(side="left", fill="both", expand=True, padx=20, pady=(0, 20))
        
        def sort_key(k):
            m = re.search(r'\d+', k)
            if k.startswith('h') and m: return (0, int(m.group()))
            elif k.startswith('VAL'): return (1, k)
            else: return (2, k)
            
        def filter_kurallar(*args):
            q = search_var.get().lower()
            tree.delete(*tree.get_children())
            for kod in sorted(kurallar.HATA_SOZLUGU.keys(), key=sort_key):
                acik = kurallar.HATA_SOZLUGU[kod]
                if q in kod.lower() or q in acik.lower():
                    tree.insert("", tk.END, values=(kod, acik))
                    
        search_var.trace_add("write", filter_kurallar)
        filter_kurallar() # Ã¼lk yÃ¼kleme iÃ§in Ã¼aÄ°År
            
    btn_kurallar = tk.Button(main_frame, text="KURALLARI GÃ–STER", command=kurallari_goster, font=("Segoe UI", 10, "bold"), bg="#107C41", fg="white", activebackground="#0C5D31", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_kurallar.pack(fill="x", pady=(0, 8))

    def dosyalari_indir_ac():
        import datetime
        simdi = datetime.datetime.now()
        v_ay = simdi.month
        v_yil = simdi.year

        indirme_yili = simpledialog.askinteger('Dosya AdÄ±nÄ±n YÄ±lÄ±', 'Kardelen\'den dosyalarÄ± indirirken kaydedeceÃ¼iniz dosyanÃ¼n YILINI giriniz:\n(Ã–rn: 2026)', initialvalue=v_yil, minvalue=2000, maxvalue=2050, parent=root)
        if not indirme_yili: return
        indirme_ayi = simpledialog.askinteger('Dosya AdÄ±nÄ±n AyÄ±', f'Ä°ndireceÄŸiniz dosyalarÄ± {indirme_yili} yÄ±lÄ± iÃ§in kaydederken,\ndosya adÄ±nda kullanacaÄ°ÅnÃ¼z AYI giriniz:\n(Ã–rn: 1)', initialvalue=v_ay, minvalue=1, maxvalue=12, parent=root)
        if not indirme_ayi: return

        messagebox.showinfo('Dosya Ä°simlendirme', f'Kardelen aÄ°ÅldÄ±ÅŸÄ±nda dosyalarÄ± tam olarak ÅŸu isimlerle indirmelisiniz:\n\nSÄ°NOPTÄ°K: {indirme_ayi:02d}{indirme_yili}-sinoptik.xls\nMETAR: {indirme_ayi:02d}{indirme_yili}-metar.xls', parent=root)

        dosya_oneki = f"{indirme_ayi:02d}{indirme_yili}-"

        btn_indir.config(state="disabled", text="âš¡ TARAYICI AÃ‡ILIYOR...")
        if btn_cancel: btn_cancel.config(state=tk.NORMAL)
        root.update()
        
        baslangic_zamani = time.time()

        try:
            ist_kodu_cache = ent_ist.get().strip()
        except Exception:
            ist_kodu_cache = "17244"

        def arkaplanda_tarayici_ac():
            try:
                # DÄ°NAMÄ°K YOL: ProgramÄ±n her bilgisayarda Ã¼alÄ°Åabilmesi iÃ§in sabit yol yerine kullanÄ±cÄ±nÃ¼n masaÃœstÃ¼nÅŸ otomatik bul.
                hedef_klasor = HEDEF_KLASOR
                if not os.path.exists(hedef_klasor):
                    os.makedirs(hedef_klasor)
                    
                os.startfile(hedef_klasor)
                
                url = "http://kardelen.mgm.gov.tr/BultenGenel/Default.aspx"
                
                # SÄ°STEMÄ°N VARSAYILAN TARAYICISINI ANINDA AÃ‡ (SELENIUM Ä°PTAL EDÄ°LDÄ°)
                import webbrowser
                webbrowser.open(url)
                
                # KullanÄ±cÄ± kolayca yapÄ°ÅtÃ¼rabilsin diye istasyon kodunu panoya kopyala
                if ist_kodu_cache:
                    try:
                        root.clipboard_clear()
                        root.clipboard_append(ist_kodu_cache)
                        root.update()
                    except Exception: pass
                
                # TarayÄ±cÄ± kendi varsayÄ±lan klasÃ¶rÃ¼ne (genelde Downloads) indireceÄŸi iÃ§in o klasÃ¶rÅŸ izliyoruz
                indirilenler_klasoru = os.path.join(os.path.expanduser("~"), "Downloads")
                
                def oto_tasima_ve_bekle():
                    zaman_asimi = 600
                    baslangic_z = time.time()
                    
                    safe_after(0, lambda: lbl_status.config(text="TarayÄ±cÄ± aÄ°ÅldÃ¼. (Otomatik taÄ°Åma devrede)..."))
                    safe_after(0, lambda: btn_indir.config(text="Ä°NDÄ°RME BEKLENÄ°YOR...", state="disabled"))
                    
                    while time.time() - baslangic_z < zaman_asimi:
                        if iptal_istendi:
                            break
                            
                        # 1. KullanÄ±cÄ±nÄ±n Ä°ndirilenler klasÃ¶rÃ¼ne dÄ°Åen yeni Kardelen dosyalarÄ±nÄ± otomatik 'check' klasÃ¶rÃ¼ne taÄ°Å
                        try:
                            if os.path.exists(indirilenler_klasoru):
                                for f in os.listdir(indirilenler_klasoru):
                                    if f.endswith('.crdownload') or f.endswith('.tmp') or f.endswith('.part'):
                                        continue
                                    tam_yol = os.path.join(indirilenler_klasoru, f)
                                    if os.path.isfile(tam_yol) and f.lower().endswith(('.xls', '.xlsx', '.csv', '.html')):
                                        # Sadece butona basÄ±ldÄ±ktan sonra indirilen dosyalarÄ± taÄ°Å
                                        try:
                                            if max(os.path.getmtime(tam_yol), os.path.getctime(tam_yol)) >= baslangic_z:
                                                yeni_dosya_adi = f
                                                f_lower = f.lower()
                                                if "sintum" in f_lower:
                                                    yeni_dosya_adi = f"{dosya_oneki}SinTum{os.path.splitext(f)[1]}"
                                                elif "metartum" in f_lower:
                                                    yeni_dosya_adi = f"{dosya_oneki}MetarTum{os.path.splitext(f)[1]}"
                                                hedef_yol = os.path.join(hedef_klasor, yeni_dosya_adi)
                                                import shutil
                                                shutil.move(tam_yol, hedef_yol)
                                        except Exception: pass
                        except Exception: pass
                        
                        # 2. Check klasÃ¶rÃ¼ndeki dosyalarÄ± kontrol et (SÄ°NOPTÄ°K ve METAR ikisi de geldi mi?)
                        try:
                            dosyalar = os.listdir(hedef_klasor)
                            devam_eden_var = any(f.endswith('.crdownload') or f.endswith('.tmp') for f in dosyalar)
                            
                            if not devam_eden_var:
                                sin_yeni = met_yeni = False
                                for f in dosyalar:
                                    tam_yol = os.path.join(hedef_klasor, f)
                                    if not os.path.isfile(tam_yol): continue
                                    
                                    try:
                                        yeni_mi = max(os.path.getmtime(tam_yol), os.path.getctime(tam_yol)) >= baslangic_z
                                    except Exception:
                                        yeni_mi = False
                                        
                                    if yeni_mi and f.lower().endswith(('.xls', '.xlsx', '.csv', '.html')):
                                        f_upper = f.upper()
                                        if "SIN" in f_upper or "SÄ°N" in f_upper: sin_yeni = True
                                        elif "METAR" in f_upper: met_yeni = True
                                        
                                if sin_yeni and met_yeni:
                                    time.sleep(1.5)
                                    def sor_ve_baslat():
                                        btn_indir.config(state="normal", text="âš¡ DOSYALARI Ä°NDÄ°R")
                                        if btn_cancel: btn_cancel.config(state=tk.DISABLED)
                                        lbl_status.config(text="HazÃ¼r")
                                        cevap = messagebox.askyesno("Ã¼ndirme TamamlandÄ±", "SÄ°NOPTÄ°K ve METAR dosyalarÄ± baÅŸarÄ±yla indirildi!\n\nRaporlama iÅŸlemi hemen baÅŸlatÄ±lsÄ±n mÃ¼", parent=root)
                                        if cevap:
                                            sadece_en_yeni_dosyalari_tut()
                                            aylik_rapor_olustur(run_async=True)
                                    safe_after(0, sor_ve_baslat)
                                    return
                        except Exception: pass
                        time.sleep(2)
                        
                    def reset_ui():
                        btn_indir.config(state="normal", text="âš¡ DOSYALARI Ä°NDÄ°R")
                        if btn_cancel: btn_cancel.config(state=tk.DISABLED)
                        lbl_status.config(text="HazÃ¼r")
                        if not iptal_istendi:
                            messagebox.showwarning("Zaman AÄ°ÅmÅŸ / Bilgi", "Ã¼ndirme otomatik algÄ±lanamadÄ± veya zaman aÄ°ÅmÃ¼na uÄŸradÄ±.\nDosyalar indiÃ§inden eminseniz rapor oluÅŸturmayÄ± manuel baÅŸlatabilirsiniz.", parent=root)
                    safe_after(0, reset_ui)
                
                threading.Thread(target=oto_tasima_ve_bekle, daemon=True).start()
                    
            except Exception as e:
                # Capture 'e' in closure by using default argument
                def show_err(err_msg=str(e)):
                    messagebox.showerror("Hata", f"Ä°Ålem sÄ±rasÄ±nda hata oluÅŸtu:\n{err_msg}")
                    btn_indir.config(state="normal", text="âš¡ DOSYALARI Ä°NDÄ°R")
                    if btn_cancel: btn_cancel.config(state=tk.DISABLED)
                    safe_after(0, show_err)

        # Selenium baÅŸlatma iÅŸlemini arka planda (ayrÄ± thread) Ã¼alÄ°ÅtÃ¼r
        threading.Thread(target=arkaplanda_tarayici_ac, daemon=True).start()

    btn_indir = tk.Button(main_frame, text="âš¡ DOSYALARI Ä°NDÄ°R", command=dosyalari_indir_ac, font=("Segoe UI", 10, "bold"), bg="#673AB7", fg="white", activebackground="#512DA8", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_indir.pack(fill="x", pady=(0, 8))

    def canli_analiz_penceresi_ac():
        canli_pop = tk.Toplevel(root)
        canli_pop.title("CanlÅŸ HTML Veri Analizi")
        canli_pop.geometry("600x500")
        canli_pop.configure(bg="#F8F9FA")
        
        cfg = canli_analiz.get_config()
        istasyonlar = cfg.get_enabled_stations()
        ist_listesi = [f"{s['id']} - {s['name']}" for s in istasyonlar]
        
        lbl_ist = tk.Label(canli_pop, text="Ã¼stasyon (Manuel SeÃ§im):", bg="#F8F9FA", font=("Segoe UI", 10, "bold"))
        lbl_ist.pack(pady=(15, 2))
        cmb_ist = ttk.Combobox(canli_pop, values=ist_listesi, font=("Segoe UI", 11), state="readonly")
        if ist_listesi:
            # LTAN 17244 varsayÄ±lan seÃ§ilsin
            default_idx = next((i for i, v in enumerate(ist_listesi) if "17244" in v), 0)
            cmb_ist.current(default_idx)
        cmb_ist.pack()
        
        import datetime
        simdi = datetime.datetime.now()
        dun = simdi - datetime.timedelta(days=1)
        
        lbl_tarih = tk.Label(canli_pop, text="Tarih Aralâš™ (Sadece Manuel Analiz Ä°Åin):", bg="#F8F9FA", font=("Segoe UI", 10, "bold"))
        lbl_tarih.pack(pady=(15, 2))
        
        frame_tarih = tk.Frame(canli_pop, bg="#F8F9FA")
        frame_tarih.pack()
        
        try:
            if DateEntry is None:
                raise ImportError("tkcalendar kÃ¼tÃ¼phanesi eksik!")
            cal_bas = DateEntry(frame_tarih, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
            cal_bas.set_date(dun)
            cal_bas.pack(side="left", padx=5)
            tk.Label(frame_tarih, text="-", bg="#F8F9FA").pack(side="left")
            cal_bit = DateEntry(frame_tarih, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
            cal_bit.set_date(simdi)
            cal_bit.pack(side="left", padx=5)
        except Exception:
            tk.Label(frame_tarih, text="tkcalendar eksik! Terminalde Ã¼alÄ°ÅtÃ¼rÃ¼n: python -m pip install tkcalendar", fg="red", bg="#F8F9FA").pack()
            
            # Fallback olarak basit metin kutularÅŸ kullan
            cal_bas = tk.Entry(frame_tarih, width=12, font=("Segoe UI", 10))
            cal_bas.insert(0, dun.strftime("%d.%m.%Y"))
            cal_bas.pack(side="left", padx=5)
            tk.Label(frame_tarih, text="-", bg="#F8F9FA").pack(side="left")
            cal_bit = tk.Entry(frame_tarih, width=12, font=("Segoe UI", 10))
            cal_bit.insert(0, simdi.strftime("%d.%m.%Y"))
            cal_bit.pack(side="left", padx=5)
            
            # Sahte get_date fonksiyonlarÃ¼nÅŸ ekle ki aÃ¼aÄ°Ådaki mantÃ¼k bozulmasÃ¼n
            def fake_get_date(entry_widget):
                try:
                    return datetime.datetime.strptime(entry_widget.get(), "%d.%m.%Y").date()
                except:
                    return datetime.datetime.now().date()
            cal_bas.get_date = lambda: fake_get_date(cal_bas)
            cal_bit.get_date = lambda: fake_get_date(cal_bit)
            
        lbl_durum = tk.Label(canli_pop, text="HazÃ¼r", bg="#E9ECEF", font=("Segoe UI", 9))
        lbl_durum.pack(side="bottom", fill="x", pady=10)
        
        def update_cb(pct, msg):
            safe_after(0, lambda: lbl_durum.config(text=f"%{pct} - {msg}"))
            
        def islem_bitirici(df_sin, df_metar, y, a, isim, title=""):
            # islem_yurut iÃ§indeki df_sin_param ve df_metar_param ile Ã¼alÄ°ÅmasÃ¼nÅŸ saÄŸlayan hook
            safe_after(0, lambda: lbl_durum.config(text="UI'ye aktarÃ¼lÃ¼yor..."))
            
            # âš¡ iÃ§e import sorunu ve scope kirliliÃ§ini Ã¶nlemek iÃ§in,
            # main root Ã¼zerinden mevcut aylik_rapor_olustur yapÄ±sÃ¼na inject ediyoruz.
            global iptal_istendi
            iptal_istendi = False
            
            if btn_run: btn_run.config(state=tk.DISABLED, text="CanlÅŸ Analiz...")
            if btn_cancel: btn_cancel.config(state=tk.NORMAL)
            if lbl_status: lbl_status.config(text="HTML verileri iÅŸleniyor...")
            
            # AylÃ¼k Rapor iÃ§indeki iÅŸ fonksiyon 'islem_yurut' parametre alacak ÅŸekilde deÃ¼iÃ¼tirildi
            # Bunu doÄŸrudan Ã¼aÄ°Årmak iÃ§in bir trick kullanÃ¼yoruz:
            def arka_plan_islem():
                try:
                    # Yeni bir Ã¼evre (scope) yaratÃ¼p inject etmek yerine, fonksiyonu override_yil ile Ã¼aÄ°ÅrÃ¼yoruz
                    # Ancak `islem_yurut` iÅŸ iÃ§e (nested) bir fonksiyon.
                    # Bu nedenle arayuz.py iÃ§erisine genel bir df_inject globali koyup oradan okutabiliriz.
                    # YÃ¼NTEM 2: df_sin ve df_metar'ÅŸ global_inject deÃ¼iÃ¼kenine yazÃ¼p aylik_rapor_olustur'u tetiklemek
                    pass
                except Exception as e:
                    print(e)
            
            # Temiz Ä°ÅzÃ¼m: Dosyaya yazÃ¼p (geÃ¼ici) mevcut sistemi hiÃ§ deÃ¼iÃ¼tirmeden tetiklemek (Yedek Plan)
            # AMA En iyisi: `islem_yurut`'ÅŸ dÄ°ÅarÅŸ Ä°ÅkarmaktÃ¼r. Ancak dosya Ã§ok bÃ¼yÃ¼k.
            # Ã¼imdilik global bir deÃ¼iÃ¼ken (INJECT_SIND, INJECT_METD) ile aktaralÃ¼m.
            global INJECT_SIN, INJECT_MET, INJECT_Y, INJECT_A
            INJECT_SIN = df_sin
            INJECT_MET = df_metar
            INJECT_Y = y
            INJECT_A = a
            
            threading.Thread(target=aylik_rapor_olustur_inject_mode, daemon=True).start()

        def manuel_baslat():
            secim = cmb_ist.get().split("-")[0].strip()
            b = cal_bas.get_date()
            bt = cal_bit.get_date()
            
            def arkaplan():
                try:
                    # df_sin, df_metar = ...
                    df_sin, df_metar, y, a, isim = canli_analiz.manuel_analiz(
                        int(secim),
                        datetime.datetime.combine(b, datetime.datetime.min.time()),
                        datetime.datetime.combine(bt, datetime.datetime.max.time()),
                        update_cb
                    )
                    islem_bitirici(df_sin, df_metar, y, a, isim)
                except Exception as e:
                    safe_after(0, lambda err=str(e): messagebox.showerror("Hata", err, parent=canli_pop))
                    update_cb(0, "Hata oluÅŸtu.")
            threading.Thread(target=arkaplan, daemon=True).start()
            
        btn_man = tk.Button(canli_pop, text="MANUEL ANALÄ°ZÄ° BAÃ‡LAT", command=manuel_baslat, bg="#0066CC", fg="white", font=("Segoe UI", 11, "bold"), pady=8)
        btn_man.pack(fill="x", padx=20, pady=20)
        
        lbl_oto = tk.Label(canli_pop, text="Otomatik Analiz (LTAN 17244 | Her Saat :55):", bg="#F8F9FA", font=("Segoe UI", 10, "bold"))
        lbl_oto.pack(pady=(15, 2))
        
        def durum_cb(msg):
            safe_after(0, lambda: lbl_durum.config(text=msg))
            
        def oto_baslat():
            # LTAN 17244 iÃ§in otomatik baÃ¼lat
            canli_analiz.otomatik_analiz_baslat(17244, islem_bitirici, durum_cb)
            btn_oto_b.config(state="disabled")
            btn_oto_d.config(state="normal")
            
        def oto_durdur():
            canli_analiz.otomatik_analiz_durdur(durum_cb)
            btn_oto_b.config(state="normal")
            btn_oto_d.config(state="disabled")
            
        f_oto = tk.Frame(canli_pop, bg="#F8F9FA")
        f_oto.pack(fill="x", padx=20)
        btn_oto_b = tk.Button(f_oto, text="OTOMATÄ°K BAÃ‡LAT", command=oto_baslat, bg="#107C41", fg="white", font=("Segoe UI", 10, "bold"), pady=5)
        btn_oto_b.pack(side="left", expand=True, fill="x", padx=5)
        btn_oto_d = tk.Button(f_oto, text="DURDUR", command=oto_durdur, state="disabled", bg="#D32F2F", fg="white", font=("Segoe UI", 10, "bold"), pady=5)
        btn_oto_d.pack(side="left", expand=True, fill="x", padx=5)
        
        if canli_analiz._OTO_ANALIZ_CALISIYOR:
            btn_oto_b.config(state="disabled")
            btn_oto_d.config(state="normal")
            lbl_durum.config(text="Oto Analiz Ã¼U AN AKTÃ¼F.")

    btn_canli = tk.Button(main_frame, text="âš¡ CANLI HTML ANALÄ°Z", command=canli_analiz_penceresi_ac, font=("Segoe UI", 10, "bold"), bg="#009688", fg="white", activebackground="#00796B", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_canli.pack(fill="x", pady=(0, 8))

    # ARÄ°ÅV SÃœTUNLARINI GÃœNCELLE butonu kaldÄ±rÄ±ldÄ±

    def loglari_goster():
        log_pop = tk.Toplevel(root)
        log_pop.title("Sistem LoglarÄ±")
        log_pop.geometry("850x600")
        log_pop.configure(bg="#F8F9FA")
        
        top_frame = tk.Frame(log_pop, bg="#F8F9FA")
        top_frame.pack(fill="x", padx=10, pady=10)
        
        txt_log = tk.Text(log_pop, font=("Consolas", 10), bg="#1E1E1E", fg="#00FF00", wrap="none")
        
        v_scroll = tk.Scrollbar(log_pop, orient="vertical", command=txt_log.yview)
        v_scroll.pack(side="right", fill="y")
        h_scroll = tk.Scrollbar(log_pop, orient="horizontal", command=txt_log.xview)
        h_scroll.pack(side="bottom", fill="x")
        
        txt_log.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        txt_log.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        
        def load_logs(filter_text=None):
            txt_log.config(state="normal")
            txt_log.delete("1.0", tk.END)
            try:
                with open(log_dosyasi, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if filter_text:
                        lines = [l for l in lines if filter_text in l]
                    txt_log.insert(tk.END, "".join(lines))
            except Exception as e:
                txt_log.insert(tk.END, f"Log dosyasÄ± okunamadÄ±: {e}")
            txt_log.see(tk.END)
            txt_log.config(state="disabled")

        tk.Button(top_frame, text="TÃ¼m LoglarÄ± GÃ¼ster", command=lambda: load_logs(), bg="#0066CC", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)
        tk.Button(top_frame, text="âš¡ SÃ¼tun EÅŸleÅŸmeleri", command=lambda: load_logs("EÅŸleÅŸen SÃ¼tunlar"), bg="#107C41", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)
        tk.Button(top_frame, text="HatalarÄ± Filtrele", command=lambda: load_logs("ERROR"), bg="#D32F2F", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)
        def loglari_temizle():
            try:
                import logging
                for handler in logging.root.handlers:
                    if hasattr(handler, 'stream') and hasattr(handler, 'baseFilename'):
                        handler.stream.seek(0)
                        handler.stream.truncate(0)
                load_logs()
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Hata", f"Loglar temizlenemedi: {e}", parent=log_win)
                
        tk.Button(top_frame, text="âš¡ TEMÄ°ZLE", command=loglari_temizle, bg="#FF9800", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=5).pack(side="left", padx=5)
        
        load_logs()

    btn_loglar = tk.Button(main_frame, text="SÄ°STEM LOGLARINI GÃ–STER", command=loglari_goster, font=("Segoe UI", 10, "bold"), bg="#607D8B", fg="white", activebackground="#455A64", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_loglar.pack(fill="x", pady=(0, 8))

    def log_dosyasini_ac():
        try:
            if os.path.exists(log_dosyasi):
                os.startfile(log_dosyasi) # Windows'un varsayÄ±lan uygulamasÄ±yla (Ã–rn: Not Defteri) aÃ§ar
            else:
                messagebox.showwarning("BulunamadÄ±", "Log dosyasÄ± henÃ¼z oluÅŸturulmamÄ°Å.", parent=root)
        except Exception as e:
            messagebox.showerror("Hata", f"Log dosyasÄ± aÄ°ÅlamadÃ¼:\n{e}", parent=root)
            
    btn_log_dosyasi = tk.Button(main_frame, text="âš¡ LOG DOSYASINI AÃ‡ (NOT DEFTERÄ°)", command=log_dosyasini_ac, font=("Segoe UI", 10, "bold"), bg="#546E7A", fg="white", activebackground="#37474F", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_log_dosyasi.pack(fill="x", pady=(0, 8))

    def manuel_temizlik_yap():
        clear_pycache_on_startup()
        cleanup_old_temp_files()
        
        temizlenen_arsiv = 0
        cevap = messagebox.askyesno("ArÅŸiv TemizliÃ§i", "Sistemin Ã–nbellek ve loglarÄ± temizlenecek.\n\nAyrÄ±ca 'check\\Arsiv' klasÃ¶rÃ¼ndeki TÃœM geÃ§miÅŸ Excel raporlarÄ± da kalÄ±cÄ± olarak silinsin mi?", parent=root)
        if cevap:
            arsiv_dir = ARSIV_KLASORU
            if os.path.exists(arsiv_dir):
                try:
                    for root_d, dirs, files in os.walk(arsiv_dir, topdown=False):
                        for f in files:
                            try:
                                os.remove(os.path.join(root_d, f))
                                temizlenen_arsiv += 1
                            except: pass
                        if root_d != arsiv_dir:
                            try: os.rmdir(root_d)
                            except: pass
                except Exception as e:
                    logging.error(f"ArÅŸiv temizleme hatasÄ±: {e}")
        
        mesaj = "Ã–nbellek (Cache), eski loglar ve gereksiz geÃ¼ici dosyalar baÅŸarÄ±yla temizlendi."
        if cevap:
            mesaj += f"\n\nSilinen geÃ§miÅŸ arÅŸiv dosyasÄ±: {temizlenen_arsiv} adet."
        messagebox.showinfo("Temizlik TamamlandÄ±", mesaj, parent=root)
        
    btn_temizle = tk.Button(main_frame, text="âš¡ SÄ°STEMÅŸ TEMÄ°ZLE (ARÄ°ÅV/LOG)", command=manuel_temizlik_yap, font=("Segoe UI", 10, "bold"), bg="#795548", fg="white", activebackground="#5D4037", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_temizle.pack(fill="x", pady=(0, 8))

    def dosya_icerigi_incele():
        dosya_yolu = filedialog.askopenfilename(
            title="Ä°ncelenecek Bozuk/Okunamayan DosyayÄ± SeÃ§in",
            filetypes=[("TÃ¼m Dosyalar", "*.*"), ("Excel/Metin", "*.xls *.xlsx *.csv *.html *.txt")]
        )
        if not dosya_yolu: return
        
        incele_pop = tk.Toplevel(root)
        incele_pop.title(f"Ham Dosya Ä°nceleme - {os.path.basename(dosya_yolu)}")
        incele_pop.geometry("850x600")
        incele_pop.configure(bg="#F8F9FA")
        
        top_frame = tk.Frame(incele_pop, bg="#F8F9FA")
        top_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(top_frame, text=f"Dosya Ham (Raw) Ä°ÅeriÃ§i:\n{dosya_yolu}", font=("Segoe UI", 10, "bold"), bg="#F8F9FA", fg="#D32F2F", justify="left").pack(side="left")
        
        txt_icerik = tk.Text(incele_pop, font=("Consolas", 10), bg="#1E1E1E", fg="#00FF00", wrap="none")
        v_scroll = tk.Scrollbar(incele_pop, orient="vertical", command=txt_icerik.yview)
        v_scroll.pack(side="right", fill="y")
        h_scroll = tk.Scrollbar(incele_pop, orient="horizontal", command=txt_icerik.xview)
        h_scroll.pack(side="bottom", fill="x")
        
        txt_icerik.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        txt_icerik.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        
        def load_content():
            try:
                dosya_boyutu = os.path.getsize(dosya_yolu)
                if dosya_boyutu == 0:
                    txt_icerik.insert(tk.END, "âš™ BU DOSYA TAMAMEN BOÅ (0 BYTE)!\n\nKardelen sistemi bu dosyayÄ± Ã¼retirken hata vermiÅŸ veya dosya eksik inmiÅŸ. Yeniden indirmeyi deneyin.")
                else:
                    txt_icerik.insert(tk.END, f"--- Dosya Boyutu: {dosya_boyutu / 1024:.2f} KB ---\n\n")
                    with open(dosya_yolu, 'r', encoding='utf-8', errors='ignore') as f:
                        satirlar = f.readlines()
                        if len(satirlar) > 1000:
                            icerik = "".join(satirlar[:1000]) + "\n\n... (DOSYA Ã¼OK UZUN OLDUÃ¼U Ã¼Ã¼N SADECE Ä°LK 1000 SATIR GÃ–STERÄ°LÄ°YOR) ..."
                        else:
                            icerik = "".join(satirlar)
                        
                        if icerik.strip(): txt_icerik.insert(tk.END, icerik)
                        else: txt_icerik.insert(tk.END, "Dosyada okunabilir metin verisi bulunamadÄ±.")
            except Exception as e:
                txt_icerik.insert(tk.END, f"Dosya okunurken hata oluÅŸtu:\n{e}")
            txt_icerik.config(state="disabled")
            
        load_content()

    btn_bozuk_incele = tk.Button(main_frame, text="OKUNMAYAN / BOZUK DOSYAYI Ä°NCELE", command=dosya_icerigi_incele, font=("Segoe UI", 10, "bold"), bg="#8D6E63", fg="white", activebackground="#6D4C41", activeforeground="white", cursor="hand2", relief="flat", borderwidth=0, pady=8)
    btn_bozuk_incele.pack(fill="x", pady=(0, 8))

    # --- Ä°STASYON KODU GÃ¼Râš™ ---
    frame_ist = tk.Frame(main_frame, bg="#F8F9FA")
    frame_ist.pack(fill="x", pady=(0, 8))
    tk.Label(frame_ist, text="Ã¼stasyon Kodu:", font=("Segoe UI", 10, "bold"), bg="#F8F9FA", fg="#495057").pack(side="left")
    ent_ist = ttk.Entry(frame_ist, font=("Segoe UI", 11), width=15)
    ent_ist.insert(0, "17244")
    ent_ist.pack(side="left", padx=(10, 0))

    # --- YENÄ°: DURUM Ã‡UBUÄU ---
    status_frame = tk.Frame(root, bg="#E9ECEF")
    status_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 0))

    lbl_status = tk.Label(status_frame, text="HazÃ¼r", anchor="w", bg="#E9ECEF", font=("Segoe UI", 9))
    lbl_status.pack(side="left", padx=5, pady=2)

    
    root.mainloop()
else:
    print("Terminal modunda Ã¼alÄ°ÅtÃ¼rÃ¼lÃ¼yor. GUI devre dâš™ bÄ±rakÄ±ldÄ±.")
    if __name__ == "__main__": aylik_rapor_olustur(run_async=False)

# --- YENÄ°: LOG DOSYASINI OKUDAN Ã–NCE HANDLER'LARI KAPAT VE FLUSH ET ---
if False:
        handler.close()
        logging.root.removeHandler(handler)

# EÃ¼er log dosyasÄ± varsa oku ve yazdÄ±r
if os.path.exists(log_dosyasi):
    try:
        with open(log_dosyasi, 'r', encoding='utf-8') as f:
            print(f.read())
    except Exception as e:
        print(f"{Colors.WARNING}Log dosyasÄ± okunamadÄ±: {e}{Colors.ENDC}")
else:
    print(f"{Colors.WARNING}Log dosyasÄ± bulunamadÄ±: {log_dosyasi}{Colors.ENDC}")

try:
    pass # input removed for headless
except KeyboardInterrupt:
    print("\nProgram kullanÄ±cÄ± tarafÃ¼ndan sonlandÄ±rÄ±ldÄ±.")
# Program baÅŸarÄ±yla tamamlandÄ±
    pass # sys.exit removed for headless



