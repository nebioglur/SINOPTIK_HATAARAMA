"""
MGM Monitor - Ana Giriş Noktası
=================================
Tüm modülleri birleştiren ana çalışma dosyası.

Kullanım:
    python -m mgm_monitor.main
    python mgm_monitor/main.py
"""

import logging
import sys
from pathlib import Path

# Proje kökünü path'e ekle
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mgm_monitor.config import ConfigLoader
from mgm_monitor.readers import DateResolver, AspNetReader


def setup_logging(cfg: dict) -> logging.Logger:
    """Loglama yapılandırması."""
    log_cfg = cfg.get("logging", {})
    log_level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    log_file = log_cfg.get("file", "logs/monitor.log")

    # Log klasörünü oluştur
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Root logger
    logger = logging.getLogger("mgm_monitor")
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def main():
    """Ana çalışma fonksiyonu."""

    # 1) Config yükle
    config_dir = Path(__file__).parent / "config"
    cfg = ConfigLoader(str(config_dir))

    # 2) Loglama başlat
    logger = setup_logging(cfg.app)
    logger.info("=" * 60)
    logger.info("MGM Monitor başlatılıyor...")
    logger.info(f"Versiyon: {cfg.app.get('app', {}).get('version', '?')}")

    # 3) Tarihleri çöz
    date_resolver = DateResolver(cfg.dates)
    start, end = date_resolver.resolve()
    logger.info(f"Tarih aralığı: {date_resolver.get_display_range()}")
    logger.info(f"Tarih modu: {date_resolver.mode}")

    # 4) İstasyonları al
    stations = cfg.get_enabled_stations()
    logger.info(f"Aktif istasyon sayısı: {len(stations)}")

    # 5) Aktif raporları al
    reports = cfg.get_enabled_reports()
    logger.info(f"Aktif raporlar: {list(reports.keys())}")

    # 6) ASP.NET Reader oluştur
    with AspNetReader(cfg) as reader:
        reader.resolve_dates()

        for report_name, report_cfg in reports.items():
            logger.info("-" * 40)
            logger.info(f"Rapor: {report_cfg.get('name', report_name)}")

            # Tüm istasyonlar için HTML çek
            results = reader.fetch_all_stations(report_name, stations)

            # Sonuçları özetle
            success = sum(1 for v in results.values() if v)
            fail = sum(1 for v in results.values() if not v)
            logger.info(
                f"Sonuç: {success} başarılı, {fail} başarısız "
                f"(toplam {len(results)})"
            )

            # TODO: Parser'a gönder
            # TODO: Analyzer ile analiz et
            # TODO: History ile karşılaştır
            # TODO: Bildirim gönder

    logger.info("=" * 60)
    logger.info("MGM Monitor tamamlandı.")


if __name__ == "__main__":
    main()
