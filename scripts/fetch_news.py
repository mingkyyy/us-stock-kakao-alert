"""Fetch news headlines from Google News RSS (no API key required)."""
from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET

import requests

RSS_BASE = "https://news.google.com/rss/search"


def search_news(query: str, limit: int = 5) -> list[dict]:
    params = {
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    }
    url = f"{RSS_BASE}?{urllib.parse.urlencode(params)}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall("./channel/item")[:limit]:
        items.append(
            {
                "title": item.findtext("title", ""),
                "link": item.findtext("link", ""),
                "source": item.findtext("source", ""),
            }
        )
    return items


def fetch_market_news(limit: int = 6) -> list[dict]:
    return search_news("US stock market", limit=limit)


def fetch_ticker_news(ticker: str, limit: int = 3) -> list[dict]:
    return search_news(f"{ticker} stock", limit=limit)
