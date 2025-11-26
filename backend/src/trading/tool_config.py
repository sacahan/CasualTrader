"""
動態工具配置管理

根據 Agent 執行模式 (TRADING/REBALANCING) 動態加載所需工具的配置管理模組。

### 工具配置設計

#### TRADING 模式 (完整工具集)
- OpenAI Tools: ~~WebSearch, CodeInterpreter~~ (LiteLLM 不支持，已禁用)
- MCP Servers: memory-mcp, casual-market-mcp, perplexity-mcp
- 交易工具: buy_stock, sell_stock, get_portfolio, get_cash_balance
- Sub-agents: 4 個 (Fundamental, Technical, Risk, Sentiment)

#### REBALANCING 模式 (簡化工具集)
- OpenAI Tools: ~~CodeInterpreter~~ (LiteLLM 不支持，已禁用)
- MCP Servers: memory-mcp, casual-market-mcp, perplexity-mcp (新聞搜尋)
- 交易工具: get_portfolio, get_cash_balance (無買賣工具)
- Sub-agents: 2 個 (Technical, Risk)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from common.enums import AgentMode
from common.logger import logger


@dataclass(frozen=True)
class ToolRequirements:
    """工具需求規格

    定義 Agent 在某個執行模式下所需的所有工具配置。

    Attributes:
        include_web_search: 是否包含網路搜尋工具
        include_code_interpreter: 是否包含程式碼執行工具
        include_memory_mcp: 是否包含記憶體 MCP 伺服器
        include_casual_market_mcp: 是否包含市場數據 MCP 伺服器
        include_perplexity_mcp: 是否包含新聞/投資研究 MCP 伺服器
        include_buy_sell_tools: 是否包含買賣交易工具
        include_portfolio_tools: 是否包含投資組合查詢工具
        include_fundamental_agent: 是否包含基本面分析 Sub-agent
        include_technical_agent: 是否包含技術面分析 Sub-agent
        include_risk_agent: 是否包含風險評估 Sub-agent
        include_sentiment_agent: 是否包含情緒分析 Sub-agent
    """

    include_web_search: bool
    include_code_interpreter: bool
    include_memory_mcp: bool
    include_casual_market_mcp: bool
    include_perplexity_mcp: bool
    include_buy_sell_tools: bool
    include_portfolio_tools: bool
    include_fundamental_agent: bool
    include_technical_agent: bool
    include_risk_agent: bool
    include_sentiment_agent: bool

    def __str__(self) -> str:
        """生成配置摘要"""
        tools = []
        if self.include_web_search:
            tools.append("WebSearch")
        if self.include_code_interpreter:
            tools.append("CodeInterpreter")
        if self.include_buy_sell_tools:
            tools.append("BuySellTools")
        if self.include_portfolio_tools:
            tools.append("PortfolioTools")

        mcps = []
        if self.include_memory_mcp:
            mcps.append("memory")
        if self.include_casual_market_mcp:
            mcps.append("market")
        if self.include_perplexity_mcp:
            mcps.append("perplexity")

        agents = []
        if self.include_fundamental_agent:
            agents.append("Fundamental")
        if self.include_technical_agent:
            agents.append("Technical")
        if self.include_risk_agent:
            agents.append("Risk")
        if self.include_sentiment_agent:
            agents.append("Sentiment")

        return (
            f"Tools: {', '.join(tools) or 'None'} | "
            f"MCPs: {', '.join(mcps)} | "
            f"Agents: {', '.join(agents)}"
        )


class ToolConfig:
    """動態工具配置管理器

    根據 Agent 執行模式返回相應的工具配置。
    """

    # TRADING 模式：完整工具集配置
    _TRADING_CONFIG: Final[ToolRequirements] = ToolRequirements(
        include_web_search=False,  # ❌ LiteLLM 不支持 OpenAI Tools
        include_code_interpreter=False,  # ❌ LiteLLM 不支持 OpenAI Tools
        include_memory_mcp=True,
        include_casual_market_mcp=True,
        include_perplexity_mcp=True,
        include_buy_sell_tools=True,
        include_portfolio_tools=True,
        include_fundamental_agent=True,
        include_technical_agent=True,
        include_risk_agent=True,
        include_sentiment_agent=True,
    )

    # REBALANCING 模式：簡化工具集配置
    _REBALANCING_CONFIG: Final[ToolRequirements] = ToolRequirements(
        include_web_search=False,  # ❌ LiteLLM 不支持 OpenAI Tools
        include_code_interpreter=False,  # ❌ LiteLLM 不支持 OpenAI Tools
        include_memory_mcp=True,
        include_casual_market_mcp=True,
        include_perplexity_mcp=True,  # ✅ 可用於新聞搜尋和信息檢索
        include_buy_sell_tools=False,  # ❌ 不執行買賣操作
        include_portfolio_tools=True,
        include_fundamental_agent=False,  # ❌ 不需要基本面分析
        include_technical_agent=True,
        include_risk_agent=True,
        include_sentiment_agent=False,  # ❌ 不需要情緒分析
    )

    @staticmethod
    def get_requirements(mode: AgentMode | None = None) -> ToolRequirements:
        """根據執行模式返回工具需求配置

        Args:
            mode: Agent 執行模式。若為 None，預設為 TRADING

        Returns:
            ToolRequirements：對應模式的工具配置

        Raises:
            ValueError: 如果提供的模式不支援

        Examples:
            >>> config = ToolConfig.get_requirements(AgentMode.TRADING)
            >>> config.include_web_search
            True

            >>> config = ToolConfig.get_requirements(AgentMode.REBALANCING)
            >>> config.include_buy_sell_tools
            False
        """
        if mode is None:
            mode = AgentMode.TRADING

        if mode == AgentMode.TRADING:
            logger.debug(
                "Tool configuration loaded",
                extra={"mode": "TRADING", "config": str(ToolConfig._TRADING_CONFIG)},
            )
            return ToolConfig._TRADING_CONFIG

        elif mode == AgentMode.REBALANCING:
            logger.debug(
                "Tool configuration loaded",
                extra={
                    "mode": "REBALANCING",
                    "config": str(ToolConfig._REBALANCING_CONFIG),
                },
            )
            return ToolConfig._REBALANCING_CONFIG

        else:
            error_msg = f"Unsupported agent mode: {mode}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    @staticmethod
    def compare_configurations(mode1: AgentMode, mode2: AgentMode) -> dict[str, bool]:
        """比較兩個模式的工具配置差異

        用於分析不同模式間的工具差異。

        Args:
            mode1: 第一個模式
            mode2: 第二個模式

        Returns:
            dict: 鍵為配置項名稱，值為是否存在差異

        Examples:
            >>> diff = ToolConfig.compare_configurations(AgentMode.TRADING, AgentMode.REBALANCING)
            >>> diff["include_web_search"]
            True  # 表示兩個模式在此項上有差異
        """
        config1 = ToolConfig.get_requirements(mode1)
        config2 = ToolConfig.get_requirements(mode2)

        differences = {}
        for field in config1.__dataclass_fields__:
            val1 = getattr(config1, field)
            val2 = getattr(config2, field)
            if val1 != val2:
                differences[field] = True

        return differences


# 預設配置快取，避免重複建立
_CONFIG_CACHE: dict[AgentMode, ToolRequirements] = {
    AgentMode.TRADING: ToolConfig._TRADING_CONFIG,
    AgentMode.REBALANCING: ToolConfig._REBALANCING_CONFIG,
}


def get_tool_config(mode: AgentMode | None = None) -> ToolRequirements:
    """便利函數：取得工具配置

    Args:
        mode: Agent 執行模式

    Returns:
        ToolRequirements：對應模式的工具配置
    """
    if mode is None:
        mode = AgentMode.TRADING
    return _CONFIG_CACHE.get(mode, ToolConfig.get_requirements(mode))
