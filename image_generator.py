"""Generate sports schedule timetable image using Pillow."""
from __future__ import annotations

import io
import os
from datetime import date

from PIL import Image, ImageDraw, ImageFont

_W = 760
_PAD = 24
_ROW_H = 44
_SPORT_H = 50
_HEADER_H = 68
_SECTION_GAP = 8
_LOTTERY_HEADER_H = 46
_LOTTERY_LINE_H = 26

_BG = (30, 31, 34)
_CARD_BG = (40, 42, 48)
_ROW_ALT = (35, 36, 40)
_WHITE = (255, 255, 255)
_TEXT = (220, 221, 222)
_MUTED = (148, 155, 164)
_LOTTERY_ACCENT = (241, 167, 68)
_STOCK_ACCENT = (38, 166, 91)

_ACCENT: dict[str, tuple[int, int, int]] = {
    "Premier League": (149, 59, 237),
    "Champions League": (0, 135, 210),
    "Formula 1": (225, 6, 0),
}
_ACCENT_DEFAULT = (80, 85, 95)

_SPORT_LABELS = {
    "Premier League": "พรีเมียร์ลีก",
    "Champions League": "ยูฟ่า แชมเปียนส์ลีก",
    "Formula 1": "ฟอร์มูล่า 1",
}


def _lottery_mode_summary_lines(analysis: dict, label: str) -> list[str]:
    if analysis.get("total_draws", 0) == 0:
        return [f"{label}: ไม่มีข้อมูล"]

    latest = analysis.get("latest") or {}
    lines = [f"{label} | ผลล่าสุด: {latest.get('number', '-')}  |  {label}: {latest.get('two_digit', '??')}"]
    suggestions = analysis.get("suggestions", [])
    if suggestions:
        lines.append(f"เลขแนะนำ 5 ตัว: {'  '.join(suggestions[:5])}")
    hot = analysis.get("hot", [])
    if hot:
        lines.append("เลขร้อน: " + "  ".join(f"{item['number']} ({item['count']})" for item in hot[:5]))
    due = analysis.get("due", [])
    if due:
        lines.append("เลขค้าง: " + "  ".join(item["number"] for item in due[:5]))
    lines.append(f"วิเคราะห์จาก {analysis['total_draws']} งวด")
    return lines


def _lottery_summary_lines(analysis: dict) -> list[str]:
    if "lower" not in analysis and "upper" not in analysis:
        analysis = {"lower": analysis}

    lines: list[str] = []
    if analysis.get("lower"):
        lines.extend(_lottery_mode_summary_lines(analysis["lower"], "2 ตัวล่าง"))
    if analysis.get("upper"):
        lines.extend(_lottery_mode_summary_lines(analysis["upper"], "2 ตัวบน"))
    return lines or ["ไม่มีข้อมูลหวยลาว"]


def _stock_summary_lines(stocks: list[dict] | None) -> list[str]:
    if not stocks:
        return ["ไม่มีหุ้นแนะนำวันนี้"]
    lines = []
    for item in stocks[:3]:
        lines.append(
            f"{item['ticker']} {item['company']} | {item['consensus']} | TP ${item['price_target']:.2f} | Upside +{item['upside']:.2f}%"
        )
    return lines


def _crypto_summary_lines(crypto: list[dict] | None) -> list[str]:
    if not crypto:
        return ["ไม่มีคริปโตแนะนำวันนี้"]
    lines = []
    for item in crypto[:3]:
        lines.append(
            f"{item['symbol']} | {item['pair']} | 24h {item['change_24h']:+.2f}% | {item['quote_volume'] / 1_000_000:.1f}M USDT"
        )
    return lines


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _truncate_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    if _text_width(draw, text, font) <= max_width:
        return text
    candidate = text
    while candidate and _text_width(draw, candidate + "...", font) > max_width:
        candidate = candidate[:-1]
    return (candidate + "...") if candidate else "..."


def _font(bold: bool = False, size: int = 16):
    # Thai-capable fonts must come first — Latin-only fonts render Thai as boxes
    if bold:
        ttc_candidates = [
            ("/System/Library/Fonts/Supplemental/Thonburi.ttc", 1),
            ("/System/Library/Fonts/Supplemental/SukhumvitSet.ttc", 0),
        ]
        path_candidates = [
            "/usr/share/fonts/truetype/thai-tlwg/Garuda-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    else:
        ttc_candidates = [
            ("/System/Library/Fonts/Supplemental/Thonburi.ttc", 0),
            ("/System/Library/Fonts/Supplemental/SukhumvitSet.ttc", 0),
        ]
        path_candidates = [
            "/usr/share/fonts/truetype/thai-tlwg/Garuda.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for path, index in ttc_candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size, index=index)
    for path in path_candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_schedule_image(
    matches_by_sport: dict[str, list[dict]],
    today: date,
    lottery_analysis: dict | None = None,
    stock_recommendations: list[dict] | None = None,
    crypto_recommendations: list[dict] | None = None,
) -> bytes:
    total_rows = sum(len(m) for m in matches_by_sport.values())
    num_sports = len(matches_by_sport)
    lottery_lines = _lottery_summary_lines(lottery_analysis or {"total_draws": 0})
    stock_lines = _stock_summary_lines(stock_recommendations)
    crypto_lines = _crypto_summary_lines(crypto_recommendations)
    stock_height = _LOTTERY_HEADER_H + len(stock_lines) * _LOTTERY_LINE_H + _SECTION_GAP + _LOTTERY_LINE_H
    crypto_height = _LOTTERY_HEADER_H + len(crypto_lines) * _LOTTERY_LINE_H + _SECTION_GAP + _LOTTERY_LINE_H
    lottery_height = _LOTTERY_HEADER_H + len(lottery_lines) * _LOTTERY_LINE_H + _SECTION_GAP
    height = (
        _HEADER_H
        + _PAD
        + num_sports * (_SPORT_H + _SECTION_GAP)
        + total_rows * _ROW_H
        + lottery_height
        + stock_height
        + crypto_height
        + _PAD
    )

    img = Image.new("RGB", (_W, height), _BG)
    draw = ImageDraw.Draw(img)

    f_title = _font(bold=True, size=22)
    f_sport = _font(bold=True, size=14)
    f_match = _font(bold=False, size=14)
    f_time = _font(bold=True, size=14)
    f_sub = _font(bold=False, size=12)

    # Header
    draw.rectangle([0, 0, _W, _HEADER_H], fill=_CARD_BG)
    draw.text((_PAD, 14), "ตารางกีฬาและหวยลาว", font=f_title, fill=_WHITE)
    draw.text((_PAD, 42), f"ประจำวันที่ {today.isoformat()}", font=f_sub, fill=_MUTED)
    date_str = today.isoformat()
    bb = draw.textbbox((0, 0), date_str, font=f_sub)
    draw.text((_W - _PAD - (bb[2] - bb[0]), 28), date_str, font=f_sub, fill=_MUTED)

    y = _HEADER_H + _PAD

    for sport, matches in matches_by_sport.items():
        color = _ACCENT.get(sport, _ACCENT_DEFAULT)
        label = _SPORT_LABELS.get(sport, sport)

        # Sport header row
        draw.rectangle([0, y, _W, y + _SPORT_H], fill=_CARD_BG)
        draw.rectangle([0, y, 5, y + _SPORT_H], fill=color)
        draw.text((_PAD + 10, y + (_SPORT_H - 16) // 2), label, font=f_sport, fill=color)
        y += _SPORT_H

        for i, match in enumerate(matches):
            bg = _ROW_ALT if i % 2 == 0 else _BG
            draw.rectangle([0, y, _W, y + _ROW_H], fill=bg)
            draw.rectangle([0, y, 5, y + _ROW_H], fill=color)
            match_label = _truncate_text(draw, match.get("label", ""), f_match, _W - (_PAD * 2) - 150)
            time_str = match.get("time", "")
            draw.text((_PAD + 10, y + (_ROW_H - 14) // 2), match_label, font=f_match, fill=_TEXT)
            tbb = draw.textbbox((0, 0), time_str, font=f_time)
            draw.text((_W - _PAD - (tbb[2] - tbb[0]), y + (_ROW_H - 14) // 2), time_str, font=f_time, fill=_MUTED)
            y += _ROW_H

        y += _SECTION_GAP

    draw.rectangle([0, y, _W, y + _LOTTERY_HEADER_H], fill=_CARD_BG)
    draw.rectangle([0, y, 5, y + _LOTTERY_HEADER_H], fill=_LOTTERY_ACCENT)
    draw.text((_PAD + 10, y + 14), "หวยลาว", font=f_sport, fill=_LOTTERY_ACCENT)
    y += _LOTTERY_HEADER_H

    for i, line in enumerate(lottery_lines):
        bg = _ROW_ALT if i % 2 == 0 else _BG
        draw.rectangle([0, y, _W, y + _LOTTERY_LINE_H], fill=bg)
        draw.rectangle([0, y, 5, y + _LOTTERY_LINE_H], fill=_LOTTERY_ACCENT)
        draw.text(
            (_PAD + 10, y + 5),
            _truncate_text(draw, line, f_match, _W - (_PAD * 2) - 10),
            font=f_match,
            fill=_TEXT,
        )
        y += _LOTTERY_LINE_H

    y += _SECTION_GAP
    draw.rectangle([0, y, _W, y + _LOTTERY_HEADER_H], fill=_CARD_BG)
    draw.rectangle([0, y, 5, y + _LOTTERY_HEADER_H], fill=_STOCK_ACCENT)
    draw.text((_PAD + 10, y + 14), "หุ้นแนะนำวันนี้", font=f_sport, fill=_STOCK_ACCENT)
    y += _LOTTERY_HEADER_H

    for i, line in enumerate(stock_lines):
        bg = _ROW_ALT if i % 2 == 0 else _BG
        draw.rectangle([0, y, _W, y + _LOTTERY_LINE_H], fill=bg)
        draw.rectangle([0, y, 5, y + _LOTTERY_LINE_H], fill=_STOCK_ACCENT)
        draw.text(
            (_PAD + 10, y + 5),
            _truncate_text(draw, line, f_match, _W - (_PAD * 2) - 10),
            font=f_match,
            fill=_TEXT,
        )
        y += _LOTTERY_LINE_H

    y += 2
    draw.rectangle([0, y, _W, y + _LOTTERY_HEADER_H], fill=_CARD_BG)
    draw.rectangle([0, y, 5, y + _LOTTERY_HEADER_H], fill=(239, 83, 80))
    draw.text((_PAD + 10, y + 14), "คริปโตโมเมนตัมวันนี้", font=f_sport, fill=(239, 83, 80))
    y += _LOTTERY_HEADER_H

    for i, line in enumerate(crypto_lines):
        bg = _ROW_ALT if i % 2 == 0 else _BG
        draw.rectangle([0, y, _W, y + _LOTTERY_LINE_H], fill=bg)
        draw.rectangle([0, y, 5, y + _LOTTERY_LINE_H], fill=(239, 83, 80))
        draw.text(
            (_PAD + 10, y + 5),
            _truncate_text(draw, line, f_match, _W - (_PAD * 2) - 10),
            font=f_match,
            fill=_TEXT,
        )
        y += _LOTTERY_LINE_H

    y += 2
    draw.rectangle([0, y, _W, y + _LOTTERY_LINE_H], fill=_BG)
    draw.rectangle([0, y, 5, y + _LOTTERY_LINE_H], fill=_STOCK_ACCENT)
    disclaimer = "การลงทุนมีความเสี่ยง ควรศึกษาให้ดีก่อนตัดสินใจ"
    draw.text(
        (_PAD + 10, y + 5),
        _truncate_text(draw, disclaimer, f_match, _W - (_PAD * 2) - 10),
        font=f_match,
        fill=_MUTED,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
