"""
測試腳本：驗證 session detail API 改進

測試 API 是否正確返回：
1. 交易記錄列表 (trades)
2. 統計資料 (stats)
3. 工具調用列表 (tools_called)
"""

import asyncio
import httpx
import json


API_BASE_URL = "http://localhost:8000/api"


async def test_session_detail_api():
    """測試 session detail API"""
    print("=" * 60)
    print("測試 Session Detail API 改進")
    print("=" * 60)

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
        agent_id = agent["agent_id"]
        agent_name = agent["name"]
        print(f"✅ 使用 Agent: {agent_name} ({agent_id})")

        # 2. 獲取執行歷史
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

        # 顯示歷史記錄摘要
        for i, session in enumerate(history, 1):
            print(f"\n  記錄 {i}:")
            print(f"    Session ID: {session['id']}")
            print(f"    模式: {session['mode']}")
            print(f"    狀態: {session['status']}")
            print(f"    執行時間: {session.get('execution_time_ms', 'N/A')} ms")
            print(f"    交易數量: {session.get('trade_count', 0)}")
            print(f"    成交數量: {session.get('filled_count', 0)}")
            print(f"    總金額: ${session.get('total_notional', 0):,.2f}")

        # 3. 獲取第一個 session 的詳細資訊
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

        # 檢查統計資料
        stats = detail.get("stats", {})
        print("\n📈 統計資料:")
        print(f"  總交易數: {stats.get('total_trades', 0)}")
        print(f"  成交數: {stats.get('filled', 0)}")
        print(f"  總金額: ${stats.get('notional', 0):,.2f}")

        # 檢查交易記錄
        trades = detail.get("trades", [])
        print(f"\n💰 交易記錄 ({len(trades)} 筆):")
        if trades:
            for i, trade in enumerate(trades[:5], 1):  # 只顯示前 5 筆
                print(f"\n  交易 {i}:")
                print(f"    股票: {trade['ticker']} ({trade.get('company_name', 'N/A')})")
                print(f"    動作: {trade['action']}")
                print(f"    數量: {trade['quantity']}")
                print(f"    價格: ${trade['price']:.2f}")
                print(f"    金額: ${trade['total_amount']:.2f}")
                print(f"    狀態: {trade['status']}")
                if trade.get("decision_reason"):
                    print(f"    原因: {trade['decision_reason'][:100]}...")
            if len(trades) > 5:
                print(f"\n  ... 還有 {len(trades) - 5} 筆交易")
        else:
            print("  ⚠️ 沒有交易記錄")

        # 檢查工具調用
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

        # 檢查輸出
        final_output = detail.get("final_output")
        print("\n📝 執行輸出:")
        if final_output:
            print(f"  輸出類型: {type(final_output).__name__}")
            if isinstance(final_output, dict):
                print(f"  輸出鍵: {list(final_output.keys())}")
            elif isinstance(final_output, str):
                print(f"  輸出長度: {len(final_output)} 字元")
                print(f"  輸出預覽: {final_output[:200]}...")
        else:
            print("  ⚠️ 沒有輸出內容")

        # 檢查錯誤訊息
        error_message = detail.get("error_message")
        if error_message:
            print("\n❌ 錯誤訊息:")
            print(f"  {error_message}")

        print("\n" + "=" * 60)
        print("測試完成！")
        print("=" * 60)


async def main():
    """主函數"""
    try:
        await test_session_detail_api()
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP 錯誤: {e.response.status_code}")
        print(f"回應內容: {e.response.text}")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
