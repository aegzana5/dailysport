from fetchers.laolottery_analyzer import analyze

_DRAWS = [
    {"two_digit": "41"}, {"two_digit": "07"}, {"two_digit": "41"},
    {"two_digit": "23"}, {"two_digit": "41"}, {"two_digit": "07"},
    {"two_digit": "99"}, {"two_digit": "41"}, {"two_digit": "55"},
]


def test_total_draws():
    r = analyze(_DRAWS)
    assert r["total_draws"] == 9


def test_hot_top_number():
    r = analyze(_DRAWS)
    assert r["hot"][0]["number"] == "41"
    assert r["hot"][0]["count"] == 4


def test_cold_includes_never_appeared():
    r = analyze(_DRAWS)
    cold_nums = [x["number"] for x in r["cold"]]
    assert "00" in cold_nums  # never appeared


def test_suggestions_are_strings():
    r = analyze(_DRAWS)
    assert all(isinstance(s, str) for s in r["suggestions"])


def test_empty_results():
    r = analyze([])
    assert r["total_draws"] == 0
    assert r["hot"] == []


def test_due_only_includes_seen_numbers():
    r = analyze(_DRAWS)
    seen = {d["two_digit"] for d in _DRAWS}
    assert all(d["number"] in seen for d in r["due"])
