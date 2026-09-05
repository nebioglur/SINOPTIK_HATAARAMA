"""
MGM Monitor - Date Resolver
=============================
dates.yaml yapılandırmasına göre dinamik tarih üretir.

Desteklenen modlar:
    today    → Bugüne göre offset ile hesaplar
    rolling  → Son N gün (last_days)
    custom   → Sabit tarih aralığı (custom_start / custom_end)

Kullanım:
    from mgm_monitor.config import ConfigLoader
    from mgm_monitor.readers import DateResolver

    cfg = ConfigLoader()
    resolver = DateResolver(cfg.dates)
    start, end = resolver.resolve()
    form_fields = resolver.get_form_fields()
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Tuple


class DateResolver:
    """
    Config'e göre başlangıç ve bitiş tarihlerini hesaplar,
    ASP.NET form alanlarını hazırlar.
    """

    def __init__(self, date_config: Dict[str, Any]):
        """
        Args:
            date_config: dates.yaml içeriği (dict).
                         'date' ve 'controls' anahtarlarını içerir.
        """
        self._cfg = date_config.get("date", date_config)
        self._controls = date_config.get("controls", {})
        self._start: datetime | None = None
        self._end: datetime | None = None

    def resolve(self, reference: datetime | None = None) -> Tuple[datetime, datetime]:
        """
        Tarihleri hesaplar ve (start, end) tuple döndürür.

        Args:
            reference: Referans tarih. Verilmezse datetime.now() kullanılır.
                       Test/debug için farklı tarih verilebilir.

        Returns:
            (start_date, end_date) tuple

        Raises:
            ValueError: Geçersiz mod veya eksik config durumunda.
        """
        now = reference or datetime.now()
        mode = self._cfg.get("mode", "rolling").lower().strip()

        if mode == "today":
            self._start, self._end = self._resolve_today(now)
        elif mode == "rolling":
            self._start, self._end = self._resolve_rolling(now)
        elif mode == "custom":
            self._start, self._end = self._resolve_custom()
        else:
            raise ValueError(
                f"Geçersiz tarih modu: '{mode}'. "
                f"Geçerli modlar: today, rolling, custom"
            )

        return self._start, self._end

    def _resolve_today(self, now: datetime) -> Tuple[datetime, datetime]:
        """today modu: Offset ile bugünden hesaplar."""
        start_offset = int(self._cfg.get("start_offset", -1))
        end_offset = int(self._cfg.get("end_offset", 0))

        start = now + timedelta(days=start_offset)
        end = now + timedelta(days=end_offset)
        return start, end

    def _resolve_rolling(self, now: datetime) -> Tuple[datetime, datetime]:
        """rolling modu: Son N gün."""
        last_days = int(self._cfg.get("last_days", 2))
        if last_days < 1:
            raise ValueError(f"last_days en az 1 olmalı, verilen: {last_days}")

        start = now - timedelta(days=last_days - 1)
        end = now
        return start, end

    def _resolve_custom(self) -> Tuple[datetime, datetime]:
        """custom modu: Sabit tarih aralığı."""
        custom_start = self._cfg.get("custom_start", "")
        custom_end = self._cfg.get("custom_end", "")

        if not custom_start or not custom_end:
            raise ValueError(
                "custom modunda 'custom_start' ve 'custom_end' "
                "değerleri zorunludur. Örnek: '2026-07-01'"
            )

        start = datetime.strptime(str(custom_start), "%Y-%m-%d")
        end = datetime.strptime(str(custom_end), "%Y-%m-%d")

        if start > end:
            raise ValueError(
                f"Başlangıç tarihi ({custom_start}) bitiş tarihinden "
                f"({custom_end}) sonra olamaz."
            )

        return start, end

    def get_form_fields(self) -> Dict[str, str]:
        """
        ASP.NET form POST verileri için tarih alanlarını döndürür.

        Önce resolve() çağrılmalıdır.

        Returns:
            {
                "ctl00$cBody$ddBasGun": "14",
                "ctl00$cBody$ddBasAy": "7",
                "ctl00$cBody$ddBasYil": "2026",
                "ctl00$cBody$ddBitisGun": "15",
                "ctl00$cBody$ddbitisAy": "7",
                "ctl00$cBody$ddbitisYil": "2026"
            }
        """
        if self._start is None or self._end is None:
            raise RuntimeError(
                "Tarihler henüz hesaplanmadı. Önce resolve() çağırın."
            )

        fields = {}

        # Başlangıç tarihi
        if "start_day" in self._controls:
            fields[self._controls["start_day"]] = str(self._start.day)
        if "start_month" in self._controls:
            fields[self._controls["start_month"]] = str(self._start.month)
        if "start_year" in self._controls:
            fields[self._controls["start_year"]] = str(self._start.year)

        # Bitiş tarihi
        if "end_day" in self._controls:
            fields[self._controls["end_day"]] = str(self._end.day)
        if "end_month" in self._controls:
            fields[self._controls["end_month"]] = str(self._end.month)
        if "end_year" in self._controls:
            fields[self._controls["end_year"]] = str(self._end.year)

        return fields

    def get_display_range(self) -> str:
        """İnsan tarafından okunabilir tarih aralığı string'i döndürür."""
        if self._start is None or self._end is None:
            return "(tarih henüz hesaplanmadı)"

        fmt = self._cfg.get("format", "%d.%m.%Y")
        return f"{self._start.strftime(fmt)} - {self._end.strftime(fmt)}"

    @property
    def start(self) -> datetime | None:
        return self._start

    @property
    def end(self) -> datetime | None:
        return self._end

    @property
    def mode(self) -> str:
        return self._cfg.get("mode", "rolling")

    def __repr__(self) -> str:
        return (
            f"<DateResolver mode='{self.mode}' "
            f"range='{self.get_display_range()}'>"
        )
