from unittest.mock import patch, MagicMock
from datetime import date
from fetchers.f1 import fetch_sessions


def _mock_resp(json_data, status=200):
    mock = MagicMock()
    mock.ok = status < 400
    mock.status_code = status
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


def test_fetch_sessions_returns_today_sessions():
    api_resp = [
        {
            "session_name": "Qualifying",
            "country_name": "Australia",
            "circuit_short_name": "Albert Park",
            "date_start": "2026-05-05T06:00:00",
        }
    ]
    with patch("fetchers.f1.requests.get", return_value=_mock_resp(api_resp)):
        result = fetch_sessions(date(2026, 5, 5))

    assert len(result) == 1
    assert result[0]["label"] == "Australia GP — Qualifying"
    assert result[0]["time"] == "06:00 UTC"
    assert result[0]["competition"] == "Formula 1"


def test_fetch_sessions_empty_when_no_sessions():
    with patch("fetchers.f1.requests.get", return_value=_mock_resp([])):
        result = fetch_sessions(date(2026, 5, 5))

    assert result == []


def test_fetch_sessions_empty_on_api_error():
    with patch("fetchers.f1.requests.get", side_effect=Exception("timeout")):
        result = fetch_sessions(date(2026, 5, 5))

    assert result == []


def test_fetch_sessions_calls_correct_url():
    with patch(
        "fetchers.f1.requests.get", return_value=_mock_resp([])
    ) as mock_get:
        fetch_sessions(date(2026, 5, 5))

    called_url = mock_get.call_args[0][0]
    assert "date_start>=2026-05-05T00:00:00" in called_url
    assert "date_start<2026-05-06T00:00:00" in called_url
