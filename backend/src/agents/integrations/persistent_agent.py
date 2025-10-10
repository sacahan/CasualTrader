"""
Persistent Agent - 具備資料庫持久化功能的 Agent 基類
整合 Agent 執行與 SQLite 資料庫儲存
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from typing import Any

from ..core.models import (
    AgentConfig,
    AgentExecutionResult,
    AgentMode,
    StrategyChange,
)
from ..trading.trading_agent import TradingAgent
from .database_service import AgentDatabaseService, DatabaseConfig

# ==========================================
# 具備持久化功能的 Trading Agent
# ==========================================


class PersistentTradingAgent(TradingAgent):
    """
    具備資料庫持久化功能的 Trading Agent
    自動保存執行狀態和結果到 SQLite
    """

    def __init__(
        self,
        config: AgentConfig,
        agent_id: str | None = None,
        database_config: DatabaseConfig | None = None,
    ) -> None:
        super().__init__(config, agent_id)

        # 資料庫服務
        self.db_service = AgentDatabaseService(database_config)
        self._db_initialized = False

        # 持久化設定
        self.auto_save_state = True
        self.auto_save_sessions = True
        self.auto_save_strategy_changes = True

        self.logger = logging.getLogger(f"persistent_agent.{self.agent_id}")

    # ==========================================
    # 生命週期管理（覆寫父類方法）
    # ==========================================

    async def initialize(self) -> None:
        """初始化 Agent 和資料庫連接"""
        # 初始化資料庫
        await self._initialize_database()

        # 嘗試從資料庫載入現有狀態
        await self._load_state_from_database()

        # 調用父類初始化
        await super().initialize()

        # 保存初始狀態
        if self.auto_save_state:
            await self._save_state_to_database()

        self.logger.info(f"Persistent agent {self.agent_id} initialized")

    async def shutdown(self) -> None:
        """關閉 Agent 並保存最終狀態"""
        # 保存最終狀態
        if self.auto_save_state:
            await self._save_state_to_database()

        # 調用父類關閉
        await super().shutdown()

        # 關閉資料庫連接
        await self.db_service.close()

        self.logger.info(f"Persistent agent {self.agent_id} shutdown")

    # ==========================================
    # 模型配置覆寫
    # ==========================================

    async def _get_model_config(self, model_key: str) -> dict[str, Any] | None:
        """
        從數據庫獲取模型配置

        Args:
            model_key: 模型 key (例如: "gpt-4o", "claude-sonnet-4.5")

        Returns:
            模型配置字典,如果找不到則返回 None
        """
        try:
            if not self._db_initialized:
                await self._initialize_database()

            model_config = await self.db_service.get_ai_model_config(model_key)

            if model_config:
                self.logger.debug(
                    f"Model config loaded for {model_key}: {model_config.get('display_name')}"
                )
                return {
                    "model_key": model_config["model_key"],
                    "display_name": model_config["display_name"],
                    "provider": model_config["provider"],
                    "model_type": model_config["model_type"],
                    "full_model_name": model_config["full_model_name"],
                    "litellm_prefix": model_config.get("litellm_prefix"),
                }
            else:
                self.logger.warning(
                    f"No model config found for {model_key}, using default OpenAI model"
                )
                return None

        except Exception as e:
            self.logger.warning(f"Failed to fetch model config for {model_key}: {e}")
            return None

    # ==========================================
    # 執行方法覆寫
    # ==========================================

    async def execute(
        self,
        mode: AgentMode | None = None,
        user_message: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentExecutionResult:
        """執行 Agent 任務並自動保存結果"""
        # 確保資料庫已初始化
        if not self._db_initialized:
            await self._initialize_database()

        # 執行前保存狀態
        if self.auto_save_state:
            await self._save_state_to_database()

        # 調用父類執行
        result = await super().execute(mode, user_message, context)

        # 執行後處理
        await self._post_execution_persistence(result)

        return result

    async def _post_execution_persistence(self, result: AgentExecutionResult) -> None:
        """執行後的持久化處理"""
        try:
            # 保存會話結果
            if self.auto_save_sessions:
                await self.db_service.save_agent_session(result)

            # 更新並保存 Agent 狀態
            if self.auto_save_state:
                await self._save_state_to_database()

            # 保存投資組合變更（如果有）
            await self._save_portfolio_if_changed()

            self.logger.debug(f"Post-execution persistence completed for {result.session_id}")

        except Exception as e:
            self.logger.error(f"Failed to persist execution data: {e}")
            # 不拋出異常，避免影響主執行流程

    # ==========================================
    # 策略變更持久化
    # ==========================================

    async def record_strategy_change(
        self,
        trigger_reason: str,
        new_strategy_addition: str,
        change_summary: str,
        agent_explanation: str,
    ) -> dict[str, Any]:
        """記錄策略變更並保存到資料庫"""
        # 調用父類方法
        result = await super().record_strategy_change(
            trigger_reason, new_strategy_addition, change_summary, agent_explanation
        )

        # 保存到資料庫
        if self.auto_save_strategy_changes and result["success"]:
            try:
                # 從策略變更歷史中獲取最新記錄
                strategy_changes = self.get_strategy_changes()
                if strategy_changes:
                    latest_change = strategy_changes[-1]

                    # 轉換為 StrategyChange 模型
                    strategy_change = StrategyChange(
                        id=latest_change["id"],
                        agent_id=self.agent_id,
                        trigger_reason=latest_change["trigger_reason"],
                        new_strategy=latest_change["new_strategy_addition"],
                        change_summary=latest_change["change_summary"],
                        agent_explanation=latest_change["agent_explanation"],
                        performance_at_change=latest_change["performance_at_change"],
                    )

                    await self.db_service.save_strategy_change(self.agent_id, strategy_change)

                    self.logger.info(f"Strategy change persisted: {strategy_change.id}")

            except Exception as e:
                self.logger.error(f"Failed to persist strategy change: {e}")

        return result

    # ==========================================
    # 資料庫操作方法
    # ==========================================

    async def _initialize_database(self) -> None:
        """初始化資料庫連接"""
        if self._db_initialized:
            return

        await self.db_service.initialize()
        self._db_initialized = True

        self.logger.debug("Database connection initialized")

    async def _load_state_from_database(self) -> None:
        """從資料庫載入 Agent 狀態"""
        try:
            stored_state = await self.db_service.load_agent_state(self.agent_id)

            if stored_state:
                # 更新當前狀態
                self.state = stored_state
                self.config = stored_state.config

                self.logger.info(f"Agent state loaded from database: {self.agent_id}")
            else:
                self.logger.info(f"No existing state found for agent: {self.agent_id}")

        except Exception as e:
            self.logger.warning(f"Failed to load state from database: {e}")
            # 繼續使用預設狀態

    async def _save_state_to_database(self) -> None:
        """保存 Agent 狀態到資料庫"""
        try:
            await self.db_service.save_agent_state(self.state)
            self.logger.debug(f"Agent state saved to database: {self.agent_id}")

        except Exception as e:
            self.logger.error(f"Failed to save state to database: {e}")

    async def _save_portfolio_if_changed(self) -> None:
        """保存投資組合變更"""
        try:
            # 獲取當前持倉
            current_holdings = self._get_current_holdings()

            if current_holdings:
                await self.db_service.save_agent_holdings(self.agent_id, current_holdings)
                self.logger.debug(f"Portfolio saved for agent: {self.agent_id}")

        except Exception as e:
            self.logger.error(f"Failed to save portfolio: {e}")

    # ==========================================
    # 歷史資料查詢
    # ==========================================

    async def get_execution_history(self, limit: int = 20) -> list[AgentExecutionResult]:
        """獲取執行歷史"""
        if not self._db_initialized:
            await self._initialize_database()

        return await self.db_service.get_agent_sessions(self.agent_id, limit)

    async def get_strategy_change_history(self, limit: int = 20) -> list[StrategyChange]:
        """獲取策略變更歷史"""
        if not self._db_initialized:
            await self._initialize_database()

        return await self.db_service.get_strategy_changes(self.agent_id, limit)

    async def get_portfolio_history(self) -> dict[str, Any]:
        """獲取投資組合歷史"""
        if not self._db_initialized:
            await self._initialize_database()

        return await self.db_service.get_agent_holdings(self.agent_id)

    # ==========================================
    # 統計和分析
    # ==========================================

    async def get_performance_analytics(self) -> dict[str, Any]:
        """獲取詳細績效分析"""
        try:
            # 獲取執行歷史
            execution_history = await self.get_execution_history(100)

            # 計算統計指標
            total_executions = len(execution_history)
            successful_executions = sum(
                1 for result in execution_history if result.status.value == "completed"
            )

            success_rate = (
                (successful_executions / total_executions * 100) if total_executions > 0 else 0.0
            )

            avg_execution_time = (
                sum(result.execution_time_ms for result in execution_history) / total_executions
                if total_executions > 0
                else 0.0
            )

            # 統計模式使用
            mode_usage = {}
            for result in execution_history:
                mode = result.mode.value
                mode_usage[mode] = mode_usage.get(mode, 0) + 1

            # 獲取策略變更統計
            strategy_changes = await self.get_strategy_change_history()

            # 獲取投資組合狀況
            portfolio = await self.get_portfolio_history()

            return {
                "execution_stats": {
                    "total_executions": total_executions,
                    "successful_executions": successful_executions,
                    "success_rate": round(success_rate, 2),
                    "avg_execution_time_ms": round(avg_execution_time, 2),
                },
                "mode_usage": mode_usage,
                "strategy_changes_count": len(strategy_changes),
                "portfolio_positions": len(portfolio),
                "analysis_timestamp": self.state.updated_at.isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to generate performance analytics: {e}")
            return {"error": str(e)}

    # ==========================================
    # 配置管理
    # ==========================================

    def enable_auto_persistence(
        self, state: bool = True, sessions: bool = True, strategies: bool = True
    ) -> None:
        """啟用/停用自動持久化"""
        self.auto_save_state = state
        self.auto_save_sessions = sessions
        self.auto_save_strategy_changes = strategies

        self.logger.info(
            f"Auto persistence configured - State: {state}, "
            f"Sessions: {sessions}, Strategies: {strategies}"
        )

    async def backup_agent_data(self) -> dict[str, Any]:
        """備份 Agent 的所有資料"""
        try:
            backup_data = {
                "agent_state": self.state.model_dump(),
                "execution_history": [
                    result.model_dump() for result in await self.get_execution_history(1000)
                ],
                "strategy_changes": [
                    change.model_dump() for change in await self.get_strategy_change_history(1000)
                ],
                "portfolio": await self.get_portfolio_history(),
                "performance_analytics": await self.get_performance_analytics(),
                "backup_timestamp": self.state.updated_at.isoformat(),
            }

            self.logger.info(f"Agent data backup created for: {self.agent_id}")
            return backup_data

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise

    # ==========================================
    # 健康檢查
    # ==========================================

    async def health_check(self) -> dict[str, Any]:
        """Agent 和資料庫健康檢查"""
        agent_health = {
            "agent_id": self.agent_id,
            "status": self.state.status.value,
            "is_active": self.is_active,
            "database_initialized": self._db_initialized,
        }

        if self._db_initialized:
            db_health = await self.db_service.health_check()
            agent_health["database"] = db_health
        else:
            agent_health["database"] = {"status": "not_initialized"}

        return agent_health

    def __repr__(self) -> str:
        return (
            f"PersistentTradingAgent(id={self.agent_id}, "
            f"name='{self.config.name}', "
            f"status={self.state.status}, "
            f"db_enabled={self._db_initialized})"
        )
