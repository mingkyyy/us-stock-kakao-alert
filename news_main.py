"""Entry point for the daily news digest, run by GitHub Actions."""
from scripts.fetch_and_calc import load_portfolio
from scripts.fetch_news import fetch_market_news, fetch_ticker_news
from scripts.summarize_news import summarize
from scripts.telegram_send import send_report


def main() -> None:
    portfolio = load_portfolio()
    tickers = [p["ticker"] for p in portfolio]

    market_news = fetch_market_news()
    ticker_news = {ticker: fetch_ticker_news(ticker) for ticker in tickers}

    digest = summarize(market_news, ticker_news)
    print(digest)
    send_report(digest)


if __name__ == "__main__":
    main()
