"""
TradingService - 交易服務層

提供 Agent 單一模式執行的服務（手動觸發設計）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from trading.trading_agent import TradingAgent
from service.agents_service import AgentsService, AgentNotFoundError
from common.enums import AgentMode, AgentStatus, SessionStatus
from common.logger import logger
from service.session_service import AgentSessionService


# ==========================================
# Custom Exceptions
# ==========================================


class TradingServiceError(Exception):
    """TradingService 基礎錯誤"""

    pass


class AgentBusyError(TradingServiceError):
    """Agent 正在執行中"""

    pass


class InvalidOperationError(TradingServiceError):
    """無效操作"""

    pass


# ==========================================
# TradingService
# ==========================================


class TradingService:
    """
    交易服務層

    提供單一模式執行功能（手動觸發）：
    - 執行指定模式並完成後立即返回
    - 資源清理（finally 塊確保）
    - 會話管理
    """

    def __init__(self, db_session: AsyncSession):
        """
        初始化 TradingService

        Args:
            db_session: SQLAlchemy 異步 session
        """
        self.db_session = db_session
        self.agents_service = AgentsService(db_session)
        self.session_service = AgentSessionService(db_session)

        # 活躍的 TradingAgent 實例（記憶體中）
        self.active_agents: dict[str, TradingAgent] = {}

        logger.info("TradingService initialized")

    async def execute_single_mode(
        self,
        agent_id: str,
        mode: AgentMode,
        max_turns: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        執行單一模式（執行完後立即返回，不再循環轉換）

        Args:
            agent_id: Agent ID
            mode: 執行模式 (TRADING/REBALANCING)
            max_turns: 最大輪數（可選）
            session_id: 既存的 session ID（可選）。如果提供，使用該 session 而不創建新的

        Returns:
            執行結果：
            {
                "success": bool,
                "session_id": str,
                "mode": str,
                "execution_time_ms": int,
                "output": str (可選),
                "error": str (如果失敗)
            }

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentBusyError: Agent 正在執行中
            TradingServiceError: 執行失敗
        """
        start_time = datetime.now()
        agent = None

        try:
            # 1. 檢查 Agent 是否存在
            agent_config = await self.agents_service.get_agent_config(agent_id)

            # 2. 檢查 Agent 是否已在執行
            if agent_id in self.active_agents:
                raise AgentBusyError(f"Agent {agent_id} is already running")

            # 3. 取得或創建執行會話
            if session_id:
                # 使用既存的 session（由 API 層創建）
                session = await self.session_service.get_session(session_id)
                logger.info(f"Using existing session {session_id} for agent {agent_id}")
            else:
                # 創建新會話（直接調用服務層時使用）
                session = await self.session_service.create_session(
                    agent_id=agent_id,
                    mode=mode,
                    initial_input={},
                )
                session_id = session.id
                logger.info(
                    f"🆕 Created session {session_id} for agent {agent_id} ({mode.value}) 🎯"
                )

            # 4. 更新會Session狀態為 RUNNING
            await self.session_service.update_session_status(session_id, SessionStatus.RUNNING)

            # 5. 取得或創建 TradingAgent 實例
            agent = await self._get_or_create_agent(agent_id, agent_config)

            # 6. 標記為活躍
            self.active_agents[agent_id] = agent

            # 7. 初始化 Agent（載入工具、Sub-agents 等）
            logger.info(f"Initializing agent {agent_id}")
            await agent.initialize()

            # 8. 執行指定模式
            logger.info(f"Executing {mode.value} for agent {agent_id}")
            result = await agent.run(mode=mode)

            # 9. 更新會話狀態為 COMPLETED
            await self.session_service.update_session_status(session_id, SessionStatus.COMPLETED)

            # 10. 更新 Agent 狀態為 INACTIVE（執行完成）
            await self.agents_service.update_agent_status(agent_id, status=AgentStatus.INACTIVE)

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info(
                f"✅ Completed {mode.value} for agent {agent_id} in {execution_time_ms}ms 🚀"
            )

            return {
                "success": True,
                "session_id": session_id,
                "mode": mode.value,
                "execution_time_ms": execution_time_ms,
                "output": result.get("output") if result else None,
            }

        except AgentNotFoundError:
            raise
        except AgentBusyError:
            raise
        except Exception as e:
            logger.error(f"Error executing {mode.value} for {agent_id}: {e}", exc_info=True)

            # 更新會話狀態為 FAILED
            if session_id:
                try:
                    await self.session_service.update_session_status(
                        session_id, SessionStatus.FAILED, error_message=str(e)
                    )
                except Exception as cleanup_error:
                    logger.error(f"Error updating session {session_id}: {cleanup_error}")

            # 更新 Agent 狀態為 INACTIVE（即使執行失敗）
            await self.agents_service.update_agent_status(agent_id, status=AgentStatus.INACTIVE)

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            raise TradingServiceError(f"Failed to execute {mode.value}: {str(e)}") from e

        finally:
            # 確保資源清理（即使發生異常）
            if agent_id in self.active_agents:
                try:
                    if agent is not None:
                        await agent.cleanup()
                    logger.debug(f"Cleaned up agent {agent_id}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up agent {agent_id}: {cleanup_error}")
                finally:
                    del self.active_agents[agent_id]

    async def stop_agent(self, agent_id: str) -> dict[str, Any]:
        """
        停止 Agent 正在執行的任務

        Args:
            agent_id: Agent ID

        Returns:
            停止結果：
            {
                "success": bool,
                "status": "stopped" | "not_running"
            }

        Raises:
            AgentNotFoundError: Agent 不存在
            TradingServiceError: 停止失敗
        """
        try:
            # 檢查 Agent 是否存在
            await self.agents_service.get_agent_config(agent_id)

            # 檢查是否有正在執行的 agent
            if agent_id not in self.active_agents:
                return {
                    "success": True,
                    "status": "not_running",
                }

            # 取得 agent 並停止
            agent = self.active_agents[agent_id]
            try:
                await agent.cancel()
                logger.info(f"Cancelled agent {agent_id}")
            except Exception as e:
                logger.error(f"Error cancelling agent {agent_id}: {e}")

            # 清理
            try:
                await agent.cleanup()
                logger.debug(f"Cleaned up agent {agent_id}")
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_id}: {e}")
            finally:
                del self.active_agents[agent_id]

            # 更新 Agent 狀態為 INACTIVE（停止）
            await self.agents_service.update_agent_status(agent_id, status=AgentStatus.INACTIVE)

            return {
                "success": True,
                "status": "stopped",
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            raise TradingServiceError(f"Failed to stop agent: {str(e)}") from e

    # ==========================================
    # Atomic Trading Operations (Internal)
    # ==========================================

    async def execute_trade_atomic(
        self,
        agent_id: str,
        ticker: str,
        action: str,
        quantity: int,
        price: float,
        decision_reason: str | None = None,
        company_name: str | None = None,
    ) -> dict[str, Any]:
        """
        執行完整交易 - 原子操作

        所有操作在單一事務中，保證:
        - 全成功 → 提交所有變更
        - 任何失敗 → 回滾所有變更

        此方法管理整個事務生命週期。

        Args:
            agent_id: Agent ID
            ticker: 股票代號 (例如: "2330")
            action: 交易動作 ("BUY" 或 "SELL")
            quantity: 交易股數 (必須是 1000 的倍數)
            price: 交易價格
            decision_reason: 交易決策理由 (可選)
            company_name: 公司名稱 (可選)

        Returns:
            交易執行結果：
            {
                "success": bool,
                "transaction_id": str (如果成功),
                "message": str,
                "error": str (如果失敗)
            }

        Raises:
            TradingServiceError: 交易執行失敗（事務自動回滾）
        """
        try:
            # 參數驗證
            action_upper = action.upper()
            if action_upper not in ["BUY", "SELL"]:
                raise ValueError(f"無效的 action: {action}，必須是 'BUY' 或 'SELL'")

            if not isinstance(quantity, int) or quantity <= 0:
                raise ValueError(f"股數必須是正整數，收到: {quantity}")

            if quantity % 1000 != 0:
                raise ValueError(f"股數必須是 1000 的倍數，收到: {quantity}")

            logger.info(
                f"開始原子交易: agent_id={agent_id}, ticker={ticker}, "
                f"action={action_upper}, quantity={quantity}, price={price}"
            )

            # ⭐ 開始事務 - 所有操作在同一事務內
            async with self.db_session.begin():
                # Step 1: 驗證 Agent 存在
                agent_config = await self.agents_service.get_agent_config(agent_id)
                if not agent_config:
                    raise ValueError(f"Agent {agent_id} 不存在")

                # Step 2: 記錄交易到資料庫
                total_amount = float(quantity * price)
                commission = total_amount * 0.001425  # 假設手續費 0.1425%

                transaction = await self._create_transaction_internal(
                    agent_id=agent_id,
                    ticker=ticker,
                    action=action_upper,
                    quantity=quantity,
                    price=price,
                    total_amount=total_amount,
                    commission=commission,
                    decision_reason=decision_reason or "原子交易",
                    company_name=company_name,
                    status="COMPLETED",
                )
                logger.info(f"交易已記錄: {transaction.id}")

                # Step 3: 更新持股明細
                await self._update_agent_holdings_internal(
                    agent_id=agent_id,
                    ticker=ticker,
                    action=action_upper,
                    quantity=quantity,
                    price=price,
                    company_name=company_name,
                )
                logger.info("持股已更新")

                # Step 4: 更新資金餘額
                if action_upper == "BUY":
                    amount_change = -(total_amount + commission)
                else:  # SELL
                    amount_change = total_amount - commission

                await self._update_agent_funds_internal(
                    agent_id=agent_id,
                    amount_change=amount_change,
                    transaction_type=f"{action_upper} {ticker}",
                )
                logger.info(f"資金已更新: {amount_change:+.2f} 元")

                # Step 5: 更新績效指標
                await self._calculate_and_update_performance_internal(agent_id)
                logger.info("績效已更新")

                # ⭐ 事務自動提交（所有步驟都成功）
                logger.info("原子交易成功完成")

            return {
                "success": True,
                "transaction_id": transaction.id,
                "message": f"✅ 交易執行成功\n"
                f"• 股票: {ticker} ({company_name or '未知'})\n"
                f"• 類型: {action_upper}\n"
                f"• 股數: {quantity:,}\n"
                f"• 成交價: {price:,.2f}\n"
                f"• 手續費: {commission:,.2f}\n"
                f"• 實際成本: {total_amount + commission:,.2f}",
            }

        except Exception as e:
            # ⭐ 任何失敗 → 事務自動回滾
            logger.error(f"原子交易失敗，已完全回滾: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 交易執行失敗，已完全回滾\n❌ 錯誤: {str(e)}",
            }

    async def _create_transaction_internal(
        self,
        agent_id: str,
        ticker: str,
        action: str,
        quantity: int,
        price: float,
        total_amount: float,
        commission: float,
        decision_reason: str,
        company_name: str | None = None,
        status: str = "COMPLETED",
        session_id: str | None = None,
    ):
        """
        內部交易記錄方法（事務內使用）

        不會自動提交，由外層事務管理。

        Args:
            同 AgentsService.create_transaction

        Returns:
            Transaction 物件
        """
        from decimal import Decimal
        from database.models import Transaction
        from common.enums import TransactionAction, TransactionStatus
        import uuid

        action_enum = TransactionAction.BUY if action.upper() == "BUY" else TransactionAction.SELL
        status_enum = (
            TransactionStatus.EXECUTED
            if status.upper() == "EXECUTED"
            else TransactionStatus.PENDING
        )

        transaction = Transaction(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            ticker=ticker,
            company_name=company_name,
            action=action_enum,
            quantity=quantity,
            price=Decimal(str(price)),
            total_amount=Decimal(str(total_amount)),
            commission=Decimal(str(commission)),
            status=status_enum,
            session_id=session_id,
            execution_time=(datetime.now() if status_enum == TransactionStatus.EXECUTED else None),
            decision_reason=decision_reason,
        )

        self.db_session.add(transaction)
        return transaction

    async def _update_agent_holdings_internal(
        self,
        agent_id: str,
        ticker: str,
        action: str,
        quantity: int,
        price: float,
        company_name: str | None = None,
    ) -> None:
        """
        內部持股更新方法（事務內使用）

        不會自動提交，由外層事務管理。
        """
        from decimal import Decimal
        from database.models import AgentHolding
        from sqlalchemy import select

        # 查找現有持股
        stmt = select(AgentHolding).where(
            AgentHolding.agent_id == agent_id, AgentHolding.ticker == ticker
        )
        result = await self.db_session.execute(stmt)
        holding = result.scalar_one_or_none()

        if action.upper() == "BUY":
            if holding:
                # 更新現有持股
                new_quantity = holding.quantity + quantity
                new_total_cost = holding.total_cost + Decimal(str(quantity * price))
                new_average_cost = new_total_cost / new_quantity

                holding.quantity = new_quantity
                holding.total_cost = new_total_cost
                holding.average_cost = new_average_cost
                holding.updated_at = datetime.now()
            else:
                # 創建新持股
                total_cost = Decimal(str(quantity * price))
                holding = AgentHolding(
                    agent_id=agent_id,
                    ticker=ticker,
                    company_name=company_name,
                    quantity=quantity,
                    average_cost=Decimal(str(price)),
                    total_cost=total_cost,
                )
                self.db_session.add(holding)

        elif action.upper() == "SELL":
            if not holding:
                raise TradingServiceError(f"Cannot sell {ticker}: no holdings found")

            if holding.quantity < quantity:
                raise TradingServiceError(
                    f"Cannot sell {quantity} shares of {ticker}: "
                    f"only {holding.quantity} shares available"
                )

            # 更新持股
            holding.quantity -= quantity
            if holding.quantity == 0:
                # 完全賣出，刪除持股記錄
                await self.db_session.delete(holding)
            else:
                # 部分賣出，更新成本
                holding.total_cost = holding.average_cost * holding.quantity
                holding.updated_at = datetime.now()

    async def _update_agent_funds_internal(
        self,
        agent_id: str,
        amount_change: float,
        transaction_type: str,
    ) -> None:
        """
        內部資金更新方法（事務內使用）

        不會自動提交，由外層事務管理。
        """
        from decimal import Decimal
        from database.models import Agent
        from sqlalchemy import select

        stmt = select(Agent).where(Agent.id == agent_id)
        result = await self.db_session.execute(stmt)
        agent = result.scalar_one_or_none()

        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found")

        current_funds = agent.current_funds or agent.initial_funds
        new_funds = float(current_funds) + amount_change

        if new_funds < 0:
            raise TradingServiceError(
                f"Insufficient funds: current={current_funds}, required={-amount_change}"
            )

        agent.current_funds = Decimal(str(new_funds))

        # 更新時間戳記
        agent.updated_at = datetime.now()
        agent.last_active_at = datetime.now()

        logger.info(
            f"Updated funds for agent {agent_id}: {current_funds} -> {new_funds} ({transaction_type})"
        )

    async def _calculate_and_update_performance_internal(self, agent_id: str) -> None:
        """
        內部績效更新方法（事務內使用）

        不會自動提交，由外層事務管理。
        """
        from decimal import Decimal
        from database.models import AgentPerformance, Transaction
        from common.enums import TransactionAction, TransactionStatus
        from sqlalchemy import select, func, case
        from datetime import date

        # 取得 Agent 配置
        agent = await self.agents_service.get_agent_config(agent_id)

        # 取得持股明細
        holdings = await self.agents_service.get_agent_holdings(agent_id)

        # 計算股票市值
        stocks_value = sum(holding.quantity * holding.average_cost for holding in holdings)

        # 計算現金餘額
        cash_balance = agent.current_funds or agent.initial_funds

        # 計算總資產價值
        total_value = Decimal(str(cash_balance)) + stocks_value

        # 取得交易統計
        stmt_transactions = (
            select(
                func.count(Transaction.id).label("total_trades"),
                func.sum(case((Transaction.action == TransactionAction.SELL, 1), else_=0)).label(
                    "completed_trades"
                ),
            )
            .where(Transaction.agent_id == agent_id)
            .where(Transaction.status == TransactionStatus.EXECUTED)
        )

        result = await self.db_session.execute(stmt_transactions)
        trade_stats = result.first()

        total_trades = trade_stats.total_trades or 0
        completed_trades = trade_stats.completed_trades or 0

        # 計算總回報率
        total_return = (
            (total_value - agent.initial_funds) / agent.initial_funds
            if agent.initial_funds > 0
            else Decimal("0")
        )

        # 計算勝率
        win_rate = (
            Decimal(str(completed_trades / total_trades * 100))
            if total_trades > 0
            else Decimal("0")
        )

        # 查找今日績效記錄
        today = date.today()
        stmt_performance = select(AgentPerformance).where(
            AgentPerformance.agent_id == agent_id, AgentPerformance.date == today
        )
        result = await self.db_session.execute(stmt_performance)
        performance = result.scalar_one_or_none()

        if performance:
            # 更新現有記錄
            performance.total_value = total_value
            performance.cash_balance = Decimal(str(cash_balance))
            performance.total_return = total_return
            performance.win_rate = win_rate
            performance.total_trades = total_trades
            performance.winning_trades = completed_trades
            performance.updated_at = datetime.now()
        else:
            # 創建新記錄
            performance = AgentPerformance(
                agent_id=agent_id,
                date=today,
                total_value=total_value,
                cash_balance=Decimal(str(cash_balance)),
                unrealized_pnl=Decimal("0"),
                realized_pnl=Decimal("0"),
                total_return=total_return,
                win_rate=win_rate,
                total_trades=total_trades,
                winning_trades=completed_trades,
            )
            self.db_session.add(performance)

        logger.info(f"Updated performance for agent {agent_id}: total_value={total_value}")

    async def _get_or_create_agent(
        self,
        agent_id: str,
        agent_config: Any,
    ) -> TradingAgent:
        """
        獲取或創建 TradingAgent 實例

        Args:
            agent_id: Agent ID
            agent_config: Agent 配置

        Returns:
            TradingAgent 實例

        Raises:
            TypeError: 如果 agents_service 類型不正確
        """
        # 防禦性驗證 - 確保依賴注入正確
        if not isinstance(self.agents_service, AgentsService):
            raise TypeError(
                f"agents_service must be AgentsService instance, "
                f"got {type(self.agents_service).__name__}"
            )

        if agent_id in self.active_agents:
            return self.active_agents[agent_id]

        logger.debug(f"Creating TradingAgent for {agent_id}")
        agent = TradingAgent(agent_id, agent_config, self.agents_service)
        self.active_agents[agent_id] = agent
        return agent

    async def cleanup(self) -> None:
        """清理所有活躍 agent"""
        logger.info(f"Cleaning up {len(self.active_agents)} active agents")

        for agent_id, agent in self.active_agents.items():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_id}: {e}")

        self.active_agents.clear()
