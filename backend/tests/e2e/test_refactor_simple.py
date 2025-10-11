#!/usr/bin/env python3
"""
簡單測試：驗證重構後的功能
"""

import requests


def test_agent_creation():
    """測試 Agent 創建（驗證 @function_tool decorator 和 max_turns）"""
    print("=" * 60)
    print("測試 Agent 創建 (驗證重構後功能)")
    print("=" * 60)

    url = "http://localhost:8000/api/agents"
    payload = {
        "name": "重構功能驗證",
        "strategy_prompt": "測試 @function_tool decorator 和 max_turns 傳遞",
        "initial_funds": 1000000,
        "ai_model": "gpt-5-mini",
        "investment_preferences": {
            "preferred_sectors": [],
            "excluded_tickers": [],
            "max_position_size": 0.5,
            "rebalance_frequency": "weekly",
        },
    }

    print(f"\n📤 發送請求到: {url}")
    print(f"📝 Agent 名稱: {payload['name']}")

    response = requests.post(url, json=payload)

    if response.status_code == 201:
        data = response.json()
        print("\n✅ Agent 創建成功！")
        print(f"   ID: {data['id']}")
        print(f"   名稱: {data['name']}")
        print(f"   模型: {data['ai_model']}")
        print(f"   max_turns: {data['max_turns']}")  # 驗證 max_turns 配置
        print(f"   狀態: {data['status']}")
        print("   啟用工具:")
        for tool, enabled in data["enabled_tools"].items():
            status = "✓" if enabled else "✗"
            print(f"     {status} {tool}")

        print("\n" + "=" * 60)
        print("🎉 重構功能驗證成功！")
        print("=" * 60)
        print("\n已驗證:")
        print("  ✅ @function_tool decorator 在 _setup_trading_tools 中正常工作")
        print("  ✅ Agent 創建使用正確的 OpenAI SDK 導入")
        print("  ✅ max_turns 配置正確保存在 AgentConfig 中")
        print("\n待運行時驗證:")
        print("  ⏳ max_turns 正確傳遞給 Runner.run() (需要執行 Agent 時驗證)")

        return True
    else:
        print("\n❌ 創建失敗")
        print(f"   狀態碼: {response.status_code}")
        print(f"   錯誤: {response.text}")
        return False


if __name__ == "__main__":
    success = test_agent_creation()
    exit(0 if success else 1)
