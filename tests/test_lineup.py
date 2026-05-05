from unittest.mock import patch, MagicMock
from fetchers.lineup import fetch_lineup


def _mock_resp(json_data, status=200):
    mock = MagicMock()
    mock.ok = status < 400
    mock.status_code = status
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


def test_fetch_lineup_returns_player_names():
    api_resp = {
        "homeTeam": {"lineup": [{"name": "Raya"}, {"name": "Saliba"}]},
        "awayTeam": {"lineup": [{"name": "Sanchez"}, {"name": "Palmer"}]},
    }
    with patch("fetchers.lineup.requests.get", return_value=_mock_resp(api_resp)):
        home, away = fetch_lineup("key", 123)

    assert home == ["Raya", "Saliba"]
    assert away == ["Sanchez", "Palmer"]


def test_fetch_lineup_returns_empty_when_not_released():
    api_resp = {"homeTeam": {"lineup": []}, "awayTeam": {"lineup": []}}
    with patch("fetchers.lineup.requests.get", return_value=_mock_resp(api_resp)):
        home, away = fetch_lineup("key", 123)

    assert home == []
    assert away == []


def test_fetch_lineup_returns_empty_on_api_error():
    with patch("fetchers.lineup.requests.get", side_effect=Exception("timeout")):
        home, away = fetch_lineup("key", 123)

    assert home == []
    assert away == []


def test_fetch_lineup_calls_correct_url():
    api_resp = {"homeTeam": {"lineup": []}, "awayTeam": {"lineup": []}}
    with patch("fetchers.lineup.requests.get", return_value=_mock_resp(api_resp)) as mock_get:
        fetch_lineup("my-key", 456)

    mock_get.assert_called_once_with(
        "https://api.football-data.org/v4/matches/456",
        headers={"X-Auth-Token": "my-key"},
        timeout=10,
    )
