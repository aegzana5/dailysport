from __future__ import annotations

import requests
from datetime import date, timedelta

_BASE_URL = "https://api.openf1.org/v1/sessions"


def fetch_sessions(today: date | None = None) -> list[dict]:
    if today is None:
        today = date.today()
    next_day = today + timedelta(days=1)
    url = (
        f"{_BASE_URL}"
        f"?date_start>={today.isoformat()}T00:00:00"
        f"&date_start<{next_day.isoformat()}T00:00:00"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        sessions = []
        for s in resp.json():
            country = s.get("country_name", "Unknown")
            session_type = s.get("session_name", "Session")
            raw_start = s.get("date_start", "")
            time_utc = raw_start[11:16] + " UTC" if len(raw_start) >= 16 else "TBC"
            sessions.append(
                {
                    "label": f"{country} GP — {session_type}",
                    "time": time_utc,
                    "competition": "Formula 1",
                }
            )
        return sessions
    except Exception as e:
        print(f"Warning: failed to fetch F1 sessions: {e}")
        return []
