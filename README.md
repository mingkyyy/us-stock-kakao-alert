# 미장 마감 포트폴리오 텔레그램 알림

매일 미국 주식시장 마감 후, 보유 종목의 전일 대비 수익률 / 평단가 대비 수익률 / 전체 포트폴리오 수익률을 텔레그램 봇으로 받습니다.

## 구조

- `portfolio.json` — 보유 종목(티커, 수량, 평단가). 매수/매도할 때마다 직접 수정.
- `scripts/fetch_and_calc.py` — yfinance로 현재가/전일종가 조회 후 리포트 텍스트 생성.
- `scripts/telegram_send.py` — 텔레그램 봇 API로 메시지 전송.
- `main.py` — 위 과정을 순서대로 실행하는 진입점. GitHub Actions가 매일 이걸 실행.
- `.github/workflows/daily-stock-alert.yml` — 매일 미장 마감 후 자동 실행되는 스케줄러.

## 설정 순서

### 1. 텔레그램 봇 생성 (직접 진행)

1. 텔레그램 앱에서 **@BotFather** 검색 후 대화 시작
2. `/newbot` 입력 → 봇 이름(아무거나) → 봇 username(끝에 `bot` 포함 필수, 예: `my_stock_alert_bot`) 입력
3. 생성 완료되면 **봇 토큰**이 나옴 (`123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` 형식) → 복사해두기
4. 방금 만든 봇을 검색해서 **대화 시작** (`/start` 아무 메시지나 전송) — 봇이 나에게 메시지를 보내려면 내가 먼저 봇과 대화를 시작해야 함

### 2. 내 chat_id 확인

1. 1단계에서 봇한테 아무 메시지나 보낸 직후, 브라우저에서 아래 주소 접속 (`<봇토큰>` 자리에 3단계에서 받은 토큰 입력):
   ```
   https://api.telegram.org/bot<봇토큰>/getUpdates
   ```
2. 응답 JSON에서 `"chat":{"id":123456789, ...}` 부분의 숫자를 복사 — 이게 내 `chat_id`

### 3. GitHub repo Secrets 등록

repo Settings → Secrets and variables → Actions 에서 아래 2개를 등록:

| Secret 이름 | 값 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | 1단계에서 받은 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 2단계에서 확인한 chat_id |

카카오 때와 달리 토큰 만료/갱신이 없어서 이 2개만 등록하면 끝입니다.

### 4. 포트폴리오 입력

`portfolio.json`을 실제 보유 종목으로 수정 후 push:

```json
[
  {"ticker": "AAPL", "shares": 10, "avg_price": 150.0}
]
```

### 5. 테스트

- 로컬 테스트 (전송 없이 계산만): `python scripts/fetch_and_calc.py`
- 전체 테스트 (텔레그램 전송 포함, Secrets 환경변수 필요): GitHub repo → Actions 탭 → "Daily US Stock Telegram Alert" → "Run workflow" 로 수동 실행

## 스케줄 참고

- 현재 cron은 매일(월~금) UTC 21:30에 실행 — 미장 마감(미 동부 16:00) 기준 최소 30분 후.
- 서머타임(3월~11월, EDT)에는 한국시간 새벽 5:30, 겨울(EST)에는 새벽 6:30에 실행됩니다.
- 더 정확히 맞추고 싶으면 `.github/workflows/daily-stock-alert.yml`의 cron 값을 계절별로 2개 등록해도 됩니다.
