"""Send the report via a Telegram bot."""
from __future__ import annotations

import os

import requests


def send_report(message: str) -> None:
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    chat_id = os.environ["TELEGRAM_CHAT_ID"].strip()

    resp = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={"chat_id": chat_id, "text": message},
        timeout=10,
    )
    if not resp.ok:
        print(f"Telegram send failed ({resp.status_code}): {resp.text}")
    resp.raise_for_status()
