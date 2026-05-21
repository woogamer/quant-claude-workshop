"""5일/20일 이동평균 골든크로스 / 데드크로스 감지.

한국 종목 (6자리 숫자) 과 미국 종목 (영문 심볼) 둘 다 지원.
  - 한국: pykrx 로 OHLCV
  - 미국: yfinance 로 OHLCV

사용법: python scripts/golden_cross.py [종목]
예시:
  python scripts/golden_cross.py 005930   # 삼성전자
  python scripts/golden_cross.py NVDA      # 엔비디아
"""

import json
import sys
from datetime import datetime, timedelta


def _is_korean_ticker(t: str) -> bool:
    return t.isdigit() and len(t) == 6


def _fetch_korean(ticker: str, lookback_days: int):
    from pykrx import stock
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y%m%d")
    df = stock.get_market_ohlcv(start, end, ticker)
    return df, "종가"


def _fetch_us(ticker: str, lookback_days: int):
    import yfinance as yf
    end = datetime.now()
    start = end - timedelta(days=lookback_days)
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    if isinstance(df.columns, type(df.columns)) and hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    return df, "Close"


def detect_cross(ticker: str, lookback_days: int = 60) -> dict:
    is_kr = _is_korean_ticker(ticker)
    market = "KR" if is_kr else "US"

    try:
        df, close_col = _fetch_korean(ticker, lookback_days) if is_kr else _fetch_us(ticker, lookback_days)
    except Exception as e:
        return {"ticker": ticker, "market": market, "error": f"OHLCV fetch 실패: {e}"}

    if df is None or df.empty or len(df) < 21:
        return {"ticker": ticker, "market": market, "error": "데이터 부족 (영업일 21일 필요)"}

    df["MA5"] = df[close_col].rolling(5).mean()
    df["MA20"] = df[close_col].rolling(20).mean()

    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    golden = bool(yesterday["MA5"] < yesterday["MA20"] and today["MA5"] >= today["MA20"])
    dead = bool(yesterday["MA5"] > yesterday["MA20"] and today["MA5"] <= today["MA20"])

    signal = "GOLDEN_CROSS_BUY" if golden else ("DEAD_CROSS_SELL" if dead else "HOLD")

    return {
        "ticker": ticker,
        "market": market,
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "close": round(float(today[close_col]), 2),
        "ma5": round(float(today["MA5"]), 2),
        "ma20": round(float(today["MA20"]), 2),
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
