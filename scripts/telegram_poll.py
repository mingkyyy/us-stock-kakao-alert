"""Long-poll helpers for reading and replying to Telegram messages."""
from __future__ import annotations

import requests


def get_updates(bot_token: str, offset: int | None) -> list[dict]:
    params = {"timeout": 0}
    if offset is not None:
        params["offset"] = offset
    resp = requests.get(
        f"https://api.telegram.org/bot{bot_token}/getUpdates", params=params, timeout=10
    )
    resp.raise_for_status()
    return resp.json()["result"]


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    resp = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={"chat_id": chat_id, "text": text},
        timeout=10,
    )
    resp.raise_for_status()
