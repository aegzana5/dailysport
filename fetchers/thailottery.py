"""Thai Government Lottery fetcher — scrapes news.sanook.com/lotto/."""

from __future__ import annotations

import re
from datetime import date, timedelta

import requests

_BASE_URL = "https://news.sanook.com/lotto/check/{date}/"
_DRAW_LIMIT = 100
_PRIZE1_RE = re.compile(r"รางวัลที่\s*1[\s\S]*?(\d{6})", re.S)


def _latest_draw_date(today: date | None = None) -> date:
    d = today or date.today()
    if d.day >= 16:
        return d.replace(day=16)
    return d.replace(day=1)


def _prev_draw_date(d: date) -> date:
    if d.day == 16:
        return d.replace(day=1)
    prev = d.replace(day=1) - timedelta(days=1)
    return prev.replace(day=16)


def _page_url(d: date) -> str:
    return _BASE_URL.format(date=d.strftime("%Y%m%d"))


def _parse_sanook_page(html: str) -> dict | None:
    m = _PRIZE1_RE.search(html)
    if not m:
        return None
    prize1 = m.group(1)
    return {"prize1": prize1, "two_digit": prize1[-2:]}


def _collect_results(limit: int = _DRAW_LIMIT) -> list[dict]:
    collected: list[dict] = []
    d = _latest_draw_date()
    seen_dates: set[str] = set()

    for _ in range(limit + 20):
        date_str = d.isoformat()
        if date_str not in seen_dates:
            seen_dates.add(date_str)
            try:
                resp = requests.get(
                    _page_url(d),
                    timeout=10,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    resp.encoding = resp.apparent_encoding or "utf-8"
                    result = _parse_sanook_page(resp.text)
                    if result:
                        result["date"] = date_str
                        collected.append(result)
                        if len(collected) >= limit:
                            return collected
            except Exception as e:
                print(f"Warning: failed to fetch Thai lottery for {date_str}: {e}")
        d = _prev_draw_date(d)

    return collected


def fetch_results() -> list[dict]:
    """Return Thai lottery results as list[dict] newest-first, up to 100 draws."""
    try:
        return _collect_results(limit=_DRAW_LIMIT)
    except Exception as e:
        print(f"Warning: failed to fetch Thai lottery: {e}")
        return []
