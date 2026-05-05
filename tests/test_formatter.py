from datetime import date
from formatter import format_embed, format_reminder

_PL = [{"label": "Arsenal vs Chelsea", "time": "19:45 UTC", "competition": "Premier League"}]
_UCL = [{"label": "PSG vs Barcelona", "time": "20:00 UTC", "competition": "Champions League"}]
_F1 = [{"label": "Australia GP — Race", "time": "06:00 UTC", "competition": "Formula 1"}]


def test_includes_all_sports_with_matches():
    result = format_embed(
        {"Premier League": _PL, "Champions League": _UCL, "Formula 1": _F1},
        date(2026, 5, 5),
    )
    content = result["content"]
    assert "Arsenal vs Chelsea" in content
    assert "PSG vs Barcelona" in content
    assert "Australia GP — Race" in content


def test_skips_sport_with_no_matches():
    result = format_embed({"Premier League": _PL}, date(2026, 5, 5))
    content = result["content"]
    assert "แชมเปียนส์ลีก" not in content
    assert "ฟอร์มูล่า 1" not in content


def test_includes_date_in_header():
    result = format_embed({"Premier League": _PL}, date(2026, 5, 5))
    assert "2026-05-05" in result["content"]


def test_returns_dict_with_content_key():
    result = format_embed({"Premier League": _PL}, date(2026, 5, 5))
    assert "content" in result
    assert isinstance(result["content"], str)


def test_format_reminder_includes_thai_alert_header():
    result = format_reminder({"Premier League": _PL}, date(2026, 5, 5))
    assert "แจ้งเตือน" in result["content"]
    assert "Arsenal vs Chelsea" in result["content"]


def test_multiple_matches_same_sport():
    pl_two = [
        {"label": "Arsenal vs Chelsea", "time": "14:00 UTC", "competition": "Premier League"},
        {"label": "Liverpool vs City", "time": "16:30 UTC", "competition": "Premier League"},
    ]
    result = format_embed({"Premier League": pl_two}, date(2026, 5, 5))
    content = result["content"]
    assert "Arsenal vs Chelsea" in content
    assert "Liverpool vs City" in content
