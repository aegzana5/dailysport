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

_BG = (30, 31, 34)
_CARD_BG = (40, 42, 48)
_ROW_ALT = (35, 36, 40)
_WHITE = (255, 255, 255)
_TEXT = (220, 221, 222)
_MUTED = (148, 155, 164)

_ACCENT: dict[str, tuple[int, int, int]] = {
    "Premier League": (149, 59, 237),
    "Champions League": (0, 135, 210),
    "Formula 1": (225, 6, 0),
}
_ACCENT_DEFAULT = (80, 85, 95)

_SPORT_LABELS = {
    "Premier League": "PREMIER LEAGUE",
    "Champions League": "CHAMPIONS LEAGUE",
    "Formula 1": "FORMULA 1",
}


def _font(bold: bool = False, size: int = 16):
    paths = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    )
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_schedule_image(matches_by_sport: dict[str, list[dict]], today: date) -> bytes:
    total_rows = sum(len(m) for m in matches_by_sport.values())
    num_sports = len(matches_by_sport)
    height = _HEADER_H + _PAD + num_sports * (_SPORT_H + 8) + total_rows * _ROW_H + _PAD

    img = Image.new("RGB", (_W, height), _BG)
    draw = ImageDraw.Draw(img)

    f_title = _font(bold=True, size=22)
    f_sport = _font(bold=True, size=14)
    f_match = _font(bold=False, size=14)
    f_time = _font(bold=True, size=14)
    f_sub = _font(bold=False, size=12)

    # Header
    draw.rectangle([0, 0, _W, _HEADER_H], fill=_CARD_BG)
    draw.text((_PAD, 14), "Sports Schedule", font=f_title, fill=_WHITE)
    draw.text((_PAD, 42), today.strftime("%A  ·  %d %B %Y"), font=f_sub, fill=_MUTED)
    date_str = today.isoformat()
    bb = draw.textbbox((0, 0), date_str, font=f_sub)
    draw.text((_W - _PAD - (bb[2] - bb[0]), 28), date_str, font=f_sub, fill=_MUTED)

    y = _HEADER_H + _PAD

    for sport, matches in matches_by_sport.items():
        color = _ACCENT.get(sport, _ACCENT_DEFAULT)
        label = _SPORT_LABELS.get(sport, sport.upper())

        # Sport header row
        draw.rectangle([0, y, _W, y + _SPORT_H], fill=_CARD_BG)
        draw.rectangle([0, y, 5, y + _SPORT_H], fill=color)
        draw.text((_PAD + 10, y + (_SPORT_H - 16) // 2), label, font=f_sport, fill=color)
        y += _SPORT_H

        for i, match in enumerate(matches):
            bg = _ROW_ALT if i % 2 == 0 else _BG
            draw.rectangle([0, y, _W, y + _ROW_H], fill=bg)
            draw.rectangle([0, y, 5, y + _ROW_H], fill=color)
            match_label = match.get("label", "")
            time_str = match.get("time", "")
            draw.text((_PAD + 10, y + (_ROW_H - 14) // 2), match_label, font=f_match, fill=_TEXT)
            tbb = draw.textbbox((0, 0), time_str, font=f_time)
            draw.text((_W - _PAD - (tbb[2] - tbb[0]), y + (_ROW_H - 14) // 2), time_str, font=f_time, fill=_MUTED)
            y += _ROW_H

        y += 8

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
