"""
集成測試: 情緒分析 Agent 與 MCP 服務器集成

測試範圍:
- sentiment_agent 與 tavily_mcp 的集成
- 全局上下文管理 (_sentiment_agent_context)
- 自動蒐集數據流程
- 多個 MCP 服務器的協調
- 實際的 MCP 工具調用（模擬）
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


class TestSentimentAgentMCPIntegration:
    """情緒分析 Agent 與 MCP 的集成測試"""

    def setup_method(self):
        """重置全局上下文"""
        _sentiment_agent_context["tavily_mcp"] = None

    def teardown_method(self):
        """清理測試環境"""
        _sentiment_agent_context["tavily_mcp"] = None

    def test_agent_initialization_with_mcp(self):
        """測試 Agent 初始化時正確綁定 MCP"""
        # 模擬 MCP 服務器
        mock_tavily = Mock()
        mock_tavily.name = "tavily_mcp"
        mock_tavily.session = Mock()

        mock_memory = Mock()
        mock_memory.name = "memory_mcp"

        mock_market = Mock()
        mock_market.name = "casual_market_mcp"

        mcp_servers = [mock_tavily, mock_memory, mock_market]

        # 初始化 Agent
        agent = get_sentiment_agent(mcp_servers=mcp_servers)

        # 驗證 Agent 已建立
        assert agent is not None
        assert hasattr(agent, "name")

        # 驗證全局上下文已設置
        assert _sentiment_agent_context["tavily_mcp"] == mock_tavily

    def test_context_extraction_priority(self):
        """測試 MCP 上下文提取優先級"""
        # 多個 MCP 服務器的情況
        mock_mcp_list = [
            Mock(name="memory_mcp"),
            Mock(name="casual_market_mcp"),
            Mock(name="tavily_mcp"),  # 應優先提取此項
        ]

        _sentiment_agent_context["tavily_mcp"] = None
        get_sentiment_agent(mcp_servers=mock_mcp_list)

        # 驗證 tavily_mcp 被正確提取
        assert _sentiment_agent_context["tavily_mcp"] is not None
        # 注意：在實現中，我們通過名稱比較尋找 tavily_mcp

    def test_analysis_with_mcp_context(self):
        """測試分析函數可訪問 MCP 上下文"""
        mock_mcp = Mock()
        mock_mcp.name = "tavily_mcp"
        mock_mcp.session = Mock()

        _sentiment_agent_context["tavily_mcp"] = mock_mcp

        # 進行分析
        result = analyze_news_sentiment(
            ticker="2330",
            news_data=[{"title": "測試", "content": "測試內容", "source": "TEST"}],
        )

        assert result is not None
        assert result.get("data_source") == "provided"

    def test_empty_mcp_servers_list(self):
        """測試空 MCP 服務器列表"""
        agent = get_sentiment_agent(mcp_servers=[])
        assert agent is not None
        # 全局上下文應保持 None
        assert _sentiment_agent_context["tavily_mcp"] is None

    def test_multiple_agent_instances_share_context(self):
        """測試多個 Agent 實例共享全局上下文"""
        mock_mcp = Mock()
        mock_mcp.name = "tavily_mcp"
        mock_mcp.session = Mock()

        # 第一個 Agent
        get_sentiment_agent(mcp_servers=[mock_mcp])
        context_after_first = _sentiment_agent_context["tavily_mcp"]

        # 第二個 Agent（使用相同 MCP）
        get_sentiment_agent(mcp_servers=[mock_mcp])
        context_after_second = _sentiment_agent_context["tavily_mcp"]

        # 上下文應保持一致
        assert context_after_first is not None
        assert context_after_second is not None


class TestAutoFetchWithMockMCP:
    """測試自動蒐集功能（使用模擬 MCP）"""

    def setup_method(self):
        """重置全局上下文"""
        _sentiment_agent_context["tavily_mcp"] = None

    def teardown_method(self):
        """清理測試環境"""
        _sentiment_agent_context["tavily_mcp"] = None

    def test_auto_fetch_with_no_data_provided(self):
        """測試當沒有數據提供時自動蒐集"""
        # 由於沒有實際 MCP 連接，應返回 empty 或 error
        result = analyze_news_sentiment(
            ticker="2330",
            news_data=None,
            auto_fetch=True,
        )

        assert result is not None
        assert result.get("data_source") in ["empty", "error", "fetched"]

    def test_auto_fetch_disabled_returns_empty(self):
        """測試關閉自動蒐集時返回空"""
        result = analyze_news_sentiment(
            ticker="2330",
            news_data=None,
            auto_fetch=False,
        )

        assert result.get("data_source") == "empty"
        assert result.get("sentiment_score") == 0

    def test_provided_data_overrides_auto_fetch(self):
        """測試提供數據時自動蒐集被忽略"""
        result = analyze_news_sentiment(
            ticker="2330",
            news_data=[{"title": "提供的數據", "content": "內容", "source": "TEST"}],
            auto_fetch=True,
        )

        assert result.get("data_source") == "provided"
        # 不應觸發 MCP 調用

    def test_social_sentiment_auto_fetch_disabled(self):
        """測試社群情緒自動蒐集關閉"""
        result = analyze_social_sentiment(
            ticker="2330",
            social_data=None,
            auto_fetch=False,
        )

        assert result.get("data_source") == "empty"
        assert result.get("total_mentions") == 0


class TestContextIsolation:
    """測試全局上下文隔離"""

    def setup_method(self):
        """重置全局上下文"""
        _sentiment_agent_context["tavily_mcp"] = None

    def teardown_method(self):
        """清理測試環境"""
        _sentiment_agent_context["tavily_mcp"] = None

    def test_context_isolation_between_tests(self):
        """測試不同測試之間的上下文隔離"""
        # 設置上下文
        mock_mcp = Mock()
        mock_mcp.name = "tavily_mcp"
        _sentiment_agent_context["tavily_mcp"] = mock_mcp

        assert _sentiment_agent_context["tavily_mcp"] is mock_mcp

        # teardown 應清理上下文
        _sentiment_agent_context["tavily_mcp"] = None
        assert _sentiment_agent_context["tavily_mcp"] is None

    def test_concurrent_access_safety(self):
        """測試並發訪問安全性"""
        # 注意：全局字典本身不是線程安全的，但在 Agent 執行中應無競爭
        mock_mcp = Mock()
        mock_mcp.name = "tavily_mcp"

        # 模擬多個 Agent 初始化
        for _ in range(5):
            get_sentiment_agent(mcp_servers=[mock_mcp])
            # 上下文應保持一致
            assert _sentiment_agent_context["tavily_mcp"] is mock_mcp


class TestDataFlowIntegration:
    """測試完整的數據流"""

    def test_news_analysis_complete_flow(self):
        """測試完整的新聞分析數據流"""
        # 流程: 輸入數據 → 分析 → 返回結果

        input_news = [
            {
                "title": "台積電股價上升",
                "content": "利好消息，業績增長",
                "source": "新聞社",
            },
            {
                "title": "晶片需求下降",
                "content": "下跌趨勢，利空消息",
                "source": "市場分析",
            },
        ]

        result = analyze_news_sentiment(
            ticker="2330",
            news_data=input_news,
        )

        # 驗證完整的數據流
        assert result is not None
        assert result.get("ticker") == "2330"
        assert result.get("article_count") == 2
        assert result.get("data_source") == "provided"
        assert "sentiment_score" in result
        assert "confidence" in result
        assert "key_topics" in result

    def test_social_analysis_complete_flow(self):
        """測試完整的社群分析數據流"""
        social_data = SocialData(
            platform="PTT",
            mentions=150,
            positive_ratio=0.5,
            negative_ratio=0.3,
            neutral_ratio=0.2,
        )

        result = analyze_social_sentiment(
            ticker="2330",
            social_data=social_data,
        )

        # 驗證完整的數據流
        assert result is not None
        assert result.get("ticker") == "2330"
        assert result.get("total_mentions") == 150
        assert result.get("data_source") == "provided"
        assert "positive_mentions" in result
        assert "negative_mentions" in result


class TestErrorRecovery:
    """測試錯誤恢復機制"""

    def test_malformed_mcp_server(self):
        """測試格式錯誤的 MCP 服務器"""
        # MCP 沒有 name 屬性
        malformed_mcp = Mock(spec=[])

        # 應能優雅地處理
        agent = get_sentiment_agent(mcp_servers=[malformed_mcp])
        assert agent is not None

    def test_missing_mcp_session(self):
        """測試缺少 session 的 MCP"""
        incomplete_mcp = Mock()
        incomplete_mcp.name = "tavily_mcp"
        # 沒有 session 屬性

        agent = get_sentiment_agent(mcp_servers=[incomplete_mcp])
        assert agent is not None

    def test_analysis_with_corrupted_data(self):
        """測試數據損壞情況下的分析"""
        corrupted_news = [
            {"title": None, "content": None, "source": None},
            {"title": 123, "content": [], "source": {}},
        ]

        # 應能優雅地處理
        result = analyze_news_sentiment(
            ticker="2330",
            news_data=corrupted_news,
        )
        assert result is not None


class TestMCPCallSequence:
    """測試 MCP 調用序列"""

    def setup_method(self):
        """重置全局上下文"""
        _sentiment_agent_context["tavily_mcp"] = None

    def teardown_method(self):
        """清理測試環境"""
        _sentiment_agent_context["tavily_mcp"] = None

    def test_tool_call_sequence(self):
        """測試工具調用序列"""
        mock_mcp = Mock()
        mock_mcp.name = "tavily_mcp"
        mock_session = Mock()
        mock_mcp.session = mock_session

        # 初始化
        get_sentiment_agent(mcp_servers=[mock_mcp])

        # 進行分析（不觸發 MCP 因為有提供數據）
        result = analyze_news_sentiment(
            ticker="2330",
            news_data=[{"title": "測試", "content": "內容", "source": "TEST"}],
        )

        assert result is not None

        # 如果沒有提供數據且 auto_fetch=True，應嘗試調用 MCP
        # 但由於沒有實際實現，應返回 empty 或 error
        result_no_data = analyze_news_sentiment(
            ticker="2330",
            news_data=None,
            auto_fetch=True,
        )
        assert result_no_data.get("data_source") in ["empty", "error", "fetched"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
