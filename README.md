# 미장 마감 포트폴리오 + 뉴스 브리핑 텔레그램 알림

1. 매일 미국 주식시장 마감 후, 보유 종목의 전일 대비 수익률 / 평단가 대비 수익률 / 전체 포트폴리오 수익률을 텔레그램 봇으로 받습니다.
2. 매일 아침 7시 30분, 미국 증시 전반 + 보유 종목 관련 뉴스를 요약해서 받습니다.
3. 텔레그램 봇한테 `/buy`, `/sell` 명령어를 보내면 `portfolio.json`이 자동으로 업데이트됩니다.

## 구조

- `portfolio.json` — 보유 종목(티커, 수량, 평단가). `/buy`, `/sell` 명령어로 자동 수정되거나 직접 수정 가능.
- `scripts/fetch_and_calc.py` — yfinance로 현재가/전일종가 조회 후 포트폴리오 리포트 텍스트 생성.
- `scripts/fetch_news.py` — Google News RSS로 시장 전반/종목별 뉴스 헤드라인 수집 (API 키 불필요).
- `scripts/summarize_news.py` — 수집한 헤드라인을 Claude API로 한국어 브리핑으로 요약.
- `scripts/telegram_send.py` — 텔레그램 봇 API로 메시지 전송.
- `scripts/telegram_poll.py` — 텔레그램 메시지를 가져오고(getUpdates) 답장을 보내는(sendMessage) 헬퍼.
- `scripts/portfolio_commands.py` — `/buy`, `/sell`, `/list` 명령어 파싱 및 `portfolio.json` 반영 로직.
- `report_main.py` — 포트폴리오 리포트 진입점. 미장 마감 후 GitHub Actions가 실행. (Vercel이 `main.py`를 자동으로 Python 앱 엔트리포인트로 오인해서 이 이름을 씁니다)
- `news_main.py` — 뉴스 브리핑 진입점. 매일 아침 7시 30분 GitHub Actions가 실행.
- `commands_main.py` — 텔레그램 명령어 폴링 진입점(구버전, 5분 간격). **Vercel webhook 설정 후엔 꺼두세요** (아래 참고).
- `.telegram_offset` — 폴링 방식이 마지막으로 처리한 텔레그램 메시지 번호. webhook으로 전환하면 더는 쓰이지 않음.
- `api/webhook.py` — **Vercel 서버리스 함수**. 텔레그램이 메시지 오는 즉시 호출해서 바로 답장. GitHub Contents API로 `portfolio.json`을 직접 읽고 커밋.
- `api/requirements.txt` — `api/webhook.py` 전용 의존성(가볍게 `requests`만).
- `.github/workflows/daily-stock-alert.yml` — 미장 마감 후 포트폴리오 리포트 스케줄러.
- `.github/workflows/daily-news-digest.yml` — 아침 7시 30분 뉴스 브리핑 스케줄러.
- `.github/workflows/telegram-commands.yml` — (구버전) 5분마다 텔레그램 명령어를 폴링하는 스케줄러.

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

### 3. Claude API 키 발급 (뉴스 브리핑용)

[console.anthropic.com](https://console.anthropic.com)에서 API 키 발급. 뉴스 요약 용도로는 호출량이 적어서 비용은 월 몇백 원 수준입니다.

### 4. GitHub repo Secrets 등록

repo Settings → Secrets and variables → Actions 에서 아래 3개를 등록:

| Secret 이름 | 값 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | 1단계에서 받은 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 2단계에서 확인한 chat_id |
| `ANTHROPIC_API_KEY` | 3단계에서 발급받은 Claude API 키 |

카카오 때와 달리 토큰 만료/갱신이 없어서 이대로 등록하면 끝입니다.

### 5. Actions 쓰기 권한 활성화 (명령어 기능용)

`/buy`, `/sell` 명령어로 `portfolio.json`을 자동 커밋하려면 Actions가 repo에 push할 권한이 필요합니다.

repo Settings → Actions → General → **Workflow permissions** → **Read and write permissions** 선택 → Save

### 6. 포트폴리오 입력

`portfolio.json`을 실제 보유 종목으로 수정 후 push (이후로는 텔레그램 명령어로도 수정 가능):

```json
[
  {"ticker": "AAPL", "shares": 10, "avg_price": 150.0}
]
```

### 7. (추천) Vercel webhook으로 즉시 답장 설정

폴링(5단계)은 평균 2~3분, 최악의 경우 GitHub 부하에 따라 훨씬 더 걸립니다. **즉시 답장**을 받으려면 Vercel에 webhook 함수를 배포하세요.

1. **GitHub PAT 발급** (이 repo의 `portfolio.json`을 커밋할 권한용): [github.com/settings/tokens](https://github.com/settings/tokens) → "Generate new token (Fine-grained)" → 이 repo 선택 → Permissions에서 **Contents: Read and write** 설정 → 생성 → 토큰 복사
2. **Vercel 가입/연결**: [vercel.com](https://vercel.com) 에서 **GitHub으로 로그인** → "Add New..." → "Project" → 이 repo(`us-stock-kakao-alert`) 선택 → Import
3. **환경 변수 등록**: Vercel 프로젝트 → Settings → Environment Variables 에서 아래 4개 등록 후 Deploy
   | 이름 | 값 |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | 봇 토큰 |
   | `TELEGRAM_CHAT_ID` | 내 chat_id |
   | `GH_TOKEN` | 1단계에서 발급한 GitHub PAT |
   | `GITHUB_REPOSITORY` | `<본인 깃허브 아이디>/us-stock-kakao-alert` |
4. 배포 완료되면 `https://<프로젝트명>.vercel.app` 같은 URL이 생김
5. **텔레그램에 webhook 등록** — 브라우저에서 아래 주소 접속 (`<봇토큰>`, `<vercel URL>` 자리 채워서):
   ```
   https://api.telegram.org/bot<봇토큰>/setWebhook?url=<vercel URL>/api/webhook
   ```
   `{"ok":true,"result":true,...}` 응답 오면 성공
6. **구버전 폴링 끄기**: webhook과 폴링(`getUpdates`)은 동시에 쓸 수 없어요 (텔레그램이 충돌 에러를 냄). `.github/workflows/telegram-commands.yml` 파일을 삭제하거나, repo Settings → Actions에서 그 워크플로우를 비활성화(Disable workflow)하세요.

이후로는 봇한테 메시지 보내면 1~2초 안에 답장이 옵니다.

### 8. 테스트

- 포트폴리오 리포트 계산만: `python scripts/fetch_and_calc.py`
- 포트폴리오 리포트 전체(텔레그램 전송 포함): GitHub repo → Actions 탭 → "Daily US Stock Telegram Alert" → "Run workflow"
- 뉴스 브리핑 전체(텔레그램 전송 포함): GitHub repo → Actions 탭 → "Daily US Stock News Digest" → "Run workflow"
- 텔레그램 명령어(webhook): 봇한테 바로 `/list` 보내고 몇 초 안에 답장 오는지 확인

## 텔레그램 명령어

봇한테 아래 메시지를 보내면 `portfolio.json`이 자동으로 수정되고 확인 답장이 옵니다. Vercel webhook이면 즉시, 구버전 폴링이면 최대 몇 분 걸릴 수 있어요.

| 명령어 | 설명 | 예시 |
|---|---|---|
| `/buy TICKER 수량 가격` | 매수 반영 (기존 종목이면 평단가 재계산) | `/buy AAPL 10 150.5` |
| `/sell TICKER 수량` | 매도 반영 (전량 매도 시 목록에서 제거) | `/sell AAPL 3` |
| `/list` | 현재 포트폴리오 보기 | `/list` |
| `/help` | 명령어 목록 보기 | `/help` |

본인 chat_id로 보낸 메시지만 처리되고, 다른 사람이 봇에게 보낸 메시지는 무시됩니다.

## 스케줄 참고

- **포트폴리오 리포트**: 매일(월~금) UTC 21:30 — 미장 마감(미 동부 16:00) 기준 최소 30분 후. 서머타임(3~11월, EDT)엔 한국시간 새벽 5:30, 겨울(EST)엔 새벽 6:30.
- **뉴스 브리핑**: 매일(주말 포함) UTC 22:30 = 한국시간 아침 7:30 (한국은 서머타임 없어서 연중 고정).
- **텔레그램 명령어**: 5분마다 확인.
- GitHub Actions의 `schedule`은 정시 실행을 보장하지 않습니다 — 서버 부하가 높으면 지연될 수 있습니다 (공식 문서에 명시된 제약).
- 더 정확히 맞추고 싶으면 각 workflow 파일의 cron 값을 조정하면 됩니다.
