from unittest.mock import patch
from datetime import datetime, timezone
import pytest
import main  # import at module level so patch("main.X") works


_ENV = {"FOOTBALL_DATA_API_KEY": "key", "DISCORD_WEBHOOK_URL": "https://hook"}
_MATCH_DT = datetime(2026, 5, 5, 19, 45, tzinfo=timezone.utc)


def test_no_matches_skips_discord_post():
    with (
        patch("main.fetch_matches", return_value=[]),
        patch("main.fetch_sessions", return_value=[]),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main()
        mock_post.assert_not_called()


def test_pl_matches_triggers_discord_post():
    pl = [{"label": "Arsenal vs Chelsea", "time": "19:45 UTC", "competition": "Premier League"}]
    with (
        patch("main.fetch_matches", side_effect=[pl, []]),
        patch("main.fetch_sessions", return_value=[]),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main()
        mock_post.assert_called_once()
        payload = mock_post.call_args[0][1]
        assert "Arsenal vs Chelsea" in payload["content"]


def test_f1_only_triggers_discord_post():
    f1 = [{"label": "Australia GP — Race", "time": "06:00 UTC", "competition": "Formula 1"}]
    with (
        patch("main.fetch_matches", return_value=[]),
        patch("main.fetch_sessions", return_value=f1),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main()
        mock_post.assert_called_once()


def test_missing_env_var_raises():
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(KeyError),
    ):
        main.main()


def test_reminder_posts_when_match_in_2h_window():
    now = datetime(2026, 5, 5, 17, 45, tzinfo=timezone.utc)
    pl = [{"label": "Arsenal vs Chelsea", "time": "02:45 ICT", "competition": "Premier League", "datetime_utc": _MATCH_DT}]
    with (
        patch("main.fetch_matches", side_effect=[pl, []]),
        patch("main.fetch_sessions", return_value=[]),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main(now_utc=now, reminder_mode=True)
        mock_post.assert_called_once()
        assert "แจ้งเตือน" in mock_post.call_args[0][1]["content"]


def test_reminder_skips_when_match_outside_window():
    now = datetime(2026, 5, 5, 14, 0, tzinfo=timezone.utc)
    pl = [{"label": "Arsenal vs Chelsea", "time": "02:45 ICT", "competition": "Premier League", "datetime_utc": _MATCH_DT}]
    with (
        patch("main.fetch_matches", side_effect=[pl, []]),
        patch("main.fetch_sessions", return_value=[]),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main(now_utc=now, reminder_mode=True)
        mock_post.assert_not_called()


def test_kickoff_posts_when_match_in_1h_window():
    now = datetime(2026, 5, 5, 18, 45, tzinfo=timezone.utc)
    pl = [{
        "label": "Arsenal vs Chelsea", "time": "02:45 ICT",
        "competition": "Premier League", "datetime_utc": _MATCH_DT,
        "match_id": 1, "home_team": "Arsenal", "away_team": "Chelsea",
    }]
    _ODDS_ENV = {**_ENV, "ODDS_API_KEY": "odds-key"}
    with (
        patch("main.fetch_matches", side_effect=[pl, []]),
        patch("main.fetch_lineup", return_value=(["Raya"], ["Sanchez"])),
        patch("main.fetch_handicap", return_value=None),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ODDS_ENV),
    ):
        main.main(now_utc=now, kickoff_mode=True)
        mock_post.assert_called_once()
        assert "เตะในอีก 1 ชั่วโมง" in mock_post.call_args[0][1]["content"]


def test_kickoff_skips_when_no_matches_in_window():
    now = datetime(2026, 5, 5, 14, 0, tzinfo=timezone.utc)
    pl = [{
        "label": "Arsenal vs Chelsea", "time": "02:45 ICT",
        "competition": "Premier League", "datetime_utc": _MATCH_DT,
        "match_id": 1, "home_team": "Arsenal", "away_team": "Chelsea",
    }]
    _ODDS_ENV = {**_ENV, "ODDS_API_KEY": "odds-key"}
    with (
        patch("main.fetch_matches", side_effect=[pl, []]),
        patch("main.fetch_lineup", return_value=([], [])),
        patch("main.fetch_handicap", return_value=None),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ODDS_ENV),
    ):
        main.main(now_utc=now, kickoff_mode=True)
        mock_post.assert_not_called()


def test_lottery_mode_posts_analysis():
    _analysis = {
        "total_draws": 10,
        "hot": [{"number": "41", "count": 4}],
        "cold": [{"number": "00", "count": 0}],
        "due": [],
        "suggestions": ["41"],
    }
    with (
        patch("main.fetch_lottery_results", return_value=[{"two_digit": "41"}]),
        patch("main.analyze_lottery", return_value=_analysis),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main(lottery_mode=True)
        mock_post.assert_called_once()
        assert "หวยลาว" in mock_post.call_args[0][1]["content"]


def test_lottery_mode_no_football_api_key_needed():
    _analysis = {"total_draws": 0, "hot": [], "cold": [], "due": [], "suggestions": []}
    with (
        patch("main.fetch_lottery_results", return_value=[]),
        patch("main.analyze_lottery", return_value=_analysis),
        patch("main.post_to_webhook"),
        patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://hook"}, clear=True),
    ):
        main.main(lottery_mode=True)  # should not raise KeyError for FOOTBALL_DATA_API_KEY
