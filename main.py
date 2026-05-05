from __future__ import annotations

import os
from datetime import date

from fetchers.football import fetch_matches
from fetchers.f1 import fetch_sessions
from formatter import format_embed
from discord_webhook import post_to_webhook


def main() -> None:
    api_key = os.environ["FOOTBALL_DATA_API_KEY"]
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    today = date.today()

    pl = fetch_matches(api_key, "PL", "Premier League", today)
    ucl = fetch_matches(api_key, "CL", "Champions League", today)
    f1 = fetch_sessions(today)

    if not pl and not ucl and not f1:
        print("No matches today. Skipping.")
        return

    matches_by_sport: dict[str, list[dict]] = {}
    if pl:
        matches_by_sport["Premier League"] = pl
    if ucl:
        matches_by_sport["Champions League"] = ucl
    if f1:
        matches_by_sport["Formula 1"] = f1

    payload = format_embed(matches_by_sport, today)
    post_to_webhook(webhook_url, payload)
    total = sum(len(v) for v in matches_by_sport.values())
    print(f"Posted {total} event(s) to Discord.")


if __name__ == "__main__":
    main()
