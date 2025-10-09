"""
策略變更追蹤器
追蹤和管理 TradingAgent 的策略演化過程
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .models import AgentConfig, ChangeType


class StrategyChange(BaseModel):
    """策略變更記錄"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    change_type: ChangeType
    trigger_reason: str
    new_strategy_addition: str
    change_summary: str
    agent_explanation: str
    performance_before: dict[str, Any] = Field(default_factory=dict)
    performance_after: dict[str, Any] | None = None
    auto_applied: bool = False
    effectiveness_score: float | None = None
    user_feedback: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "change_type": self.change_type,
            "trigger_reason": self.trigger_reason,
            "new_strategy_addition": self.new_strategy_addition,
            "change_summary": self.change_summary,
            "agent_explanation": self.agent_explanation,
            "performance_before": self.performance_before,
            "performance_after": self.performance_after,
            "auto_applied": self.auto_applied,
            "effectiveness_score": self.effectiveness_score,
            "user_feedback": self.user_feedback,
        }


class StrategyTracker:
    """
    策略變更追蹤器 - 管理 Agent 策略演化歷史
    """

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"strategy_tracker.{agent_id}")
        self._changes: list[StrategyChange] = []

    def record_strategy_change(
        self,
        trigger_reason: str,
        new_strategy_addition: str,
        change_summary: str,
        agent_explanation: str,
        change_type: ChangeType = ChangeType.AUTO,
        performance_snapshot: dict[str, Any] | None = None,
        auto_applied: bool = True,
    ) -> StrategyChange:
        """
        記錄策略變更

        Args:
            trigger_reason: 觸發策略變更的原因
            new_strategy_addition: 新增的策略內容
            change_summary: 變更摘要
            agent_explanation: Agent 的變更解釋
            change_type: 變更類型
            performance_snapshot: 變更時的績效快照
            auto_applied: 是否自動套用

        Returns:
            策略變更記錄
        """
        try:
            change = StrategyChange(
                agent_id=self.agent_id,
                change_type=change_type,
                trigger_reason=trigger_reason,
                new_strategy_addition=new_strategy_addition,
                change_summary=change_summary,
                agent_explanation=agent_explanation,
                performance_before=performance_snapshot or {},
                auto_applied=auto_applied,
            )

            self._changes.append(change)

            self.logger.info(f"Strategy change recorded: {change.id} - {change_summary}")

            return change

        except Exception as e:
            self.logger.error(f"Failed to record strategy change: {e}")
            raise

    def get_strategy_changes(
        self,
        limit: int | None = None,
        change_type: ChangeType | None = None,
        since: datetime | None = None,
    ) -> list[StrategyChange]:
        """
        獲取策略變更歷史

        Args:
            limit: 返回記錄數量限制
            change_type: 篩選變更類型
            since: 篩選時間起點

        Returns:
            策略變更記錄列表
        """
        filtered_changes = self._changes.copy()

        # 時間篩選
        if since:
            filtered_changes = [change for change in filtered_changes if change.timestamp >= since]

        # 類型篩選
        if change_type:
            filtered_changes = [
                change for change in filtered_changes if change.change_type == change_type
            ]

        # 按時間排序（最新的在前）
        filtered_changes.sort(key=lambda x: x.timestamp, reverse=True)

        # 數量限制
        if limit:
            filtered_changes = filtered_changes[:limit]

        return filtered_changes

    def get_latest_change(self) -> StrategyChange | None:
        """獲取最新的策略變更"""
        if not self._changes:
            return None
        return max(self._changes, key=lambda x: x.timestamp)

    def update_change_effectiveness(
        self,
        change_id: str,
        effectiveness_score: float,
        performance_after: dict[str, Any] | None = None,
        user_feedback: str | None = None,
    ) -> bool:
        """
        更新策略變更的效果評估

        Args:
            change_id: 變更記錄 ID
            effectiveness_score: 效果評分 (0.0-10.0)
            performance_after: 變更後的績效數據
            user_feedback: 用戶反饋

        Returns:
            是否更新成功
        """
        try:
            for change in self._changes:
                if change.id == change_id:
                    change.effectiveness_score = max(0.0, min(10.0, effectiveness_score))
                    if performance_after:
                        change.performance_after = performance_after
                    if user_feedback:
                        change.user_feedback = user_feedback

                    self.logger.info(
                        f"Updated effectiveness for change {change_id}: {effectiveness_score}"
                    )
                    return True

            self.logger.warning(f"Strategy change not found: {change_id}")
            return False

        except Exception as e:
            self.logger.error(f"Failed to update change effectiveness: {e}")
            return False

    def get_strategy_evolution_summary(self) -> dict[str, Any]:
        """
        獲取策略演化摘要

        Returns:
            策略演化摘要資訊
        """
        if not self._changes:
            return {
                "total_changes": 0,
                "evolution_timeline": [],
                "performance_trend": None,
                "most_effective_changes": [],
            }

        # 統計資訊
        total_changes = len(self._changes)
        auto_changes = len([c for c in self._changes if c.change_type == ChangeType.AUTO])
        manual_changes = len([c for c in self._changes if c.change_type == ChangeType.MANUAL])
        performance_driven = len(
            [c for c in self._changes if c.change_type == ChangeType.PERFORMANCE_DRIVEN]
        )

        # 演化時間軸
        timeline = []
        for change in sorted(self._changes, key=lambda x: x.timestamp):
            timeline.append(
                {
                    "date": change.timestamp.strftime("%Y-%m-%d"),
                    "summary": change.change_summary,
                    "type": change.change_type,
                    "effectiveness": change.effectiveness_score,
                }
            )

        # 最有效的變更
        effective_changes = [
            c
            for c in self._changes
            if c.effectiveness_score is not None and c.effectiveness_score >= 7.0
        ]
        effective_changes.sort(key=lambda x: x.effectiveness_score or 0, reverse=True)

        # 績效趨勢分析
        performance_trend = self._analyze_performance_trend()

        return {
            "total_changes": total_changes,
            "change_breakdown": {
                "auto": auto_changes,
                "manual": manual_changes,
                "performance_driven": performance_driven,
            },
            "evolution_timeline": timeline,
            "performance_trend": performance_trend,
            "most_effective_changes": [
                {
                    "id": c.id,
                    "summary": c.change_summary,
                    "effectiveness": c.effectiveness_score,
                    "date": c.timestamp.strftime("%Y-%m-%d"),
                }
                for c in effective_changes[:5]
            ],
            "recent_changes": [
                {
                    "summary": c.change_summary,
                    "date": c.timestamp.strftime("%Y-%m-%d"),
                    "auto_applied": c.auto_applied,
                }
                for c in self.get_strategy_changes(limit=3)
            ],
        }

    def _analyze_performance_trend(self) -> dict[str, Any] | None:
        """分析績效趨勢"""
        changes_with_performance = [
            c for c in self._changes if c.performance_before and c.performance_after
        ]

        if not changes_with_performance:
            return None

        try:
            # 計算平均改善程度
            improvements = []
            for change in changes_with_performance:
                before_return = change.performance_before.get("total_return", 0)
                after_return = change.performance_after.get("total_return", 0)
                improvement = after_return - before_return
                improvements.append(improvement)

            avg_improvement = sum(improvements) / len(improvements) if improvements else 0

            return {
                "average_improvement": avg_improvement,
                "positive_changes": len([i for i in improvements if i > 0]),
                "negative_changes": len([i for i in improvements if i < 0]),
                "total_evaluated": len(improvements),
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze performance trend: {e}")
            return None

    def export_history(self, format: str = "json") -> str:
        """
        導出策略變更歷史

        Args:
            format: 導出格式 ("json" 或 "csv")

        Returns:
            序列化的歷史數據
        """
        if format == "json":
            return json.dumps(
                [change.to_dict() for change in self._changes],
                indent=2,
                default=str,
                ensure_ascii=False,
            )
        elif format == "csv":
            # 簡化的 CSV 格式
            lines = ["timestamp,type,summary,trigger_reason,effectiveness"]
            for change in self._changes:
                lines.append(
                    f"{change.timestamp.isoformat()},"
                    f"{change.change_type},"
                    f'"{change.change_summary}",'
                    f'"{change.trigger_reason}",'
                    f"{change.effectiveness_score or 'N/A'}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def should_trigger_adjustment(
        self,
        config: AgentConfig,
        performance_data: dict[str, Any],
        market_conditions: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """
        檢查是否應該觸發策略調整

        Args:
            config: Agent 配置
            performance_data: 當前績效數據
            market_conditions: 市場條件數據

        Returns:
            (是否觸發, 觸發原因)
        """
        if not config.auto_adjust.enabled:
            return False, "自動調整已停用"

        # 檢查調整頻率限制
        recent_changes = self.get_strategy_changes(limit=config.auto_adjust.max_adjustments_per_day)
        today_changes = [c for c in recent_changes if c.timestamp.date() == datetime.now().date()]

        if len(today_changes) >= config.auto_adjust.max_adjustments_per_day:
            return False, "已達到每日調整上限"

        # 檢查最近調整時間間隔
        latest_change = self.get_latest_change()
        if latest_change:
            hours_since_last = (datetime.now() - latest_change.timestamp).total_seconds() / 3600
            if hours_since_last < config.auto_adjust.min_hours_between_adjustments:
                return (
                    False,
                    f"距離上次調整未滿 {config.auto_adjust.min_hours_between_adjustments} 小時",
                )

        # 解析觸發條件
        triggers = config.auto_adjust.triggers.split(";")

        for trigger in triggers:
            trigger = trigger.strip()
            if self._evaluate_trigger_condition(trigger, performance_data):
                return True, trigger

        return False, "未滿足任何觸發條件"

    def _evaluate_trigger_condition(
        self,
        condition: str,
        performance_data: dict[str, Any],
    ) -> bool:
        """評估單個觸發條件"""
        try:
            condition.lower()

            # 連續虧損條件
            if "連續" in condition and "虧損" in condition:
                if "三天" in condition and "2%" in condition:
                    # 檢查是否連續三天虧損超過2%
                    daily_returns = performance_data.get("daily_returns", [])
                    if len(daily_returns) >= 3:
                        recent_3_days = daily_returns[-3:]
                        return all(r < -0.02 for r in recent_3_days)

            # 單日跌幅條件
            if "單日" in condition and "跌幅" in condition and "3%" in condition:
                latest_return = performance_data.get("latest_daily_return", 0)
                return latest_return < -0.03

            # 最大回撤條件
            if "回撤" in condition and "10%" in condition:
                max_drawdown = performance_data.get("max_drawdown", 0)
                return max_drawdown > 0.10

            return False

        except Exception as e:
            self.logger.error(f"Failed to evaluate trigger condition '{condition}': {e}")
            return False

    def clear_history(self) -> None:
        """清空策略變更歷史（慎用）"""
        self._changes.clear()
        self.logger.warning("Strategy change history cleared")

    def __len__(self) -> int:
        return len(self._changes)

    def __repr__(self) -> str:
        return f"StrategyTracker(agent_id={self.agent_id}, changes={len(self._changes)})"
