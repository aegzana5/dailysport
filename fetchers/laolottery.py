from __future__ import annotations

import requests

_API_URL = "https://api.th-starvip.com/api/laolotto/total"


def fetch_results() -> list[dict]:
    """Returns list of {date, time, number, two_digit}, newest first."""
    try:
        resp = requests.get(_API_URL, timeout=10)
        resp.raise_for_status()
        results = []
        for item in resp.json():
            number = item.get("field_lao_lotto_number", "")
            two_digit = number[-2:] if len(number) >= 2 else "??"
            results.append({
                "date": item.get("field_lao_lotto_date", ""),
                "time": item.get("field_lao_lotto_datetime", ""),
                "number": number,
                "two_digit": two_digit,
            })
        return results
    except Exception as e:
        print(f"Warning: failed to fetch Lao lottery: {e}")
        return []
