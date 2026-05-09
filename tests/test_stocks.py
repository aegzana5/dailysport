from unittest.mock import Mock, patch

from fetchers.stocks import fetch_recommendations


def test_fetch_recommendations_filters_and_sorts_by_upside():
    html = """
    <html>
      <head><title>Alpha Corp (NYSE: ABC) Analyst Ratings</title></head>
      <body>
        Total Analysts 12 Consensus Rating Buy Price Target $45.00 Upside +12.5%
      </body>
    </html>
    """
    html2 = """
    <html>
      <head><title>Beta Inc (NASDAQ: BET) Analyst Ratings</title></head>
      <body>
        Total Analysts 8 Consensus Rating Strong Buy Price Target $18.00 Upside +7.1%
      </body>
    </html>
    """
    html3 = """
    <html>
      <head><title>Gamma Co (NYSE: GAM) Analyst Ratings</title></head>
      <body>
        Total Analysts 6 Consensus Rating Hold Price Target $11.00 Upside +4.0%
      </body>
    </html>
    """
    responses = []
    for text in (html, html2, html3):
        resp = Mock(text=text)
        resp.raise_for_status = Mock()
        responses.append(resp)

    with patch("fetchers.stocks._WATCHLIST", ["ABC", "BET", "GAM"]):
        with patch("fetchers.stocks.requests.get", side_effect=responses):
            picks = fetch_recommendations(limit=2)

    assert [item["ticker"] for item in picks] == ["ABC", "BET"]
    assert picks[0]["company"] == "Alpha Corp"
    assert picks[0]["consensus"] == "Buy"
    assert picks[0]["upside"] == 12.5
