"""
Agent Manager - 管理多個 Agent 的生命週期和執行
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from .base_agent import CasualTradingAgent
from .models import (
    AgentConfig,
    AgentExecutionResult,
    AgentMode,
    AgentState,
    AgentStatus,
    create_default_agent_config,
    generate_agent_id,
)

# ==========================================
# Agent Manager 主類別
# ==========================================


class AgentManager:
    """
    Agent 管理器 - 負責管理多個 Agent 的生命週期
    """

    def __init__(self) -> None:
        self._agents: dict[str, CasualTradingAgent] = {}
        self._active_executions: dict[str, asyncio.Task[AgentExecutionResult]] = {}
        self._execution_history: dict[str, list[AgentExecutionResult]] = {}

        # 配置管理
        self._max_concurrent_executions = 10
        self._execution_semaphore = asyncio.Semaphore(self._max_concurrent_executions)

        # 日誌設定
        self.logger = logging.getLogger("agent_manager")
        self.logger.setLevel(logging.INFO)

        # 管理器狀態
        self._is_running = False
        self._shutdown_event = asyncio.Event()

    @property
    def is_running(self) -> bool:
        """檢查管理器是否運行中"""
        return self._is_running

    @property
    def agent_count(self) -> int:
        """獲取 Agent 總數"""
        return len(self._agents)

    @property
    def active_agent_count(self) -> int:
        """獲取活躍 Agent 數量"""
        return sum(1 for agent in self._agents.values() if agent.is_active)

    # ==========================================
    # 管理器生命週期
    # ==========================================

    async def start(self) -> None:
        """啟動 Agent 管理器"""
        if self._is_running:
            return

        self.logger.info("Starting Agent Manager...")
        self._is_running = True
        self._shutdown_event.clear()

        # 啟動背景任務
        asyncio.create_task(self._monitor_executions())

        self.logger.info("Agent Manager started successfully")

    async def shutdown(self) -> None:
        """關閉 Agent 管理器"""
        if not self._is_running:
            return

        self.logger.info("Shutting down Agent Manager...")
        self._is_running = False

        # 停止所有 Agent
        await self._shutdown_all_agents()

        # 等待所有執行完成
        await self._wait_for_all_executions()

        # 設定關閉事件
        self._shutdown_event.set()

        self.logger.info("Agent Manager shutdown completed")

    async def _shutdown_all_agents(self) -> None:
        """關閉所有 Agent"""
        tasks = []
        for agent in self._agents.values():
            if agent.is_active:
                tasks.append(agent.shutdown())

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _wait_for_all_executions(self) -> None:
        """等待所有執行完成"""
        if self._active_executions:
            self.logger.info(
                f"Waiting for {len(self._active_executions)} active executions to complete..."
            )
            await asyncio.gather(
                *self._active_executions.values(), return_exceptions=True
            )

    # ==========================================
    # Agent 管理
    # ==========================================

    async def create_agent(
        self,
        config: AgentConfig,
        agent_id: str | None = None,
        auto_start: bool = True,
    ) -> str:
        """
        創建新的 Agent

        Args:
            config: Agent 配置
            agent_id: 可選的 Agent ID，None 時自動生成
            auto_start: 是否自動啟動 Agent

        Returns:
            創建的 Agent ID
        """
        if not self._is_running:
            raise RuntimeError("Agent Manager is not running")

        # 生成或驗證 Agent ID
        final_agent_id = agent_id or generate_agent_id()

        if final_agent_id in self._agents:
            raise ValueError(f"Agent with ID {final_agent_id} already exists")

        try:
            # 創建 Agent (需要由子類別實作)
            agent = await self._create_agent_instance(config, final_agent_id)

            # 註冊 Agent
            self._agents[final_agent_id] = agent
            self._execution_history[final_agent_id] = []

            # 自動啟動
            if auto_start:
                await agent.initialize()

            self.logger.info(f"Agent {final_agent_id} created successfully")
            return final_agent_id

        except Exception as e:
            self.logger.error(f"Failed to create agent {final_agent_id}: {e}")
            raise

    async def _create_agent_instance(
        self, config: AgentConfig, agent_id: str
    ) -> CasualTradingAgent:
        """創建 Agent 實例 - 子類別應覆寫此方法"""
        # 這裡需要導入具體的 Agent 實作類別
        # 暫時使用抽象基類，實際使用時需要替換
        from ..trading.trading_agent import TradingAgent

        return TradingAgent(config, agent_id)

    async def remove_agent(self, agent_id: str) -> None:
        """移除 Agent"""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        # 停止 Agent
        if agent.is_active:
            await agent.shutdown()

        # 取消相關執行
        await self._cancel_agent_executions(agent_id)

        # 移除 Agent
        del self._agents[agent_id]
        if agent_id in self._execution_history:
            del self._execution_history[agent_id]

        self.logger.info(f"Agent {agent_id} removed successfully")

    async def get_agent(self, agent_id: str) -> CasualTradingAgent:
        """獲取指定 Agent"""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        return self._agents[agent_id]

    def list_agents(self) -> list[str]:
        """列出所有 Agent ID"""
        return list(self._agents.keys())

    def get_agent_states(self) -> dict[str, AgentState]:
        """獲取所有 Agent 狀態"""
        return {agent_id: agent.state for agent_id, agent in self._agents.items()}

    # ==========================================
    # Agent 執行管理
    # ==========================================

    async def execute_agent(
        self,
        agent_id: str,
        mode: AgentMode | None = None,
        message: str | None = None,
        context: dict[str, Any] | None = None,
        wait_for_completion: bool = True,
    ) -> AgentExecutionResult | None:
        """
        執行指定 Agent

        Args:
            agent_id: Agent ID
            mode: 執行模式
            message: 用戶訊息
            context: 執行上下文
            wait_for_completion: 是否等待執行完成

        Returns:
            執行結果，如果 wait_for_completion=False 則返回 None
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        if not agent.is_active:
            raise RuntimeError(f"Agent {agent_id} is not active")

        # 檢查並發限制
        async with self._execution_semaphore:
            # 創建執行任務
            execution_task = asyncio.create_task(
                agent.execute(mode=mode, user_message=message, context=context)
            )

            # 註冊活躍執行
            self._active_executions[agent_id] = execution_task

            try:
                if wait_for_completion:
                    result = await execution_task
                    self._record_execution_result(agent_id, result)
                    return result
                else:
                    # 非同步執行，設定完成回調
                    execution_task.add_done_callback(
                        lambda task: self._handle_async_execution_completion(
                            agent_id, task
                        )
                    )
                    return None

            finally:
                # 清理活躍執行記錄
                if agent_id in self._active_executions:
                    del self._active_executions[agent_id]

    def _handle_async_execution_completion(
        self, agent_id: str, task: asyncio.Task[AgentExecutionResult]
    ) -> None:
        """處理非同步執行完成"""
        try:
            if task.exception():
                self.logger.error(
                    f"Async execution for agent {agent_id} failed: {task.exception()}"
                )
            else:
                result = task.result()
                self._record_execution_result(agent_id, result)
                self.logger.info(
                    f"Async execution for agent {agent_id} completed: {result.status}"
                )
        except Exception as e:
            self.logger.error(f"Error handling async execution completion: {e}")

    def _record_execution_result(
        self, agent_id: str, result: AgentExecutionResult
    ) -> None:
        """記錄執行結果"""
        if agent_id in self._execution_history:
            self._execution_history[agent_id].append(result)

            # 限制歷史記錄數量
            max_history = 100
            if len(self._execution_history[agent_id]) > max_history:
                self._execution_history[agent_id] = self._execution_history[agent_id][
                    -max_history:
                ]

    async def _cancel_agent_executions(self, agent_id: str) -> None:
        """取消 Agent 的所有執行"""
        if agent_id in self._active_executions:
            task = self._active_executions[agent_id]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            del self._active_executions[agent_id]

    # ==========================================
    # 批量操作
    # ==========================================

    async def execute_all_agents(
        self, mode: AgentMode | None = None, wait_for_completion: bool = True
    ) -> dict[str, AgentExecutionResult | None]:
        """執行所有活躍 Agent"""
        active_agents = [
            agent_id for agent_id, agent in self._agents.items() if agent.is_active
        ]

        if not active_agents:
            self.logger.warning("No active agents to execute")
            return {}

        self.logger.info(f"Executing {len(active_agents)} active agents")

        results = {}
        for agent_id in active_agents:
            try:
                result = await self.execute_agent(
                    agent_id=agent_id,
                    mode=mode,
                    wait_for_completion=wait_for_completion,
                )
                results[agent_id] = result
            except Exception as e:
                self.logger.error(f"Failed to execute agent {agent_id}: {e}")
                results[agent_id] = None

        return results

    async def stop_all_agents(self) -> None:
        """停止所有 Agent"""
        for agent in self._agents.values():
            if agent.is_active:
                await agent.shutdown()

        self.logger.info("All agents stopped")

    async def start_all_agents(self) -> None:
        """啟動所有 Agent"""
        for agent in self._agents.values():
            if not agent.is_active:
                await agent.initialize()

        self.logger.info("All agents started")

    # ==========================================
    # 監控和統計
    # ==========================================

    async def _monitor_executions(self) -> None:
        """監控執行狀態的背景任務"""
        while self._is_running:
            try:
                # 清理完成的執行
                completed_executions = []
                for agent_id, task in self._active_executions.items():
                    if task.done():
                        completed_executions.append(agent_id)

                for agent_id in completed_executions:
                    del self._active_executions[agent_id]

                # 記錄監控資訊
                if self._active_executions:
                    self.logger.debug(
                        f"Active executions: {len(self._active_executions)}"
                    )

                # 等待下次檢查
                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"Error in execution monitoring: {e}")
                await asyncio.sleep(30)

    def get_execution_statistics(self) -> dict[str, Any]:
        """獲取執行統計資訊"""
        total_executions = sum(
            len(history) for history in self._execution_history.values()
        )

        agent_stats = {}
        for agent_id, agent in self._agents.items():
            agent_stats[agent_id] = agent.get_performance_summary()

        return {
            "total_agents": self.agent_count,
            "active_agents": self.active_agent_count,
            "active_executions": len(self._active_executions),
            "total_executions": total_executions,
            "agent_statistics": agent_stats,
        }

    def get_agent_execution_history(
        self, agent_id: str, limit: int = 10
    ) -> list[AgentExecutionResult]:
        """獲取 Agent 執行歷史"""
        if agent_id not in self._execution_history:
            return []

        history = self._execution_history[agent_id]
        return history[-limit:] if limit > 0 else history

    # ==========================================
    # 上下文管理器支援
    # ==========================================

    @asynccontextmanager
    async def agent_execution_context(
        self, agent_id: str
    ) -> AsyncIterator[CasualTradingAgent]:
        """Agent 執行上下文管理器"""
        agent = await self.get_agent(agent_id)

        if not agent.is_active:
            await agent.initialize()

        try:
            yield agent
        finally:
            # 可以在這裡加入清理邏輯
            pass

    # ==========================================
    # 工具方法
    # ==========================================

    async def health_check(self) -> dict[str, Any]:
        """健康檢查"""
        return {
            "manager_running": self._is_running,
            "total_agents": self.agent_count,
            "active_agents": self.active_agent_count,
            "active_executions": len(self._active_executions),
            "timestamp": datetime.now().isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"AgentManager(running={self._is_running}, "
            f"agents={self.agent_count}, "
            f"active={self.active_agent_count})"
        )
