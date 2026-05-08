"""Thai Government Lottery fetcher — scrapes news.sanook.com/lotto/."""

from __future__ import annotations

import re
from datetime import date, timedelta

import requests

_BASE_URL = "https://news.sanook.com/lotto/check/{date}/"
_DRAW_LIMIT = 100
_PRIZE1_RE = re.compile(r"รางวัลที่\s*1[^0-9]*?(\d{6})", re.S)


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
