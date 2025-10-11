"""
Agent Database Integration Service
提供 Agent 與 SQLite 資料庫的完整整合
使用 Python 3.12+ 語法和異步 SQLAlchemy
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .models import (
    Agent as DBAgent,
    AgentHolding,
    AgentSession as DBAgentSession,
    StrategyChange as DBStrategyChange,
    AIModelConfig,
)

from ..agents.core.models import (
    AgentConfig,
    AgentExecutionResult,
    AgentState,
    AgentStatus,
    ChangeType,
    SessionStatus,
    StrategyChange,
)

# ==========================================
# 資料庫配置
# ==========================================


class DatabaseConfig:
    """資料庫配置"""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///casualtrader.db"):
        self.database_url = database_url
        self.echo = False  # 生產環境設為 False


# ==========================================
# Agent 資料庫服務
# ==========================================


class AgentDatabaseService:
    """
    Agent 資料庫整合服務
    提供 Agent 狀態持久化和資料管理
    """

    def __init__(self, config: DatabaseConfig | None = None):
        self.config = config or DatabaseConfig()
        self.engine: AsyncEngine | None = None
        self.session_factory: sessionmaker[AsyncSession] | None = None

        self.logger = logging.getLogger("agent_db_service")
        self.logger.setLevel(logging.INFO)

    async def initialize(self) -> None:
        """初始化資料庫連接"""
        if self.engine:
            return

        self.engine = create_async_engine(
            self.config.database_url,
            echo=self.config.echo,
        )

        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        self.logger.info("Database service initialized")

    async def close(self) -> None:
        """關閉資料庫連接"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

        self.logger.info("Database service closed")

    # ==========================================
    # Agent 狀態管理
    # ==========================================

    async def save_agent_state(self, agent_state: AgentState) -> None:
        """保存 Agent 狀態到資料庫"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                # 檢查 Agent 是否已存在
                stmt = select(DBAgent).where(DBAgent.id == agent_state.id)
                result = await session.execute(stmt)
                existing_agent = result.scalar_one_or_none()

                if existing_agent:
                    # 更新現有 Agent
                    await self._update_existing_agent(session, existing_agent, agent_state)
                else:
                    # 創建新 Agent
                    await self._create_new_agent(session, agent_state)

                await session.commit()
                self.logger.info(f"Agent state saved: {agent_state.id}")

            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to save agent state: {e}")
                raise

    async def _create_new_agent(self, session: AsyncSession, agent_state: AgentState) -> None:
        """創建新的 Agent 記錄"""
        config = agent_state.config

        db_agent = DBAgent(
            id=agent_state.id,
            name=agent_state.name,
            description=config.description,
            instructions=config.instructions,
            model=config.model,
            initial_funds=config.initial_funds,
            max_position_size=config.investment_preferences.max_position_size,
            status=agent_state.status.value,
            current_mode=agent_state.current_mode.value,
            config=self._serialize_config(config),
            investment_preferences=config.investment_preferences.preferred_sectors,
            strategy_adjustment_criteria=config.strategy_adjustment_criteria,
            auto_adjust_settings=self._serialize_auto_adjust(config.auto_adjust),
            created_at=agent_state.created_at,
            updated_at=agent_state.updated_at,
            last_active_at=agent_state.last_active_at,
        )

        session.add(db_agent)

    async def _update_existing_agent(
        self, session: AsyncSession, db_agent: DBAgent, agent_state: AgentState
    ) -> None:
        """更新現有的 Agent 記錄"""
        config = agent_state.config

        db_agent.name = agent_state.name
        db_agent.description = config.description
        db_agent.instructions = config.instructions
        db_agent.status = agent_state.status.value
        db_agent.current_mode = agent_state.current_mode.value
        db_agent.config = self._serialize_config(config)
        db_agent.investment_preferences = config.investment_preferences.preferred_sectors
        db_agent.strategy_adjustment_criteria = config.strategy_adjustment_criteria
        db_agent.auto_adjust_settings = self._serialize_auto_adjust(config.auto_adjust)
        db_agent.updated_at = agent_state.updated_at
        db_agent.last_active_at = agent_state.last_active_at

    async def load_agent_state(self, agent_id: str) -> AgentState | None:
        """從資料庫載入 Agent 狀態"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                stmt = select(DBAgent).where(DBAgent.id == agent_id)
                result = await session.execute(stmt)
                db_agent = result.scalar_one_or_none()

                if not db_agent:
                    return None

                # 轉換為 AgentState
                return await self._db_agent_to_state(db_agent)

            except Exception as e:
                self.logger.error(f"Failed to load agent state: {e}")
                raise

    async def _db_agent_to_state(self, db_agent: DBAgent) -> AgentState:
        """將資料庫 Agent 轉換為 AgentState"""
        # 重建 AgentConfig
        config = AgentConfig(
            name=db_agent.name,
            description=db_agent.description or "",
            instructions=db_agent.instructions,
            model=db_agent.model,
            initial_funds=db_agent.initial_funds,
            strategy_adjustment_criteria=db_agent.strategy_adjustment_criteria or "",
        )

        # 創建 AgentState
        state = AgentState(
            id=db_agent.id,
            name=db_agent.name,
            status=AgentStatus(db_agent.status),
            config=config,
            created_at=db_agent.created_at,
            updated_at=db_agent.updated_at,
            last_active_at=db_agent.last_active_at,
        )

        return state

    async def list_agents(
        self, status_filter: AgentStatus | None = None, limit: int = 50
    ) -> list[AgentState]:
        """列出所有 Agent"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                stmt = select(DBAgent).order_by(desc(DBAgent.created_at)).limit(limit)

                if status_filter:
                    stmt = stmt.where(DBAgent.status == status_filter.value)

                result = await session.execute(stmt)
                db_agents = result.scalars().all()

                # 轉換為 AgentState 列表
                agent_states = []
                for db_agent in db_agents:
                    state = await self._db_agent_to_state(db_agent)
                    agent_states.append(state)

                return agent_states

            except Exception as e:
                self.logger.error(f"Failed to list agents: {e}")
                raise

    async def delete_agent(self, agent_id: str) -> bool:
        """刪除 Agent 及其所有相關資料"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                stmt = select(DBAgent).where(DBAgent.id == agent_id)
                result = await session.execute(stmt)
                db_agent = result.scalar_one_or_none()

                if not db_agent:
                    return False

                # 由於設定了 CASCADE，相關資料會自動刪除
                await session.delete(db_agent)
                await session.commit()

                self.logger.info(f"Agent deleted: {agent_id}")
                return True

            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to delete agent: {e}")
                raise

    # ==========================================
    # Agent 會話管理
    # ==========================================

    async def save_agent_session(self, execution_result: AgentExecutionResult) -> None:
        """保存 Agent 執行會話"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                db_session = DBAgentSession(
                    id=execution_result.session_id,
                    agent_id=execution_result.agent_id,
                    session_type="execution",
                    mode=execution_result.mode.value,
                    status=execution_result.status.value,
                    start_time=execution_result.start_time,
                    end_time=execution_result.end_time,
                    execution_time_ms=execution_result.execution_time_ms,
                    initial_input=json.dumps(execution_result.initial_input),
                    final_output=json.dumps(execution_result.final_output),
                    tools_called=(
                        ",".join(execution_result.tools_called)
                        if execution_result.tools_called
                        else None
                    ),
                    error_message=execution_result.error_message,
                    trace_data=json.dumps(execution_result.trace_data),
                )

                session.add(db_session)
                await session.commit()

                self.logger.info(f"Session saved: {execution_result.session_id}")

            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to save session: {e}")
                raise

    async def get_agent_sessions(
        self,
        agent_id: str,
        limit: int = 20,
        status_filter: SessionStatus | None = None,
    ) -> list[AgentExecutionResult]:
        """獲取 Agent 執行會話歷史"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                stmt = (
                    select(DBAgentSession)
                    .where(DBAgentSession.agent_id == agent_id)
                    .order_by(desc(DBAgentSession.start_time))
                    .limit(limit)
                )

                if status_filter:
                    stmt = stmt.where(DBAgentSession.status == status_filter.value)

                result = await session.execute(stmt)
                db_sessions = result.scalars().all()

                # 轉換為 AgentExecutionResult
                execution_results = []
                for db_session in db_sessions:
                    execution_result = self._db_session_to_result(db_session)
                    execution_results.append(execution_result)

                return execution_results

            except Exception as e:
                self.logger.error(f"Failed to get agent sessions: {e}")
                raise

    def _db_session_to_result(self, db_session: DBAgentSession) -> AgentExecutionResult:
        """將資料庫會話轉換為執行結果"""
        return AgentExecutionResult(
            session_id=db_session.id,
            agent_id=db_session.agent_id,
            status=SessionStatus(db_session.status),
            mode=db_session.mode,  # type: ignore[arg-type]
            start_time=db_session.start_time,
            end_time=db_session.end_time,
            execution_time_ms=db_session.execution_time_ms or 0,
            turns_used=0,  # 需要從 trace_data 解析
            initial_input=(
                json.loads(db_session.initial_input) if db_session.initial_input else {}
            ),
            final_output=(json.loads(db_session.final_output) if db_session.final_output else {}),
            tools_called=(db_session.tools_called.split(",") if db_session.tools_called else []),
            error_message=db_session.error_message,
            error_type=None,  # 需要從 trace_data 解析
            trace_data=(json.loads(db_session.trace_data) if db_session.trace_data else {}),
        )

    # ==========================================
    # 策略變更管理
    # ==========================================

    async def save_strategy_change(self, agent_id: str, strategy_change: StrategyChange) -> None:
        """保存策略變更記錄"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                db_change = DBStrategyChange(
                    id=strategy_change.id,
                    agent_id=agent_id,
                    trigger_reason=strategy_change.trigger_reason,
                    change_type=strategy_change.change_type.value,
                    old_strategy=strategy_change.old_strategy,
                    new_strategy=strategy_change.new_strategy,
                    change_summary=strategy_change.change_summary,
                    performance_at_change=(
                        json.dumps(strategy_change.performance_at_change)
                        if strategy_change.performance_at_change
                        else None
                    ),
                    agent_explanation=strategy_change.agent_explanation,
                    timestamp=strategy_change.timestamp,
                )

                session.add(db_change)
                await session.commit()

                self.logger.info(f"Strategy change saved: {strategy_change.id}")

            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to save strategy change: {e}")
                raise

    async def get_strategy_changes(self, agent_id: str, limit: int = 20) -> list[StrategyChange]:
        """獲取策略變更歷史"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                stmt = (
                    select(DBStrategyChange)
                    .where(DBStrategyChange.agent_id == agent_id)
                    .order_by(desc(DBStrategyChange.timestamp))
                    .limit(limit)
                )

                result = await session.execute(stmt)
                db_changes = result.scalars().all()

                # 轉換為 StrategyChange
                strategy_changes = []
                for db_change in db_changes:
                    change = StrategyChange(
                        id=db_change.id,
                        agent_id=db_change.agent_id,
                        timestamp=db_change.timestamp,
                        trigger_reason=db_change.trigger_reason,
                        change_type=ChangeType(db_change.change_type),
                        old_strategy=db_change.old_strategy,
                        new_strategy=db_change.new_strategy,
                        change_summary=db_change.change_summary,
                        performance_at_change=(
                            json.loads(db_change.performance_at_change)
                            if db_change.performance_at_change
                            else None
                        ),
                        agent_explanation=db_change.agent_explanation,
                    )
                    strategy_changes.append(change)

                return strategy_changes

            except Exception as e:
                self.logger.error(f"Failed to get strategy changes: {e}")
                raise

    # ==========================================
    # 投資組合管理
    # ==========================================

    async def save_agent_holdings(self, agent_id: str, holdings: dict[str, Any]) -> None:
        """保存 Agent 持倉資料"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                # 先清除現有持倉
                await session.execute(
                    text("DELETE FROM agent_holdings WHERE agent_id = :agent_id"),
                    {"agent_id": agent_id},
                )

                # 插入新持倉
                for ticker, holding_data in holdings.items():
                    db_holding = AgentHolding(
                        agent_id=agent_id,
                        ticker=ticker,
                        company_name=holding_data.get("company_name"),
                        quantity=holding_data.get("quantity", 0),
                        average_cost=holding_data.get("average_cost", 0.0),
                        total_cost=holding_data.get("total_cost", 0.0),
                    )
                    session.add(db_holding)

                await session.commit()
                self.logger.info(f"Holdings saved for agent: {agent_id}")

            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to save holdings: {e}")
                raise

    async def get_agent_holdings(self, agent_id: str) -> list[AgentHolding]:
        """獲取 Agent 持倉資料"""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                stmt = select(AgentHolding).where(AgentHolding.agent_id == agent_id)
                result = await session.execute(stmt)
                db_holdings = result.scalars().all()

                return list(db_holdings)

            except Exception as e:
                self.logger.error(f"Failed to get holdings: {e}")
                raise

    async def get_agent_transactions(
        self, agent_id: str, limit: int = 100, offset: int = 0
    ) -> list:
        """
        獲取 Agent 交易歷史

        Args:
            agent_id: Agent ID
            limit: 返回數量限制
            offset: 偏移量

        Returns:
            交易記錄列表
        """
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                from .models import Transaction

                stmt = (
                    select(Transaction)
                    .where(Transaction.agent_id == agent_id)
                    .order_by(desc(Transaction.executed_at))
                    .limit(limit)
                    .offset(offset)
                )

                result = await session.execute(stmt)
                transactions = result.scalars().all()

                return list(transactions)

            except Exception as e:
                self.logger.error(f"Failed to get transactions: {e}")
                return []

    # ==========================================
    # AI 模型配置管理
    # ==========================================

    async def get_ai_model_config(self, model_key: str) -> dict[str, Any] | None:
        """
        獲取 AI 模型配置

        Args:
            model_key: 模型 key (例如: "gpt-4o", "claude-sonnet-4.5")

        Returns:
            模型配置字典,如果找不到則返回 None
        """
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                stmt = select(AIModelConfig).where(
                    AIModelConfig.model_key == model_key,
                    AIModelConfig.is_enabled == True,  # noqa: E712
                )

                result = await session.execute(stmt)
                model_config = result.scalar_one_or_none()

                if not model_config:
                    return None

                return {
                    "model_key": model_config.model_key,
                    "display_name": model_config.display_name,
                    "provider": model_config.provider,
                    "group_name": model_config.group_name,
                    "model_type": (
                        model_config.model_type.value
                        if hasattr(model_config.model_type, "value")
                        else model_config.model_type
                    ),
                    "litellm_prefix": model_config.litellm_prefix,
                    "full_model_name": model_config.full_model_name,
                    "max_tokens": model_config.max_tokens,
                    "cost_per_1k_tokens": (
                        float(model_config.cost_per_1k_tokens)
                        if model_config.cost_per_1k_tokens
                        else None
                    ),
                    "description": model_config.description,
                }

            except Exception as e:
                self.logger.error(f"Failed to get AI model config: {e}")
                return None

    async def list_ai_models(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        """
        列出所有 AI 模型

        Args:
            enabled_only: 是否只返回啟用的模型

        Returns:
            模型配置列表
        """
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")

        async with self.session_factory() as session:
            try:
                stmt = select(AIModelConfig).order_by(AIModelConfig.display_order)

                if enabled_only:
                    stmt = stmt.where(AIModelConfig.is_enabled == True)  # noqa: E712

                result = await session.execute(stmt)
                models = result.scalars().all()

                return [
                    {
                        "model_key": model.model_key,
                        "display_name": model.display_name,
                        "provider": model.provider,
                        "group_name": model.group_name,
                        "model_type": (
                            model.model_type.value
                            if hasattr(model.model_type, "value")
                            else model.model_type
                        ),
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

            except Exception as e:
                self.logger.error(f"Failed to list AI models: {e}")
                return []

    # ==========================================
    # 輔助方法
    # ==========================================

    def _serialize_config(self, config: AgentConfig) -> str:
        """序列化 Agent 配置"""
        config_dict = {
            "model": config.model,
            "max_turns": config.max_turns,
            "execution_timeout": config.execution_timeout,
            "enabled_tools": config.enabled_tools,
            "investment_preferences": {
                "preferred_sectors": config.investment_preferences.preferred_sectors,
                "excluded_tickers": config.investment_preferences.excluded_tickers,
                "max_position_size": config.investment_preferences.max_position_size,
                "risk_tolerance": config.investment_preferences.risk_tolerance,
            },
            "trading_settings": {
                "max_daily_trades": config.trading_settings.max_daily_trades,
                "enable_stop_loss": config.trading_settings.enable_stop_loss,
                "default_stop_loss_percent": config.trading_settings.default_stop_loss_percent,
            },
        }
        return json.dumps(config_dict, ensure_ascii=False)

    def _serialize_auto_adjust(self, auto_adjust: Any) -> str:
        """序列化自動調整設定"""
        auto_adjust_dict = {
            "enabled": auto_adjust.enabled,
            "triggers": auto_adjust.triggers,
            "auto_apply": auto_adjust.auto_apply,
            "max_adjustments_per_day": auto_adjust.max_adjustments_per_day,
        }
        return json.dumps(auto_adjust_dict, ensure_ascii=False)

    async def health_check(self) -> dict[str, Any]:
        """資料庫健康檢查"""
        if not self.session_factory:
            return {"status": "not_initialized", "error": "Database not initialized"}

        try:
            async with self.session_factory() as session:
                # 測試基本查詢
                result = await session.execute(text("SELECT 1"))
                result.fetchone()

                # 統計 Agent 數量
                agent_count_result = await session.execute(text("SELECT COUNT(*) FROM agents"))
                agent_count = agent_count_result.scalar()

                return {
                    "status": "healthy",
                    "agent_count": agent_count,
                    "database_url": self.config.database_url,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def __repr__(self) -> str:
        return f"AgentDatabaseService(url={self.config.database_url})"
