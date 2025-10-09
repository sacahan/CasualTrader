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
        # Auto-start Agent Manager if not running
        if not self._is_running:
            self.logger.warning("Agent Manager not running, starting automatically...")
            await self.start()

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

        return {
            "id": agent.agent_id,
            "name": agent.config.name,
            "description": agent.config.description,
            "ai_model": agent.config.model,
            "strategy_type": agent.config.investment_preferences.strategy_type,
            "strategy_prompt": agent.config.instructions,
            "current_mode": str(agent.state.current_mode.value),
            "status": str(agent.state.status.value),
            "initial_funds": float(agent.config.initial_funds),
            "current_funds": float(
                agent.config.current_funds or agent.config.initial_funds
            ),
            "max_turns": agent.config.max_turns,
            "risk_tolerance": agent.config.investment_preferences.risk_tolerance_to_float(
                agent.config.investment_preferences.risk_tolerance
            ),
            "enabled_tools": agent.config.enabled_tools,
            "investment_preferences": {
                "preferred_sectors": agent.config.investment_preferences.preferred_sectors,
                "excluded_stocks": agent.config.investment_preferences.excluded_symbols,
                "max_position_size": agent.config.investment_preferences.max_position_size
                / 100,  # Convert back to 0-1 range
                "rebalance_frequency": "weekly",  # Default value
            },
            "custom_instructions": agent.config.additional_instructions,
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
            "total_value": float(
                agent.config.current_funds or agent.config.initial_funds
            ),
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
                        "symbol": h.symbol,
                        "quantity": int(h.quantity),
                        "average_cost": float(h.average_cost),
                        "current_price": float(h.current_price or h.average_cost),
                        "market_value": float(
                            h.quantity * (h.current_price or h.average_cost)
                        ),
                        "unrealized_pnl": float(
                            h.quantity
                            * ((h.current_price or h.average_cost) - h.average_cost)
                        ),
                        "weight": 0.0,  # Will be calculated
                    }
                    for h in holdings
                ]

                # Calculate total market value and weights
                total_market_value = sum(
                    h["market_value"] for h in portfolio_data["holdings"]
                )
                portfolio_data["total_value"] = (
                    portfolio_data["cash"] + total_market_value
                )

                # Calculate weights
                if portfolio_data["total_value"] > 0:
                    for holding in portfolio_data["holdings"]:
                        holding["weight"] = (
                            holding["market_value"] / portfolio_data["total_value"]
                        )

                # Calculate total unrealized PnL
                total_unrealized_pnl = sum(
                    h["unrealized_pnl"] for h in portfolio_data["holdings"]
                )
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
                        "symbol": t.symbol,
                        "action": t.action,
                        "quantity": int(t.quantity),
                        "price": float(t.price),
                        "total_amount": float(t.total_amount),
                        "fee": float(t.fee or 0),
                        "tax": float(t.tax or 0),
                        "status": t.status,
                        "executed_at": (
                            t.executed_at.isoformat() if t.executed_at else None
                        ),
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
                        "changed_at": c.changed_at.isoformat()
                        if c.changed_at
                        else None,
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
