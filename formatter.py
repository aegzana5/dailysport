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
    lines = [f"**⚽ เตะในอีก 30 นาที — {today.isoformat()}**", ""]
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


def _lottery_mode_lines(analysis: dict, label: str) -> list[str]:
    if analysis["total_draws"] == 0:
        return [f"**{label}**", "ไม่มีข้อมูล", ""]
    hot = analysis["hot"]
    cold = analysis["cold"]
    due = analysis["due"]
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
    suggestions = analysis["suggestions"]
    lines = [
        f"**{label}**",
        f"จำนวนงวดในฐานข้อมูล: {analysis['total_draws']} งวด",
    ]
    latest = analysis.get("latest")
    if latest:
        latest_details = []
        if latest.get("date"):
            latest_details.append(latest["date"])
        if latest.get("time"):
            latest_details.append(latest["time"])
        suffix = f" — {' '.join(latest_details)}" if latest_details else ""
        recent = analysis.get("recent_two_digits")
        if recent:
            lines.append(f"🎯 **ผลล่าสุด 5 งวด**: {' • '.join(recent[:5])}{suffix}")
        else:
            prize_num = latest.get("number") or latest.get("prize1") or "-"
            lines.append(f"🎯 **ผลล่าสุด**: {prize_num} ({label} {latest.get('two_digit') or '??'}){suffix}")
    lines.append("")
    if hot:
        lines.append("🔥 **เลขร้อน (ออกบ่อย)**")
        for h in hot:
            lines.append(f"  {h['number']} — {h['count']} ครั้ง")
        lines.append("")
    if cold:
        lines.append("🧊 **เลขเย็น (ออกน้อย/ไม่เคยออก)**")
        for c in cold:
            cold_label = "ไม่เคยออก" if c["count"] == 0 else f"{c['count']} ครั้ง"
            lines.append(f"  {c['number']} — {cold_label}")
        lines.append("")
    if avg_data:
        lines.append(avg_header)
        for w in avg_data:
            lines.append(f"  {w['number']} — {w[avg_val_key]:.1f} {avg_unit}")
        lines.append("")
    if due:
        lines.append("⏰ **เลขค้าง (ถึงรอบออกแล้ว)**")
        for d in due:
            lines.append(f"  {d['number']} — เฉลี่ยทุก {d['avg_gap']:.1f} งวด, ห่างมาแล้ว {d['last_seen']} งวด")
        lines.append("")
    if suggestions:
        lines.append(f"✨ **แนะนำ**: {' • '.join(suggestions)}")
    lines.append("")
    return lines


def _lottery_lines(analysis: dict, today: date) -> list[str]:
    if "lower" not in analysis and "upper" not in analysis:
        analysis = {"lower": analysis}

    if not analysis.get("lower") and not analysis.get("upper"):
        return [f"**🎱 หวยลาว — {today.isoformat()}**", "ไม่มีข้อมูล"]

    lines = [f"**🎱 วิเคราะห์หวยลาว — {today.isoformat()}**", ""]
    if analysis.get("lower"):
        lines.extend(_lottery_mode_lines(analysis["lower"], "2 ตัวล่าง"))
    if analysis.get("upper"):
        lines.extend(_lottery_mode_lines(analysis["upper"], "2 ตัวบน"))
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def format_lottery(analysis: dict, today: date) -> dict:
    return {"content": "\n".join(_lottery_lines(analysis, today)).strip()}


def format_thailottery(analysis: dict, today: date) -> dict:
    if not analysis.get("total_draws"):
        lines = [f"**🎰 วิเคราะห์หวยไทย — {today.isoformat()}**", "ไม่มีข้อมูล"]
    else:
        lines = [f"**🎰 วิเคราะห์หวยไทย — {today.isoformat()}**", ""]
        lines.extend(_lottery_mode_lines(analysis, "2 ตัวล่าง"))
    while lines and lines[-1] == "":
        lines.pop()
    return {"content": "\n".join(lines).strip()}


def _stock_lines(stocks: list[dict]) -> list[str]:
    if not stocks:
        return []
    lines = ["**📈 หุ้นแนะนำ**", ""]
    for s in stocks:
        lines.append(f"  **{s['ticker']}** — {s['consensus']} — เป้า ${s['price_target']:,.0f} ({s['upside']:+.1f}%)")
    lines.append("")
    return lines


def _crypto_lines(cryptos: list[dict]) -> list[str]:
    if not cryptos:
        return []
    lines = ["**🪙 คริปโต**", ""]
    for c in cryptos:
        lines.append(f"  **{c['symbol']}** — ${c['price']:,.2f} — {c['change_24h']:+.1f}% (24h)")
    lines.append("")
    return lines


def _lottery_compact_lines(analysis: dict, today: date) -> list[str]:
    lines = [f"**🎱 หวยลาว — {today.isoformat()}**", ""]
    for key, label in (("lower", "2 ตัวล่าง"), ("upper", "2 ตัวบน")):
        mode = analysis.get(key, {})
        if not mode or not mode.get("total_draws"):
            continue
        recent = mode.get("recent_two_digits") or []
        suggestions = mode.get("suggestions") or []
        parts_line = []
        if recent:
            parts_line.append(f"ล่าสุด: {' • '.join(recent[:5])}")
        if suggestions:
            parts_line.append(f"แนะนำ: {' • '.join(suggestions)}")
        lines.append(f"**{label}** — " + " | ".join(parts_line) if parts_line else f"**{label}**")
    lines.append("")
    return lines


def format_combined(
    matches_by_sport: dict[str, list[dict]],
    lottery_analysis: dict,
    stock_recommendations: list[dict],
    crypto_recommendations: list[dict],
    today: date,
) -> list[dict]:
    sep = ["", "─" * 30, ""]
    parts: list[str] = []
    parts += _build_lines(f"**📅 ตารางกีฬาและหวยลาว — {today.isoformat()}**", matches_by_sport)
    parts += sep + _stock_lines(stock_recommendations)
    parts += sep + _crypto_lines(crypto_recommendations)
    parts += sep + _lottery_compact_lines(lottery_analysis, today)
    content = "\n".join(parts).strip()
    # split at 2000-char boundary on newline
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
