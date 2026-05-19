# quant-claude-workshop

AI 도구로 한국 주식 모의투자를 체험하는 워크샵 키트.
**자연어 매매**와 **간단한 알고리즘 매매** 두 가지를 다룹니다.

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

- "삼성전자 현재가 알려줘"
- "내 모의계좌 잔고 보여줘"
- "삼성전자 외국인 매매 동향 어때?"
- "삼성전자 1주 시장가로 매수해줘" → Claude가 확인 후 `buy_stock` 호출

`.mcp.json` 이 KIS MCP 서버를 자동 로드해서 Claude가 위 도구들을 사용합니다.

## Goal 2 — 알고리즘 신호 + Claude 판단

스크립트가 **신호를 계산**하고, **Claude가 신호를 읽고 매매 결정**하는 패턴.
멤버가 직접 실행해보거나, 또는 Claude에게 "골든크로스 신호 보고 매수 판단해줘" 같이 시킴.

### 시나리오 A — 이동평균 골든크로스

```bash
python scripts/golden_cross.py 005930
# 출력: {"signal": "GOLDEN_CROSS_BUY", "ma5": ..., "ma20": ..., ...}
```

Claude 안에서:
> `scripts/golden_cross.py 005930` 실행해서 결과 보고 매수할지 판단해줘. 매수하면 1주만.

Claude 는 → Bash 로 스크립트 실행 → JSON 파싱 → signal 확인 → 사용자에게 확인 받고 `buy_stock` 호출.

### 시나리오 B — DART 대량보유 공시

```bash
python scripts/dart_shareholding.py 3
# 출력: 최근 3일 5%룰 대량보유 공시 + 임원·주요주주 보고
```

Claude 안에서:
> `scripts/dart_shareholding.py 3` 결과에서 매수 후보 1~2개 골라줘. 이유도 같이.

Claude 는 공시 목록 보고 → 종목명·신고 종류로 판단 → 후보 제시 → 사용자 OK 후 매수.

> 두 시나리오 모두 **Claude가 자동 매매하지 않습니다.** 신호를 읽고 후보를 제시할 뿐, `buy_stock` 호출 직전에 사용자 확인을 요청합니다.

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
│   └── dart_shareholding.py  # DART 대량보유 공시 (Goal 2 시나리오 B)
├── config.example.yaml    # 키 입력 템플릿
└── setup.sh               # 첫 셋업 (config.yaml 생성)
```

## 자주 묻는 문제

- **`config.yaml 없음`** → `./setup.sh` 다시 실행
- **`401 Unauthorized`** → KIS App Key / Secret 오타. config.yaml 직접 확인
- **`tr_id 오류`** → 모의투자 계좌가 아닐 가능성. 실계좌면 `vendor/kis_api.py` 의 BASE_URL 과 tr_id 변경 필요
- **Claude 가 buy_stock 안 부름** → `claude` 재실행 (MCP 서버 등록 갱신)

## 운영 모드 vs 워크샵 모드

이 레포는 **워크샵 / 학습용 자립 키트**. 실제 자동매매 시스템 (`quant-claude` 본 레포) 과는 분리되어 있습니다.
멤버는 자기 모의계좌로 자유롭게 실험.
