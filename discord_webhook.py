import json

import requests


def post_to_webhook(webhook_url: str, payload: dict) -> None:
    resp = requests.post(webhook_url, json=payload, timeout=10)
    if not resp.ok:
        raise RuntimeError(f"Discord webhook failed: {resp.status_code} {resp.text}")


def post_with_image(webhook_url: str, payload: dict, image_bytes: bytes, filename: str = "schedule.png") -> None:
    files = {"file": (filename, image_bytes, "image/png")}
    data = {"payload_json": json.dumps(payload)}
    resp = requests.post(webhook_url, data=data, files=files, timeout=15)
    if not resp.ok:
        raise RuntimeError(f"Discord webhook failed: {resp.status_code} {resp.text}")
