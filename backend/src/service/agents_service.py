"""
Agent 資料庫服務層

提供 Agent 配置的 CRUD 操作和錯誤處理
基於 POC 實作，增強功能和錯誤處理
"""

from __future__ import annotations

import json
from typing import Any
from decimal import Decimal
from datetime import datetime, date
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import (
    Agent,
    Transaction,
    AgentHolding,
    AgentPerformance,
    AIModelConfig,
)
from common.enums import (
    AgentMode,
    AgentStatus,
    TransactionAction,
    TransactionStatus,
    validate_agent_mode,
    validate_agent_status,
)
from common.logger import logger


# ==========================================
# Custom Exceptions
# ==========================================


class AgentNotFoundError(Exception):
    """Agent 不存在於資料庫"""

    pass


class AgentConfigurationError(Exception):
    """Agent 配置錯誤"""

    pass


class AgentDatabaseError(Exception):
    """資料庫操作錯誤"""

    pass


# ==========================================
# Agents Service
# ==========================================


class AgentsService:
    """
    Agents 資料庫服務

    提供 Agents 配置的完整 CRUD 操作
    """

    def __init__(self, session: AsyncSession):
        """
        初始化 Agents 資料庫服務

        Args:
            session: SQLAlchemy 異步 Session
        """
        self.session = session

    # ==========================================
    # Query Operations
    # ==========================================

    async def get_agent_config(self, agent_id: str) -> Agent:
        """
        載入 Agents 配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent 模型實例

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentConfigurationError: 配置格式錯誤
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found in database")

            # 驗證必要欄位
            self._validate_agent_config(agent)

            logger.info(f"Loaded agent config: {agent_id} (model: {agent.ai_model})")
            return agent

        except AgentNotFoundError:
            raise
        except AgentConfigurationError:
            raise
        except Exception as e:
            logger.error(f"Database error loading agent {agent_id}: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to load agent config: {str(e)}")

    async def get_agent_with_holdings(self, agent_id: str) -> Agent:
        """
        載入 Agents 配置和持倉資料

        Args:
            agent_id: Agent ID

        Returns:
            Agent 模型實例（包含 holdings 關聯）

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id).options(selectinload(Agent.holdings))
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found")

            logger.info(f"Loaded agent with {len(agent.holdings)} holdings: {agent_id}")
            return agent

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Database error loading agent with holdings: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to load agent with holdings: {str(e)}")

    async def list_agents(self) -> list[Agent]:
        """
        取得所有的 Agents

        Returns:
            Agent 列表

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            logger.debug("Executing list_agents query")
            stmt = select(Agent)
            result = await self.session.execute(stmt)
            agents = list(result.scalars().all())

            logger.info(f"Found {len(agents)} active agents in database")

            # 驗證 agents 的完整性
            if agents:
                for agent in agents:
                    logger.debug(
                        f"Agent retrieved: {agent.id}",
                        extra={
                            "agent_id": agent.id,
                            "agent_name": agent.name,
                            "has_investment_prefs": bool(agent.investment_preferences),
                        },
                    )

            return agents

        except Exception as e:
            logger.error(f"Database error listing active agents: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to list active agents: {str(e)}")

    async def list_agents_by_status(self, status: AgentStatus) -> list[Agent]:
        """
        取得指定狀態的 Agents

        Args:
            status: Agent 狀態

        Returns:
            Agent 列表

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.status == status)
            result = await self.session.execute(stmt)
            agents = list(result.scalars().all())

            logger.info(f"Found {len(agents)} agents with status {status.value}")
            return agents

        except Exception as e:
            logger.error(f"Database error listing agents by status: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to list agents by status: {str(e)}")

    # ==========================================
    # AI Model Operations
    # ==========================================

    async def list_ai_models(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        """
        取得 AI 模型列表

        Args:
            enabled_only: 是否只返回已啟用的模型

        Returns:
            AI 模型配置列表（按 display_order 排序）

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(AIModelConfig).order_by(AIModelConfig.display_order)

            if enabled_only:
                stmt = stmt.where(AIModelConfig.is_enabled)

            result = await self.session.execute(stmt)
            models = list(result.scalars().all())

            # 轉換為字典格式
            model_list = [
                {
                    "model_key": model.model_key,
                    "display_name": model.display_name,
                    "provider": model.provider,
                    "group_name": model.group_name,
                    "model_type": model.model_type,
                    "litellm_prefix": model.litellm_prefix,
                    "api_key_env_var": model.api_key_env_var,
                    "display_order": model.display_order,
                }
                for model in models
            ]

            logger.info(f"Found {len(model_list)} AI models (enabled_only={enabled_only})")
            return model_list

        except Exception as e:
            logger.error(f"Database error listing AI models: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to list AI models: {str(e)}")

    async def get_ai_model_config(self, model_key: str) -> dict[str, Any] | None:
        """
        根據 model_key 取得 AI 模型配置

        Args:
            model_key: 模型唯一識別碼

        Returns:
            AI 模型配置字典，若不存在則返回 None

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(AIModelConfig).where(
                AIModelConfig.model_key == model_key, AIModelConfig.is_enabled
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                logger.warning(f"AI model '{model_key}' not found or not enabled")
                return None

            # 轉換為字典格式
            model_config = {
                "model_key": model.model_key,
                "display_name": model.display_name,
                "provider": model.provider,
                "group_name": model.group_name,
                "model_type": model.model_type
                if isinstance(model.model_type, str)
                else model.model_type.value,
                "litellm_prefix": model.litellm_prefix,
                "api_key_env_var": model.api_key_env_var,
                "display_order": model.display_order,
            }

            logger.info(f"Loaded AI model config: {model_key}")
            return model_config

        except Exception as e:
            logger.error(f"Database error getting AI model config: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to get AI model config: {str(e)}")

    # ==========================================
    # Create Operations
    # ==========================================

    async def create_agent(
        self,
        name: str,
        description: str,
        ai_model: str,
        initial_funds: float,
        max_position_size: float = 50.0,
        color_theme: str = "34, 197, 94",
        investment_preferences: list[str] | None = None,
    ) -> Agent:
        """
        創建新 Agent

        Args:
            name: Agent 名稱
            description: Agent 描述
            ai_model: AI 模型名稱
            initial_funds: 初始資金
            max_position_size: 最大持倉比例 (%)
            color_theme: 顏色主題 (RGB 格式)
            investment_preferences: 投資偏好列表

        Returns:
            創建的 Agent 實例

        Raises:
            AgentConfigurationError: 配置錯誤
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 生成 Agent ID
            agent_id = f"agent-{str(uuid.uuid4())[:8]}"

            # 轉換投資偏好為 JSON 字串
            preferences_json = None
            if investment_preferences:
                import json

                preferences_json = json.dumps(investment_preferences, ensure_ascii=False)

            # 創建 Agent 實例
            agent = Agent(
                id=agent_id,
                name=name,
                description=description,
                ai_model=ai_model,
                color_theme=color_theme,
                initial_funds=Decimal(str(initial_funds)),
                current_funds=Decimal(str(initial_funds)),
                max_position_size=Decimal(str(max_position_size)),
                status=AgentStatus.INACTIVE,
                current_mode=AgentMode.TRADING,
                investment_preferences=preferences_json,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.session.add(agent)
            logger.info(f"Created new agent: {agent_id}")

            return agent

        except Exception as e:
            logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to create agent: {str(e)}")

    # ==========================================
    # Update Operations
    # ==========================================

    async def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus | str | None = None,
        mode: AgentMode | str | None = None,
    ) -> bool:
        """
        更新 Agent 狀態

        遵循 timestamp.instructions.md 的原則：
        - EXPLICIT_OVER_IMPLICIT: 明確設置狀態變更
        - CONSISTENCY_AND_ACCURACY: 總是更新 updated_at 和 last_active_at

        此方法會自行消化所有異常，不向外部拋出。
        調用者無需處理異常。

        Args:
            agent_id: Agent ID
            status: 新狀態
            mode: 新模式（可選）

        Returns:
            True: 更新成功
            False: 更新失敗（異常已記錄）
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                logger.warning(f"Agent '{agent_id}' not found for status update")
                return False

            # 允許傳入字串並做轉換，避免 .value 屬性錯誤
            if status is not None:
                agent.status = (
                    status
                    if isinstance(status, AgentStatus)
                    else validate_agent_status(str(status)) or AgentStatus.INACTIVE
                )
            if mode is not None:
                agent.current_mode = (
                    mode
                    if isinstance(mode, AgentMode)
                    else validate_agent_mode(str(mode)) or AgentMode.TRADING
                )

            # 更新時間戳記
            agent.updated_at = datetime.now()
            if status is not None:
                agent.last_active_at = datetime.now()

            await self.session.commit()

            log_msg = f"Updated agent {agent_id}"
            if status is not None:
                status_str = status.value if isinstance(status, AgentStatus) else str(status)
                log_msg += f" status to {status_str}"
            if mode is not None:
                mode_str = mode.value if isinstance(mode, AgentMode) else str(mode)
                log_msg += f" mode to {mode_str}"
            logger.info(log_msg)
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Error updating agent {agent_id} status: {e}",
                exc_info=True,
                extra={
                    "agent_id": agent_id,
                    "new_status": status.value
                    if isinstance(status, AgentStatus)
                    else (str(status) if status is not None else None),
                },
            )
            return False

    # ==========================================
    # Trading Operations
    # ==========================================

    async def create_transaction(
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
    ) -> Transaction:
        """
        創建交易記錄

        遵循 timestamp.instructions.md 的原則：
        - EXPLICIT_OVER_IMPLICIT: 明確設置所有欄位包括 session_id
        - COMPLETE_LIFECYCLE_TRACKING: 設置 execution_time 以追蹤交易執行時刻

        Args:
            agent_id: Agent ID
            ticker: 股票代號
            action: 交易動作 ("BUY" 或 "SELL")
            quantity: 交易股數
            price: 交易價格
            total_amount: 交易總金額
            commission: 手續費
            decision_reason: 交易決策理由
            company_name: 公司名稱（可選）
            status: 交易狀態
            session_id: 關聯的 Agent Session ID（可選）

        Returns:
            創建的交易記錄

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 轉換 action 為 enum
            action_enum = (
                TransactionAction.BUY if action.upper() == "BUY" else TransactionAction.SELL
            )
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
                execution_time=(
                    datetime.now() if status_enum == TransactionStatus.EXECUTED else None
                ),
                decision_reason=decision_reason,
            )

            self.session.add(transaction)
            await self.session.commit()

            logger.info(
                f"Created transaction: {action} {quantity}股 x ${price} @ {ticker} for agent {agent_id}",
                extra={
                    "agent_id": agent_id,
                    "ticker": ticker,
                    "session_id": session_id,
                    "transaction_id": transaction.id,
                },
            )
            return transaction

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Database error creating transaction: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to create transaction: {str(e)}")

    async def get_agent_holdings(self, agent_id: str) -> list[AgentHolding]:
        """
        取得 Agent 持股明細

        Args:
            agent_id: Agent ID

        Returns:
            持股列表

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(AgentHolding).where(AgentHolding.agent_id == agent_id)
            result = await self.session.execute(stmt)
            holdings = list(result.scalars().all())

            logger.info(f"Found {len(holdings)} holdings for agent {agent_id}")
            return holdings

        except Exception as e:
            logger.error(f"Database error getting holdings: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to get holdings: {str(e)}")

    async def update_agent_holdings(
        self,
        agent_id: str,
        ticker: str,
        action: str,
        quantity: int,
        price: float,
        company_name: str | None = None,
    ) -> None:
        """
        更新 Agent 持股明細

        Args:
            agent_id: Agent ID
            ticker: 股票代號
            action: 交易動作 ("BUY" 或 "SELL")
            quantity: 交易股數
            price: 交易價格
            company_name: 公司名稱（可選）

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 查找現有持股
            stmt = select(AgentHolding).where(
                AgentHolding.agent_id == agent_id, AgentHolding.ticker == ticker
            )
            result = await self.session.execute(stmt)
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
                    self.session.add(holding)

            elif action.upper() == "SELL":
                if not holding:
                    raise AgentDatabaseError(f"Cannot sell {ticker}: no holdings found")

                if holding.quantity < quantity:
                    raise AgentDatabaseError(
                        f"Cannot sell {quantity} shares of {ticker}: only {holding.quantity} shares available"
                    )

                # 更新持股
                holding.quantity -= quantity
                if holding.quantity == 0:
                    # 完全賣出，刪除持股記錄
                    await self.session.delete(holding)
                else:
                    # 部分賣出，更新成本
                    holding.total_cost = holding.average_cost * holding.quantity
                    holding.updated_at = datetime.now()

            await self.session.commit()
            logger.info(
                f"Updated holdings: {action} {quantity}股 x ${price} @ {ticker} for agent {agent_id}"
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Database error updating holdings: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to update holdings: {str(e)}")

    async def get_agent_transactions(
        self,
        agent_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """
        取得 Agent 的交易記錄

        Args:
            agent_id: Agent ID
            limit: 返回記錄數量限制
            offset: 偏移量

        Returns:
            交易記錄列表

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = (
                select(Transaction)
                .where(Transaction.agent_id == agent_id)
                .order_by(Transaction.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            transactions = list(result.scalars().all())

            logger.info(f"Found {len(transactions)} transactions for agent {agent_id}")
            return transactions

        except Exception as e:
            logger.error(f"Database error getting transactions: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to get transactions: {str(e)}")

    async def calculate_trade_pairs_and_win_rate(self, agent_id: str) -> dict[str, Any]:
        """
        計算交易對數和勝率 (使用 FIFO 買賣配對邏輯)

        此方法實現完整的買賣配對邏輯，追蹤每個股票的買入成本和賣出收益，
        計算真實的獲利交易數和勝率。

        Args:
            agent_id: Agent ID

        Returns:
            包含以下鍵值的字典:
            - total_pairs (int): 已完成的買賣對數
            - winning_pairs (int): 獲利的買賣對數
            - losing_pairs (int): 虧損的買賣對數
            - win_rate (Decimal): 勝率 (%)

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 取得所有已執行的交易記錄（按時間排序）
            stmt = (
                select(Transaction)
                .where(Transaction.agent_id == agent_id)
                .where(Transaction.status == TransactionStatus.EXECUTED)
                .order_by(Transaction.created_at)
            )
            result = await self.session.execute(stmt)
            transactions = list(result.scalars().all())

            # 按股票分組交易
            trades_by_ticker: dict[str, dict[str, list[Transaction]]] = {}
            for tx in transactions:
                if tx.ticker not in trades_by_ticker:
                    trades_by_ticker[tx.ticker] = {"buys": [], "sells": []}

                if tx.action == TransactionAction.BUY:
                    trades_by_ticker[tx.ticker]["buys"].append(tx)
                else:
                    trades_by_ticker[tx.ticker]["sells"].append(tx)

            # 計算買賣對和損益
            total_pairs = 0
            winning_pairs = 0

            for ticker, trades in trades_by_ticker.items():
                buys = trades["buys"].copy()
                sells = trades["sells"].copy()

                buy_idx = 0

                for sell in sells:
                    remaining_qty = sell.quantity

                    while remaining_qty > 0 and buy_idx < len(buys):
                        buy = buys[buy_idx]

                        # 計算此次配對的數量（取較小值）
                        matched_qty = min(remaining_qty, buy.quantity)

                        # 計算此對交易的損益（含手續費）
                        # 損益 = (賣出價 - 買入價) × 數量 - 雙邊手續費
                        gross_pnl = (sell.price - buy.price) * matched_qty
                        buy_commission_portion = buy.commission * Decimal(
                            str(matched_qty / buy.quantity)
                        )  # 按比例分攤手續費
                        sell_commission_portion = sell.commission * Decimal(
                            str(matched_qty / sell.quantity)
                        )
                        net_pnl = gross_pnl - buy_commission_portion - sell_commission_portion

                        # 判斷是否獲利
                        if net_pnl > 0:
                            winning_pairs += 1

                        total_pairs += 1

                        # 更新剩餘數量
                        remaining_qty -= matched_qty
                        buy.quantity -= matched_qty

                        # 如果買入交易完全配對，移到下一個買入交易
                        if buy.quantity == 0:
                            buy_idx += 1

            # 計算勝率
            win_rate = (
                Decimal(str(winning_pairs / total_pairs * 100)) if total_pairs > 0 else Decimal("0")
            )

            logger.info(
                f"Trade pairs calculated for agent {agent_id}: "
                f"total={total_pairs}, winning={winning_pairs}, win_rate={win_rate}%"
            )

            return {
                "total_pairs": total_pairs,
                "winning_pairs": winning_pairs,
                "losing_pairs": total_pairs - winning_pairs,
                "win_rate": win_rate,
            }

        except Exception as e:
            logger.error(
                f"Failed to calculate trade pairs for agent {agent_id}: {e}", exc_info=True
            )
            raise AgentDatabaseError(f"Failed to calculate trade pairs: {str(e)}")

    async def calculate_realized_pnl(self, agent_id: str) -> Decimal:
        """
        計算已實現損益 (使用 FIFO 方法)

        此方法追蹤每個股票的買入成本，並在賣出時計算實際損益。
        使用 FIFO (First In, First Out) 方法來匹配買賣交易。

        Args:
            agent_id: Agent ID

        Returns:
            已實現損益總額 (Decimal)

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 取得所有已執行的交易記錄（按時間排序）
            stmt = (
                select(Transaction)
                .where(Transaction.agent_id == agent_id)
                .where(Transaction.status == TransactionStatus.EXECUTED)
                .order_by(Transaction.created_at)
            )
            result = await self.session.execute(stmt)
            transactions = list(result.scalars().all())

            # 追蹤成本基礎 (cost basis)
            # 格式: {ticker: [(quantity, price, commission), ...]}
            cost_basis: dict[str, list[tuple[int, Decimal, Decimal]]] = {}
            realized_pnl = Decimal("0")

            for tx in transactions:
                ticker = tx.ticker

                if tx.action == TransactionAction.BUY:
                    # 買入: 記錄成本基礎
                    if ticker not in cost_basis:
                        cost_basis[ticker] = []

                    cost_basis[ticker].append((tx.quantity, tx.price, tx.commission))

                elif tx.action == TransactionAction.SELL:
                    # 賣出: 使用 FIFO 配對並計算損益
                    remaining_qty = tx.quantity
                    sell_price = tx.price
                    sell_commission_per_share = (
                        tx.commission / Decimal(tx.quantity) if tx.quantity else Decimal("0")
                    )

                    while remaining_qty > 0 and ticker in cost_basis and cost_basis[ticker]:
                        # 取得最早的買入記錄 (FIFO)
                        buy_qty, buy_price, buy_commission = cost_basis[ticker][0]

                        # 計算此次配對的數量
                        matched_qty = min(remaining_qty, buy_qty)

                        # 計算毛損益
                        gross_pnl = (sell_price - buy_price) * Decimal(matched_qty)

                        # 扣除手續費（按比例分攤）
                        allocation_ratio = (
                            Decimal(matched_qty) / Decimal(buy_qty) if buy_qty else Decimal("0")
                        )
                        buy_commission_portion = buy_commission * allocation_ratio
                        sell_commission_portion = sell_commission_per_share * Decimal(matched_qty)

                        # 計算淨損益
                        net_pnl = gross_pnl - buy_commission_portion - sell_commission_portion

                        # 累加到總已實現損益
                        realized_pnl += net_pnl

                        # 更新剩餘數量
                        remaining_qty -= matched_qty
                        buy_qty -= matched_qty

                        # 更新或移除成本基礎記錄
                        if buy_qty == 0:
                            cost_basis[ticker].pop(0)
                        else:
                            cost_basis[ticker][0] = (buy_qty, buy_price, buy_commission)

            logger.info(f"Calculated realized P&L for agent {agent_id}: {realized_pnl}")
            return realized_pnl

        except Exception as e:
            logger.error(
                f"Failed to calculate realized P&L for agent {agent_id}: {e}", exc_info=True
            )
            raise AgentDatabaseError(f"Failed to calculate realized P&L: {str(e)}")

    async def calculate_max_drawdown(self, agent_id: str) -> Decimal | None:
        """
        計算最大回撤

        最大回撤 = (歷史最高淨值 - 當前最低淨值) / 歷史最高淨值 × 100%

        演算法:
        1. 取得所有歷史績效記錄（按日期排序）
        2. 追蹤滾動最高淨值 (peak)
        3. 計算每日回撤 = (peak - current_value) / peak × 100%
        4. 追蹤最大回撤

        Args:
            agent_id: Agent ID

        Returns:
            最大回撤百分比 (%) 或 None (資料不足)

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 取得所有歷史績效記錄（按日期升序排序）
            stmt = (
                select(AgentPerformance.total_value)
                .where(AgentPerformance.agent_id == agent_id)
                .order_by(AgentPerformance.date.asc())
            )

            result = await self.session.execute(stmt)
            values = [row[0] for row in result.all()]

            # 需要至少 2 個資料點才能計算回撤
            if len(values) < 2:
                logger.debug(
                    f"Insufficient data to calculate max drawdown for agent {agent_id}: "
                    f"only {len(values)} records"
                )
                return None

            # 初始化追蹤變數
            peak = Decimal("0")  # 歷史最高淨值
            max_drawdown = Decimal("0")  # 最大回撤

            # 遍歷每個淨值
            for value in values:
                # 更新歷史最高淨值
                if value > peak:
                    peak = value

                # 計算當前回撤
                if peak > 0:
                    drawdown = (peak - value) / peak * 100
                    # 更新最大回撤
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown

            logger.info(
                f"Calculated max drawdown for agent {agent_id}: {max_drawdown:.2f}% "
                f"(peak={peak}, data_points={len(values)})"
            )
            return max_drawdown

        except Exception as e:
            logger.error(
                f"Failed to calculate max drawdown for agent {agent_id}: {e}", exc_info=True
            )
            raise AgentDatabaseError(f"Failed to calculate max drawdown: {str(e)}")

    async def calculate_sharpe_ratio(self, agent_id: str) -> Decimal | None:
        """
        計算夏普比率

        衡量投資風險調整後的報酬。
        公式: (年化報酬率 - 無風險利率) / 年化波動率

        無風險利率設定為 2%（台灣公債平均利率）
        波動率計算：日報酬率的標準差 × √252（交易日數）

        Args:
            agent_id: Agent ID

        Returns:
            夏普比率 或 None (資料不足)

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 無風險利率（年化 2%）
            RISK_FREE_RATE = Decimal("2")

            # 取得所有歷史績效記錄（按日期排序）
            stmt = (
                select(AgentPerformance.daily_return)
                .where(AgentPerformance.agent_id == agent_id)
                .where(AgentPerformance.daily_return.isnot(None))
                .order_by(AgentPerformance.date.asc())
            )

            result = await self.session.execute(stmt)
            daily_returns = [row[0] for row in result.all()]

            # 需要至少 20 個交易日資料
            if len(daily_returns) < 20:
                logger.debug(
                    f"Insufficient data to calculate Sharpe ratio for agent {agent_id}: "
                    f"only {len(daily_returns)} records (need >= 20)"
                )
                return None

            # 計算日報酬率平均值
            avg_return = sum(daily_returns) / len(daily_returns)

            # 計算日報酬率標準差（波動率）
            variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
            daily_volatility = variance.sqrt()

            # 年化波動率（252 個交易日）
            annual_volatility = daily_volatility * Decimal("15.8745")  # √252

            # 計算年化報酬率
            # 假設日平均報酬複利計算：(1 + 日平均報酬)^252 - 1
            if avg_return > -1:
                annual_return = ((1 + avg_return / 100) ** 252 - 1) * 100
            else:
                annual_return = Decimal("0")

            # 計算夏普比率
            if annual_volatility > 0:
                sharpe_ratio = (annual_return - RISK_FREE_RATE) / annual_volatility
            else:
                sharpe_ratio = Decimal("0")

            logger.info(
                f"Calculated Sharpe ratio for agent {agent_id}: {sharpe_ratio:.4f} "
                f"(annual_return={annual_return:.2f}%, annual_volatility={annual_volatility:.2f}%, "
                f"data_points={len(daily_returns)})"
            )
            return sharpe_ratio

        except Exception as e:
            logger.error(
                f"Failed to calculate Sharpe ratio for agent {agent_id}: {e}", exc_info=True
            )
            raise AgentDatabaseError(f"Failed to calculate Sharpe ratio: {str(e)}")

    async def calculate_sortino_ratio(self, agent_id: str) -> Decimal | None:
        """
        計算索提諾比率

        改良版的夏普比率，只考慮下行風險（負報酬）。
        公式: (年化報酬率 - 無風險利率) / 年化下行波動率

        下行波動率只計算低於目標報酬（通常為 0%）的報酬標準差。
        無風險利率設定為 2%。

        Args:
            agent_id: Agent ID

        Returns:
            索提諾比率 或 None (資料不足)

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 無風險利率（年化 2%）
            RISK_FREE_RATE = Decimal("2")
            TARGET_RETURN = Decimal("0")  # 目標報酬為 0%

            # 取得所有歷史績效記錄（按日期排序）
            stmt = (
                select(AgentPerformance.daily_return)
                .where(AgentPerformance.agent_id == agent_id)
                .where(AgentPerformance.daily_return.isnot(None))
                .order_by(AgentPerformance.date.asc())
            )

            result = await self.session.execute(stmt)
            daily_returns = [row[0] for row in result.all()]

            # 需要至少 20 個交易日資料
            if len(daily_returns) < 20:
                logger.debug(
                    f"Insufficient data to calculate Sortino ratio for agent {agent_id}: "
                    f"only {len(daily_returns)} records (need >= 20)"
                )
                return None

            # 計算日報酬率平均值
            avg_return = sum(daily_returns) / len(daily_returns)

            # 計算下行波動率（只考慮負報酬）
            downside_returns = [r for r in daily_returns if r < TARGET_RETURN]

            if downside_returns:
                downside_variance = sum((r - TARGET_RETURN) ** 2 for r in downside_returns) / len(
                    daily_returns
                )  # 分母用總數，不是負報酬數
                downside_volatility = downside_variance.sqrt()
            else:
                # 無下行波動，直接返回
                downside_volatility = Decimal("0")

            # 年化下行波動率
            annual_downside_volatility = downside_volatility * Decimal("15.8745")  # √252

            # 計算年化報酬率
            if avg_return > -1:
                annual_return = ((1 + avg_return / 100) ** 252 - 1) * 100
            else:
                annual_return = Decimal("0")

            # 計算索提諾比率
            if annual_downside_volatility > 0:
                sortino_ratio = (annual_return - RISK_FREE_RATE) / annual_downside_volatility
            else:
                # 無下行風險，索提諾比率為無窮大（用很大的數表示）
                sortino_ratio = Decimal("999") if annual_return > RISK_FREE_RATE else Decimal("0")

            logger.info(
                f"Calculated Sortino ratio for agent {agent_id}: {sortino_ratio:.4f} "
                f"(annual_return={annual_return:.2f}%, annual_downside_volatility={annual_downside_volatility:.2f}%, "
                f"data_points={len(daily_returns)}, downside_returns={len(downside_returns)})"
            )
            return sortino_ratio

        except Exception as e:
            logger.error(
                f"Failed to calculate Sortino ratio for agent {agent_id}: {e}", exc_info=True
            )
            raise AgentDatabaseError(f"Failed to calculate Sortino ratio: {str(e)}")

    async def calculate_calmar_ratio(self, agent_id: str) -> Decimal | None:
        """
        計算卡瑪比率

        衡量報酬率與最大回撤的比值。
        公式: 年化報酬率 / 最大回撤

        Args:
            agent_id: Agent ID

        Returns:
            卡瑪比率 或 None (資料不足)

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 取得最大回撤
            max_drawdown = await self.calculate_max_drawdown(agent_id)
            if max_drawdown is None or max_drawdown == 0:
                logger.debug(
                    f"Cannot calculate Calmar ratio for agent {agent_id}: "
                    f"max_drawdown is {max_drawdown}"
                )
                return None

            # 取得所有日報酬率計算年化報酬率
            stmt = (
                select(AgentPerformance.daily_return)
                .where(AgentPerformance.agent_id == agent_id)
                .where(AgentPerformance.daily_return.isnot(None))
                .order_by(AgentPerformance.date.asc())
            )

            result = await self.session.execute(stmt)
            daily_returns = [row[0] for row in result.all()]

            if not daily_returns:
                return None

            # 計算平均日報酬率
            avg_return = sum(daily_returns) / len(daily_returns)

            # 計算年化報酬率
            if avg_return > -1:
                annual_return = ((1 + avg_return / 100) ** 252 - 1) * 100
            else:
                annual_return = Decimal("0")

            # 計算卡瑪比率
            calmar_ratio = annual_return / max_drawdown

            logger.info(
                f"Calculated Calmar ratio for agent {agent_id}: {calmar_ratio:.4f} "
                f"(annual_return={annual_return:.2f}%, max_drawdown={max_drawdown:.2f}%)"
            )
            return calmar_ratio

        except Exception as e:
            logger.error(
                f"Failed to calculate Calmar ratio for agent {agent_id}: {e}", exc_info=True
            )
            raise AgentDatabaseError(f"Failed to calculate Calmar ratio: {str(e)}")

    async def calculate_daily_return(self, agent_id: str, current_date: date) -> Decimal | None:
        """
        計算當日報酬率

        比較當日與前一個交易日的投資組合總價值，計算日報酬率。
        公式: (今日總價值 - 前日總價值) / 前日總價值 × 100%

        Args:
            agent_id: Agent ID
            current_date: 計算日期

        Returns:
            當日報酬率 (%) 或 None (無前一日資料)

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            from datetime import timedelta

            # 取得當日績效
            stmt_today = (
                select(AgentPerformance)
                .where(AgentPerformance.agent_id == agent_id)
                .where(AgentPerformance.date == current_date)
            )
            result_today = await self.session.execute(stmt_today)
            today_perf = result_today.scalar_one_or_none()

            if not today_perf:
                logger.debug(f"No performance record for agent {agent_id} on {current_date}")
                return None

            # 尋找前一個交易日的績效記錄
            # 向前查找最多 7 天（處理週末和假日）
            prev_perf = None
            for days_back in range(1, 8):
                prev_date = current_date - timedelta(days=days_back)
                stmt_prev = (
                    select(AgentPerformance)
                    .where(AgentPerformance.agent_id == agent_id)
                    .where(AgentPerformance.date == prev_date)
                )
                result_prev = await self.session.execute(stmt_prev)
                prev_perf = result_prev.scalar_one_or_none()

                if prev_perf:
                    break

            if not prev_perf or prev_perf.total_value <= 0:
                logger.debug(f"No previous performance record found for agent {agent_id}")
                return None

            # 計算日報酬率
            daily_return = (
                (today_perf.total_value - prev_perf.total_value) / prev_perf.total_value * 100
            )

            logger.info(
                f"Calculated daily return for agent {agent_id} on {current_date}: "
                f"{daily_return}% (from {prev_perf.total_value} to {today_perf.total_value})"
            )

            return Decimal(str(daily_return))

        except Exception as e:
            logger.error(
                f"Failed to calculate daily return for agent {agent_id} on {current_date}: {e}",
                exc_info=True,
            )
            raise AgentDatabaseError(f"Failed to calculate daily return: {str(e)}")

    async def calculate_unrealized_pnl(self, agent_id: str) -> Decimal:
        """
        計算未實現損益

        使用 MCP casual-market 服務獲取實時股價，計算當前持股的未實現損益。
        公式: Σ (當前價格 - 平均成本) × 持有數量

        Args:
            agent_id: Agent ID

        Returns:
            未實現損益總額 (Decimal)

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 取得當前持股
            holdings = await self.get_agent_holdings(agent_id)

            if not holdings:
                logger.debug(f"No holdings found for agent {agent_id}")
                return Decimal("0")

            # 導入 MCP Client
            from api.mcp_client import MCPMarketClient

            unrealized_pnl = Decimal("0")
            successful_prices = 0
            failed_prices = 0

            # 初始化 MCP Client
            async with MCPMarketClient() as mcp_client:
                for holding in holdings:
                    try:
                        # 調用 MCP 服務獲取實時價格
                        price_data = await mcp_client.get_stock_price(holding.ticker)

                        # 檢查回應格式
                        if not price_data or not price_data.get("success"):
                            logger.warning(
                                f"Failed to get price for {holding.ticker}: "
                                f"{price_data.get('error', 'Unknown error')}"
                            )
                            failed_prices += 1
                            continue

                        # 從回應中提取當前價格
                        stock_data = price_data.get("data", {})
                        current_price = stock_data.get("current_price")

                        if current_price is None:
                            logger.warning(
                                f"No current_price in response for {holding.ticker}: {stock_data}"
                            )
                            failed_prices += 1
                            continue

                        # 轉換為 Decimal 並計算此持股的未實現損益
                        current_price_decimal = Decimal(str(current_price))
                        position_pnl = (
                            current_price_decimal - holding.average_cost
                        ) * holding.quantity

                        unrealized_pnl += position_pnl
                        successful_prices += 1

                        logger.debug(
                            f"Holding {holding.ticker}: qty={holding.quantity}, "
                            f"cost={holding.average_cost}, current={current_price_decimal}, "
                            f"pnl={position_pnl}"
                        )

                    except Exception as e:
                        logger.warning(
                            f"Error getting price for {holding.ticker}: {e}", exc_info=True
                        )
                        failed_prices += 1
                        continue

            logger.info(
                f"Calculated unrealized P&L for agent {agent_id}: {unrealized_pnl} "
                f"(successful: {successful_prices}, failed: {failed_prices})"
            )

            return unrealized_pnl

        except Exception as e:
            logger.error(
                f"Failed to calculate unrealized P&L for agent {agent_id}: {e}", exc_info=True
            )
            raise AgentDatabaseError(f"Failed to calculate unrealized P&L: {str(e)}")

    async def calculate_and_update_performance(self, agent_id: str) -> None:
        """
        計算並更新 Agent 績效指標

        Args:
            agent_id: Agent ID

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            from datetime import date

            # 取得 Agent 配置
            agent = await self.get_agent_config(agent_id)

            # 取得持股明細
            holdings = await self.get_agent_holdings(agent_id)

            # 計算股票市值（簡化：使用平均成本作為當前價格）
            stocks_value = sum(holding.quantity * holding.average_cost for holding in holdings)

            # 計算現金餘額
            cash_balance = agent.current_funds or agent.initial_funds

            # 計算總資產價值
            total_value = Decimal(str(cash_balance)) + stocks_value

            # 取得交易統計
            from sqlalchemy import func, case

            stmt_transactions = (
                select(
                    func.count(Transaction.id).label("total_trades"),
                    func.sum(
                        case((Transaction.action == TransactionAction.SELL, 1), else_=0)
                    ).label("completed_trades"),
                )
                .where(Transaction.agent_id == agent_id)
                .where(Transaction.status == TransactionStatus.EXECUTED)
            )

            result = await self.session.execute(stmt_transactions)
            trade_stats = result.first()

            total_trades = trade_stats.total_trades or 0
            completed_trades = trade_stats.completed_trades or 0

            # 計算總回報率
            total_return = (
                (total_value - agent.initial_funds) / agent.initial_funds
                if agent.initial_funds > 0
                else Decimal("0")
            )

            # 計算真實買賣配對和勝率（使用 FIFO 邏輯）
            trade_pairs_result = await self.calculate_trade_pairs_and_win_rate(agent_id)
            winning_pairs = trade_pairs_result["winning_pairs"]
            win_rate = trade_pairs_result["win_rate"]

            # 計算已實現損益（使用 FIFO 邏輯）
            realized_pnl = await self.calculate_realized_pnl(agent_id)

            # 計算未實現損益（使用 MCP 服務獲取實時股價）
            unrealized_pnl = await self.calculate_unrealized_pnl(agent_id)

            # 查找今日績效記錄
            today = date.today()
            stmt_performance = select(AgentPerformance).where(
                AgentPerformance.agent_id == agent_id, AgentPerformance.date == today
            )
            result = await self.session.execute(stmt_performance)
            performance = result.scalar_one_or_none()

            if performance:
                # 更新現有記錄
                performance.total_value = total_value
                performance.cash_balance = Decimal(str(cash_balance))
                performance.total_return = total_return
                performance.realized_pnl = realized_pnl  # 已實現損益
                performance.unrealized_pnl = unrealized_pnl  # 未實現損益（實時計算）
                # 使用真實買賣配對邏輯計算的勝率
                performance.win_rate = win_rate
                performance.total_trades = total_trades
                performance.sell_trades_count = completed_trades  # 賣出交易數
                performance.winning_trades_correct = winning_pairs  # 真實獲利交易數
                performance.updated_at = datetime.now()
            else:
                # 創建新記錄
                performance = AgentPerformance(
                    agent_id=agent_id,
                    date=today,
                    total_value=total_value,
                    cash_balance=Decimal(str(cash_balance)),
                    # 損益欄位
                    unrealized_pnl=unrealized_pnl,  # 未實現損益（使用 MCP 服務獲取實時股價）
                    realized_pnl=realized_pnl,  # 已實現損益（使用 FIFO 邏輯）
                    daily_return=None,  # 首次創建時無法計算，需要前一日資料
                    # 績效指標
                    total_return=total_return,
                    # 使用真實買賣配對邏輯計算的勝率
                    win_rate=win_rate,
                    max_drawdown=None,  # 待計算：需要歷史淨值曲線
                    total_trades=total_trades,
                    sell_trades_count=completed_trades,  # 賣出交易數
                    winning_trades_correct=winning_pairs,  # 真實獲利交易數
                )
                self.session.add(performance)

            # 先提交當前績效記錄，然後計算日報酬率和最大回撤
            await self.session.commit()

            # 計算並更新當日報酬率（需要前一日資料）
            daily_return = await self.calculate_daily_return(agent_id, today)
            if daily_return is not None:
                performance.daily_return = daily_return
                logger.info(f"Updated daily return for agent {agent_id}: {daily_return}%")

            # 計算並更新最大回撤（需要歷史淨值曲線）
            max_drawdown = await self.calculate_max_drawdown(agent_id)
            if max_drawdown is not None:
                performance.max_drawdown = max_drawdown
                logger.info(f"Updated max drawdown for agent {agent_id}: {max_drawdown:.2f}%")

            # 計算並更新進階風險指標
            sharpe_ratio = await self.calculate_sharpe_ratio(agent_id)
            if sharpe_ratio is not None:
                performance.sharpe_ratio = sharpe_ratio
                logger.info(f"Updated Sharpe ratio for agent {agent_id}: {sharpe_ratio:.4f}")

            sortino_ratio = await self.calculate_sortino_ratio(agent_id)
            if sortino_ratio is not None:
                performance.sortino_ratio = sortino_ratio
                logger.info(f"Updated Sortino ratio for agent {agent_id}: {sortino_ratio:.4f}")

            calmar_ratio = await self.calculate_calmar_ratio(agent_id)
            if calmar_ratio is not None:
                performance.calmar_ratio = calmar_ratio
                logger.info(f"Updated Calmar ratio for agent {agent_id}: {calmar_ratio:.4f}")

            # 提交所有更新
            await self.session.commit()
            logger.info(f"Updated performance for agent {agent_id}: total_value={total_value}")

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Database error calculating performance: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to calculate performance: {str(e)}")

    async def update_agent_funds(
        self,
        agent_id: str,
        amount_change: float,
        transaction_type: str,
    ) -> None:
        """
        更新 Agent 資金

        Args:
            agent_id: Agent ID
            amount_change: 資金變化量（正數為增加，負數為減少）
            transaction_type: 交易類型描述

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found")

            current_funds = agent.current_funds or agent.initial_funds
            new_funds = float(current_funds) + amount_change

            if new_funds < 0:
                raise AgentDatabaseError(
                    f"Insufficient funds: current={current_funds}, required={-amount_change}"
                )

            agent.current_funds = Decimal(str(new_funds))

            # 更新時間戳記
            agent.updated_at = datetime.now()
            agent.last_active_at = datetime.now()

            await self.session.commit()

            logger.info(
                f"Updated funds for agent {agent_id}: {current_funds} -> {new_funds} ({transaction_type})"
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Database error updating funds: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to update funds: {str(e)}")

    # ==========================================
    # Validation and Parsing
    # ==========================================

    def _validate_agent_config(self, agent: Agent) -> None:
        """
        驗證 Agent 配置完整性

        Args:
            agent: Agent 模型實例

        Raises:
            AgentConfigurationError: 配置驗證失敗
        """
        # 驗證必要欄位
        if not agent.name:
            raise AgentConfigurationError("Agent name is required")

        if not agent.ai_model:
            raise AgentConfigurationError("AI model is required")

        # 驗證 JSON 格式
        if agent.investment_preferences:
            try:
                json.loads(agent.investment_preferences)
            except json.JSONDecodeError as e:
                raise AgentConfigurationError(f"Invalid investment_preferences JSON: {str(e)}")

    def parse_investment_preferences(self, agent: Agent) -> dict[str, Any]:
        """
        解析 investment_preferences JSON

        Args:
            agent: Agent 模型實例

        Returns:
            解析後的字典（如果為空則返回預設值）
        """
        if not agent.investment_preferences:
            return self._get_default_preferences()

        try:
            return json.loads(agent.investment_preferences)
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to parse investment_preferences for agent {agent.id}, using defaults"
            )
            return self._get_default_preferences()

    def _get_default_preferences(self) -> dict[str, Any]:
        """預設投資偏好"""
        return {
            "enabled_tools": {
                "fundamental_analysis": True,
                "technical_analysis": True,
                "risk_assessment": True,
                "sentiment_analysis": True,
                "web_search": True,
                "code_interpreter": True,
            },
            "risk_tolerance": "moderate",
            "max_single_position": 10.0,
            "stop_loss_percent": 8.0,
            "take_profit_percent": 15.0,
        }

    async def get_performance_history(
        self,
        agent_id: str,
        limit: int = 30,
        order: str = "desc",
    ) -> list[dict[str, Any]]:
        """
        獲取 Agent 的性能歷史記錄

        Args:
            agent_id: Agent ID
            limit: 返回的記錄數量（最多 365）
            order: 排序順序 ('asc' 或 'desc')，預設 'desc' 最近的在前

        Returns:
            性能歷史記錄列表，每條包含 date, total_value, cash_balance, unrealized_pnl,
            realized_pnl, daily_return, total_return, win_rate, max_drawdown, total_trades,
            winning_trades

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 驗證 Agent 存在
            await self.get_agent_config(agent_id)

            # 限制查詢數量
            limit = min(limit, 365)

            # 構建查詢
            stmt = (
                select(AgentPerformance)
                .where(AgentPerformance.agent_id == agent_id)
                .order_by(
                    AgentPerformance.date.asc()
                    if order.lower() == "asc"
                    else AgentPerformance.date.desc()
                )
                .limit(limit)
            )

            result = await self.session.execute(stmt)
            performance_records = result.scalars().all()

            # 轉換為字典列表
            history = []
            for record in performance_records:
                history.append(
                    {
                        "date": record.date.isoformat(),
                        "total_value": float(record.total_value),
                        "cash_balance": float(record.cash_balance),
                        "unrealized_pnl": float(record.unrealized_pnl or 0),
                        "realized_pnl": float(record.realized_pnl or 0),
                        "daily_return": float(record.daily_return) if record.daily_return else None,
                        "total_return": float(record.total_return) if record.total_return else None,
                        "win_rate": float(record.win_rate) if record.win_rate else None,
                        "max_drawdown": float(record.max_drawdown) if record.max_drawdown else None,
                        "sharpe_ratio": float(record.sharpe_ratio) if record.sharpe_ratio else None,
                        "sortino_ratio": float(record.sortino_ratio)
                        if record.sortino_ratio
                        else None,
                        "calmar_ratio": float(record.calmar_ratio) if record.calmar_ratio else None,
                        "total_trades": record.total_trades,
                        "sell_trades_count": record.sell_trades_count,  # 修正: 賣出交易數
                        "winning_trades_correct": record.winning_trades_correct,  # 真實獲利交易數
                    }
                )

            # 如果排序是 desc，需要反轉回 asc 以便圖表顯示正確的時間序列
            if order.lower() == "desc":
                history.reverse()

            logger.info(
                f"Retrieved performance history for agent {agent_id}: {len(history)} records"
            )
            return history

        except AgentNotFoundError:
            raise

        except Exception as e:
            logger.error(
                f"Failed to get performance history for agent {agent_id}: {e}", exc_info=True
            )
            raise AgentDatabaseError(f"Failed to retrieve performance history: {str(e)}")

    async def get_agent_financial_summary(self, agent_id: str) -> dict[str, Any]:
        """
        獲取 Agent 的財務摘要數據

        用於 WebSocket 廣播，提供完整的財務狀態資訊。

        Args:
            agent_id: Agent ID

        Returns:
            包含以下財務數據的字典：
            - current_funds: 當前資金
            - initial_funds: 初始資金
            - total_portfolio_value: 總投資組合價值（現金 + 持倉市值）
            - holdings_value: 持倉總市值
            - cash_percentage: 現金比例
            - stocks_percentage: 股票比例
            - total_return: 總回報金額
            - total_return_percent: 總回報率

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 獲取 Agent 配置
            agent = await self.get_agent_config(agent_id)

            # 獲取持倉資料
            holdings = await self.get_agent_holdings(agent_id)

            # 計算財務數據
            current_funds = float(agent.current_funds)
            initial_funds = float(agent.initial_funds)

            # 計算持倉總市值（使用平均成本作為估計）
            holdings_value = sum(
                float(holding.quantity) * float(holding.average_cost) for holding in holdings
            )

            # 計算總投資組合價值
            total_portfolio_value = current_funds + holdings_value

            # 計算比例
            cash_percentage = (
                (current_funds / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0
            )
            stocks_percentage = (
                (holdings_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0
            )

            # 計算總回報
            total_return = total_portfolio_value - initial_funds
            total_return_percent = (
                (total_return / initial_funds * 100) if initial_funds > 0 else 0.0
            )

            return {
                "current_funds": current_funds,
                "initial_funds": initial_funds,
                "total_portfolio_value": total_portfolio_value,
                "holdings_value": holdings_value,
                "cash_percentage": round(cash_percentage, 2),
                "stocks_percentage": round(stocks_percentage, 2),
                "total_return": total_return,
                "total_return_percent": round(total_return_percent, 2),
                "holdings_count": len(holdings),
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error getting financial summary for agent '{agent_id}': {e}",
                exc_info=True,
            )
            raise AgentDatabaseError(
                f"Failed to get financial summary for agent '{agent_id}'"
            ) from e

    # ==========================================
    # Context Manager Support
    # ==========================================

    async def __aenter__(self):
        """進入異步上下文管理器"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出異步上下文管理器"""
        if exc_type is not None:
            await self.session.rollback()
        await self.session.close()
