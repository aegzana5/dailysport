from __future__ import annotations

import requests

_BASE = "https://openfpl-scout-ai-186049008266.europe-west1.run.app"
_TIMEOUT = 10


def fetch_scout_team() -> dict:
    try:
        gw_res = requests.get(f"{_BASE}/api/gameweeks", timeout=_TIMEOUT)
        gw_res.raise_for_status()
        latest_gw = gw_res.json().get("latest", 38)

        data_res = requests.get(
            f"{_BASE}/data/internal/scout_team/gw_{latest_gw}.json",
            timeout=_TIMEOUT,
        )
        data_res.raise_for_status()
        data = data_res.json()
        return {
            "gameweek": latest_gw,
            "players": [
                {
                    "name": p["web_name"],
                    "position": p["element_type"],
                    "team": p["team_name"],
                    "opponent": p["opponent_team_name"],
                    "home": p["was_home"],
                    "xpts": round(p["expected_points"], 2),
                    "role": p.get("role", ""),
                }
                for p in data.get("scout_team", [])
            ],
        }
    except Exception as e:
        print(f"Warning: failed to fetch FPL scout team: {e}")
        return {"gameweek": None, "players": []}
