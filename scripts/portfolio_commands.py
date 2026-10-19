"""Parse Telegram commands and apply them to portfolio.json."""
from __future__ import annotations

import json
import re
from pathlib import Path

PORTFOLIO_PATH = Path(__file__).resolve().parent.parent / "portfolio.json"

BUY_RE = re.compile(r"^/buy\s+([A-Za-z.]+)\s+([\d.]+)\s+([\d.]+)$", re.IGNORECASE)
SELL_RE = re.compile(r"^/sell\s+([A-Za-z.]+)\s+([\d.]+)$", re.IGNORECASE)

HELP_TEXT = (
    "사용 가능한 명령어:\n"
    "/buy TICKER 수량 가격 — 매수 반영 (예: /buy AAPL 10 150.5)\n"
    "/sell TICKER 수량 — 매도 반영 (예: /sell AAPL 3)\n"
    "/list — 현재 포트폴리오 보기"
)


def load_portfolio() -> list[dict]:
    with open(PORTFOLIO_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_portfolio(portfolio: list[dict]) -> None:
    with open(PORTFOLIO_PATH, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)
        f.write("\n")


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
    """Returns (reply_message, portfolio_changed)."""
    text = text.strip()

    if text in ("/list", "/portfolio"):
        return format_portfolio(portfolio), False

    if text in ("/help", "/start"):
        return HELP_TEXT, False

    match = BUY_RE.match(text)
    if match:
        ticker, shares, price = match.group(1), float(match.group(2)), float(match.group(3))
        reply = apply_buy(portfolio, ticker, shares, price)
        return reply, True

    match = SELL_RE.match(text)
    if match:
        ticker, shares = match.group(1), float(match.group(2))
        reply = apply_sell(portfolio, ticker, shares)
        return reply, reply.startswith("✅")

    return f"❓ 이해 못한 명령어예요.\n\n{HELP_TEXT}", False
