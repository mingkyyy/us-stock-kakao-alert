"""One-time helper: exchange a Kakao OAuth authorization code for
an access/refresh token pair. Run this locally and by hand — it needs
YOUR Kakao login in a browser, which this script cannot do for you.

Usage:
  1. Fill in REST_API_KEY and REDIRECT_URI below (must match the app's
     registered Redirect URI exactly).
  2. Open the printed authorize URL in your browser and log in.
  3. After logging in, your browser is redirected to:
       <REDIRECT_URI>?code=XXXXXXXX
     Copy the "code" value from that URL.
  4. Run this script and paste the code when prompted.
  5. Save the printed refresh_token as the GitHub secret KAKAO_REFRESH_TOKEN.
"""
import urllib.parse

import requests

REST_API_KEY = "<YOUR_REST_API_KEY>"
REDIRECT_URI = "https://localhost.com"

AUTHORIZE_URL = (
    "https://kauth.kakao.com/oauth/authorize?"
    + urllib.parse.urlencode(
        {
            "client_id": REST_API_KEY,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "talk_message",
        }
    )
)

TOKEN_URL = "https://kauth.kakao.com/oauth/token"


def main() -> None:
    print("1) 아래 URL을 브라우저에서 열고 로그인하세요:\n")
    print(AUTHORIZE_URL)
    print("\n2) 로그인 후 리다이렉트된 URL에서 code= 뒤의 값을 복사하세요.\n")

    code = input("code 값 입력: ").strip()

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": REST_API_KEY,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        timeout=10,
    )
    resp.raise_for_status()
    token_data = resp.json()

    print("\n=== 발급된 토큰 (refresh_token을 GitHub Secret으로 저장하세요) ===")
    print(f"access_token:  {token_data['access_token']}")
    print(f"refresh_token: {token_data['refresh_token']}")


if __name__ == "__main__":
    main()
