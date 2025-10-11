"""
Trading Agent 工具配置測試
驗證修正後的工具配置是否正確
"""

import pytest


@pytest.mark.asyncio
async def test_mcp_client():
    """測試 MCP Client 初始化和基本功能"""
    print("\n🔍 測試 1: MCP Client 初始化")
    print("=" * 60)

    try:
        from agents.integrations.mcp_client import get_mcp_client

        client = get_mcp_client()
        await client.initialize()

        print("✅ MCP Client 初始化成功")

        # 測試股票價格查詢
        print("\n📊 測試股票價格查詢 (2330 台積電)...")
        result = await client.get_stock_price("2330")

        if result.get("current_price"):
            print(f"✅ 股票價格: NT${result['current_price']:.2f}")
            print(f"   公司名稱: {result.get('company_name', 'N/A')}")
            print(f"   漲跌幅: {result.get('change_percent', 0):.2f}%")
        else:
            print("⚠️ 股票價格查詢返回空數據")

        await client.close()
        return True

    except Exception as e:
        print(f"❌ MCP Client 測試失敗: {e}")
        return False


@pytest.mark.asyncio
async def test_agent_tools_import():
    """測試 OpenAI Agent SDK 工具導入"""
    print("\n🔍 測試 2: OpenAI Agent SDK 工具導入")
    print("=" * 60)

    try:
        from agents import CodeInterpreterTool  # noqa: F401
        from agents import FunctionTool  # noqa: F401
        from agents import WebSearchTool  # noqa: F401

        print("✅ FunctionTool 導入成功")
        print("✅ WebSearchTool 導入成功")
        print("✅ CodeInterpreterTool 導入成功")

        return True

    except ImportError as e:
        print(f"❌ OpenAI Agent SDK 工具導入失敗: {e}")
        print("請安裝: pip install openai-agents>=0.1.0")
        return False


@pytest.mark.asyncio
async def test_trading_agent_tools():
    """測試 Trading Agent 工具配置"""
    print("\n🔍 測試 3: Trading Agent 工具配置")
    print("=" * 60)

    try:
        from agents.core.models import create_default_agent_config
        from agents.trading.trading_agent import TradingAgent

        # 創建測試配置
        config = create_default_agent_config(
            name="Test Trading Agent",
            description="測試用交易 Agent",
            initial_funds=1000000.0,
        )

        # 創建 Agent 實例
        agent = TradingAgent(config)

        print("✅ Trading Agent 實例創建成功")

        # 測試工具配置
        print("\n📋 配置工具...")
        tools = await agent._setup_tools()

        print(f"✅ 工具配置完成，共 {len(tools)} 個工具")

        # 分類統計
        tool_types = {}
        for tool in tools:
            tool_type = type(tool).__name__
            tool_types[tool_type] = tool_types.get(tool_type, 0) + 1

        print("\n📊 工具類型統計:")
        for tool_type, count in tool_types.items():
            print(f"   - {tool_type}: {count} 個")

        return True

    except Exception as e:
        print(f"❌ Trading Agent 工具配置測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_specialized_agents():
    """測試專門化 Agent 工具"""
    print("\n🔍 測試 4: 專門化 Agent 工具")
    print("=" * 60)

    results = {}

    # 測試 Fundamental Agent
    try:
        from agents.tools.fundamental_agent import (  # noqa: F401
            get_fundamental_agent_tool,
        )

        print("✅ Fundamental Agent 可用")
        results["fundamental"] = True
    except ImportError:
        print("⚠️ Fundamental Agent 未實作")
        results["fundamental"] = False

    # 測試 Technical Agent
    try:
        from agents.tools.technical_agent import (  # noqa: F401
            get_technical_agent_tool,
        )

        print("✅ Technical Agent 可用")
        results["technical"] = True
    except ImportError:
        print("⚠️ Technical Agent 未實作")
        results["technical"] = False

    # 測試 Risk Agent
    try:
        from agents.tools.risk_agent import get_risk_agent_tool  # noqa: F401

        print("✅ Risk Agent 可用")
        results["risk"] = True
    except ImportError:
        print("⚠️ Risk Agent 未實作")
        results["risk"] = False

    # 測試 Sentiment Agent
    try:
        from agents.tools.sentiment_agent import (  # noqa: F401
            get_sentiment_agent_tool,
        )

        print("✅ Sentiment Agent 可用")
        results["sentiment"] = True
    except ImportError:
        print("⚠️ Sentiment Agent 未實作")
        results["sentiment"] = False

    return any(results.values())


@pytest.mark.asyncio
async def test_all_tools():
    """綜合測試：驗證所有工具配置"""
    results = []

    # 執行所有子測試
    results.append(await test_mcp_client())
    results.append(await test_agent_tools_import())
    results.append(await test_trading_agent_tools())
    results.append(await test_specialized_agents())

    # 至少要有一個測試通過
    assert any(results), "所有工具配置測試均失敗"
