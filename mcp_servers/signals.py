"""신호 분석 MCP 서버 — 골든크로스 / DART 지분공시.

Claude 안에서 자연어로 호출 가능:
  > "삼성전자 골든크로스 신호 어때?"
  > "오늘 대량보유 공시 나온 종목 좀 보여줘"

내부적으로 scripts/ 의 함수를 재사용해서 알고리즘 코드는 그대로 학습/수정 가능.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from scripts.golden_cross import detect_cross
from scripts.dart_shareholding import fetch_recent, load_dart_key


app = Server("signals")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="golden_cross_signal",
            description=(
                "종목의 5일/20일 이동평균 골든크로스 신호를 계산합니다. "
                "GOLDEN_CROSS_BUY(상향 돌파, 매수), DEAD_CROSS_SELL(하향, 매도), HOLD(교차 없음) 중 하나 반환."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "6자리 종목코드 (예: 005930 삼성전자)"},
                },
                "required": ["ticker"],
            },
        ),
        Tool(
            name="dart_recent_disclosures",
            description=(
                "최근 N일 DART 지분공시 목록을 가져옵니다. "
                "대량보유(5% 룰) 및 임원·주요주주 보고 — 매매 후보 발굴용."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "days_back": {"type": "integer", "description": "조회 일수 (기본 3)", "default": 3},
                    "limit": {"type": "integer", "description": "결과 최대 건수 (기본 25)", "default": 25},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "golden_cross_signal":
            result = detect_cross(arguments["ticker"])
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "dart_recent_disclosures":
            api_key = load_dart_key()
            days = arguments.get("days_back", 3)
            limit = arguments.get("limit", 25)
            items = fetch_recent(api_key, days_back=days)
            output = [
                {
                    "date": it["rcept_dt"],
                    "corp_name": it.get("corp_name"),
                    "stock_code": it.get("stock_code"),
                    "report": it["report_nm"],
                    "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={it.get('rcept_no')}",
                }
                for it in items[:limit]
            ]
            return [TextContent(type="text", text=json.dumps(
                {"count": len(output), "disclosures": output},
                ensure_ascii=False, indent=2,
            ))]

        else:
            return [TextContent(type="text", text=f"알 수 없는 도구: {name}")]

    except SystemExit:
        return [TextContent(
            type="text",
            text="config.yaml 또는 DART API 키가 누락됐습니다. setup.sh 다시 실행하거나 config.yaml 의 dart.api_key 를 채워주세요.",
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"오류: {e}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
