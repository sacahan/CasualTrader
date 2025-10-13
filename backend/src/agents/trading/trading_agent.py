"""
Trading Agent Implementation
基於 OpenAI Agent SDK 的智能交易 Agent
使用 Python 3.12+ 語法

## MCP Server 整合說明

Trading Agent 使用 Model Context Protocol (MCP) 來整合外部工具和服務。
MCP Server 配置從環境變數讀取，支援靈活的部署配置。

### 環境變數配置:

在 `.env` 文件中設定以下變數：
```env
# MCP Server 配置
MCP_CASUAL_MARKET_COMMAND="uvx"              # 執行命令 (uvx 或 npx)
MCP_CASUAL_MARKET_ARGS="casual-market-mcp"   # MCP Server 套件名稱
MCP_CASUAL_MARKET_TIMEOUT=10                 # API 請求超時時間（秒）
MCP_CASUAL_MARKET_RETRIES=5                  # API 重試次數
```

### 使用方式:

```python
from agents.trading.trading_agent import TradingAgent
from agents.core.models import AgentConfig

# 創建 Trading Agent，MCP Server 從環境變數自動配置
trading_agent = TradingAgent(
    config=AgentConfig(
        name="My Trading Agent",
        model="gpt-4o-mini",
        # ... 其他配置
    )
)

# MCP Server 會在首次使用時自動創建
```

### Casual Market MCP 提供的工具:

透過 stdio MCP Server 提供以下台股相關工具（自動配置）:
- `get_taiwan_stock_price`: 取得股票即時價格
- `get_company_profile`: 取得公司基本資料
- `get_company_income_statement`: 取得綜合損益表
- `get_company_balance_sheet`: 取得資產負債表
- `buy_taiwan_stock`: 執行買入交易(模擬)
- `sell_taiwan_stock`: 執行賣出交易(模擬)
- `check_taiwan_trading_day`: 檢查是否為交易日
- 以及其他財務分析和市場數據工具

### MCP Server 架構:

TradingAgent 使用 `MCPServerStdio` 來啟動本地 MCP Server 子進程：
- 命令: `uvx casual-market-mcp` (或 `npx casual-market-mcp`)
- 通訊: stdin/stdout
- 生命週期: 由 Agent 管理，自動啟動和關閉

參考文檔: https://openai.github.io/openai-agents-python/mcp/#4-stdio-mcp-servers
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, time
from typing import Any

import pytz

from ..core.base_agent import CasualTradingAgent
from ..core.models import (
    AgentConfig,
    AgentExecutionContext,
    AgentMode,
    generate_session_id,
)

# OpenAI Agent SDK Tools
try:
    from agents import CodeInterpreterTool, WebSearchTool, function_tool
    from agents.mcp import MCPServerStdio
except ImportError:
    # Fallback for development
    function_tool = Any
    WebSearchTool = Any
    CodeInterpreterTool = Any
    MCPServerStdio = None

# ==========================================
# Trading Agent 主要實作
# ==========================================


class TradingAgent(CasualTradingAgent):
    """
    智能交易 Agent - 基於 Prompt 驅動的投資決策系統
    """

    # MCP Server 配置方法（從環境變數讀取）
    @classmethod
    def _get_mcp_server_config(cls) -> dict[str, Any]:
        """
        獲取 MCP Server 配置（從環境變數或 config.py）

        Returns:
            包含 MCP Server 參數的字典，用於 MCPServerStdio 的 params 參數

        支援的 args 格式：
            - JSON 陣列: ["--from", "/path/to/dir", "casual-market-mcp"]
        """
        import json

        # 從環境變數讀取，提供預設值
        command = os.getenv("MCP_CASUAL_MARKET_COMMAND", "uvx")
        args_str = os.getenv("MCP_CASUAL_MARKET_ARGS", '["casual-market-mcp"]')

        # 解析 args - 必須是 JSON 陣列格式
        try:
            args = json.loads(args_str)
            if not isinstance(args, list):
                logging.warning("MCP_CASUAL_MARKET_ARGS is not a list, using default")
                args = ["casual-market-mcp"]
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse MCP_CASUAL_MARKET_ARGS as JSON: {e}")
            args = ["casual-market-mcp"]

        return {
            "command": command,
            "args": args,
        }

    @classmethod
    async def create_mcp_server(cls, name: str = "Casual Market MCP Server") -> Any | None:
        """
        創建 MCP Server 實例

        Args:
            name: MCP Server 名稱

        Returns:
            MCPServerStdio 實例，如果未安裝 SDK 則返回 None
        """
        if MCPServerStdio is None:
            logging.warning("MCPServerStdio not available, please install openai-agents-python")
            return None

        config = cls._get_mcp_server_config()

        try:
            # 根據 OpenAI Agents SDK 文檔，MCPServerStdio 的正確用法
            server = MCPServerStdio(
                name=name,
                params=config,
            )
            return server
        except Exception as e:
            logging.error(f"Failed to create MCP Server: {e}")
            return None

    def __init__(
        self,
        config: AgentConfig,
        agent_id: str | None = None,
        subagent_max_turns: int = 15,
    ) -> None:
        self.logger = logging.getLogger(f"trading_agent.{agent_id or 'unknown'}")
        self.logger.info(f"TradingAgent.__init__ called for agent_id={agent_id}")

        super().__init__(config, agent_id)
        self.logger.debug("TradingAgent: super().__init__ completed")

        # 交易相關設定
        self._market_data_cache: dict[str, Any] = {}
        self._portfolio_cache: dict[str, Any] = {}
        self._last_market_check: datetime | None = None

        # 策略變更追蹤
        self._strategy_changes: list[dict[str, Any]] = []

        # 統一管理 OpenAI 工具實例
        self._web_search_tool: WebSearchTool | None = None
        self._code_interpreter_tool: CodeInterpreterTool | None = None

        # Sub-agent 執行參數
        # Note: Timeout 由主 Agent 的 execution_timeout 統一控制
        self._subagent_max_turns = subagent_max_turns

        self.logger.info(f"TradingAgent.__init__ completed for {self.agent_id}")

    # ==========================================
    # 抽象方法實作
    # ==========================================

    async def _setup_tools(self) -> list[Any]:
        """設定 Trading Agent 工具"""
        self.logger.info(f"_setup_tools() started for {self.agent_id}")
        tools = []

        # 初始化 OpenAI 工具（供 sub-agents 共用）
        self.logger.debug("Calling _initialize_openai_tools()")
        await self._initialize_openai_tools()
        self.logger.debug("_initialize_openai_tools() completed")

        # 基本面分析工具
        if self.config.enabled_tools.get("fundamental_analysis", True):
            self.logger.debug("Setting up fundamental_analysis tools")
            tools.extend(await self._setup_fundamental_tools())
            self.logger.debug(f"fundamental_analysis tools added, total tools: {len(tools)}")

        # 技術分析工具
        if self.config.enabled_tools.get("technical_analysis", True):
            self.logger.debug("Setting up technical_analysis tools")
            tools.extend(await self._setup_technical_tools())
            self.logger.debug(f"technical_analysis tools added, total tools: {len(tools)}")

        # 風險評估工具
        if self.config.enabled_tools.get("risk_assessment", True):
            self.logger.debug("Setting up risk_assessment tools")
            tools.extend(await self._setup_risk_tools())
            self.logger.debug(f"risk_assessment tools added, total tools: {len(tools)}")

        # 市場情緒分析工具
        if self.config.enabled_tools.get("sentiment_analysis", True):
            self.logger.debug("Setting up sentiment_analysis tools")
            tools.extend(await self._setup_sentiment_tools())
            self.logger.debug(f"sentiment_analysis tools added, total tools: {len(tools)}")

        # 加入 OpenAI 內建工具
        if self._web_search_tool:
            tools.append(self._web_search_tool)
            self.logger.debug("web_search_tool added")
        if self._code_interpreter_tool:
            tools.append(self._code_interpreter_tool)
            self.logger.debug("code_interpreter_tool added")

        # 交易驗證和執行工具
        self.logger.debug("Setting up trading tools")
        tools.extend(await self._setup_trading_tools())
        self.logger.debug(f"trading tools added, total tools: {len(tools)}")

        self.logger.info(f"Configured {len(tools)} tools for trading agent")
        return tools

    async def _prepare_execution(self, context: AgentExecutionContext) -> None:
        """執行前準備工作"""
        # 更新市場狀態
        await self._update_market_status()

        # 更新投資組合狀態
        await self._update_portfolio_status()

        # 設定執行上下文
        context.market_is_open = await self._check_market_hours()
        context.available_cash = self._get_available_cash()
        context.current_holdings = self._get_current_holdings()

        self.logger.info(
            f"Execution prepared - Market open: {context.market_is_open}, "
            f"Cash: NT${context.available_cash:,.0f}, "
            f"Holdings: {len(context.current_holdings)} positions"
        )

    async def _build_execution_prompt(self, context: AgentExecutionContext) -> str:
        """建構執行提示詞"""
        # 基礎情境資訊
        market_status = "開盤中" if context.market_is_open else "休市中"
        current_time = datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")

        # 投資組合摘要
        portfolio_summary = self._build_portfolio_summary(context.current_holdings)

        # 根據模式生成不同的提示詞
        mode_prompt = self._build_mode_specific_prompt(context.mode)

        # 完整提示詞
        execution_prompt = f"""
當前時間：{current_time}
市場狀態：{market_status}
執行模式：{context.mode}

投資組合狀況：
{portfolio_summary}

可用現金：NT${context.available_cash:,.0f}

{mode_prompt}

{self._build_market_context()}

{self._build_strategy_guidance()}

請根據當前情況執行適當的投資決策。
        """.strip()

        return execution_prompt

    # ==========================================
    # 工具設定方法
    # ==========================================

    async def _initialize_openai_tools(self) -> None:
        """初始化 OpenAI 工具實例（統一管理，供所有 sub-agents 使用）"""
        # Web Search Tool - 用於搜尋最新市場新聞和資訊
        if self.config.enabled_tools.get("web_search", True):
            try:
                self._web_search_tool = WebSearchTool()
                self.logger.debug("Initialized WebSearchTool")
            except Exception as e:
                self.logger.warning(f"Failed to initialize WebSearchTool: {e}")

        # Code Interpreter Tool - 用於量化分析和計算
        if self.config.enabled_tools.get("code_interpreter", True):
            try:
                self._code_interpreter_tool = CodeInterpreterTool(
                    tool_config={"type": "code_interpreter", "container": {"type": "auto"}}
                )
                self.logger.debug("Initialized CodeInterpreterTool")
            except Exception as e:
                self.logger.warning(f"Failed to initialize CodeInterpreterTool: {e}")

    def _get_shared_tools(self) -> list[Any]:
        """獲取共用工具（供 sub-agents 使用）"""
        shared_tools = []
        if self._web_search_tool:
            shared_tools.append(self._web_search_tool)
        if self._code_interpreter_tool:
            shared_tools.append(self._code_interpreter_tool)
        return shared_tools

    async def _get_mcp_server_instance(self) -> Any | None:
        """
        獲取 MCP Server 實例（延遲創建）

        Returns:
            MCPServerStdio 實例或 None
        """
        if not hasattr(self, "_mcp_server_instance"):
            self._mcp_server_instance = await self.create_mcp_server()
        return self._mcp_server_instance

    async def _setup_fundamental_tools(self) -> list[Any]:
        """設定基本面分析工具"""
        self.logger.debug("_setup_fundamental_tools() started")
        try:
            self.logger.debug("Importing get_fundamental_agent")
            from ..tools.fundamental_agent import get_fundamental_agent

            # 獲取 MCP Server 實例
            self.logger.debug("Getting MCP Server instance")
            mcp_server = await self._get_mcp_server_instance()
            mcp_servers = [mcp_server] if mcp_server else []
            self.logger.debug(f"MCP Server instance: {mcp_server is not None}")

            # 創建 Agent
            self.logger.info(f"Creating fundamental_agent with ai_model={self.config.ai_model}")
            fundamental_agent = await get_fundamental_agent(
                mcp_servers=mcp_servers,
                model_name=self.config.ai_model,
                shared_tools=self._get_shared_tools(),
                max_turns=self._subagent_max_turns,
            )
            self.logger.debug("fundamental_agent created successfully")

            # 轉換為 Tool
            self.logger.debug("Converting fundamental_agent to tool")
            fundamental_tool = fundamental_agent.as_tool(
                tool_name="FundamentalAnalyst",
                tool_description="""專業基本面分析 Agent,提供深入的財務和價值分析。

功能: 財務比率計算、財務體質評估、估值分析、成長潛力評估、投資評級

適用場景: 價值投資、長期投資決策、公司基本面研究、股票篩選""",
            )
            self.logger.info("Fundamental tools setup completed")
            return [fundamental_tool]
        except ImportError as e:
            self.logger.warning(f"Fundamental agent not available: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error setting up fundamental tools: {e}", exc_info=True)
            raise

    async def _setup_technical_tools(self) -> list[Any]:
        """設定技術分析工具"""
        try:
            from ..tools.technical_agent import get_technical_agent

            # 獲取 MCP Server 實例
            mcp_server = await self._get_mcp_server_instance()
            mcp_servers = [mcp_server] if mcp_server else []

            # 創建 Agent
            technical_agent = await get_technical_agent(
                mcp_servers=mcp_servers,
                model_name=self.config.ai_model,
                shared_tools=self._get_shared_tools(),
                max_turns=self._subagent_max_turns,
            )

            # 轉換為 Tool
            technical_tool = technical_agent.as_tool(
                tool_name="TechnicalAnalyst",
                tool_description="""專業技術分析 Agent,提供深入的股票技術面分析。

功能: 圖表型態識別、技術指標分析、趨勢判斷、支撐壓力、交易訊號

適用場景: 技術面分析、進出場時機判斷、趨勢確認、交易策略制定""",
            )
            return [technical_tool]
        except ImportError as e:
            self.logger.warning(f"Technical agent not available: {e}")
            return []

    async def _setup_risk_tools(self) -> list[Any]:
        """設定風險評估工具"""
        try:
            from ..tools.risk_agent import get_risk_agent

            # 獲取 MCP Server 實例
            mcp_server = await self._get_mcp_server_instance()
            mcp_servers = [mcp_server] if mcp_server else []

            # 創建 Agent
            risk_agent = await get_risk_agent(
                mcp_servers=mcp_servers,
                model_name=self.config.ai_model,
                shared_tools=self._get_shared_tools(),
                max_turns=self._subagent_max_turns,
            )

            # 轉換為 Tool
            risk_tool = risk_agent.as_tool(
                tool_name="RiskManager",
                tool_description="""專業風險管理 Agent,提供全面的風險評估和控制建議。

功能: 部位風險計算、集中度分析、投資組合風險評估、壓力測試、風險管理建議

適用場景: 風險控制、部位管理、投資組合優化、風險預警""",
            )
            return [risk_tool]
        except ImportError as e:
            self.logger.warning(f"Risk agent not available: {e}")
            return []

    async def _setup_sentiment_tools(self) -> list[Any]:
        """設定市場情緒分析工具"""
        try:
            from ..tools.sentiment_agent import get_sentiment_agent

            # 獲取 MCP Server 實例
            mcp_server = await self._get_mcp_server_instance()
            mcp_servers = [mcp_server] if mcp_server else []

            # 創建 Agent
            sentiment_agent = await get_sentiment_agent(
                mcp_servers=mcp_servers,
                model_name=self.config.ai_model,
                shared_tools=self._get_shared_tools(),
                max_turns=self._subagent_max_turns,
            )

            # 轉換為 Tool
            sentiment_tool = sentiment_agent.as_tool(
                tool_name="SentimentAnalyst",
                tool_description="""專業市場情緒分析 Agent,提供全面的心理面和資金面分析。

功能: 恐懼貪婪指數、資金流向追蹤、新聞情緒分析、社群情緒分析、情緒交易訊號

適用場景: 市場時機判斷、反向操作策略、短線交易、情緒面研究""",
            )
            return [sentiment_tool]
        except ImportError as e:
            self.logger.warning(f"Sentiment agent not available: {e}")
            return []

    # ==========================================
    # Trading Tools (使用 @function_tool decorator)
    # ==========================================

    @function_tool(strict_mode=False)
    async def check_market_open(self) -> bool:
        """檢查台灣股市是否開盤中

        Returns:
            bool: True 表示市場開盤中，False 表示市場關閉
        """
        taiwan_tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(taiwan_tz)

        # 台股交易時間：週一到週五 09:00-13:30
        is_weekday = now.weekday() < 5
        is_trading_time = time(9, 0) <= now.time() <= time(13, 30)

        return is_weekday and is_trading_time

    @function_tool(strict_mode=False)
    def get_available_cash(self) -> dict[str, float]:
        """獲取當前可用現金餘額

        Returns:
            dict: 包含 available_cash 鍵值的字典
        """
        return {"available_cash": self._get_available_cash()}

    @function_tool(strict_mode=False)
    def get_current_holdings(self) -> dict[str, Any]:
        """獲取當前投資組合持倉

        Returns:
            dict: 包含 holdings 鍵值的字典，holdings 為持倉詳情
        """
        return {"holdings": self._get_current_holdings()}

    @function_tool(strict_mode=False)
    async def record_strategy_change_tool(
        self,
        trigger_reason: str,
        new_strategy_addition: str,
        change_summary: str,
        agent_explanation: str,
    ) -> dict[str, str]:
        """記錄投資策略調整

        用於記錄 Agent 自主學習和策略調整的過程。

        Args:
            trigger_reason: 觸發原因
            new_strategy_addition: 新增策略內容
            change_summary: 變更摘要
            agent_explanation: Agent 解釋

        Returns:
            dict: 包含記錄結果的字典
        """
        result = await self.record_strategy_change(
            trigger_reason=trigger_reason,
            new_strategy_addition=new_strategy_addition,
            change_summary=change_summary,
            agent_explanation=agent_explanation,
        )
        return {"status": "success", "message": "Strategy change recorded", "result": result}

    async def _setup_trading_tools(self) -> list[Any]:
        """設定交易驗證和執行工具

        使用 @function_tool decorator 定義的方法，自動從 docstring 和 type hints 生成工具 schema。
        """
        return [
            self.check_market_open,
            self.get_available_cash,
            self.get_current_holdings,
            self.record_strategy_change_tool,
        ]

    # ==========================================
    # 市場狀態管理
    # ==========================================

    async def _update_market_status(self) -> None:
        """更新市場狀態資訊"""
        current_time = datetime.now()

        # 避免頻繁更新
        if self._last_market_check and (current_time - self._last_market_check).seconds < 300:
            return

        try:
            # 這裡可以整合市場數據更新
            self._market_data_cache = {
                "last_update": current_time.isoformat(),
                "market_open": await self._check_market_hours(),
                # 其他市場指標...
            }

            self._last_market_check = current_time
            self.logger.debug("Market status updated")

        except Exception as e:
            self.logger.error(f"Failed to update market status: {e}")

    async def _update_portfolio_status(self) -> None:
        """更新投資組合狀態"""
        try:
            # 這裡將整合資料庫查詢
            self._portfolio_cache = {
                "last_update": datetime.now().isoformat(),
                "total_value": self.config.current_funds or self.config.initial_funds,
                "cash_balance": self.config.current_funds or self.config.initial_funds,
                "holdings": {},  # 從資料庫查詢持倉
                # 其他投資組合指標...
            }

            self.logger.debug("Portfolio status updated")

        except Exception as e:
            self.logger.error(f"Failed to update portfolio status: {e}")

    def _get_available_cash(self) -> float:
        """獲取可用現金"""
        return self._portfolio_cache.get(
            "cash_balance", self.config.current_funds or self.config.initial_funds
        )

    def _get_current_holdings(self) -> dict[str, Any]:
        """獲取當前持倉"""
        return self._portfolio_cache.get("holdings", {})

    # ==========================================
    # 提示詞生成
    # ==========================================

    def _build_portfolio_summary(self, holdings: dict[str, Any]) -> str:
        """建構投資組合摘要"""
        if not holdings:
            return "目前無持股部位"

        # 計算持倉摘要
        total_positions = len(holdings)
        total_value = sum(holding.get("market_value", 0) for holding in holdings.values())

        summary = f"持股檔數：{total_positions}\n"
        summary += f"總市值：NT${total_value:,.0f}\n"

        # 列出主要持股（前 5 大）
        sorted_holdings = sorted(
            holdings.items(),
            key=lambda x: x[1].get("market_value", 0),
            reverse=True,
        )

        summary += "主要持股：\n"
        for symbol, holding in sorted_holdings[:5]:
            market_value = holding.get("market_value", 0)
            summary += f"  {symbol}: NT${market_value:,.0f}\n"

        return summary

    def _build_mode_specific_prompt(self, mode: AgentMode) -> str:
        """根據執行模式建構特定提示詞"""
        match mode:
            case AgentMode.TRADING:
                return """
🔄 **交易模式** - 主動尋找投資機會並執行交易決策

任務重點：
1. 分析市場機會和個股投資價值
2. 根據投資策略執行買賣決策
3. 管理部位大小和風險控制
4. 記錄交易決策的原因和預期

注意事項：
- 僅在開盤時間執行實際交易
- 遵守最大部位限制和風險控制規則
- 每筆交易需要詳細的分析和理由
                """.strip()

            case AgentMode.REBALANCING:
                return """
⚖️ **再平衡模式** - 調整投資組合配置

任務重點：
1. 評估當前投資組合的配置狀況
2. 識別需要調整的部位
3. 執行賣出過重部位、買入不足部位
4. 優化整體風險收益特性

注意事項：
- 考慮交易成本和稅務影響
- 保持投資策略的一致性
- 避免過度頻繁的調整
                """.strip()

            case AgentMode.STRATEGY_REVIEW:
                return """
📊 **策略檢討模式** - 評估和調整投資策略

任務重點：
1. 回顧近期投資績效和決策品質
2. 分析市場環境變化的影響
3. 評估策略調整的必要性
4. 記錄策略變更的原因和內容

注意事項：
- 基於客觀數據和績效分析
- 考慮長期投資目標
- 記錄所有策略變更以供追蹤
                """.strip()

            case AgentMode.OBSERVATION:
                return """
👀 **觀察模式** - 市場監控和分析

任務重點：
1. 監控市場趨勢和重要事件
2. 分析持股公司的最新動態
3. 評估潛在投資機會
4. 準備投資決策的背景資料

注意事項：
- 不執行實際交易，僅進行分析
- 關注長期趨勢和結構性變化
- 為下次交易模式執行做準備
                """.strip()

    def _build_market_context(self) -> str:
        """建構市場環境上下文"""
        market_open = self._market_data_cache.get("market_open", False)

        context = f"""
市場環境：
- 交易狀態：{"開盤中" if market_open else "休市中"}
- 當前時段：{datetime.now(pytz.timezone("Asia/Taipei")).strftime("%A %H:%M")}
        """.strip()

        return context

    def _build_strategy_guidance(self) -> str:
        """建構策略指導"""
        guidance = f"""
投資策略指導：
{self.config.investment_preferences}

策略調整依據：
{self.config.strategy_adjustment_criteria}
        """.strip()

        if self.config.auto_adjust.enabled:
            guidance += f"""

自動調整設定：
- 觸發條件：{self.config.auto_adjust.triggers}
- 自動套用：{"是" if self.config.auto_adjust.auto_apply else "否"}
            """.strip()

        return guidance

    # ==========================================
    # 策略管理
    # ==========================================

    async def record_strategy_change(
        self,
        trigger_reason: str,
        new_strategy_addition: str,
        change_summary: str,
        agent_explanation: str,
    ) -> dict[str, Any]:
        """記錄策略變更"""
        change_record = {
            "id": generate_session_id(self.agent_id),
            "timestamp": datetime.now().isoformat(),
            "trigger_reason": trigger_reason,
            "new_strategy_addition": new_strategy_addition,
            "change_summary": change_summary,
            "agent_explanation": agent_explanation,
            "performance_at_change": self.get_performance_summary(),
        }

        self._strategy_changes.append(change_record)

        # 更新 Agent 指令
        current_instructions = await self._build_agent_instructions()
        updated_instructions = current_instructions + "\n\n" + new_strategy_addition

        # 更新配置
        self.config.instructions = updated_instructions

        self.logger.info(f"Strategy change recorded: {change_summary}")

        return {
            "success": True,
            "change_id": change_record["id"],
            "message": "Strategy change recorded successfully",
        }

    def get_strategy_changes(self) -> list[dict[str, Any]]:
        """獲取策略變更歷史"""
        return self._strategy_changes.copy()

    # ==========================================
    # 屬性和特殊方法
    # ==========================================

    async def get_mcp_servers_list(self) -> list[Any]:
        """
        獲取 MCP servers 實例列表（供外部使用）

        Returns:
            MCPServerStdio 實例列表
        """
        mcp_server = await self._get_mcp_server_instance()
        return [mcp_server] if mcp_server else []

    def __repr__(self) -> str:
        return (
            f"TradingAgent(id={self.agent_id}, "
            f"name='{self.config.name}', "
            f"status={self.state.status}, "
            f"mode={self.state.current_mode}, "
            f"funds=NT${self.config.current_funds or self.config.initial_funds:,.0f})"
        )
