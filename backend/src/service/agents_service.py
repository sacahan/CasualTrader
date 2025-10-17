"""
Agent 資料庫服務層

提供 Agent 配置的 CRUD 操作和錯誤處理
基於 POC 實作，增強功能和錯誤處理
"""

from __future__ import annotations

import json
import logging
from typing import Any
from decimal import Decimal
from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import (
    Agent,
    Transaction,
    AgentHolding,
    AgentPerformance,
    AIModelConfig,
)
from ..common.enums import AgentMode, AgentStatus, TransactionAction, TransactionStatus

logger = logging.getLogger(__name__)


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
            stmt = select(Agent)
            result = await self.session.execute(stmt)
            agents = list(result.scalars().all())

            logger.info(f"Found {len(agents)} active agents")
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
                    "full_model_name": model.full_model_name,
                    "max_tokens": model.max_tokens,
                    "cost_per_1k_tokens": (
                        float(model.cost_per_1k_tokens) if model.cost_per_1k_tokens else None
                    ),
                    "description": model.description,
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
                "model_type": model.model_type.value,
                "litellm_prefix": model.litellm_prefix,
                "full_model_name": model.full_model_name,
                "max_tokens": model.max_tokens,
                "cost_per_1k_tokens": (
                    float(model.cost_per_1k_tokens) if model.cost_per_1k_tokens else None
                ),
                "description": model.description,
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
        strategy_prompt: str,
        initial_funds: float,
        max_position_size: float = 5.0,
        color_theme: str = "34, 197, 94",
        investment_preferences: list[str] | None = None,
        custom_instructions: str = "",
        enabled_tools: dict | None = None,
    ) -> Agent:
        """
        創建新 Agent

        Args:
            name: Agent 名稱
            description: Agent 描述
            ai_model: AI 模型名稱
            strategy_prompt: 策略提示
            initial_funds: 初始資金
            max_position_size: 最大持倉比例 (%)
            color_theme: 顏色主題 (RGB 格式)
            investment_preferences: 投資偏好列表
            custom_instructions: 自訂指令
            enabled_tools: 啟用的工具

        Returns:
            創建的 Agent 實例

        Raises:
            AgentConfigurationError: 配置錯誤
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            # 生成 Agent ID
            agent_id = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

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
                current_mode=AgentMode.OBSERVATION,
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
        status: AgentStatus | None = None,
        mode: AgentMode | None = None,
    ) -> None:
        """
        更新 Agent 狀態

        Args:
            agent_id: Agent ID
            status: 新狀態
            mode: 新模式（可選）

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found")

            if status is not None:
                agent.status = status
            if mode is not None:
                agent.current_mode = mode

            await self.session.commit()

            log_msg = f"Updated agent {agent_id}"
            if status:
                log_msg += f" status to {status.value}"
            if mode:
                log_msg += f" mode to {mode.value}"
            logger.info(log_msg)

        except AgentNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Database error updating agent status: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to update agent status: {str(e)}")

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
    ) -> Transaction:
        """
        創建交易記錄

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
                TransactionStatus.COMPLETED
                if status.upper() == "COMPLETED"
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
                execution_time=(
                    datetime.now() if status_enum == TransactionStatus.COMPLETED else None
                ),
                decision_reason=decision_reason,
            )

            self.session.add(transaction)
            await self.session.commit()

            logger.info(f"Created transaction: {action} {quantity} {ticker} for agent {agent_id}")
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
            logger.info(f"Updated holdings: {action} {quantity} {ticker} for agent {agent_id}")

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
            from sqlalchemy import func

            stmt_transactions = (
                select(
                    func.count(Transaction.id).label("total_trades"),
                    func.sum(
                        func.case((Transaction.action == TransactionAction.SELL, 1), else_=0)
                    ).label("completed_trades"),
                )
                .where(Transaction.agent_id == agent_id)
                .where(Transaction.status == TransactionStatus.COMPLETED)
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

            # 計算勝率（簡化：基於交易完成率）
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
            result = await self.session.execute(stmt_performance)
            performance = result.scalar_one_or_none()

            if performance:
                # 更新現有記錄
                performance.total_value = total_value
                performance.cash_balance = Decimal(str(cash_balance))
                performance.total_return = total_return
                performance.win_rate = win_rate
                performance.total_trades = total_trades
                performance.winning_trades = completed_trades
            else:
                # 創建新記錄
                performance = AgentPerformance(
                    agent_id=agent_id,
                    date=today,
                    total_value=total_value,
                    cash_balance=Decimal(str(cash_balance)),
                    unrealized_pnl=Decimal("0"),  # TODO: 計算未實現損益
                    realized_pnl=Decimal("0"),  # TODO: 計算已實現損益
                    total_return=total_return,
                    win_rate=win_rate,
                    total_trades=total_trades,
                    winning_trades=completed_trades,
                )
                self.session.add(performance)

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
