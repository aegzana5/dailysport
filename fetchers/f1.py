from __future__ import annotations

import requests
from datetime import date, datetime, timezone, timedelta

_BASE_URL = "https://api.openf1.org/v1/sessions"
_ICT = timezone(timedelta(hours=7))


def fetch_sessions(today: date | None = None) -> list[dict]:
    if today is None:
        today = date.today()
    url = f"{_BASE_URL}?year={today.year}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        sessions = []
        for s in resp.json():
            raw_start = s.get("date_start", "")
            if not raw_start.startswith(today.isoformat()):
                continue
            country = s.get("country_name", "Unknown")
            session_type = s.get("session_name", "Session")
            if len(raw_start) >= 16:
                dt_utc = datetime.strptime(raw_start[:16], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
                time_ict = dt_utc.astimezone(_ICT).strftime("%H:%M") + " ICT"
            else:
                dt_utc = None
                time_ict = "TBC"
            sessions.append(
                {
                    "label": f"{country} GP — {session_type}",
                    "time": time_ict,
                    "competition": "Formula 1",
                    "datetime_utc": dt_utc,
                }
            )
        return sessions
    except Exception as e:
        print(f"Warning: failed to fetch F1 sessions: {e}")
        return []
