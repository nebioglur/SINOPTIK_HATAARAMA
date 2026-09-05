"""
MGM Monitor - Config Loader
============================
Tüm YAML config dosyalarını okur ve tek bir nesne üzerinden erişim sağlar.

Kullanım:
    from mgm_monitor.config import ConfigLoader

    cfg = ConfigLoader()
    print(cfg.app)          # app.yaml içeriği
    print(cfg.reports)      # reports.yaml içeriği
    print(cfg.dates)        # dates.yaml içeriği
    print(cfg.stations)     # stations.yaml içeriği
    print(cfg.analyzer)     # analyzer.yaml içeriği
    print(cfg.notify)       # notify.yaml içeriği
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigLoader:
    """
    Tüm YAML yapılandırma dosyalarını yükler.
    config/ klasöründeki her .yaml dosyası otomatik olarak okunur.
    """

    # Yüklenecek config dosyaları ve attribute isimleri
    _CONFIG_FILES = {
        "app": "app.yaml",
        "reports": "reports.yaml",
        "dates": "dates.yaml",
        "stations": "stations.yaml",
        "analyzer": "analyzer.yaml",
        "notify": "notify.yaml",
    }

    def __init__(self, config_dir: Optional[str] = None):
        """
        Args:
            config_dir: Config klasörü yolu.
                         Verilmezse bu dosyanın bulunduğu klasör kullanılır.
        """
        if config_dir is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))

        self._config_dir = Path(config_dir)
        self._data: Dict[str, Any] = {}

        self._load_all()

    def _load_all(self) -> None:
        """Tüm config dosyalarını yükler."""
        for attr_name, filename in self._CONFIG_FILES.items():
            filepath = self._config_dir / filename
            if filepath.exists():
                self._data[attr_name] = self._load_yaml(filepath)
            else:
                print(f"[UYARI] Config dosyası bulunamadı: {filepath}")
                self._data[attr_name] = {}

    @staticmethod
    def _load_yaml(filepath: Path) -> Dict[str, Any]:
        """Tek bir YAML dosyasını okur ve dict olarak döndürür."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if data is not None else {}

    # ----------------------------------------------------------------
    # Property erişimleri
    # ----------------------------------------------------------------

    @property
    def app(self) -> Dict[str, Any]:
        """app.yaml içeriği."""
        return self._data.get("app", {})

    @property
    def reports(self) -> Dict[str, Any]:
        """reports.yaml içeriği."""
        return self._data.get("reports", {})

    @property
    def dates(self) -> Dict[str, Any]:
        """dates.yaml içeriği."""
        return self._data.get("dates", {})

    @property
    def stations(self) -> List[Dict[str, Any]]:
        """stations.yaml içeriği (istasyon listesi)."""
        data = self._data.get("stations", {})
        # stations.yaml kökünde "stations" anahtarı varsa listeyi döndür
        if isinstance(data, dict) and "stations" in data:
            return data["stations"]
        return data if isinstance(data, list) else []

    @property
    def analyzer(self) -> Dict[str, Any]:
        """analyzer.yaml içeriği."""
        return self._data.get("analyzer", {})

    @property
    def notify(self) -> Dict[str, Any]:
        """notify.yaml içeriği."""
        return self._data.get("notify", {})

    # ----------------------------------------------------------------
    # Yardımcı metodlar
    # ----------------------------------------------------------------

    def get_enabled_reports(self) -> Dict[str, Dict[str, Any]]:
        """Sadece enabled: true olan raporları döndürür."""
        all_reports = self.reports.get("reports", {})
        return {
            name: cfg
            for name, cfg in all_reports.items()
            if cfg.get("enabled", False)
        }

    def get_enabled_stations(self) -> List[Dict[str, Any]]:
        """Sadece enabled: true olan istasyonları döndürür."""
        return [
            s for s in self.stations
            if s.get("enabled", True)
        ]

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        İç içe değerlere noktalı erişim.

        Örnek:
            cfg.get("app", "http.timeout", 30)
        """
        data = self._data.get(section, {})
        keys = key.split(".")
        for k in keys:
            if isinstance(data, dict):
                data = data.get(k, default)
            else:
                return default
        return data

    def reload(self) -> None:
        """Tüm config dosyalarını yeniden yükler."""
        self._data.clear()
        self._load_all()

    def __repr__(self) -> str:
        sections = ", ".join(self._data.keys())
        return f"<ConfigLoader sections=[{sections}]>"
