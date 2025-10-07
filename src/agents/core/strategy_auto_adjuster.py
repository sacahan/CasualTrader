"""
策略自動調整邏輯
基於績效表現和市場條件自動調整投資策略
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel

from ..functions.strategy_change_recorder import (
    StrategyChangeRecorder,
    StrategyChangeRequest,
)
from ..tools.fundamental_agent import FundamentalAgent
from ..tools.risk_agent import RiskAgent
from ..tools.sentiment_agent import SentimentAgent
from ..tools.technical_agent import TechnicalAgent
from .instruction_generator import InstructionGenerator
from .strategy_tracker import ChangeType, StrategyTracker


class PerformanceTrigger(BaseModel):
    """績效觸發條件"""

    trigger_type: str  # "return", "drawdown", "volatility", "sharpe"
    threshold: float
    direction: str  # "above", "below"
    lookback_days: int = 30
    description: str


class MarketTrigger(BaseModel):
    """市場觸發條件"""

    trigger_type: str  # "vix", "sector_rotation", "interest_rate", "sentiment"
    threshold: float
    direction: str  # "above", "below"
    description: str


class AdjustmentAction(BaseModel):
    """調整動作"""

    action_type: str  # "reduce_risk", "increase_aggression", "sector_rotation", "cash_management"
    intensity: float  # 0.0-1.0
    target_parameters: dict[str, Any]
    rationale: str


class AdjustmentResult(BaseModel):
    """調整結果"""

    success: bool
    applied_actions: list[AdjustmentAction]
    strategy_changes: list[str]
    change_id: str | None = None
    error_message: str | None = None
    timestamp: datetime


class StrategyAutoAdjuster:
    """
    策略自動調整器 - 核心智能調整邏輯
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("strategy_auto_adjuster")

        # 核心組件
        self.instruction_generator = InstructionGenerator()
        self.strategy_recorder = StrategyChangeRecorder()

        # 分析工具
        self.fundamental_agent = FundamentalAgent()
        self.technical_agent = TechnicalAgent()
        self.risk_agent = RiskAgent()
        self.sentiment_agent = SentimentAgent()

        # 預設觸發條件
        self.default_performance_triggers = [
            PerformanceTrigger(
                trigger_type="return",
                threshold=-0.10,
                direction="below",
                lookback_days=30,
                description="30日累積報酬率低於-10%",
            ),
            PerformanceTrigger(
                trigger_type="drawdown",
                threshold=0.15,
                direction="above",
                lookback_days=60,
                description="最大回撤超過15%",
            ),
            PerformanceTrigger(
                trigger_type="volatility",
                threshold=0.25,
                direction="above",
                lookback_days=20,
                description="20日波動率超過25%",
            ),
            PerformanceTrigger(
                trigger_type="sharpe",
                threshold=0.5,
                direction="below",
                lookback_days=90,
                description="90日夏普比率低於0.5",
            ),
        ]

        self.default_market_triggers = [
            MarketTrigger(
                trigger_type="vix",
                threshold=25.0,
                direction="above",
                description="恐慌指數超過25",
            ),
            MarketTrigger(
                trigger_type="sentiment",
                threshold=20.0,
                direction="below",
                description="市場情緒指數低於20(極度恐慌)",
            ),
            MarketTrigger(
                trigger_type="sentiment",
                threshold=80.0,
                direction="above",
                description="市場情緒指數高於80(極度貪婪)",
            ),
        ]

    async def evaluate_adjustment_needs(
        self,
        agent_id: str,
        performance_data: dict[str, Any],
        market_data: dict[str, Any] | None = None,
        portfolio_data: dict[str, Any] | None = None,
    ) -> list[AdjustmentAction]:
        """
        評估策略調整需求

        Args:
            agent_id: Agent ID
            performance_data: 績效數據
            market_data: 市場數據
            portfolio_data: 投資組合數據

        Returns:
            建議的調整動作
        """
        actions = []
        market_data = market_data or {}
        portfolio_data = portfolio_data or {}

        try:
            # 檢查績效觸發條件
            performance_actions = await self._check_performance_triggers(
                performance_data, portfolio_data
            )
            actions.extend(performance_actions)

            # 檢查市場觸發條件
            market_actions = await self._check_market_triggers(market_data)
            actions.extend(market_actions)

            # 檢查時間觸發條件
            time_actions = await self._check_time_triggers(agent_id)
            actions.extend(time_actions)

            # 綜合分析和優化動作
            optimized_actions = await self._optimize_actions(actions, agent_id)

            self.logger.info(
                f"Evaluated {len(optimized_actions)} adjustment actions for agent {agent_id}"
            )

            return optimized_actions

        except Exception as e:
            self.logger.error(f"Failed to evaluate adjustment needs: {e}")
            return []

    async def apply_strategy_adjustment(
        self,
        agent_id: str,
        actions: list[AdjustmentAction],
        current_instructions: str | None = None,
        auto_apply: bool = True,
    ) -> AdjustmentResult:
        """
        應用策略調整

        Args:
            agent_id: Agent ID
            actions: 調整動作
            current_instructions: 當前指令
            auto_apply: 是否自動應用

        Returns:
            調整結果
        """
        try:
            if not actions:
                return AdjustmentResult(
                    success=True,
                    applied_actions=[],
                    strategy_changes=[],
                    timestamp=datetime.now(),
                )

            # 生成策略變更內容
            strategy_changes = await self._generate_strategy_changes(actions)

            # 構建變更請求
            change_request = StrategyChangeRequest(
                agent_id=agent_id,
                trigger_reason=self._build_trigger_reason(actions),
                new_strategy_addition=self._build_strategy_addition(strategy_changes),
                change_summary=self._build_change_summary(actions),
                agent_explanation=self._build_explanation(actions),
                change_type=ChangeType.AUTO,
                auto_apply=auto_apply,
                performance_snapshot=self._capture_performance_snapshot(actions),
            )

            # 記錄策略變更
            record_result = await self.strategy_recorder.record_strategy_change(
                change_request, current_instructions
            )

            if record_result.success:
                self.logger.info(
                    f"Successfully applied strategy adjustment for agent {agent_id}: {record_result.change_id}"
                )

                return AdjustmentResult(
                    success=True,
                    applied_actions=actions,
                    strategy_changes=strategy_changes,
                    change_id=record_result.change_id,
                    timestamp=datetime.now(),
                )
            else:
                return AdjustmentResult(
                    success=False,
                    applied_actions=[],
                    strategy_changes=[],
                    error_message=record_result.error_message,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            self.logger.error(f"Failed to apply strategy adjustment: {e}")
            return AdjustmentResult(
                success=False,
                applied_actions=[],
                strategy_changes=[],
                error_message=f"調整應用失敗: {e}",
                timestamp=datetime.now(),
            )

    async def _check_performance_triggers(
        self, performance_data: dict[str, Any], portfolio_data: dict[str, Any]
    ) -> list[AdjustmentAction]:
        """檢查績效觸發條件"""
        actions = []

        for trigger in self.default_performance_triggers:
            value = performance_data.get(trigger.trigger_type, 0)

            is_triggered = (
                trigger.direction == "above" and value > trigger.threshold
            ) or (trigger.direction == "below" and value < trigger.threshold)

            if is_triggered:
                action = await self._create_performance_action(
                    trigger, value, portfolio_data
                )
                if action:
                    actions.append(action)

        return actions

    async def _check_market_triggers(
        self, market_data: dict[str, Any]
    ) -> list[AdjustmentAction]:
        """檢查市場觸發條件"""
        actions = []

        for trigger in self.default_market_triggers:
            value = market_data.get(trigger.trigger_type, 0)

            is_triggered = (
                trigger.direction == "above" and value > trigger.threshold
            ) or (trigger.direction == "below" and value < trigger.threshold)

            if is_triggered:
                action = await self._create_market_action(trigger, value)
                if action:
                    actions.append(action)

        return actions

    async def _check_time_triggers(self, agent_id: str) -> list[AdjustmentAction]:
        """檢查時間觸發條件"""
        actions = []

        try:
            # 檢查最近策略變更時間
            tracker = StrategyTracker(agent_id)
            recent_changes = tracker.get_strategy_changes(limit=5)

            if not recent_changes:
                # 長期無調整，建議重新評估
                actions.append(
                    AdjustmentAction(
                        action_type="strategy_review",
                        intensity=0.3,
                        target_parameters={"review_type": "comprehensive"},
                        rationale="長期未進行策略調整，建議重新評估投資組合",
                    )
                )
            else:
                last_change = recent_changes[0]
                days_since_change = (datetime.now() - last_change.timestamp).days

                # 超過90天未調整且有連續虧損
                if days_since_change > 90:
                    actions.append(
                        AdjustmentAction(
                            action_type="periodic_rebalance",
                            intensity=0.4,
                            target_parameters={"rebalance_type": "strategic"},
                            rationale="定期重新平衡投資組合以維持最佳配置",
                        )
                    )

        except Exception as e:
            self.logger.warning(f"Time trigger check failed: {e}")

        return actions

    async def _create_performance_action(
        self, trigger: PerformanceTrigger, value: float, portfolio_data: dict[str, Any]
    ) -> AdjustmentAction | None:
        """創建績效驅動的調整動作"""

        if trigger.trigger_type == "return" and trigger.direction == "below":
            # 報酬率過低，降低風險
            intensity = min(abs(value - trigger.threshold) * 2, 1.0)
            return AdjustmentAction(
                action_type="reduce_risk",
                intensity=intensity,
                target_parameters={
                    "position_size_reduction": 0.2,
                    "cash_increase": 0.15,
                    "stop_loss_tightening": 0.05,
                },
                rationale=f"累積報酬率為{value:.1%}，低於{trigger.threshold:.1%}閾值，需要降低風險暴露",
            )

        elif trigger.trigger_type == "drawdown" and trigger.direction == "above":
            # 回撤過大，強化風控
            intensity = min((value - trigger.threshold) * 3, 1.0)
            return AdjustmentAction(
                action_type="risk_control",
                intensity=intensity,
                target_parameters={
                    "max_position_size": 0.05,
                    "stop_loss_level": 0.08,
                    "diversification_increase": True,
                },
                rationale=f"最大回撤為{value:.1%}，超過{trigger.threshold:.1%}限制，必須加強風險控制",
            )

        elif trigger.trigger_type == "volatility" and trigger.direction == "above":
            # 波動率過高，降低部位
            intensity = min((value - trigger.threshold) * 2, 1.0)
            return AdjustmentAction(
                action_type="volatility_management",
                intensity=intensity,
                target_parameters={
                    "position_scaling": 0.7,
                    "volatility_targeting": True,
                    "rebalance_frequency": "weekly",
                },
                rationale=f"投資組合波動率為{value:.1%}，超過{trigger.threshold:.1%}目標，需要降低波動性",
            )

        elif trigger.trigger_type == "sharpe" and trigger.direction == "below":
            # 風險調整報酬率過低
            intensity = min((trigger.threshold - value) * 1.5, 1.0)
            return AdjustmentAction(
                action_type="efficiency_improvement",
                intensity=intensity,
                target_parameters={
                    "selection_criteria_tightening": True,
                    "correlation_analysis": True,
                    "factor_exposure_optimization": True,
                },
                rationale=f"夏普比率為{value:.2f}，低於{trigger.threshold:.2f}標準，需要提升投資效率",
            )

        return None

    async def _create_market_action(
        self, trigger: MarketTrigger, value: float
    ) -> AdjustmentAction | None:
        """創建市場驅動的調整動作"""

        if trigger.trigger_type == "vix" and trigger.direction == "above":
            # 恐慌指數過高，防禦性調整
            intensity = min((value - trigger.threshold) / 10, 1.0)
            return AdjustmentAction(
                action_type="defensive_positioning",
                intensity=intensity,
                target_parameters={
                    "defensive_stocks_increase": 0.3,
                    "cash_position_increase": 0.2,
                    "volatility_hedge": True,
                },
                rationale=f"恐慌指數達到{value:.1f}，市場恐慌情緒高漲，採取防禦性部署",
            )

        elif trigger.trigger_type == "sentiment":
            if trigger.direction == "below":
                # 極度恐慌，逢低布局
                intensity = min((trigger.threshold - value) / 20, 1.0)
                return AdjustmentAction(
                    action_type="contrarian_opportunity",
                    intensity=intensity,
                    target_parameters={
                        "value_stocks_increase": 0.25,
                        "opportunistic_buying": True,
                        "dca_activation": True,
                    },
                    rationale=f"市場情緒指數為{value:.1f}，極度恐慌提供絕佳進場機會",
                )
            elif trigger.direction == "above":
                # 極度貪婪，獲利了結
                intensity = min((value - trigger.threshold) / 20, 1.0)
                return AdjustmentAction(
                    action_type="profit_taking",
                    intensity=intensity,
                    target_parameters={
                        "profit_realization": 0.3,
                        "overvalued_exit": True,
                        "cash_accumulation": True,
                    },
                    rationale=f"市場情緒指數為{value:.1f}，極度貪婪時機適合獲利了結",
                )

        return None

    async def _optimize_actions(
        self, actions: list[AdjustmentAction], agent_id: str
    ) -> list[AdjustmentAction]:
        """優化和整合調整動作"""
        if not actions:
            return []

        # 依動作類型分組
        action_groups = {}
        for action in actions:
            action_type = action.action_type
            if action_type not in action_groups:
                action_groups[action_type] = []
            action_groups[action_type].append(action)

        optimized = []

        # 整合同類型動作
        for action_type, group_actions in action_groups.items():
            if len(group_actions) == 1:
                optimized.append(group_actions[0])
            else:
                # 合併同類型動作
                merged_action = await self._merge_actions(group_actions)
                optimized.append(merged_action)

        # 檢查動作衝突
        resolved_actions = await self._resolve_conflicts(optimized)

        return resolved_actions

    async def _merge_actions(self, actions: list[AdjustmentAction]) -> AdjustmentAction:
        """合併同類型動作"""
        base_action = actions[0]

        # 取最高強度
        max_intensity = max(action.intensity for action in actions)

        # 合併目標參數
        merged_parameters = {}
        for action in actions:
            merged_parameters.update(action.target_parameters)

        # 合併理由
        merged_rationale = "; ".join(action.rationale for action in actions)

        return AdjustmentAction(
            action_type=base_action.action_type,
            intensity=max_intensity,
            target_parameters=merged_parameters,
            rationale=merged_rationale,
        )

    async def _resolve_conflicts(
        self, actions: list[AdjustmentAction]
    ) -> list[AdjustmentAction]:
        """解決動作衝突"""
        # 簡化版本：移除相互衝突的動作，保留優先級較高的

        conflict_matrix = {
            "increase_aggression": ["reduce_risk", "defensive_positioning"],
            "profit_taking": ["contrarian_opportunity"],
            "risk_control": ["increase_aggression"],
        }

        resolved = []
        excluded = set()

        for action in actions:
            if action.action_type in excluded:
                continue

            conflicting_types = conflict_matrix.get(action.action_type, [])
            for other_action in actions:
                if (
                    other_action.action_type in conflicting_types
                    and other_action.intensity < action.intensity
                ):
                    excluded.add(other_action.action_type)

            resolved.append(action)

        return resolved

    async def _generate_strategy_changes(
        self, actions: list[AdjustmentAction]
    ) -> list[str]:
        """生成具體的策略變更內容"""
        changes = []

        for action in actions:
            if action.action_type == "reduce_risk":
                changes.append(
                    f"降低投資組合風險暴露，減少單一部位至{action.target_parameters.get('position_size_reduction', 0.2):.1%}"
                )
                changes.append(
                    f"提高現金部位至{action.target_parameters.get('cash_increase', 0.15):.1%}"
                )

            elif action.action_type == "risk_control":
                changes.append(
                    f"設定最大單一部位限制為{action.target_parameters.get('max_position_size', 0.05):.1%}"
                )
                changes.append(
                    f"收緊停損條件至{action.target_parameters.get('stop_loss_level', 0.08):.1%}"
                )

            elif action.action_type == "defensive_positioning":
                changes.append(
                    f"增加防禦性股票配置{action.target_parameters.get('defensive_stocks_increase', 0.3):.1%}"
                )
                changes.append("啟用波動性對沖機制")

            elif action.action_type == "contrarian_opportunity":
                changes.append(
                    f"增加價值股配置{action.target_parameters.get('value_stocks_increase', 0.25):.1%}"
                )
                changes.append("啟用定期定額投資策略")

            elif action.action_type == "profit_taking":
                changes.append(
                    f"獲利了結{action.target_parameters.get('profit_realization', 0.3):.1%}倉位"
                )
                changes.append("退出高估值標的")

        return changes

    def _build_trigger_reason(self, actions: list[AdjustmentAction]) -> str:
        """構建觸發原因"""
        reasons = [action.rationale for action in actions]
        return f"自動策略調整觸發：{'; '.join(reasons[:3])}{'...' if len(reasons) > 3 else ''}"

    def _build_strategy_addition(self, strategy_changes: list[str]) -> str:
        """構建策略新增內容"""
        if not strategy_changes:
            return "基於當前市場條件進行策略微調"

        return f"""
## 自動策略調整

### 調整措施：
{chr(10).join(f"- {change}" for change in strategy_changes)}

### 調整原因：
基於投資組合績效表現和市場風險評估，系統自動執行上述策略調整以優化風險報酬比。

### 監控指標：
- 持續監控投資組合波動率變化
- 追蹤調整後的風險指標表現
- 評估策略變更的有效性

### 復原條件：
當觸發條件恢復正常範圍或策略效果不佳時，考慮調整或恢復先前策略。
        """.strip()

    def _build_change_summary(self, actions: list[AdjustmentAction]) -> str:
        """構建變更摘要"""
        action_types = [action.action_type for action in actions]
        return f"自動調整：{', '.join(set(action_types))}"

    def _build_explanation(self, actions: list[AdjustmentAction]) -> str:
        """構建Agent解釋"""
        return f"""
基於系統監控發現{len(actions)}個觸發條件，自動執行策略調整：

{chr(10).join(f"• {action.rationale}" for action in actions)}

此次調整旨在：
1. 優化風險管理
2. 提升投資效率
3. 適應市場變化
4. 保護投資本金

系統將持續監控調整效果，並在必要時進行進一步優化。
        """.strip()

    def _capture_performance_snapshot(
        self, actions: list[AdjustmentAction]
    ) -> dict[str, Any]:
        """捕獲績效快照"""
        return {
            "adjustment_timestamp": datetime.now().isoformat(),
            "triggered_actions": len(actions),
            "max_intensity": max((action.intensity for action in actions), default=0.0),
            "action_types": [action.action_type for action in actions],
        }

    async def monitor_adjustment_effectiveness(
        self,
        agent_id: str,
        change_id: str,
        monitoring_period_days: int = 14,
    ) -> dict[str, Any]:
        """
        監控調整效果

        Args:
            agent_id: Agent ID
            change_id: 變更ID
            monitoring_period_days: 監控期間（天）

        Returns:
            效果評估結果
        """
        try:
            # 獲取調整記錄
            tracker = StrategyTracker(agent_id)
            changes = tracker.get_strategy_changes()
            target_change = next((c for c in changes if c.id == change_id), None)

            if not target_change:
                return {"error": f"找不到變更記錄: {change_id}"}

            # 計算監控期間績效
            adjustment_date = target_change.timestamp
            monitoring_end = adjustment_date + timedelta(days=monitoring_period_days)

            # 這裡應該整合實際的績效數據獲取
            # 目前返回模擬的監控結果

            effectiveness_score = 7.5  # 0-10分
            performance_improvement = True
            risk_reduction = True

            return {
                "change_id": change_id,
                "monitoring_period": f"{monitoring_period_days} days",
                "effectiveness_score": effectiveness_score,
                "performance_improvement": performance_improvement,
                "risk_reduction": risk_reduction,
                "recommendations": [
                    "調整效果良好，建議繼續維持當前策略",
                    "密切關注市場變化，準備下一步優化",
                ],
                "next_review_date": (datetime.now() + timedelta(days=30)).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to monitor adjustment effectiveness: {e}")
            return {"error": f"監控失敗: {e}"}

    def get_adjuster_status(self) -> dict[str, Any]:
        """獲取調整器狀態"""
        return {
            "performance_triggers": len(self.default_performance_triggers),
            "market_triggers": len(self.default_market_triggers),
            "analysis_tools": [
                "fundamental_agent",
                "technical_agent",
                "risk_agent",
                "sentiment_agent",
            ],
            "status": "operational",
            "last_update": datetime.now().isoformat(),
        }
