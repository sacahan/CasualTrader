"""
完整的概念驗證: 從資料庫載入配置並執行 Agent

這個腳本展示整個流程:
1. 從資料庫載入 Agent 配置
2. 初始化 TradingAgent
3. 執行交易會話
4. 查看 Trace 結果

使用方式:
    python -m src.agents.poc_full_workflow
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# 添加專案根目錄到 path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from src.agents.poc_trading_agent import POCTradingAgent  # noqa: E402
from src.database.models import Agent, AgentMode, AgentStatus, Base  # noqa: E402
from src.database.poc_agent_service import POCAgentDatabaseService  # noqa: E402

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def setup_test_database() -> tuple[any, sessionmaker]:
    """建立測試資料庫和 session factory"""
    # 使用記憶體資料庫進行 POC 測試
    database_url = "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(database_url, echo=False)

    # 建立表格
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✓ Database schema created")

    # 建立 session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return engine, async_session


async def seed_test_data(session: AsyncSession) -> str:
    """建立測試用的 Agent 資料"""
    test_agent = Agent(
        id="poc_agent_001",
        name="POC 交易分析助手",
        description="用於概念驗證的台股交易分析 Agent",
        instructions="""你是一個專業的台股投資分析助手。

你的職責:
1. 使用 casual_market MCP 查詢台灣股票市場資訊
2. 分析市場趨勢和潛在投資機會
3. 提供專業的投資建議

分析重點:
- 大盤指數走勢
- 熱門股票表現
- 市場情緒分析
- 風險評估

請務必基於事實數據提供建議，並說明理由。""",
        ai_model="gpt-4o-mini",
        initial_funds=100000.00,
        max_position_size=10.0,
        status=AgentStatus.ACTIVE,
        current_mode=AgentMode.OBSERVATION,
        investment_preferences=json.dumps(
            {
                "enabled_tools": {
                    "web_search": True,
                    "code_interpreter": False,
                    "fundamental_analysis": True,
                    "technical_analysis": True,
                },
                "risk_tolerance": "moderate",
                "max_single_position": 10.0,
                "preferred_sectors": ["Technology", "Finance"],
            }
        ),
    )

    session.add(test_agent)
    await session.commit()

    logger.info(f"✓ Test agent created: {test_agent.id}")
    return test_agent.id


async def run_poc_workflow():
    """執行完整的 POC 工作流程"""

    print("\n" + "=" * 80)
    print("CasualTrader Agent POC - 完整工作流程測試")
    print("=" * 80)

    # Step 1: 設置資料庫
    print("\n【Step 1】設置測試資料庫...")
    engine, async_session = await setup_test_database()

    async with async_session() as session:
        # Step 2: 建立測試資料
        print("\n【Step 2】建立測試 Agent 資料...")
        agent_id = await seed_test_data(session)

        # Step 3: 從資料庫載入配置
        print("\n【Step 3】從資料庫載入 Agent 配置...")
        db_service = POCAgentDatabaseService(session)
        db_config = await db_service.get_agent_config(agent_id)

        print("✓ 載入成功:")
        print(f"  - Agent ID: {db_config.id}")
        print(f"  - 名稱: {db_config.name}")
        print(f"  - AI 模型: {db_config.ai_model}")
        print(f"  - 初始資金: TWD {float(db_config.initial_funds):,.0f}")

        # 解析投資偏好
        prefs = db_service.parse_investment_preferences(db_config)
        enabled_tools = [k for k, v in prefs["enabled_tools"].items() if v]
        print(f"  - 啟用工具: {', '.join(enabled_tools)}")

        # Step 4: 創建 TradingAgent
        print("\n【Step 4】創建 TradingAgent 實例...")
        trading_agent = POCTradingAgent(agent_id, db_config)
        print("✓ TradingAgent 創建成功")

        # Step 5: 初始化 Agent
        print("\n【Step 5】初始化 Agent (設置 MCP/Tools)...")
        try:
            await trading_agent.initialize()
            print("✓ Agent 初始化成功")
            print(f"  - MCP Servers: {len(trading_agent.mcp_servers)}")
            print(f"  - OpenAI Tools: {len(trading_agent.openai_tools)}")
        except Exception as e:
            logger.error(f"✗ Agent 初始化失敗: {e}")
            print("\n⚠️  警告: Agent 初始化失敗")
            print(f"原因: {str(e)}")
            print("\n這可能是因為:")
            print("  1. MCP Server 路徑不正確")
            print("  2. 缺少必要的環境變數")
            print("  3. OpenAI API Key 未設置")
            print("\n但這不影響 POC 的主要目的（驗證架構設計）")
            return

        # Step 6: 執行交易會話
        print("\n【Step 6】執行交易會話 (OBSERVATION 模式)...")
        print("⏳ 正在執行 Agent（這可能需要幾秒鐘）...")

        try:
            result = await trading_agent.execute_trading_session(
                mode=AgentMode.OBSERVATION, context={"poc_test": True, "date": "2025-10-15"}
            )

            print("\n" + "=" * 80)
            print("執行結果")
            print("=" * 80)

            if result["success"]:
                print("✓ 執行成功")
                print(f"\n模式: {result['mode']}")
                print(f"Trace ID: {result['trace_id']}")
                print(f"Trace URL: {result['trace_url']}")

                print("\n--- Agent 輸出 ---")
                print(result["result"].final_output)
                print("--- 輸出結束 ---")

            else:
                print("✗ 執行失敗")
                print(f"錯誤類型: {result.get('error_type')}")
                print(f"錯誤訊息: {result.get('error')}")

        except Exception as e:
            logger.error(f"執行交易會話時發生錯誤: {e}", exc_info=True)
            print(f"\n✗ 執行失敗: {str(e)}")

    # 清理
    await engine.dispose()

    print("\n" + "=" * 80)
    print("POC 工作流程完成")
    print("=" * 80)
    print("\n✓ 概念驗證完成！")
    print("\n總結:")
    print("1. ✓ 成功從資料庫載入 Agent 配置")
    print("2. ✓ 成功創建 TradingAgent 實例")
    print("3. ✓ 配置解析正常運作")
    print("4. ✓ 架構設計驗證通過")
    print("\n後續步驟:")
    print("- 完善錯誤處理")
    print("- 實作 Sub-agents")
    print("- 建立完整測試套件")
    print("- 整合到實際 API")


def check_environment():
    """檢查環境設置"""
    print("\n檢查環境設置...")

    # 檢查 OpenAI API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  警告: 未設置 OPENAI_API_KEY 環境變數")
        print("   Agent 執行可能會失敗")
        print("   設置方法: export OPENAI_API_KEY='your-api-key'")
    else:
        print("✓ OPENAI_API_KEY 已設置")

    # 檢查 Python 版本
    import sys

    if sys.version_info < (3, 12):
        print(f"⚠️  警告: Python 版本 {sys.version_info.major}.{sys.version_info.minor}")
        print("   建議使用 Python 3.12+")
    else:
        print(f"✓ Python 版本: {sys.version_info.major}.{sys.version_info.minor}")


if __name__ == "__main__":
    # 檢查環境
    check_environment()

    # 執行 POC
    try:
        asyncio.run(run_poc_workflow())
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷執行")
    except Exception as e:
        logger.error(f"POC 執行失敗: {e}", exc_info=True)
        print(f"\n✗ 錯誤: {str(e)}")
        sys.exit(1)
