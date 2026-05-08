from datetime import date

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
