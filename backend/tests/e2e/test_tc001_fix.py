"""
測試 TC-001 修復：驗證 Agent 創建後資料庫有記錄

這個腳本測試以下修復：
1. AgentManager 注入 AgentDatabaseService
2. create_agent() 方法呼叫 save_agent_state()
3. Agent 資料正確寫入資料庫
"""

import asyncio
import sys
from pathlib import Path

# 加入 src 到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 直接導入需要的模組，避免導入 TradingAgent
from src.agents.core.models import AgentConfig
from src.database.agent_database_service import AgentDatabaseService, DatabaseConfig

# 使用測試資料庫
TEST_DB_URL = "sqlite+aiosqlite:///./test_tc001.db"


async def test_agent_creation_with_database():
    """測試 Agent 創建並驗證資料庫記錄"""

    print("=" * 80)
    print("🧪 TC-001 修復驗證測試")
    print("=" * 80)

    # 1. 初始化資料庫服務
    print("\n📦 Step 1: 初始化資料庫服務...")
    db_config = DatabaseConfig(database_url=TEST_DB_URL)
    db_service = AgentDatabaseService(db_config)
    await db_service.initialize()
    print("✅ 資料庫服務初始化成功")

    # 2. 創建 Agent Manager（注入資料庫服務）
    print("\n📦 Step 2: 創建 Agent Manager（注入資料庫服務）...")
    from src.agents.core.agent_manager import AgentManager

    agent_manager = AgentManager(database_service=db_service)
    await agent_manager.start()
    print("✅ Agent Manager 啟動成功")

    # 3. 創建 Agent 配置
    print("\n📦 Step 3: 準備 Agent 配置...")
    config = AgentConfig(
        name="TC-001 測試 Agent",
        description="測試 Agent 創建後資料庫持久化",
        model="gpt-4o-mini",
        instructions="你是一位測試用的交易 Agent",
        initial_funds=1000000.0,
        investment_preferences=["長期投資", "科技股偏好", "穩健成長"],
    )
    print(f"✅ Agent 配置準備完成：{config.name}")

    # 4. 創建 Agent（應該自動寫入資料庫）
    print("\n📦 Step 4: 創建 Agent...")
    try:
        agent_id = await agent_manager.create_agent(config=config, auto_start=False)
        print(f"✅ Agent 創建成功：{agent_id}")
    except Exception as e:
        print(f"❌ Agent 創建失敗：{e}")
        await agent_manager.shutdown()
        await db_service.close()
        return False

    # 5. 驗證資料庫中是否有記錄
    print("\n📦 Step 5: 驗證資料庫記錄...")
    try:
        # 從資料庫載入 Agent
        agent_state = await db_service.load_agent_state(agent_id)

        if agent_state:
            print("✅ 資料庫中找到 Agent 記錄：")
            print(f"   - ID: {agent_state.id}")
            print(f"   - Name: {agent_state.name}")
            print(f"   - Status: {agent_state.status}")
            print(f"   - AI Model: {agent_state.config.ai_model}")
            print(f"   - Initial Funds: {agent_state.config.initial_funds:,.2f}")
            print(f"   - Created At: {agent_state.created_at}")

            # 驗證資料正確性
            assert agent_state.name == config.name, "名稱不一致"
            assert agent_state.config.ai_model == config.ai_model, "AI 模型不一致"
            assert agent_state.config.initial_funds == config.initial_funds, "初始資金不一致"

            print("\n✅ 所有驗證通過！")
            result = True
        else:
            print(f"❌ 資料庫中未找到 Agent 記錄：{agent_id}")
            result = False

    except Exception as e:
        print(f"❌ 驗證失敗：{e}")
        import traceback

        traceback.print_exc()
        result = False

    # 6. 清理
    print("\n📦 Step 6: 清理測試資料...")
    try:
        await agent_manager.remove_agent(agent_id)
        print("✅ Agent 已從內存和資料庫中移除")
    except Exception as e:
        print(f"⚠️ 清理警告：{e}")

    await agent_manager.shutdown()
    await db_service.close()

    print("\n" + "=" * 80)
    if result:
        print("🎉 TC-001 修復驗證測試通過！")
        print("   Agent 創建後成功寫入資料庫")
    else:
        print("❌ TC-001 修復驗證測試失敗！")
        print("   Agent 創建後未寫入資料庫")
    print("=" * 80)

    return result


async def main():
    """主函數"""
    try:
        success = await test_agent_creation_with_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 測試執行錯誤：{e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
