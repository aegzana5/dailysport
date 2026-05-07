from datetime import date
from formatter import format_embed, format_reminder, format_kickoff, format_lottery, format_combined

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


def test_format_kickoff_includes_lineup_and_handicap():
    event = {
        "competition": "Premier League",
        "label": "Arsenal vs Chelsea",
        "time": "02:45 ICT",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "home_lineup": ["Raya", "White", "Saliba"],
        "away_lineup": ["Sanchez", "Gusto", "Chalobah"],
        "handicap": {
            "bookmaker": "Bet365",
            "home": {"name": "Arsenal", "point": -0.5, "price": 1.90},
            "away": {"name": "Chelsea", "point": 0.5, "price": 1.90},
        },
    }
    result = format_kickoff([event], date(2026, 5, 5))
    content = result["content"]
    assert "เตะในอีก 30 นาที" in content
    assert "Arsenal vs Chelsea" in content
    assert "Raya" in content
    assert "Sanchez" in content
    assert "แฮนดิแคป" in content
    assert "Bet365" in content
    assert "-0.5" in content


def test_format_kickoff_shows_no_lineup_message_when_empty():
    event = {
        "competition": "Premier League",
        "label": "Arsenal vs Chelsea",
        "time": "02:45 ICT",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "home_lineup": [],
        "away_lineup": [],
        "handicap": None,
    }
    result = format_kickoff([event], date(2026, 5, 5))
    assert "ยังไม่ประกาศไลน์อัพ" in result["content"]


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


_LOTTERY_ANALYSIS = {
    "total_draws": 10,
    "latest": {"date": "2026-05-06", "time": "20:30", "number": "12341", "two_digit": "41"},
    "hot": [{"number": "41", "count": 4}, {"number": "07", "count": 2}],
    "cold": [{"number": "00", "count": 0}],
    "due": [{"number": "23", "avg_gap": 3.0, "last_seen": 5}],
    "weekly_avg": [{"number": "41", "count": 4, "avg_per_week": 1.3}],
    "suggestions": ["41", "07", "23", "55", "99"],
}


def test_format_lottery_shows_hot_cold_suggestions():
    result = format_lottery(_LOTTERY_ANALYSIS, date(2026, 5, 6))
    content = result["content"]
    assert "หวยลาว" in content
    assert "2 ตัวบน" in content
    assert "ผลล่าสุด" in content
    assert "12341" in content
    assert "41" in content
    assert "00" in content
    assert "ไม่เคยออก" in content
    assert "41 • 07 • 23 • 55 • 99" in content


def test_format_lottery_shows_weekly_avg():
    result = format_lottery(_LOTTERY_ANALYSIS, date(2026, 5, 6))
    assert "เฉลี่ยต่อสัปดาห์" in result["content"]
    assert "1.3" in result["content"]


def test_format_lottery_empty():
    analysis = {"total_draws": 0, "latest": None, "hot": [], "cold": [], "due": [], "weekly_avg": [], "suggestions": []}
    result = format_lottery(analysis, date(2026, 5, 6))
    assert "ไม่มีข้อมูล" in result["content"]


def test_format_combined_includes_sport_and_lottery():
    result = format_combined({"Premier League": _PL}, _LOTTERY_ANALYSIS, date(2026, 5, 6))
    content = result["content"]
    assert "ตารางกีฬาวันนี้" in content
    assert "Arsenal vs Chelsea" in content
    assert "หวยลาว" in content
    assert "41" in content
