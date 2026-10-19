"""Telegram webhook handler (Vercel serverless function).

Telegram calls this URL the instant a message arrives — no polling, instant replies.
Reads/writes portfolio.json directly in GitHub via the Contents API, since this
function's filesystem is ephemeral (nothing written here persists between calls).

Required env vars (set in the Vercel project's Settings > Environment Variables):
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID       - only messages from this chat are processed
  GH_TOKEN               - GitHub PAT with Contents: Read and write on the repo
  GITHUB_REPOSITORY      - "owner/repo", e.g. "mingkyy12/us-stock-kakao-alert"
"""
from __future__ import annotations

import base64
import json
import os
import re
from http.server import BaseHTTPRequestHandler

import requests

GITHUB_API = "https://api.github.com"
PORTFOLIO_PATH = "portfolio.json"

BUY_RE = re.compile(r"^/buy\s+([A-Za-z.]+)\s+([\d.]+)\s+([\d.]+)$", re.IGNORECASE)
SELL_RE = re.compile(r"^/sell\s+([A-Za-z.]+)\s+([\d.]+)$", re.IGNORECASE)

HELP_TEXT = (
    "사용 가능한 명령어:\n"
    "/buy TICKER 수량 가격 — 매수 반영 (예: /buy AAPL 10 150.5)\n"
    "/sell TICKER 수량 — 매도 반영 (예: /sell AAPL 3)\n"
    "/list — 현재 포트폴리오 보기"
)


def format_portfolio(portfolio: list[dict]) -> str:
    if not portfolio:
        return "포트폴리오가 비어있어요."
    lines = ["📋 현재 포트폴리오"]
    for p in portfolio:
        lines.append(f"- {p['ticker']}: {p['shares']}주 (평단가 ${p['avg_price']:,.4f})")
    return "\n".join(lines)


def apply_buy(portfolio: list[dict], ticker: str, shares: float, price: float) -> str:
    ticker = ticker.upper()
    for p in portfolio:
        if p["ticker"] == ticker:
            new_shares = p["shares"] + shares
            p["avg_price"] = round((p["shares"] * p["avg_price"] + shares * price) / new_shares, 4)
            p["shares"] = new_shares
            return f"✅ {ticker} {shares}주 매수 반영 (총 {new_shares}주, 평단가 ${p['avg_price']:,.4f})"
    portfolio.append({"ticker": ticker, "shares": shares, "avg_price": price})
    return f"✅ {ticker} {shares}주 신규 추가 (평단가 ${price:,.4f})"


def apply_sell(portfolio: list[dict], ticker: str, shares: float) -> str:
    ticker = ticker.upper()
    for i, p in enumerate(portfolio):
        if p["ticker"] == ticker:
            if shares > p["shares"]:
                return f"⚠️ {ticker} 보유 수량({p['shares']}주)보다 많이 팔 수 없어요."
            remaining = p["shares"] - shares
            if remaining <= 0:
                portfolio.pop(i)
                return f"✅ {ticker} 전량 매도, 포트폴리오에서 제거됨"
            p["shares"] = remaining
            return f"✅ {ticker} {shares}주 매도 반영 (잔여 {remaining}주)"
    return f"⚠️ {ticker} 보유 중이 아니에요."


def handle_command(text: str, portfolio: list[dict]) -> tuple[str, bool]:
    text = text.strip()

    if text in ("/list", "/portfolio"):
        return format_portfolio(portfolio), False
    if text in ("/help", "/start"):
        return HELP_TEXT, False

    match = BUY_RE.match(text)
    if match:
        ticker, shares, price = match.group(1), float(match.group(2)), float(match.group(3))
        return apply_buy(portfolio, ticker, shares, price), True

    match = SELL_RE.match(text)
    if match:
        ticker, shares = match.group(1), float(match.group(2))
        reply = apply_sell(portfolio, ticker, shares)
        return reply, reply.startswith("✅")

    return f"❓ 이해 못한 명령어예요.\n\n{HELP_TEXT}", False


def github_get_portfolio(owner: str, repo: str, token: str) -> tuple[list[dict], str]:
    resp = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/contents/{PORTFOLIO_PATH}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content), data["sha"]


def github_put_portfolio(owner: str, repo: str, token: str, portfolio: list[dict], sha: str, message: str) -> None:
    content_b64 = base64.b64encode(
        (json.dumps(portfolio, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    ).decode("utf-8")
    resp = requests.put(
        f"{GITHUB_API}/repos/{owner}/{repo}/contents/{PORTFOLIO_PATH}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"message": message, "content": content_b64, "sha": sha},
        timeout=10,
    )
    resp.raise_for_status()


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> None:
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={"chat_id": chat_id, "text": text},
        timeout=10,
    )


def process_update(update: dict) -> None:
    message = update.get("message")
    if not message:
        return

    bot_token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    chat_id = os.environ["TELEGRAM_CHAT_ID"].strip()

    if str(message["chat"]["id"]) != chat_id:
        return  # ignore anyone other than the owner

    text = message.get("text", "")
    if not text.startswith("/"):
        return

    gh_token = os.environ["GH_TOKEN"].strip()
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/", 1)

    portfolio, sha = github_get_portfolio(owner, repo, gh_token)
    reply, changed = handle_command(text, portfolio)

    if changed:
        github_put_portfolio(owner, repo, gh_token, portfolio, sha, f"chore: {text} via telegram webhook")

    send_telegram_message(bot_token, chat_id, reply)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length)

        try:
            update = json.loads(body)
            process_update(update)
        except Exception as e:  # noqa: BLE001 - always ack Telegram, log the error
            print(f"webhook error: {e}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')
