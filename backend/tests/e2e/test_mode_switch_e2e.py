#!/usr/bin/env python
"""
測試從 OBSERVATION 模式切換到 TRADING 模式的場景

這個端到端測試驗證 AsyncExitStack 和 MCP servers cancel scope 問題是否已解決。
"""

import asyncio
import httpx
from loguru import logger

# 配置日誌
logger.remove()
logger.add(lambda msg: print(msg, end=""), colorize=True)

API_BASE_URL = "http://localhost:8000"
AGENT_ID = "test-agent-mode-switch"


async def test_mode_switch():
    """測試模式切換"""
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            print("\n" + "=" * 80)
            print("測試：OBSERVATION → TRADING 模式切換")
            print("=" * 80)

            # 1. 建立 Agent
            print("\n[1] 建立測試 Agent...")
            agent_data = {
                "name": "Test Agent Mode Switch",
                "description": "Test switching between OBSERVATION and TRADING modes",
                "initial_funds": 1000000,
                "investment_preferences": ["2330", "2454"],
            }

            response = await client.post(
                f"{API_BASE_URL}/api/agents",
                json=agent_data,
            )
            print(f"    回應狀態: {response.status_code}")

            if response.status_code not in [200, 201]:
                print(f"    錯誤: {response.text}")
                return False

            result = response.json()
            agent_id = result.get("agent_id", AGENT_ID)
            print(f"    ✓ Agent 已建立: {agent_id}")

            # 2. 執行 OBSERVATION 模式
            print("\n[2] 執行 OBSERVATION 模式...")
            observation_data = {
                "mode": "OBSERVATION",
                "context": {"max_turns": 5},
            }

            response = await client.post(
                f"{API_BASE_URL}/api/agent-execution/{agent_id}/start",
                json=observation_data,
            )
            print(f"    回應狀態: {response.status_code}")

            if response.status_code != 200:
                print(f"    錯誤: {response.text}")
                return False

            result = response.json()
            observation_session = result.get("session_id")
            print(f"    ✓ OBSERVATION 模式執行完成: {observation_session}")

            # 等待一下，讓清理完成
            await asyncio.sleep(2)

            # 3. 執行 TRADING 模式
            print("\n[3] 執行 TRADING 模式...")
            trading_data = {
                "mode": "TRADING",
                "context": {"max_turns": 5},
            }

            response = await client.post(
                f"{API_BASE_URL}/api/agent-execution/{agent_id}/start",
                json=trading_data,
            )
            print(f"    回應狀態: {response.status_code}")

            if response.status_code != 200:
                print(f"    錯誤: {response.text}")
                print("\n    ❌ 模式切換失敗！這可能表示 cancel scope 問題仍未解決")
                return False

            result = response.json()
            trading_session = result.get("session_id")
            print(f"    ✓ TRADING 模式執行完成: {trading_session}")

            print("\n" + "=" * 80)
            print("✓ 測試成功！模式切換工作正常")
            print("=" * 80)
            return True

        except Exception as e:
            logger.error(f"測試失敗: {e}", exc_info=True)
            return False


async def main():
    """主函數"""
    print("等待伺服器啟動...")
    await asyncio.sleep(3)

    success = await test_mode_switch()
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
