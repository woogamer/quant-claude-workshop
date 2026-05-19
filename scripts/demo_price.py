"""KIS API 연결 확인용 — Claude/MCP 없이 직접 Python에서 호출.

사용법: python scripts/demo_price.py [종목코드]
예시: python scripts/demo_price.py 005930
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml
from vendor.kis_api import KISClient


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "005930"

    config_path = ROOT / "config.yaml"
    if not config_path.exists():
        print(f"config.yaml 없음. setup.sh 먼저 실행하세요.")
        sys.exit(1)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    kis = cfg["kis"]
    client = KISClient(
        kis["app_key"], kis["app_secret"],
        kis["account_no"].replace("-", ""),
    )

    print(f"종목 조회 중: {ticker}")
    result = client.get_price(ticker)
    output = result.get("output", {})

    print(f"  현재가:   {output.get('stck_prpr')} 원")
    print(f"  전일대비: {output.get('prdy_vrss')} ({output.get('prdy_ctrt')}%)")
    print(f"  거래량:   {output.get('acml_vol')}")
    print()
    print("KIS API 정상 연결 확인 완료.")


if __name__ == "__main__":
    main()
