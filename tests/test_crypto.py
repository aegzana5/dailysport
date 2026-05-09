from unittest.mock import Mock, patch

from fetchers.crypto import fetch_recommendations


def test_fetch_recommendations_returns_top_24h_momentum_pairs():
    payload = [
        {"symbol": "BTCUSDT", "lastPrice": "100000", "priceChangePercent": "2.5", "quoteVolume": "1000000"},
        {"symbol": "ETHUSDT", "lastPrice": "4000", "priceChangePercent": "7.2", "quoteVolume": "2000000"},
        {"symbol": "SOLUSDT", "lastPrice": "180", "priceChangePercent": "5.1", "quoteVolume": "3000000"},
        {"symbol": "USDCUSDT", "lastPrice": "1.0", "priceChangePercent": "0.1", "quoteVolume": "5000000"},
        {"symbol": "1000SHIBUSDT", "lastPrice": "0.01", "priceChangePercent": "12.0", "quoteVolume": "9000000"},
        {"symbol": "DOGEUSDT", "lastPrice": "0.25", "priceChangePercent": "-1.0", "quoteVolume": "8000000"},
    ]
    resp = Mock()
    resp.raise_for_status = Mock()
    resp.json = Mock(return_value=payload)

    with patch("fetchers.crypto.requests.get", return_value=resp):
        picks = fetch_recommendations(limit=3)

    assert [item["symbol"] for item in picks] == ["ETH", "SOL", "BTC"]
    assert picks[0]["pair"] == "ETHUSDT"
    assert picks[0]["change_24h"] == 7.2
