from __future__ import annotations

import re

import requests

_WATCHLIST = ["VST", "TDC", "TOL", "UPST", "LKQ", "DG"]
_URL_TEMPLATE = "https://stockanalysis.com/stocks/{ticker}/ratings/"
_UA = {"user-agent": "Mozilla/5.0"}


def _clean_text(html: str) -> str:
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def _parse_title(html: str, ticker: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, flags=re.S | re.I)
    if not m:
        return ticker
    title = re.sub(r"\s+Analyst Ratings$", "", m.group(1).strip(), flags=re.I)
    title = re.sub(r"\s+\([^)]*\)$", "", title).strip()
    return title or ticker


def _parse_page(html: str, ticker: str) -> dict | None:
    text = _clean_text(html)
    m = re.search(
        r"Total Analysts\s+([\d,]+)\s+Consensus Rating\s+([A-Za-z ]+?)\s+Price Target\s+\$([0-9.,]+)\s+Upside\s+([+\-0-9.,%]+)",
        text,
    )
    if not m:
        return None

    total_analysts = int(m.group(1).replace(",", ""))
    consensus = m.group(2).strip()
    price_target = float(m.group(3).replace(",", ""))
    upside = float(m.group(4).replace("%", "").replace("+", ""))
    company = _parse_title(html, ticker)

    return {
        "ticker": ticker,
        "company": company,
        "total_analysts": total_analysts,
        "consensus": consensus,
        "price_target": price_target,
        "upside": upside,
    }


def fetch_recommendations(limit: int = 3) -> list[dict]:
    picks: list[dict] = []
    for ticker in _WATCHLIST:
        try:
            resp = requests.get(_URL_TEMPLATE.format(ticker=ticker.lower()), timeout=15, headers=_UA)
            resp.raise_for_status()
            item = _parse_page(resp.text, ticker)
            if not item:
                continue
            if item["consensus"].lower() not in {"buy", "strong buy"}:
                continue
            if item["upside"] <= 0:
                continue
            picks.append(item)
        except Exception as e:
            print(f"Warning: failed to fetch stock rating for {ticker}: {e}")

    picks.sort(key=lambda x: (-x["upside"], x["ticker"]))
    return picks[:limit]
