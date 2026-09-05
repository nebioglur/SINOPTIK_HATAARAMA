"""
MGM Monitor - ASP.NET Reader
==============================
MGM Kardelen sunucusundaki ASP.NET sayfalarından veri çeken sınıf.

Bu sınıf:
  1. Sayfa GET isteği ile __VIEWSTATE, __EVENTVALIDATION,
     __VIEWSTATEGENERATOR değerlerini otomatik alır.
  2. Tarih alanlarını DateResolver'dan gelen verilerle doldurur.
  3. İstasyon bilgisini URL query parametresi olarak ekler.
  4. "Yükle" butonuna POST gönderir.
  5. Sonuçta oluşan HTML'yi döndürür.

Kullanım:
    from mgm_monitor.config import ConfigLoader
    from mgm_monitor.readers import DateResolver, AspNetReader

    cfg = ConfigLoader()
    resolver = DateResolver(cfg.dates)
    resolver.resolve()

    reader = AspNetReader(cfg)
    html = reader.fetch("sinoptik", station_id=17244, station_name="KONYA MEYDAN")
"""

import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .date_resolver import DateResolver

logger = logging.getLogger("mgm_monitor.reader")


class AspNetReader:
    """
    ASP.NET tabanlı MGM sayfalarından veri çeken genel amaçlı okuyucu.
    Hem SinGoster.aspx hem MetarDefter.aspx için ortak kullanılır.
    """

    # ASP.NET gizli alanları
    _HIDDEN_FIELDS = [
        "__VIEWSTATE",
        "__VIEWSTATEGENERATOR",
        "__EVENTVALIDATION",
        "__EVENTTARGET",
        "__EVENTARGUMENT",
    ]

    def __init__(self, config):
        """
        Args:
            config: ConfigLoader instance veya dict.
                    config.app, config.reports, config.dates bilgilerini kullanır.
        """
        # ConfigLoader nesnesi mi yoksa düz dict mi?
        if hasattr(config, "app"):
            self._http_cfg = config.app.get("http", {})
            self._reports_cfg = config.reports.get("reports", {})
            self._dates_cfg = config.dates
        else:
            self._http_cfg = config.get("http", {})
            self._reports_cfg = config.get("reports", {})
            self._dates_cfg = config.get("dates", {})

        # HTTP oturum ayarları
        self._session = requests.Session()
        self._session.verify = self._http_cfg.get("verify_ssl", False)
        self._session.headers.update({
            "User-Agent": self._http_cfg.get(
                "user_agent", "MGM Monitor/1.0"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
        })

        self._timeout = self._http_cfg.get("timeout", 30)
        self._retries = self._http_cfg.get("retries", 3)
        self._retry_delay = self._http_cfg.get("retry_delay", 5)

        # Tarih çözümleyici
        self._date_resolver = DateResolver(self._dates_cfg)

    # ================================================================
    # Public API
    # ================================================================

    def fetch(
        self,
        report_name: str,
        station_id: int,
        station_name: str,
    ) -> str:
        """
        Belirtilen rapor türü ve istasyon için HTML içeriğini çeker.

        Args:
            report_name: Rapor adı (reports.yaml'daki anahtar: "sinoptik" / "metar")
            station_id: İstasyon numarası (örn: 17244)
            station_name: İstasyon adı (örn: "KONYA MEYDAN")

        Returns:
            POST sonucu oluşan HTML string.

        Raises:
            KeyError: Rapor tanımı bulunamazsa.
            ConnectionError: Bağlantı başarısız olursa.
        """
        # Rapor config'ini al
        report_cfg = self._reports_cfg.get(report_name)
        if report_cfg is None:
            available = ", ".join(self._reports_cfg.keys())
            raise KeyError(
                f"Rapor bulunamadı: '{report_name}'. "
                f"Mevcut raporlar: {available}"
            )

        if not report_cfg.get("enabled", True):
            logger.info(f"Rapor devre dışı: {report_name}")
            return ""

        # URL oluştur (query parametreleri ile)
        base_url = report_cfg["url"]
        url = self._build_url(base_url, report_cfg, station_id, station_name)

        logger.info(
            f"[{report_name.upper()}] İstasyon: {station_name} ({station_id}) "
            f"| Tarih: {self._date_resolver.get_display_range()}"
        )

        # Retry mekanizması ile çek
        return self._fetch_with_retry(url, report_cfg)

    def fetch_all_stations(
        self,
        report_name: str,
        stations: List[Dict[str, Any]],
    ) -> Dict[int, str]:
        """
        Tüm istasyonlar için HTML çeker.

        Args:
            report_name: Rapor adı
            stations: İstasyon listesi [{"id": 17244, "name": "KONYA MEYDAN"}, ...]

        Returns:
            {station_id: html_content, ...}
        """
        results = {}
        total = len(stations)

        for i, station in enumerate(stations, 1):
            sid = station["id"]
            sname = station["name"]

            logger.info(f"[{i}/{total}] {sname} ({sid}) çekiliyor...")

            try:
                html = self.fetch(report_name, sid, sname)
                results[sid] = html
            except Exception as e:
                logger.error(f"HATA - {sname} ({sid}): {e}")
                results[sid] = ""

            # İstekler arası kısa bekleme (sunucuyu yormamak için)
            if i < total:
                time.sleep(1)

        return results

    def resolve_dates(self, reference=None):
        """Tarihleri hesaplar. Fetch öncesinde çağrılmalıdır."""
        self._date_resolver.resolve(reference)
        return self._date_resolver

    # ================================================================
    # Private
    # ================================================================

    def _build_url(
        self,
        base_url: str,
        report_cfg: Dict[str, Any],
        station_id: int,
        station_name: str,
    ) -> str:
        """İstasyon bilgisini query parametresi olarak ekler."""
        query_cfg = report_cfg.get("station_query", {})
        id_param = query_cfg.get("id", "ist")
        name_param = query_cfg.get("name", "istIsim")

        params = {
            id_param: str(station_id),
            name_param: station_name,
        }

        return f"{base_url}?{urlencode(params)}"

    def _fetch_with_retry(
        self,
        url: str,
        report_cfg: Dict[str, Any],
    ) -> str:
        """Retry mekanizması ile GET + POST yapar."""
        last_error = None

        for attempt in range(1, self._retries + 1):
            try:
                return self._do_fetch(url, report_cfg)
            except requests.RequestException as e:
                last_error = e
                logger.warning(
                    f"Deneme {attempt}/{self._retries} başarısız: {e}"
                )
                if attempt < self._retries:
                    time.sleep(self._retry_delay)

        raise ConnectionError(
            f"{self._retries} deneme sonrasında bağlantı kurulamadı. "
            f"Son hata: {last_error}"
        )

    def _do_fetch(self, url: str, report_cfg: Dict[str, Any]) -> str:
        """
        Tek bir GET + POST döngüsü.

        1. GET → Hidden fields'ları yakala
        2. POST → Tarih + buton ile formu gönder
        3. Response HTML döndür
        """
        # ---- STEP 1: GET ----
        logger.debug(f"GET {url}")
        resp_get = self._session.get(url, timeout=self._timeout)
        resp_get.raise_for_status()
        resp_get.encoding = "utf-8"

        # Hidden alanları parse et
        hidden_fields = self._extract_hidden_fields(resp_get.text)

        if "__VIEWSTATE" not in hidden_fields:
            raise ValueError(
                "__VIEWSTATE bulunamadı. Sayfa yapısı değişmiş olabilir."
            )

        # ---- STEP 2: POST payload oluştur ----
        payload = dict(hidden_fields)  # Gizli alanlarla başla

        # Tarih alanlarını ekle
        date_fields = self._date_resolver.get_form_fields()
        payload.update(date_fields)

        # Yükle butonunu ekle
        button = report_cfg.get("button", "ctl00$cBody$btnYukle")
        payload[button] = "Yükle"

        # ---- STEP 3: POST ----
        logger.debug(f"POST {url}")
        resp_post = self._session.post(
            url,
            data=payload,
            timeout=self._timeout,
        )
        resp_post.raise_for_status()
        resp_post.encoding = "utf-8"

        logger.debug(
            f"Yanıt boyutu: {len(resp_post.text)} karakter"
        )

        return resp_post.text

    def _extract_hidden_fields(self, html: str) -> Dict[str, str]:
        """
        HTML'den ASP.NET gizli form alanlarını çıkarır.

        Args:
            html: Sayfa HTML'i

        Returns:
            {"__VIEWSTATE": "...", "__EVENTVALIDATION": "...", ...}
        """
        soup = BeautifulSoup(html, "html.parser")
        fields = {}

        for field_name in self._HIDDEN_FIELDS:
            tag = soup.find("input", {"name": field_name})
            if tag and tag.get("value"):
                fields[field_name] = tag["value"]

        logger.debug(
            f"Bulunan hidden alanlar: {list(fields.keys())}"
        )

        return fields

    # ================================================================
    # Context Manager desteği
    # ================================================================

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        """HTTP oturumunu kapatır."""
        self._session.close()

    def __repr__(self):
        reports = list(self._reports_cfg.keys())
        return (
            f"<AspNetReader reports={reports} "
            f"dates='{self._date_resolver.get_display_range()}'>"
        )
