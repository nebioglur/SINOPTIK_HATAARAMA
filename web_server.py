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
    logging.info(f"[{ist_isim}] Otomatik analiz tetiklendi: {custom_title}")
    # Arayuz'deki analiz mantigini konsol modunda cagir
    arayuz.islem_yurut(
        load_from_cache=False, 
        df_sin_param=df_sin, 
        df_metar_param=df_metar, 
        override_yil=yil, 
        override_ay=ay, 
        custom_title=custom_title
    )
    logging.info(f"[{ist_isim}] Otomatik analiz tamamlandi, rapor uretildi.")

def baslat_arka_plan_gorevleri():
    """Gunicorn altinda birden cok kez tetiklenmemesi icin kontrol ekleyerek gorevleri baslatir."""
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not os.environ.get("FLASK_RUN_FROM_CLI"):
        # Eger background task onceden baslamissa tekrar baslatma
        if getattr(app, '_bg_started', False):
            return
        app._bg_started = True
        
        logging.info("Arka plan otomatik analiz gorevleri baslatiliyor...")
        cfg = canli_analiz.get_config()
        istasyonlar = cfg.get_enabled_stations()
        if not istasyonlar:
            logging.warning("stations.yaml icinde aktif istasyon bulunamadi! Varsayilan (17244) kullaniliyor.")
            istasyonlar = [{'id': 17244, 'name': 'KONYA MEYDAN'}]
        
        for s in istasyonlar:
            ist_kodu = int(s.get('id', 17244))
            ist_isim = s.get('name', str(ist_kodu))
            logging.info(f"Arka plan gorevi baslatildi: {ist_isim} ({ist_kodu})")
            t = threading.Thread(
                target=canli_analiz.otomatik_dongu,
                args=(ist_kodu, 1, oto_trigger, lambda msg: logging.info(f"[{ist_isim}] {msg}")),
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

if __name__ == "__main__":
    print("HATA RAMA Web Sunucusu Başlatıldı - http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
