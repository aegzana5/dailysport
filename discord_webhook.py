import requests


def post_to_webhook(webhook_url: str, payload: dict) -> None:
    resp = requests.post(webhook_url, json=payload, timeout=10)
    if not resp.ok:
        raise RuntimeError(f"Discord webhook failed: {resp.status_code} {resp.text}")
