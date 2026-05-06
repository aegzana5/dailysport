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


def _lottery_lines(analysis: dict, today: date) -> list[str]:
    if analysis["total_draws"] == 0:
        return [f"**🎱 หวยลาว — {today.isoformat()}**", "ไม่มีข้อมูล"]
    hot = analysis["hot"]
    cold = analysis["cold"]
    due = analysis["due"]
    weekly_avg = analysis.get("weekly_avg", [])
    suggestions = analysis["suggestions"]
    lines = [
        f"**🎱 วิเคราะห์หวยลาว (2 ตัวล่าง) — {today.isoformat()}**",
        f"จำนวนงวดในฐานข้อมูล: {analysis['total_draws']} งวด",
        "",
    ]
    if hot:
        lines.append("🔥 **เลขร้อน (ออกบ่อย)**")
        for h in hot:
            lines.append(f"  {h['number']} — {h['count']} ครั้ง")
        lines.append("")
    if cold:
        lines.append("🧊 **เลขเย็น (ออกน้อย/ไม่เคยออก)**")
        for c in cold:
            label = "ไม่เคยออก" if c["count"] == 0 else f"{c['count']} ครั้ง"
            lines.append(f"  {c['number']} — {label}")
        lines.append("")
    if weekly_avg:
        lines.append("📅 **เฉลี่ยต่อสัปดาห์**")
        for w in weekly_avg:
            lines.append(f"  {w['number']} — {w['avg_per_week']:.1f} ครั้ง/สัปดาห์")
        lines.append("")
    if due:
        lines.append("⏰ **เลขค้าง (ถึงรอบออกแล้ว)**")
        for d in due:
            lines.append(f"  {d['number']} — เฉลี่ยทุก {d['avg_gap']:.1f} งวด, ห่างมาแล้ว {d['last_seen']} งวด")
        lines.append("")
    if suggestions:
        lines.append(f"✨ **แนะนำ**: {' • '.join(suggestions)}")
    return lines


def format_lottery(analysis: dict, today: date) -> dict:
    return {"content": "\n".join(_lottery_lines(analysis, today)).strip()}


def format_combined(matches_by_sport: dict[str, list[dict]], lottery_analysis: dict, today: date) -> dict:
    sport_lines = _build_lines(f"**📅 ตารางกีฬาวันนี้ — {today.isoformat()}**", matches_by_sport)
    lottery_lines = _lottery_lines(lottery_analysis, today)
    combined = sport_lines + ["", "─" * 30, ""] + lottery_lines
    return {"content": "\n".join(combined).strip()}
