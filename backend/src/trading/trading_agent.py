"""
TradingAgent - 基於 OpenAI Agents SDK 的 生產級實作

整合 AgentDatabaseService，提供完整的生命週期管理、
模式驅動執行、錯誤處理和日誌追蹤。
"""

from __future__ import annotations
import asyncio
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
from agents.mcp import MCPServerStdio, MCPServerSse

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

# CASUAL_MARKET_SSE_URL: casual-market-mcp 的 SSE 連接 URL
# 預設使用本地開發 URL
CASUAL_MARKET_SSE_URL = os.getenv("CASUAL_MARKET_SSE_URL", "http://sacahan-ubunto:8066/sse")
# MEMORY_DB_PATH: Memory MCP 資料庫文件存儲位置
# 預設使用 backend/memory 目錄
MEMORY_DB_PATH = os.getenv(
    "MEMORY_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "memory"),
)
# PERPLEXITY 用於網頁搜索的 MCP 伺服器 API 金鑰
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
# 設置追蹤 API 金鑰（用於監控和日誌）
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

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
        trading_service=None,
    ):
        """
        初始化 TradingAgent

        Args:
            agent_id: Agent ID
            agent_config: Agent 配置
            agent_service: Agent 服務實例
            trading_service: Trading 服務實例（用於執行原子交易）

        Note:
            初始化後需要呼叫 initialize() 完成 Agent 設定
        """
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.agent_service = agent_service
        self.trading_service = trading_service
        self.llm_model = None
        self.extra_headers = None
        self.agent = None
        self.is_initialized = False
        self._exit_stack = (
            AsyncExitStack()
        )  # 創建並保存 AsyncExitStack 實例以管理 MCP servers 生命週期
        self.casual_market_mcp = None
        self.memory_mcp = None
        self.perplexity_mcp = None

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
                "reasoning": {"effort": "medium"},
                "parallel_tool_calls": True,
            }

            # 只有特定模型支援 tool_choice，OpenAI 系列模型不支援
            model_name = self.llm_model.model if self.llm_model else ""
            supports_tool_choice = (
                "gpt-5" not in model_name.lower()
                and "gpt-5-mini" not in model_name.lower()
                and "gpt-4.1" not in model_name.lower()
                and "gpt-4o" not in model_name.lower()
            )
            if supports_tool_choice:
                model_settings_dict["tool_choice"] = "required"

            if self.extra_headers:
                model_settings_dict["extra_headers"] = self.extra_headers

            # 構建 MCP servers 列表，排除 None 值
            mcp_servers_list = [self.memory_mcp, self.casual_market_mcp]

            self.agent = Agent(
                name=self.agent_id,
                model=self.llm_model,
                instructions=self._build_instructions(self.agent_config.description),
                tools=all_tools,
                mcp_servers=mcp_servers_list,
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
        """

        # AsyncExitStack 可能在 cleanup 後被重設，因此需要確保存在
        if self._exit_stack is None:
            self._exit_stack = AsyncExitStack()

        # Casual Market MCP Server (兩種模式都需要)
        if tool_requirements.include_casual_market_mcp:
            self.casual_market_mcp = await self._start_mcp_server_sse(
                name="casual_market_mcp",
                url=CASUAL_MARKET_SSE_URL,
                success_message="casual_market_mcp server initialized (SSE)",
            )

        # Memory MCP Server (兩種模式都需要)
        if tool_requirements.include_memory_mcp:
            memory_db_path = os.path.join(
                MEMORY_DB_PATH,
                f"{self.agent_id}.db",
            )
            os.makedirs(MEMORY_DB_PATH, exist_ok=True)

            self.memory_mcp = await self._start_mcp_server(
                name="memory_mcp",
                params={
                    "command": "npx",
                    "args": ["-y", "mcp-memory-libsql"],
                    "env": {"LIBSQL_URL": f"file:{memory_db_path}"},
                },
                success_message=(f"memory_mcp server initialized (db: {memory_db_path})"),
            )

        # PERPLEXITY MCP Server
        if tool_requirements.include_perplexity_mcp:
            self.perplexity_mcp = await self._start_mcp_server(
                name="perplexity_mcp",
                params={
                    "command": "npx",
                    "args": ["-y", "@perplexity-ai/mcp-server"],
                    "env": {"PERPLEXITY_API_KEY": f"{PERPLEXITY_API_KEY}"},
                },
                success_message="perplexity_mcp server initialized",
            )

    async def _start_mcp_server_sse(
        self,
        *,
        name: str,
        url: str,
        success_message: str,
        timeout_seconds: int = DEFAULT_AGENT_TIMEOUT,
    ):
        """啟動單一 MCP server (SSE)，若失敗則記錄並返回 None。"""

        if self._exit_stack is None:
            self._exit_stack = AsyncExitStack()

        try:
            server = await self._exit_stack.enter_async_context(
                MCPServerSse(
                    name=name,
                    params={"url": url},
                    client_session_timeout_seconds=timeout_seconds,
                )
            )
            logger.info(success_message)
            return server
        except Exception as exc:
            logger.warning(
                f"Failed to initialize {name}: {exc}",
                exc_info=True,
            )
            return None

    async def _start_mcp_server(
        self,
        *,
        name: str,
        params: dict[str, Any],
        success_message: str,
        timeout_seconds: int = DEFAULT_AGENT_TIMEOUT,
    ):
        """啟動單一 MCP server，若失敗則記錄並返回 None。"""

        if self._exit_stack is None:
            self._exit_stack = AsyncExitStack()

        try:
            server = await self._exit_stack.enter_async_context(
                MCPServerStdio(
                    name=name,
                    params=params,
                    client_session_timeout_seconds=timeout_seconds,
                )
            )
            logger.info(success_message)
            return server
        except Exception as exc:
            logger.warning(
                f"Failed to initialize {name}: {exc}",
                exc_info=True,
            )
            return None

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

        # WebSearchTool: OpenAI 提供搜尋功能 (LiteLLM 不支持 OpenAI Tools)
        if tool_requirements.include_web_search:
            web_search_tool = WebSearchTool(
                user_location=None,
                filters=None,
                search_context_size="medium",
            )
            tools.append(web_search_tool)
            logger.debug("WebSearchTool included")

        # CodeInterpreterTool: OpenAI 提供程式碼執行功能 (LiteLLM 不支持 OpenAI Tools)
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
            self.trading_service,
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
            if tool_requirements.include_perplexity_mcp and self.perplexity_mcp:
                mcp_servers.append(self.perplexity_mcp)

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
    ) -> dict[str, Any]:
        """
        執行 Agent 任務（含記憶體工作流程）

        工作流程：
        1. 執行前：加載過往記憶體和決策
        2. 執行中：分析、決策、執行、記錄
        3. 執行後：保存本次決策並規劃下一步

        Args:
            mode: 執行模式

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
            # logger.debug(
            #     f"Loaded execution memory: {execution_memory if execution_memory else 'No past decisions'}"
            # )

            # 生成 trace ID 並執行
            trace_id = gen_trace_id()
            with trace(workflow_name=f"TradingAgent-{self.agent_id}", trace_id=trace_id):
                # === Phase 2: 構建任務提示（融入記憶體） ===
                task_prompt = await self._build_task_prompt(execution_mode, execution_memory)

                # === Phase 3: 執行 Agent ===
                result = await Runner.run(self.agent, task_prompt, max_turns=DEFAULT_MAX_TURNS)

                logger.info(
                    f"✅ Agent {self.agent_id} execution completed: {result} (trace_id: {trace_id})"
                )

                # === Phase 4: 執行後 - 保存記憶體 ===
                await self._save_execution_memory(
                    execution_result=result.final_output,
                    execution_memory=execution_memory,
                )

                return {
                    "success": True,
                    "output": result.final_output,
                    "trace_id": trace_id,
                    "mode": execution_mode.value if execution_mode else "unknown",
                }

        except asyncio.CancelledError:
            logger.warning(f"Agent execution cancelled: {self.agent_id}")

            # 當被取消時，更新狀態為 INACTIVE（已停止）
            try:
                await self.agent_service.update_agent_status(self.agent_id, AgentStatus.INACTIVE)
            except Exception as status_error:
                logger.error(f"Failed to update status on cancel: {status_error}")

            # 重新拋出 CancelledError 以保持正確的異步行為
            raise

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
        根據描述構建 Agent 指令（系統角色和基本原則）

        Args:
            description: Agent 基本描述

        Returns:
            Agent 指令（專注於角色和目標）
        """

        # 基本角色描述
        instructions_parts = [
            f"你是一個專業的股票交易 Agent，你的代號是 {self.agent_id}。",
            "你的投資主張如下：",
            f"{description}",
        ]

        # 投資偏好設定（如果有的話）
        # 注意：不在 instructions 中提及具體股票代號，避免產生偏見
        # investment_preferences 應該在任務執行過程中作為參考，而非硬性限制
        if self.agent_config.investment_preferences:
            instructions_parts.extend(
                [
                    f"你最近對清單中的 {self.agent_config.investment_preferences} 股票感到興趣，希望進一步研究是否值得投資，但同時也不限於這些股票，你會廣泛探索其他潛在機會。",
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

**🎯 你的核心目標：**
- 你應該基於市場分析和投資策略，廣泛尋找最佳投資機會（不限於特定股票）
- 最大化投資回報，同時嚴格控制風險
- 基於充分的市場分析進行理性、謹慎的決策
- 遵守所有交易約束和持股限制
- 記錄每次交易的決策理由供未來參考

**💡 工作原則：**
- 在任務提示(Task Prompt)中會提供詳細的工具說明和使用流程
- 根據執行模式的不同，工具和功能會有所不同
- 遵守系統提供的所有約束和指導
        """
        )
        logger.info(f"Instructions for {self.agent_id}: {instructions.strip()}")

        return instructions.strip()

    async def _build_task_prompt(
        self,
        mode: AgentMode,
        execution_memory: str | None = None,
    ) -> str:
        """
        根據執行模式構建任務提示（融入記憶體上下文）

        Args:
            mode: 執行模式
            execution_memory: 執行記憶體（含過往決策）

        Returns:
            完整的任務提示
        """

        # 獲取投資組合狀態
        portfolio_status = await get_portfolio_status(self.agent_service, self.agent_id)

        # 根據模式添加指導
        if mode == AgentMode.TRADING:
            action_message = f"""
**🎯 交易執行模式 (TRADING MODE)**

**🚨 核心原則：你是一個完全自主的交易 Agent，分析完成後必須立即執行交易，無需等待任何人工確認或批准。**

{portfolio_status}
---
{execution_memory if execution_memory else ""}
---

**🛠️ 可用工具：**

1. **原子交易工具（⭐ 必須使用）**
   - execute_trade_atomic(ticker, action, quantity, price, decision_reason, company_name)
   - 作用：執行完整交易（市場交易 → 記錄 → 更新資金 → 更新績效）
   - 特點：原子性保證，全部成功或全部失敗，自動回滾
   - 例子：execute_trade_atomic("2330", "BUY", 1000, 520.0, "技術突破信號", "台積電")

2. **投資組合工具**
   - get_portfolio_status_tool：查詢當前投資組合狀態（持股、資金、績效）
   - get_stock_price_tool：查詢股票即時價格
   - record_trade_tool：（備用）記錄交易決策

3. **記憶工具**
   - memory_mcp：儲存和回想分析結論、過往決策

4. **分析 Sub-Agents**
   - technical_analyst：技術面分析
   - fundamental_analyst：基本面分析
   - sentiment_analyst：情感面分析
   - risk_analyst：風險評估

**📋 執行流程（必須完整執行）：**

1️⃣ 使用 get_portfolio_status_tool 查詢當前狀態
2️⃣ 使用各分析 Sub-Agents 對候選標的進行全面評估
3️⃣ **🔴 立即執行交易**：一旦分析完成且有交易機會，必須立即調用 execute_trade_atomic() 執行
4️⃣ 執行交易後，將交易結果和決策理由摘要為500字以內的結論回覆

**🚨 自主行動規則（最高優先級）：**

• ✅ **必須自主行動**：你擁有完整的交易授權，分析完成後必須立即執行，不要詢問是否執行
• ✅ **禁止等待確認**：不要說「請確認是否執行」「等待您的指示」「是否要我執行」等
• ✅ **先執行再報告**：應該是「我已執行...」而不是「我建議執行...」
• ✅ **決策即行動**：有交易決策 = 立即調用 execute_trade_atomic() 執行

**⚠️ 交易約束：**

• 必須使用 execute_trade_atomic() 執行交易（原子性保證）
• 必須根據現價進行交易，例如現價為每股 1050 元，則只能以 1050 元執行買入或賣出
• 買入前需確認有足夠資金，賣出前需確認有足夠持股
• 遵守最大持股比例限制：{self.agent_config.max_position_size}%
• 最終必須在決策理由中說明：分析過程、市場判斷、風險考量

**❌ 禁止行為：**

• 禁止等待人工確認後才執行
• 禁止用「建議」「推薦」代替實際執行
• 禁止在有交易機會時選擇觀望而不行動
"""

        elif mode == AgentMode.REBALANCING:
            action_message = f"""
**⚖️ 投資組合重新平衡模式 (REBALANCING MODE)**

**🚨 核心原則：你是一個完全自主的分析 Agent，必須獨立完成投資組合評估並產生具體的再平衡執行計畫，無需等待任何人工確認。**

{portfolio_status}
---
{execution_memory if execution_memory else ""}
---

**📚 模式說明：**

本模式專注於分析現有持股並產生具體的再平衡計畫。
雖然本模式無法直接執行交易，但你必須產生完整、具體的交易計畫，
該計畫將自動保存到記憶體，作為下一輪 TRADING 模式執行時的參考依據。

**🛠️ 可用工具：**

1. **投資組合查詢工具**
   - get_portfolio_status_tool：查詢當前投資組合狀態（持股明細、資金、績效）
   - get_stock_price_tool：查詢股票即時價格

2. **分析工具**
   - memory_mcp：儲存重新平衡分析結論和執行計畫
   - technical_analyst：評估技術面信號
   - risk_analyst：評估持股風險

3. **本模式不可用工具**
   - ❌ execute_trade_atomic()：本模式無法直接執行交易
   - ❌ record_trade_tool：不可用

**📋 執行流程（必須完整執行）：**

1️⃣ 使用 get_portfolio_status_tool 查詢當前持股和比例
2️⃣ 使用 Sub-Agents 分析現有持股是否符合投資策略
3️⃣ 評估每個持股的目標比例 vs 當前比例的偏差
4️⃣ **🔴 產生具體執行計畫**：必須輸出明確的買賣建議（見下方格式）
5️⃣ 將分析結論和執行計畫摘要為報告回覆（自動保存到記憶體）

**🚨 自主行動規則（最高優先級）：**

• ✅ **必須自主分析**：完成分析後必須立即產生具體計畫，不要詢問是否繼續
• ✅ **禁止等待確認**：不要說「請確認是否需要調整」「等待您的指示」等
• ✅ **必須產生計畫**：分析結果必須轉化為具體的交易計畫，不能只有抽象建議
• ✅ **計畫即輸出**：有再平衡需求 = 立即產生具體執行計畫

**📝 執行計畫輸出格式（必須遵守）：**

```
## 再平衡執行計畫

### 建議賣出
| 股票代碼 | 公司名稱 | 當前持股 | 建議賣出 | 目標價格 | 原因 |
|---------|---------|---------|---------|---------|------|
| XXXX    | XXX     | X張     | X張     | $XXX    | ...  |

### 建議買入
| 股票代碼 | 公司名稱 | 當前持股 | 建議買入 | 目標價格 | 原因 |
|---------|---------|---------|---------|---------|------|
| XXXX    | XXX     | X張     | X張     | $XXX    | ...  |

### 執行優先順序
1. 先執行賣出以釋放資金
2. 再執行買入

### 預期結果
- 調整後現金部位：$XXX
- 調整後持股比例：...
```

**⚠️ 分析約束：**

• 遵守最大持股比例限制：{self.agent_config.max_position_size}%
• 考量交易成本和稅務影響（在計畫中說明）
• 分析結論應詳盡且有理有據
• 若無需調整，明確說明原因並記錄當前狀態

**❌ 禁止行為：**

• 禁止等待人工確認後才產生計畫
• 禁止用模糊的「建議考慮」代替具體的買賣計畫
• 禁止遺漏執行細節（數量、價格、優先順序）

**💡 重要提示：**

你的輸出將自動保存到記憶體，下一輪 TRADING 模式會讀取這份計畫並據此執行交易。
因此，計畫必須足夠具體、可執行，讓 TRADING 模式能夠直接依照計畫調用 execute_trade_atomic() 執行。
"""

        else:
            # 預設為 TRADING 模式
            action_message = f"""
**🎯 交易執行模式 (TRADING MODE)**

目的：分析市場機會並執行交易。

{portfolio_status}
---
{execution_memory if execution_memory else ""}

**🛠️ 可用工具：**

1. **原子交易工具（⭐ 優先使用）**
   - execute_trade_atomic(ticker, action, quantity, price, decision_reason, company_name)
   - 作用：執行完整交易（市場交易 → 記錄 → 更新資金 → 更新績效）

2. **投資組合工具**
   - get_portfolio_status_tool：查詢當前投資組合狀態
   - get_stock_price_tool：查詢股票即時價格

3. **分析 Sub-Agents**
   - technical_analyst、fundamental_analyst、sentiment_analyst、risk_analyst
"""

        action_message = (
            action_message
            + f"\n\n**📅 目前的日期時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info(f"Action message for {self.agent_id}: {action_message.strip()}")
        return action_message.strip()

    async def _load_execution_memory(self) -> str | None:
        """
        從 memory_mcp 加載過往的執行記憶體和決策

        Returns:
            執行記憶體字串，若無記憶體則返回 None
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

    async def cancel(self) -> None:
        """
        取消 Agent 正在執行的任務

        這個方法被 TradingService.stop_agent() 呼叫，
        用於中斷正在進行的 Agent 執行。

        Note:
            OpenAI Agents SDK 不提供直接的任務取消機制。
            此實現通過觸發清理流程來停止 Agent。

        Timestamps Updated:
            - Agent.updated_at: 設置為當前時間
        """
        logger.info(f"Cancelling agent execution: {self.agent_id}")
        # 清理資源（會關閉 MCP servers）
        await self.cleanup()
        logger.info(f"Agent execution cancelled: {self.agent_id}")

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

        遵循 timestamp.instructions.md：
        - 明確設置 Agent 狀態為 INACTIVE
        - 完整清理所有資源
        """
        try:
            # 更新 Agent 狀態為 INACTIVE（遵循 timestamp.instructions.md)
            if self.agent_service:
                await self.agent_service.update_agent_status(self.agent_id, AgentStatus.INACTIVE)
                logger.debug(f"Updated agent {self.agent_id} status to INACTIVE during cleanup")
        except Exception as e:
            logger.error(f"Failed to update agent status during cleanup: {e}")

        # 關閉 MCP servers
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
