from unittest.mock import patch, MagicMock
from datetime import date
import pytest
from fetchers.football import fetch_matches


def _mock_resp(json_data, status=200):
    mock = MagicMock()
    mock.ok = status < 400
    mock.status_code = status
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock(
        side_effect=None if status < 400 else Exception("HTTP Error")
    )
    return mock


def test_fetch_matches_returns_today_matches():
    api_resp = {
        "matches": [
            {
                "homeTeam": {"shortName": "Arsenal"},
                "awayTeam": {"shortName": "Chelsea"},
                "utcDate": "2026-05-05T19:45:00Z",
            }
        ]
    }
    with patch("fetchers.football.requests.get", return_value=_mock_resp(api_resp)):
        result = fetch_matches("fake-key", "PL", "Premier League", date(2026, 5, 5))

    assert len(result) == 1
    assert result[0]["label"] == "Arsenal vs Chelsea"
    assert result[0]["time"] == "19:45 UTC"
    assert result[0]["competition"] == "Premier League"


def test_fetch_matches_empty_when_no_matches():
    with patch(
        "fetchers.football.requests.get", return_value=_mock_resp({"matches": []})
    ):
        result = fetch_matches("fake-key", "PL", "Premier League", date(2026, 5, 5))

    assert result == []


def test_fetch_matches_empty_on_api_error():
    with patch(
        "fetchers.football.requests.get", side_effect=Exception("connection refused")
    ):
        result = fetch_matches("fake-key", "PL", "Premier League", date(2026, 5, 5))

    assert result == []


def test_fetch_matches_sends_correct_params():
    with patch(
        "fetchers.football.requests.get", return_value=_mock_resp({"matches": []})
    ) as mock_get:
        fetch_matches("my-key", "CL", "Champions League", date(2026, 5, 5))

    mock_get.assert_called_once_with(
        "https://api.football-data.org/v4/competitions/CL/matches",
        headers={"X-Auth-Token": "my-key"},
        params={"dateFrom": "2026-05-05", "dateTo": "2026-05-05"},
        timeout=10,
    )
