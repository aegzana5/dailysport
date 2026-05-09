from unittest.mock import Mock, patch

from fetchers.horoscope import fetch_horoscopes, _translate_description


def _mock_response(data: dict) -> Mock:
    resp = Mock()
    resp.raise_for_status = Mock()
    resp.json = Mock(return_value={"data": data})
    return resp


_SAMPLE_DATA = {
    "date": "2026-05-09",
    "period": "daily",
    "sign": "Aries",
    "horoscope": "Today is a great day.",
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


def test_fetch_horoscopes_translates_description():
    resp = _mock_response(_SAMPLE_DATA)
    with (
        patch("fetchers.horoscope.requests.get", return_value=resp),
        patch("fetchers.horoscope._translate_description", return_value="วันนี้ดีมาก"),
    ):
        result = fetch_horoscopes()
    aries = result[0]
    assert aries["description"] == "วันนี้ดีมาก"


def test_fetch_horoscopes_fallback_on_http_error():
    resp = Mock()
    resp.raise_for_status = Mock(side_effect=Exception("timeout"))
    with patch("fetchers.horoscope.requests.get", return_value=resp):
        result = fetch_horoscopes()
    assert len(result) == 12
    assert result[0]["description"] == "ไม่สามารถโหลดข้อมูลได้"



def test_translate_description_fallback_on_error():
    with patch("fetchers.horoscope.GoogleTranslator") as MockGT:
        MockGT.return_value.translate.side_effect = Exception("network error")
        result = _translate_description("Today is good.")
    assert result == "Today is good."
