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
    generate_agent_id,
)

# ==========================================
# Agent Manager 主類別
# ==========================================


class AgentManager:
    """
    Agent 管理器 - 負責管理多個 Agent 的生命週期
    """

    def __init__(self, database_service: Any = None, max_concurrent_executions: int = 10) -> None:
        self._agents: dict[str, CasualTradingAgent] = {}
        self._active_executions: dict[str, asyncio.Task[AgentExecutionResult]] = {}
        self._execution_history: dict[str, list[AgentExecutionResult]] = {}

        # Agent runtime status tracking (idle/running/stopped)
        self._runtime_status: dict[str, str] = {}

        # 資料庫服務（用於持久化 Agent 狀態）
        self._database_service = database_service

        # 配置管理
        self._max_concurrent_executions = max_concurrent_executions
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

    @property
    def max_concurrent_executions(self) -> int:
        """獲取最大併發執行數"""
        return self._max_concurrent_executions

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
            await asyncio.gather(*self._active_executions.values(), return_exceptions=True)

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
        self.logger.info(
            f"create_agent called for '{config.name}' with ai_model '{config.ai_model}'"
        )

        # Auto-start Agent Manager if not running
        if not self._is_running:
            self.logger.warning("Agent Manager not running, starting automatically...")
            await self.start()

        # 生成或驗證 Agent ID
        final_agent_id = agent_id or generate_agent_id()
        self.logger.debug(f"Generated agent_id: {final_agent_id}")

        if final_agent_id in self._agents:
            raise ValueError(f"Agent with ID {final_agent_id} already exists")

        try:
            # 創建 Agent (需要由子類別實作)
            self.logger.info(f"Calling _create_agent_instance for {final_agent_id}")
            agent = await self._create_agent_instance(config, final_agent_id)
            self.logger.info(f"_create_agent_instance completed for {final_agent_id}")

            # 註冊 Agent
            self._agents[final_agent_id] = agent
            self._execution_history[final_agent_id] = []

            # 持久化到資料庫 (關鍵步驟！)
            if self._database_service:
                self.logger.info(f"Saving agent state to database for {final_agent_id}")
                try:
                    await self._database_service.save_agent_state(agent.state)
                    self.logger.info(f"Agent state saved to database: {final_agent_id}")
                except Exception as db_error:
                    self.logger.error(f"Failed to save agent to database: {db_error}")
                    # 清理已創建的內存狀態
                    del self._agents[final_agent_id]
                    del self._execution_history[final_agent_id]
                    raise RuntimeError(
                        f"Agent created in memory but failed to persist to database: {db_error}"
                    ) from db_error
            else:
                self.logger.warning(
                    f"Database service not configured, agent {final_agent_id} created in-memory only"
                )

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
        self.logger.debug(f"_create_agent_instance: Importing TradingAgent for {agent_id}")
        # 這裡需要導入具體的 Agent 實作類別
        # 暫時使用抽象基類，實際使用時需要替換
        from ..trading.trading_agent import TradingAgent

        self.logger.debug(f"_create_agent_instance: Creating TradingAgent instance for {agent_id}")
        agent = TradingAgent(config, agent_id)
        self.logger.info(f"_create_agent_instance: TradingAgent instance created for {agent_id}")
        return agent

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

        # 從資料庫刪除（包括所有相關資料）
        if self._database_service:
            self.logger.info(f"Deleting agent from database: {agent_id}")
            try:
                deleted = await self._database_service.delete_agent(agent_id)
                if deleted:
                    self.logger.info(f"Agent deleted from database: {agent_id}")
                else:
                    self.logger.warning(f"Agent {agent_id} not found in database")
            except Exception as db_error:
                self.logger.error(f"Failed to delete agent from database: {db_error}")
                # 繼續移除內存中的 Agent，但記錄錯誤
        else:
            self.logger.warning(
                f"Database service not configured, agent {agent_id} removed from memory only"
            )

        # 移除 Agent
        del self._agents[agent_id]
        if agent_id in self._execution_history:
            del self._execution_history[agent_id]

        self.logger.info(f"Agent {agent_id} removed successfully")

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        """獲取指定 Agent 的信息（API用）"""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]
        return self._agent_to_dict(agent)

    def get_agent_instance(self, agent_id: str) -> CasualTradingAgent:
        """獲取指定 Agent 實例（內部用）"""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        return self._agents[agent_id]

    async def list_agents(self) -> list[dict[str, Any]]:
        """列出所有 Agent 及其狀態信息"""
        # 如果有資料庫服務，從資料庫載入所有 agents
        if self._database_service:
            try:
                # 從資料庫載入所有 agent 狀態
                await self._database_service.initialize()
                agent_states = await self._database_service.list_agents()

                # 為不在記憶體中的 agents 創建實例
                for agent_state in agent_states:
                    if agent_state.id not in self._agents:
                        self.logger.info(f"Restoring agent from database: {agent_state.id}")
                        # 從資料庫狀態重建 agent 實例
                        agent = await self._create_agent_instance(
                            agent_state.config, agent_state.id
                        )
                        self._agents[agent_state.id] = agent
                        self._execution_history[agent_state.id] = []
                        self.logger.info(f"Agent restored: {agent_state.id}")

            except Exception as e:
                self.logger.error(f"Error loading agents from database: {e}")
                # 繼續使用記憶體中的 agents

        # 返回所有 agents (記憶體中的)
        agents_list = []
        for agent in self._agents.values():
            agent_dict = self._agent_to_dict(agent)
            agents_list.append(agent_dict)
        return agents_list

    def list_agent_ids(self) -> list[str]:
        """列出所有 Agent ID"""
        return list(self._agents.keys())

    def get_agent_states(self) -> dict[str, AgentState]:
        """獲取所有 Agent 狀態"""
        return {agent_id: agent.state for agent_id, agent in self._agents.items()}

    def _agent_to_dict(self, agent: CasualTradingAgent) -> dict[str, Any]:
        """Convert agent to dictionary for API response."""

        # Determine runtime status
        agent_id = agent.agent_id
        if agent_id in self._active_executions:
            runtime_status = "running"
        elif agent.is_active:
            runtime_status = "idle"
        else:
            runtime_status = "stopped"

        # Update runtime status cache
        self._runtime_status[agent_id] = runtime_status

        return {
            "id": agent.agent_id,
            "name": agent.config.name,
            "description": agent.config.description,
            "ai_model": agent.config.ai_model,
            "strategy_type": agent.config.investment_preferences.strategy_type,
            "strategy_prompt": agent.config.instructions,
            "current_mode": str(agent.state.current_mode.value),
            "status": str(
                agent.state.status.value
            ),  # persistent status (active/inactive/error/suspended)
            "runtime_status": runtime_status,  # runtime status (idle/running/stopped)
            "initial_funds": float(agent.config.initial_funds),
            "current_funds": float(agent.config.current_funds or agent.config.initial_funds),
            "max_turns": agent.config.max_turns,
            "risk_tolerance": agent.config.investment_preferences.risk_tolerance_to_float(
                agent.config.investment_preferences.risk_tolerance
            ),
            "enabled_tools": agent.config.enabled_tools,
            "investment_preferences": {
                "preferred_sectors": agent.config.investment_preferences.preferred_sectors,
                "excluded_stocks": agent.config.investment_preferences.excluded_tickers,
                "max_position_size": agent.config.investment_preferences.max_position_size,
                "rebalance_frequency": "weekly",  # Default value
            },
            "custom_instructions": agent.config.additional_instructions,
            "color_theme": agent.config.color_theme,  # 添加 color_theme 字段
            "created_at": agent.state.created_at,
            "updated_at": agent.state.updated_at,
            "portfolio": None,
            "performance": None,
        }

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

        # 檢查並發限制：每次執行 async with semaphore: 時，計數器減一，直到為零時，新的協程會被暫停（等待），直到有其他協程釋放（離開 with 區塊，計數器加一
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
                        lambda task: self._handle_async_execution_completion(agent_id, task)
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
                self.logger.info(f"Async execution for agent {agent_id} completed: {result.status}")
        except Exception as e:
            self.logger.error(f"Error handling async execution completion: {e}")

    def _record_execution_result(self, agent_id: str, result: AgentExecutionResult) -> None:
        """記錄執行結果"""
        if agent_id in self._execution_history:
            self._execution_history[agent_id].append(result)

            # 限制歷史記錄數量
            max_history = 100
            if len(self._execution_history[agent_id]) > max_history:
                self._execution_history[agent_id] = self._execution_history[agent_id][-max_history:]

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
        active_agents = [agent_id for agent_id, agent in self._agents.items() if agent.is_active]

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

    async def start_agent(
        self,
        agent_id: str,
        max_cycles: int | None = None,
        stop_loss_threshold: float | None = None,
    ) -> None:
        """
        啟動並執行指定 Agent

        Args:
            agent_id: Agent ID
            max_cycles: 最大執行週期數
            stop_loss_threshold: 停損閾值

        Raises:
            ValueError: Agent 不存在
            RuntimeError: Agent 無法啟動
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        # 確保 Agent 已初始化
        if not agent.is_active:
            await agent.initialize()

            # 同步狀態到資料庫（Agent 已啟動為 ACTIVE）
            if self._database_service:
                try:
                    await self._database_service.save_agent_state(agent.state)
                    self.logger.info(f"Agent {agent_id} status updated in database: ACTIVE")
                except Exception as db_error:
                    self.logger.error(f"Failed to update agent status in database: {db_error}")

        # 更新配置（如果提供）
        if max_cycles is not None:
            agent.config.max_turns = max_cycles

        # 執行 Agent（非阻塞）
        await self.execute_agent(
            agent_id=agent_id,
            mode=None,  # 使用 Agent 當前模式
            wait_for_completion=False,  # 非阻塞執行
        )

        self.logger.info(
            f"Agent {agent_id} started with max_cycles={max_cycles}, "
            f"stop_loss_threshold={stop_loss_threshold}"
        )

    async def stop_agent(self, agent_id: str) -> None:
        """
        停止指定 Agent

        Args:
            agent_id: Agent ID

        Raises:
            ValueError: Agent 不存在
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        # 取消正在執行的任務
        await self._cancel_agent_executions(agent_id)

        # 關閉 Agent
        if agent.is_active:
            await agent.shutdown()

            # 同步狀態到資料庫（Agent 已停止為 INACTIVE）
            if self._database_service:
                try:
                    await self._database_service.save_agent_state(agent.state)
                    self.logger.info(f"Agent {agent_id} status updated in database: INACTIVE")
                except Exception as db_error:
                    self.logger.error(f"Failed to update agent status in database: {db_error}")

        self.logger.info(f"Agent {agent_id} stopped successfully")

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
                    self.logger.debug(f"Active executions: {len(self._active_executions)}")

                # 等待下次檢查
                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"Error in execution monitoring: {e}")
                await asyncio.sleep(30)

    def get_execution_statistics(self) -> dict[str, Any]:
        """獲取執行統計資訊"""
        total_executions = sum(len(history) for history in self._execution_history.values())

        agent_stats = {}
        for agent_id, agent in self._agents.items():
            agent_stats[agent_id] = agent.get_performance_summary()

        return {
            "total_agents": self.agent_count,
            "active_agents": self.active_agent_count,
            "active_executions": len(self._active_executions),
            "max_concurrent_executions": self._max_concurrent_executions,
            "available_execution_slots": self._max_concurrent_executions
            - len(self._active_executions),
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
    async def agent_execution_context(self, agent_id: str) -> AsyncIterator[CasualTradingAgent]:
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

    # ==========================================
    # Trading Data Access Methods
    # ==========================================

    async def get_portfolio(self, agent_id: str) -> dict[str, Any]:
        """
        獲取 Agent 的投資組合

        Args:
            agent_id: Agent ID

        Returns:
            投資組合資訊
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        # Try to get portfolio from persistent agent if available
        if hasattr(agent, "get_portfolio_history"):
            return await agent.get_portfolio_history()

        # Otherwise return basic portfolio info from agent state
        portfolio_data = {
            "cash": float(agent.config.current_funds or agent.config.initial_funds),
            "holdings": [],
            "total_value": float(agent.config.current_funds or agent.config.initial_funds),
            "total_cost": float(agent.config.initial_funds),
            "unrealized_pnl": 0.0,
            "unrealized_pnl_percent": 0.0,
        }

        # Get holdings from database if available
        if hasattr(agent, "db_service") and agent.db_service:
            try:
                holdings = await agent.db_service.get_agent_holdings(agent_id)
                portfolio_data["holdings"] = [
                    {
                        "ticker": h.ticker,
                        "quantity": int(h.quantity),
                        "average_cost": float(h.average_cost),
                        "current_price": float(h.current_price or h.average_cost),
                        "market_value": float(h.quantity * (h.current_price or h.average_cost)),
                        "unrealized_pnl": float(
                            h.quantity * ((h.current_price or h.average_cost) - h.average_cost)
                        ),
                        "weight": 0.0,  # Will be calculated
                    }
                    for h in holdings
                ]

                # Calculate total market value and weights
                total_market_value = sum(h["market_value"] for h in portfolio_data["holdings"])
                portfolio_data["total_value"] = portfolio_data["cash"] + total_market_value

                # Calculate weights
                if portfolio_data["total_value"] > 0:
                    for holding in portfolio_data["holdings"]:
                        holding["weight"] = holding["market_value"] / portfolio_data["total_value"]

                # Calculate total unrealized PnL
                total_unrealized_pnl = sum(h["unrealized_pnl"] for h in portfolio_data["holdings"])
                portfolio_data["unrealized_pnl"] = total_unrealized_pnl
                portfolio_data["unrealized_pnl_percent"] = (
                    (total_unrealized_pnl / portfolio_data["total_cost"] * 100)
                    if portfolio_data["total_cost"] > 0
                    else 0.0
                )

            except Exception as e:
                self.logger.error(f"Error fetching holdings from database: {e}")

        return portfolio_data

    async def get_trades(
        self, agent_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        獲取 Agent 的交易歷史

        Args:
            agent_id: Agent ID
            limit: 返回數量限制
            offset: 偏移量

        Returns:
            交易記錄列表
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        # Try to get trades from database
        if hasattr(agent, "db_service") and agent.db_service:
            try:
                transactions = await agent.db_service.get_agent_transactions(
                    agent_id=agent_id, limit=limit, offset=offset
                )

                return [
                    {
                        "id": t.id,
                        "ticker": t.ticker,
                        "action": t.action,
                        "quantity": int(t.quantity),
                        "price": float(t.price),
                        "total_amount": float(t.total_amount),
                        "fee": float(t.fee or 0),
                        "tax": float(t.tax or 0),
                        "status": t.status,
                        "executed_at": (t.executed_at.isoformat() if t.executed_at else None),
                        "session_id": t.session_id,
                    }
                    for t in transactions
                ]

            except Exception as e:
                self.logger.error(f"Error fetching trades from database: {e}")
                return []

        # Return empty list if no database service
        return []

    async def get_strategy_changes(
        self, agent_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        獲取 Agent 的策略變更歷史

        Args:
            agent_id: Agent ID
            limit: 返回數量限制
            offset: 偏移量

        Returns:
            策略變更記錄列表
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        # Try to get strategy changes from database
        if hasattr(agent, "db_service") and agent.db_service:
            try:
                changes = await agent.db_service.get_strategy_changes(
                    agent_id=agent_id, limit=limit, offset=offset
                )

                return [
                    {
                        "id": c.id,
                        "change_type": c.change_type,
                        "old_strategy": c.old_strategy,
                        "new_strategy": c.new_strategy,
                        "reason": c.reason,
                        "performance_before": c.performance_before,
                        "performance_after": c.performance_after,
                        "changed_at": (c.changed_at.isoformat() if c.changed_at else None),
                        "applied": c.applied,
                    }
                    for c in changes
                ]

            except Exception as e:
                self.logger.error(f"Error fetching strategy changes from database: {e}")
                return []

        # Try to get from agent's strategy tracker
        if hasattr(agent, "get_strategy_changes"):
            try:
                changes = agent.get_strategy_changes()
                return changes[-limit:] if limit > 0 else changes
            except Exception as e:
                self.logger.error(f"Error getting strategy changes from agent: {e}")

        return []

    async def get_performance(self, agent_id: str) -> dict[str, Any]:
        """
        獲取 Agent 的績效指標

        Args:
            agent_id: Agent ID

        Returns:
            績效指標
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]

        # Get basic metrics from agent config
        initial_funds = float(agent.config.initial_funds)
        current_funds = float(agent.config.current_funds or agent.config.initial_funds)

        # Start with basic metrics
        performance = {
            "initial_funds": initial_funds,
            "current_funds": current_funds,
            "total_return": current_funds - initial_funds,
            "total_return_percent": (
                ((current_funds - initial_funds) / initial_funds * 100)
                if initial_funds > 0
                else 0.0
            ),
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": None,
        }

        # Try to get additional performance metrics from agent
        try:
            if hasattr(agent, "get_performance_analytics"):
                analytics = await agent.get_performance_analytics()
                # Merge analytics with basic performance
                performance.update(analytics)
            elif hasattr(agent, "get_performance_summary"):
                summary = agent.get_performance_summary()
                # Merge summary but keep initial_funds and current_funds
                for key, value in summary.items():
                    if key not in ["initial_funds", "current_funds"]:
                        performance[key] = value
        except Exception as e:
            self.logger.error(f"Error getting additional performance metrics: {e}")

        return performance

    async def update_agent_config(self, agent_id: str, config_updates: dict[str, Any]) -> None:
        """
        更新 Agent 配置

        Args:
            agent_id: Agent ID
            config_updates: 配置更新數據

        Raises:
            ValueError: Agent 不存在
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]
        config_changed = False

        # 更新基本配置
        if "name" in config_updates:
            agent.config.name = config_updates["name"]
            config_changed = True

        if "description" in config_updates:
            agent.config.description = config_updates["description"]
            config_changed = True

        if "strategy_prompt" in config_updates:
            agent.config.instructions = config_updates["strategy_prompt"]
            config_changed = True

        if "custom_instructions" in config_updates:
            agent.config.additional_instructions = config_updates["custom_instructions"]
            config_changed = True

        if "color_theme" in config_updates:
            agent.config.color_theme = config_updates["color_theme"]
            config_changed = True

        if "ai_model" in config_updates:
            agent.config.ai_model = config_updates["ai_model"]
            config_changed = True

        # 更新風險容忍度
        if "risk_tolerance" in config_updates:
            from .models import InvestmentPreferences

            risk_category = InvestmentPreferences.risk_tolerance_from_float(
                config_updates["risk_tolerance"]
            )
            agent.config.investment_preferences.risk_tolerance = risk_category
            config_changed = True

        # 更新工具配置
        if "enabled_tools" in config_updates:
            agent.config.enabled_tools = config_updates["enabled_tools"]
            config_changed = True

        # 更新投資偏好
        if "investment_preferences" in config_updates:
            prefs_data = config_updates["investment_preferences"]
            if "preferred_sectors" in prefs_data:
                agent.config.investment_preferences.preferred_sectors = prefs_data[
                    "preferred_sectors"
                ]
                config_changed = True
            if "excluded_tickers" in prefs_data:
                agent.config.investment_preferences.excluded_tickers = prefs_data[
                    "excluded_tickers"
                ]
                config_changed = True
            if "max_position_size" in prefs_data:
                agent.config.investment_preferences.max_position_size = prefs_data[
                    "max_position_size"
                ]
                config_changed = True

        # 如果配置有變更，同步到狀態並保存
        if config_changed:
            await self._sync_config_to_state_and_persist(agent)

        self.logger.info(f"Agent {agent_id} configuration updated")

    async def update_agent_state(self, agent_id: str, state_updates: dict[str, Any]) -> None:
        """
        更新 Agent 狀態

        Args:
            agent_id: Agent ID
            state_updates: 狀態更新數據

        Raises:
            ValueError: Agent 不存在
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]
        state_changed = False

        # 更新狀態欄位
        if "name" in state_updates:
            agent.state.name = state_updates["name"]
            state_changed = True

        # 如果狀態有變更，保存到資料庫
        if state_changed:
            agent.state.update_activity()
            await self._persist_agent_state(agent)

        self.logger.info(f"Agent {agent_id} state updated")

    async def update_agent(self, agent_id: str, update_data: dict[str, Any]) -> None:
        """
        更新 Agent（配置和狀態的統一入口）

        Args:
            agent_id: Agent ID
            update_data: 更新數據字典

        Raises:
            ValueError: Agent 不存在
        """
        # 分離配置更新和狀態更新
        config_updates = {}
        state_updates = {}

        # 配置相關的更新
        config_fields = {
            "description",
            "strategy_prompt",
            "custom_instructions",
            "color_theme",
            "ai_model",
            "risk_tolerance",
            "enabled_tools",
            "investment_preferences",
        }

        # name 比較特殊，需要同時更新配置和狀態
        if "name" in update_data:
            config_updates["name"] = update_data["name"]
            state_updates["name"] = update_data["name"]

        # 分類其他更新
        for key, value in update_data.items():
            if key in config_fields:
                config_updates[key] = value

        # 執行更新
        if config_updates:
            await self.update_agent_config(agent_id, config_updates)

        if state_updates:
            await self.update_agent_state(agent_id, state_updates)

    async def _sync_config_to_state_and_persist(self, agent: CasualTradingAgent) -> None:
        """
        同步配置到狀態並持久化

        Args:
            agent: Agent 實例
        """
        # 確保 state 中的 config 是最新的（雖然通常是同一個物件引用）
        agent.state.config = agent.config

        # 更新時間戳
        agent.state.update_activity()

        # 持久化到資料庫
        await self._persist_agent_state(agent)

    async def _persist_agent_state(self, agent: CasualTradingAgent) -> None:
        """
        持久化 Agent 狀態到資料庫

        Args:
            agent: Agent 實例
        """
        if self._database_service:
            try:
                await self._database_service.save_agent_state(agent.state)
                self.logger.debug(f"Agent {agent.agent_id} persisted to database")
            except Exception as e:
                self.logger.error(f"Failed to persist agent {agent.agent_id} to database: {e}")
                raise

    async def update_agent_mode(
        self, agent_id: str, new_mode: AgentMode, reason: str = "", trigger: str = ""
    ) -> None:
        """
        更新 Agent 交易模式

        Args:
            agent_id: Agent ID
            new_mode: 新的交易模式
            reason: 模式變更原因
            trigger: 觸發模式變更的事件

        Raises:
            ValueError: Agent 不存在
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self._agents[agent_id]
        old_mode = agent.state.current_mode

        # 更新模式
        agent.state.current_mode = new_mode
        agent.state.update_activity()

        # 記錄模式變更
        self.logger.info(
            f"Agent {agent_id} mode changed from {old_mode.value} to {new_mode.value}. "
            f"Reason: {reason}, Trigger: {trigger}"
        )

        # 同步狀態到資料庫
        if self._database_service:
            try:
                await self._database_service.save_agent_state(agent.state)
                self.logger.info(f"Agent {agent_id} mode updated in database")
            except Exception as e:
                self.logger.error(f"Failed to save agent mode change to database: {e}")

        # TODO: 記錄模式變更歷史到資料庫
        # if self._database_service and hasattr(self._database_service, 'log_mode_change'):
        #     try:
        #         await self._database_service.log_mode_change(
        #             agent_id=agent_id,
        #             old_mode=old_mode.value,
        #             new_mode=new_mode.value,
        #             reason=reason,
        #             trigger=trigger
        #         )
        #     except Exception as e:
        #         self.logger.error(f"Failed to log mode change: {e}")

        self.logger.info(f"Agent {agent_id} mode successfully updated to {new_mode.value}")
