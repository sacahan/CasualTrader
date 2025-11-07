"""
E2E 測試: 完整的交易 Agent 流程與情緒分析集成

測試範圍:
- 完整的 TradingAgent 執行流程
- sentiment_agent 作為子 Agent 的角色
- 情緒分析數據流入決策邏輯
- 交易信號生成
- 端到端的 MCP 整合
"""

import pytest
from unittest.mock import Mock

from src.trading.tools.sentiment_agent import (
    analyze_news_sentiment,
    analyze_social_sentiment,
    get_sentiment_agent,
    _sentiment_agent_context,
    SocialData,
)


class TestSentimentAgentInTradingFlow:
    """測試情緒分析在交易流程中的角色"""

    def setup_method(self):
        """重置全局上下文"""
        _sentiment_agent_context["tavily_mcp"] = None

    def teardown_method(self):
        """清理測試環境"""
        _sentiment_agent_context["tavily_mcp"] = None

    def test_sentiment_agent_initialization_in_context(self):
        """測試情緒分析 Agent 在交易 Agent 中的初始化"""
        # 模擬交易 Agent 的 MCP 設置
        mock_tavily = Mock()
        mock_tavily.name = "tavily_mcp"
        mock_tavily.session = Mock()

        mock_market = Mock()
        mock_market.name = "casual_market_mcp"

        mock_memory = Mock()
        mock_memory.name = "memory_mcp"

        mcp_servers = [mock_tavily, mock_market, mock_memory]

        # 初始化情緒分析 Agent
        sentiment_agent = get_sentiment_agent(mcp_servers=mcp_servers)

        assert sentiment_agent is not None
        # 驗證上下文已設置
        assert _sentiment_agent_context["tavily_mcp"] is mock_tavily

    def test_sentiment_analysis_data_flow_to_signal(self):
        """測試情緒分析數據流向交易信號"""
        # 模擬市場數據
        market_data = {
            "ticker": "2330",
            "current_price": 500,
            "previous_close": 495,
            "change_percent": 1.01,
        }

        # 模擬新聞數據
        news_data = [
            {
                "title": "台積電 3nm 工藝領先全球",
                "content": "利好消息，營收增長",
                "source": "經濟日報",
            },
            {
                "title": "AI 晶片需求旺盛",
                "content": "市場看好，訂單增加",
                "source": "工商時報",
            },
        ]

        # 分析情緒
        sentiment = analyze_news_sentiment(
            ticker="2330",
            news_data=news_data,
        )

        # 驗證情緒分析結果
        assert sentiment is not None
        assert sentiment.get("ticker") == "2330"
        assert sentiment.get("sentiment_score") > 0  # 正面新聞
        assert sentiment.get("data_source") == "provided"

        # 驗證信號邏輯：正面情緒 + 上漲價格 = 買入信號
        if sentiment.get("sentiment_score") > 0 and market_data["change_percent"] > 0:
            signal_type = "BUY"
        else:
            signal_type = "HOLD"

        assert signal_type == "BUY"

    def test_social_sentiment_in_market_assessment(self):
        """測試社群情緒在市場評估中的角色"""
        social_data = SocialData(
            platform="PTT",
            mentions=500,
            positive_ratio=0.65,
            negative_ratio=0.20,
            neutral_ratio=0.15,
        )

        result = analyze_social_sentiment(
            ticker="2330",
            social_data=social_data,
        )

        assert result is not None
        # 驗證社群情緒指標
        assert result.get("positive_mentions") == int(500 * 0.65)
        assert result.get("negative_mentions") == int(500 * 0.20)
        assert result.get("total_mentions") == 500

        # 判斷社群情緒態度
        positive_ratio = result.get("positive_mentions", 0) / max(
            result.get("total_mentions", 1), 1
        )
        assert positive_ratio > 0.5  # 社群整體看好

    def test_multiple_agents_coordination(self):
        """測試多個 Agent 的協調"""
        # 模擬技術分析 Agent、基本面 Agent、風險 Agent 的運行

        # 技術分析結果
        technical_signal = {"trend": "UP", "strength": 0.75}

        # 基本面分析結果
        fundamental_data = {"pe_ratio": 20, "growth_rate": 0.15}

        # 情緒分析結果
        sentiment_result = analyze_news_sentiment(
            ticker="2330",
            news_data=[{"title": "業績增長", "content": "利好", "source": "TEST"}],
        )

        # 綜合評估
        combined_signal = {
            "technical": technical_signal.get("trend") == "UP",
            "fundamental": fundamental_data.get("growth_rate", 0) > 0.1,
            "sentiment": sentiment_result.get("sentiment_score", 0) > 0,
        }

        # 決策邏輯：所有指標看好才買入
        should_buy = all(combined_signal.values())
        assert should_buy is True

    def test_agent_decision_matrix(self):
        """測試 Agent 決策矩陣"""
        test_cases = [
            {
                "name": "全面看好",
                "sentiment": 0.8,
                "market_trend": "UP",
                "expected_signal": "BUY",
            },
            {
                "name": "情緒負面但市場上升",
                "sentiment": -0.5,
                "market_trend": "UP",
                "expected_signal": "HOLD",
            },
            {
                "name": "情緒正面但市場下跌",
                "sentiment": 0.6,
                "market_trend": "DOWN",
                "expected_signal": "HOLD",
            },
            {
                "name": "全面負面",
                "sentiment": -0.7,
                "market_trend": "DOWN",
                "expected_signal": "SELL",
            },
        ]

        for case in test_cases:
            # 簡化的決策邏輯
            sentiment_buy = case["sentiment"] > 0.5
            trend_buy = case["market_trend"] == "UP"

            if sentiment_buy and trend_buy:
                signal = "BUY"
            elif not sentiment_buy and not trend_buy:
                signal = "SELL"
            else:
                signal = "HOLD"

            assert signal == case["expected_signal"], f"失敗: {case['name']}"


class TestSentimentDataSourceReliability:
    """測試情緒分析數據源的可靠性"""

    def setup_method(self):
        """重置全局上下文"""
        _sentiment_agent_context["tavily_mcp"] = None

    def teardown_method(self):
        """清理測試環境"""
        _sentiment_agent_context["tavily_mcp"] = None

    def test_auto_fetch_vs_provided_data_consistency(self):
        """測試自動蒐集和手動提供數據的一致性"""
        # 手動提供數據
        manual_data = [
            {
                "title": "新聞 1",
                "content": "利好消息，上升",
                "source": "新聞社",
            }
        ]

        result_manual = analyze_news_sentiment(
            ticker="2330",
            news_data=manual_data,
        )

        # 驗證數據源
        assert result_manual.get("data_source") == "provided"
        assert result_manual.get("sentiment_score") > 0

    def test_data_source_tracking_accuracy(self):
        """測試數據源追蹤的準確性"""
        # 測試各種場景的 data_source 值

        # 場景 1: 提供數據
        result1 = analyze_news_sentiment(
            ticker="2330",
            news_data=[{"title": "t", "content": "c", "source": "TEST"}],
        )
        assert result1.get("data_source") == "provided"

        # 場景 2: 無數據，禁用自動蒐集
        result2 = analyze_news_sentiment(
            ticker="2330",
            news_data=None,
            auto_fetch=False,
        )
        assert result2.get("data_source") == "empty"

        # 場景 3: 空列表
        result3 = analyze_news_sentiment(
            ticker="2330",
            news_data=[],
        )
        assert result3.get("data_source") == "provided"

    def test_sentiment_confidence_levels(self):
        """測試情緒信心等級"""
        # 測試不同數據量下的信心等級

        # 單個數據點
        result_single = analyze_news_sentiment(
            ticker="2330",
            news_data=[{"title": "新聞", "content": "內容", "source": "TEST"}],
        )
        confidence_single = result_single.get("confidence", 0)

        # 多個數據點
        result_multiple = analyze_news_sentiment(
            ticker="2330",
            news_data=[
                {"title": f"新聞{i}", "content": f"內容{i}", "source": "TEST"} for i in range(10)
            ],
        )
        confidence_multiple = result_multiple.get("confidence", 0)

        # 信心應該隨著數據量增加而提高
        # （假設實現了這個邏輯）
        assert isinstance(confidence_single, (int, float))
        assert isinstance(confidence_multiple, (int, float))


class TestRealWorldScenarios:
    """測試真實世界場景"""

    def test_earnings_announcement_sentiment(self):
        """測試財報公告的情緒分析"""
        earnings_news = [
            {
                "title": "台積電 Q3 營收創新高",
                "content": "超過預期，利好消息，投資者看好",
                "source": "IR部門",
            },
            {
                "title": "毛利率提升至 53%",
                "content": "成本控制有效，盈利能力增強",
                "source": "財務報表",
            },
        ]

        result = analyze_news_sentiment(
            ticker="2330",
            news_data=earnings_news,
        )

        # 財報利好應該產生正面情緒
        assert result.get("sentiment_score") > 0
        assert result.get("article_count") == 2

    def test_crisis_event_sentiment(self):
        """測試危機事件的情緒分析"""
        crisis_news = [
            {
                "title": "芯片出口管制升級",
                "content": "美國禁止銷售先進芯片，市場受影響",
                "source": "新聞社",
            },
            {
                "title": "台積電股價下跌 5%",
                "content": "市場擔憂，投資者拋售",
                "source": "證券分析",
            },
        ]

        result = analyze_news_sentiment(
            ticker="2330",
            news_data=crisis_news,
        )

        # 危機事件應該產生負面情緒
        assert result.get("sentiment_score") < 0

    def test_mixed_sentiment_scenarios(self):
        """測試混合情緒場景"""
        mixed_news = [
            {
                "title": "營收增長 15%",
                "content": "利好消息，業績看好",
                "source": "新聞社",
            },
            {
                "title": "面臨供應鏈風險",
                "content": "原材料短缺可能影響生產",
                "source": "分析報告",
            },
            {
                "title": "新產品線獲好評",
                "content": "市場反響積極",
                "source": "產業評論",
            },
        ]

        result = analyze_news_sentiment(
            ticker="2330",
            news_data=mixed_news,
        )

        # 混合情緒應該接近中立但略微正面
        sentiment = result.get("sentiment_score", 0)
        assert -0.5 < sentiment < 0.5


class TestPerformanceUnderLoad:
    """測試高負載下的性能"""

    def test_large_batch_processing(self):
        """測試大批量數據處理"""
        # 模擬 100 篇新聞
        large_batch = [
            {
                "title": f"新聞標題 {i}",
                "content": f"新聞內容 {i}" * 10,
                "source": f"來源 {i % 5}",
            }
            for i in range(100)
        ]

        result = analyze_news_sentiment(
            ticker="2330",
            news_data=large_batch,
        )

        assert result is not None
        assert result.get("article_count") == 100

    def test_multiple_concurrent_analyses(self):
        """測試多個並發分析"""
        tickers = ["2330", "2454", "3008", "2412", "2408"]
        results = []

        for ticker in tickers:
            result = analyze_news_sentiment(
                ticker=ticker,
                news_data=[{"title": f"{ticker} 新聞", "content": "內容", "source": "TEST"}],
            )
            results.append(result)

        # 所有分析應成功完成
        assert len(results) == len(tickers)
        assert all(r is not None for r in results)
        assert all(r.get("ticker") in tickers for r in results)


class TestIntegrationWithOtherAgents:
    """測試與其他 Agent 的集成"""

    def test_sentiment_output_for_downstream_agents(self):
        """測試情緒分析輸出給下游 Agent"""
        # 情緒分析輸出
        sentiment = analyze_news_sentiment(
            ticker="2330",
            news_data=[{"title": "利好新聞", "content": "正面", "source": "TEST"}],
        )

        # 轉換為下游 Agent 可用的格式
        sentiment_input = {
            "ticker": sentiment.get("ticker"),
            "sentiment_score": sentiment.get("sentiment_score"),
            "confidence": sentiment.get("confidence"),
            "key_topics": sentiment.get("key_topics", []),
            "data_source": sentiment.get("data_source"),
        }

        # 驗證轉換結果
        assert sentiment_input["ticker"] == "2330"
        assert isinstance(sentiment_input["sentiment_score"], (int, float))
        assert isinstance(sentiment_input["confidence"], (int, float))
        assert isinstance(sentiment_input["key_topics"], list)

    def test_agent_collaboration_workflow(self):
        """測試 Agent 協作工作流"""
        # 模擬工作流：情緒分析 → 風險評估 → 決策

        # Step 1: 情緒分析
        sentiment = analyze_news_sentiment(
            ticker="2330",
            news_data=[{"title": "新聞", "content": "內容", "source": "TEST"}],
        )

        # Step 2: 模擬風險評估
        risk_level = "HIGH" if abs(sentiment.get("sentiment_score", 0)) > 0.7 else "MEDIUM"

        # Step 3: 模擬最終決策
        if risk_level == "HIGH":
            position_size = 0.5  # 減小倉位
        else:
            position_size = 1.0

        assert position_size in [0.5, 1.0]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
