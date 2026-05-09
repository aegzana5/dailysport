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
