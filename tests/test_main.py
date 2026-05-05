from unittest.mock import patch
import pytest
import main  # import at module level so patch("main.X") works


_ENV = {"FOOTBALL_DATA_API_KEY": "key", "DISCORD_WEBHOOK_URL": "https://hook"}


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
