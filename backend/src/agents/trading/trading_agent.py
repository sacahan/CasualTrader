"""
Trading Agent Implementation
基於 OpenAI Agent SDK 的智能交易 Agent
使用 Python 3.12+ 語法

## MCP 工具整合說明

Trading Agent 使用 Casual Market MCP 提供的台股市場數據工具。
這些工具應該在創建 Agent 時透過 `mcp_servers` 參數傳入,而不是在代碼中直接包裝。

### 使用方式:

```python
from agents import Agent

# 創建 Agent 時傳入 MCP servers 配置
trading_agent = Agent(
    name="Trading Agent",
    instructions="...",
    tools=[...],  # FunctionTool 等自定義工具
    mcp_servers={
        "casual-market": {
            "command": "uvx",
            "args": ["casual-market-mcp"]
        }
    }
)
```

### 可用的 MCP 工具:

Casual Market MCP 提供以下台股相關工具:
- `get_taiwan_stock_price`: 取得股票即時價格
- `get_company_profile`: 取得公司基本資料
- `get_income_statement`: 取得綜合損益表
- `get_balance_sheet`: 取得資產負債表
- `buy_taiwan_stock`: 執行買入交易(模擬)
- `sell_taiwan_stock`: 執行賣出交易(模擬)
- `check_taiwan_trading_day`: 檢查是否為交易日
- 以及其他財務分析和市場數據工具

詳細的 MCP 工具列表請參考: https://github.com/yourusername/casual-market-mcp
"""

from __future__ import annotations

import logging
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
    from agents import CodeInterpreterTool, FunctionTool, WebSearchTool
except ImportError:
    # Fallback for development
    FunctionTool = Any
    WebSearchTool = Any
    CodeInterpreterTool = Any

# ==========================================
# Trading Agent 主要實作
# ==========================================


class TradingAgent(CasualTradingAgent):
    """
    智能交易 Agent - 基於 Prompt 驅動的投資決策系統
    """

    def __init__(self, config: AgentConfig, agent_id: str | None = None) -> None:
        super().__init__(config, agent_id)

        # 交易相關設定
        self._market_data_cache: dict[str, Any] = {}
        self._portfolio_cache: dict[str, Any] = {}
        self._last_market_check: datetime | None = None

        # 策略變更追蹤
        self._strategy_changes: list[dict[str, Any]] = []

        self.logger = logging.getLogger(f"trading_agent.{self.agent_id}")

    # ==========================================
    # 抽象方法實作
    # ==========================================

    async def _setup_tools(self) -> list[Any]:
        """設定 Trading Agent 工具"""
        tools = []

        # 基本面分析工具
        if self.config.enabled_tools.get("fundamental_analysis", True):
            tools.extend(await self._setup_fundamental_tools())

        # 技術分析工具
        if self.config.enabled_tools.get("technical_analysis", True):
            tools.extend(await self._setup_technical_tools())

        # 風險評估工具
        if self.config.enabled_tools.get("risk_assessment", True):
            tools.extend(await self._setup_risk_tools())

        # 市場情緒分析工具
        if self.config.enabled_tools.get("sentiment_analysis", True):
            tools.extend(await self._setup_sentiment_tools())

        # OpenAI 內建工具 (WebSearch, CodeInterpreter)
        tools.extend(await self._setup_openai_tools())

        # 交易驗證和執行工具
        tools.extend(await self._setup_trading_tools())

        # Note: CasualMarket MCP tools should be added via mcp_servers parameter
        # when creating the agent, not through FunctionTool wrappers

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

    async def _setup_fundamental_tools(self) -> list[Any]:
        """設定基本面分析工具 - 整合 Fundamental Agent"""
        try:
            from ..tools.fundamental_agent import get_fundamental_agent_tool

            # 獲取基本面分析 Agent 工具
            # TODO: 需要傳入 MCP servers 參數
            fundamental_tool = await get_fundamental_agent_tool(
                mcp_servers=[],  # 將由 Agent 層級的 mcp_servers 參數處理
                model_name=self.config.model,
            )
            return [fundamental_tool]
        except ImportError as e:
            self.logger.warning(f"Fundamental agent not available: {e}")
            return []

    async def _setup_technical_tools(self) -> list[Any]:
        """設定技術分析工具 - 整合 Technical Agent"""
        try:
            from ..tools.technical_agent import get_technical_agent_tool

            # 獲取技術分析 Agent 工具
            technical_tool = await get_technical_agent_tool(
                mcp_servers=[],  # 將由 Agent 層級的 mcp_servers 參數處理
                model_name=self.config.model,
            )
            return [technical_tool]
        except ImportError as e:
            self.logger.warning(f"Technical agent not available: {e}")
            return []

    async def _setup_risk_tools(self) -> list[Any]:
        """設定風險評估工具 - 整合 Risk Management Agent"""
        try:
            from ..tools.risk_agent import get_risk_agent_tool

            # 獲取風險管理 Agent 工具
            risk_tool = await get_risk_agent_tool(
                mcp_servers=[],
                model_name=self.config.model,
            )
            return [risk_tool]
        except ImportError as e:
            self.logger.warning(f"Risk agent not available: {e}")
            return []

    async def _setup_sentiment_tools(self) -> list[Any]:
        """設定市場情緒分析工具 - 整合 Sentiment Agent"""
        try:
            from ..tools.sentiment_agent import get_sentiment_agent_tool

            # 獲取市場情緒分析 Agent 工具
            sentiment_tool = await get_sentiment_agent_tool(
                mcp_servers=[],
                model_name=self.config.model,
            )
            return [sentiment_tool]
        except ImportError as e:
            self.logger.warning(f"Sentiment agent not available: {e}")
            return []

    async def _setup_openai_tools(self) -> list[Any]:
        """設定 OpenAI 內建工具 (WebSearch, CodeInterpreter)"""
        tools = []

        # Web Search Tool - 用於搜尋最新市場新聞和資訊
        if self.config.enabled_tools.get("web_search", True):
            try:
                tools.append(WebSearchTool())
                self.logger.debug("Added WebSearchTool")
            except Exception as e:
                self.logger.warning(f"Failed to add WebSearchTool: {e}")

        # Code Interpreter Tool - 用於量化分析和計算
        if self.config.enabled_tools.get("code_interpreter", True):
            try:
                tools.append(CodeInterpreterTool())
                self.logger.debug("Added CodeInterpreterTool")
            except Exception as e:
                self.logger.warning(f"Failed to add CodeInterpreterTool: {e}")

        return tools

    async def _setup_trading_tools(self) -> list[Any]:
        """設定交易驗證和執行工具"""
        tools = []

        # 交易時段檢查工具
        tools.append(
            FunctionTool(
                name="check_market_open",
                description="檢查台灣股市是否開盤中",
                callable=self._check_market_hours,
            )
        )

        # 可用現金查詢工具
        tools.append(
            FunctionTool(
                name="get_available_cash",
                description="獲取當前可用現金餘額",
                callable=lambda: {"available_cash": self._get_available_cash()},
            )
        )

        # 持倉查詢工具
        tools.append(
            FunctionTool(
                name="get_current_holdings",
                description="獲取當前投資組合持倉",
                callable=lambda: {"holdings": self._get_current_holdings()},
            )
        )

        # 策略變更記錄工具
        tools.append(
            FunctionTool(
                name="record_strategy_change",
                description="""記錄投資策略調整。

參數:
- trigger_reason (str): 觸發原因
- new_strategy_addition (str): 新增策略內容
- change_summary (str): 變更摘要
- agent_explanation (str): Agent 解釋

用於記錄 Agent 自主學習和策略調整的過程""",
                callable=self.record_strategy_change,
            )
        )

        return tools

    # ==========================================
    # 市場狀態管理
    # ==========================================

    async def _check_market_hours(self) -> bool:
        """檢查台股交易時間"""
        taiwan_tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(taiwan_tz)

        # 台股交易時間：週一到週五 09:00-13:30
        is_weekday = now.weekday() < 5
        is_trading_time = time(9, 0) <= now.time() <= time(13, 30)

        return is_weekday and is_trading_time

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
    # 特殊功能
    # ==========================================

    async def auto_mode_selection(self) -> AgentMode:
        """自動模式選擇邏輯"""
        current_time = datetime.now(pytz.timezone("Asia/Taipei"))
        market_open = await self._check_market_hours()

        # 基於時間和市場狀態的模式選擇
        if not market_open:
            # 休市時間：觀察或策略檢討
            if current_time.hour >= 18:  # 晚間時間進行策略檢討
                return AgentMode.STRATEGY_REVIEW
            else:
                return AgentMode.OBSERVATION

        # 開盤時間：根據投資組合狀況選擇
        portfolio_value = self._get_available_cash()
        initial_funds = self.config.initial_funds

        # 如果現金比例過高，考慮交易模式
        cash_ratio = portfolio_value / initial_funds
        if cash_ratio > 0.3:  # 現金比例超過 30%
            return AgentMode.TRADING

        # 根據最後執行時間決定是否需要再平衡
        if self.state.last_active_at:
            hours_since_last = (datetime.now() - self.state.last_active_at).total_seconds() / 3600
            if hours_since_last > 24:  # 超過 24 小時未執行
                return AgentMode.REBALANCING

        # 預設為觀察模式
        return AgentMode.OBSERVATION

    async def execute_with_auto_mode(
        self, user_message: str | None = None, context: dict[str, Any] | None = None
    ) -> Any:
        """使用自動模式選擇執行"""
        optimal_mode = await self.auto_mode_selection()

        self.logger.info(f"Auto-selected mode: {optimal_mode}")

        return await self.execute(mode=optimal_mode, user_message=user_message, context=context)

    def __repr__(self) -> str:
        return (
            f"TradingAgent(id={self.agent_id}, "
            f"name='{self.config.name}', "
            f"status={self.state.status}, "
            f"mode={self.state.current_mode}, "
            f"funds=NT${self.config.current_funds or self.config.initial_funds:,.0f})"
        )
