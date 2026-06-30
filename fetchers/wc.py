from __future__ import annotations

import requests
from datetime import date, datetime, timezone, timedelta

_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary"
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


def fetch_wc_lineup(event_id: str) -> dict[str, list[str]]:
    """Returns {"home": [...names], "away": [...names]} — empty lists if not yet announced."""
    try:
        resp = requests.get(_SUMMARY_URL, params={"event": event_id}, timeout=10)
        resp.raise_for_status()
        rosters = resp.json().get("rosters", [])
        result: dict[str, list[str]] = {"home": [], "away": []}
        for i, roster in enumerate(rosters[:2]):
            key = "home" if i == 0 else "away"
            entries = roster.get("roster", [])
            starters = [e for e in entries if e.get("starter")]
            result[key] = [e.get("athlete", {}).get("shortName") or e.get("athlete", {}).get("displayName", "?") for e in starters]
        return result
    except Exception as e:
        print(f"Warning: failed to fetch WC lineup {event_id}: {e}")
        return {"home": [], "away": []}
