from __future__ import annotations

import math

import requests

_URL = "https://api.binance.com/api/v3/ticker/24hr"
_UA = {"user-agent": "Mozilla/5.0"}
_EXCLUDED_QUOTES = {
    "USDT",
    "USDC",
    "FDUSD",
    "TUSD",
    "BUSD",
    "DAI",
    "USDP",
    "PYUSD",
    "EUR",
    "GBP",
    "TRY",
    "BRL",
    "AUD",
    "BIDR",
    "IDRT",
    "UAH",
    "RUB",
    "NGN",
    "ZAR",
    "MXN",
    "CHF",
    "JPY",
    "CNH",
}
_EXCLUDED_PREFIXES = ("UP", "DOWN", "BULL", "BEAR", "1000")


def _parse_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _is_valid_symbol(symbol: str) -> bool:
    if not symbol.endswith("USDT"):
        return False
    base = symbol[:-4]
    if not base or base in _EXCLUDED_QUOTES:
        return False
    if any(base.startswith(prefix) for prefix in _EXCLUDED_PREFIXES):
        return False
    return True


def _build_item(raw: dict) -> dict | None:
    symbol = str(raw.get("symbol", "")).upper()
    if not _is_valid_symbol(symbol):
        return None

    change = _parse_float(raw.get("priceChangePercent"))
    price = _parse_float(raw.get("lastPrice"))
    volume = _parse_float(raw.get("quoteVolume"))

    if not math.isfinite(change) or not math.isfinite(price) or not math.isfinite(volume):
        return None
    if change <= 0:
        return None
    if volume <= 0:
        return None

    return {
        "symbol": symbol[:-4],
        "pair": symbol,
        "price": price,
        "change_24h": change,
        "quote_volume": volume,
    }


def fetch_recommendations(limit: int = 3) -> list[dict]:
    try:
        resp = requests.get(_URL, timeout=15, headers=_UA)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        print(f"Warning: failed to fetch crypto momentum: {e}")
        return []

    picks: list[dict] = []
    if isinstance(payload, list):
        for raw in payload:
            if not isinstance(raw, dict):
                continue
            item = _build_item(raw)
            if item:
                picks.append(item)

    picks.sort(key=lambda item: (-item["change_24h"], -item["quote_volume"], item["symbol"]))
    return picks[:limit]
