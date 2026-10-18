# 미장 마감 포트폴리오 카톡 알림

매일 미국 주식시장 마감 후, 보유 종목의 전일 대비 수익률 / 평단가 대비 수익률 / 전체 포트폴리오 수익률을 카카오톡 "나에게 보내기"로 받습니다.

## 구조

- `portfolio.json` — 보유 종목(티커, 수량, 평단가). 매수/매도할 때마다 직접 수정.
- `scripts/fetch_and_calc.py` — yfinance로 현재가/전일종가 조회 후 리포트 텍스트 생성.
- `scripts/kakao_send.py` — Access Token 갱신 후 "나에게 보내기" 전송.
- `scripts/update_github_secret.py` — Kakao가 refresh_token을 재발급하면 GitHub Secret에 다시 저장.
- `scripts/get_kakao_token.py` — **최초 1회만** 로컬에서 직접 실행하는 OAuth 인증 헬퍼.
- `main.py` — 위 과정을 순서대로 실행하는 진입점. GitHub Actions가 매일 이걸 실행.
- `.github/workflows/daily-stock-alert.yml` — 매일 미장 마감 후 자동 실행되는 스케줄러.

## 설정 순서

### 1. 카카오 디벨로퍼스 앱 등록 (직접 진행)

1. https://developers.kakao.com 에서 로그인 후 "애플리케이션 추가"
2. 앱 설정 → "카카오 로그인" 활성화
3. "카카오 로그인" → "Redirect URI" 등록: `https://localhost.com` (아무 URL이든 가능, 실제로 서버를 띄울 필요 없음)
4. "카카오 로그인" → "동의항목"에서 **카카오톡 메시지 전송** 항목을 "필수 동의"로 설정
5. 앱 설정 → "앱 키"에서 **REST API 키** 복사해두기

### 2. 최초 1회 OAuth 인증으로 refresh_token 발급

로컬에서 실행 (이 단계는 본인 로그인이 필요해서 자동화할 수 없습니다):

```bash
cd us-stock-kakao-alert
pip install -r requirements.txt
```

`scripts/get_kakao_token.py` 파일을 열어 `REST_API_KEY` 값을 1단계에서 복사한 키로 바꾼 뒤:

```bash
python scripts/get_kakao_token.py
```

안내에 따라 브라우저에서 로그인 → 리다이렉트된 URL의 `code=` 값을 복사해서 입력하면 `access_token`, `refresh_token`이 출력됩니다.

### 3. GitHub repo 생성 및 Secrets 등록

이 폴더를 GitHub repo로 push한 뒤, repo Settings → Secrets and variables → Actions 에서 아래 3개를 등록:

| Secret 이름 | 값 |
|---|---|
| `KAKAO_REST_API_KEY` | 1단계에서 복사한 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | 2단계에서 발급받은 refresh_token |
| `GH_PAT` | repo secret 쓰기 권한이 있는 Personal Access Token (아래 참고) |

**`GH_PAT` 발급**: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained token 생성, 이 repo에 대해 "Secrets" 권한을 Read/Write로 설정. (refresh_token이 재발급될 때마다 workflow가 이 토큰으로 `KAKAO_REFRESH_TOKEN` secret을 스스로 갱신합니다.)

### 4. 포트폴리오 입력

`portfolio.json`을 실제 보유 종목으로 수정 후 push:

```json
[
  {"ticker": "AAPL", "shares": 10, "avg_price": 150.0}
]
```

### 5. 테스트

- 로컬 테스트 (카톡 전송 없이 계산만): `python scripts/fetch_and_calc.py`
- 전체 테스트 (카톡 전송 포함, Secrets 환경변수 필요): GitHub repo → Actions 탭 → "Daily US Stock Kakao Alert" → "Run workflow" 로 수동 실행

## 스케줄 참고

- 현재 cron은 매일(월~금) UTC 21:30에 실행 — 미장 마감(미 동부 16:00) 기준 최소 30분 후.
- 서머타임(3월~11월, EDT)에는 한국시간 새벽 5:30, 겨울(EST)에는 새벽 6:30에 실행됩니다.
- 더 정확히 맞추고 싶으면 `.github/workflows/daily-stock-alert.yml`의 cron 값을 계절별로 2개 등록해도 됩니다.
