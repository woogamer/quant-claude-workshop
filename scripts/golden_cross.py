"""5일/20일 이동평균 골든크로스 / 데드크로스 감지.

워크샵 흐름:
  1. 이 스크립트 실행 → 신호 JSON 출력
  2. Claude 안에서: "scripts/golden_cross.py 005930 결과 보고 매수 판단해줘"
  3. Claude 가 신호 읽고 → 확인 후 buy_stock 호출

사용법: python scripts/golden_cross.py [종목코드]
예시: python scripts/golden_cross.py 005930
"""

import json
import sys
from datetime import datetime, timedelta

from pykrx import stock


def detect_cross(ticker: str, lookback_days: int = 60) -> dict:
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y%m%d")

    df = stock.get_market_ohlcv(start_date, end_date, ticker)
    if df.empty or len(df) < 21:
        return {"ticker": ticker, "error": "데이터 부족 (영업일 기준 21일 필요)"}

    df["MA5"] = df["종가"].rolling(5).mean()
    df["MA20"] = df["종가"].rolling(20).mean()

    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    golden = bool(yesterday["MA5"] < yesterday["MA20"] and today["MA5"] >= today["MA20"])
    dead = bool(yesterday["MA5"] > yesterday["MA20"] and today["MA5"] <= today["MA20"])

    signal = "GOLDEN_CROSS_BUY" if golden else ("DEAD_CROSS_SELL" if dead else "HOLD")

    return {
        "ticker": ticker,
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "close": int(today["종가"]),
        "ma5": round(float(today["MA5"]), 1),
        "ma20": round(float(today["MA20"]), 1),
        "ma5_above_ma20": bool(today["MA5"] > today["MA20"]),
        "golden_cross_today": golden,
        "dead_cross_today": dead,
        "signal": signal,
        "interpretation": {
            "GOLDEN_CROSS_BUY": "5일선이 20일선 위로 돌파 — 단기 상승 시그널 (매수 고려)",
            "DEAD_CROSS_SELL": "5일선이 20일선 아래로 하향 돌파 — 단기 하락 시그널 (매도 고려)",
            "HOLD": "교차 없음 — 추세 유지 또는 관망",
        }[signal],
    }


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "005930"
    result = detect_cross(ticker)
    print(json.dumps(result, ensure_ascii=False, indent=2))
