from fetchers.laolottery_analyzer import analyze

_DRAWS = [
    {"two_digit": "41", "date": "2026-05-05", "time": "20:30", "number": "12341"},
    {"two_digit": "07", "date": "2026-05-05"},
    {"two_digit": "41", "date": "2026-05-04"}, {"two_digit": "23", "date": "2026-05-04"},
    {"two_digit": "41", "date": "2026-04-28"}, {"two_digit": "07", "date": "2026-04-28"},
    {"two_digit": "99", "date": "2026-04-27"}, {"two_digit": "41", "date": "2026-04-27"},
    {"two_digit": "55", "date": "2026-04-21"},
]


def test_total_draws():
    r = analyze(_DRAWS)
    assert r["total_draws"] == 9


def test_hot_top_number():
    r = analyze(_DRAWS)
    assert r["hot"][0]["number"] == "41"
    assert r["hot"][0]["count"] == 4


def test_latest_result_uses_newest_draw():
    r = analyze(_DRAWS)
    assert r["latest"] == {
        "date": "2026-05-05",
        "time": "20:30",
        "number": "12341",
        "two_digit": "41",
    }


def test_cold_includes_never_appeared():
    r = analyze(_DRAWS)
    cold_nums = [x["number"] for x in r["cold"]]
    assert "00" in cold_nums


def test_suggestions_are_strings():
    r = analyze(_DRAWS)
    assert all(isinstance(s, str) for s in r["suggestions"])


def test_suggestions_up_to_5():
    r = analyze(_DRAWS)
    assert len(r["suggestions"]) <= 5


def test_empty_results():
    r = analyze([])
    assert r["total_draws"] == 0
    assert r["latest"] is None
    assert r["hot"] == []
    assert r["weekly_avg"] == []


def test_due_only_includes_seen_numbers():
    r = analyze(_DRAWS)
    seen = {d["two_digit"] for d in _DRAWS}
    assert all(d["number"] in seen for d in r["due"])


def test_weekly_avg_present():
    r = analyze(_DRAWS)
    assert "weekly_avg" in r
    assert len(r["weekly_avg"]) > 0
    assert all("avg_per_week" in w for w in r["weekly_avg"])


def test_weekly_avg_top_is_most_frequent():
    r = analyze(_DRAWS)
    assert r["weekly_avg"][0]["number"] == "41"
