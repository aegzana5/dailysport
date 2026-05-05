from __future__ import annotations

import requests
from datetime import date

_BASE_URL = "https://api.football-data.org/v4/competitions/{code}/matches"


def fetch_matches(
    api_key: str,
    competition_code: str,
    competition_name: str,
    today: date | None = None,
) -> list[dict]:
    if today is None:
        today = date.today()
    date_str = today.isoformat()
    try:
        resp = requests.get(
            _BASE_URL.format(code=competition_code),
            headers={"X-Auth-Token": api_key},
            params={"dateFrom": date_str, "dateTo": date_str},
            timeout=10,
        )
        resp.raise_for_status()
        matches = []
        for m in resp.json().get("matches", []):
            home = m["homeTeam"].get("shortName") or m["homeTeam"].get("name")
            away = m["awayTeam"].get("shortName") or m["awayTeam"].get("name")
            time_utc = m["utcDate"][11:16]
            matches.append(
                {
                    "label": f"{home} vs {away}",
                    "time": f"{time_utc} UTC",
                    "competition": competition_name,
                }
            )
        return matches
    except Exception as e:
        print(f"Warning: failed to fetch {competition_code}: {e}")
        return []
