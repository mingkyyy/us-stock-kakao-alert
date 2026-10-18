"""Refresh the Kakao access token and send a 'to me' message."""
from __future__ import annotations

import json
import os

import requests

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


def refresh_access_token(rest_api_key: str, refresh_token: str, client_secret: str) -> dict:
    """Returns the token response dict. May contain a NEW refresh_token
    (Kakao rotates it sometimes) — caller must persist it if present."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": rest_api_key,
            "refresh_token": refresh_token,
            "client_secret": client_secret,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def send_to_me(access_token: str, message: str) -> None:
    template = {
        "object_type": "text",
        "text": message,
        "link": {
            "web_url": "https://www.google.com/finance",
            "mobile_web_url": "https://www.google.com/finance",
        },
    }
    resp = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template)},
        timeout=10,
    )
    resp.raise_for_status()


def send_report(message: str) -> str | None:
    """Sends the report. Returns a new refresh_token if Kakao rotated it,
    else None."""
    rest_api_key = os.environ["KAKAO_REST_API_KEY"]
    refresh_token = os.environ["KAKAO_REFRESH_TOKEN"]
    client_secret = os.environ["KAKAO_CLIENT_SECRET"]

    token_data = refresh_access_token(rest_api_key, refresh_token, client_secret)
    send_to_me(token_data["access_token"], message)

    return token_data.get("refresh_token")
