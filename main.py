from __future__ import annotations

import os
import sys
from datetime import date, datetime, timezone, timedelta

from fetchers.football import fetch_matches
from fetchers.f1 import fetch_sessions
from fetchers.lineup import fetch_lineup
from fetchers.odds import fetch_handicap
from fetchers.stocks import fetch_recommendations as fetch_stock_recommendations
from fetchers.crypto import fetch_recommendations as fetch_crypto_recommendations
from fetchers.laolottery import fetch_results as fetch_lottery_results
from fetchers.laolottery_analyzer import analyze as analyze_lottery
from fetchers.thailottery import fetch_results as fetch_thai_results
from fetchers.thailottery_analyzer import analyze as analyze_thai
from fetchers.horoscope import fetch_horoscopes
from fetchers.fpl import fetch_standings as fetch_fpl_standings, fetch_bootstrap, fetch_team_picks
from fetchers.fpl_scout import fetch_scout_team
from formatter import format_embed, format_reminder, format_kickoff, format_lottery, format_combined, format_thailottery, format_horoscope, format_fpl_standings, format_fpl_scout, format_fpl_team_picks
from discord_webhook import post_to_webhook

_REMINDER_TARGET = timedelta(hours=2)
_KICKOFF_TARGET = timedelta(minutes=30)
_REMINDER_WINDOW = timedelta(minutes=15)


def _in_window(dt_utc: datetime | None, now_utc: datetime, target: timedelta) -> bool:
    if dt_utc is None:
        return False
    delta = dt_utc - now_utc
    return (target - _REMINDER_WINDOW) <= delta <= (target + _REMINDER_WINDOW)


def _first_match_slot(matches: list[dict]) -> datetime | None:
    kickoff_times = [match.get("datetime_utc") for match in matches if match.get("datetime_utc") is not None]
    if not kickoff_times:
        return None
    return min(kickoff_times)


def _build_lottery_bundle(results: list[dict]) -> dict:
    return {
        "lower": analyze_lottery(results, digit_key="two_digit"),
        "upper": analyze_lottery(results, digit_key="upper_two_digit"),
    }


def main(
    now_utc: datetime | None = None,
    reminder_mode: bool = False,
    kickoff_mode: bool = False,
    lottery_mode: bool = False,
    combined_mode: bool = False,
    thailottery_mode: bool = False,
    horoscope_mode: bool = False,
    fpl_mode: bool = False,
) -> None:
    if not reminder_mode:
        reminder_mode = "--reminder" in sys.argv
    if not kickoff_mode:
        kickoff_mode = "--kickoff" in sys.argv
    if not lottery_mode:
        lottery_mode = "--lottery" in sys.argv
    if not combined_mode:
        combined_mode = "--combined" in sys.argv
    if not thailottery_mode:
        thailottery_mode = "--thailottery" in sys.argv
    if not horoscope_mode:
        horoscope_mode = "--horoscope" in sys.argv
    if not fpl_mode:
        fpl_mode = "--fpl" in sys.argv

    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    if lottery_mode:
        results = fetch_lottery_results()
        analysis = _build_lottery_bundle(results)
        payload = format_lottery(analysis, now_utc.date())
        post_to_webhook(webhook_url, payload)
        print(f"Posted lottery analysis ({analysis['lower']['total_draws']} draws).")
        return

    if thailottery_mode:
        results = fetch_thai_results()
        analysis = analyze_thai(results)
        payload = format_thailottery(analysis, now_utc.date())
        post_to_webhook(webhook_url, payload)
        print(f"Posted Thai lottery analysis ({analysis['total_draws']} draws).")
        return

    if horoscope_mode:
        horoscopes = fetch_horoscopes()
        payloads = format_horoscope(horoscopes, now_utc.date())
        for payload in payloads:
            post_to_webhook(webhook_url, payload)
        print(f"Posted horoscope ({len(horoscopes)} signs, {len(payloads)} msg).")
        return

    if fpl_mode:
        scout = fetch_scout_team()
        scout_payload = format_fpl_scout(scout)
        post_to_webhook(webhook_url, scout_payload)
        standings = fetch_fpl_standings()
        standings_payload = format_fpl_standings(standings, now_utc.date())
        post_to_webhook(webhook_url, standings_payload)
        bootstrap = fetch_bootstrap()
        gw = scout.get("gameweek") or bootstrap["current_gw"]
        name_map = bootstrap["name_map"]
        picks_map: dict = {}
        for s in standings["standings"]:
            picks_map[s["entry_id"]] = fetch_team_picks(s["entry_id"], gw)
        for payload in format_fpl_team_picks(standings["standings"], picks_map, name_map, gw):
            post_to_webhook(webhook_url, payload)
        print(f"Posted FPL scout (GW{scout['gameweek']}, {len(scout['players'])} players) + standings ({len(standings['standings'])} entries) + team picks.")
        return

    api_key = os.environ["FOOTBALL_DATA_API_KEY"]

    if combined_mode:
        today = now_utc.date()
        pl = fetch_matches(api_key, "PL", "Premier League", today)
        ucl = fetch_matches(api_key, "CL", "Champions League", today)
        f1 = fetch_sessions(today)
        matches_by_sport: dict[str, list[dict]] = {}
        if pl:
            matches_by_sport["Premier League"] = pl
        if ucl:
            matches_by_sport["Champions League"] = ucl
        if f1:
            matches_by_sport["Formula 1"] = f1
        lottery_results = fetch_lottery_results()
        lottery_analysis = _build_lottery_bundle(lottery_results)
        stock_recommendations = fetch_stock_recommendations()
        crypto_recommendations = fetch_crypto_recommendations()
        sport_total = sum(len(v) for v in matches_by_sport.values())
        payloads = format_combined(matches_by_sport, lottery_analysis, stock_recommendations, crypto_recommendations, today)
        for payload in payloads:
            post_to_webhook(webhook_url, payload)
        print(f"Posted combined ({len(payloads)} msg): {sport_total} sport event(s) + lottery ({lottery_analysis['lower']['total_draws']} draws).")
        return

    if kickoff_mode:
        force = "--force" in sys.argv
        odds_key = os.environ["ODDS_API_KEY"]
        fetch_date = now_utc.date() if force else (now_utc + _KICKOFF_TARGET).date()
        pl = fetch_matches(api_key, "PL", "Premier League", fetch_date)
        ucl = fetch_matches(api_key, "CL", "Champions League", fetch_date)
        day_matches = pl + ucl
        first_slot = _first_match_slot(day_matches)
        if not force and (first_slot is None or not _in_window(first_slot, now_utc, _KICKOFF_TARGET)):
            print("No first-match kickoff alert in 30m window. Skipping.")
            return
        upcoming = []
        for match in day_matches:
            match_dt = match.get("datetime_utc")
            if not force and match_dt != first_slot:
                continue
            home_lu, away_lu = fetch_lineup(api_key, match["match_id"])
            handicap = fetch_handicap(odds_key, match["competition"], match["home_team"], match["away_team"])
            upcoming.append({**match, "home_lineup": home_lu, "away_lineup": away_lu, "handicap": handicap})
        if not upcoming:
            print("No matches at first kickoff slot. Skipping.")
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
