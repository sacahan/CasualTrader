"""
CasualTrader Base Agent Implementation
使用 Python 3.12+ 語法和 OpenAI Agent SDK 的基礎 Agent 類別

Tracing 架構說明
===============

本系統整合兩種互補的執行追蹤機制:

1. OpenAI Agents SDK Trace (自動啟用)
   - 用途: 即時可視化和調試 Agent 執行流程
   - 位置: 上傳到 OpenAI Dashboard (https://platform.openai.com/traces)
   - 啟用方式: trace() context manager 自動記錄
   - 適用場景: 開發、調試、問題排查
   - 特點:
     * 自動記錄所有 Runner.run() 調用
     * 可視化工具調用和 LLM 響應
     * 預設使用 OpenAI API key (無需額外配置)
     * 可用 group_id 將多個 run 關聯為同一工作流

2. 內部執行日誌 (trace_data)
   - 用途: 業務分析、績效追蹤、審計記錄
   - 位置: 存儲在資料庫 AgentExecutionResult.trace_data 欄位
   - 記錄內容:
     * 執行步驟詳細日誌 (turn_start, turn_end, tool_call, agent_decision)
     * 會話摘要 (session_summary)
     * 執行統計資訊
   - 適用場景: 生產環境、長期數據分析、合規審計
   - 特點:
     * 持久化存儲
     * 可查詢和分析
     * 包含業務相關的上下文資訊

整合原則
--------
- OpenAI trace 專注於技術層面的可觀察性
- 內部 trace_data 專注於業務層面的可追溯性
- 兩者互補，不重複記錄相同資訊
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

# OpenAI Agent SDK 導入
from agents import Agent, trace  # OpenAI Agents SDK


from .models import (
    AgentConfig,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentMode,
    AgentState,
    AgentStatus,
    SessionStatus,
    generate_session_id,
)

# ==========================================
# Agent 基礎抽象類別
# ==========================================


class CasualTradingAgent(ABC):
    """
    CasualTrader 系統的基礎 Agent 抽象類別
    提供 Agent 生命週期管理和執行環境
    """

    def __init__(self, config: AgentConfig, agent_id: str | None = None) -> None:
        self.config = config
        self.agent_id = agent_id or self._generate_agent_id()
        self.state = AgentState(id=self.agent_id, name=config.name, config=config)

        # 內部狀態管理
        self._openai_agent: Agent | None = None
        self._current_session: AgentExecutionContext | None = None
        self._is_initialized = False

        # 日誌設定
        self.logger = logging.getLogger(f"agent.{self.agent_id}")
        self.logger.setLevel(logging.INFO)

    @property
    def is_active(self) -> bool:
        """檢查 Agent 是否處於活躍狀態"""
        return self.state.status == AgentStatus.ACTIVE

    @property
    def current_mode(self) -> AgentMode:
        """獲取當前執行模式"""
        return self.state.current_mode

    # ==========================================
    # Agent 生命週期管理
    # ==========================================

    async def initialize(self) -> None:
        """初始化 Agent 系統"""
        if self._is_initialized:
            return

        try:
            # 初始化 OpenAI Agent
            await self._setup_openai_agent()

            # 初始化工具
            await self._setup_tools()

            # 設定為活躍狀態
            self.state.status = AgentStatus.ACTIVE
            self.state.update_activity()

            self._is_initialized = True
            self.logger.info(f"Agent {self.agent_id} initialized successfully")

        except Exception as e:
            self.state.status = AgentStatus.ERROR
            self.logger.error(f"Agent {self.agent_id} initialization failed: {e}")
            raise

    async def shutdown(self) -> None:
        """關閉 Agent 系統"""
        self.logger.info(f"Shutting down agent {self.agent_id}")

        # 設定為非活躍狀態
        self.state.status = AgentStatus.INACTIVE
        self.state.update_activity()

        self._is_initialized = False

    # ==========================================
    # Agent 執行核心
    # ==========================================

    async def execute(
        self,
        mode: AgentMode | None = None,
        user_message: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentExecutionResult:
        """
        執行 Agent 任務

        Args:
            mode: 執行模式，None 時使用當前模式
            user_message: 用戶訊息
            context: 額外執行上下文

        Returns:
            執行結果
        """
        if not self._is_initialized:
            await self.initialize()

        # 設定執行模式
        execution_mode = mode or self.state.current_mode
        session_id = generate_session_id(self.agent_id)

        # 創建執行上下文
        execution_context = AgentExecutionContext(
            agent_id=self.agent_id,
            session_id=session_id,
            mode=execution_mode,
            max_turns=self.config.max_turns,
            timeout=self.config.execution_timeout,
            initial_input=context or {},
            user_message=user_message,
        )

        # 設定當前會話
        self._current_session = execution_context

        # 使用 OpenAI Agents SDK trace context manager 包裹執行過程
        # - trace_name: 工作流名稱，用於在 OpenAI Dashboard 中識別
        # - group_id: 將同一 Agent 的多次執行關聯在一起
        # - 自動記錄所有 Runner.run() 調用和工具使用
        # - 內部執行日誌 (trace_data) 由子類別在 _prepare_execution 中記錄
        trace_name = f"{self.config.name}-{execution_mode.value}"
        with trace(trace_name, group_id=self.agent_id):
            try:
                # 執行前準備
                await self._prepare_execution(execution_context)

                # 執行 Agent
                result = await self._execute_agent(execution_context)

                # 後處理
                await self._post_execution(execution_context, result)

                # 更新統計資訊
                self._update_execution_stats(result)

                return result

            except Exception as e:
                # 錯誤處理
                error_result = await self._handle_execution_error(execution_context, e)
                self._update_execution_stats(error_result)
                return error_result

            finally:
                # 清理會話
                self._current_session = None

    # ==========================================
    # 抽象方法 - 子類別必須實作
    # ==========================================

    @abstractmethod
    async def _setup_tools(self) -> list[Any]:
        """設定 Agent 工具"""
        pass

    @abstractmethod
    async def _prepare_execution(self, context: AgentExecutionContext) -> None:
        """執行前準備工作"""
        pass

    @abstractmethod
    async def _build_execution_prompt(self, context: AgentExecutionContext) -> str:
        """建構執行提示詞"""
        pass

    # ==========================================
    # 內部實作方法
    # ==========================================

    def _generate_agent_id(self) -> str:
        """生成 Agent ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"agent_{timestamp}_{id(self):x}"

    async def _setup_openai_agent(self) -> None:
        """設定 OpenAI Agent SDK - 支援 OpenAI 和 LiteLLM 模型"""
        tools = await self._setup_tools()

        # 生成指令
        instructions = await self._build_agent_instructions()

        # 使用配置中的模型創建 Agent
        self._openai_agent = Agent(
            name=self.config.name,
            instructions=instructions,
            tools=tools,
            model=self.config.model,
            max_turns=self.config.max_turns,
        )
        self.logger.info(
            f"OpenAI Agent created with {len(tools)} tools and model {self.config.model}"
        )

    async def _get_model_config(self, model_key: str) -> dict[str, Any] | None:
        """
        從數據庫獲取模型配置

        Args:
            model_key: 模型 key (例如: "gpt-4o", "claude-sonnet-4.5")

        Returns:
            模型配置字典,如果找不到則返回 None
        """
        try:
            # 這裡需要注入 database_service 依賴
            # 暫時使用 None,需要在子類別中覆寫或注入
            return None
        except Exception as e:
            self.logger.warning(f"Failed to fetch model config for {model_key}: {e}")
            return None

    async def _build_agent_instructions(self) -> str:
        """建構 Agent 指令"""
        # 基礎指令模板
        base_instructions = f"""
你是 {self.config.name}，一個智能台灣股票交易代理人。

核心任務：
{self.config.description}

投資偏好：
{self.config.investment_preferences}

你可以使用以下執行模式：
- TRADING: 主動交易模式，執行買賣決策
- REBALANCING: 投資組合再平衡
- STRATEGY_REVIEW: 策略檢討和調整
- OBSERVATION: 市場觀察和分析

交易限制：
- 可用資金：NT${self.config.initial_funds:,.0f}
- 最大單筆部位：{self.config.investment_preferences.max_position_size}%
- 台灣股市交易時間：09:00-13:30（週一至週五）
- 最小交易單位：1000 股

請根據當前市場條件和您的投資策略進行適當的決策。
        """.strip()

        # 加入額外指令
        if self.config.additional_instructions:
            base_instructions += f"\n\n額外指令：\n{self.config.additional_instructions}"

        return base_instructions

    async def _execute_agent(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """執行 OpenAI Agent"""
        start_time = datetime.now()

        # 建構執行訊息
        execution_prompt = await self._build_execution_prompt(context)

        try:
            # 使用超時機制執行
            result = await asyncio.wait_for(
                self._openai_agent.run(execution_prompt),  # type: ignore[union-attr]
                timeout=context.timeout,
            )

            end_time = datetime.now()

            # 建構執行結果
            execution_result = AgentExecutionResult(
                session_id=context.session_id,
                agent_id=context.agent_id,
                status=SessionStatus.COMPLETED,
                mode=context.mode,
                start_time=start_time,
                end_time=end_time,
                initial_input=context.initial_input,
                final_output=result,
                tools_called=self._extract_tools_called(result),
            )

            execution_result.calculate_execution_time()
            return execution_result

        except TimeoutError:
            end_time = datetime.now()
            execution_result = AgentExecutionResult(
                session_id=context.session_id,
                agent_id=context.agent_id,
                status=SessionStatus.TIMEOUT,
                mode=context.mode,
                start_time=start_time,
                end_time=end_time,
                initial_input=context.initial_input,
                error_message="Agent execution timed out",
                error_type="TimeoutError",
            )
            execution_result.calculate_execution_time()
            return execution_result

    def _extract_tools_called(self, result: dict[str, Any]) -> list[str]:
        """從執行結果中提取調用的工具列表"""
        # 這裡需要根據 OpenAI Agent SDK 的實際響應格式來實作
        # 暫時返回空列表
        return []

    async def _handle_execution_error(
        self, context: AgentExecutionContext, error: Exception
    ) -> AgentExecutionResult:
        """處理執行錯誤"""
        end_time = datetime.now()

        self.logger.error(f"Agent execution failed for session {context.session_id}: {error}")

        return AgentExecutionResult(
            session_id=context.session_id,
            agent_id=context.agent_id,
            status=SessionStatus.FAILED,
            mode=context.mode,
            start_time=context.start_time,
            end_time=end_time,
            initial_input=context.initial_input,
            error_message=str(error),
            error_type=type(error).__name__,
        )

    async def _post_execution(
        self, context: AgentExecutionContext, result: AgentExecutionResult
    ) -> None:
        """執行後處理"""
        # 更新 Agent 狀態
        self.state.update_activity()
        self.state.last_execution_id = result.session_id

        # 記錄日誌
        match result.status:
            case SessionStatus.COMPLETED:
                self.logger.info(
                    f"Session {result.session_id} completed successfully "
                    f"in {result.execution_time_ms}ms"
                )
            case SessionStatus.FAILED:
                self.logger.error(f"Session {result.session_id} failed: {result.error_message}")
            case SessionStatus.TIMEOUT:
                self.logger.warning(
                    f"Session {result.session_id} timed out after {result.execution_time_ms}ms"
                )

    def _update_execution_stats(self, result: AgentExecutionResult) -> None:
        """更新執行統計"""
        self.state.total_executions += 1
        self.state.total_execution_time += result.execution_time_ms / 1000.0

        match result.status:
            case SessionStatus.COMPLETED:
                self.state.successful_executions += 1
            case SessionStatus.FAILED | SessionStatus.TIMEOUT:
                self.state.failed_executions += 1

    # ==========================================
    # 公共 API 方法
    # ==========================================

    async def change_mode(self, new_mode: AgentMode, reason: str = "") -> None:
        """變更 Agent 執行模式"""
        old_mode = self.state.current_mode
        self.state.current_mode = new_mode
        self.state.update_activity()

        self.logger.info(
            f"Agent mode changed from {old_mode} to {new_mode}" + (f": {reason}" if reason else "")
        )

    async def update_config(self, new_config: AgentConfig) -> None:
        """更新 Agent 配置"""
        self.config = new_config
        self.state.config = new_config
        self.state.update_activity()

        # 如果 Agent 已初始化，需要重新設定
        if self._is_initialized:
            await self._setup_openai_agent()

        self.logger.info("Agent configuration updated")

    def get_performance_summary(self) -> dict[str, Any]:
        """獲取績效摘要"""
        success_rate = 0.0
        if self.state.total_executions > 0:
            success_rate = self.state.successful_executions / self.state.total_executions * 100

        avg_execution_time = 0.0
        if self.state.total_executions > 0:
            avg_execution_time = self.state.total_execution_time / self.state.total_executions

        return {
            "total_executions": self.state.total_executions,
            "success_rate": round(success_rate, 2),
            "avg_execution_time": round(avg_execution_time, 2),
            "total_return": self.state.total_return,
            "current_portfolio_value": self.state.current_portfolio_value,
            "unrealized_pnl": self.state.unrealized_pnl,
            "realized_pnl": self.state.realized_pnl,
        }

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典格式"""
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "status": self.state.status,
            "current_mode": self.state.current_mode,
            "created_at": self.state.created_at.isoformat(),
            "last_active_at": (
                self.state.last_active_at.isoformat() if self.state.last_active_at else None
            ),
            "performance": self.get_performance_summary(),
            "config": {
                "description": self.config.description,
                "initial_funds": self.config.initial_funds,
                "model": self.config.model,
                "max_turns": self.config.max_turns,
            },
        }

    def __repr__(self) -> str:
        return (
            f"CasualTradingAgent(id={self.agent_id}, "
            f"name='{self.config.name}', "
            f"status={self.state.status}, "
            f"mode={self.state.current_mode})"
        )
