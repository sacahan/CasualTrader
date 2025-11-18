"""
Manual verification script for execution history API.

Moved from backend root so manual checks live under tests/manual.
"""

import asyncio
import json

import httpx

API_BASE_URL = "http://localhost:8000/api"


async def test_execution_history_with_trades() -> None:
    """Run the execution history API check and print diagnostic output."""
    print("=" * 80)
    print("測試執行歷史 API - 驗證 trades 陣列返回")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 獲取 agents 列表
        print("\n1️⃣ 獲取 Agents 列表...")
        response = await client.get(f"{API_BASE_URL}/agents")
        response.raise_for_status()
        agents = response.json()

        if not agents:
            print("❌ 沒有找到任何 Agent")
            return

        agent = agents[0]
        agent_id = agent["id"]
        print(f"✅ 使用 Agent: {agent['name']} ({agent_id})")

        # 2. 獲取執行歷史
        print("\n2️⃣ 獲取執行歷史...")
        response = await client.get(
            f"{API_BASE_URL}/agent-execution/{agent_id}/history",
            params={"limit": 5},
        )
        response.raise_for_status()
        history = response.json()

        if not history:
            print("⚠️ 沒有執行歷史記錄")
            return

        print(f"✅ 找到 {len(history)} 筆執行記錄")

        # 3. 驗證歷史記錄結構
        print("\n3️⃣ 驗證歷史記錄結構...")
        first_session = history[0]

        required_fields = [
            "id",
            "agent_id",
            "mode",
            "status",
            "start_time",
            "end_time",
            "execution_time_ms",
            "trade_count",
            "filled_count",
            "total_notional",
        ]

        missing_fields = [f for f in required_fields if f not in first_session]
        if missing_fields:
            print(f"❌ 缺少欄位: {missing_fields}")
            return

        print("✅ 所有必填欄位都存在")

        if "trades" not in first_session:
            print("❌ 缺少 'trades' 陣列（新增欄位）")
            print(f"   當前欄位: {list(first_session.keys())}")
            return

        print("✅ 'trades' 陣列存在")

        trades = first_session["trades"]
        print(f"\n4️⃣ 驗證 trades 陣列 ({len(trades)} 筆交易)...")

        if not trades:
            print("⚠️ trades 陣列為空")
        else:
            trade = trades[0]
            trade_required_fields = [
                "id",
                "ticker",
                "company_name",
                "action",
                "quantity",
                "price",
                "total_amount",
                "commission",
                "status",
            ]

            missing_trade_fields = [f for f in trade_required_fields if f not in trade]
            if missing_trade_fields:
                print(f"❌ 交易記錄缺少欄位: {missing_trade_fields}")
                return

            print("✅ 第一筆交易記錄完整:")
            print(f"   股票: {trade['ticker']} ({trade['company_name']})")
            print(f"   動作: {trade['action']}")
            print(f"   數量: {trade['quantity']}")
            print(f"   價格: ${trade['price']:.2f}")
            print(f"   總額: ${trade['total_amount']:,.2f}")

        print("\n5️⃣ 驗證統計資料...")
        print(f"   交易總數: {first_session['trade_count']}")
        print(f"   成交數: {first_session['filled_count']}")
        print(f"   總金額: ${first_session['total_notional']:,.2f}")

        if first_session["trade_count"] != len(trades):
            print(
                f"⚠️ 警告：trade_count ({first_session['trade_count']}) "
                f"與 trades 長度 ({len(trades)}) 不一致"
            )
        else:
            print("✅ trade_count 與 trades 長度一致")

        print("\n6️⃣ 完整回應預覽（第一筆記錄）:")
        print(json.dumps(first_session, indent=2, ensure_ascii=False)[:1000] + "...")

        print("\n" + "=" * 80)
        print("✅ 所有驗證通過！執行歷史 API 已正確返回 trades 陣列")
        print("=" * 80)


def main() -> None:
    """Entry point for manual execution."""
    try:
        asyncio.run(test_execution_history_with_trades())
    except httpx.HTTPStatusError as exc:
        print(f"\n❌ HTTP 錯誤: {exc.response.status_code}")
        print(f"回應內容: {exc.response.text}")
    except Exception as exc:  # noqa: BLE001 - manual diagnostic script
        print(f"\n❌ 錯誤: {exc}")


if __name__ == "__main__":
    main()
