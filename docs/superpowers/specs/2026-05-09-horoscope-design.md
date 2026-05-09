---
name: Daily Horoscope Feature
description: Add daily Western zodiac horoscope (all 12 signs, detailed) fetched from free API, posted to Discord at 8:00 AM via standalone --horoscope mode
type: project
---

# Daily Horoscope Feature

## Overview

Add a standalone `--horoscope` mode that fetches detailed daily Western zodiac horoscopes for all 12 signs from a free public API and posts them to Discord at 8:00 AM daily.

## Data Source

**API:** `https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily`
- No API key required
- Query params: `sign=<Sign>&day=today`
- Returns JSON: `date_range`, `current_date`, `description`, `compatibility`, `color`, `lucky_number`, `lucky_time`, `mood`
- 12 sequential calls, one per sign

**Signs (in order):** Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces

## Translation Strategy

Fixed fields (`color`, `mood`, `compatibility`, `lucky_time`) use hardcoded Thai dicts in `fetchers/horoscope.py`. Unmapped values fall back to original English.

`description` (free-form daily text) translated via `deep_translator` library using Google Translate backend — no API key required, ~12 extra HTTP calls.

Dependency: add `deep_translator` to `requirements.txt`.

## Architecture

### New file: `fetchers/horoscope.py`

Single public function:
```python
def fetch_horoscopes() -> list[dict]
```
Returns list of 12 dicts, one per sign:
```python
{
    "sign": "Aries",
    "sign_thai": "ราศีเมษ",
    "emoji": "♈",
    "date_range": "Mar 21 - Apr 19",
    "description": "...",          # translated Thai via deep_translator
    "compatibility": "ราศีพฤษภ",  # hardcoded Thai dict
    "color": "สีแดง",              # hardcoded Thai dict
    "lucky_number": "7",           # numeric, no translation
    "lucky_time": "06:00",         # normalised Thai format
    "mood": "มีความสุข",           # hardcoded Thai dict
}
```
On HTTP error for a sign: return partial dict with `description: "ไม่สามารถโหลดข้อมูลได้"`.
On translation failure: keep original English text.

### Modified: `formatter.py`

Add `format_horoscope(horoscopes: list[dict], today: date) -> list[dict]`.

Output format per sign:
```
♈ **ราศีเมษ** (Mar 21 - Apr 19)
<Thai description text>
💑 เข้ากันได้: ราศีพฤษภ | 🎨 สี: สีแดง | 🍀 เลขนำโชค: 7 | ⏰ เวลามงคล: 06:00 | 😊 อารมณ์: มีความสุข

```

Header: `**🔮 ดวงชะตาประจำวัน — <date>**`

Returns `list[dict]` (multiple `{"content": ...}` payloads), splitting at 2000-char boundary on newline — same logic as `format_combined`.

### Modified: `main.py`

Add `horoscope_mode` parameter and `--horoscope` argv flag. When active:
1. Call `fetch_horoscopes()`
2. Call `format_horoscope(horoscopes, today)`
3. Loop `post_to_webhook(webhook_url, payload)` for each payload
4. Print count of signs posted

No `FOOTBALL_DATA_API_KEY` or `ODDS_API_KEY` required for this mode.

## Scheduling

Add cron entry (08:00 local time) to run:
```bash
python main.py --horoscope
```
Document in README alongside existing cron entries.

## Sign Thai Name Mapping

| Sign | Thai | Emoji |
|------|------|-------|
| Aries | ราศีเมษ | ♈ |
| Taurus | ราศีพฤษภ | ♉ |
| Gemini | ราศีเมถุน | ♊ |
| Cancer | ราศีกรกฎ | ♋ |
| Leo | ราศีสิงห์ | ♌ |
| Virgo | ราศีกันย์ | ♍ |
| Libra | ราศีตุลย์ | ♎ |
| Scorpio | ราศีพิจิก | ♏ |
| Sagittarius | ราศีธนู | ♐ |
| Capricorn | ราศีมังกร | ♑ |
| Aquarius | ราศีกุมภ์ | ♒ |
| Pisces | ราศีมีน | ♓ |

## Error Handling

- Per-sign HTTP failure: insert placeholder text, continue other signs
- All signs fail: post single message "ไม่สามารถโหลดดวงได้ในขณะนี้"
- Timeout: 10s per request

## Testing

Add `tests/test_horoscope.py`:
- Mock HTTP responses, verify 12-sign output shape
- Test format split at 2000-char boundary
- Test per-sign error fallback

## Files Changed

| File | Change |
|------|--------|
| `fetchers/horoscope.py` | New — fetcher + translation |
| `formatter.py` | Add `format_horoscope()` |
| `main.py` | Add `--horoscope` mode |
| `requirements.txt` | Add `deep_translator` |
| `tests/test_horoscope.py` | New — tests |
