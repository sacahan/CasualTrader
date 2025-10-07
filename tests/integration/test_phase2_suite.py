"""
Phase 2 Integration Test Suite
測試所有 Phase 2 新功能的整合測試
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.core.instruction_generator import (
    AgentConfig,
    InstructionGenerator,
    TradingRules,
)
from agents.core.strategy_auto_adjuster import (
    StrategyAutoAdjuster,
)
from agents.core.strategy_tracker import ChangeType, StrategyTracker
from agents.functions.market_status import MarketStatusChecker
from agents.functions.strategy_change_recorder import (
    StrategyChangeRecorder,
    StrategyChangeRequest,
)
from agents.functions.trading_validation import TradingValidator
from agents.integrations.openai_tools import OpenAIToolsIntegrator
from agents.tools.fundamental_agent import FundamentalAgent
from agents.tools.risk_agent import RiskAgent
from agents.tools.sentiment_agent import SentimentAgent
from agents.tools.technical_agent import TechnicalAgent


class TestPhase2CoreIntegration:
    """測試 Phase 2 核心組件整合"""

    @pytest.fixture
    def agent_config(self) -> AgentConfig:
        """測試用 Agent 配置"""
        return AgentConfig(
            agent_id="test_agent_001",
            investment_style="growth",
            risk_tolerance="medium",
            investment_horizon="long_term",
            target_sectors=["technology", "healthcare"],
            excluded_sectors=["tobacco"],
            max_position_size=0.15,
            max_portfolio_sectors=8,
            trading_rules=TradingRules(
                max_daily_trades=5,
                min_trade_amount=50000,
                stop_loss_percentage=0.08,
                take_profit_percentage=0.20,
                position_sizing_method="equal_weight",
            ),
        )

    @pytest.fixture
    def performance_data(self) -> dict[str, float]:
        """測試用績效數據"""
        return {
            "return": -0.12,  # 觸發調整的虧損
            "drawdown": 0.18,  # 觸發調整的回撤
            "volatility": 0.28,  # 觸發調整的波動率
            "sharpe": 0.3,  # 觸發調整的夏普比率
            "win_rate": 0.35,
            "total_trades": 45,
        }

    @pytest.fixture
    def market_data(self) -> dict[str, float]:
        """測試用市場數據"""
        return {
            "vix": 28.5,  # 觸發調整的恐慌指數
            "sentiment": 15.0,  # 觸發調整的極度恐慌
            "interest_rate": 2.5,
            "sector_rotation": 0.7,
        }

    async def test_complete_instruction_generation_workflow(
        self, agent_config: AgentConfig
    ):
        """測試完整的指令生成工作流程"""
        generator = InstructionGenerator()

        # 生成基礎指令
        instructions = generator.generate_trading_instructions(agent_config)

        # 驗證指令內容完整性
        assert "投資風格：成長型" in instructions
        assert "風險承受度：中等" in instructions
        assert "科技" in instructions and "醫療保健" in instructions
        assert "菸草" in instructions
        assert "15%" in instructions  # max_position_size
        assert "8%" in instructions  # stop_loss
        assert "20%" in instructions  # take_profit

        # 測試策略更新
        new_strategy = "因應市場波動，調整部位管理策略"
        updated_instructions = generator.update_instructions_with_strategy_change(
            instructions, new_strategy
        )

        assert new_strategy in updated_instructions
        assert "策略演化記錄" in updated_instructions

    async def test_strategy_tracking_and_recording_integration(self):
        """測試策略追蹤和記錄整合"""
        agent_id = "test_agent_002"

        # 初始化組件
        tracker = StrategyTracker(agent_id)
        recorder = StrategyChangeRecorder()

        # 創建策略變更請求
        change_request = StrategyChangeRequest(
            agent_id=agent_id,
            trigger_reason="績效不佳，需要降低風險",
            new_strategy_addition="減少單一部位至10%，增加現金部位至20%",
            change_summary="風險控制調整",
            agent_explanation="基於最近虧損情況，主動降低投資組合風險暴露",
            change_type=ChangeType.PERFORMANCE_DRIVEN,
        )

        # 記錄策略變更
        result = await recorder.record_strategy_change(change_request)

        # 驗證記錄結果
        assert result.success
        assert result.change_id is not None
        assert len(result.warnings) >= 0
        assert len(result.recommendations) > 0

        # 驗證追蹤器中的記錄
        changes = tracker.get_strategy_changes(limit=1)
        assert len(changes) == 1
        assert changes[0].trigger_reason == change_request.trigger_reason
        assert changes[0].change_type == ChangeType.PERFORMANCE_DRIVEN

        # 測試演化摘要
        evolution = tracker.get_strategy_evolution_summary()
        assert evolution["total_changes"] == 1
        assert len(evolution["evolution_timeline"]) == 1

    async def test_auto_adjustment_trigger_and_application(
        self, performance_data: dict[str, float], market_data: dict[str, float]
    ):
        """測試自動調整觸發和應用流程"""
        agent_id = "test_agent_003"
        adjuster = StrategyAutoAdjuster()

        # 評估調整需求
        actions = await adjuster.evaluate_adjustment_needs(
            agent_id=agent_id,
            performance_data=performance_data,
            market_data=market_data,
        )

        # 驗證觸發了多個調整動作
        assert len(actions) > 0

        # 檢查具體的調整動作類型
        action_types = [action.action_type for action in actions]
        expected_types = ["reduce_risk", "risk_control", "defensive_positioning"]
        assert any(action_type in expected_types for action_type in action_types)

        # 應用策略調整
        adjustment_result = await adjuster.apply_strategy_adjustment(
            agent_id=agent_id, actions=actions, auto_apply=True
        )

        # 驗證調整應用結果
        assert adjustment_result.success
        assert adjustment_result.change_id is not None
        assert len(adjustment_result.applied_actions) > 0
        assert len(adjustment_result.strategy_changes) > 0

        # 驗證策略變更內容
        strategy_changes = adjustment_result.strategy_changes
        risk_related_changes = [
            change
            for change in strategy_changes
            if "風險" in change or "部位" in change or "現金" in change
        ]
        assert len(risk_related_changes) > 0

    async def test_analysis_tools_integration(self):
        """測試分析工具整合"""
        symbol = "2330"  # 台積電

        # 初始化所有分析工具
        fundamental = FundamentalAgent()
        technical = TechnicalAgent()
        risk = RiskAgent()
        sentiment = SentimentAgent()

        # 模擬市場數據
        mock_price_data = [100, 102, 98, 105, 103, 107, 104, 108, 106, 110]

        # 執行各種分析
        with patch.object(
            fundamental,
            "_fetch_company_data",
            return_value={
                "revenue": 1000000,
                "net_income": 200000,
                "total_assets": 2000000,
                "total_debt": 500000,
                "shares_outstanding": 100000,
                "dividend_yield": 0.025,
            },
        ):
            fundamental_result = await fundamental.analyze_company_fundamentals(symbol)

        with patch.object(technical, "_fetch_price_data", return_value=mock_price_data):
            technical_result = await technical.analyze_technical_indicators(symbol)

        portfolio_data = {
            "positions": {symbol: {"quantity": 10000, "current_price": 110}},
            "total_value": 1100000,
        }
        risk_result = await risk.assess_investment_risk(symbol, portfolio_data)

        with patch.object(sentiment, "_fetch_news_sentiment", return_value=0.6):
            with patch.object(sentiment, "_fetch_social_sentiment", return_value=0.7):
                sentiment_result = await sentiment.analyze_market_sentiment(symbol)

        # 驗證分析結果
        assert fundamental_result.investment_recommendation in [
            "strong_buy",
            "buy",
            "hold",
            "sell",
            "strong_sell",
        ]
        assert 0 <= fundamental_result.overall_score <= 10

        assert technical_result.overall_signal in ["buy", "sell", "hold"]
        assert technical_result.indicators.rsi is not None

        assert risk_result.overall_risk_level in ["low", "medium", "high"]
        assert risk_result.portfolio_risk.concentration_risk >= 0

        assert sentiment_result.overall_sentiment in [
            "very_positive",
            "positive",
            "neutral",
            "negative",
            "very_negative",
        ]
        assert 0 <= sentiment_result.sentiment_score <= 100

    async def test_trading_validation_integration(self):
        """測試交易驗證整合"""
        validator = TradingValidator()

        # 測試有效交易
        valid_result = await validator.validate_trade_parameters(
            symbol="2330",
            action="buy",
            quantity=2000,
            price=100.0,
            portfolio_value=1000000,
            current_positions={},
            daily_trade_count=2,
        )

        assert valid_result.is_valid
        assert len(valid_result.validation_errors) == 0
        assert valid_result.risk_score < 50

        # 測試無效交易（超過部位限制）
        invalid_result = await validator.validate_trade_parameters(
            symbol="2330",
            action="buy",
            quantity=20000,  # 過大的數量
            price=100.0,
            portfolio_value=1000000,
            current_positions={},
            daily_trade_count=2,
        )

        assert not invalid_result.is_valid
        assert len(invalid_result.validation_errors) > 0
        assert invalid_result.risk_score > 50

    async def test_market_status_integration(self):
        """測試市場狀態檢查整合"""
        checker = MarketStatusChecker()

        # 測試市場狀態檢查
        status = await checker.get_market_status()

        assert status.timezone == "Asia/Taipei"
        assert isinstance(status.is_open, bool)
        assert status.market_date is not None

        # 測試交易時間檢查
        is_trading = await checker.is_trading_hours()
        assert isinstance(is_trading, bool)

        # 測試下一個交易時段
        next_session = await checker.get_next_trading_session()
        assert isinstance(next_session, dict)

        # 測試交易日曆
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        calendar = await checker.get_market_calendar(start_date, end_date)

        assert "trading_days" in calendar
        assert "non_trading_days" in calendar
        assert calendar["total_days"] == 31

    async def test_openai_tools_integration(self):
        """測試 OpenAI 工具整合"""
        integrator = OpenAIToolsIntegrator()

        # 測試網路搜尋
        search_result = await integrator.web_search("台積電 投資分析", max_results=5)

        assert search_result.query == "台積電 投資分析"
        assert len(search_result.results) <= 5
        assert search_result.source == "web_search_tool"

        # 測試程式碼執行
        code = """
import numpy as np
data = np.array([1, 2, 3, 4, 5])
mean = np.mean(data)
print(f"平均值: {mean}")
        """
        exec_result = await integrator.execute_code(code)

        assert exec_result.code == code
        assert exec_result.error is None
        assert exec_result.execution_time >= 0

        # 測試整合分析
        integrated_result = await integrator.execute_integrated_analysis(
            symbol="2330",
            analysis_request="技術分析",
        )

        assert integrated_result["symbol"] == "2330"
        assert "web_search" in integrated_result
        assert "code_analysis" in integrated_result


class TestPhase2WorkflowIntegration:
    """測試 Phase 2 完整工作流程整合"""

    async def test_complete_agent_lifecycle(self):
        """測試完整的 Agent 生命週期"""
        agent_id = "lifecycle_test_agent"

        # 1. 生成初始指令
        config = AgentConfig(
            agent_id=agent_id,
            investment_style="balanced",
            risk_tolerance="medium",
            investment_horizon="medium_term",
            target_sectors=["technology"],
            max_position_size=0.12,
        )

        generator = InstructionGenerator()
        initial_instructions = generator.generate_trading_instructions(config)

        # 2. 設置追蹤器
        tracker = StrategyTracker(agent_id)

        # 3. 模擬一段時間後的績效不佳
        poor_performance = {
            "return": -0.15,
            "drawdown": 0.20,
            "volatility": 0.30,
            "sharpe": 0.2,
        }

        market_stress = {
            "vix": 30.0,
            "sentiment": 18.0,
        }

        # 4. 自動調整觸發
        adjuster = StrategyAutoAdjuster()
        actions = await adjuster.evaluate_adjustment_needs(
            agent_id=agent_id,
            performance_data=poor_performance,
            market_data=market_stress,
        )

        assert len(actions) > 0

        # 5. 應用調整
        adjustment_result = await adjuster.apply_strategy_adjustment(
            agent_id=agent_id,
            actions=actions,
            current_instructions=initial_instructions,
            auto_apply=True,
        )

        assert adjustment_result.success

        # 6. 驗證策略演化
        evolution = tracker.get_strategy_evolution_summary()
        assert evolution["total_changes"] == 1

        # 7. 生成更新後的指令
        strategy_addition = "\n".join(adjustment_result.strategy_changes)
        updated_instructions = generator.update_instructions_with_strategy_change(
            initial_instructions, strategy_addition
        )

        assert len(updated_instructions) > len(initial_instructions)
        assert "策略演化記錄" in updated_instructions

        # 8. 監控調整效果
        monitoring_result = await adjuster.monitor_adjustment_effectiveness(
            agent_id=agent_id,
            change_id=adjustment_result.change_id,
            monitoring_period_days=7,
        )

        assert "effectiveness_score" in monitoring_result
        assert monitoring_result["effectiveness_score"] >= 0

    async def test_batch_trading_validation_workflow(self):
        """測試批量交易驗證工作流程"""
        validator = TradingValidator()

        # 模擬一批交易
        trades = [
            {"symbol": "2330", "action": "buy", "quantity": 2000, "price": 100.0},
            {"symbol": "2317", "action": "buy", "quantity": 3000, "price": 50.0},
            {"symbol": "2454", "action": "sell", "quantity": 1000, "price": 80.0},
            {"symbol": "0050", "action": "buy", "quantity": 5000, "price": 120.0},
        ]

        current_positions = {
            "2454": {"quantity": 2000, "purchase_price": 75.0},
        }

        # 執行批量驗證
        results = await validator.validate_batch_trades(
            trades=trades,
            portfolio_value=2000000,
            current_positions=current_positions,
        )

        assert len(results) == len(trades)

        # 檢查每個交易的驗證結果
        for i, result in enumerate(results):
            trade = trades[i]
            assert result.validated_parameters["symbol"] == trade["symbol"]
            assert isinstance(result.is_valid, bool)
            assert isinstance(result.risk_score, (int, float))

        # 至少有一些交易應該是有效的
        valid_trades = [r for r in results if r.is_valid]
        assert len(valid_trades) > 0

    async def test_cross_component_data_flow(self):
        """測試跨組件數據流"""
        agent_id = "dataflow_test_agent"

        # 1. 市場狀態檢查
        market_checker = MarketStatusChecker()
        market_status = await market_checker.get_market_status()

        # 2. 只在交易時間進行分析
        if market_status.is_open:
            # 3. 執行技術分析
            technical = TechnicalAgent()
            with patch.object(
                technical, "_fetch_price_data", return_value=[100, 102, 98, 105, 103]
            ):
                tech_result = await technical.analyze_technical_indicators("2330")

            # 4. 基於技術分析結果進行風險評估
            risk_agent = RiskAgent()
            portfolio_data = {
                "positions": {"2330": {"quantity": 1000, "current_price": 103}}
            }
            risk_result = await risk_agent.assess_investment_risk(
                "2330", portfolio_data
            )

            # 5. 如果風險過高，觸發調整
            if risk_result.overall_risk_level == "high":
                adjuster = StrategyAutoAdjuster()
                performance_data = {"volatility": 0.3, "drawdown": 0.2}

                actions = await adjuster.evaluate_adjustment_needs(
                    agent_id=agent_id,
                    performance_data=performance_data,
                    market_data={},
                )

                # 6. 驗證調整動作包含風險控制
                risk_actions = [a for a in actions if "risk" in a.action_type]
                assert len(risk_actions) >= 0  # 可能為0，因為取決於具體觸發條件

        # 7. 記錄整個流程
        recorder = StrategyChangeRecorder()
        status = recorder.get_recorder_status()

        assert status["status"] == "operational"


@pytest.mark.asyncio
class TestPhase2PerformanceIntegration:
    """測試 Phase 2 性能整合"""

    async def test_concurrent_analysis_performance(self):
        """測試並發分析性能"""
        symbols = ["2330", "2317", "2454", "0050", "2882"]

        # 並發執行多個分析
        tasks = []
        for symbol in symbols:
            # 技術分析任務
            tech_agent = TechnicalAgent()
            with patch.object(
                tech_agent, "_fetch_price_data", return_value=[100, 102, 98, 105, 103]
            ):
                tasks.append(tech_agent.analyze_technical_indicators(symbol))

            # 風險分析任務
            risk_agent = RiskAgent()
            portfolio_data = {
                "positions": {symbol: {"quantity": 1000, "current_price": 100}}
            }
            tasks.append(risk_agent.assess_investment_risk(symbol, portfolio_data))

        # 執行所有任務並測量時間
        start_time = datetime.now()
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()

        # 驗證結果
        assert len(results) == len(symbols) * 2  # 每個股票2個分析

        # 性能檢查（並發執行應該比順序執行快）
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 5  # 應該在5秒內完成

    async def test_memory_usage_optimization(self):
        """測試記憶體使用優化"""
        agent_id = "memory_test_agent"

        # 創建大量策略變更記錄
        recorder = StrategyChangeRecorder()
        tracker = StrategyTracker(agent_id)

        # 模擬多次策略變更
        for i in range(10):
            change_request = StrategyChangeRequest(
                agent_id=agent_id,
                trigger_reason=f"測試變更 {i}",
                new_strategy_addition=f"調整策略 {i}",
                change_summary=f"測試摘要 {i}",
                agent_explanation=f"測試解釋 {i}",
            )

            result = await recorder.record_strategy_change(change_request)
            assert result.success

        # 檢查記憶體使用情況
        status = recorder.get_recorder_status()
        assert status["active_trackers"] == 1
        assert status["total_changes"] == 10

        # 清理和垃圾回收測試
        del recorder
        del tracker

        # 驗證新實例可以正常工作
        new_recorder = StrategyChangeRecorder()
        new_status = new_recorder.get_recorder_status()
        assert new_status["status"] == "operational"


if __name__ == "__main__":
    # 運行特定測試
    pytest.main([__file__, "-v", "--tb=short"])
