from unittest.mock import patch, MagicMock
import pytest
from discord_webhook import post_to_webhook


def test_post_sends_json_to_url():
    mock_resp = MagicMock()
    mock_resp.ok = True
    with patch("discord_webhook.requests.post", return_value=mock_resp) as mock_post:
        post_to_webhook("https://discord.com/api/webhooks/123/abc", {"content": "hello"})

    mock_post.assert_called_once_with(
        "https://discord.com/api/webhooks/123/abc",
        json={"content": "hello"},
        timeout=10,
    )


def test_post_raises_on_non_2xx():
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 429
    mock_resp.text = "Too Many Requests"
    with patch("discord_webhook.requests.post", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="Discord webhook failed: 429"):
            post_to_webhook("https://discord.com/api/webhooks/123/abc", {"content": "x"})


def test_post_succeeds_silently_on_2xx():
    mock_resp = MagicMock()
    mock_resp.ok = True
    with patch("discord_webhook.requests.post", return_value=mock_resp):
        post_to_webhook("https://discord.com/api/webhooks/123/abc", {"content": "x"})
