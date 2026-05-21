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
    # 지분공시 중 매매 시그널이 될 만한 보고만:
    # - "대량보유" (5% 룰)
    # - 임원·주요주주 보고 (가운뎃점 유니코드 다양해서 contains 두 개로 체크)
    def is_match(name: str) -> bool:
        if "대량보유" in name:
            return True
        if "임원" in name and "주요주주" in name:
            return True
        return False

    return [it for it in items if is_match(it.get("report_nm", ""))]


def _parse_int(s) -> int:
    try:
        return int(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return 0


def _parse_float(s) -> float:
    try:
        return float(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def fetch_insider_buying(api_key: str, days_back: int = 5, limit: int = 10) -> list[dict]:
    """임원·주요주주 보고 중 **순취득(양수)** 만 추출 — 내부자 매수 시그널.

    1) list.json 에서 days_back 일치 임원·주요주주 보고만
    2) 각 corp_code 에 대해 elestock.json 호출
    3) rcept_no 매칭 → 보고자별 증감 합산 → 양수만
    """
    items = fetch_recent(api_key, days_back=days_back)
    insider_reports = [
        it for it in items
        if "임원" in it.get("report_nm", "") and "주요주주" in it.get("report_nm", "")
        and it.get("stock_code")
    ]

    results: list[dict] = []
    seen: set[tuple] = set()
    for it in insider_reports:
        if len(results) >= limit:
            break
        corp_code = it.get("corp_code")
        rcept_no = it.get("rcept_no")
        key = (corp_code, rcept_no)
        if key in seen:
            continue
        seen.add(key)

        try:
            resp = requests.get(
                "https://opendart.fss.or.kr/api/elestock.json",
                params={"crtfc_key": api_key, "corp_code": corp_code},
                timeout=10,
            )
            data = resp.json()
        except Exception:
            continue

        if data.get("status") != "000":
            continue

        matched = [r for r in data.get("list", []) if r.get("rcept_no") == rcept_no]
        if not matched:
            continue

        net_shares = sum(_parse_int(r.get("sp_stock_lmp_irds_cnt")) for r in matched)
        if net_shares <= 0:
            continue

        net_rate = sum(_parse_float(r.get("sp_stock_lmp_irds_rate")) for r in matched)
        reporters = sorted({r.get("repror", "") for r in matched if r.get("repror")})
        positions = sorted({
            r.get("isu_exctv_ofcps", "") for r in matched
            if r.get("isu_exctv_ofcps") and r.get("isu_exctv_ofcps") != "-"
        })

        results.append({
            "date": it["rcept_dt"],
            "corp_name": it.get("corp_name"),
            "stock_code": it.get("stock_code"),
            "net_shares_acquired": net_shares,
            "net_rate_change_pct": round(net_rate, 4),
            "reporters": reporters,
            "positions": positions,
            "rcept_no": rcept_no,
            "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
        })

    return sorted(results, key=lambda x: -x["net_shares_acquired"])


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
