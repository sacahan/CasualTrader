"""
策略變更記錄機制
提供統一的策略變更記錄和管理功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from ..core.instruction_generator import InstructionGenerator
from ..core.strategy_tracker import ChangeType, StrategyTracker


class StrategyChangeRequest(BaseModel):
    """策略變更請求"""

    agent_id: str
    trigger_reason: str
    new_strategy_addition: str
    change_summary: str
    agent_explanation: str
    change_type: ChangeType = ChangeType.AUTO
    auto_apply: bool = True
    performance_snapshot: dict[str, Any] | None = None


class StrategyChangeResult(BaseModel):
    """策略變更結果"""

    success: bool
    change_id: str | None = None
    updated_instructions: str | None = None
    error_message: str | None = None
    warnings: list[str] = []
    recommendations: list[str] = []
    timestamp: datetime


class StrategyChangeRecorder:
    """
    策略變更記錄器 - 統一管理策略變更的記錄和應用
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("strategy_change_recorder")
        self.instruction_generator = InstructionGenerator()
        self._trackers: dict[str, StrategyTracker] = {}

    def _get_tracker(self, agent_id: str) -> StrategyTracker:
        """獲取或創建指定 Agent 的策略追蹤器"""
        if agent_id not in self._trackers:
            self._trackers[agent_id] = StrategyTracker(agent_id)
        return self._trackers[agent_id]

    async def record_strategy_change(
        self,
        request: StrategyChangeRequest,
        current_instructions: str | None = None,
    ) -> StrategyChangeResult:
        """
        記錄策略變更

        Args:
            request: 策略變更請求
            current_instructions: 當前指令（如果需要更新）

        Returns:
            策略變更結果
        """
        try:
            tracker = self._get_tracker(request.agent_id)
            warnings = []
            recommendations = []

            # 驗證變更請求
            validation_result = self._validate_change_request(request)
            if not validation_result["is_valid"]:
                return StrategyChangeResult(
                    success=False,
                    error_message=validation_result["error"],
                    warnings=validation_result["warnings"],
                    timestamp=datetime.now(),
                )

            warnings.extend(validation_result["warnings"])

            # 檢查變更頻率
            frequency_check = self._check_change_frequency(tracker, request)
            if not frequency_check["allowed"]:
                return StrategyChangeResult(
                    success=False,
                    error_message=frequency_check["reason"],
                    warnings=warnings,
                    timestamp=datetime.now(),
                )

            warnings.extend(frequency_check["warnings"])

            # 記錄策略變更
            change_record = tracker.record_strategy_change(
                trigger_reason=request.trigger_reason,
                new_strategy_addition=request.new_strategy_addition,
                change_summary=request.change_summary,
                agent_explanation=request.agent_explanation,
                change_type=request.change_type,
                performance_snapshot=request.performance_snapshot,
                auto_applied=request.auto_apply,
            )

            # 更新指令（如果提供了當前指令）
            updated_instructions = None
            if current_instructions:
                updated_instructions = (
                    self.instruction_generator.update_instructions_with_strategy_change(
                        current_instructions, request.new_strategy_addition
                    )
                )

            # 生成建議
            recommendations.extend(
                self._generate_post_change_recommendations(request, change_record)
            )

            self.logger.info(
                f"Strategy change recorded for agent {request.agent_id}: {change_record.id}"
            )

            return StrategyChangeResult(
                success=True,
                change_id=change_record.id,
                updated_instructions=updated_instructions,
                warnings=warnings,
                recommendations=recommendations,
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Failed to record strategy change: {e}")
            return StrategyChangeResult(
                success=False,
                error_message=f"策略變更記錄失敗: {e}",
                timestamp=datetime.now(),
            )

    def _validate_change_request(
        self, request: StrategyChangeRequest
    ) -> dict[str, Any]:
        """驗證策略變更請求"""
        warnings = []

        # 檢查必要欄位
        if not request.trigger_reason.strip():
            return {
                "is_valid": False,
                "error": "觸發原因不能為空",
                "warnings": warnings,
            }

        if not request.new_strategy_addition.strip():
            return {
                "is_valid": False,
                "error": "新策略內容不能為空",
                "warnings": warnings,
            }

        if not request.change_summary.strip():
            return {
                "is_valid": False,
                "error": "變更摘要不能為空",
                "warnings": warnings,
            }

        if not request.agent_explanation.strip():
            return {
                "is_valid": False,
                "error": "Agent 解釋不能為空",
                "warnings": warnings,
            }

        # 檢查內容合理性
        if len(request.new_strategy_addition) < 50:
            warnings.append("新策略內容較短，請確認是否完整")

        if len(request.change_summary) < 20:
            warnings.append("變更摘要較簡短，建議提供更詳細的說明")

        # 檢查敏感內容
        sensitive_keywords = ["清倉", "全部賣出", "停止交易", "暫停", "緊急"]
        if any(
            keyword in request.new_strategy_addition for keyword in sensitive_keywords
        ):
            warnings.append("策略變更包含敏感操作，請謹慎確認")

        return {"is_valid": True, "error": None, "warnings": warnings}

    def _check_change_frequency(
        self, tracker: StrategyTracker, request: StrategyChangeRequest
    ) -> dict[str, Any]:
        """檢查變更頻率限制"""
        warnings = []

        # 檢查當日變更次數
        recent_changes = tracker.get_strategy_changes(limit=10)
        today_changes = [
            change
            for change in recent_changes
            if change.timestamp.date() == datetime.now().date()
        ]

        max_daily_changes = 5  # 每日最大變更次數
        if len(today_changes) >= max_daily_changes:
            return {
                "allowed": False,
                "reason": f"已達到每日最大策略變更次數 ({max_daily_changes})",
                "warnings": warnings,
            }

        # 檢查變更間隔
        if recent_changes:
            latest_change = recent_changes[0]
            time_since_last = (
                datetime.now() - latest_change.timestamp
            ).total_seconds() / 3600

            min_interval_hours = 2  # 最小間隔 2 小時
            if time_since_last < min_interval_hours:
                return {
                    "allowed": False,
                    "reason": f"距離上次策略變更未滿 {min_interval_hours} 小時",
                    "warnings": warnings,
                }

            if time_since_last < 4:  # 4 小時內的變更給予警告
                warnings.append("策略變更頻率較高，請確認必要性")

        return {"allowed": True, "reason": None, "warnings": warnings}

    def _generate_post_change_recommendations(
        self, request: StrategyChangeRequest, change_record: Any
    ) -> list[str]:
        """生成策略變更後的建議"""
        recommendations = []

        # 基於變更類型的建議
        if request.change_type == ChangeType.PERFORMANCE_DRIVEN:
            recommendations.append("建議密切監控變更後的績效表現")
            recommendations.append("設定績效檢查點以評估策略效果")

        elif request.change_type == ChangeType.AUTO:
            recommendations.append("自動策略調整已生效，建議定期檢視")
            recommendations.append("如有疑慮可手動介入調整")

        # 基於觸發原因的建議
        if "虧損" in request.trigger_reason or "回撤" in request.trigger_reason:
            recommendations.append("風險控制策略已調整，建議降低部位大小")
            recommendations.append("考慮設定更嚴格的停損條件")

        if "市場" in request.trigger_reason and "波動" in request.trigger_reason:
            recommendations.append("市場波動策略調整，建議增加現金部位")
            recommendations.append("密切關注市場情緒變化")

        # 通用建議
        recommendations.append("記錄策略變更的實際效果以供後續參考")
        recommendations.append("如策略效果不佳，可考慮回滾到先前版本")

        return recommendations

    async def get_strategy_change_history(
        self,
        agent_id: str,
        limit: int | None = None,
        change_type: ChangeType | None = None,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        獲取策略變更歷史

        Args:
            agent_id: Agent ID
            limit: 返回記錄數量限制
            change_type: 篩選變更類型
            since: 時間起點

        Returns:
            策略變更歷史
        """
        try:
            tracker = self._get_tracker(agent_id)
            changes = tracker.get_strategy_changes(
                limit=limit, change_type=change_type, since=since
            )

            return [change.to_dict() for change in changes]

        except Exception as e:
            self.logger.error(f"Failed to get strategy change history: {e}")
            return []

    async def get_strategy_evolution_summary(self, agent_id: str) -> dict[str, Any]:
        """
        獲取策略演化摘要

        Args:
            agent_id: Agent ID

        Returns:
            策略演化摘要
        """
        try:
            tracker = self._get_tracker(agent_id)
            return tracker.get_strategy_evolution_summary()

        except Exception as e:
            self.logger.error(f"Failed to get strategy evolution summary: {e}")
            return {
                "total_changes": 0,
                "evolution_timeline": [],
                "performance_trend": None,
                "most_effective_changes": [],
            }

    async def evaluate_change_effectiveness(
        self,
        agent_id: str,
        change_id: str,
        effectiveness_score: float,
        performance_after: dict[str, Any] | None = None,
        user_feedback: str | None = None,
    ) -> bool:
        """
        評估策略變更效果

        Args:
            agent_id: Agent ID
            change_id: 變更記錄 ID
            effectiveness_score: 效果評分 (0-10)
            performance_after: 變更後績效數據
            user_feedback: 用戶反饋

        Returns:
            是否更新成功
        """
        try:
            tracker = self._get_tracker(agent_id)
            success = tracker.update_change_effectiveness(
                change_id=change_id,
                effectiveness_score=effectiveness_score,
                performance_after=performance_after,
                user_feedback=user_feedback,
            )

            if success:
                self.logger.info(
                    f"Updated effectiveness for change {change_id}: {effectiveness_score}"
                )
            else:
                self.logger.warning(
                    f"Failed to update effectiveness for change {change_id}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to evaluate change effectiveness: {e}")
            return False

    async def rollback_strategy_change(
        self, agent_id: str, change_id: str, rollback_reason: str
    ) -> StrategyChangeResult:
        """
        回滾策略變更

        Args:
            agent_id: Agent ID
            change_id: 要回滾的變更 ID
            rollback_reason: 回滾原因

        Returns:
            回滾結果
        """
        try:
            tracker = self._get_tracker(agent_id)

            # 查找要回滾的變更
            changes = tracker.get_strategy_changes()
            target_change = next((c for c in changes if c.id == change_id), None)

            if not target_change:
                return StrategyChangeResult(
                    success=False,
                    error_message=f"找不到變更記錄: {change_id}",
                    timestamp=datetime.now(),
                )

            # 記錄回滾操作
            rollback_request = StrategyChangeRequest(
                agent_id=agent_id,
                trigger_reason=f"回滾策略變更: {rollback_reason}",
                new_strategy_addition=f"撤銷先前變更: {target_change.change_summary}",
                change_summary=f"回滾變更 {change_id[:8]}",
                agent_explanation=f"基於以下原因回滾策略: {rollback_reason}",
                change_type=ChangeType.MANUAL,
                auto_apply=True,
            )

            # 執行回滾記錄
            result = await self.record_strategy_change(rollback_request)

            if result.success:
                self.logger.info(
                    f"Strategy change {change_id} rolled back successfully"
                )
                result.recommendations.append("策略已回滾，建議監控後續表現")
                result.recommendations.append("分析回滾原因以避免類似問題")

            return result

        except Exception as e:
            self.logger.error(f"Failed to rollback strategy change: {e}")
            return StrategyChangeResult(
                success=False,
                error_message=f"回滾操作失敗: {e}",
                timestamp=datetime.now(),
            )

    async def suggest_strategy_improvement(
        self, agent_id: str, performance_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        基於績效數據建議策略改進

        Args:
            agent_id: Agent ID
            performance_data: 績效數據

        Returns:
            改進建議
        """
        try:
            tracker = self._get_tracker(agent_id)
            evolution_summary = tracker.get_strategy_evolution_summary()

            suggestions = []
            priority = "medium"

            # 分析績效趨勢
            total_return = performance_data.get("total_return", 0)
            max_drawdown = performance_data.get("max_drawdown", 0)
            win_rate = performance_data.get("win_rate", 0.5)

            # 基於績效生成建議
            if total_return < -0.1:  # 虧損超過 10%
                suggestions.append(
                    {
                        "type": "risk_control",
                        "description": "當前績效不佳，建議加強風險控制",
                        "action": "降低部位大小，增加現金比例",
                        "priority": "high",
                    }
                )
                priority = "high"

            if max_drawdown > 0.15:  # 最大回撤超過 15%
                suggestions.append(
                    {
                        "type": "drawdown_control",
                        "description": "最大回撤偏高，需要改善風險管理",
                        "action": "設定更嚴格的停損條件",
                        "priority": "high",
                    }
                )

            if win_rate < 0.4:  # 勝率低於 40%
                suggestions.append(
                    {
                        "type": "selection_improvement",
                        "description": "勝率偏低，建議改善選股策略",
                        "action": "加強基本面分析，提高選股品質",
                        "priority": "medium",
                    }
                )

            # 基於歷史變更效果生成建議
            effective_changes = [
                c
                for c in evolution_summary.get("most_effective_changes", [])
                if c.get("effectiveness", 0) >= 7
            ]

            if effective_changes:
                suggestions.append(
                    {
                        "type": "repeat_success",
                        "description": "參考過往成功的策略調整",
                        "action": f"考慮重複應用效果良好的策略: {effective_changes[0].get('summary', '')}",
                        "priority": "low",
                    }
                )

            return {
                "agent_id": agent_id,
                "suggestions": suggestions,
                "overall_priority": priority,
                "performance_context": {
                    "total_return": total_return,
                    "max_drawdown": max_drawdown,
                    "win_rate": win_rate,
                },
                "strategy_history_context": {
                    "total_changes": evolution_summary.get("total_changes", 0),
                    "effective_changes_count": len(effective_changes),
                },
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Failed to suggest strategy improvement: {e}")
            return {
                "agent_id": agent_id,
                "suggestions": [],
                "overall_priority": "low",
                "error": str(e),
                "timestamp": datetime.now(),
            }

    def get_recorder_status(self) -> dict[str, Any]:
        """獲取記錄器狀態"""
        return {
            "active_trackers": len(self._trackers),
            "tracked_agents": list(self._trackers.keys()),
            "total_changes": sum(len(tracker) for tracker in self._trackers.values()),
            "status": "operational",
        }

    def as_tool(self) -> dict[str, Any]:
        """
        將 StrategyChangeRecorder 轉換為可供 OpenAI Agent 使用的工具

        Returns:
            工具配置字典
        """
        return {
            "type": "function",
            "function": {
                "name": "record_strategy_change",
                "description": "記錄和應用策略變更",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trigger_reason": {
                            "type": "string",
                            "description": "策略變更的觸發原因",
                        },
                        "new_strategy_addition": {
                            "type": "string",
                            "description": "新增的策略內容",
                        },
                        "change_summary": {
                            "type": "string",
                            "description": "變更摘要說明",
                        },
                        "agent_explanation": {
                            "type": "string",
                            "description": "Agent 對此變更的說明",
                        },
                        "auto_apply": {
                            "type": "boolean",
                            "description": "是否自動應用變更",
                            "default": True,
                        },
                        "performance_snapshot": {
                            "type": "object",
                            "description": "當前績效快照 (可選)",
                        },
                    },
                    "required": [
                        "trigger_reason",
                        "new_strategy_addition",
                        "change_summary",
                        "agent_explanation",
                    ],
                },
            },
            "implementation": self.record_change,
        }
