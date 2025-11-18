"""
Manual verification script for session detail API responses.

Relocated under tests/manual for consistency with other diagnostics.
"""

import asyncio
import json

import httpx

API_BASE_URL = "http://localhost:8000/api"


async def test_session_detail_api() -> None:
    """Run the session detail API diagnostic flow."""
    print("=" * 60)
    print("測試 Session Detail API 改進")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n1️⃣ 獲取 Agents 列表...")
        response = await client.get(f"{API_BASE_URL}/agents")
        response.raise_for_status()
        agents = response.json()

        if not agents:
            print("❌ 沒有找到任何 Agent")
            return

        agent = agents[0]
        agent_id = agent.get("agent_id") or agent.get("id")
        agent_name = agent.get("name", "未知 Agent")
        print(f"✅ 使用 Agent: {agent_name} ({agent_id})")

        print(f"\n2️⃣ 獲取 Agent {agent_name} 的執行歷史...")
        response = await client.get(
            f"{API_BASE_URL}/agent-execution/{agent_id}/history",
            params={"limit": 5},
        )
        response.raise_for_status()
        history = response.json()

        if not history:
            print("❌ 沒有執行歷史記錄")
            return

        print(f"✅ 找到 {len(history)} 筆執行記錄")

        for index, session in enumerate(history, 1):
            print(f"\n  記錄 {index}:")
            print(f"    Session ID: {session['id']}")
            print(f"    模式: {session['mode']}")
            print(f"    狀態: {session['status']}")
            print(f"    執行時間: {session.get('execution_time_ms', 'N/A')} ms")
            print(f"    交易數量: {session.get('trade_count', 0)}")
            print(f"    成交數量: {session.get('filled_count', 0)}")
            print(f"    總金額: ${session.get('total_notional', 0):,.2f}")

        session_id = history[0]["id"]
        print(f"\n3️⃣ 獲取 Session {session_id} 的詳細資訊...")
        response = await client.get(
            f"{API_BASE_URL}/agent-execution/{agent_id}/sessions/{session_id}"
        )
        response.raise_for_status()
        detail = response.json()

        print("\n📊 Session 詳細資訊:")
        print(f"  Session ID: {detail['id']}")
        print(f"  模式: {detail['mode']}")
        print(f"  狀態: {detail['status']}")
        print(f"  開始時間: {detail['start_time']}")
        print(f"  結束時間: {detail['end_time']}")
        print(f"  執行時間: {detail['execution_time_ms']} ms")

        stats = detail.get("stats", {})
        print("\n📈 統計資料:")
        print(f"  總交易數: {stats.get('total_trades', 0)}")
        print(f"  成交數: {stats.get('filled', 0)}")
        print(f"  總金額: ${stats.get('notional', 0):,.2f}")

        trades = detail.get("trades", [])
        print(f"\n💰 交易記錄 ({len(trades)} 筆):")
        if trades:
            for index, trade in enumerate(trades[:5], 1):
                print(f"\n  交易 {index}:")
                print(f"    股票: {trade['ticker']} ({trade.get('company_name', 'N/A')})")
                print(f"    動作: {trade['action']}")
                print(f"    數量: {trade['quantity']}")
                print(f"    價格: ${trade['price']:.2f}")
                print(f"    金額: ${trade['total_amount']:.2f}")
                print(f"    狀態: {trade['status']}")
                if trade.get("decision_reason"):
                    preview = trade["decision_reason"][:100]
                    print(f"    原因: {preview}...")
            if len(trades) > 5:
                print(f"\n  ... 還有 {len(trades) - 5} 筆交易")
        else:
            print("  ⚠️ 沒有交易記錄")

        tools_called = detail.get("tools_called")
        print("\n🔧 工具調用:")
        if tools_called:
            if isinstance(tools_called, str):
                try:
                    tools_list = json.loads(tools_called)
                    print(f"  調用了 {len(tools_list)} 個工具:")
                    for tool in tools_list:
                        print(f"    - {tool}")
                except json.JSONDecodeError:
                    print(f"  工具列表: {tools_called}")
            else:
                print(f"  工具列表: {tools_called}")
        else:
            print("  ⚠️ 沒有工具調用記錄")

        final_output = detail.get("final_output")
        print("\n📝 執行輸出:")
        if final_output:
            print(f"  輸出類型: {type(final_output).__name__}")
            if isinstance(final_output, dict):
                print(f"  輸出鍵: {list(final_output.keys())}")
            elif isinstance(final_output, str):
                preview = final_output[:200]
                print(f"  輸出長度: {len(final_output)} 字元")
                print(f"  輸出預覽: {preview}...")
        else:
            print("  ⚠️ 沒有輸出內容")

        error_message = detail.get("error_message")
        if error_message:
            print("\n❌ 錯誤訊息:")
            print(f"  {error_message}")

        print("\n" + "=" * 60)
        print("測試完成！")
        print("=" * 60)


def main() -> None:
    """Entry point for manual execution."""
    try:
        asyncio.run(test_session_detail_api())
    except httpx.HTTPStatusError as exc:
        print(f"\n❌ HTTP 錯誤: {exc.response.status_code}")
        print(f"回應內容: {exc.response.text}")
    except Exception as exc:  # noqa: BLE001 - manual diagnostic script
        print(f"\n❌ 錯誤: {exc}")


if __name__ == "__main__":
    main()
