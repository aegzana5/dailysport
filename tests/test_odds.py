from unittest.mock import patch, MagicMock
from fetchers.odds import fetch_handicap


def _mock_resp(json_data, status=200):
    mock = MagicMock()
    mock.ok = status < 400
    mock.status_code = status
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


_ODDS_RESP = [
    {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "bookmakers": [
            {
                "key": "bet365",
                "title": "Bet365",
                "markets": [
                    {
                        "key": "asian_handicap",
                        "outcomes": [
                            {"name": "Arsenal", "point": -0.5, "price": 1.90},
                            {"name": "Chelsea", "point": 0.5, "price": 1.90},
                        ],
                    }
                ],
            }
        ],
    }
]


def test_fetch_handicap_returns_correct_data():
    with patch("fetchers.odds.requests.get", return_value=_mock_resp(_ODDS_RESP)):
        result = fetch_handicap("key", "Premier League", "Arsenal", "Chelsea")

    assert result is not None
    assert result["bookmaker"] == "Bet365"
    assert result["home"]["point"] == -0.5
    assert result["home"]["price"] == 1.90
    assert result["away"]["point"] == 0.5


def test_fetch_handicap_returns_none_for_unknown_competition():
    result = fetch_handicap("key", "Bundesliga", "Bayern", "Dortmund")
    assert result is None


def test_fetch_handicap_returns_none_when_no_match_found():
    with patch("fetchers.odds.requests.get", return_value=_mock_resp(_ODDS_RESP)):
        result = fetch_handicap("key", "Premier League", "Liverpool", "City")

    assert result is None


def test_fetch_handicap_returns_none_on_api_error():
    with patch("fetchers.odds.requests.get", side_effect=Exception("timeout")):
        result = fetch_handicap("key", "Premier League", "Arsenal", "Chelsea")

    assert result is None
