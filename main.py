from __future__ import annotations

import os
import sys
from datetime import date, datetime, timezone, timedelta

from fetchers.football import fetch_matches
from fetchers.f1 import fetch_sessions
from fetchers.lineup import fetch_lineup
from fetchers.odds import fetch_handicap
from formatter import format_embed, format_reminder, format_kickoff
from discord_webhook import post_to_webhook

_REMINDER_TARGET = timedelta(hours=2)
_KICKOFF_TARGET = timedelta(hours=1)
_REMINDER_WINDOW = timedelta(minutes=15)


def _in_window(dt_utc: datetime | None, now_utc: datetime, target: timedelta) -> bool:
    if dt_utc is None:
        return False
    delta = dt_utc - now_utc
    return (target - _REMINDER_WINDOW) <= delta <= (target + _REMINDER_WINDOW)


def main(
    now_utc: datetime | None = None,
    reminder_mode: bool = False,
    kickoff_mode: bool = False,
) -> None:
    if not reminder_mode:
        reminder_mode = "--reminder" in sys.argv
    if not kickoff_mode:
        kickoff_mode = "--kickoff" in sys.argv

    api_key = os.environ["FOOTBALL_DATA_API_KEY"]
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    if kickoff_mode:
        odds_key = os.environ["ODDS_API_KEY"]
        fetch_date = (now_utc + _KICKOFF_TARGET).date()
        pl = fetch_matches(api_key, "PL", "Premier League", fetch_date)
        ucl = fetch_matches(api_key, "CL", "Champions League", fetch_date)
        upcoming = []
        for match in pl + ucl:
            if not _in_window(match.get("datetime_utc"), now_utc, _KICKOFF_TARGET):
                continue
            home_lu, away_lu = fetch_lineup(api_key, match["match_id"])
            handicap = fetch_handicap(odds_key, match["competition"], match["home_team"], match["away_team"])
            upcoming.append({**match, "home_lineup": home_lu, "away_lineup": away_lu, "handicap": handicap})
        if not upcoming:
            print("No matches in 1h kickoff window. Skipping.")
            return
        payload = format_kickoff(upcoming, fetch_date)
        post_to_webhook(webhook_url, payload)
        print(f"Posted kickoff info for {len(upcoming)} match(es).")
        return

    fetch_date = (now_utc + _REMINDER_TARGET).date() if reminder_mode else now_utc.date()

    pl = fetch_matches(api_key, "PL", "Premier League", fetch_date)
    ucl = fetch_matches(api_key, "CL", "Champions League", fetch_date)
    f1 = fetch_sessions(fetch_date)

    if reminder_mode:
        pl = [m for m in pl if _in_window(m.get("datetime_utc"), now_utc, _REMINDER_TARGET)]
        ucl = [m for m in ucl if _in_window(m.get("datetime_utc"), now_utc, _REMINDER_TARGET)]
        f1 = [m for m in f1 if _in_window(m.get("datetime_utc"), now_utc, _REMINDER_TARGET)]

    if not pl and not ucl and not f1:
        mode = "reminder window" if reminder_mode else "today"
        print(f"No matches for {mode}. Skipping.")
        return

    matches_by_sport: dict[str, list[dict]] = {}
    if pl:
        matches_by_sport["Premier League"] = pl
    if ucl:
        matches_by_sport["Champions League"] = ucl
    if f1:
        matches_by_sport["Formula 1"] = f1

    payload = format_reminder(matches_by_sport, fetch_date) if reminder_mode else format_embed(matches_by_sport, fetch_date)
    post_to_webhook(webhook_url, payload)
    total = sum(len(v) for v in matches_by_sport.values())
    print(f"Posted {total} event(s) to Discord.")


if __name__ == "__main__":
    main()
