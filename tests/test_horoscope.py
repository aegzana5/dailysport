from unittest.mock import Mock, patch

from fetchers.horoscope import fetch_horoscopes, _lucky_time_thai, _translate_description


def _mock_response(data: dict) -> Mock:
    resp = Mock()
    resp.raise_for_status = Mock()
    resp.json = Mock(return_value={"data": data})
    return resp


_SAMPLE_DATA = {
    "date_range": "Mar 21 - Apr 19",
    "current_date": "May 9, 2026",
    "description": "Today is a great day.",
    "compatibility": "Taurus",
    "color": "Red",
    "lucky_number": "7",
    "lucky_time": "6am",
    "mood": "Happy",
}


def test_fetch_horoscopes_returns_12_signs():
    resp = _mock_response(_SAMPLE_DATA)
    with (
        patch("fetchers.horoscope.requests.get", return_value=resp),
        patch("fetchers.horoscope._translate_description", return_value="วันนี้ดีมาก"),
    ):
        result = fetch_horoscopes()
    assert len(result) == 12


def test_fetch_horoscopes_first_sign_is_aries():
    resp = _mock_response(_SAMPLE_DATA)
    with (
        patch("fetchers.horoscope.requests.get", return_value=resp),
        patch("fetchers.horoscope._translate_description", return_value="วันนี้ดีมาก"),
    ):
        result = fetch_horoscopes()
    assert result[0]["sign"] == "Aries"
    assert result[0]["sign_thai"] == "ราศีเมษ"
    assert result[0]["emoji"] == "♈"


def test_fetch_horoscopes_translates_fixed_fields():
    resp = _mock_response(_SAMPLE_DATA)
    with (
        patch("fetchers.horoscope.requests.get", return_value=resp),
        patch("fetchers.horoscope._translate_description", return_value="วันนี้ดีมาก"),
    ):
        result = fetch_horoscopes()
    aries = result[0]
    assert aries["color"] == "สีแดง"
    assert aries["mood"] == "มีความสุข"
    assert aries["compatibility"] == "ราศีพฤษภ"
    assert aries["lucky_time"] == "06:00 น."
    assert aries["lucky_number"] == "7"
    assert aries["description"] == "วันนี้ดีมาก"


def test_fetch_horoscopes_fallback_on_http_error():
    resp = Mock()
    resp.raise_for_status = Mock(side_effect=Exception("timeout"))
    with patch("fetchers.horoscope.requests.get", return_value=resp):
        result = fetch_horoscopes()
    assert len(result) == 12
    assert result[0]["description"] == "ไม่สามารถโหลดข้อมูลได้"


def test_lucky_time_thai_am():
    assert _lucky_time_thai("6am") == "06:00 น."


def test_lucky_time_thai_pm():
    assert _lucky_time_thai("3pm") == "15:00 น."


def test_lucky_time_thai_noon():
    assert _lucky_time_thai("12pm") == "12:00 น."


def test_lucky_time_thai_midnight():
    assert _lucky_time_thai("12am") == "00:00 น."


def test_lucky_time_thai_unknown_passthrough():
    assert _lucky_time_thai("evening") == "evening"


def test_translate_description_fallback_on_error():
    with patch("fetchers.horoscope.GoogleTranslator") as MockGT:
        MockGT.return_value.translate.side_effect = Exception("network error")
        result = _translate_description("Today is good.")
    assert result == "Today is good."
