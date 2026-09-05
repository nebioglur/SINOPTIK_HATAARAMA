import os
from flask import Flask, send_file

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(BASE_DIR, "latest_report.html")

@app.route("/")
def index():
    if os.path.exists(REPORT_PATH):
        return send_file(REPORT_PATH)
    else:
        return "<h1>Henüz analiz sonucu oluşturulmadı.</h1><p>Lütfen masaüstü uygulamasından analizi başlatın veya otomatik analizi bekleyin.</p>", 404

if __name__ == "__main__":
    print("HATA RAMA Web Sunucusu Başlatıldı - http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
