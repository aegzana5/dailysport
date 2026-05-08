from datetime import date

from fetchers.thailottery import _latest_draw_date, _prev_draw_date


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
