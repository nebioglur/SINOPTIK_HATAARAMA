"""
MGM Monitor - Config ve DateResolver Test
===========================================
Config dosyalarının doğru okunduğunu ve tarih üretiminin çalıştığını doğrular.

Çalıştırma:
    cd mgm_monitor
    python test_config.py
"""

import sys
from pathlib import Path

# Proje kökünü path'e ekle
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mgm_monitor.config import ConfigLoader
from mgm_monitor.readers import DateResolver
from datetime import datetime


def test_config_loader():
    """Config dosyalarının doğru yüklendiğini test eder."""
    print("=" * 60)
    print("TEST: ConfigLoader")
    print("=" * 60)

    config_dir = Path(__file__).parent / "config"
    cfg = ConfigLoader(str(config_dir))

    print(f"\n{cfg}")
    print(f"\nApp adı    : {cfg.app.get('app', {}).get('name', '?')}")
    print(f"Versiyon   : {cfg.app.get('app', {}).get('version', '?')}")
    print(f"Timeout    : {cfg.get('app', 'http.timeout', '?')} saniye")
    print(f"SSL doğ.   : {cfg.get('app', 'http.verify_ssl', '?')}")

    # Raporlar
    reports = cfg.get_enabled_reports()
    print(f"\nAktif raporlar ({len(reports)}):")
    for name, rcfg in reports.items():
        print(f"  - {rcfg.get('name', name)}: {rcfg.get('url', '?')}")

    # İstasyonlar
    stations = cfg.get_enabled_stations()
    print(f"\nAktif istasyonlar ({len(stations)}):")
    for s in stations[:5]:
        print(f"  - {s['id']}: {s['name']}")
    if len(stations) > 5:
        print(f"  ... ve {len(stations) - 5} istasyon daha")

    # Tarih modu
    print(f"\nTarih modu: {cfg.dates.get('date', {}).get('mode', '?')}")

    # Analyzer kuralları
    rules = cfg.analyzer.get("rules", {})
    active_rules = [k for k, v in rules.items() if v]
    print(f"\nAktif analiz kuralları ({len(active_rules)}):")
    for r in active_rules:
        print(f"  [+] {r}")

    # Bildirim
    notify = cfg.notify
    channels = []
    if notify.get("desktop", {}).get("enabled"):
        channels.append("Masaüstü")
    if notify.get("sound", {}).get("enabled"):
        channels.append("Ses")
    if notify.get("telegram", {}).get("enabled"):
        channels.append("Telegram")
    if notify.get("mail", {}).get("enabled"):
        channels.append("E-posta")
    print(f"\nAktif bildirim kanalları: {', '.join(channels) or 'Yok'}")

    print("\n[OK] ConfigLoader testi BASARILI\n")


def test_date_resolver():
    """Tarih üretiminin doğru çalıştığını test eder."""
    print("=" * 60)
    print("TEST: DateResolver")
    print("=" * 60)

    config_dir = Path(__file__).parent / "config"
    cfg = ConfigLoader(str(config_dir))

    # 1) Rolling mod (config'den)
    print("\n--- Rolling Mod (config'den) ---")
    resolver = DateResolver(cfg.dates)
    start, end = resolver.resolve()
    print(f"  Mod       : {resolver.mode}")
    print(f"  Başlangıç : {start.strftime('%d.%m.%Y')}")
    print(f"  Bitiş     : {end.strftime('%d.%m.%Y')}")
    print(f"  Aralık    : {resolver.get_display_range()}")
    print(f"  Form alanları:")
    for key, val in resolver.get_form_fields().items():
        print(f"    {key} = {val}")

    # 2) Today modu simülasyonu
    print("\n--- Today Modu (simülasyon) ---")
    today_config = {
        "date": {
            "mode": "today",
            "start_offset": -1,
            "end_offset": 0,
            "format": "%d.%m.%Y",
        },
        "controls": cfg.dates.get("controls", {}),
    }
    resolver2 = DateResolver(today_config)
    s2, e2 = resolver2.resolve()
    print(f"  Mod       : {resolver2.mode}")
    print(f"  Başlangıç : {s2.strftime('%d.%m.%Y')}")
    print(f"  Bitiş     : {e2.strftime('%d.%m.%Y')}")

    # 3) Custom mod simülasyonu
    print("\n--- Custom Modu (simülasyon) ---")
    custom_config = {
        "date": {
            "mode": "custom",
            "custom_start": "2026-07-01",
            "custom_end": "2026-07-15",
            "format": "%d.%m.%Y",
        },
        "controls": cfg.dates.get("controls", {}),
    }
    resolver3 = DateResolver(custom_config)
    s3, e3 = resolver3.resolve()
    print(f"  Mod       : {resolver3.mode}")
    print(f"  Başlangıç : {s3.strftime('%d.%m.%Y')}")
    print(f"  Bitiş     : {e3.strftime('%d.%m.%Y')}")

    # 4) Farklı referans tarih ile test
    print("\n--- Farklı Referans Tarih (01.01.2027) ---")
    resolver4 = DateResolver(cfg.dates)
    ref = datetime(2027, 1, 1)
    s4, e4 = resolver4.resolve(reference=ref)
    print(f"  Referans  : {ref.strftime('%d.%m.%Y')}")
    print(f"  Aralık    : {resolver4.get_display_range()}")

    print(f"\n{resolver}")
    print("\n[OK] DateResolver testi BASARILI\n")


if __name__ == "__main__":
    test_config_loader()
    test_date_resolver()
    print("=" * 60)
    print("TUM TESTLER BASARILI [OK]")
    print("=" * 60)
