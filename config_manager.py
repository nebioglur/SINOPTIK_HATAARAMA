# -*- coding: utf-8 -*-
try:
    import yaml
    HAS_YAML = True
except ImportError:
    import json
    HAS_YAML = False

import os
import sys
import logging
import traceback
import threading
from logging.handlers import RotatingFileHandler
import shutil

# EXE çalışıyorsa exe'nin olduğu klasörü, değilse dosyanın olduğu klasörü al
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Öncelik: EXE'nin yanındaki dosya (Taşınabilir Mod)
CONFIG_FILE = os.path.join(APP_DIR, "kardelen_ayarlar.yaml")
CONFIG_FILE_OLD = os.path.join(APP_DIR, "kardelen_ayarlar.json")

# 2. Yedek: Kullanıcı Klasörü (Eğer EXE klasörüne yazma izni yoksa veya eski ayarlar oradaysa)
def _get_safe_user_dir():
    for p in [os.environ.get("USERPROFILE"), os.path.expanduser("~"), os.environ.get("PUBLIC")]:
        if p and os.path.exists(p):
            return p
    return APP_DIR

USER_DATA_DIR = os.path.join(_get_safe_user_dir(), "KardelenLogs")
USER_CONFIG_FILE = os.path.join(USER_DATA_DIR, "kardelen_ayarlar.yaml")
USER_CONFIG_FILE_OLD = os.path.join(USER_DATA_DIR, "kardelen_ayarlar.json")

def load_config():
    """Uygulama ayarlarını yükler."""
    # 1. ÖNCELİK: Kullanıcı Klasörü (Exe güncellense bile ayarların kaybolmaması için ana merkez burasıdır)
    if os.path.exists(USER_CONFIG_FILE):
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                if HAS_YAML: return yaml.safe_load(f) or {}
                else: return json.load(f) or {}
        except Exception as e:
            logging.error(f"Bozuk ayar dosyası (USER_CONFIG). Yedekleniyor... Hata: {e}")
            try: shutil.copy(USER_CONFIG_FILE, USER_CONFIG_FILE + ".bozuk")
            except: pass
            
    # ESKİ SÜRÜMDEN GEÇİŞ (JSON -> YAML OTOMATİK DÖNÜŞÜM)
    elif os.path.exists(USER_CONFIG_FILE_OLD):
        try:
            with open(USER_CONFIG_FILE_OLD, 'r', encoding='utf-8') as f:
                old_config = json.load(f) or {}
            save_config(old_config) # Yeni formata (YAML) dönüştürüp kaydet
            return old_config
        except Exception as e:
            logging.error(f"Eski JSON ayar dosyası (USER_CONFIG) okunamadı. Hata: {e}")

    # 2. Yedek: EXE yanına bak (Taşınabilir mod veya ilk kurulum)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                if HAS_YAML: return yaml.safe_load(f) or {}
                else: return json.load(f) or {}
        except Exception as e:
            logging.error(f"Bozuk ayar dosyası (CONFIG_FILE). Yedekleniyor... Hata: {e}")
            try: shutil.copy(CONFIG_FILE, CONFIG_FILE + ".bozuk")
            except: pass
            
    elif os.path.exists(CONFIG_FILE_OLD):
        try:
            with open(CONFIG_FILE_OLD, 'r', encoding='utf-8') as f:
                old_config = json.load(f) or {}
            save_config(old_config) # Yeni formata (YAML) dönüştürüp kaydet
            return old_config
        except Exception as e:
            logging.error(f"Eski JSON ayar dosyası (CONFIG_FILE) okunamadı. Hata: {e}")

    # 3. Yoksa EXE içine gömülü ayarlara bak (Varsayılanlar)
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled_config = os.path.join(sys._MEIPASS, "kardelen_ayarlar.yaml")
        if os.path.exists(bundled_config):
            try:
                with open(bundled_config, 'r', encoding='utf-8') as f:
                    if HAS_YAML: return yaml.safe_load(f) or {}
                    else: return json.load(f) or {}
            except: pass
        
    return {}

def save_config(data):
    """Mevcut ayarları kaydeder."""
    try:
        # 1. ÖNCELİK: Kullanıcı Klasörüne yaz (Ayarların kalıcı olması için)
        if not os.path.exists(USER_DATA_DIR):
            os.makedirs(USER_DATA_DIR)
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            if HAS_YAML:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            else:
                json.dump(data, f, indent=4, ensure_ascii=False)
    except: pass

# =============================================================================
# MERKEZİ LOGLAMA SİSTEMİ
# =============================================================================

# Terminal Hatalarını ve Kayıp Çıktıları Önlemek İçin Gelişmiş Logger Stream
class LoggerStream:
    def __init__(self, level, prefix=""):
        self.level = level
        self.prefix = prefix
        self.encoding = 'utf-8'

    def write(self, message):
        try:
            if isinstance(message, str) and message.strip():
                self.level(f"{self.prefix}{message.strip()}")
            elif isinstance(message, bytes) and message.strip():
                self.level(f"{self.prefix}{message.decode('utf-8', errors='ignore').strip()}")
        except Exception:
            pass
        return len(message) if message else 0

    def flush(self):
        pass

    def isatty(self):
        return False

# Global Hata Yakalayıcılar (Crash Handler)
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.critical("BEKLENMEYEN KRİTİK HATA (GLOBAL CRASH):\n" + error_msg)
    
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Kritik Uygulama Hatası", 
            f"Uygulama beklenmedik bir hata ile karşılaştı ve kapatılacak.\n\n"
            f"Hata Detayı: {exc_value}\n\n"
            f"Lütfen KardelenLogs klasöründeki log dosyalarını kontrol edin.")
        root.destroy()
    except: pass
    sys.exit(1)

def thread_exception_handler(args):
    """Arka planda (Thread) sessizce oluşan hataları log dosyasına yazar."""
    logging.critical(f"ARKA PLAN İŞLEM HATASI ({args.thread.name if args.thread else 'Bilinmeyen'}):\n" + "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)))

def setup_logging(log_filename="kardelen_gunluk_log.txt", level=logging.INFO):
    """Tüm uygulama için merkezi daily-folder loglama yapılandırmasını kurar."""
    from datetime import datetime, timezone
    
    base_log_dir = USER_DATA_DIR
    # Her gün için ayrı klasör (YYYY-MM-DD)
    today_folder = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    log_dir = os.path.join(base_log_dir, today_folder)
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, log_filename)

    # Temizlik: Mevcut tüm handler'ları kaldır
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    class SafeRotatingFileHandler(RotatingFileHandler):
        def doRollover(self):
            try:
                super().doRollover()
            except (PermissionError, OSError):
                pass # Windows'ta dosya başka işlem tarafından kilitliyse rollover'ı atla

    file_handler = SafeRotatingFileHandler(log_file_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    handlers = [file_handler]
    
    # Penceresiz (windowed) exe veya geçersiz stdout durumunda çökmeyi önlemek için
    original_stdout = sys.stdout
    if original_stdout:
        try:
            if hasattr(original_stdout, 'isatty') and original_stdout.isatty():
                handlers.append(logging.StreamHandler(original_stdout))
            elif not getattr(sys, 'frozen', False):
                handlers.append(logging.StreamHandler(original_stdout))
        except Exception:
            pass

    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s', handlers=handlers)
    
    if os.environ.get("HEADLESS_MODE", "0") != "1":
        sys.stdout = LoggerStream(logging.info, "TERMINAL_Cikti: ")
        sys.stderr = LoggerStream(logging.error, "TERMINAL_HATA: ")
    
    sys.excepthook = global_exception_handler
    threading.excepthook = thread_exception_handler
    
    logging.info(f"Merkezi loglama sistemi '{log_file_path}' için başarıyla başlatıldı.")
    return log_file_path