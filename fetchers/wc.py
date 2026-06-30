from __future__ import annotations

import requests
from datetime import date, datetime, timezone, timedelta

_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
_ICT = timezone(timedelta(hours=7))


def fetch_wc_matches(today: date | None = None) -> list[dict]:
    if today is None:
        today = date.today()
    date_str = today.strftime("%Y%m%d")
    try:
        resp = requests.get(_BASE_URL, params={"dates": date_str}, timeout=10)
        resp.raise_for_status()
        matches = []
        for event in resp.json().get("events", []):
            comps = event.get("competitions", [{}])
            c = comps[0] if comps else {}
            teams = c.get("competitors", [])
            home_t = next((t for t in teams if t.get("homeAway") == "home"), {})
            away_t = next((t for t in teams if t.get("homeAway") == "away"), {})
            home = home_t.get("team", {}).get("shortDisplayName") or home_t.get("team", {}).get("displayName", "?")
            away = away_t.get("team", {}).get("shortDisplayName") or away_t.get("team", {}).get("displayName", "?")
            raw_date = event.get("date", "")
            dt_utc = datetime.strptime(raw_date, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
            time_ict = dt_utc.astimezone(_ICT).strftime("%H:%M") + " ICT"
            matches.append({
                "label": f"{home} vs {away}",
                "time": time_ict,
                "competition": "World Cup",
                "datetime_utc": dt_utc,
                "match_id": event.get("id"),
                "home_team": home,
                "away_team": away,
            })
        return matches
    except Exception as e:
        print(f"Warning: failed to fetch WC from ESPN: {e}")
        return []
