from __future__ import annotations

import requests

_ODDS_URL = "https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"

_SPORT_KEYS: dict[str, str] = {
    "Premier League": "soccer_epl",
    "Champions League": "soccer_uefa_champs_league",
}


def _team_matches(odds_name: str, fd_name: str) -> bool:
    a, b = odds_name.lower(), fd_name.lower()
    return a in b or b in a


def fetch_handicap(
    api_key: str,
    competition: str,
    home_team: str,
    away_team: str,
) -> dict | None:
    """Returns handicap dict or None if unavailable."""
    sport_key = _SPORT_KEYS.get(competition)
    if not sport_key:
        return None
    try:
        resp = requests.get(
            _ODDS_URL.format(sport_key=sport_key),
            params={
                "apiKey": api_key,
                "regions": "eu",
                "markets": "asian_handicap",
                "dateFormat": "iso",
            },
            timeout=10,
        )
        resp.raise_for_status()
        for event in resp.json():
            if not (
                _team_matches(event.get("home_team", ""), home_team)
                and _team_matches(event.get("away_team", ""), away_team)
            ):
                continue
            for bookmaker in event.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("key") != "asian_handicap":
                        continue
                    outcomes = market.get("outcomes", [])
                    h = next((o for o in outcomes if _team_matches(o["name"], home_team)), None)
                    a = next((o for o in outcomes if _team_matches(o["name"], away_team)), None)
                    if h and a:
                        return {
                            "bookmaker": bookmaker.get("title", ""),
                            "home": {"name": h["name"], "point": h["point"], "price": h["price"]},
                            "away": {"name": a["name"], "point": a["point"], "price": a["price"]},
                        }
    except Exception as e:
        print(f"Warning: failed to fetch handicap for {home_team} vs {away_team}: {e}")
    return None
