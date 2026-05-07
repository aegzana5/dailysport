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


def test_kickoff_posts_when_match_in_30m_window():
    now = datetime(2026, 5, 5, 19, 15, tzinfo=timezone.utc)
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
        assert "เตะในอีก 30 นาที" in mock_post.call_args[0][1]["content"]


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


def test_kickoff_posts_only_first_match_slot():
    now = datetime(2026, 5, 5, 19, 15, tzinfo=timezone.utc)
    same_slot = datetime(2026, 5, 5, 19, 45, tzinfo=timezone.utc)
    later_slot = datetime(2026, 5, 5, 20, 45, tzinfo=timezone.utc)
    pl = [
        {
            "label": "Arsenal vs Chelsea", "time": "02:45 ICT",
            "competition": "Premier League", "datetime_utc": same_slot,
            "match_id": 1, "home_team": "Arsenal", "away_team": "Chelsea",
        },
        {
            "label": "Liverpool vs City", "time": "02:45 ICT",
            "competition": "Premier League", "datetime_utc": same_slot,
            "match_id": 2, "home_team": "Liverpool", "away_team": "City",
        },
        {
            "label": "Spurs vs United", "time": "03:45 ICT",
            "competition": "Premier League", "datetime_utc": later_slot,
            "match_id": 3, "home_team": "Spurs", "away_team": "United",
        },
    ]
    _ODDS_ENV = {**_ENV, "ODDS_API_KEY": "odds-key"}
    with (
        patch("main.fetch_matches", side_effect=[pl, []]),
        patch("main.fetch_lineup", return_value=([], [])),
        patch("main.fetch_handicap", return_value=None),
        patch("main.post_to_webhook") as mock_post,
        patch.dict("os.environ", _ODDS_ENV),
    ):
        main.main(now_utc=now, kickoff_mode=True)
        mock_post.assert_called_once()
        content = mock_post.call_args[0][1]["content"]
        assert "Arsenal vs Chelsea" in content
        assert "Liverpool vs City" in content
        assert "Spurs vs United" not in content


def test_kickoff_skips_when_first_match_is_not_in_window_even_if_later_match_is():
    now = datetime(2026, 5, 5, 19, 15, tzinfo=timezone.utc)
    early_slot = datetime(2026, 5, 5, 18, 0, tzinfo=timezone.utc)
    later_slot = datetime(2026, 5, 5, 19, 45, tzinfo=timezone.utc)
    pl = [
        {
            "label": "Early Match", "time": "01:00 ICT",
            "competition": "Premier League", "datetime_utc": early_slot,
            "match_id": 1, "home_team": "Early", "away_team": "Team",
        },
        {
            "label": "Later Match", "time": "02:45 ICT",
            "competition": "Premier League", "datetime_utc": later_slot,
            "match_id": 2, "home_team": "Later", "away_team": "Team",
        },
    ]
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
    _analysis = {"total_draws": 0, "hot": [], "cold": [], "due": [], "weekly_avg": [], "suggestions": []}
    with (
        patch("main.fetch_lottery_results", return_value=[]),
        patch("main.analyze_lottery", return_value=_analysis),
        patch("main.post_to_webhook"),
        patch.dict("os.environ", {"DISCORD_WEBHOOK_URL": "https://hook"}, clear=True),
    ):
        main.main(lottery_mode=True)  # should not raise KeyError for FOOTBALL_DATA_API_KEY


def test_combined_mode_no_matches_posts_image_only():
    _analysis = {
        "total_draws": 5, "hot": [], "cold": [], "due": [], "weekly_avg": [], "suggestions": [],
    }
    fake_img = b"PNG_BYTES"
    with (
        patch("main.fetch_matches", return_value=[]),
        patch("main.fetch_sessions", return_value=[]),
        patch("main.fetch_lottery_results", return_value=[]),
        patch("main.analyze_lottery", return_value=_analysis),
        patch("main.generate_schedule_image", return_value=fake_img),
        patch("main.post_with_image") as mock_img_post,
        patch("main.post_to_webhook") as mock_text_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main(combined_mode=True)
        mock_img_post.assert_called_once()
        mock_text_post.assert_not_called()
        assert mock_img_post.call_args[0][1] == {}
        assert mock_img_post.call_args[0][2] == fake_img


def test_combined_mode_with_matches_posts_image():
    _analysis = {
        "total_draws": 5,
        "latest": {"date": "2026-05-06", "time": "", "number": "12341", "two_digit": "41"},
        "hot": [],
        "cold": [],
        "due": [],
        "weekly_avg": [],
        "suggestions": [],
    }
    pl = [{"label": "Arsenal vs Chelsea", "time": "19:45 ICT", "competition": "Premier League"}]
    fake_img = b"PNG_BYTES"
    with (
        patch("main.fetch_matches", side_effect=[pl, []]),
        patch("main.fetch_sessions", return_value=[]),
        patch("main.fetch_lottery_results", return_value=[]),
        patch("main.analyze_lottery", return_value=_analysis),
        patch("main.generate_schedule_image", return_value=fake_img),
        patch("main.post_with_image") as mock_img_post,
        patch("main.post_to_webhook") as mock_text_post,
        patch.dict("os.environ", _ENV),
    ):
        main.main(combined_mode=True)
        mock_img_post.assert_called_once()
        mock_text_post.assert_not_called()
        payload = mock_img_post.call_args[0][1]
        assert payload == {}
        assert mock_img_post.call_args[0][2] == fake_img
