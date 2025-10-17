"""
TradingAgent - 基於 OpenAI Agents SDK 的生產級實作

整合 AgentDatabaseService，提供完整的生命週期管理、
模式驅動執行、錯誤處理和日誌追蹤。
"""

from __future__ import annotations
import os
import logging
from typing import Any
from contextlib import AsyncExitStack
from datetime import datetime

from dotenv import load_dotenv

# 現在可以正常導入 OpenAI Agents SDK
try:
    from agents import (
        Agent,
        ModelSettings,
        Runner,
        gen_trace_id,
        trace,
        Tool,
        WebSearchTool,
        CodeInterpreterTool,
    )
    from agents.mcp import MCPServerStdio
except ImportError as e:
    logging.getLogger(__name__).error(f"Failed to import OpenAI Agents SDK: {e}")
    raise

# 導入所有 sub-agents
from .tools.technical_agent import get_technical_agent
from .tools.sentiment_agent import get_sentiment_agent
from .tools.fundamental_agent import get_fundamental_agent
from .tools.risk_agent import get_risk_agent
from .tools.trading_tools import create_trading_tools

from ..common.enums import AgentStatus, AgentMode
from ..service.agents_service import (
    AgentsService,
    AgentConfigurationError,
    AgentNotFoundError,
    AgentDatabaseError,
)

from ..database.models import Agent as AgentConfig

logger = logging.getLogger(__name__)

load_dotenv()

# 預設配置
DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = os.getenv("DEFAULT_MAX_TURNS", 30)
DEFAULT_AGENT_TIMEOUT = os.getenv("DEFAULT_AGENT_TIMEOUT", 300)  # 秒
DEFAULT_TEMPERATURE = os.getenv("DEFAULT_MODEL_TEMPERATURE", 0.7)

# ==========================================
# Custom Exceptions
# ==========================================


class TradingAgentError(Exception):
    """TradingAgent 基礎錯誤"""

    pass


class AgentInitializationError(TradingAgentError):
    """Agent 初始化錯誤"""

    pass


class AgentExecutionError(TradingAgentError):
    """Agent 執行錯誤"""

    pass


# MCP 伺服器配置
def mcp_server_params(name: str):
    return [
        {
            "command": "uvx",
            "args": [
                "--from",
                "/Users/sacahan/Documents/workspace/CasualMarket",
                "casual-market-mcp",
            ],
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        },
    ]


# ==========================================
# TradingAgent
# ==========================================


class TradingAgent:
    """
    生產級 Trading Agent

    整合資料庫服務、OpenAI Agents SDK、MCP 伺服器，
    提供完整的 Agent 生命週期管理。
    """

    def __init__(
        self,
        agent_id: str,
        agent_config: AgentConfig | None = None,
        agent_service: AgentsService | None = None,
    ):
        """
        初始化 TradingAgent

        Args:
            agent_id: Agent ID
            db_service: 資料庫服務實例

        Note:
            初始化後需要呼叫 initialize() 完成 Agent 設定
        """
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.agent_service = agent_service
        self.agent = None
        self.is_initialized = False
        self._exit_stack = None  # 用於管理 MCP servers 生命週期

        logger.info(f"TradingAgent created: {agent_id}")

    async def initialize(self) -> None:
        """
        初始化 Agent（載入配置、創建 SDK Agent、載入 Sub-agents）

        Raises:
            AgentNotFoundError: Agent 不存在於資料庫
            AgentConfigurationError: 配置錯誤
            AgentInitializationError: 初始化失敗
        """
        # 檢查是否已經初始化，避免重複初始化
        if self.is_initialized:
            logger.debug(f"Agent {self.agent_id} already initialized, skipping...")
            return

        try:
            # 1. 初始化 MCP Servers
            self.mcp_servers = await self._setup_mcp_servers()

            # 2. 初始化 OpenAI Tools
            self.openai_tools = self._setup_openai_tools()

            # 3. 初始化 Trading Tools
            self.trading_tools = self._setup_trading_tools()

            # 4. 載入 Sub-agents (從 tools/ 目錄，傳入共享配置)
            self.subagent_tools = await self._load_subagents_as_tools()

            # 5. 合併所有 tools
            all_tools = self.openai_tools + self.trading_tools + self.subagent_tools

            # 6. 創建 OpenAI Agent
            self.agent = Agent(
                name=self.agent_id,
                model=self.agent_config.ai_model or DEFAULT_MODEL,
                instructions=self._build_instructions(self.agent_config.description),
                tools=all_tools,
                mcp_servers=self.mcp_servers,
                model_settings=ModelSettings(
                    temperature=DEFAULT_TEMPERATURE,
                    tool_choice="required",
                ),
                max_turns=DEFAULT_MAX_TURNS,
            )

            self.is_initialized = True
            logger.info(
                f"Agent initialized successfully: {self.agent_id} "
                f"(model: {self.agent_config.ai_model})"
            )

        except (AgentNotFoundError, AgentConfigurationError):
            raise
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_id}: {e}", exc_info=True)
            raise AgentInitializationError(f"Agent initialization failed: {str(e)}")

    async def _setup_mcp_servers(self) -> list[MCPServerStdio]:
        """
        初始化 MCP 伺服器列表

        Returns:
            MCP 伺服器實例列表

        Note:
            未來可以根據 Agent 配置動態載入不同的 MCP 伺服器
        """
        servers = []
        try:
            # 創建並保存 AsyncExitStack 實例以管理 MCP servers 生命週期
            self._exit_stack = AsyncExitStack()

            # 初始化 MCP servers 並註冊到 exit stack
            for params in mcp_server_params(self.agent_id):
                server = await self._exit_stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=DEFAULT_AGENT_TIMEOUT)
                )
                servers.append(server)

            logger.debug(f"{len(servers)} MCP servers initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize MCP server: {e}")
            # 如果初始化失敗，清理已創建的資源
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None

        return servers

    def _setup_openai_tools(self) -> list[Any]:
        """設置 OpenAI 內建工具（根據資料庫配置）"""
        tools = [WebSearchTool(), CodeInterpreterTool(container={"type": "auto"})]

        return tools

    def _setup_trading_tools(self) -> list[Tool]:
        """設置交易相關工具"""
        return create_trading_tools(self.agent_service, self.agent_id)

    async def _load_subagents_as_tools(self) -> list[Tool]:
        """載入 Sub-agents (從 tools/ 目錄，根據資料庫配置）"""
        subagents = []

        try:
            # 統一的 subagent 配置參數
            subagent_config = {
                "model_name": self.agent_config.ai_model or DEFAULT_MODEL,  # 從資料庫載入
                "mcp_servers": self.mcp_servers,  # 傳入相同的 MCP servers
                "openai_tools": self.openai_tools,  # 傳入相同的 OpenAI tools
                "max_turns": DEFAULT_MAX_TURNS,
            }

            # 生成所有 Sub-agents
            try:
                technical_agent = await get_technical_agent(**subagent_config)
                subagents.append(technical_agent)
                logger.info("技術分析 agent 載入成功")
            except Exception as e:
                logger.warning(f"技術分析 agent 載入失敗: {e}")

            try:
                sentiment_agent = await get_sentiment_agent(**subagent_config)
                subagents.append(sentiment_agent)
                logger.info("情緒分析 agent 載入成功")
            except Exception as e:
                logger.warning(f"情緒分析 agent 載入失敗: {e}")

            try:
                fundamental_agent = await get_fundamental_agent(**subagent_config)
                subagents.append(fundamental_agent)
                logger.info("基本面分析 agent 載入成功")
            except Exception as e:
                logger.warning(f"基本面分析 agent 載入失敗: {e}")

            try:
                risk_agent = await get_risk_agent(**subagent_config)
                subagents.append(risk_agent)
                logger.info("風險評估 agent 載入成功")
            except Exception as e:
                logger.warning(f"風險評估 agent 載入失敗: {e}")

        except Exception as e:
            logger.error(f"載入 sub-agents 時發生錯誤: {e}")

        # 將 Sub-agents 包裝為工具
        return [agent.as_tool() for agent in subagents]

    async def run(
        self,
        mode: AgentMode | None = None,
        agent_config: Agent | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        執行 Agent 任務

        Args:
            mode: 執行模式
            agent_config: Agent 配置
            context: 額外上下文（可選）

        Returns:
            執行結果字典：
            {
                "success": bool,
                "output": str,
                "trace_id": str,
                "mode": str,
                "error": str (如果失敗)
            }

        Raises:
            AgentInitializationError: Agent 未初始化
            AgentExecutionError: 執行失敗
        """
        if not self.is_initialized:
            raise AgentInitializationError(
                f"Agent {self.agent_id} not initialized. Call initialize() first."
            )

        # 使用預設模式或指定模式
        execution_mode = mode or (
            self.agent_config.current_mode if self.agent_config else AgentMode.OBSERVATION
        )

        logger.info(
            f"Starting agent execution: {self.agent_id} "
            f"(mode: {execution_mode.value if execution_mode else 'unknown'})"
        )

        try:
            # 更新資料庫狀態為執行中
            await self.agent_service.update_agent_status(
                self.agent_id, AgentStatus.ACTIVE, execution_mode
            )

            # 生成 trace ID 並執行
            trace_id = gen_trace_id()
            with trace(workflow_name=f"TradingAgent-{self.agent_id}", trace_id=trace_id):
                # 構建任務提示（可以根據 mode 調整）
                task_prompt = self._build_task_prompt(execution_mode, context)

                # 執行 Agent
                result = await Runner.run(self.agent, task_prompt, max_turns=DEFAULT_MAX_TURNS)

                logger.info(
                    f"Agent {self.agent_id} execution completed: {result} (trace_id: {trace_id})"
                )

                return {
                    "success": True,
                    "output": result.final_output,
                    "used_turns": result.current_turn,
                    "trace_id": trace_id,
                    "mode": execution_mode.value if execution_mode else "unknown",
                }

        except Exception as e:
            logger.error(f"Agent execution failed: {self.agent_id}: {e}", exc_info=True)

            # 更新狀態為錯誤
            try:
                await self.agent_service.update_agent_status(self.agent_id, AgentStatus.ERROR)
            except Exception as status_error:
                logger.error(f"Failed to update error status: {status_error}")

            raise AgentExecutionError(f"Agent execution failed: {str(e)}")

    def _build_instructions(self, description: str) -> str:
        """
        根據描述構建 Agent 指令
        Args:
            description: Agent 基本描述

        Returns:
            Agent 指令
        """

        # 基本描述
        instructions_parts = [
            f"你是一個專業的股票交易 Agent，你的代號是 {self.agent_id}。",
            "你的基本描述如下：",
            f"{description}",
        ]

        # 投資偏好設定（如果有的話）
        if self.agent_config.investment_preferences:
            instructions_parts.extend(
                [
                    "你偏好以下的股票代號：",
                    f"{self.agent_config.investment_preferences}",
                ]
            )

        # 持股比例限制
        if self.agent_config.max_position_per_stock:
            instructions_parts.extend(
                [
                    f"你對於每一隻股票的最大持股比例為 {self.agent_config.max_position_per_stock}%。",
                ]
            )

        instructions = (
            "\n".join(instructions_parts)
            + """
請根據以上描述作為你的根本指導。

你可以使用各種工具來幫助你完成任務，包括：

**🌐 OpenAI 內建工具：**
• 網路搜尋 (WebSearchTool) - 獲取最新市場資訊、新聞、產業動態
• 程式碼執行 (CodeInterpreterTool) - 進行複雜的數據計算、統計分析、圖表繪製

**📊 台灣股市數據工具 (Casual Market MCP)：**
• get_taiwan_stock_price(symbol) - 查詢台灣股票即時價格、漲跌幅、成交量
• get_market_index_info(category, count, format) - 取得市場指數資訊（加權指數、類股指數等）
• get_market_historical_index() - 查詢歷史指數資料，進行技術分析與回測
• check_taiwan_trading_day(date) - 檢查是否為交易日，避免在休市日執行交易
• get_taiwan_holiday_info(date) - 取得節假日資訊
• get_foreign_investment_by_industry() - 查詢外資各產業持股狀況
• get_top_foreign_holdings() - 取得外資持股前20名
• get_dividend_rights_schedule(symbol) - 查詢除權息行事曆
• get_etf_regular_investment_ranking() - 取得ETF定期定額排名
• buy_taiwan_stock(symbol, quantity, price) - 模擬買入台灣股票
• sell_taiwan_stock(symbol, quantity, price) - 模擬賣出台灣股票

**💰 投資組合管理工具：**
• get_portfolio_status() - 查詢當前投資組合狀態，包括現金餘額、持股明細、總資產價值、資產配置比例
• record_trade(symbol, action, quantity, price, decision_reason, company_name) - 記錄交易到資料庫，自動更新持股、資金和績效指標

**🧠 持久記憶工具 (Memory MCP)：**
• 使用記憶工具儲存和回想：
    - 市場分析結果和趨勢判斷
    - 技術指標計算和圖表分析
    - 基本面研究和公司評估
    - 風險評估和投資決策邏輯
    - 過往交易經驗和教訓
• 你的記憶會在不同執行週期間保持，請善用此能力累積知識

**🤖 專業分析 Sub-Agents：**
• technical_agent - 技術分析專家
    - 進行技術指標分析（MA, RSI, MACD, KD, 布林帶等）
    - 識別圖表型態和趨勢
    - 提供買賣點建議

• sentiment_agent - 情緒分析專家
    - 分析市場情緒和投資人心理
    - 追蹤社交媒體和新聞輿論
    - 評估市場氛圍對股價的影響

• fundamental_agent - 基本面分析專家
    - 研究公司財務報表和營運狀況
    - 評估本益比、股價淨值比等估值指標
    - 分析產業競爭力和成長潛力

• risk_agent - 風險評估專家
    - 評估投資風險和波動性
    - 計算風險調整後報酬
    - 提供資產配置和避險建議

**⚠️ 重要執行原則：**
1. 決策前必須先使用投資組合管理工具了解資產狀況
2. 充分利用專業分析 Sub-Agents 的能力，做出全面評估
3. 善用持久記憶工具累積知識和經驗
4. 每筆交易都要詳細記錄決策理由
5. 決策理由應包含：分析過程、市場判斷、風險考量、Sub-Agents 建議
6. 注意交易日檢查，避免在休市日執行操作
7. 最終目標是最大化投資回報，同時嚴格控制風險

請始終保持理性、謹慎，運用所有可用工具做出明智的投資決策。
        """
        )
        logger.info(f"Instructions for {self.agent_id}: {instructions.strip()}")

        return instructions.strip()

    def _build_task_prompt(self, mode: AgentMode, context: dict[str, Any] | None) -> str:
        """
        根據執行模式構建任務提示

        Args:
            mode: 執行模式
            context: 額外上下文

        Returns:
            完整的任務提示
        """

        # 根據模式添加指導
        task_prompts = {
            AgentMode.TRADING: """
**🎯 交易執行模式 (TRADING MODE)**

目的：分析市場機會並執行交易。

可用工具：
• OpenAI 內建工具 - 網路搜尋、程式碼執行
• 台灣股市數據工具 (Casual Market MCP) - 市場指數、股票價格、資金流向、除權息資訊、交易日檢查、買賣交易
• 投資組合管理工具 - 查詢投資組合狀態、記錄交易決策
• 持久記憶工具 (Memory MCP) - 儲存和回想分析結論
• 專業分析 Sub-Agents - 技術分析、基本面分析、情緒分析、風險評估

限制：
• 必須有充分的分析支持才能執行交易
• 遵守最大持股比例限制
• 交易後必須記錄決策理由
• 將分析過程利用持久記憶工具存入知識庫供下次參考
""",
            AgentMode.REBALANCING: """
**⚖️ 投資組合重新平衡模式 (REBALANCING MODE)**

目的：檢視投資組合並根據策略進行重新平衡調整。

可用工具：
• OpenAI 內建工具 - 網路搜尋、程式碼執行
• 台灣股市數據工具 (Casual Market MCP) - 市場指數、股票價格、資金流向、除權息資訊、買賣交易
• 投資組合管理工具 - 查詢投資組合狀態、記錄調整決策
• 持久記憶工具 (Memory MCP) - 儲存和回想平衡分析
• 專業分析 Sub-Agents - 技術分析、基本面分析、情緒分析、風險評估

限制：
• 焦點在現有持股調整，不需要識別新的投資機會
• 調整應符合投資策略和偏好設定
• 考量交易成本和稅務影響
• 調整理由利用持久記憶工具存入知識庫累積詳細記錄
""",
            AgentMode.OBSERVATION: """
**🔍 市場觀察與機會發掘模式 (OBSERVATION MODE)**

目的：研究市場機會並識別符合投資策略的潛在標的。

可用工具：
• OpenAI 內建工具 - 網路搜尋、程式碼執行
• 台灣股市數據工具 (Casual Market MCP) - 市場指數、歷史數據、資金動向、熱門標的、股票資訊
• 投資組合管理工具 - 查詢投資組合以評估相關性
• 持久記憶工具 (Memory MCP) - 儲存機會分析和投資線索
• 專業分析 Sub-Agents - 技術分析、基本面分析、情緒分析、風險評估

限制：
• 本模式不執行交易，僅識別和研究機會
• 評估標的應考量與投資策略的一致性
• 記錄分析過程和進場條件供未來參考
• 利用持久記憶工具累積知識庫
""",
        }

        return (
            task_prompts[mode]
            + f"\n\n目前的日期時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    async def stop(self) -> None:
        """
        停止 Agent 執行

        Note:
            OpenAI Agents SDK 當前不支援中途停止，
            此方法主要用於更新資料庫狀態
        """
        # 暫時跳過資料庫操作
        try:
            await self.agent_service.update_agent_status(self.agent_id, AgentStatus.INACTIVE)
            logger.info(f"Agent stopped: {self.agent_id}")
        except AgentDatabaseError as e:
            logger.error(f"Failed to update agent status on stop: {e}")
        logger.info(f"Agent stopped: {self.agent_id}")

    async def cleanup(self) -> None:
        """
        清理 Agent 資源，包括關閉 MCP servers
        """
        try:
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None
                logger.info(f"MCP servers closed for agent: {self.agent_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup MCP servers: {e}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """支持 async context manager - 自動清理資源"""
        await self.cleanup()

    async def get_status(self) -> dict[str, Any]:
        """
        取得 Agent 狀態資訊

        Returns:
            狀態資訊字典
        """
        if not self.agent_config:
            return {
                "agent_id": self.agent_id,
                "initialized": False,
                "status": "not_loaded",
            }

        return {
            "agent_id": self.agent_id,
            "name": getattr(self.agent_config, "name", self.agent_id),
            "initialized": self.is_initialized,
            "status": getattr(self.agent_config, "status", "unknown"),
            "mode": getattr(self.agent_config, "current_mode", "unknown"),
            "model": self.agent_config.ai_model,
        }

    def __repr__(self) -> str:
        """字串表示"""
        status = "initialized" if self.is_initialized else "not initialized"
        return f"<TradingAgent {self.agent_id} ({status})>"
