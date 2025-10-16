"""
TradingAgent - 基於 OpenAI Agents SDK 的生產級實作

整合 AgentDatabaseService，提供完整的生命週期管理、
模式驅動執行、錯誤處理和日誌追蹤。
"""

from __future__ import annotations
import os

from dotenv import load_dotenv

import logging
from typing import Any
from contextlib import AsyncExitStack

from agents import Agent, ModelSettings, Runner, gen_trace_id, trace, Tool
from agents.mcp import MCPServerStdio
from agents.tools import WebSearchTool, CodeInterpreterTool

from .tools.fundamental_agent import get_fundamental_agent

from .models import AgentStatus

from ..service.agents_service import (
    AgentsService,
    AgentConfigurationError,
    AgentNotFoundError,
    AgentDatabaseError,
)
from ..service.models import AgentMode, Agent as AgentConfig

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

            # 3. 載入 Sub-agents (從 tools/ 目錄，傳入共享配置)
            self.subagent_tools = await self._load_subagents_as_tools()

            # 4. 合併所有 tools
            all_tools = self.openai_tools + self.subagent_tools

            # 5. 創建 OpenAI Agent
            self.agent = Agent(
                name=self.agent_id,
                model=self.agent_config.ai_model or DEFAULT_MODEL,
                instructions=self.agent_config.instructions,
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

    async def _load_subagents_as_tools(self) -> list[Tool]:
        """載入 Sub-agents (從 tools/ 目錄，根據資料庫配置）"""
        subagents = []

        # 統一的 subagent 配置參數
        subagent_config = {
            "model_name": self.ai_model,  # 從資料庫載入
            "mcp_servers": self.mcp_servers,  # 傳入相同的 MCP servers
            "openai_tools": self.openai_tools,  # 傳入相同的 OpenAI tools
            "max_turns": DEFAULT_MAX_TURNS,
        }

        # 生成 Sub-agents
        subagents.append(await get_fundamental_agent(**subagent_config))

        # 將 Sub-agents 包裝為工具
        return [agent.as_tool() for agent in subagents]

    async def run(
        self,
        task: str,
        mode: AgentMode | None = None,
        agent_config: Agent | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        執行 Agent 任務

        Args:
            task: 任務描述
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
                task_prompt = self._build_task_prompt(task, execution_mode, context)

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

    def _build_task_prompt(self, task: str, mode: AgentMode, context: dict[str, Any] | None) -> str:
        """
        根據執行模式構建任務提示

        Args:
            task: 基本任務描述
            mode: 執行模式
            context: 額外上下文

        Returns:
            完整的任務提示
        """
        # 基礎提示
        prompt_parts = [task]

        # 根據模式添加指導
        mode_instructions = {
            AgentMode.TRADING: "請執行交易決策，包括分析和具體買賣建議。",
            AgentMode.REBALANCING: "請檢查當前持倉並提供再平衡建議。",
            AgentMode.STRATEGY_REVIEW: "請全面檢視當前投資策略的有效性。",
            AgentMode.OBSERVATION: "請進行市場觀察和資訊收集，不需要具體交易建議。",
        }

        if mode in mode_instructions:
            prompt_parts.append(mode_instructions[mode])

        # 添加上下文資訊
        if context:
            if "holdings" in context:
                prompt_parts.append(f"當前持倉：{context['holdings']}")
            if "market_conditions" in context:
                prompt_parts.append(f"市場狀況：{context['market_conditions']}")

        return "\n\n".join(prompt_parts)

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
