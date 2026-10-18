"""Summarize collected news headlines into a Korean digest using the Claude API."""
from __future__ import annotations

import os

import requests

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-5-5"


def build_prompt(market_news: list[dict], ticker_news: dict[str, list[dict]]) -> str:
    lines = [
        "아래는 오늘자 미국 증시 관련 뉴스 헤드라인이야. 이걸 바탕으로 한국어 아침 브리핑 메시지를 만들어줘.",
        "",
        "[시장 전반 뉴스]",
    ]
    for item in market_news:
        lines.append(f"- {item['title']} ({item['source']})")

    for ticker, items in ticker_news.items():
        if not items:
            continue
        lines.append("")
        lines.append(f"[{ticker} 관련 뉴스]")
        for item in items:
            lines.append(f"- {item['title']} ({item['source']})")

    lines.append("")
    lines.append(
        "형식: '📰 오늘의 미국 증시 브리핑' 제목으로 시작. "
        "시장 전반 핵심을 3~5줄로 요약하고, 그다음 보유 종목 중 관련 뉴스가 있는 것만 한두 줄씩 요약. "
        "텔레그램 메시지로 보낼 거라 전체 800자 내외로 간결하게. 다른 설명 없이 메시지 본문만 출력해."
    )
    return "\n".join(lines)


def summarize(market_news: list[dict], ticker_news: dict[str, list[dict]]) -> str:
    api_key = os.environ["ANTHROPIC_API_KEY"].strip()
    prompt = build_prompt(market_news, ticker_news)

    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 1024,
            "thinking": {"type": "disabled"},
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    if not resp.ok:
        print(f"Claude API call failed ({resp.status_code}): {resp.text}")
    resp.raise_for_status()

    data = resp.json()
    text_blocks = [block["text"] for block in data["content"] if block["type"] == "text"]
    return "".join(text_blocks)
