from fetchers.thailottery_analyzer import analyze

_DRAWS = [
    {"date": "2025-12-16", "prize1": "123456", "two_digit": "56"},
    {"date": "2025-12-01", "prize1": "654321", "two_digit": "21"},
    {"date": "2025-11-16", "prize1": "111156", "two_digit": "56"},
    {"date": "2025-11-01", "prize1": "222256", "two_digit": "56"},
    {"date": "2025-10-16", "prize1": "333321", "two_digit": "21"},
]


def test_total_draws():
    r = analyze(_DRAWS)
    assert r["total_draws"] == 5


def test_hot_top_number():
    r = analyze(_DRAWS)
    assert r["hot"][0]["number"] == "56"
    assert r["hot"][0]["count"] == 3


def test_latest_is_newest():
    r = analyze(_DRAWS)
    assert r["latest"]["prize1"] == "123456"
    assert r["latest"]["two_digit"] == "56"
    assert r["latest"]["date"] == "2025-12-16"


def test_cold_includes_never_appeared():
    r = analyze(_DRAWS)
    cold_nums = [x["number"] for x in r["cold"]]
    assert "00" in cold_nums


def test_monthly_avg_present():
    r = analyze(_DRAWS)
    assert "monthly_avg" in r
    assert len(r["monthly_avg"]) > 0
    assert all("avg_per_month" in w for w in r["monthly_avg"])


def test_monthly_avg_denominator():
    # 3 unique months (Oct, Nov, Dec). "56" appears 3 times → 3/3 = 1.0
    r = analyze(_DRAWS)
    top = r["monthly_avg"][0]
    assert top["number"] == "56"
    assert top["avg_per_month"] == 1.0


def test_suggestions_are_strings():
    r = analyze(_DRAWS)
    assert all(isinstance(s, str) for s in r["suggestions"])


def test_suggestions_max_5():
    r = analyze(_DRAWS)
    assert len(r["suggestions"]) <= 5


def test_empty_results():
    r = analyze([])
    assert r["total_draws"] == 0
    assert r["latest"] is None
    assert r["hot"] == []
    assert r["monthly_avg"] == []
    assert r["suggestions"] == []


def test_due_only_has_seen_numbers():
    r = analyze(_DRAWS)
    seen = {"56", "21"}
    assert all(d["number"] in seen for d in r["due"])
