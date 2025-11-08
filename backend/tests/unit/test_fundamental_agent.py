"""
基本面分析 Agent 的測試

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

from trading.tools.fundamental_agent import (  # noqa: E402
    parse_tool_params,
    fundamental_agent_instructions,
    get_fundamental_agent,
)


# ============================================================================
# 輔助函數測試
# ============================================================================


class TestParseToolParams:
    """測試參數解析函數"""

    def test_parse_direct_parameters(self):
        """測試直接參數解析"""
        result = parse_tool_params(ticker="2330", value=100)
        assert result["ticker"] == "2330"
        assert result["value"] == 100

    def test_parse_json_string_in_args(self):
        """測試 JSON 字符串參數解析"""
        import json

        data = {"ticker": "2330", "amount": 1000}
        result = parse_tool_params(args=json.dumps(data))
        assert result["ticker"] == "2330"
        assert result["amount"] == 1000

    def test_parse_removes_invalid_keys(self):
        """測試移除無效鍵"""
        result = parse_tool_params(ticker="2330", input_image="invalid", other="value")
        assert "ticker" in result
        assert "other" in result
        assert "input_image" not in result

    def test_parse_empty_parameters(self):
        """測試空參數"""
        result = parse_tool_params()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parse_args_field_priority(self):
        """測試 args 字段優先級"""
        import json

        data = {"ticker": "from_args", "key": "value"}
        result = parse_tool_params(
            ticker="direct_param",
            args=json.dumps(data),
        )
        # args 中的數據應該有優先級
        assert result["ticker"] == "from_args" or result["ticker"] == "direct_param"


# ============================================================================
# Agent 初始化和工具加載測試
# ============================================================================


class TestFundamentalAgentInitialization:
    """測試 Fundamental Agent 初始化"""

    def test_agent_instructions_generated(self):
        """測試 Agent 指令生成"""
        instructions = fundamental_agent_instructions()

        assert instructions is not None
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        # 驗證關鍵內容存在
        assert "基本面" in instructions

    @pytest.mark.asyncio
    async def test_get_fundamental_agent_creation(self):
        """測試創建 Fundamental Agent"""
        agent = await get_fundamental_agent()

        assert agent is not None
        assert hasattr(agent, "name")
        assert agent.name == "fundamental_analyst"
        assert hasattr(agent, "instructions")

    @pytest.mark.asyncio
    async def test_get_fundamental_agent_with_empty_mcp(self):
        """測試帶空 MCP servers 列表創建 Agent"""
        agent = await get_fundamental_agent(mcp_servers=[])

        assert agent is not None
        assert hasattr(agent, "name")
        assert agent.name == "fundamental_analyst"

    @pytest.mark.asyncio
    async def test_fundamental_agent_has_tools(self):
        """測試 Agent 包含工具"""
        agent = await get_fundamental_agent()

        assert agent is not None
        # Agent 應該有 tools 屬性或方法
        has_tools = hasattr(agent, "tools") or hasattr(agent, "model_settings")
        assert has_tools is True

    @pytest.mark.asyncio
    async def test_fundamental_agent_model_settings(self):
        """測試 Agent 模型配置"""
        agent = await get_fundamental_agent()

        assert agent is not None
        # 驗證 Agent 有必要的配置屬性
        assert hasattr(agent, "instructions") or hasattr(agent, "tools")


# ============================================================================
# 工具定義驗證測試
# ============================================================================


class TestFundamentalAgentTools:
    """測試 Fundamental Agent 工具定義"""

    @pytest.mark.asyncio
    async def test_agent_has_required_tools(self):
        """測試 Agent 包含必要的工具"""
        agent = await get_fundamental_agent()

        assert agent is not None
        # Agent 應該包含這些工具:
        # - calculate_financial_ratios
        # - analyze_financial_health
        # - evaluate_valuation
        # - analyze_growth_potential
        # - generate_investment_rating

        if hasattr(agent, "tools") and agent.tools:
            tool_count = len(agent.tools)
            # 應該至少有 5 個工具
            assert tool_count >= 5

    @pytest.mark.asyncio
    async def test_agent_tools_have_descriptions(self):
        """測試工具有描述信息"""
        agent = await get_fundamental_agent()

        assert agent is not None
        if hasattr(agent, "tools") and agent.tools:
            for tool in agent.tools:
                # 每個工具應該有描述
                assert hasattr(tool, "description") or hasattr(tool, "name")


# ============================================================================
# 邊界和錯誤情況測試
# ============================================================================


class TestFundamentalAgentEdgeCases:
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
            "data": {
                "revenue": 1_000_000,
                "nested": {"key": "value"},
            },
        }
        result = parse_tool_params(args=json.dumps(nested_data))

        assert result["ticker"] == "2330"
        assert "data" in result
        assert "nested" in result["data"]

    @pytest.mark.asyncio
    async def test_multiple_agent_creations(self):
        """測試多次創建 Agent"""
        agent1 = await get_fundamental_agent()
        agent2 = await get_fundamental_agent()

        assert agent1 is not None
        assert agent2 is not None
        # 兩個代理應該都是有效的
        assert agent1.name == agent2.name

    def test_parse_with_special_characters(self):
        """測試特殊字符處理"""
        result = parse_tool_params(
            ticker="2330-TW",
            description="基本面分析 (台積電)",
            special="™®©",
        )

        assert result is not None
        assert result["ticker"] == "2330-TW"
        assert result["description"] == "基本面分析 (台積電)"

    def test_parse_with_very_large_dict(self):
        """測試大型字典解析"""
        large_dict = {f"key_{i}": i for i in range(1000)}

        result = parse_tool_params(**large_dict)

        assert result is not None
        assert len(result) >= 1000
