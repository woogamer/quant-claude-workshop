"""한국투자증권(KIS) 모의투자 API 래퍼 — 워크샵 vendor 사본.

원본: ~/quant-bot-template/core/kis_api.py
워크샵용으로 stdlib logging 사용 + 토큰 캐시 경로를 프로젝트 루트로 변경.
"""

import fcntl
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger("kis_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

BASE_URL = "https://openapivts.koreainvestment.com:29443"

_MAX_RETRIES = 3
_RETRY_DELAY = 1.0

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TOKEN_CACHE = _PROJECT_ROOT / ".kis_token_cache.json"
_TOKEN_SAFETY_MARGIN = 600


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    last_resp = None
    for attempt in range(_MAX_RETRIES):
        resp = requests.request(method, url, **kwargs)
        if resp.status_code < 500:
            return resp
        last_resp = resp
        if attempt < _MAX_RETRIES - 1:
            time.sleep(_RETRY_DELAY)
    return last_resp


class KISClient:
    def __init__(self, app_key: str, app_secret: str, account_no: str) -> None:
        self._app_key = app_key
        self._app_secret = app_secret
        self._account_no = account_no
        self._access_token: str = ""
        self._token_expires_at: float = 0

    def _load_cached_token(self) -> bool:
        if not _TOKEN_CACHE.exists():
            return False
        try:
            with open(_TOKEN_CACHE) as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                data = json.load(f)
            if data.get("app_key") != self._app_key:
                return False
            expires_at = data.get("expires_at", 0)
            if time.time() >= expires_at - _TOKEN_SAFETY_MARGIN:
                return False
            self._access_token = data["access_token"]
            self._token_expires_at = expires_at
            return True
        except Exception as e:
            log.warning(f"KIS 토큰 캐시 로드 실패: {e}")
            return False

    def _save_cached_token(self) -> None:
        try:
            _TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
            tmp = _TOKEN_CACHE.with_suffix(".tmp")
            with open(tmp, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump({
                    "app_key": self._app_key,
                    "access_token": self._access_token,
                    "expires_at": self._token_expires_at,
                }, f)
            os.replace(tmp, _TOKEN_CACHE)
            os.chmod(_TOKEN_CACHE, 0o600)
        except Exception as e:
            log.warning(f"KIS 토큰 캐시 저장 실패: {e}")

    def authenticate(self) -> str:
        if self._load_cached_token():
            log.info("KIS 토큰 캐시 재사용")
            return self._access_token

        url = f"{BASE_URL}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data.get("access_token", "")
        self._token_expires_at = time.time() + 86000
        self._save_cached_token()
        log.info("KIS 인증 완료 (신규 발급)")
        return self._access_token

    def _ensure_auth(self) -> None:
        if not self._access_token or time.time() >= self._token_expires_at - _TOKEN_SAFETY_MARGIN:
            if not self._load_cached_token():
                self.authenticate()

    def _headers(self, tr_id: str) -> dict[str, str]:
        return {
            "authorization": f"Bearer {self._access_token}",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
            "tr_id": tr_id,
        }

    def get_price(self, ticker: str) -> dict[str, Any]:
        self._ensure_auth()
        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker}
        resp = _request_with_retry(
            "GET", url, params=params,
            headers=self._headers("FHKST01010100"), timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_balance(self) -> dict[str, Any]:
        self._ensure_auth()
        url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance"
        params = {
            "CANO": self._account_no[:8],
            "ACNT_PRDT_CD": self._account_no[8:],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        resp = _request_with_retry(
            "GET", url, params=params,
            headers=self._headers("VTTC8434R"), timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_investor_trend(self, ticker: str) -> dict[str, Any]:
        self._ensure_auth()
        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker}
        resp = _request_with_retry(
            "GET", url, params=params,
            headers=self._headers("FHKST01010900"), timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def buy(self, ticker: str, qty: int, price: int = 0) -> dict[str, Any]:
        return self._place_order(ticker, qty, price, side="buy")

    def sell(self, ticker: str, qty: int, price: int = 0) -> dict[str, Any]:
        return self._place_order(ticker, qty, price, side="sell")

    def _place_order(self, ticker: str, qty: int, price: int, *, side: str) -> dict[str, Any]:
        self._ensure_auth()
        tr_id = "VTTC0802U" if side == "buy" else "VTTC0801U"
        url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"
        ord_dvsn = "01" if price == 0 else "00"
        payload = {
            "CANO": self._account_no[:8],
            "ACNT_PRDT_CD": self._account_no[8:],
            "PDNO": ticker,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price),
        }
        resp = _request_with_retry(
            "POST", url, json=payload,
            headers=self._headers(tr_id), timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        action = "매수" if side == "buy" else "매도"
        log.info(f"주문 완료: {action} {ticker} {qty}주 (가격: {price or '시장가'})")
        return result

    # ------------------------------------------------------------------ #
    #  해외주식 (미국)
    # ------------------------------------------------------------------ #

    def get_overseas_price(self, symbol: str, exchange: str = "NAS") -> dict[str, Any]:
        """해외종목의 현재가를 조회합니다. exchange: NAS(나스닥), NYS(뉴욕), AMS(아멕스)."""
        self._ensure_auth()
        url = f"{BASE_URL}/uapi/overseas-price/v1/quotations/price"
        params = {"AUTH": "", "EXCD": exchange.upper(), "SYMB": symbol.upper()}
        resp = _request_with_retry(
            "GET", url, params=params,
            headers=self._headers("HHDFS00000300"), timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_overseas_balance(self, exchange: str = "NASD") -> dict[str, Any]:
        """해외주식 잔고 조회. exchange: NASD(전체미국), NYSE, AMEX."""
        self._ensure_auth()
        url = f"{BASE_URL}/uapi/overseas-stock/v1/trading/inquire-balance"
        params = {
            "CANO": self._account_no[:8],
            "ACNT_PRDT_CD": self._account_no[8:],
            "OVRS_EXCG_CD": exchange.upper(),
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }
        resp = _request_with_retry(
            "GET", url, params=params,
            headers=self._headers("VTTS3012R"), timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def buy_overseas(self, symbol: str, qty: int, price: float, exchange: str = "NASD") -> dict[str, Any]:
        """해외주식 매수 (모의투자는 지정가만)."""
        return self._place_overseas_order(symbol, qty, price, exchange, side="buy")

    def sell_overseas(self, symbol: str, qty: int, price: float, exchange: str = "NASD") -> dict[str, Any]:
        """해외주식 매도 (모의투자는 지정가만)."""
        return self._place_overseas_order(symbol, qty, price, exchange, side="sell")

    def _place_overseas_order(
        self, symbol: str, qty: int, price: float, exchange: str, *, side: str,
    ) -> dict[str, Any]:
        self._ensure_auth()
        tr_id = "VTTT1002U" if side == "buy" else "VTTT1006U"
        url = f"{BASE_URL}/uapi/overseas-stock/v1/trading/order"
        payload = {
            "CANO": self._account_no[:8],
            "ACNT_PRDT_CD": self._account_no[8:],
            "OVRS_EXCG_CD": exchange.upper(),
            "PDNO": symbol.upper(),
            "ORD_QTY": str(qty),
            "OVRS_ORD_UNPR": str(price),
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": "00",
            "SLL_TYPE": "" if side == "buy" else "00",
            "CTAC_TLNO": "",
            "MGCO_APTM_ODNO": "",
        }
        resp = _request_with_retry(
            "POST", url, json=payload,
            headers=self._headers(tr_id), timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        action = "매수" if side == "buy" else "매도"
        log.info(f"해외주문 완료: {action} {symbol} {qty}주 @ ${price} ({exchange})")
        return result
