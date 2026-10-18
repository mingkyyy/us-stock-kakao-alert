"""Fetch latest prices for the portfolio and build the alert message."""
from __future__ import annotations

import json
from pathlib import Path

import yfinance as yf

PORTFOLIO_PATH = Path(__file__).resolve().parent.parent / "portfolio.json"


def load_portfolio() -> list[dict]:
    with open(PORTFOLIO_PATH, encoding="utf-8") as f:
        return json.load(f)


def fetch_prices(tickers: list[str]) -> dict[str, dict]:
    """Return {ticker: {"close": today's close, "prev_close": previous close}}."""
    data = yf.download(tickers, period="5d", interval="1d", group_by="ticker", progress=False, auto_adjust=False)

    prices = {}
    for ticker in tickers:
        closes = data[ticker]["Close"].dropna() if len(tickers) > 1 else data["Close"].dropna()
        prices[ticker] = {
            "close": float(closes.iloc[-1]),
            "prev_close": float(closes.iloc[-2]),
        }
    return prices


def fetch_usd_krw_rate() -> float:
    closes = yf.Ticker("KRW=X").history(period="5d")["Close"].dropna()
    return float(closes.iloc[-1])


def build_report(portfolio: list[dict], prices: dict[str, dict], usd_krw_rate: float) -> str:
    lines = ["📊 미장 마감 포트폴리오 리포트", ""]

    total_value = 0.0
    total_prev_value = 0.0
    total_cost = 0.0

    for position in portfolio:
        ticker = position["ticker"]
        shares = position["shares"]
        avg_price = position["avg_price"]
        price = prices[ticker]["close"]
        prev_close = prices[ticker]["prev_close"]

        day_pct = (price - prev_close) / prev_close * 100
        avg_pct = (price - avg_price) / avg_price * 100
        value = price * shares

        total_value += value
        total_prev_value += prev_close * shares
        total_cost += avg_price * shares

        day_sign = "+" if day_pct >= 0 else ""
        avg_sign = "+" if avg_pct >= 0 else ""
        lines.append(
            f"{ticker}: ${price:,.2f} "
            f"(전일 {day_sign}{day_pct:.2f}% / 평단가 {avg_sign}{avg_pct:.2f}%)"
        )

    total_day_pct = (total_value - total_prev_value) / total_prev_value * 100
    total_avg_pct = (total_value - total_cost) / total_cost * 100
    total_day_sign = "+" if total_day_pct >= 0 else ""
    total_avg_sign = "+" if total_avg_pct >= 0 else ""

    total_value_krw = total_value * usd_krw_rate

    lines.append("")
    lines.append(f"💰 총 평가금액: ${total_value:,.2f} (₩{total_value_krw:,.0f})")
    lines.append(f"전일 대비: {total_day_sign}{total_day_pct:.2f}%")
    lines.append(f"평단가 대비: {total_avg_sign}{total_avg_pct:.2f}%")
    lines.append(f"(환율 ₩{usd_krw_rate:,.2f}/$ 기준, 달러 기준 주가 변동만 반영 — 환차손익 미포함)")

    return "\n".join(lines)


def get_report() -> str:
    portfolio = load_portfolio()
    tickers = [p["ticker"] for p in portfolio]
    prices = fetch_prices(tickers)
    usd_krw_rate = fetch_usd_krw_rate()
    return build_report(portfolio, prices, usd_krw_rate)


if __name__ == "__main__":
    print(get_report())
