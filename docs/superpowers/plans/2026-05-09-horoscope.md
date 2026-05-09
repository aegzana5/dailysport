# Daily Horoscope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--horoscope` mode that fetches all 12 Western zodiac signs from a free API, translates content to Thai, and posts detailed horoscopes to Discord daily at 8:00 AM.

**Architecture:** New `fetchers/horoscope.py` fetches each sign from `horoscope-app-api.vercel.app`, translates description via `deep_translator` (Google backend), maps fixed fields (color/mood/compatibility/lucky_time) to Thai using hardcoded dicts, then returns a list of 12 sign dicts. `format_horoscope()` in `formatter.py` renders them into split Discord payloads. `main.py` wires the `--horoscope` flag.

**Tech Stack:** Python 3, `requests`, `deep_translator>=1.10.1`, `pytest`, `unittest.mock`

---

## File Map

| File | Change |
|------|--------|
| `requirements.txt` | Add `deep_translator>=1.10.1` |
| `fetchers/horoscope.py` | New — API fetch + Thai translation |
| `formatter.py` | Add `format_horoscope()` |
| `main.py` | Add `--horoscope` mode |
| `tests/test_horoscope.py` | New — fetcher tests |
| `tests/test_formatter.py` | Add horoscope formatter tests |
| `tests/test_main.py` | Add horoscope main() tests |

---

## Task 1: Add `deep_translator` dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add dependency**

Open `requirements.txt` and append:
```
deep_translator>=1.10.1
```

Final file:
```
requests==2.31.0
Pillow==10.3.0
pytest==8.2.0
deep_translator>=1.10.1
```

- [ ] **Step 2: Install**

```bash
pip install deep_translator
```

Expected: installs without error.

- [ ] **Step 3: Verify import**

```bash
python -c "from deep_translator import GoogleTranslator; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add deep_translator dependency for Thai horoscope translation"
```

---

## Task 2: Create `fetchers/horoscope.py`

**Files:**
- Create: `fetchers/horoscope.py`
- Create: `tests/test_horoscope.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_horoscope.py`:

```python
from unittest.mock import Mock, patch, call

from fetchers.horoscope import fetch_horoscopes, _lucky_time_thai, _translate_description


def _mock_response(data: dict) -> Mock:
    resp = Mock()
    resp.raise_for_status = Mock()
    resp.json = Mock(return_value={"data": data})
    return resp


_SAMPLE_DATA = {
    "date_range": "Mar 21 - Apr 19",
    "current_date": "May 9, 2026",
    "description": "Today is a great day.",
    "compatibility": "Taurus",
    "color": "Red",
    "lucky_number": "7",
    "lucky_time": "6am",
    "mood": "Happy",
}


def test_fetch_horoscopes_returns_12_signs():
    resp = _mock_response(_SAMPLE_DATA)
    with (
        patch("fetchers.horoscope.requests.get", return_value=resp),
        patch("fetchers.horoscope._translate_description", return_value="วันนี้ดีมาก"),
    ):
        result = fetch_horoscopes()
    assert len(result) == 12


def test_fetch_horoscopes_first_sign_is_aries():
    resp = _mock_response(_SAMPLE_DATA)
    with (
        patch("fetchers.horoscope.requests.get", return_value=resp),
        patch("fetchers.horoscope._translate_description", return_value="วันนี้ดีมาก"),
    ):
        result = fetch_horoscopes()
    assert result[0]["sign"] == "Aries"
    assert result[0]["sign_thai"] == "ราศีเมษ"
    assert result[0]["emoji"] == "♈"


def test_fetch_horoscopes_translates_fixed_fields():
    resp = _mock_response(_SAMPLE_DATA)
    with (
        patch("fetchers.horoscope.requests.get", return_value=resp),
        patch("fetchers.horoscope._translate_description", return_value="วันนี้ดีมาก"),
    ):
        result = fetch_horoscopes()
    aries = result[0]
    assert aries["color"] == "สีแดง"
    assert aries["mood"] == "มีความสุข"
    assert aries["compatibility"] == "ราศีพฤษภ"
    assert aries["lucky_time"] == "06:00 น."
    assert aries["lucky_number"] == "7"
    assert aries["description"] == "วันนี้ดีมาก"


def test_fetch_horoscopes_fallback_on_http_error():
    resp = Mock()
    resp.raise_for_status = Mock(side_effect=Exception("timeout"))
    with patch("fetchers.horoscope.requests.get", return_value=resp):
        result = fetch_horoscopes()
    assert len(result) == 12
    assert result[0]["description"] == "ไม่สามารถโหลดข้อมูลได้"


def test_lucky_time_thai_am():
    assert _lucky_time_thai("6am") == "06:00 น."


def test_lucky_time_thai_pm():
    assert _lucky_time_thai("3pm") == "15:00 น."


def test_lucky_time_thai_noon():
    assert _lucky_time_thai("12pm") == "12:00 น."


def test_lucky_time_thai_midnight():
    assert _lucky_time_thai("12am") == "00:00 น."


def test_lucky_time_thai_unknown_passthrough():
    assert _lucky_time_thai("evening") == "evening"


def test_translate_description_fallback_on_error():
    with patch("fetchers.horoscope.GoogleTranslator") as MockGT:
        MockGT.return_value.translate.side_effect = Exception("network error")
        result = _translate_description("Today is good.")
    assert result == "Today is good."
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/aegisen/discord-sports-schedule && python -m pytest tests/test_horoscope.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'fetchers.horoscope'`

- [ ] **Step 3: Create `fetchers/horoscope.py`**

```python
from __future__ import annotations

import requests
from deep_translator import GoogleTranslator

_BASE_URL = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
_TIMEOUT = 10

_SIGNS = [
    ("Aries",       "ราศีเมษ",   "♈", "Mar 21 - Apr 19"),
    ("Taurus",      "ราศีพฤษภ",  "♉", "Apr 20 - May 20"),
    ("Gemini",      "ราศีเมถุน", "♊", "May 21 - Jun 20"),
    ("Cancer",      "ราศีกรกฎ",  "♋", "Jun 21 - Jul 22"),
    ("Leo",         "ราศีสิงห์", "♌", "Jul 23 - Aug 22"),
    ("Virgo",       "ราศีกันย์", "♍", "Aug 23 - Sep 22"),
    ("Libra",       "ราศีตุลย์", "♎", "Sep 23 - Oct 22"),
    ("Scorpio",     "ราศีพิจิก", "♏", "Oct 23 - Nov 21"),
    ("Sagittarius", "ราศีธนู",   "♐", "Nov 22 - Dec 21"),
    ("Capricorn",   "ราศีมังกร", "♑", "Dec 22 - Jan 19"),
    ("Aquarius",    "ราศีกุมภ์", "♒", "Jan 20 - Feb 18"),
    ("Pisces",      "ราศีมีน",   "♓", "Feb 19 - Mar 20"),
]

_SIGN_THAI = {sign: thai for sign, thai, _, _ in _SIGNS}

_COLOR_THAI: dict[str, str] = {
    "Red": "สีแดง", "Blue": "สีน้ำเงิน", "Green": "สีเขียว",
    "Yellow": "สีเหลือง", "White": "สีขาว", "Black": "สีดำ",
    "Purple": "สีม่วง", "Orange": "สีส้ม", "Pink": "สีชมพู",
    "Gold": "สีทอง", "Silver": "สีเงิน", "Brown": "สีน้ำตาล",
    "Gray": "สีเทา", "Grey": "สีเทา", "Violet": "สีม่วง",
    "Indigo": "สีคราม", "Maroon": "สีแดงเข้ม", "Teal": "สีเขียวอมฟ้า",
    "Turquoise": "สีเทอร์ควอยซ์", "Lavender": "สีลาเวนเดอร์",
    "Beige": "สีเบจ", "Crimson": "สีแดงเข้ม", "Navy": "สีกรมท่า",
    "Coral": "สีคอรัล", "Mint": "สีมิ้นต์", "Scarlet": "สีแดงเข้ม",
    "Sky Blue": "สีฟ้า", "Peach": "สีพีช", "Cream": "สีครีม",
    "Magenta": "สีม่วงแดง", "Cyan": "สีฟ้าเข้ม",
}

_MOOD_THAI: dict[str, str] = {
    "Happy": "มีความสุข", "Excited": "ตื่นเต้น", "Romantic": "โรแมนติก",
    "Adventurous": "ชอบผจญภัย", "Calm": "สงบ", "Energetic": "มีพลังงาน",
    "Creative": "สร้างสรรค์", "Focused": "มีสมาธิ", "Mysterious": "ลึกลับ",
    "Optimistic": "มองโลกในแง่ดี", "Confident": "มั่นใจ", "Passionate": "หลงใหล",
    "Peaceful": "สงบสุข", "Anxious": "กังวล", "Nostalgic": "คิดถึงอดีต",
    "Playful": "ขี้เล่น", "Thoughtful": "ใคร่ครวญ", "Motivated": "มีแรงบันดาลใจ",
    "Inspired": "ได้รับแรงบันดาลใจ", "Melancholy": "เศร้า", "Cheerful": "ร่าเริง",
    "Determined": "มุ่งมั่น", "Curious": "อยากรู้อยากเห็น", "Grateful": "กตัญญู",
    "Ambitious": "มีความทะเยอทะยาน", "Sensitive": "อ่อนไหว", "Stubborn": "ดื้อรั้น",
    "Generous": "ใจกว้าง", "Analytical": "ชอบวิเคราะห์", "Intuitive": "มีสัญชาตญาณดี",
    "Sociable": "ชอบเข้าสังคม", "Independent": "เป็นอิสระ",
}


def _translate_description(text: str) -> str:
    try:
        return GoogleTranslator(source="en", target="th").translate(text)
    except Exception:
        return text


def _lucky_time_thai(raw: str) -> str:
    s = raw.strip().lower()
    try:
        if s.endswith("am"):
            hour = int(s[:-2])
            return f"{hour % 12:02d}:00 น."
        if s.endswith("pm"):
            hour = int(s[:-2])
            if hour != 12:
                hour += 12
            return f"{hour:02d}:00 น."
    except ValueError:
        pass
    return raw


def _fetch_sign(sign: str, sign_thai: str, emoji: str, date_range: str) -> dict:
    try:
        resp = requests.get(_BASE_URL, params={"sign": sign, "day": "today"}, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("data", {})
    except Exception as e:
        print(f"Warning: failed to fetch horoscope for {sign}: {e}")
        return {
            "sign": sign, "sign_thai": sign_thai, "emoji": emoji,
            "date_range": date_range, "description": "ไม่สามารถโหลดข้อมูลได้",
            "compatibility": "-", "color": "-", "lucky_number": "-",
            "lucky_time": "-", "mood": "-",
        }

    raw_desc = str(data.get("description", "")).strip()
    raw_color = str(data.get("color", "")).strip()
    raw_mood = str(data.get("mood", "")).strip()
    raw_compat = str(data.get("compatibility", "")).strip()
    raw_time = str(data.get("lucky_time", "")).strip()

    return {
        "sign": sign,
        "sign_thai": sign_thai,
        "emoji": emoji,
        "date_range": date_range,
        "description": _translate_description(raw_desc) if raw_desc else "-",
        "compatibility": _SIGN_THAI.get(raw_compat, raw_compat),
        "color": _COLOR_THAI.get(raw_color, raw_color),
        "lucky_number": str(data.get("lucky_number", "-")),
        "lucky_time": _lucky_time_thai(raw_time) if raw_time else "-",
        "mood": _MOOD_THAI.get(raw_mood, raw_mood),
    }


def fetch_horoscopes() -> list[dict]:
    return [_fetch_sign(sign, thai, emoji, date_range) for sign, thai, emoji, date_range in _SIGNS]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/aegisen/discord-sports-schedule && python -m pytest tests/test_horoscope.py -v
```

Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add fetchers/horoscope.py tests/test_horoscope.py
git commit -m "feat: add horoscope fetcher with Thai translation"
```

---

## Task 3: Add `format_horoscope()` to `formatter.py`

**Files:**
- Modify: `formatter.py`
- Modify: `tests/test_formatter.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_formatter.py`:

```python
from datetime import date
from formatter import format_horoscope

_SIGN = {
    "sign": "Aries",
    "sign_thai": "ราศีเมษ",
    "emoji": "♈",
    "date_range": "Mar 21 - Apr 19",
    "description": "วันนี้เป็นวันที่ดี",
    "compatibility": "ราศีพฤษภ",
    "color": "สีแดง",
    "lucky_number": "7",
    "lucky_time": "06:00 น.",
    "mood": "มีความสุข",
}


def test_format_horoscope_returns_list_of_dicts():
    result = format_horoscope([_SIGN], date(2026, 5, 9))
    assert isinstance(result, list)
    assert all("content" in p for p in result)


def test_format_horoscope_contains_thai_sign_name():
    result = format_horoscope([_SIGN], date(2026, 5, 9))
    combined = "\n".join(p["content"] for p in result)
    assert "ราศีเมษ" in combined


def test_format_horoscope_contains_description():
    result = format_horoscope([_SIGN], date(2026, 5, 9))
    combined = "\n".join(p["content"] for p in result)
    assert "วันนี้เป็นวันที่ดี" in combined


def test_format_horoscope_contains_date_header():
    result = format_horoscope([_SIGN], date(2026, 5, 9))
    assert "2026-05-09" in result[0]["content"]


def test_format_horoscope_splits_at_2000_chars():
    long_sign = {**_SIGN, "description": "ก" * 300}
    signs = [long_sign] * 12
    result = format_horoscope(signs, date(2026, 5, 9))
    assert all(len(p["content"]) <= 2000 for p in result)
    assert len(result) > 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/aegisen/discord-sports-schedule && python -m pytest tests/test_formatter.py -k "horoscope" -v
```

Expected: `ImportError: cannot import name 'format_horoscope' from 'formatter'`

- [ ] **Step 3: Add `format_horoscope()` to `formatter.py`**

Add import at top of `formatter.py` (already has `from datetime import date` — no change needed).

Append to end of `formatter.py`:

```python
def format_horoscope(horoscopes: list[dict], today: date) -> list[dict]:
    lines = [f"**🔮 ดวงชะตาประจำวัน — {today.isoformat()}**", ""]
    for h in horoscopes:
        lines.append(f"{h['emoji']} **{h['sign_thai']}** ({h['date_range']})")
        lines.append(h["description"])
        lines.append(
            f"💑 เข้ากันได้: {h['compatibility']} | "
            f"🎨 สี: {h['color']} | "
            f"🍀 เลขนำโชค: {h['lucky_number']} | "
            f"⏰ เวลามงคล: {h['lucky_time']} | "
            f"😊 อารมณ์: {h['mood']}"
        )
        lines.append("")
    content = "\n".join(lines).strip()
    payloads: list[dict] = []
    while content:
        if len(content) <= 2000:
            payloads.append({"content": content})
            break
        split = content.rfind("\n", 0, 2000)
        if split == -1:
            split = 2000
        payloads.append({"content": content[:split].strip()})
        content = content[split:].strip()
    return payloads
```

Also update the import line in `tests/test_formatter.py` (line 2) to include `format_horoscope`:

```python
from formatter import format_embed, format_reminder, format_kickoff, format_lottery, format_combined, format_thailottery, format_horoscope
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/aegisen/discord-sports-schedule && python -m pytest tests/test_formatter.py -v
```

Expected: all tests PASS (including the 5 new horoscope ones).

- [ ] **Step 5: Commit**

```bash
git add formatter.py tests/test_formatter.py
git commit -m "feat: add format_horoscope() to formatter"
```

---

## Task 4: Wire `--horoscope` into `main.py`

**Files:**
- Modify: `main.py`
- Modify: `tests/test_main.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_main.py`:

```python
_HOROSCOPE_SIGN = {
    "sign": "Aries", "sign_thai": "ราศีเมษ", "emoji": "♈",
    "date_range": "Mar 21 - Apr 19", "description": "วันนี้ดี",
    "compatibility": "ราศีพฤษภ", "color": "สีแดง",
    "lucky_number": "7", "lucky_time": "06:00 น.", "mood": "มีความสุข",
}
_HOROSCOPES = [_HOROSCOPE_SIGN] * 12


def test_horoscope_mode_posts_to_discord():
    with (
        patch("main.fetch_horoscopes", return_value=_HOROSCOPES),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://hook"}),
    ):
        main.main(horoscope_mode=True)
    assert mock_post.called


def test_horoscope_mode_does_not_require_football_api_key():
    with (
        patch("main.fetch_horoscopes", return_value=_HOROSCOPES),
        patch("main.post_to_webhook"),
        patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://hook"}, clear=True),
    ):
        main.main(horoscope_mode=True)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/aegisen/discord-sports-schedule && python -m pytest tests/test_main.py -k "horoscope" -v
```

Expected: `TypeError: main() got an unexpected keyword argument 'horoscope_mode'`

- [ ] **Step 3: Update `main.py`**

Add import at top of `main.py` (after existing fetcher imports):

```python
from fetchers.horoscope import fetch_horoscopes
```

Update the `format_*` import line to include `format_horoscope`:

```python
from formatter import format_embed, format_reminder, format_kickoff, format_lottery, format_combined, format_thailottery, format_horoscope
```

Add `horoscope_mode: bool = False` parameter to `main()` signature:

```python
def main(
    now_utc: datetime | None = None,
    reminder_mode: bool = False,
    kickoff_mode: bool = False,
    lottery_mode: bool = False,
    combined_mode: bool = False,
    thailottery_mode: bool = False,
    horoscope_mode: bool = False,
) -> None:
```

Add argv detection inside `main()` after the existing `if not thailottery_mode:` block:

```python
    if not horoscope_mode:
        horoscope_mode = "--horoscope" in sys.argv
```

Add horoscope handler block inside `main()` after the `if thailottery_mode:` block (before `api_key = os.environ["FOOTBALL_DATA_API_KEY"]`):

```python
    if horoscope_mode:
        horoscopes = fetch_horoscopes()
        payloads = format_horoscope(horoscopes, now_utc.date())
        for payload in payloads:
            post_to_webhook(webhook_url, payload)
        print(f"Posted horoscope ({len(horoscopes)} signs, {len(payloads)} msg).")
        return
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/aegisen/discord-sports-schedule && python -m pytest tests/test_main.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
cd /Users/aegisen/discord-sports-schedule && python -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add --horoscope mode to main"
```

---

## Task 5: Document cron schedule

**Files:**
- Modify or create: `README.md` (or wherever existing cron docs live — check with `ls *.md`)

- [ ] **Step 1: Check existing cron docs**

```bash
ls /Users/aegisen/discord-sports-schedule/*.md 2>/dev/null && grep -r "cron\|schedule\|8:00\|08:00" /Users/aegisen/discord-sports-schedule --include="*.md" -l
```

- [ ] **Step 2: Add cron entry**

Add the following cron entry to the cron section of the relevant doc (or create a `CRON.md` at the project root if no existing doc covers it):

```
# Daily horoscope at 08:00 local time
0 8 * * * cd /path/to/discord-sports-schedule && python main.py --horoscope
```

- [ ] **Step 3: Commit**

```bash
git add README.md  # or whichever file was modified
git commit -m "docs: add 8am daily horoscope cron entry"
```
