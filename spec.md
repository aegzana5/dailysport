# Project Spec — discord-sports-schedule

> Source of truth. Update after every task.

## Architecture

**Runtime:** Python 3.12 · GitHub Actions CI/CD · Discord Webhooks

**Entry point:** `main.py` — CLI flags select mode, dispatches to fetchers/formatter/webhook

**Modes (CLI flags):**
| Flag | Description |
|------|-------------|
| `--combined` | Daily digest: PL + UCL + F1 + Lao lottery + stocks + crypto |
| `--reminder` | 2h-before match alert (±15min window) |
| `--kickoff` | 30min-before lineup + handicap alert |
| `--lottery` | Lao lottery analysis only |
| `--thailottery` | Thai lottery analysis only |
| `--horoscope` | Daily horoscope (12 signs) |
| `--fpl` | FPL scout + standings + team picks |

**Module map:**
```
main.py                  # orchestrator
formatter.py             # Discord embed builders
discord_webhook.py       # HTTP POST to webhook
image_generator.py       # image generation helper
fetchers/
  football.py            # football-data.org API (PL, UCL)
  f1.py                  # F1 sessions
  lineup.py              # match lineups
  odds.py                # handicap odds
  stocks.py              # stock recommendations
  crypto.py              # crypto recommendations
  laolottery.py          # Lao lottery results
  laolottery_analyzer.py # Lao lottery frequency analysis
  thailottery.py         # Thai lottery results
  thailottery_analyzer.py# Thai lottery frequency analysis
  horoscope.py           # horoscope data
  fpl.py                 # FPL standings + picks
  fpl_scout.py           # FPL scout team
tests/                   # pytest suite (one file per module)
.github/workflows/
  sport-lottery.yml      # cron 12:00 TH → --combined daily
```

**Secrets/Env vars:**
- `DISCORD_WEBHOOK_URL` — default webhook
- `HOROSCOPE_WEBHOOK_URL` — horoscope channel
- `FPL_WEBHOOK_URL` — FPL channel
- `FOOTBALL_DATA_API_KEY` — football-data.org
- `ODDS_API_KEY` — odds API

---

## Done

- Football fetcher: PL + UCL matches from football-data.org
- F1 session fetcher
- Lineup fetcher (pre-kickoff)
- Odds/handicap fetcher
- Stock & crypto recommendation fetchers
- Lao lottery fetcher + frequency analyzer (upper/lower 2-digit)
- Thai lottery fetcher + frequency analyzer
- Horoscope fetcher (12 signs)
- FPL standings, bootstrap, team picks fetcher
- FPL scout team fetcher
- All formatters: embed, reminder, kickoff, lottery, combined, thai lottery, horoscope, FPL standings, FPL scout, FPL team picks
- Discord webhook poster
- GitHub Actions workflow: daily combined post at 12:00 TH (05:00 UTC)
- Dedicated webhook routing: `HOROSCOPE_WEBHOOK_URL`, `FPL_WEBHOOK_URL`
- FPL team picks shown after standings
- pytest test suite covering all modules
- Horoscope job disabled in workflow (flag `if: false` / schedule removed)
- `python-dotenv` added to requirements (main.py imports `load_dotenv` since `5bf04da`)
- `fetch_scout_team` takes `gameweek` param directly (no more self-lookup via `/api/gameweeks`) — resolves "auto-detect gameweek" todo
- `format_fpl_standings` now chunks to Discord's 2000-char limit (list[dict], like team_picks) — fixes crash when league >~35 entries

---

## Todo

- [ ] Re-enable horoscope schedule when needed (currently disabled in workflow)
- [ ] Add kickoff/reminder jobs back to workflow if desired
- [ ] Thai lottery: wire dedicated webhook (`THAILOTTERY_WEBHOOK_URL`?) for channel separation
- [ ] Add error handling / retry for flaky external APIs
- [ ] Image generation integration (image_generator.py exists but not wired into any mode)
- [x] FPL: auto-detect current gameweek without needing scout data as fallback

---

## Current State

As of 2026-09-01:

- `master` branch is stable and deployable
- Workflow runs daily `--combined` at 05:00 UTC (12:00 TH)
- Horoscope job is **disabled** in the workflow (`1fdbfd4`)
- FPL mode posts: scout → standings (now chunked) → team picks to `FPL_WEBHOOK_URL`
- Verified `--fpl` locally: standings crash fixed (50-entry league now posts fine); scout team returns 404 for GW2 from external `openfpl-scout-ai` API (data not published yet upstream, not our bug) — degrades gracefully with a warning
- FPL league switched from `102993` to `161756` ("Dorsor FPL", 9 entries) — `fetchers/fpl.py` `_URL`
- Uncommitted: `formatter.py` (standings chunking fix), `main.py` (loop over chunked standings payload), `fetchers/fpl_scout.py` (gameweek param, already staged before this session), `fetchers/fpl.py` (league ID)
- No active in-progress tasks
