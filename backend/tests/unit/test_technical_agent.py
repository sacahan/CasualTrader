"""
技術分析 Agent 的測試

這個模組測試：
1. 輔助函數 (parse_tool_params 等)
2. Agent 初始化和工具加載

注意: @function_tool 裝飾的函數無法直接調用（被轉換為 FunctionTool 對象）。
這些函數應該通過完整的 Agent 框架進行測試。
"""

import sys
from pathlib import Path

import pytest

# 添加 src 目錄到 Python 路徑
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from trading.tools.technical_agent import (  # noqa: E402
    parse_tool_params,
    technical_agent_instructions,
    get_technical_agent,
)


# ============================================================================
# 輔助函數測試
# ============================================================================


class TestTechnicalAgentParseToolParams:
    """測試技術分析 Agent 的參數解析函數"""

    def test_parse_direct_parameters(self):
        """測試直接參數解析"""
        result = parse_tool_params(ticker="2330", period=20)
        assert result["ticker"] == "2330"
        assert result["period"] == 20

    def test_parse_json_string_in_args(self):
        """測試 JSON 字符串參數解析"""
        import json

        data = {"ticker": "2330", "timeframe": "daily"}
        result = parse_tool_params(args=json.dumps(data))
        assert result["ticker"] == "2330"
        assert result["timeframe"] == "daily"

    def test_parse_removes_invalid_keys(self):
        """測試移除無效鍵"""
        result = parse_tool_params(ticker="2330", input_image="invalid", indicator="RSI")
        assert "ticker" in result
        assert "indicator" in result
        assert "input_image" not in result

    def test_parse_empty_parameters(self):
        """測試空參數"""
        result = parse_tool_params()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parse_technical_indicators(self):
        """測試技術指標數據解析"""
        indicator_data = {"rsi": 65, "macd": 0.05, "bb_position": 0.8}
        result = parse_tool_params(indicators=indicator_data)

        assert result is not None
        assert "indicators" in result


# ============================================================================
# Agent 初始化和工具加載測試
# ============================================================================


class TestTechnicalAgentInitialization:
    """測試 Technical Agent 初始化"""

    def test_agent_instructions_generated(self):
        """測試 Agent 指令生成"""
        instructions = technical_agent_instructions()

        assert instructions is not None
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        # 驗證關鍵內容存在
        assert "技術" in instructions or "technical" in instructions.lower()

    @pytest.mark.asyncio
    async def test_get_technical_agent_creation(self):
        """測試創建 Technical Agent"""
        agent = await get_technical_agent()

        assert agent is not None
        assert hasattr(agent, "name")
        assert agent.name == "technical_analyst"
        assert hasattr(agent, "instructions")

    @pytest.mark.asyncio
    async def test_get_technical_agent_with_empty_mcp(self):
        """測試帶空 MCP servers 列表創建 Agent"""
        agent = await get_technical_agent(mcp_servers=[])

        assert agent is not None
        assert hasattr(agent, "name")
        assert agent.name == "technical_analyst"

    @pytest.mark.asyncio
    async def test_technical_agent_has_tools(self):
        """測試 Agent 包含工具"""
        agent = await get_technical_agent()

        assert agent is not None
        # Agent 應該有 tools 屬性或方法
        has_tools = hasattr(agent, "tools") or hasattr(agent, "model_settings")
        assert has_tools is True

    @pytest.mark.asyncio
    async def test_technical_agent_model_settings(self):
        """測試 Agent 模型配置"""
        agent = await get_technical_agent()

        assert agent is not None
        # 驗證 Agent 有必要的配置屬性
        assert hasattr(agent, "instructions") or hasattr(agent, "tools")


# ============================================================================
# 工具定義驗證測試
# ============================================================================


class TestTechnicalAgentTools:
    """測試 Technical Agent 工具定義"""

    @pytest.mark.asyncio
    async def test_agent_has_required_tools(self):
        """測試 Agent 包含必要的工具"""
        agent = await get_technical_agent()

        assert agent is not None
        # Agent 應該包含技術分析相關的工具

        if hasattr(agent, "tools") and agent.tools:
            tool_count = len(agent.tools)
            # 應該至少有工具
            assert tool_count >= 3

    @pytest.mark.asyncio
    async def test_agent_tools_have_descriptions(self):
        """測試工具有描述信息"""
        agent = await get_technical_agent()

        assert agent is not None
        if hasattr(agent, "tools") and agent.tools:
            for tool in agent.tools:
                # 每個工具應該有描述
                assert hasattr(tool, "description") or hasattr(tool, "name")


# ============================================================================
# 邊界和錯誤情況測試
# ============================================================================


class TestTechnicalAgentEdgeCases:
    """測試邊界情況"""

    def test_parse_with_malformed_json(self):
        """測試解析格式錯誤的 JSON"""
        result = parse_tool_params(args='{"invalid": json}')
        # 應該返回字典
        assert isinstance(result, dict)

    def test_parse_with_nested_json(self):
        """測試嵌套 JSON 解析"""
        import json

        nested_data = {
            "ticker": "2330",
            "indicators": {
                "rsi": 65,
                "nested": {"key": "value"},
            },
        }
        result = parse_tool_params(args=json.dumps(nested_data))

        assert result["ticker"] == "2330"
        assert "indicators" in result

    @pytest.mark.asyncio
    async def test_multiple_agent_creations(self):
        """測試多次創建 Agent"""
        agent1 = await get_technical_agent()
        agent2 = await get_technical_agent()

        assert agent1 is not None
        assert agent2 is not None
        # 兩個代理應該都是有效的
        assert agent1.name == agent2.name

    def test_parse_with_special_characters(self):
        """測試特殊字符處理"""
        result = parse_tool_params(
            ticker="2330-TW",
            description="技術分析 (台積電)",
            special="™®©",
        )

        assert result is not None
        assert result["ticker"] == "2330-TW"

    def test_parse_price_levels(self):
        """測試價格水準解析"""
        result = parse_tool_params(
            support_level=500.0,
            resistance_level=550.0,
            current_price=520.0,
        )

        assert result is not None
        assert result["support_level"] == 500.0
        assert result["resistance_level"] == 550.0


# ============================================================================
# 技術分析特定場景測試
# ============================================================================


class TestTechnicalAgentScenarios:
    """測試技術分析場景"""

    @pytest.mark.asyncio
    async def test_agent_creation_with_custom_model(self):
        """測試使用自訂模型創建 Agent"""
        agent = await get_technical_agent(llm_model=None)

        assert agent is not None
        assert agent.name == "technical_analyst"

    def test_parse_ohlc_data(self):
        """測試 OHLC 數據解析"""
        ohlc_data = {
            "open": 520.0,
            "high": 525.0,
            "low": 515.0,
            "close": 522.0,
            "volume": 1_000_000,
        }

        result = parse_tool_params(price_action=ohlc_data)

        assert result is not None
        assert "price_action" in result

    def test_parse_multiple_timeframes(self):
        """測試多時間框架數據解析"""
        timeframes = {
            "1H": {"rsi": 65, "macd": 0.05},
            "4H": {"rsi": 55, "macd": -0.02},
            "1D": {"rsi": 50, "macd": 0.01},
        }

        result = parse_tool_params(analysis=timeframes)

        assert result is not None
        assert "analysis" in result

    def test_parse_signal_strength(self):
        """測試信號強度解析"""
        result = parse_tool_params(
            signal_strength=0.85,
            confidence=0.90,
            probability=0.75,
        )

        assert result is not None
        assert result["signal_strength"] == 0.85
        assert result["confidence"] == 0.90
        assert result["probability"] == 0.75

    def test_parse_with_extreme_values(self):
        """測試極端數值"""
        result = parse_tool_params(
            price_high=999999.99,
            price_low=0.01,
            volume=10_000_000_000,
        )

        assert result is not None
        assert result["price_high"] == 999999.99
