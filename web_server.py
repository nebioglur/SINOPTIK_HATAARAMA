import os
import threading
import logging

# Headless modunu aktif et ki arayuz.py tk.Tk() olusturmasin
os.environ["HEADLESS_MODE"] = "1"

from flask import Flask, send_file
import arayuz
import canli_analiz

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(BASE_DIR, "latest_report.html")

logging.basicConfig(level=logging.INFO)

# Arayuz.py'deki islem_yurut'u cagiracak callback
def oto_trigger(df_sin, df_metar, yil, ay, ist_isim, custom_title):
    print(f"WEB_SERVER_LOG: [{ist_isim}] Otomatik analiz tetiklendi: {custom_title}")
    try:
        # Arayuz'deki analiz mantigini konsol modunda cagir
        arayuz.islem_yurut(
            load_from_cache=False, 
            df_sin_param=df_sin, 
            df_metar_param=df_metar, 
            override_yil=yil, 
            override_ay=ay, 
            custom_title=custom_title
        )
        print(f"WEB_SERVER_LOG: [{ist_isim}] Otomatik analiz tamamlandi, rapor uretildi.")
    except Exception as e:
        print(f"WEB_SERVER_LOG: HATA - islem_yurut coktu: {e}")

def baslat_arka_plan_gorevleri():
    """Gunicorn altinda birden cok kez tetiklenmemesi icin kontrol ekleyerek gorevleri baslatir."""
    # Eger background task onceden baslamissa tekrar baslatma
    if getattr(app, '_bg_started', False):
        return
    app._bg_started = True
    
    print("WEB_SERVER_LOG: Arka plan otomatik analiz gorevleri baslatiliyor...")
    cfg = canli_analiz.get_config()
    istasyonlar = cfg.get_enabled_stations()
    if not istasyonlar:
        print("WEB_SERVER_LOG: UYARI - stations.yaml icinde aktif istasyon bulunamadi! Varsayilan (17244) kullaniliyor.")
        istasyonlar = [{'id': 17244, 'name': 'KONYA MEYDAN'}]
    
    for s in istasyonlar:
        ist_kodu = int(s.get('id', 17244))
        ist_isim = s.get('name', str(ist_kodu))
        print(f"WEB_SERVER_LOG: Arka plan gorevi baslatildi: {ist_isim} ({ist_kodu})")
        t = threading.Thread(
            target=canli_analiz.otomatik_dongu,
            args=(ist_kodu, 1, oto_trigger, lambda msg: print(f"WEB_SERVER_LOG: [{ist_isim}] {msg}")),
            daemon=True
        )
        t.start()

# Flask uygulamasi yuklendiginde arka plan islerini baslat
baslat_arka_plan_gorevleri()

@app.route("/")
def index():
    if os.path.exists(REPORT_PATH):
        return send_file(REPORT_PATH)
    else:
        return "<h1>Henüz analiz sonucu oluşturulmadı.</h1><p>Arka plan görevi 7/24 çalışıyor. Sistem her saat başı 55 geçe (xx:55) güncel verileri çeker. Lütfen bekleyin.</p>", 404

@app.route("/logs")
def view_logs():
    import glob
    from flask import Response
    import config_manager
    log_dir = config_manager.USER_DATA_DIR
    log_files = glob.glob(os.path.join(log_dir, "**", "*.log"), recursive=True)
    if not log_files:
        return "Log dosyasi bulunamadi."
    latest_log = max(log_files, key=os.path.getmtime)
    try:
        with open(latest_log, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()[-100:]
            return Response("<h1>Son Hata Kayitlari</h1><pre>" + "\n".join(lines) + "</pre>", mimetype='text/html')
    except Exception as e:
        return str(e)

@app.route("/start")
def force_start():
    print("WEB_SERVER_LOG: /start endpoint tetiklendi!")
    try:
        baslat_arka_plan_gorevleri()
        return "Gorevler baslatildi! Lutfen /logs veya anasayfaya donun."
    except Exception as e:
        print(f"WEB_SERVER_LOG: /start HATA: {e}")
        return f"Hata: {e}"

if __name__ == "__main__":
    print("HATA RAMA Web Sunucusu Başlatıldı - http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
