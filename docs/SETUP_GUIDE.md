# 워크샵 사전 준비 가이드

**워크샵**: AI로 모의 주식 매매해보기 — 2026/6/4 (수) 19:00

---

## 한 줄 요약

워크샵 당일 노트북 들고 오시면 **GitHub 페이지에서 버튼 1개 눌러 Codespace를 띄우고, Claude에게 "엔비디아 1주 매수해줘" 라고 말하면 진짜 주문이 들어가는** 모습을 보고 직접 따라 해봅니다.

준비는 4개. 시간 합치면 약 50분.

---

## 사전 준비 4가지

### 1. GitHub 계정 (5분)

[github.com](https://github.com) 가입.
이미 있으시면 패스. 무료 계정으로 충분합니다 (실습용 Codespace 60시간/월 무료 포함).

### 2. KIS 모의투자 신청 + API 키 발급 (30분)

워크샵은 저녁이라 한국장이 닫혀있어서 **해외주식 모의투자도 같이 신청 필수**.
다행히 한국투자증권은 **"상시 모의투자"** 하나에서 국내·해외 같이 됩니다.

#### 2-1. 한국투자증권 MTS 에서 모의투자 신청

스마트폰에 한국투자증권 앱(MTS) 설치 + 로그인 (계정 없으면 가입).

**a.** 메뉴 → **모의투자현황** → **상시 모의투자**

![MTS 모의투자현황 메뉴](images/01_mts_menu.jpg)

**b.** 참여 대회 중 **상시 모의투자** 선택

![상시 모의투자 카드 선택](images/02_mts_select_contest.jpg)

**c.** 참가신청 화면에서 **국내주식+해외주식 (5억원 / 3개월)** 체크
   → 워크샵에서 미국 종목까지 거래 가능

![리그 선택 — 국내+해외 5억원](images/03_mts_signup_league.jpg)

**d.** 통합증거금 **신청** + 확인/동의 + 개인정보 활용 동의 → **확인**

![통합증거금 + 동의 + 확인](images/04_mts_signup_confirm.jpg)

→ 신청 완료 후 **모의계좌번호** (8자리 숫자, 예: `50189***`) 가 발급됩니다. 2-2 에서 필요.

#### 2-2. KIS Developers 포털에서 API 키 발급

**a.** [한국투자증권 API 포털](https://apiportal.koreainvestment.com/) 회원가입 → 로그인

**b.** **KIS Developers 서비스 신청하기** → **모의투자계좌** 체크 → 2-1 에서 받은 **모의계좌번호 입력** → 인증

![KIS Developers 서비스 신청](images/05_kis_developers_apply.png)

**c.** 신청 완료 후 발급된 행에서 **APP Key 복사**, **APP Secret 복사**, **계좌번호** 확인

![APP Key / APP Secret / 계좌번호 발급 완료](images/06_kis_apikey_issued.png)

이 3개 (App Key · App Secret · 계좌번호) 를 워크샵 당일 `./setup.sh` 에서 입력합니다. 잊지 않게 메모장에 잠깐 저장해두세요.

> KIS 본 사이트 ([securities.koreainvestment.com](https://securities.koreainvestment.com)) 계정과는 별개입니다.
> 모의투자라 진짜 돈은 안 듭니다. 그래도 보안 위해 API 키는 다른 사람에게 안 보이게.

### 3. Anthropic Claude Pro 결제 (5분)

[claude.ai](https://claude.ai) → 로그인 → 우상단 프로필 → **Subscribe** → Pro 선택 ($20/월).
워크샵 후 해지 가능 (한 달만 결제해도 OK).

> Pro 가입해야 Claude Code (CLI) 가 사용 가능합니다. Free 계정으로는 안 됩니다.

### 4. 노트북 (당일 지참)

Mac / Windows / Linux 다 가능.
크롬·엣지·사파리 등 최신 브라우저 + 인터넷 연결만 되면 됨.

> 노트북에 아무것도 설치 안 합니다. 모든 작업은 Codespaces (브라우저) 에서.

---

## 워크샵 당일 흐름 (실습 30분)

발표 15분 듣고, 그 다음 본인 노트북으로 따라 합니다.

### Step 1 — Codespace 띄우기 (2분)

브라우저로 **https://github.com/woogamer/quant-claude-workshop** 접속 →
우상단 초록 **`<> Code`** 버튼 → **`Codespaces` 탭** → **`Create codespace on master`**.

1~2분 부팅 대기. 브라우저 안에 VS Code 가 열리고 터미널이 자동으로 보입니다.

### Step 2 — KIS 키 입력 (3분)

터미널에서:
```bash
./setup.sh
```

물어보는 대로 입력:
- KIS App Key — 모의투자 포털에서 발급받은 키
- KIS App Secret — 같은 페이지에서 발급받은 시크릿
- 계좌번호 — `50012345-01` 형식
- DART API Key — 엔터로 스킵해도 됨 (선택)

### Step 3 — 연결 확인 (1분)

```bash
python scripts/demo_price.py 005930
```
"삼성전자 현재가 ... 정상 연결 확인 완료" 가 나오면 OK.

### Step 4 — Claude Code 실행 (2분)

```bash
claude
```

첫 실행 시 브라우저 OAuth 창이 자동으로 뜹니다. claude.ai 로그인하면 끝.

### Step 5 — 자연어 매매 따라하기 (15분)

Claude 안에서 차례로:

```
> 내 미국주식 잔고 보여줘
> 엔비디아 현재가 알려줘
> 엔비디아 골든크로스 신호 어때?
> 그럼 1주 매수해줘
> 내 잔고 다시 보여줘
```

워크샵 발표 시간(19:00)에는 미국장이 안 열려있을 수 있어서, 시연 매수가 거절될 수 있습니다. 그땐 **"22:30 이후 본인 환경에서 다시 시도하면 진짜 체결됩니다"** 라고 알려드릴 예정.

### Step 6 — 자유 실험 (7분)

다른 종목 / 다른 신호 / 다른 명령 자유롭게:
- "DART 공시에서 내부자 매수 종목 찾아줘"
- "테슬라 1주 매수해줘"
- "삼성전자 골든크로스 5/20 → 10/30으로 바꿔서 신호 다시 봐줘"

---

## 자주 막히는 5가지

| 증상 | 해결 |
|---|---|
| Codespace 부팅 실패 | GitHub 무료 한도(60h/월) 다 썼을 가능성. 옆 사람 화면 같이 보기 |
| `401 Unauthorized` | KIS App Key 또는 Secret 오타. config.yaml 직접 확인 (탭/공백 들어갔는지) |
| Claude OAuth 안 열림 | Codespace 우측 하단 "포트 패널" → 콜백 URL 직접 클릭 |
| `모의투자 장시작전 입니다` | 한국장 시간 외(15:30~) 인데 한국 종목 매수 시도. 미국 종목(엔비디아 등)으로 |
| Claude 가 매수 도구 안 부름 | 터미널에서 `Ctrl+C` 로 `claude` 종료 후 다시 `claude` 실행 |

해결 안 되면 워크샵 진행자에게 손 들어주세요.

---

## 워크샵 후

- 키트 레포는 그대로 둡니다. 본인 fork 떠서 자유롭게 이어가셔도 됩니다.
- Claude Pro 구독은 한 달 후 해지 가능. 이어서 실험하고 싶으면 유지.
- 더 깊게 들어가고 싶은 분은 진행자에게 알려주세요. keep in touch 그룹 안내드립니다.

---

## 자료

- 워크샵 키트 레포: https://github.com/woogamer/quant-claude-workshop
- KIS API 포털: https://apiportal.koreainvestment.com/
- Claude 사이트: https://claude.ai
- DART OpenAPI: https://opendart.fss.or.kr/
