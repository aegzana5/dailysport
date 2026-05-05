from __future__ import annotations

from datetime import date

_SPORT_ORDER = [
    ("Premier League", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("Champions League", "🏆"),
    ("Formula 1", "🏎️"),
]


def format_embed(matches_by_sport: dict[str, list[dict]], today: date) -> dict:
    lines = [f"**📅 Today's Sports Schedule — {today.isoformat()}**\n"]
    for competition, emoji in _SPORT_ORDER:
        matches = matches_by_sport.get(competition, [])
        if not matches:
            continue
        lines.append(f"{emoji} **{competition}**")
        for m in matches:
            lines.append(f"  {m['label']} — {m['time']}")
        lines.append("")
    return {"content": "\n".join(lines).strip()}
