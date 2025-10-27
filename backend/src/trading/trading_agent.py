"""
TradingAgent - 基於 OpenAI Agents SDK 的生產級實作

整合 AgentDatabaseService，提供完整的生命週期管理、
模式驅動執行、錯誤處理和日誌追蹤。
"""

from __future__ import annotations
import os
from typing import Any
from contextlib import AsyncExitStack
from datetime import datetime

from dotenv import load_dotenv

# 導入 OpenAI Agents SDK
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

# 導入所有 sub-agents
from .tools.technical_agent import get_technical_agent
from .tools.sentiment_agent import get_sentiment_agent
from .tools.fundamental_agent import get_fundamental_agent
from .tools.risk_agent import get_risk_agent
from .tools.trading_tools import create_trading_tools, get_portfolio_status

from common.enums import AgentStatus, AgentMode
from common.logger import logger
from common.agent_utils import save_agent_graph
from service.agents_service import (
    AgentsService,
    AgentConfigurationError,
    AgentNotFoundError,
    AgentDatabaseError,
)
from agents.extensions.models.litellm_model import LitellmModel

from database.models import Agent as AgentConfig

load_dotenv()

# 預設配置
DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = int(os.getenv("DEFAULT_MAX_TURNS", "30"))
DEFAULT_AGENT_TIMEOUT = int(os.getenv("DEFAULT_AGENT_TIMEOUT", "300"))  # 秒
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_MODEL_TEMPERATURE", 0.7))

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
            agent_config: Agent 配置
            agent_service: Agent 服務實例

        Note:
            初始化後需要呼叫 initialize() 完成 Agent 設定
        """
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.agent_service = agent_service
        self.agent = None
        self.is_initialized = False
        self._exit_stack = (
            AsyncExitStack()
        )  # 創建並保存 AsyncExitStack 實例以管理 MCP servers 生命週期
        self.casual_market_mcp = None
        self.memory_mcp = None

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

        # 檢查 agent_config 是否已設置
        if not self.agent_config:
            raise AgentConfigurationError(
                f"Agent config must be set before initialization for {self.agent_id}"
            )

        try:
            # 1. 初始化 MCP Servers
            await self._setup_mcp_servers()

            # 2. 初始化 OpenAI Tools
            self.openai_tools = self._setup_openai_tools()

            # 3. 初始化 Trading Tools
            self.trading_tools = self._setup_trading_tools()

            # 4. 載入 Sub-agents (從 tools/ 目錄，傳入共享配置)
            self.subagent_tools = await self._load_subagents_as_tools()

            # 5. 合併所有 tools (不包括 OpenAI 內建工具)
            all_tools = self.trading_tools + self.subagent_tools

            # 6. 創建 LiteLLM 模型
            llm_model = await self._create_llm_model()

            # 7. 獲取 LLM 提供商（從 ai_model_configs 查詢）
            model_config = await self.agent_service.get_ai_model_config(self.agent_config.ai_model)
            provider = model_config.get("provider", "openai") if model_config else "openai"

            # 8. 設定 GitHub Copilot 的 ModelSettings（headers 必須在此層級設置）
            extra_headers = {}
            if provider and provider.lower() == "GitHub Copilot".lower():
                extra_headers = {
                    "editor-version": "vscode/1.85.1",
                    "Copilot-Integration-Id": "vscode-chat",
                }
                logger.info(f"Configuring GitHub Copilot headers for agent: {self.agent_id}")

            # 9. 創建 OpenAI Agent（使用 LiteLLM 模型）
            self.agent = Agent(
                name=self.agent_id,
                model=llm_model,
                instructions=self._build_instructions(self.agent_config.description),
                tools=all_tools,
                mcp_servers=[self.memory_mcp],
                model_settings=ModelSettings(
                    tool_choice="required",
                    extra_headers=extra_headers if extra_headers else None,
                    include_usage=True,  # 追蹤使用數據
                ),
            )

            # 10. 繪製 Agent 結構圖
            # save_agent_graph(
            #     agent=self.agent,
            #     agent_id=self.agent_id,
            #     output_dir=None,  # 使用預設的 backend/logs 目錄
            # )

            self.is_initialized = True
            logger.info(
                f"Agent initialized successfully: {self.agent_id} "
                f"(model: {self.agent_config.ai_model}, provider: {provider})"
            )

        except (AgentNotFoundError, AgentConfigurationError):
            raise
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_id}: {e}", exc_info=True)
            raise AgentInitializationError(f"Agent initialization failed: {str(e)}")

    async def _setup_mcp_servers(self):
        """
        初始化 MCP 伺服器並註冊到 exit stack

        Raises:
            Exception: 初始化失敗
        """
        try:
            # 初始化 MCP servers 並註冊到 exit stack
            self.casual_market_mcp = await self._exit_stack.enter_async_context(
                MCPServerStdio(
                    name="casual_market_mcp",
                    params={
                        "command": "uvx",
                        "args": [
                            "--from",
                            "/Users/sacahan/Documents/workspace/CasualMarket",
                            "casual-market-mcp",
                        ],
                    },
                    client_session_timeout_seconds=DEFAULT_AGENT_TIMEOUT,
                )
            )
            logger.debug("casual_market_mcp server initialized")

            # 構建絕對路徑以確保資料庫文件位置正確
            memory_db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "memory",
                f"{self.agent_id}.db",
            )
            # 確保 memory 目錄存在
            os.makedirs(os.path.dirname(memory_db_path), exist_ok=True)

            self.memory_mcp = await self._exit_stack.enter_async_context(
                MCPServerStdio(
                    name="memory_mcp",
                    params={
                        "command": "npx",
                        "args": ["-y", "mcp-memory-libsql"],
                        "env": {"LIBSQL_URL": f"file:{memory_db_path}"},
                    },
                    client_session_timeout_seconds=DEFAULT_AGENT_TIMEOUT,
                )
            )
            logger.debug(f"memory_mcp server initialized (db: {memory_db_path})")

        except Exception as e:
            logger.warning(f"Failed to initialize MCP server: {e}")
            # 如果初始化失敗，清理已創建的資源
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None

    async def _create_llm_model(self) -> LitellmModel:
        """
        創建 LiteLLM 模型，使用 ai_model_configs 表配置

        所有提供商和模型配置必須在 ai_model_configs 表中定義。
        不支持 fallback - 配置缺失會立即失敗，便於及早發現問題。

        Returns:
            LitellmModel 實例

        Raises:
            AgentConfigurationError: 如果模型配置或 API 密鑰未設置
        """
        if not self.agent_config.ai_model:
            raise AgentConfigurationError(f"Agent {self.agent_id} has no ai_model configured")

        model_name = self.agent_config.ai_model

        # 必須從 ai_model_configs 表查詢完整的模型配置
        if not self.agent_service:
            raise AgentConfigurationError("Cannot create LLM model: agent_service not available")

        model_config = await self.agent_service.get_ai_model_config(model_name)

        if not model_config:
            raise AgentConfigurationError(
                f"Model '{model_name}' not found in ai_model_configs table or not enabled. "
                f"Please configure the model in the database."
            )

        # 從配置中獲取必要的欄位
        litellm_prefix = model_config.get("litellm_prefix")
        model_key = model_config.get("model_key")
        api_key_env_var = model_config.get("api_key_env_var")
        provider = model_config.get("provider")

        if not litellm_prefix or not model_key or not api_key_env_var:
            raise AgentConfigurationError(
                f"Model '{model_name}' configuration incomplete in ai_model_configs table. "
                f"Required fields: litellm_prefix, model_key, api_key_env_var. "
                f"Got: litellm_prefix={litellm_prefix}, model_key={model_key}, "
                f"api_key_env_var={api_key_env_var}"
            )

        # 從環境變數讀取 API 密鑰
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            raise AgentConfigurationError(
                f"API key for provider '{provider}' not set. "
                f"Set environment variable: {api_key_env_var}"
            )

        # 構建完整的 LiteLLM 模型字符串
        model_str = f"{litellm_prefix}{model_key}"

        logger.info(
            f"Creating LiteLLM model: {model_str} "
            f"(provider: {provider}, api_key_env: {api_key_env_var})"
        )

        # 返回 LitellmModel - headers 將通過 ModelSettings 傳遞
        return LitellmModel(model=model_str, api_key=api_key)

    def _setup_openai_tools(self) -> list[Any]:
        """設置 OpenAI 內建工具（根據資料庫配置）"""
        # ✅ 正確配置方式（基於測試驗證）

        # WebSearchTool: 提供網路搜尋功能
        web_search_tool = WebSearchTool(
            user_location=None,  # 可選：用戶位置，用於本地化搜尋結果
            filters=None,  # 可選：搜尋過濾器
            search_context_size="medium",  # 搜尋上下文大小：'low'、'medium'、'high'
        )

        # CodeInterpreterTool: 提供程式碼執行功能
        # 必須指定 type 和 container 設置，container.type 必須為 "auto"
        code_interpreter_tool = CodeInterpreterTool(
            tool_config={
                "type": "code_interpreter",
                "container": {
                    "type": "auto"  # OpenAI 自動選擇最適合的容器
                },
            }
        )

        tools = [web_search_tool, code_interpreter_tool]
        logger.debug(
            "OpenAI tools configured: WebSearchTool(context=medium), CodeInterpreterTool(container=auto)"
        )

        return tools

    def _setup_trading_tools(self) -> list[Tool]:
        """設置交易相關工具"""

        return create_trading_tools(
            self.agent_service, self.agent_id, casual_market_mcp=self.casual_market_mcp
        )

    async def _load_subagents_as_tools(self) -> list[Tool]:
        """載入 Sub-agents (從 tools/ 目錄，根據資料庫配置）"""
        tools = []

        try:
            # 統一的 subagent 配置參數
            subagent_config = {
                "model_name": self.agent_config.ai_model or DEFAULT_MODEL,  # 從資料庫載入
                "mcp_servers": [
                    self.memory_mcp,
                    self.casual_market_mcp,
                ],  # 提供 持久記憶 和 市場數據 MCP
                "openai_tools": self.openai_tools,  # 傳入相同的 OpenAI tools
            }

            logger.debug(
                f"Loading subagents with config: model={subagent_config['model_name']}, "
                f"mcp_servers={len(subagent_config['mcp_servers'])} available"
            )

            # 生成所有 Sub-agents
            try:
                technical_agent = await get_technical_agent(**subagent_config)
                if technical_agent:
                    tool = technical_agent.as_tool(
                        tool_name="technical_analyst",
                        tool_description="""
• 技術分析專家
    - 進行技術指標分析（MA, RSI, MACD, KD, 布林帶等）
    - 識別圖表型態和趨勢
    - 提供買賣點建議
                        """,
                        max_turns=DEFAULT_MAX_TURNS,
                    )
                    if tool:
                        tools.append(tool)
                        logger.info("技術分析 Sub Agent Tool 載入成功")
                    else:
                        logger.error("技術分析 agent.as_tool() 返回 None")

                    # 繪製 Sub-Agent 圖形
                    save_agent_graph(technical_agent, "technical_agent", None)
                else:
                    logger.error("get_technical_agent() 返回 None")
            except Exception as e:
                logger.warning(f"技術分析 agent 載入失敗: {e}", exc_info=True)

            try:
                sentiment_agent = await get_sentiment_agent(**subagent_config)
                if sentiment_agent:
                    tool = sentiment_agent.as_tool(
                        tool_name="sentiment_analyst",
                        tool_description="""
• 情緒分析專家
    - 分析市場情緒和投資人心理
    - 追蹤社交媒體和新聞輿論
    - 評估市場氛圍對股價的影響
                            """,
                        max_turns=DEFAULT_MAX_TURNS,
                    )
                    if tool:
                        tools.append(tool)
                        logger.info("情緒分析 Sub Agent Tool 載入成功")
                    else:
                        logger.error("情緒分析 agent.as_tool() 返回 None")

                    # 繪製 Sub-Agent 圖形
                    save_agent_graph(sentiment_agent, "sentiment_agent", None)
                else:
                    logger.error("get_sentiment_agent() 返回 None")
            except Exception as e:
                logger.warning(f"情緒分析 agent 載入失敗: {e}", exc_info=True)

            try:
                fundamental_agent = await get_fundamental_agent(**subagent_config)
                if fundamental_agent:
                    tool = fundamental_agent.as_tool(
                        tool_name="fundamental_analyst",
                        tool_description="""
• 基本面分析專家
    - 研究公司財務報表和營運狀況
    - 評估本益比、股價淨值比等估值指標
    - 分析產業競爭力和成長潛力
                            """,
                        max_turns=DEFAULT_MAX_TURNS,
                    )
                    if tool:
                        tools.append(tool)
                        logger.info("基本面分析 Sub Agent Tool 載入成功")
                    else:
                        logger.error("基本面分析 agent.as_tool() 返回 None")

                    # 繪製 Sub-Agent 圖形
                    save_agent_graph(fundamental_agent, "fundamental_agent", None)
                else:
                    logger.error("get_fundamental_agent() 返回 None")
            except Exception as e:
                logger.warning(f"基本面分析 agent 載入失敗: {e}", exc_info=True)

            try:
                risk_agent = await get_risk_agent(**subagent_config)
                if risk_agent:
                    tool = risk_agent.as_tool(
                        tool_name="risk_analyst",
                        tool_description="""
• 風險評估專家
    - 評估投資風險和波動性
    - 計算風險調整後報酬
    - 提供資產配置和避險建議
                            """,
                        max_turns=DEFAULT_MAX_TURNS,
                    )
                    if tool:
                        tools.append(tool)
                        logger.info("風險評估 Sub Agent Tool 載入成功")
                    else:
                        logger.error("風險評估 agent.as_tool() 返回 None")

                    # 繪製 Sub-Agent 圖形
                    save_agent_graph(risk_agent, "risk_agent", None)
                else:
                    logger.error("get_risk_agent() 返回 None")
            except Exception as e:
                logger.warning(f"風險評估 agent 載入失敗: {e}", exc_info=True)

            try:
                sentiment_agent = await get_sentiment_agent(**subagent_config)
                if sentiment_agent:
                    tools.append(
                        sentiment_agent.as_tool(
                            tool_name="sentiment_analyst",
                            tool_description="""
• 情緒分析專家
    - 分析市場情緒和投資人心理
    - 追蹤社交媒體和新聞輿論
    - 評估市場氛圍對股價的影響
                            """,
                            max_turns=DEFAULT_MAX_TURNS,
                        )
                    )
                    logger.info("情緒分析 Sub Agent Tool 載入成功")
                else:
                    logger.warning("情緒分析 agent 返回 None")
            except Exception as e:
                logger.warning(f"情緒分析 agent 載入失敗: {e}")

            try:
                fundamental_agent = await get_fundamental_agent(**subagent_config)
                if fundamental_agent:
                    tools.append(
                        fundamental_agent.as_tool(
                            tool_name="fundamental_analyst",
                            tool_description="""
• 基本面分析專家
    - 研究公司財務報表和營運狀況
    - 評估本益比、股價淨值比等估值指標
    - 分析產業競爭力和成長潛力
                            """,
                            max_turns=DEFAULT_MAX_TURNS,
                        )
                    )
                    logger.info("基本面分析 Sub Agent Tool 載入成功")
                else:
                    logger.warning("基本面分析 agent 返回 None")
            except Exception as e:
                logger.warning(f"基本面分析 agent 載入失敗: {e}")

            try:
                risk_agent = await get_risk_agent(**subagent_config)
                if risk_agent:
                    tools.append(
                        risk_agent.as_tool(
                            tool_name="risk_analyst",
                            tool_description="""
• 風險評估專家
    - 評估投資風險和波動性
    - 計算風險調整後報酬
    - 提供資產配置和避險建議
                            """,
                            max_turns=DEFAULT_MAX_TURNS,
                        )
                    )
                    logger.info("風險評估 Sub Agent Tool 載入成功")
                else:
                    logger.warning("風險評估 agent 返回 None")
            except Exception as e:
                logger.warning(f"風險評估 agent 載入失敗: {e}")

        except Exception as e:
            logger.error(f"載入 sub-agents 時發生錯誤: {e}")

        return tools

    async def run(
        self,
        mode: AgentMode | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        執行 Agent 任務

        Args:
            mode: 執行模式
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

        if not self.agent_config:
            raise AgentConfigurationError(f"Agent config not set for {self.agent_id}")

        # 使用預設模式或指定模式
        execution_mode = mode or self.agent_config.current_mode or AgentMode.OBSERVATION

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
                task_prompt = await self._build_task_prompt(execution_mode, context)

                # 執行 Agent
                result = await Runner.run(self.agent, task_prompt, max_turns=DEFAULT_MAX_TURNS)

                logger.info(
                    f"*** Agent {self.agent_id} execution completed: {result} (trace_id: {trace_id}) ***"
                )

                return {
                    "success": True,
                    "output": result.final_output,
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
            "你的投資主張如下：",
            f"{description}",
        ]

        # 投資偏好設定（如果有的話）
        if self.agent_config.investment_preferences:
            instructions_parts.extend(
                [
                    f"你對這些這些公司特別感興趣（股票代號）：{self.agent_config.investment_preferences}。",
                ]
            )

        # 持股比例限制
        if self.agent_config.max_position_size:
            instructions_parts.extend(
                [
                    f"無論你多麼看好特定公司，你對於每一隻股票的最大持股比例最多為 {self.agent_config.max_position_size}%。",
                ]
            )

        instructions = (
            "\n".join(instructions_parts)
            + """
請根據以上描述作為你的根本指導。

**⚠️ 重要執行原則：**
1. 你應該使用各種工具來幫助你完成任務：
    - 決策前必須先使用投資組合管理工具了解資產狀況
    - 充分利用專業分析 Sub-Agents 的能力，做出全面評估
    - 主動使用持久記憶工具(memory_mcp)累積知識和經驗
2. 每筆交易都要詳細記錄決策理由
3. 決策理由應包含：分析過程、市場判斷、風險考量、Sub-Agents 建議
4. 注意交易日檢查，避免在休市日執行操作
5. 最終目標是最大化投資回報，同時嚴格控制風險

請始終保持理性、謹慎，運用所有可用工具做出明智的投資決策。
        """
        )
        logger.info(f"Instructions for {self.agent_id}: {instructions.strip()}")

        return instructions.strip()

    async def _build_task_prompt(self, mode: AgentMode, context: dict[str, Any] | None) -> str:
        """
        根據執行模式構建任務提示

        Args:
            mode: 執行模式
            context: 額外上下文

        Returns:
            完整的任務提示
        """

        # 獲取投資組合狀態（現在使用 await）
        portfolio_status = await get_portfolio_status(self.agent_service, self.agent_id)

        # 根據模式添加指導
        task_prompts = {
            AgentMode.TRADING: f"""
**🎯 交易執行模式 (TRADING MODE)**

目的：分析市場機會並執行交易。

---
{portfolio_status}
---

可用工具：
• 投資組合管理工具 (record_trade_tool、get_portfolio_status_tool) - 查詢投資組合狀態、記錄交易決策
• 模擬交易工具 (buy_taiwan_stock_tool、sell_taiwan_stock_tool) - 執行台灣股票模擬買賣交易
• memory_mcp (持久記憶工具) - 儲存和回想分析結論
• 專業分析 Sub-Agents - technical_analyst、fundamental_analyst、sentiment_analyst、risk_analyst

限制：
• 必須有充分的分析支持才能執行交易
• 遵守最大持股比例限制
• 交易後必須記錄決策理由
• 主動將決策過程利用 memory_mcp 存入知識庫以供未來參考
""",
            AgentMode.REBALANCING: f"""
**⚖️ 投資組合重新平衡模式 (REBALANCING MODE)**

目的：檢視投資組合並根據策略進行重新平衡調整。

---
{portfolio_status}
---

可用工具：
• 投資組合管理工具 (record_trade_tool、get_portfolio_status_tool) - 查詢投資組合狀態、記錄交易決策
• 模擬交易工具 (buy_taiwan_stock_tool、sell_taiwan_stock_tool) - 執行台灣股票模擬買賣交易
• memory_mcp (持久記憶工具) - 儲存和回想分析結論
• 專業分析 Sub-Agents - technical_analyst、fundamental_analyst、sentiment_analyst、risk_analyst

限制：
• 焦點在現有持股調整，不需要識別新的投資機會
• 調整應符合投資策略和偏好設定
• 考量交易成本和稅務影響
• 主動將調整理由利用 memory_mcp 存入知識庫以供未來參考
""",
            AgentMode.OBSERVATION: f"""
**🔍 市場觀察與機會發掘模式 (OBSERVATION MODE)**

目的：研究市場機會並識別符合投資策略的潛在標的。

---
{portfolio_status}
---

可用工具：
• 投資組合管理工具 (record_trade_tool、get_portfolio_status_tool) - 查詢投資組合狀態、記錄交易決策
• memory_mcp (持久記憶工具) - 儲存和回想分析結論
• 專業分析 Sub-Agents - technical_analyst、fundamental_analyst、sentiment_analyst、risk_analyst

限制：
• 本模式不執行交易，僅識別和研究機會
• 識別新的投資機會必須排除已經買入的標的
• 評估投資標的應該保持與投資主張的一致性
• 主動將分析過程和進場條件利用 memory_mcp 存入知識庫以供未來參考
""",
        }

        action_message = (
            task_prompts[mode]
            + f"\n\n目前的日期時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info(f"Action message for {self.agent_id}: {action_message.strip()}")
        return action_message.strip()

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
