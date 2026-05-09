from __future__ import annotations

import requests

_URL = "https://fantasy.premierleague.com/api/leagues-classic/102993/standings/"
_TIMEOUT = 10


def fetch_standings(page: int = 1) -> dict:
    try:
        resp = requests.get(
            _URL,
            params={"page_standings": page, "phase": 1},
            timeout=_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        league = data.get("league", {})
        results = data.get("standings", {}).get("results", [])
        return {
            "league_name": league.get("name", "FPL League"),
            "standings": [
                {
                    "rank": r["rank"],
                    "last_rank": r.get("last_rank", r["rank"]),
                    "entry_name": r["entry_name"],
                    "player_name": r["player_name"],
                    "total": r["total"],
                    "event_total": r["event_total"],
                }
                for r in results
            ],
        }
    except Exception as e:
        print(f"Warning: failed to fetch FPL standings: {e}")
        return {"league_name": "FPL League", "standings": []}
