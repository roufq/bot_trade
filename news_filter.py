"""Filter kalender ekonomi opsional dengan cache; sumber API dipilih pengguna."""

from datetime import datetime, timedelta, timezone
import time

import requests

import config

_cache = {"loaded_at": 0.0, "events": []}
COUNTRY_TO_CURRENCY = {"US": "USD", "USA": "USD", "UNITED STATES": "USD"}


def _parse_time(value) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        # FMP mendokumentasikan waktu kalender dalam UTC. Timestamp tanpa
        # offset diperlakukan sebagai UTC lalu dikonversi ke waktu lokal PC.
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed
    except (ValueError, TypeError):
        return None


def event_blackout(events: list[dict], now: datetime | None = None) -> tuple[bool, str]:
    now = now or datetime.now()
    for event in events:
        currency = str(event.get("currency", "")).upper()
        if not currency:
            country = str(event.get("country", "")).upper()
            currency = COUNTRY_TO_CURRENCY.get(country, country)
        impact = str(event.get("impact", "")).lower()
        event_time = _parse_time(event.get("time") or event.get("datetime") or event.get("date"))
        if currency not in config.NEWS_FILTER_CURRENCIES or impact not in config.NEWS_FILTER_IMPACTS or event_time is None:
            continue
        start = event_time - timedelta(minutes=config.NEWS_BLOCK_BEFORE_MINUTES)
        end = event_time + timedelta(minutes=config.NEWS_BLOCK_AFTER_MINUTES)
        if start <= now <= end:
            title = event.get("title") or event.get("name") or event.get("event") or "high-impact event"
            return True, f"{currency} {title} ({event_time:%H:%M})"
    return False, ""


def is_blackout(now: datetime | None = None) -> tuple[bool, str]:
    if not config.NEWS_CALENDAR_URL:
        return False, "calendar API tidak dikonfigurasi"
    if time.time() - _cache["loaded_at"] >= config.NEWS_REFRESH_SECONDS:
        try:
            response = requests.get(config.NEWS_CALENDAR_URL, timeout=10)
            response.raise_for_status()
            payload = response.json()
            events = payload.get("events", []) if isinstance(payload, dict) else payload
            if isinstance(events, list):
                _cache.update({"loaded_at": time.time(), "events": events})
        except (requests.RequestException, ValueError):
            # Fail-safe tidak mematikan bot bila feed opsional gagal; blackout
            # manual tetap tersedia. Simpan waktu percobaan agar endpoint gagal
            # tidak dipanggil dan dicatat setiap detik.
            _cache["loaded_at"] = time.time()
            return False, "calendar API gagal, gunakan blackout manual"
    return event_blackout(_cache["events"], now)
