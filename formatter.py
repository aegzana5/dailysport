from __future__ import annotations

from datetime import date

_SPORT_ORDER = [
    ("Premier League", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "พรีเมียร์ลีก"),
    ("Champions League", "🏆", "แชมเปียนส์ลีก"),
    ("Formula 1", "🏎️", "ฟอร์มูล่า 1"),
]


def _build_lines(header: str, matches_by_sport: dict[str, list[dict]]) -> list[str]:
    lines = [header, ""]
    for competition, emoji, thai_name in _SPORT_ORDER:
        matches = matches_by_sport.get(competition, [])
        if not matches:
            continue
        lines.append(f"{emoji} **{thai_name}**")
        for m in matches:
            lines.append(f"  {m['label']} — {m['time']}")
        lines.append("")
    return lines


def format_embed(matches_by_sport: dict[str, list[dict]], today: date) -> dict:
    lines = _build_lines(f"**📅 ตารางกีฬาวันนี้ — {today.isoformat()}**", matches_by_sport)
    return {"content": "\n".join(lines).strip()}


def format_reminder(matches_by_sport: dict[str, list[dict]], today: date) -> dict:
    lines = _build_lines(f"**🔔 แจ้งเตือน — เริ่มในอีก 2 ชั่วโมง — {today.isoformat()}**", matches_by_sport)
    return {"content": "\n".join(lines).strip()}
