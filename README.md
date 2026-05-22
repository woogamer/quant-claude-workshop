# quant-claude-workshop

AI 도구로 한국 주식 모의투자를 체험하는 워크샵 키트.
**자연어 매매**와 **간단한 알고리즘 매매** 두 가지를 다룹니다.

📊 **발표 슬라이드**: <https://woogamer.github.io/quant-claude-workshop/>
(화살표 키로 이동 · `s` 발표자 노트 · `o` 전체 보기 · `f` 풀스크린)

## 사전 준비 (워크샵 전 각자)

1. **GitHub 계정** — 이미 있다면 OK
2. **KIS 모의투자 + API 키** — [한국투자증권 API 포털](https://apiportal.koreainvestment.com/) 가입 → 모의투자 신청 → App Key / App Secret 발급
3. **Anthropic 결제** — [claude.ai](https://claude.ai) → Pro 또는 Max 구독 (Claude Code 사용용)
4. **DART API 키 (선택)** — [opendart.fss.or.kr](https://opendart.fss.or.kr/) → 인증키 신청. Phase 2b 데모용

## 시작하기 (Codespaces)

1. 이 레포 우상단 **Code → Codespaces → Create codespace**
2. 부팅 완료까지 1~2분 대기 (Python + Node + Claude Code 자동 설치)
3. 터미널에서:
   ```bash
   ./setup.sh         # KIS 키 입력
   python scripts/demo_price.py 005930   # 연결 확인
   claude             # Claude Code 실행 → 자연어 매매 시작
   ```

## Goal 1 — 자연어 매매

`claude` 실행 후 자연어로:

### 한국주식 (정규장 09:00 ~ 15:30)
- "삼성전자 현재가 알려줘"
- "내 모의계좌 잔고 보여줘"
- "삼성전자 외국인 매매 동향 어때?"
- "삼성전자 1주 시장가로 매수해줘" → `buy_stock` 호출

### 미국주식 (한국시간 22:30 ~ 05:00, 서머타임 적용 시기)
- "엔비디아 현재가 알려줘" → `get_overseas_stock_price`
- "내 미국주식 잔고 보여줘" → `get_overseas_balance`
- "테슬라 1주 매수해줘" → Claude가 현재가 조회 후 지정가로 `buy_overseas_stock` 호출

> **장 시간 외 매수는 "모의투자 장시작전 입니다" 응답**. 한국 시간 외 시연이면 미국 주식 사용.
> KIS 모의투자는 **시장가 미지원** — Claude 가 현재가 조회 후 지정가로 자동 호출합니다.

`.mcp.json` 이 KIS MCP 서버를 자동 로드해서 Claude가 위 도구들을 사용합니다.

## Goal 2 — 알고리즘 신호 + 자연어 매매

**신호 계산도 Claude가 도구로 호출**합니다. 멤버는 터미널 안 가고 자연어만:

### 시나리오 A — 이동평균 골든크로스 (한국 / 미국 둘 다)

```
> 삼성전자 골든크로스 신호 어때?
[Claude: golden_cross_signal("005930") → {"market": "KR", "signal": "...", "ma5": ..., "ma20": ...}]

> 엔비디아는?
[Claude: golden_cross_signal("NVDA") → {"market": "US", ...}]

> 그럼 1주 매수해줘
[Claude: 한국이면 buy_stock, 미국이면 buy_overseas_stock 호출]
```

종목 인자가 **6자리 숫자 = 한국 (pykrx)**, **영문 심볼 = 미국 (yfinance)** 자동 판별.

### 시나리오 B — DART 대량보유 공시

```
> 최근 3일 대량보유 공시 보여줘
[Claude: dart_recent_disclosures 호출 → 공시 목록]

> 이 중에 매수 후보 1개 골라줘. 이유도 같이
[Claude: 종목명·보고 종류로 판단 → 추천 → 사용자 OK 후 buy_stock]
```

### 시나리오 C — 내부자 매수 시그널 (한 마디)

```
> DART 공시 찾아봐서 내부자 매수 시그널 있는 종목 매수해줘
[Claude: insider_buying_signals 호출 → 임원·주요주주 순취득 종목 리스트]
[Claude: 가장 강한 시그널 1~2개 추천 + 이유]
[사용자: "좋아 가장 강한 시그널 1주 매수"]
[Claude: buy_stock 호출]
```

내부적으로 DART `elestock.json` 의 `sp_stock_lmp_irds_cnt` (보유 증감 주식수) 가 양수인
보고만 추출 → 보고자별 합산 → 매수 강도 순 정렬.

### 알고리즘을 직접 수정하고 싶다면

도구 내부는 `scripts/golden_cross.py`, `scripts/dart_shareholding.py` 에 함수로 들어있습니다.
Claude에게 "5/20 → 10/30 이동평균으로 바꿔줘" 처럼 자연어로 코드 수정도 가능.

직접 터미널에서 실행해서 결과 확인하고 싶다면:
```bash
python scripts/golden_cross.py 005930
python scripts/dart_shareholding.py 3
```

> **모든 매매는 사용자 확인을 거칩니다.** Claude는 신호 해석/후보 제시까지만 자동이고,
> `buy_stock` 호출 직전엔 항상 "1주 매수하시겠습니까?" 확인을 받습니다.

## 디렉토리 구조

```
quant-claude-workshop/
├── .devcontainer/         # Codespaces 부팅 설정
├── .mcp.json              # Claude Code 가 자동 로드하는 MCP 서버 등록
├── vendor/kis_api.py      # KIS REST API 래퍼 (개별 멤버 환경에 자립)
├── mcp_servers/kis_broker.py  # MCP stdio 서버 (Claude ↔ KIS)
├── scripts/
│   ├── demo_price.py      # KIS 연결 확인 (자연어 매매 전 smoke test)
│   ├── golden_cross.py    # 이동평균 골든크로스 신호 (Goal 2 시나리오 A)
│   └── dart_shareholding.py  # DART 대량보유 + 내부자 매수 (Goal 2 시나리오 B, C)
├── config.example.yaml    # 키 입력 템플릿
└── setup.sh               # 첫 셋업 (config.yaml 생성)
```

## 자주 묻는 문제

- **`config.yaml 없음`** → `./setup.sh` 다시 실행
- **`401 Unauthorized`** → KIS App Key / Secret 오타. config.yaml 직접 확인
- **`tr_id 오류`** → 모의투자 계좌가 아닐 가능성. 실계좌면 `vendor/kis_api.py` 의 BASE_URL 과 tr_id 변경 필요
- **Claude 가 buy_stock 안 부름** → `claude` 재실행 (MCP 서버 등록 갱신)
- **`모의투자 장시작전 입니다` 응답** → 한국장 시간(09:00~15:30) 외이거나 미국장 시간(한국시간 22:30~05:00) 외. 시연 시간대 맞춰 한국/미국 선택
- **미국주식 USD 잔고 0** → KIS 모의투자 콘솔에서 USD 보유고 충전. 신규 가입자는 자동 부여되는 경우가 많음 (확인 후 안내)

## 운영 모드 vs 워크샵 모드

이 레포는 **워크샵 / 학습용 자립 키트**. 실제 자동매매 시스템 (`quant-claude` 본 레포) 과는 분리되어 있습니다.
멤버는 자기 모의계좌로 자유롭게 실험.
