"""KIS 모의투자 MCP 서버 — 워크샵용.

Claude Code 에서 이 서버를 통해 자연어로 매매 호출.
config.yaml 의 KIS 키를 사용.
"""

import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from vendor.kis_api import KISClient


def load_kis_client() -> KISClient:
    config_path = ROOT / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"{config_path} 없음. config.example.yaml 복사 후 키 채워넣으세요."
        )
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    kis = cfg["kis"]
    account = kis["account_no"].replace("-", "")
    return KISClient(kis["app_key"], kis["app_secret"], account)


kis: KISClient | None = None


def get_kis() -> KISClient:
    global kis
    if kis is None:
        kis = load_kis_client()
    return kis


app = Server("kis-broker")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_stock_price",
            description="종목의 현재가를 조회. ticker는 6자리 종목코드 (예: 005930 삼성전자).",
            inputSchema={
                "type": "object",
                "properties": {"ticker": {"type": "string", "description": "6자리 종목코드"}},
                "required": ["ticker"],
            },
        ),
        Tool(
            name="get_balance",
            description="모의계좌 잔고 조회. 보유종목, 예수금, 평가금액 반환.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_investor_trend",
            description="종목의 투자자별 매매동향 (외국인/기관/개인 순매수).",
            inputSchema={
                "type": "object",
                "properties": {"ticker": {"type": "string", "description": "6자리 종목코드"}},
                "required": ["ticker"],
            },
        ),
        Tool(
            name="buy_stock",
            description="주식 매수 주문. 반드시 사용자 확인 후 호출. price=0이면 시장가.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "qty": {"type": "integer"},
                    "price": {"type": "integer", "default": 0},
                },
                "required": ["ticker", "qty"],
            },
        ),
        Tool(
            name="sell_stock",
            description="주식 매도 주문. 반드시 사용자 확인 후 호출. price=0이면 시장가.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "qty": {"type": "integer"},
                    "price": {"type": "integer", "default": 0},
                },
                "required": ["ticker", "qty"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        client = get_kis()

        if name == "get_stock_price":
            result = client.get_price(arguments["ticker"])
            output = result.get("output", {})
            return [TextContent(type="text", text=json.dumps({
                "종목코드": arguments["ticker"],
                "현재가": output.get("stck_prpr"),
                "전일대비": output.get("prdy_vrss"),
                "등락률": output.get("prdy_ctrt"),
                "거래량": output.get("acml_vol"),
            }, ensure_ascii=False, indent=2))]

        elif name == "get_balance":
            result = client.get_balance()
            holdings = [
                {
                    "종목코드": item.get("pdno"),
                    "종목명": item.get("prdt_name"),
                    "수량": item.get("hldg_qty"),
                    "평균단가": item.get("pchs_avg_pric"),
                    "현재가": item.get("prpr"),
                    "수익률": item.get("evlu_pfls_rt"),
                }
                for item in result.get("output1", [])
                if int(item.get("hldg_qty", 0)) > 0
            ]
            summary = result.get("output2", [{}])[0] if result.get("output2") else {}
            return [TextContent(type="text", text=json.dumps({
                "보유종목": holdings,
                "총평가금액": summary.get("tot_evlu_amt"),
                "예수금": summary.get("dnca_tot_amt"),
            }, ensure_ascii=False, indent=2))]

        elif name == "get_investor_trend":
            result = client.get_investor_trend(arguments["ticker"])
            items = result.get("output", [])
            if items:
                today = items[0]
                return [TextContent(type="text", text=json.dumps({
                    "종목코드": arguments["ticker"],
                    "개인": today.get("prsn_ntby_qty"),
                    "외국인": today.get("frgn_ntby_qty"),
                    "기관": today.get("orgn_ntby_qty"),
                }, ensure_ascii=False, indent=2))]
            return [TextContent(type="text", text="데이터 없음")]

        elif name == "buy_stock":
            result = client.buy(arguments["ticker"], arguments["qty"], arguments.get("price", 0))
            return [TextContent(type="text", text=json.dumps({
                "결과": "매수 주문 완료",
                "종목코드": arguments["ticker"],
                "수량": arguments["qty"],
                "가격": arguments.get("price", 0) or "시장가",
                "응답": result.get("msg1", ""),
            }, ensure_ascii=False, indent=2))]

        elif name == "sell_stock":
            result = client.sell(arguments["ticker"], arguments["qty"], arguments.get("price", 0))
            return [TextContent(type="text", text=json.dumps({
                "결과": "매도 주문 완료",
                "종목코드": arguments["ticker"],
                "수량": arguments["qty"],
                "가격": arguments.get("price", 0) or "시장가",
                "응답": result.get("msg1", ""),
            }, ensure_ascii=False, indent=2))]

        else:
            return [TextContent(type="text", text=f"알 수 없는 도구: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"오류: {e}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
