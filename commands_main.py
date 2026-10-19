"""Poll Telegram for portfolio commands (/buy, /sell, /list) and apply them.
Run on a schedule by GitHub Actions; commits portfolio.json when it changes.
"""
from __future__ import annotations

import os
from pathlib import Path

from scripts.portfolio_commands import handle_command, load_portfolio, save_portfolio
from scripts.telegram_poll import get_updates, send_message

OFFSET_PATH = Path(__file__).resolve().parent / ".telegram_offset"


def read_offset() -> int | None:
    if not OFFSET_PATH.exists():
        return None
    content = OFFSET_PATH.read_text().strip()
    return int(content) if content else None


def write_offset(offset: int) -> None:
    OFFSET_PATH.write_text(str(offset))


def main() -> None:
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    chat_id = os.environ["TELEGRAM_CHAT_ID"].strip()

    offset = read_offset()
    updates = get_updates(bot_token, offset)

    portfolio = load_portfolio()
    changed = False
    latest_update_id = None

    for update in updates:
        latest_update_id = update["update_id"]
        message = update.get("message")
        if not message:
            continue
        if str(message["chat"]["id"]) != chat_id:
            continue  # ignore anyone other than the owner
        text = message.get("text", "")
        if not text.startswith("/"):
            continue

        reply, did_change = handle_command(text, portfolio)
        send_message(bot_token, chat_id, reply)
        changed = changed or did_change

    if latest_update_id is not None:
        write_offset(latest_update_id + 1)

    if changed:
        save_portfolio(portfolio)
        print("portfolio.json updated")


if __name__ == "__main__":
    main()
