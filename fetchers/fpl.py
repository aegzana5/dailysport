from __future__ import annotations

import requests

_URL = "https://fantasy.premierleague.com/api/leagues-classic/102993/standings/"
_BASE = "https://fantasy.premierleague.com/api"
_TIMEOUT = 10
_HEADERS = {"User-Agent": "Mozilla/5.0"}

_POS_MAP = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def fetch_standings(page: int = 1) -> dict:
    try:
        resp = requests.get(
            _URL,
            params={"page_standings": page, "phase": 1},
            timeout=_TIMEOUT,
            headers=_HEADERS,
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
                    "entry_id": r["entry"],
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


def fetch_bootstrap() -> dict:
    """Returns {name_map: {id: {web_name, pos}}, current_gw: int}."""
    try:
        resp = requests.get(f"{_BASE}/bootstrap-static/", timeout=15, headers=_HEADERS)
        resp.raise_for_status()
        data = resp.json()
        name_map = {
            e["id"]: {"web_name": e["web_name"], "pos": _POS_MAP.get(e["element_type"], "?")}
            for e in data.get("elements", [])
        }
        events = data.get("events", [])
        current_gw = next((e["id"] for e in events if e.get("is_current")), None)
        if current_gw is None:
            finished = [e["id"] for e in events if e.get("finished")]
            current_gw = finished[-1] if finished else 1
        return {"name_map": name_map, "current_gw": current_gw}
    except Exception as e:
        print(f"Warning: failed to fetch FPL bootstrap: {e}")
        return {"name_map": {}, "current_gw": 1}


def fetch_team_picks(entry_id: int, gameweek: int) -> list[dict]:
    try:
        resp = requests.get(
            f"{_BASE}/entry/{entry_id}/event/{gameweek}/picks/",
            timeout=_TIMEOUT,
            headers=_HEADERS,
        )
        resp.raise_for_status()
        return resp.json().get("picks", [])
    except Exception as e:
        print(f"Warning: failed to fetch picks for entry {entry_id}: {e}")
        return []
