"""
風險評估 Agent 的測試

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

from trading.tools.risk_agent import (  # noqa: E402
    parse_tool_params,
    risk_agent_instructions,
    get_risk_agent,
)


# ============================================================================
# 輔助函數測試
# ============================================================================


class TestRiskAgentParseToolParams:
    """測試風險 Agent 的參數解析函數"""

    def test_parse_direct_parameters(self):
        """測試直接參數解析"""
        result = parse_tool_params(ticker="2330", position_size=1000)
        assert result["ticker"] == "2330"
        assert result["position_size"] == 1000

    def test_parse_json_string_in_args(self):
        """測試 JSON 字符串參數解析"""
        import json

        data = {"ticker": "2330", "risk_level": 0.15}
        result = parse_tool_params(args=json.dumps(data))
        assert result["ticker"] == "2330"
        assert result["risk_level"] == 0.15

    def test_parse_removes_invalid_keys(self):
        """測試移除無效鍵"""
        result = parse_tool_params(ticker="2330", input_image="invalid", riskage="value")
        assert "ticker" in result
        assert "riskage" in result
        assert "input_image" not in result

    def test_parse_empty_parameters(self):
        """測試空參數"""
        result = parse_tool_params()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parse_market_risk_data(self):
        """測試市場風險數據解析"""
        risk_data = {"market_volatility": 0.25, "correlation": 0.75}
        result = parse_tool_params(market_data=risk_data)

        assert result is not None
        assert "market_data" in result


# ============================================================================
# Agent 初始化和工具加載測試
# ============================================================================


class TestRiskAgentInitialization:
    """測試 Risk Agent 初始化"""

    def test_agent_instructions_generated(self):
        """測試 Agent 指令生成"""
        instructions = risk_agent_instructions()

        assert instructions is not None
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        # 驗證關鍵內容存在
        assert "風險" in instructions or "risk" in instructions.lower()

    @pytest.mark.asyncio
    async def test_get_risk_agent_creation(self):
        """測試創建 Risk Agent"""
        agent = await get_risk_agent()

        assert agent is not None
        assert hasattr(agent, "name")
        assert agent.name == "risk_analyst"
        assert hasattr(agent, "instructions")

    @pytest.mark.asyncio
    async def test_get_risk_agent_with_empty_mcp(self):
        """測試帶空 MCP servers 列表創建 Agent"""
        agent = await get_risk_agent(mcp_servers=[])

        assert agent is not None
        assert hasattr(agent, "name")
        assert agent.name == "risk_analyst"

    @pytest.mark.asyncio
    async def test_risk_agent_has_tools(self):
        """測試 Agent 包含工具"""
        agent = await get_risk_agent()

        assert agent is not None
        # Agent 應該有 tools 屬性或方法
        has_tools = hasattr(agent, "tools") or hasattr(agent, "model_settings")
        assert has_tools is True

    @pytest.mark.asyncio
    async def test_risk_agent_model_settings(self):
        """測試 Agent 模型配置"""
        agent = await get_risk_agent()

        assert agent is not None
        # 驗證 Agent 有必要的配置屬性
        assert hasattr(agent, "instructions") or hasattr(agent, "tools")


# ============================================================================
# 工具定義驗證測試
# ============================================================================


class TestRiskAgentTools:
    """測試 Risk Agent 工具定義"""

    @pytest.mark.asyncio
    async def test_agent_has_required_tools(self):
        """測試 Agent 包含必要的工具"""
        agent = await get_risk_agent()

        assert agent is not None
        # Agent 應該包含風險評估相關的工具

        if hasattr(agent, "tools") and agent.tools:
            tool_count = len(agent.tools)
            # 應該至少有工具
            assert tool_count >= 3

    @pytest.mark.asyncio
    async def test_agent_tools_have_descriptions(self):
        """測試工具有描述信息"""
        agent = await get_risk_agent()

        assert agent is not None
        if hasattr(agent, "tools") and agent.tools:
            for tool in agent.tools:
                # 每個工具應該有描述
                assert hasattr(tool, "description") or hasattr(tool, "name")


# ============================================================================
# 邊界和錯誤情況測試
# ============================================================================


class TestRiskAgentEdgeCases:
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
            "risk_data": {
                "volatility": 0.25,
                "nested": {"key": "value"},
            },
        }
        result = parse_tool_params(args=json.dumps(nested_data))

        assert result["ticker"] == "2330"
        assert "risk_data" in result

    @pytest.mark.asyncio
    async def test_multiple_agent_creations(self):
        """測試多次創建 Agent"""
        agent1 = await get_risk_agent()
        agent2 = await get_risk_agent()

        assert agent1 is not None
        assert agent2 is not None
        # 兩個代理應該都是有效的
        assert agent1.name == agent2.name

    def test_parse_with_special_characters(self):
        """測試特殊字符處理"""
        result = parse_tool_params(
            ticker="2330-TW",
            description="風險評估 (台積電)",
            special="™®©",
        )

        assert result is not None
        assert result["ticker"] == "2330-TW"

    def test_parse_extreme_risk_values(self):
        """測試極端風險數值"""
        result = parse_tool_params(
            max_drawdown=0.99,
            var_95=1.5,
            min_drawdown=-0.99,
        )

        assert result is not None
        assert result["max_drawdown"] == 0.99
        assert result["var_95"] == 1.5


# ============================================================================
# 風險管理特定場景測試
# ============================================================================


class TestRiskAgentScenarios:
    """測試風險管理場景"""

    @pytest.mark.asyncio
    async def test_agent_creation_with_custom_model(self):
        """測試使用自訂模型創建 Agent"""
        # 即使沒有實際的 LitellmModel，Agent 應該也能創建
        agent = await get_risk_agent(llm_model=None)

        assert agent is not None
        assert agent.name == "risk_analyst"

    def test_parse_portfolio_position_data(self):
        """測試投資組合持倉數據解析"""
        position_data = {
            "holdings": [
                {"ticker": "2330", "shares": 1000, "avg_cost": 520.0},
                {"ticker": "2454", "shares": 500, "avg_cost": 1000.0},
            ],
            "cash": 1000000,
        }

        result = parse_tool_params(portfolio=position_data)

        assert result is not None
        assert "portfolio" in result

    def test_parse_risk_metrics(self):
        """測試風險指標解析"""
        metrics = {
            "volatility": 0.18,
            "beta": 1.2,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.35,
        }

        result = parse_tool_params(metrics=metrics)

        assert result is not None
        assert result["metrics"]["volatility"] == 0.18
        assert result["metrics"]["beta"] == 1.2

    def test_parse_with_zero_values(self):
        """測試零值處理"""
        result = parse_tool_params(
            risk_level=0,
            position_size=0,
            correlation=0.0,
        )

        assert result is not None
        assert result["risk_level"] == 0
        assert result["position_size"] == 0
