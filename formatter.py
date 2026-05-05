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


def format_kickoff(kickoff_events: list[dict], today: date) -> dict:
    _emoji = {c: e for c, e, _ in _SPORT_ORDER}
    _thai = {c: t for c, _, t in _SPORT_ORDER}
    lines = [f"**⚽ เตะในอีก 1 ชั่วโมง — {today.isoformat()}**", ""]
    for ev in kickoff_events:
        comp = ev["competition"]
        emoji = _emoji.get(comp, "⚽")
        thai = _thai.get(comp, comp)
        lines.append(f"{emoji} **{thai}** — {ev['label']} — {ev['time']}")
        handicap = ev.get("handicap")
        if handicap:
            h, a = handicap["home"], handicap["away"]
            pt_h = f"{h['point']:+.1f}".replace("+0.0", "0").replace("-0.0", "0")
            pt_a = f"{a['point']:+.1f}".replace("+0.0", "0").replace("-0.0", "0")
            lines.append(
                f"🎯 **แฮนดิแคป** ({handicap['bookmaker']}): "
                f"{h['name']} {pt_h} @ {h['price']:.2f} | {a['name']} {pt_a} @ {a['price']:.2f}"
            )
        home_lu = ev.get("home_lineup", [])
        away_lu = ev.get("away_lineup", [])
        home_name = ev.get("home_team", "Home")
        away_name = ev.get("away_team", "Away")
        lines.append(
            f"👕 **{home_name}**: {' • '.join(home_lu[:11]) if home_lu else 'ยังไม่ประกาศไลน์อัพ'}"
        )
        lines.append(
            f"👕 **{away_name}**: {' • '.join(away_lu[:11]) if away_lu else 'ยังไม่ประกาศไลน์อัพ'}"
        )
        lines.append("")
    return {"content": "\n".join(lines).strip()}
