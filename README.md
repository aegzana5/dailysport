## Cron Schedule

```
# Daily horoscope at 08:00 local time
0 8 * * * cd /path/to/discord-sports-schedule && DISCORD_WEBHOOK_URL=<your_webhook_url> python main.py --horoscope
```
