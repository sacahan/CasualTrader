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
    set_tracing_export_api_key,
)
from agents.mcp import MCPServerStdio

# 導入所有 sub-agents
from .tools.technical_agent import get_technical_agent
from .tools.sentiment_agent import get_sentiment_agent
from .tools.fundamental_agent import get_fundamental_agent
from .tools.risk_agent import get_risk_agent
from .tools.trading_tools import create_trading_tools, get_portfolio_status
from .tools.memory_tools import (
    load_execution_memory,
    save_execution_memory,
)

from common.enums import AgentStatus, AgentMode, validate_agent_mode
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
from .tool_config import ToolConfig, ToolRequirements

load_dotenv()

# 預設配置
DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = int(os.getenv("DEFAULT_MAX_TURNS", "30"))
DEFAULT_AGENT_TIMEOUT = int(os.getenv("DEFAULT_AGENT_TIMEOUT", "300"))  # 秒
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_MODEL_TEMPERATURE", 0.7))

# 設置追蹤 API 金鑰（用於監控和日誌）
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

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
        self.llm_model = None
        self.extra_headers = None
        self.agent = None
        self.is_initialized = False
        self._exit_stack = (
            AsyncExitStack()
        )  # 創建並保存 AsyncExitStack 實例以管理 MCP servers 生命週期
        self.casual_market_mcp = None
        self.memory_mcp = None
        self.tavily_mcp = None

        logger.info(f"TradingAgent created: {agent_id}")

    async def initialize(self, mode: AgentMode | None = None) -> None:
        """
        初始化 Agent（載入配置、創建 SDK Agent、載入 Sub-agents）

        Args:
            mode: Agent 執行模式。若為 None，使用 agent_config.current_mode

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

        # 確定執行模式（容錯：資料庫可能儲存為字串）
        execution_mode = self._normalize_agent_mode(
            mode or getattr(self.agent_config, "current_mode", None) or AgentMode.TRADING
        )

        try:
            # 獲取該模式的工具配置
            tool_requirements = ToolConfig.get_requirements(execution_mode)
            logger.info(
                f"Initializing agent with mode: {execution_mode.value} | {tool_requirements}"
            )

            # 1. 初始化 MCP Servers
            await self._setup_mcp_servers(tool_requirements)

            # 2. 初始化 OpenAI Tools
            self.openai_tools = self._setup_openai_tools(tool_requirements)

            # 3. 初始化 Trading Tools
            self.trading_tools = self._setup_trading_tools(tool_requirements)

            # 4. 創建 LiteLLM 模型
            self.llm_model, self.extra_headers = await self._create_llm_model()

            # 5. 載入 Sub-agents (根據工具配置)
            self.subagent_tools = await self._load_subagents_as_tools(tool_requirements)

            # 6. 合併所有 tools
            all_tools = self.trading_tools + self.subagent_tools

            # 7. 創建 OpenAI Agent（使用 LiteLLM 模型）
            model_settings_dict = {
                "include_usage": True,
            }

            # 只有非 GitHub Copilot 模型才支援 tool_choice
            model_name = self.llm_model.model if self.llm_model else ""
            if "github_copilot" not in model_name.lower():
                model_settings_dict["tool_choice"] = "required"

            if self.extra_headers:
                model_settings_dict["extra_headers"] = self.extra_headers

            self.agent = Agent(
                name=self.agent_id,
                model=self.llm_model,
                instructions=self._build_instructions(self.agent_config.description),
                tools=all_tools,
                mcp_servers=[self.memory_mcp],
                model_settings=ModelSettings(**model_settings_dict),
            )

            # 8. 繪製 Agent 結構圖
            save_agent_graph(
                agent=self.agent,
                agent_id=self.agent_id,
                output_dir=None,  # 使用預設的 backend/logs 目錄
            )

            self.is_initialized = True
            logger.info(
                f"Agent initialized successfully: {self.agent_id} "
                f"(mode: {execution_mode.value}, model: {self.agent_config.ai_model})"
            )

        except (AgentNotFoundError, AgentConfigurationError):
            raise
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_id}: {e}", exc_info=True)
            raise AgentInitializationError(f"Agent initialization failed: {str(e)}")

    async def _setup_mcp_servers(self, tool_requirements: ToolRequirements):
        """
        初始化 MCP 伺服器並根據工具配置有條件地載入

        Args:
            tool_requirements: 工具需求配置

        Raises:
            Exception: 初始化失敗
        """
        try:
            # Casual Market MCP Server (兩種模式都需要)
            if tool_requirements.include_casual_market_mcp:
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
                            "env": {"MARKET_MCP_RATE_LIMITING_ENABLED": "false"},
                        },
                        client_session_timeout_seconds=DEFAULT_AGENT_TIMEOUT,
                    )
                )
                logger.info("casual_market_mcp server initialized")

            # Memory MCP Server (兩種模式都需要)
            if tool_requirements.include_memory_mcp:
                memory_db_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "memory",
                    f"{self.agent_id}.db",
                )
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
                logger.info(f"memory_mcp server initialized (db: {memory_db_path})")

            # Tavily MCP Server (僅 TRADING 模式)
            if tool_requirements.include_tavily_mcp:
                self.tavily_mcp = await self._exit_stack.enter_async_context(
                    MCPServerStdio(
                        name="tavily_mcp",
                        params={
                            "command": "npx",
                            "args": ["-y", "tavily-mcp@latest"],
                            "env": {"TAVILY_API_KEY": f"{TAVILY_API_KEY}"},
                        },
                        client_session_timeout_seconds=DEFAULT_AGENT_TIMEOUT,
                    )
                )
                logger.info("tavily_mcp server initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize MCP server: {e}")
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None

    async def _create_llm_model(self) -> tuple[LitellmModel, dict[str, str] | None]:
        """
        創建 LiteLLM 模型，使用 ai_model_configs 表配置

        所有提供商和模型配置必須在 ai_model_configs 表中定義。
        不支持 fallback - 配置缺失會立即失敗，便於及早發現問題。

        Returns:
            Tuple 包含 LitellmModel 實例和可選的額外 headers 字典

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

        extra_headers = None
        if provider and provider.lower() == "GitHub Copilot".lower():
            extra_headers = {
                "editor-version": "vscode/1.85.1",  # Editor version
                "editor-plugin-version": "copilot/1.155.0",  # Plugin version
                "Copilot-Integration-Id": "vscode-chat",  # Integration ID
                "user-agent": "GithubCopilot/1.155.0",  # User agent
            }
            logger.info(f"Configuring GitHub Copilot headers for agent: {self.agent_id}")

        # 從環境變數讀取 API 密鑰
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            raise AgentConfigurationError(
                f"API key for provider '{provider}' not set. "
                f"Set environment variable: {api_key_env_var}"
            )

        # 構建完整的 LiteLLM 模型字符串，格式為 "provider/model"，其中 "provider/" 可選
        model_str = f"{litellm_prefix}{model_key}"

        logger.info(
            f"Creating LiteLLM model: {model_str} "
            f"(provider: {provider}, api_key_env: {api_key_env_var})"
        )

        # 返回 LitellmModel - headers 將通過 ModelSettings 傳遞
        # return LitellmModel(model=model_str, api_key=api_key), extra_headers
        return LitellmModel(model=model_str), extra_headers

    def _setup_openai_tools(self, tool_requirements: ToolRequirements) -> list[Any]:
        """
        根據工具配置設置 OpenAI 內建工具

        Args:
            tool_requirements: 工具需求配置

        Returns:
            OpenAI 工具列表
        """
        tools = []

        # WebSearchTool: 搜尋功能 (TRADING 模式需要)
        if tool_requirements.include_web_search:
            web_search_tool = WebSearchTool(
                user_location=None,
                filters=None,
                search_context_size="medium",
            )
            tools.append(web_search_tool)
            logger.debug("WebSearchTool included")

        # CodeInterpreterTool: 程式碼執行功能 (兩種模式都需要)
        if tool_requirements.include_code_interpreter:
            code_interpreter_tool = CodeInterpreterTool(
                tool_config={
                    "type": "code_interpreter",
                    "container": {"type": "auto"},
                }
            )
            tools.append(code_interpreter_tool)
            logger.debug("CodeInterpreterTool included")

        logger.debug(
            f"OpenAI tools configured: {len(tools)} tool(s) "
            f"(WebSearch: {tool_requirements.include_web_search}, "
            f"CodeInterpreter: {tool_requirements.include_code_interpreter})"
        )

        return tools

    def _setup_trading_tools(self, tool_requirements: ToolRequirements) -> list[Tool]:
        """
        根據工具配置設置交易相關工具

        Args:
            tool_requirements: 工具需求配置

        Returns:
            交易工具列表
        """
        return create_trading_tools(
            self.agent_service,
            self.agent_id,
            casual_market_mcp=self.casual_market_mcp,
            include_buy_sell=tool_requirements.include_buy_sell_tools,
            include_portfolio=tool_requirements.include_portfolio_tools,
        )

    async def _load_subagents_as_tools(self, tool_requirements: ToolRequirements) -> list[Tool]:
        """
        根據工具配置載入 Sub-agents

        Args:
            tool_requirements: 工具需求配置

        Returns:
            Sub-agent 工具列表
        """
        tools = []

        try:
            # 構建 MCP servers 列表，根據配置動態包含
            mcp_servers = []
            if tool_requirements.include_memory_mcp and self.memory_mcp:
                mcp_servers.append(self.memory_mcp)
            if tool_requirements.include_casual_market_mcp and self.casual_market_mcp:
                mcp_servers.append(self.casual_market_mcp)
            if tool_requirements.include_tavily_mcp and self.tavily_mcp:
                mcp_servers.append(self.tavily_mcp)

            subagent_config = {
                "llm_model": self.llm_model,
                "extra_headers": self.extra_headers,
                "mcp_servers": mcp_servers,  # 共享 MCP servers（動態構建）
            }

            # 技術分析 Agent (兩種模式都需要)
            if tool_requirements.include_technical_agent:
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
                        save_agent_graph(technical_agent, "technical_agent", None)
                    else:
                        logger.error("get_technical_agent() 返回 None")
                except Exception as e:
                    logger.warning(f"技術分析 agent 載入失敗: {e}", exc_info=True)

            # 情緒分析 Agent (僅 TRADING 模式)
            if tool_requirements.include_sentiment_agent:
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
                        save_agent_graph(sentiment_agent, "sentiment_agent", None)
                    else:
                        logger.error("get_sentiment_agent() 返回 None")
                except Exception as e:
                    logger.warning(f"情緒分析 agent 載入失敗: {e}", exc_info=True)

            # 基本面分析 Agent (僅 TRADING 模式)
            if tool_requirements.include_fundamental_agent:
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
                        save_agent_graph(fundamental_agent, "fundamental_agent", None)
                    else:
                        logger.error("get_fundamental_agent() 返回 None")
                except Exception as e:
                    logger.warning(f"基本面分析 agent 載入失敗: {e}", exc_info=True)

            # 風險評估 Agent (兩種模式都需要)
            if tool_requirements.include_risk_agent:
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
                        save_agent_graph(risk_agent, "risk_agent", None)
                    else:
                        logger.error("get_risk_agent() 返回 None")
                except Exception as e:
                    logger.warning(f"風險評估 agent 載入失敗: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"載入 sub-agents 時發生錯誤: {e}")

        logger.info(f"Sub-agents loaded: {len(tools)} agent(s)")
        return tools

    async def run(
        self,
        mode: AgentMode | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        執行 Agent 任務（含記憶體工作流程）

        工作流程：
        1. 執行前：加載過往記憶體和決策
        2. 執行中：分析、決策、執行、記錄
        3. 執行後：保存本次決策並規劃下一步

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

        # 使用預設模式或指定模式，默認為 TRADING（容錯：資料庫可能儲存為字串）
        execution_mode = self._normalize_agent_mode(
            mode or getattr(self.agent_config, "current_mode", None) or AgentMode.TRADING
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

            # === Phase 1: 執行前 - 加載記憶體 ===
            execution_memory = await self._load_execution_memory()
            logger.info(
                f"Loaded execution memory: {len(execution_memory.get('past_decisions', []))} past decisions"
            )

            # 生成 trace ID 並執行
            trace_id = gen_trace_id()
            with trace(workflow_name=f"TradingAgent-{self.agent_id}", trace_id=trace_id):
                # === Phase 2: 構建任務提示（融入記憶體） ===
                task_prompt = await self._build_task_prompt(
                    execution_mode, context, execution_memory
                )

                # === Phase 3: 執行 Agent ===
                result = await Runner.run(self.agent, task_prompt, max_turns=DEFAULT_MAX_TURNS)

                logger.info(
                    f"*** Agent {self.agent_id} execution completed: {result} (trace_id: {trace_id}) ***"
                )

                # === Phase 4: 執行後 - 保存記憶體 ===
                await self._save_execution_memory(
                    execution_result=result.final_output,
                    execution_memory=execution_memory,
                )

                # === Phase 5: 規劃下一步 ===
                next_steps = await self._plan_next_steps(result.final_output)
                logger.info(f"Planned next steps: {next_steps}")

                return {
                    "success": True,
                    "output": result.final_output,
                    "trace_id": trace_id,
                    "mode": execution_mode.value if execution_mode else "unknown",
                    "next_steps": next_steps,
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
    - 主動使用持久記憶工具(memory_mcp)存取先前知識和經驗
    - 決策前必須先使用投資組合管理工具了解資產狀況
    - 充分利用專業分析 Sub-Agents 的能力，做出全面評估
2. 將每次的交易決策使用持久記憶工具(memory_mcp)記錄下來，以便未來參考
3. 決策理由應包含：分析過程、市場判斷、風險考量、Sub-Agents 建議
4. 注意交易日檢查，避免在休市日執行操作
5. 最終目標是最大化投資回報，同時嚴格控制風險

請始終保持理性、謹慎，運用所有可用工具做出明智的投資決策。
        """
        )
        logger.info(f"Instructions for {self.agent_id}: {instructions.strip()}")

        return instructions.strip()

    async def _build_task_prompt(
        self,
        mode: AgentMode,
        context: dict[str, Any] | None,
        execution_memory: dict[str, Any] | None = None,
    ) -> str:
        """
        根據執行模式構建任務提示（融入記憶體上下文）

        Args:
            mode: 執行模式
            context: 額外上下文
            execution_memory: 執行記憶體（含過往決策）

        Returns:
            完整的任務提示
        """

        # 獲取投資組合狀態
        portfolio_status = await get_portfolio_status(self.agent_service, self.agent_id)

        # 構建記憶體上下文（如果存在）
        memory_context = ""
        if execution_memory and execution_memory.get("past_decisions"):
            past_decisions = execution_memory["past_decisions"][:3]  # 最近 3 個決策
            memory_context = "\n\n**📚 過往決策參考：**\n"
            for i, decision in enumerate(past_decisions, 1):
                memory_context += (
                    f"\n{i}. {decision.get('date', 'N/A')} - {decision.get('action', 'N/A')}\n"
                )
                memory_context += f"   理由：{decision.get('reason', 'N/A')}\n"
                if decision.get("result"):
                    memory_context += f"   結果：{decision.get('result', 'N/A')}\n"

        # 根據模式添加指導
        task_prompts = {
            AgentMode.TRADING: f"""
**🎯 交易執行模式 (TRADING MODE)**

目的：分析市場機會並執行交易。

---
{portfolio_status}
---

{memory_context}

可用工具：
• 投資組合管理工具 (record_trade_tool、get_portfolio_status_tool) - 查詢投資組合狀態、記錄交易決策
• 模擬交易工具 (buy_taiwan_stock_tool、sell_taiwan_stock_tool) - 執行台灣股票模擬買賣交易
• memory_mcp (持久記憶工具) - 儲存和回想分析結論
• 專業分析 Sub-Agents - technical_analyst、fundamental_analyst、sentiment_analyst、risk_analyst

限制：
• 必須根據現價進行交易，例如現價為每股1050元，則只能以1050元執行買入或賣出
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

{memory_context}

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
        }

        action_message = (
            task_prompts[mode]
            + f"\n\n目前的日期時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info(f"Action message for {self.agent_id}: {action_message.strip()}")
        return action_message.strip()

    async def _load_execution_memory(self) -> dict[str, Any]:
        """
        從 memory_mcp 加載過往 3 天的執行記憶體和決策

        Returns:
            執行記憶體字典，包含 past_decisions 列表
        """
        return await load_execution_memory(self.memory_mcp, self.agent_id)

    async def _save_execution_memory(
        self,
        execution_result: str,
        execution_memory: dict[str, Any] | None = None,
    ) -> None:
        """
        將本次執行結果保存到 memory_mcp

        Args:
            execution_result: 本次執行的結果
            execution_memory: 前一個階段加載的記憶體（未直接使用）
        """
        # 避免資料庫返回字串導致 .value 取值錯誤
        mode = None
        if self.agent_config:
            mode = self._mode_to_str(getattr(self.agent_config, "current_mode", None))
        await save_execution_memory(self.memory_mcp, self.agent_id, execution_result, mode=mode)

    async def _plan_next_steps(self, execution_result: str) -> list[str]:
        """
        根據執行結果規劃下一步行動

        Args:
            execution_result: 本次執行的結果

        Returns:
            計劃的下一步行動列表
        """
        try:
            next_steps = []

            # 提取執行結果摘要
            summary = self._extract_result_summary(execution_result)

            # 根據結果分析下一步
            if "成功" in summary.lower() or "success" in summary.lower():
                next_steps.append("監視持股表現")
                next_steps.append("準備下次定期評估")
            elif "失敗" in summary.lower() or "error" in summary.lower():
                next_steps.append("調查失敗原因")
                next_steps.append("檢查市場條件")
            else:
                next_steps.append("繼續觀察市場")

            next_steps.append("記錄本次執行到記憶體")

            logger.info(f"Planned next steps: {', '.join(next_steps)}")
            return next_steps

        except Exception as e:
            logger.error(f"Failed to plan next steps: {e}")
            return ["重新評估市場狀況"]

    def _extract_result_summary(self, result: str) -> str:
        """
        從執行結果中提取摘要（用於記憶體存儲）

        Args:
            result: 完整執行結果

        Returns:
            結果摘要
        """
        try:
            # 簡單的摘要提取：取前 200 個字符
            summary = result.strip()
            if len(summary) > 200:
                summary = summary[:200] + "..."
            return summary
        except Exception:
            return "執行結果"

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

    # ==========================================
    # Internal helpers (Enum normalization)
    # ==========================================

    def _normalize_agent_mode(self, mode: AgentMode | str | None) -> AgentMode:
        """將輸入的模式安全轉換為 AgentMode Enum。

        容錯處理：資料庫欄位以 String 儲存，讀取後可能是字串。
        若無法解析則回退至 TRADING。
        """
        if isinstance(mode, AgentMode):
            return mode
        if isinstance(mode, str):
            parsed = validate_agent_mode(mode)
            if parsed is not None:
                return parsed
        return AgentMode.TRADING

    def _mode_to_str(self, mode: AgentMode | str | None) -> str | None:
        """取得模式的字串值，無論輸入為 Enum 或字串。"""
        if mode is None:
            return None
        if isinstance(mode, AgentMode):
            return mode.value
        if isinstance(mode, str):
            parsed = validate_agent_mode(mode)
            return parsed.value if parsed else mode
        return None
