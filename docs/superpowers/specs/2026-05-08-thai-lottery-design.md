# Thai Lottery Feature — Design Spec
**Date:** 2026-05-08
**Status:** Approved

## Overview

Standalone `--thailottery` command. Scrapes 100 draws from sanook.com, analyzes 2-digit (เลขท้าย 2 ตัว) frequency patterns, posts prediction summary to Discord.

---

## Files

| File | Role |
|------|------|
| `fetchers/thailottery.py` | Scrape sanook.com, return 100 draws newest-first |
| `fetchers/thailottery_analyzer.py` | Hot/cold/due/suggestions with monthly period grouping |
| `formatter.py` | Add `format_thailottery()` |
| `main.py` | Add `--thailottery` flag |
| `tests/test_thailottery.py` | Parser + date-walk unit tests |
| `tests/test_thailottery_analyzer.py` | Analyzer logic tests |

---

## Data Flow

```
https://news.sanook.com/lotto/check/YYYYMMDD/
        ↓  (one request per draw date, walk back 100 draws)
fetchers/thailottery.py  →  list[dict]  (newest first)
        ↓
fetchers/thailottery_analyzer.py  →  analysis dict
        ↓
formatter.format_thailottery()  →  Discord payload
        ↓
main.py --thailottery  →  post_to_webhook()
```

---

## Draw Dict Schema

```python
{
    "date": "2025-12-16",   # ISO date
    "prize1": "123456",     # 6-digit first prize (รางวัลที่ 1)
    "two_digit": "56",      # last 2 digits of prize1 (เลขท้าย 2 ตัว)
}
```

---

## Fetcher: `fetchers/thailottery.py`

- Entry point: `fetch_results() -> list[dict]`
- Start from latest draw date (1st or 16th of current/prior month)
- Walk back via `_prev_draw_date()`: 16th → 1st → prior 16th → …
- Fetch each at `https://news.sanook.com/lotto/check/YYYYMMDD/`
- Parse with `_parse_sanook_page(html) -> dict | None`
- Skip dates where page returns non-200 or parse yields nothing
- Stop after 100 valid draws
- Timeout 10s per request; catch exceptions, print warning, return partial

```python
def _prev_draw_date(d: date) -> date:
    if d.day == 16:
        return d.replace(day=1)
    prev = d.replace(day=1) - timedelta(days=1)
    return prev.replace(day=16)
```

Exact CSS selectors confirmed on live page during implementation.

---

## Analyzer: `fetchers/thailottery_analyzer.py`

- Entry point: `analyze(results: list[dict]) -> dict`
- Period grouping: **calendar half-month** via `_half_month(date_str) -> (year, month, 1|2)`
  - day ≤ 15 → half 1; day ≥ 16 → half 2
- `avg_per_month` denominator = unique calendar months in dataset

Output:
```python
{
    "total_draws": 100,
    "latest": {"date": "...", "prize1": "...", "two_digit": ".."},
    "hot":         [{"number": "56", "count": 8}, ...],       # top 5
    "cold":        [{"number": "03", "count": 0}, ...],       # top 5
    "due":         [{"number": "12", "avg_gap": 4.2, "last_seen": 7}, ...],  # top 5
    "monthly_avg": [{"number": "56", "count": 8, "avg_per_month": 1.6}, ...],
    "suggestions": ["56", "12", "33", "07", "89"],            # top-3 hot + top-5 due, deduped, max 5
}
```

---

## Formatter: `formatter.py`

Add `format_thailottery(analysis, today)`. Reuse `_lottery_mode_lines()` — tweak it to accept `monthly_avg` key in addition to existing `weekly_avg` (Thai uses monthly, Lao keeps weekly).

Discord message header: `🎰 วิเคราะห์หวยไทย — YYYY-MM-DD`

---

## main.py

```python
if thailottery_mode:
    results = fetch_thai_results()
    analysis = analyze_thai(results)
    payload = format_thailottery(analysis, now_utc.date())
    post_to_webhook(webhook_url, payload)
    print(f"Posted Thai lottery analysis ({analysis['total_draws']} draws).")
    return
```

`thailottery_mode` set by `--thailottery` in `sys.argv`. No new env vars required.

---

## Error Handling

- Fetcher: `try/except` around each page request; skip on failure; return partial list if < 100 draws fetched
- Analyzer: returns zeroed dict if `results` is empty
- main.py: no special handling (follows existing lottery pattern)

---

## Testing

**`tests/test_thailottery.py`**
- `_parse_sanook_page()` with fixture HTML → correct `prize1` + `two_digit`
- `_prev_draw_date()` boundary cases: 1st→prior 16th, 16th→1st, Jan 1st→Dec 16th prior year
- `fetch_results()` with mocked requests: deduplication, stops at 100, handles 404s

**`tests/test_thailottery_analyzer.py`**
- Empty input → zeroed dict
- Known data → correct hot/cold/due/monthly_avg/suggestions
- `_half_month()` boundary: day 15 → half 1, day 16 → half 2
