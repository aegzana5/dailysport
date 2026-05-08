"""Thai Government Lottery fetcher — scrapes horoscope.thaiorc.com."""

from __future__ import annotations

import re

import requests

_THAIORC_URL = "https://horoscope.thaiorc.com/lotto/thai/stats/lottery-years10.php"
_DRAW_LIMIT = 100
_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_DATE_RE = re.compile(r'contentID=\d+">(\d{2})/(\d{2})/(\d{4})</a>')


def _thaiorc_date_to_iso(day: str, month: str, buddhist_year: str) -> str:
    year = int(buddhist_year)
    if year > 2400:
        year -= 543
    return f"{year:04d}-{int(month):02d}-{int(day):02d}"


def _parse_thaiorc_results(html: str) -> list[dict]:
    results = []
    for row in _ROW_RE.findall(html):
        date_m = _DATE_RE.search(row)
        if not date_m:
            continue
        day, month, buddhist_year = date_m.groups()
        td_texts = [
            re.sub(r"<[^>]+>", "", td).strip()
            for td in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        ]
        prize1 = next((t for t in td_texts if re.match(r"^\d{6}$", t)), None)
        two_digit = next((t for t in reversed(td_texts) if re.match(r"^\d{2}$", t)), None)
        if prize1 and two_digit:
            results.append({
                "date": _thaiorc_date_to_iso(day, month, buddhist_year),
                "prize1": prize1,
                "two_digit": two_digit,
            })
    return results


def _page_url(page: int) -> str:
    if page <= 1:
        return _THAIORC_URL
    return f"{_THAIORC_URL}?pg={page}"


def _collect_thaiorc_results(limit: int = _DRAW_LIMIT) -> list[dict]:
    collected: list[dict] = []
    seen_dates: set[str] = set()

    for page in range(1, 20):
        resp = requests.get(_page_url(page), timeout=10)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "cp874"
        page_results = _parse_thaiorc_results(resp.text)
        if not page_results:
            break

        for result in page_results:
            result_date = result.get("date")
            if not result_date or result_date in seen_dates:
                continue
            seen_dates.add(result_date)
            collected.append(result)
            if len(collected) >= limit:
                return collected

    return collected


def fetch_results() -> list[dict]:
    """Returns Thai Government Lottery results as {date, prize1, two_digit}, newest first."""
    try:
        return _collect_thaiorc_results(limit=_DRAW_LIMIT)
    except Exception as e:
        print(f"Warning: failed to fetch Thai lottery from ThaiORC: {e}")
        return []
