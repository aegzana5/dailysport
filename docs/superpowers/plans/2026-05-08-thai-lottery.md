# Thai Lottery Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add standalone `--thailottery` Discord command that scrapes 100 draws from sanook.com, analyzes เลขท้าย 2 ตัว patterns (hot/cold/due/suggestions), and posts to webhook.

**Architecture:** New fetcher walks draw dates backwards (1st/16th) fetching `/lotto/check/YYYYMMDD/`, extracts รางวัลที่ 1 via regex, derives two_digit = prize1[-2:]. New analyzer groups by calendar month for avg_per_month stat. Formatter reuses `_lottery_mode_lines` with minor tweaks. main.py gets new `--thailottery` flag that returns before touching football API.

**Tech Stack:** Python 3.11+, requests, re, pytest, unittest.mock

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `fetchers/thailottery.py` | Create | Scrape sanook.com, walk draw dates, return 100 draws |
| `fetchers/thailottery_analyzer.py` | Create | Hot/cold/due/monthly_avg/suggestions |
| `formatter.py` | Modify | Add `format_thailottery()`, tweak `_lottery_mode_lines` |
| `main.py` | Modify | Add `--thailottery` mode + imports |
| `tests/test_thailottery.py` | Create | Fetcher unit tests (date utils + parser + mocked fetch) |
| `tests/test_thailottery_analyzer.py` | Create | Analyzer unit tests |
| `tests/test_formatter.py` | Modify | Add `format_thailottery` tests |
| `tests/test_main.py` | Modify | Add `--thailottery` mode test |

---

### Task 1: Thai Lottery Analyzer

**Files:**
- Create: `fetchers/thailottery_analyzer.py`
- Create: `tests/test_thailottery_analyzer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_thailottery_analyzer.py`:

```python
from fetchers.thailottery_analyzer import analyze

_DRAWS = [
    {"date": "2025-12-16", "prize1": "123456", "two_digit": "56"},
    {"date": "2025-12-01", "prize1": "654321", "two_digit": "21"},
    {"date": "2025-11-16", "prize1": "111156", "two_digit": "56"},
    {"date": "2025-11-01", "prize1": "222256", "two_digit": "56"},
    {"date": "2025-10-16", "prize1": "333321", "two_digit": "21"},
]


def test_total_draws():
    r = analyze(_DRAWS)
    assert r["total_draws"] == 5


def test_hot_top_number():
    r = analyze(_DRAWS)
    assert r["hot"][0]["number"] == "56"
    assert r["hot"][0]["count"] == 3


def test_latest_is_newest():
    r = analyze(_DRAWS)
    assert r["latest"]["prize1"] == "123456"
    assert r["latest"]["two_digit"] == "56"
    assert r["latest"]["date"] == "2025-12-16"


def test_cold_includes_never_appeared():
    r = analyze(_DRAWS)
    cold_nums = [x["number"] for x in r["cold"]]
    assert "00" in cold_nums


def test_monthly_avg_present():
    r = analyze(_DRAWS)
    assert "monthly_avg" in r
    assert len(r["monthly_avg"]) > 0
    assert all("avg_per_month" in w for w in r["monthly_avg"])


def test_monthly_avg_denominator():
    # 3 unique months (Oct, Nov, Dec). "56" appears 3 times → 3/3 = 1.0
    r = analyze(_DRAWS)
    top = r["monthly_avg"][0]
    assert top["number"] == "56"
    assert top["avg_per_month"] == 1.0


def test_suggestions_are_strings():
    r = analyze(_DRAWS)
    assert all(isinstance(s, str) for s in r["suggestions"])


def test_suggestions_max_5():
    r = analyze(_DRAWS)
    assert len(r["suggestions"]) <= 5


def test_empty_results():
    r = analyze([])
    assert r["total_draws"] == 0
    assert r["latest"] is None
    assert r["hot"] == []
    assert r["monthly_avg"] == []
    assert r["suggestions"] == []


def test_due_only_has_seen_numbers():
    r = analyze(_DRAWS)
    seen = {"56", "21"}
    assert all(d["number"] in seen for d in r["due"])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_thailottery_analyzer.py -v
```
Expected: `ImportError: No module named 'fetchers.thailottery_analyzer'`

- [ ] **Step 3: Create analyzer**

Create `fetchers/thailottery_analyzer.py`:

```python
"""Thai Lottery 2-digit analyzer."""

from collections import Counter
from datetime import datetime


def analyze(results: list[dict]) -> dict:
    if not results:
        return {
            "total_draws": 0,
            "latest": None,
            "hot": [],
            "cold": [],
            "due": [],
            "monthly_avg": [],
            "suggestions": [],
        }

    total = len(results)
    latest = results[0]
    digits = [r["two_digit"] for r in results if r.get("two_digit")]
    all_numbers = [f"{i:02d}" for i in range(100)]

    freq = Counter(digits)

    hot_sorted = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    hot = [{"number": n, "count": c} for n, c in hot_sorted[:5]]

    full_freq = {n: freq.get(n, 0) for n in all_numbers}
    cold_sorted = sorted(full_freq.items(), key=lambda x: (x[1], x[0]))
    cold = [{"number": n, "count": c} for n, c in cold_sorted[:5]]

    positions: dict[str, list[int]] = {}
    for idx, num in enumerate(digits):
        positions.setdefault(num, []).append(idx)

    due_candidates = []
    for num, pos_list in positions.items():
        if len(pos_list) < 2:
            continue
        gaps = [pos_list[i + 1] - pos_list[i] for i in range(len(pos_list) - 1)]
        avg_gap = sum(gaps) / len(gaps)
        last_seen = pos_list[0]
        if last_seen > avg_gap:
            due_candidates.append({
                "number": num,
                "avg_gap": round(avg_gap, 4),
                "last_seen": last_seen,
                "_score": last_seen - avg_gap,
            })

    due_candidates.sort(key=lambda x: (-x["_score"], x["number"]))
    due = [
        {"number": d["number"], "avg_gap": d["avg_gap"], "last_seen": d["last_seen"]}
        for d in due_candidates[:5]
    ]

    seen_months: set[tuple[int, int]] = set()
    for r in results:
        try:
            d = datetime.strptime(r.get("date", "")[:10], "%Y-%m-%d")
            seen_months.add((d.year, d.month))
        except Exception:
            pass
    num_months = max(len(seen_months), 1)

    monthly_sorted = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    monthly_avg = [
        {"number": n, "count": c, "avg_per_month": round(c / num_months, 1)}
        for n, c in monthly_sorted[:5]
    ]

    seen: set[str] = set()
    suggestions: list[str] = []
    for entry in hot[:3]:
        n = entry["number"]
        if n not in seen:
            seen.add(n)
            suggestions.append(n)
    for entry in due[:5]:
        n = entry["number"]
        if n not in seen and len(suggestions) < 5:
            seen.add(n)
            suggestions.append(n)

    return {
        "total_draws": total,
        "latest": {
            "date": latest.get("date", ""),
            "prize1": latest.get("prize1", ""),
            "two_digit": latest.get("two_digit", ""),
        },
        "hot": hot,
        "cold": cold,
        "due": due,
        "monthly_avg": monthly_avg,
        "suggestions": suggestions,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_thailottery_analyzer.py -v
```
Expected: all 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add fetchers/thailottery_analyzer.py tests/test_thailottery_analyzer.py
git commit -m "feat: add Thai lottery analyzer with monthly avg grouping"
```

---

### Task 2: Fetcher — Date Utilities

**Files:**
- Create: `fetchers/thailottery.py` (date functions only for now)
- Create: `tests/test_thailottery.py` (date function tests)

- [ ] **Step 1: Write failing tests**

Create `tests/test_thailottery.py`:

```python
from datetime import date
from fetchers.thailottery import _latest_draw_date, _prev_draw_date


def test_latest_draw_date_mid_month():
    assert _latest_draw_date(date(2025, 5, 10)) == date(2025, 5, 1)


def test_latest_draw_date_after_16():
    assert _latest_draw_date(date(2025, 5, 20)) == date(2025, 5, 16)


def test_latest_draw_date_on_16():
    assert _latest_draw_date(date(2025, 5, 16)) == date(2025, 5, 16)


def test_latest_draw_date_on_1():
    assert _latest_draw_date(date(2025, 5, 1)) == date(2025, 5, 1)


def test_latest_draw_date_day_2():
    assert _latest_draw_date(date(2025, 5, 2)) == date(2025, 5, 1)


def test_prev_draw_date_from_16():
    assert _prev_draw_date(date(2025, 5, 16)) == date(2025, 5, 1)


def test_prev_draw_date_from_1():
    assert _prev_draw_date(date(2025, 5, 1)) == date(2025, 4, 16)


def test_prev_draw_date_jan_1():
    assert _prev_draw_date(date(2025, 1, 1)) == date(2024, 12, 16)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_thailottery.py::test_latest_draw_date_mid_month tests/test_thailottery.py::test_prev_draw_date_from_16 -v
```
Expected: `ImportError: No module named 'fetchers.thailottery'`

- [ ] **Step 3: Create fetcher with date utilities**

Create `fetchers/thailottery.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_thailottery.py -k "latest_draw or prev_draw" -v
```
Expected: all 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add fetchers/thailottery.py tests/test_thailottery.py
git commit -m "feat: add Thai lottery fetcher date utilities"
```

---

### Task 3: Fetcher — HTML Parser

**Files:**
- Modify: `fetchers/thailottery.py` (add `_parse_sanook_page`, `_page_url`)
- Modify: `tests/test_thailottery.py` (add parser tests)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_thailottery.py`:

```python
from fetchers.thailottery import _parse_sanook_page, _page_url


def test_parse_sanook_page_success():
    html = "<div>รางวัลที่ 1</div><div>123456</div>"
    result = _parse_sanook_page(html)
    assert result == {"prize1": "123456", "two_digit": "56"}


def test_parse_sanook_page_two_digit_from_prize():
    html = "<span>รางวัลที่ 1</span><span>009900</span>"
    result = _parse_sanook_page(html)
    assert result["two_digit"] == "00"


def test_parse_sanook_page_no_match():
    html = "<div>ไม่มีผลสลาก</div>"
    assert _parse_sanook_page(html) is None


def test_parse_sanook_page_ignores_non_six_digit():
    html = "<div>รางวัลที่ 1</div><div>999</div><div>123456</div>"
    result = _parse_sanook_page(html)
    assert result["prize1"] == "123456"


def test_page_url_format():
    assert _page_url(date(2025, 12, 16)) == "https://news.sanook.com/lotto/check/20251216/"
    assert _page_url(date(2025, 1, 1)) == "https://news.sanook.com/lotto/check/20250101/"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_thailottery.py -k "parse or page_url" -v
```
Expected: `ImportError` for `_parse_sanook_page`

- [ ] **Step 3: Add parser and URL builder to fetcher**

Append to `fetchers/thailottery.py` (after `_PRIZE1_RE` definition, before the end of file):

```python
def _page_url(d: date) -> str:
    return _BASE_URL.format(date=d.strftime("%Y%m%d"))


def _parse_sanook_page(html: str) -> dict | None:
    m = _PRIZE1_RE.search(html)
    if not m:
        return None
    prize1 = m.group(1)
    return {"prize1": prize1, "two_digit": prize1[-2:]}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_thailottery.py -k "parse or page_url" -v
```
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add fetchers/thailottery.py tests/test_thailottery.py
git commit -m "feat: add sanook.com HTML parser for Thai lottery"
```

---

### Task 4: Fetcher — Full Integration

**Files:**
- Modify: `fetchers/thailottery.py` (add `_collect_results`, `fetch_results`)
- Modify: `tests/test_thailottery.py` (add fetch_results tests)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_thailottery.py`:

```python
from unittest.mock import MagicMock, patch
import fetchers.thailottery as _mod


def _make_mock_resp(html: str, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.apparent_encoding = "utf-8"
    resp.text = html
    return resp


def test_fetch_results_returns_list():
    html = "<div>รางวัลที่ 1</div><div>123456</div>"
    with (
        patch.object(_mod, "_DRAW_LIMIT", 3),
        patch("fetchers.thailottery.requests.get", return_value=_make_mock_resp(html)),
        patch("fetchers.thailottery._latest_draw_date", return_value=date(2025, 12, 16)),
    ):
        results = _mod.fetch_results()
    assert len(results) == 3
    assert results[0]["prize1"] == "123456"
    assert results[0]["two_digit"] == "56"
    assert "date" in results[0]


def test_fetch_results_skips_404():
    html = "<div>รางวัลที่ 1</div><div>111111</div>"
    responses = [
        _make_mock_resp("", status=404),
        _make_mock_resp(html),
        _make_mock_resp(html),
        _make_mock_resp(html),
    ]
    with (
        patch.object(_mod, "_DRAW_LIMIT", 3),
        patch("fetchers.thailottery.requests.get", side_effect=responses),
        patch("fetchers.thailottery._latest_draw_date", return_value=date(2025, 12, 16)),
    ):
        results = _mod.fetch_results()
    assert len(results) == 3


def test_fetch_results_skips_unparseable():
    good_html = "<div>รางวัลที่ 1</div><div>999999</div>"
    responses = [
        _make_mock_resp("<div>no prize here</div>"),
        _make_mock_resp(good_html),
        _make_mock_resp(good_html),
        _make_mock_resp(good_html),
    ]
    with (
        patch.object(_mod, "_DRAW_LIMIT", 3),
        patch("fetchers.thailottery.requests.get", side_effect=responses),
        patch("fetchers.thailottery._latest_draw_date", return_value=date(2025, 12, 16)),
    ):
        results = _mod.fetch_results()
    assert len(results) == 3
    assert all(r["prize1"] == "999999" for r in results)


def test_fetch_results_returns_empty_on_exception():
    with patch("fetchers.thailottery.requests.get", side_effect=Exception("network error")):
        results = _mod.fetch_results()
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_thailottery.py -k "fetch_results" -v
```
Expected: `ImportError` for `fetch_results`

- [ ] **Step 3: Add collect and fetch functions to fetcher**

Append to `fetchers/thailottery.py`:

```python
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
```

- [ ] **Step 4: Run all fetcher tests**

```bash
pytest tests/test_thailottery.py -v
```
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add fetchers/thailottery.py tests/test_thailottery.py
git commit -m "feat: add Thai lottery fetch_results with sanook.com scraping"
```

---

### Task 5: Formatter

**Files:**
- Modify: `formatter.py` (tweak `_lottery_mode_lines`, add `format_thailottery`)
- Modify: `tests/test_formatter.py` (add format_thailottery tests)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_formatter.py`:

```python
from formatter import format_thailottery
from datetime import date


_THAI_ANALYSIS = {
    "total_draws": 100,
    "latest": {"date": "2025-12-16", "prize1": "123456", "two_digit": "56"},
    "hot": [{"number": "56", "count": 8}],
    "cold": [{"number": "00", "count": 0}],
    "due": [{"number": "12", "avg_gap": 4.2, "last_seen": 7}],
    "monthly_avg": [{"number": "56", "count": 8, "avg_per_month": 1.6}],
    "suggestions": ["56", "12"],
}


def test_format_thailottery_has_thai_header():
    payload = format_thailottery(_THAI_ANALYSIS, date(2025, 12, 16))
    assert "หวยไทย" in payload["content"]


def test_format_thailottery_shows_prize1():
    payload = format_thailottery(_THAI_ANALYSIS, date(2025, 12, 16))
    assert "123456" in payload["content"]


def test_format_thailottery_shows_suggestions():
    payload = format_thailottery(_THAI_ANALYSIS, date(2025, 12, 16))
    assert "56" in payload["content"]


def test_format_thailottery_shows_monthly_avg():
    payload = format_thailottery(_THAI_ANALYSIS, date(2025, 12, 16))
    assert "เดือน" in payload["content"]


def test_format_thailottery_empty_analysis():
    empty = {
        "total_draws": 0, "latest": None,
        "hot": [], "cold": [], "due": [], "monthly_avg": [], "suggestions": [],
    }
    payload = format_thailottery(empty, date(2025, 12, 16))
    assert "หวยไทย" in payload["content"]
    assert "ไม่มีข้อมูล" in payload["content"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_formatter.py -k "thai" -v
```
Expected: `ImportError` for `format_thailottery`

- [ ] **Step 3: Modify `_lottery_mode_lines` in `formatter.py`**

In `formatter.py`, find `_lottery_mode_lines` (line 67). Make these two edits:

**Edit A** — change line 73 from:
```python
    weekly_avg = analysis.get("weekly_avg", [])
```
to:
```python
    if analysis.get("monthly_avg") is not None:
        avg_data = analysis.get("monthly_avg", [])
        avg_header = "📅 **เฉลี่ยต่อเดือน**"
        avg_val_key = "avg_per_month"
        avg_unit = "ครั้ง/เดือน"
    else:
        avg_data = analysis.get("weekly_avg", [])
        avg_header = "📅 **เฉลี่ยต่อสัปดาห์**"
        avg_val_key = "avg_per_week"
        avg_unit = "ครั้ง/สัปดาห์"
```

**Edit B** — change line 87 from:
```python
        lines.append(f"🎯 **ผลล่าสุด**: {latest.get('number') or '-'} ({label} {latest.get('two_digit') or '??'}){suffix}")
```
to:
```python
        prize_num = latest.get("number") or latest.get("prize1") or "-"
        lines.append(f"🎯 **ผลล่าสุด**: {prize_num} ({label} {latest.get('two_digit') or '??'}){suffix}")
```

**Edit C** — find the block that starts `if weekly_avg:` (around line 100) and replace it:

From:
```python
    if weekly_avg:
        lines.append("📅 **เฉลี่ยต่อสัปดาห์**")
        for w in weekly_avg:
            lines.append(f"  {w['number']} — {w['avg_per_week']:.1f} ครั้ง/สัปดาห์")
        lines.append("")
```
To:
```python
    if avg_data:
        lines.append(avg_header)
        for w in avg_data:
            lines.append(f"  {w['number']} — {w[avg_val_key]:.1f} {avg_unit}")
        lines.append("")
```

- [ ] **Step 4: Add `format_thailottery` to `formatter.py`**

Append after `format_lottery` function (before `format_combined`):

```python
def format_thailottery(analysis: dict, today: date) -> dict:
    if not analysis.get("total_draws"):
        lines = [f"**🎰 วิเคราะห์หวยไทย — {today.isoformat()}**", "ไม่มีข้อมูล"]
    else:
        lines = [f"**🎰 วิเคราะห์หวยไทย — {today.isoformat()}**", ""]
        lines.extend(_lottery_mode_lines(analysis, "2 ตัวล่าง"))
    while lines and lines[-1] == "":
        lines.pop()
    return {"content": "\n".join(lines).strip()}
```

- [ ] **Step 5: Run all formatter tests**

```bash
pytest tests/test_formatter.py -v
```
Expected: all tests PASS (including existing Lao lottery tests — the `_lottery_mode_lines` tweak is backwards-compatible because Lao analysis dicts have `weekly_avg` key, not `monthly_avg`)

- [ ] **Step 6: Commit**

```bash
git add formatter.py tests/test_formatter.py
git commit -m "feat: add format_thailottery, support monthly_avg in lottery display"
```

---

### Task 6: main.py Integration

**Files:**
- Modify: `main.py` (imports + `--thailottery` flag + mode block)
- Modify: `tests/test_main.py` (add `--thailottery` test)

- [ ] **Step 1: Write failing test**

Append to `tests/test_main.py`:

```python
def test_thailottery_mode_posts_analysis():
    _analysis = {
        "total_draws": 100,
        "latest": {"date": "2025-12-16", "prize1": "123456", "two_digit": "56"},
        "hot": [{"number": "56", "count": 8}],
        "cold": [{"number": "00", "count": 0}],
        "due": [],
        "monthly_avg": [{"number": "56", "count": 8, "avg_per_month": 1.6}],
        "suggestions": ["56"],
    }
    with (
        patch("main.fetch_thai_results", return_value=[]),
        patch("main.analyze_thai", return_value=_analysis),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main(thailottery_mode=True)
        mock_post.assert_called_once()
        assert "หวยไทย" in mock_post.call_args[0][1]["content"]


def test_thailottery_mode_no_football_api_key_needed():
    _analysis = {
        "total_draws": 0, "latest": None,
        "hot": [], "cold": [], "due": [], "monthly_avg": [], "suggestions": [],
    }
    with (
        patch("main.fetch_thai_results", return_value=[]),
        patch("main.analyze_thai", return_value=_analysis),
        patch("main.post_to_webhook"),
        patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://hook"}, clear=True),
    ):
        main.main(thailottery_mode=True)  # must not raise KeyError
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main.py -k "thailottery" -v
```
Expected: `TypeError: main() got an unexpected keyword argument 'thailottery_mode'`

- [ ] **Step 3: Update `main.py`**

**Edit A** — add imports after line 14:
```python
from fetchers.thailottery import fetch_results as fetch_thai_results
from fetchers.thailottery_analyzer import analyze as analyze_thai
```

**Edit B** — add `format_thailottery` to formatter import on line 15:
```python
from formatter import format_embed, format_reminder, format_kickoff, format_lottery, format_combined, format_thailottery
```

**Edit C** — add `thailottery_mode: bool = False` to `main()` signature (line 50):
```python
def main(
    now_utc: datetime | None = None,
    reminder_mode: bool = False,
    kickoff_mode: bool = False,
    lottery_mode: bool = False,
    combined_mode: bool = False,
    thailottery_mode: bool = False,
) -> None:
```

**Edit D** — add argv detection after line 59 (after `if not combined_mode:`):
```python
    if not thailottery_mode:
        thailottery_mode = "--thailottery" in sys.argv
```

**Edit E** — add the mode block after the `if lottery_mode:` block (after line 72, before `api_key = ...`):
```python
    if thailottery_mode:
        results = fetch_thai_results()
        analysis = analyze_thai(results)
        payload = format_thailottery(analysis, now_utc.date())
        post_to_webhook(webhook_url, payload)
        print(f"Posted Thai lottery analysis ({analysis['total_draws']} draws).")
        return
```

- [ ] **Step 4: Run all tests**

```bash
pytest -v
```
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add --thailottery standalone command"
```

---

## Self-Review

**Spec coverage:**
- ✅ `fetchers/thailottery.py` — scrapes sanook.com, 100 draws, newest-first
- ✅ `fetchers/thailottery_analyzer.py` — hot/cold/due/monthly_avg/suggestions
- ✅ `formatter.py` — `format_thailottery()` + `_lottery_mode_lines` tweaks
- ✅ `main.py` — `--thailottery` standalone flag, no football API needed
- ✅ Tests for all new files + modified files

**Placeholder scan:** None found.

**Type consistency:**
- `fetch_results() -> list[dict]` used in Task 4, imported as `fetch_thai_results` in Task 6 ✅
- `analyze(results: list[dict]) -> dict` returns `monthly_avg` key, consumed by `format_thailottery` and `_lottery_mode_lines` ✅
- `format_thailottery(analysis: dict, today: date) -> dict` matches usage in main.py ✅
- `latest` dict keys: `prize1`, `two_digit`, `date` — used in `_lottery_mode_lines` via `latest.get("prize1")` ✅
