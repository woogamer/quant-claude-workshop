"""DART OpenAPI — 최근 대량보유(5% 룰) 공시 fetch.

워크샵 흐름:
  1. 이 스크립트 실행 → 최근 N일 대량보유 공시 목록 출력
  2. Claude 안에서: "scripts/dart_shareholding.py 결과 중 매수 후보 골라줘"
  3. Claude 가 공시 내용 보고 → 종목 추천 → 확인 후 buy_stock 호출

사용법: python scripts/dart_shareholding.py [일수]
예시: python scripts/dart_shareholding.py 3
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_dart_key() -> str:
    cfg_path = ROOT / "config.yaml"
    if not cfg_path.exists():
        print("config.yaml 없음. setup.sh 먼저 실행.")
        sys.exit(1)
    cfg = yaml.safe_load(open(cfg_path))
    key = cfg.get("dart", {}).get("api_key", "")
    if not key or key == "YOUR_DART_API_KEY_HERE":
        print("DART API 키가 비어있음. config.yaml 의 dart.api_key 채우세요.")
        print("발급: https://opendart.fss.or.kr/")
        sys.exit(1)
    return key


def fetch_recent(api_key: str, days_back: int = 3) -> list[dict]:
    """공시 list API 로 최근 며칠 공시 중 '대량보유' 보고만 필터."""
    end = datetime.now()
    start = end - timedelta(days=days_back)

    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": api_key,
        "bgn_de": start.strftime("%Y%m%d"),
        "end_de": end.strftime("%Y%m%d"),
        "pblntf_ty": "D",  # 지분공시 (대량보유, 임원·주요주주 등)
        "page_count": 100,
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "000":
        print(f"DART API 오류: {data.get('message')}")
        return []

    items = data.get("list", [])
    # 대량보유 관련 공시만 (5% 룰)
    keywords = ["대량보유", "주식등의대량보유", "임원·주요주주"]
    return [
        it for it in items
        if any(kw in it.get("report_nm", "") for kw in keywords)
    ]


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    api_key = load_dart_key()
    items = fetch_recent(api_key, days_back=days)

    print(f"최근 {days}일 대량보유/지분 공시: {len(items)}건\n")
    for it in items[:25]:
        print(f"  {it['rcept_dt']} {it.get('corp_name', '')[:18]:<20} {it['report_nm'][:50]}")

    output = [
        {
            "date": it["rcept_dt"],
            "corp_code": it.get("corp_code"),
            "corp_name": it.get("corp_name"),
            "stock_code": it.get("stock_code"),
            "report": it["report_nm"],
            "rcept_no": it.get("rcept_no"),
            "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={it.get('rcept_no')}",
        }
        for it in items[:25]
    ]
    print("\n--- Claude 용 JSON (상위 25건) ---")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
