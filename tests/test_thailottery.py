from datetime import date
from unittest.mock import MagicMock, patch

import fetchers.thailottery as _mod
from fetchers.thailottery import _latest_draw_date, _prev_draw_date, _parse_sanook_page, _page_url


def test_latest_draw_date_mid_month():
    assert _latest_draw_date(date(2025, 5, 10)) == date(2025, 5, 1)


def test_latest_draw_date_after_16():
    assert _latest_draw_date(date(2025, 5, 20)) == date(2025, 5, 16)


def test_latest_draw_date_on_16():
    assert _latest_draw_date(date(2025, 5, 16)) == date(2025, 5, 16)


def test_latest_draw_date_on_1():
    assert _latest_draw_date(date(2025, 5, 1)) == date(2025, 5, 1)


def test_latest_draw_date_day_2():
    assert _latest_draw_date(date(2025, 5, 2)) == date(2025, 5, 1)


def test_prev_draw_date_from_16():
    assert _prev_draw_date(date(2025, 5, 16)) == date(2025, 5, 1)


def test_prev_draw_date_from_1():
    assert _prev_draw_date(date(2025, 5, 1)) == date(2025, 4, 16)


def test_prev_draw_date_jan_1():
    assert _prev_draw_date(date(2025, 1, 1)) == date(2024, 12, 16)


def test_parse_sanook_page_success():
    html = "<div>รางวัลที่ 1</div><div>123456</div>"
    result = _parse_sanook_page(html)
    assert result == {"prize1": "123456", "two_digit": "56"}


def test_parse_sanook_page_two_digit_from_prize():
    html = "<span>รางวัลที่ 1</span><span>009900</span>"
    result = _parse_sanook_page(html)
    assert result["two_digit"] == "00"


def test_parse_sanook_page_no_match():
    html = "<div>ไม่มีผลสลาก</div>"
    assert _parse_sanook_page(html) is None


def test_parse_sanook_page_ignores_non_six_digit():
    html = "<div>รางวัลที่ 1</div><div>999</div><div>123456</div>"
    result = _parse_sanook_page(html)
    assert result["prize1"] == "123456"


def test_page_url_format():
    assert _page_url(date(2025, 12, 16)) == "https://news.sanook.com/lotto/check/20251216/"
    assert _page_url(date(2025, 1, 1)) == "https://news.sanook.com/lotto/check/20250101/"


def _make_mock_resp(html: str, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.apparent_encoding = "utf-8"
    resp.text = html
    return resp


def test_fetch_results_returns_list():
    html = "<div>รางวัลที่ 1</div><div>123456</div>"
    with (
        patch.object(_mod, "_DRAW_LIMIT", 3),
        patch("fetchers.thailottery.requests.get", return_value=_make_mock_resp(html)),
        patch("fetchers.thailottery._latest_draw_date", return_value=date(2025, 12, 16)),
    ):
        results = _mod.fetch_results()
    assert len(results) == 3
    assert results[0]["prize1"] == "123456"
    assert results[0]["two_digit"] == "56"
    assert "date" in results[0]


def test_fetch_results_skips_404():
    html = "<div>รางวัลที่ 1</div><div>111111</div>"
    responses = [
        _make_mock_resp("", status=404),
        _make_mock_resp(html),
        _make_mock_resp(html),
        _make_mock_resp(html),
    ]
    with (
        patch.object(_mod, "_DRAW_LIMIT", 3),
        patch("fetchers.thailottery.requests.get", side_effect=responses),
        patch("fetchers.thailottery._latest_draw_date", return_value=date(2025, 12, 16)),
    ):
        results = _mod.fetch_results()
    assert len(results) == 3


def test_fetch_results_skips_unparseable():
    good_html = "<div>รางวัลที่ 1</div><div>999999</div>"
    responses = [
        _make_mock_resp("<div>no prize here</div>"),
        _make_mock_resp(good_html),
        _make_mock_resp(good_html),
        _make_mock_resp(good_html),
    ]
    with (
        patch.object(_mod, "_DRAW_LIMIT", 3),
        patch("fetchers.thailottery.requests.get", side_effect=responses),
        patch("fetchers.thailottery._latest_draw_date", return_value=date(2025, 12, 16)),
    ):
        results = _mod.fetch_results()
    assert len(results) == 3
    assert all(r["prize1"] == "999999" for r in results)


def test_fetch_results_returns_empty_on_exception():
    with patch("fetchers.thailottery.requests.get", side_effect=Exception("network error")):
        results = _mod.fetch_results()
    assert results == []
