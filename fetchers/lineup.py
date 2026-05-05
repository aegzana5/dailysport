from __future__ import annotations

import requests

_MATCH_URL = "https://api.football-data.org/v4/matches/{match_id}"


def fetch_lineup(api_key: str, match_id: int) -> tuple[list[str], list[str]]:
    """Returns (home_players, away_players). Empty lists if not released yet."""
    try:
        resp = requests.get(
            _MATCH_URL.format(match_id=match_id),
            headers={"X-Auth-Token": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        home = [p["name"] for p in data.get("homeTeam", {}).get("lineup", [])]
        away = [p["name"] for p in data.get("awayTeam", {}).get("lineup", [])]
        return home, away
    except Exception as e:
        print(f"Warning: failed to fetch lineup for match {match_id}: {e}")
        return [], []
