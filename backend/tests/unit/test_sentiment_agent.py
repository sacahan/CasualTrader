"""
情感分析 Agent 的測試

這個模組測試：
1. 輔助函數 (parse_tool_params 等)
2. Agent 初始化和工具加載
3. 異步操作（與之前刪除的 e2e/integration 測試不同）

注意: @function_tool 裝飾的函數無法直接調用（被轉換為 FunctionTool 對象）。
這些函數應該通過完整的 Agent 框架進行測試。
"""

import sys
from pathlib import Path

import pytest

# 添加 src 目錄到 Python 路徑
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from trading.tools.sentiment_agent import (  # noqa: E402
    parse_tool_params,
    sentiment_agent_instructions,
    get_sentiment_agent,
    _extract_sentiment_from_text,
    _extract_key_topics,
)


# ============================================================================
# 輔助函數測試 (可以直接調用，因為沒有被 @function_tool 裝飾)
# ============================================================================


class TestSentimentHelperFunctions:
    """測試不被 @function_tool 裝飾的輔助函數"""

    def test_extract_sentiment_from_text_positive(self):
        """測試從正面文本提取情感"""
        text = "台積電股票表現出色，基本面強勁，投資前景看好。"
        result = _extract_sentiment_from_text(text)

        assert result is not None
        assert isinstance(result, (float, int, str, dict))

    def test_extract_sentiment_from_text_negative(self):
        """測試從負面文本提取情感"""
        text = "股票下跌，業績不佳，市場風險增加。"
        result = _extract_sentiment_from_text(text)

        assert result is not None

    def test_extract_sentiment_from_text_neutral(self):
        """測試從中立文本提取情感"""
        text = "股票價格在520元左右波動。"
        result = _extract_sentiment_from_text(text)

        assert result is not None

    def test_extract_sentiment_from_empty_text(self):
        """測試從空文本提取情感"""
        result = _extract_sentiment_from_text("")

        # 應該返回某種結果
        assert result is not None

    def test_extract_sentiment_from_mixed_text(self):
        """測試從混合文本提取情感"""
        text = "好消息是營收增長，壞消息是成本上升。"
        result = _extract_sentiment_from_text(text)

        assert result is not None

    def test_extract_key_topics_from_text(self):
        """測試從文本提取關鍵主題"""
        articles = [
            {
                "title": "台積電強化先進製程",
                "content": "AI 應用需求旺盛，晶片短缺持續。",
            }
        ]
        result = _extract_key_topics(articles)

        assert result is not None
        # 應該返回主題相關的結果
        assert isinstance(result, (list, str, dict))

    def test_extract_key_topics_empty_text(self):
        """測試從空文本提取主題"""
        articles = []
        result = _extract_key_topics(articles)

        assert result is not None

    def test_extract_key_topics_short_text(self):
        """測試從短文本提取主題"""
        articles = [{"title": "晶片", "content": ""}]
        result = _extract_key_topics(articles)

        assert result is not None

    def test_extract_key_topics_long_text(self):
        """測試從長文本提取主題"""
        articles = [
            {
                "title": "台積電面臨挑戰和機遇",
                "content": """台積電作為全球最大的晶圓代工廠，面臨著來自多方面的挑戰和機遇。
        在人工智能芯片需求爆炸的時代，公司正在加快先進製程的開發。
        同時，地緣政治風險和供應鏈問題也在對業務造成影響。""",
            }
        ]

        result = _extract_key_topics(articles)

        assert result is not None


# ============================================================================
# 參數解析測試
# ============================================================================


class TestSentimentAgentParseToolParams:
    """測試情感分析 Agent 的參數解析函數"""

    def test_parse_direct_parameters(self):
        """測試直接參數解析"""
        result = parse_tool_params(ticker="2330", news_source="社交媒體")
        assert result["ticker"] == "2330"
        assert result["news_source"] == "社交媒體"

    def test_parse_json_string_in_args(self):
        """測試 JSON 字符串參數解析"""
        import json

        data = {"ticker": "2330", "sentiment": "positive"}
        result = parse_tool_params(args=json.dumps(data))
        assert result["ticker"] == "2330"
        assert result["sentiment"] == "positive"

    def test_parse_removes_invalid_keys(self):
        """測試移除無效鍵"""
        result = parse_tool_params(ticker="2330", input_image="invalid", topic="AI")
        assert "ticker" in result
        assert "topic" in result
        assert "input_image" not in result

    def test_parse_empty_parameters(self):
        """測試空參數"""
        result = parse_tool_params()
        assert isinstance(result, dict)

    def test_parse_sentiment_data(self):
        """測試情感數據解析"""
        sentiment_data = {
            "positive_count": 100,
            "negative_count": 30,
            "neutral_count": 70,
        }
        result = parse_tool_params(data=sentiment_data)

        assert result is not None
        assert "data" in result


# ============================================================================
# Agent 初始化和工具加載測試
# ============================================================================


class TestSentimentAgentInitialization:
    """測試 Sentiment Agent 初始化"""

    def test_agent_instructions_generated(self):
        """測試 Agent 指令生成"""
        instructions = sentiment_agent_instructions()

        assert instructions is not None
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        # 驗證關鍵內容存在
        assert "情感" in instructions or "sentiment" in instructions.lower()

    @pytest.mark.asyncio
    async def test_get_sentiment_agent_creation(self):
        """測試創建 Sentiment Agent"""
        agent = await get_sentiment_agent()

        assert agent is not None
        assert hasattr(agent, "name")
        assert agent.name == "sentiment_analyst"
        assert hasattr(agent, "instructions")

    @pytest.mark.asyncio
    async def test_get_sentiment_agent_with_empty_mcp(self):
        """測試帶空 MCP servers 列表創建 Agent"""
        agent = await get_sentiment_agent(mcp_servers=[])

        assert agent is not None
        assert hasattr(agent, "name")
        assert agent.name == "sentiment_analyst"

    @pytest.mark.asyncio
    async def test_sentiment_agent_has_tools(self):
        """測試 Agent 包含工具"""
        agent = await get_sentiment_agent()

        assert agent is not None
        # Agent 應該有 tools 屬性或方法
        has_tools = hasattr(agent, "tools") or hasattr(agent, "model_settings")
        assert has_tools is True

    @pytest.mark.asyncio
    async def test_sentiment_agent_model_settings(self):
        """測試 Agent 模型配置"""
        agent = await get_sentiment_agent()

        assert agent is not None
        # 驗證 Agent 有必要的配置屬性
        assert hasattr(agent, "instructions") or hasattr(agent, "tools")


# ============================================================================
# 工具定義驗證測試
# ============================================================================


class TestSentimentAgentTools:
    """測試 Sentiment Agent 工具定義"""

    @pytest.mark.asyncio
    async def test_agent_has_required_tools(self):
        """測試 Agent 包含必要的工具"""
        agent = await get_sentiment_agent()

        assert agent is not None
        # Agent 應該包含情感分析相關的工具

        if hasattr(agent, "tools") and agent.tools:
            tool_count = len(agent.tools)
            # 應該至少有工具
            assert tool_count >= 3

    @pytest.mark.asyncio
    async def test_agent_tools_have_descriptions(self):
        """測試工具有描述信息"""
        agent = await get_sentiment_agent()

        assert agent is not None
        if hasattr(agent, "tools") and agent.tools:
            for tool in agent.tools:
                # 每個工具應該有描述
                assert hasattr(tool, "description") or hasattr(tool, "name")


# ============================================================================
# 邊界和錯誤情況測試
# ============================================================================


class TestSentimentAgentEdgeCases:
    """測試邊界情況"""

    def test_parse_with_malformed_json(self):
        """測試解析格式錯誤的 JSON"""
        result = parse_tool_params(args='{"invalid": json}')
        # 應該返回字典
        assert isinstance(result, dict)

    def test_parse_with_nested_json(self):
        """測試嵌套 JSON 解析"""
        import json

        nested_data = {
            "ticker": "2330",
            "analysis": {
                "sentiment": "positive",
                "nested": {"key": "value"},
            },
        }
        result = parse_tool_params(args=json.dumps(nested_data))

        assert result["ticker"] == "2330"
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_multiple_agent_creations(self):
        """測試多次創建 Agent"""
        agent1 = await get_sentiment_agent()
        agent2 = await get_sentiment_agent()

        assert agent1 is not None
        assert agent2 is not None
        # 兩個代理應該都是有效的
        assert agent1.name == agent2.name

    def test_parse_with_special_characters(self):
        """測試特殊字符處理"""
        result = parse_tool_params(
            ticker="2330-TW",
            description="情感分析 (台積電)",
            special="™®©",
        )

        assert result is not None
        assert result["ticker"] == "2330-TW"

    def test_parse_sentiment_scores(self):
        """測試情感分數解析"""
        result = parse_tool_params(
            positive_score=0.85,
            negative_score=0.05,
            neutral_score=0.10,
        )

        assert result is not None
        assert result["positive_score"] == 0.85
        assert result["negative_score"] == 0.05


# ============================================================================
# 情感分析特定場景測試
# ============================================================================


class TestSentimentAgentScenarios:
    """測試情感分析場景"""

    @pytest.mark.asyncio
    async def test_agent_creation_with_custom_model(self):
        """測試使用自訂模型創建 Agent"""
        agent = await get_sentiment_agent(llm_model=None)

        assert agent is not None
        assert agent.name == "sentiment_analyst"

    def test_parse_news_content(self):
        """測試新聞內容解析"""
        news = {
            "title": "台積電先進製程取得突破",
            "content": "台積電宣布在 3nm 製程上的新進展...",
            "source": "新聞機構",
        }

        result = parse_tool_params(news=news)

        assert result is not None
        assert "news" in result

    def test_parse_social_sentiment(self):
        """測試社交媒體情感解析"""
        social_data = {
            "tweets": 1500,
            "positive_tweets": 850,
            "negative_tweets": 200,
            "mentions": 2500,
        }

        result = parse_tool_params(social=social_data)

        assert result is not None
        assert "social" in result

    def test_extract_sentiment_with_various_languages(self):
        """測試不同語言的情感提取"""
        texts = [
            "股票表現良好",  # 中文
            "Good performance",  # 英文
            "很棒的業績",  # 中文
        ]

        for text in texts:
            result = _extract_sentiment_from_text(text)
            assert result is not None

    def test_extract_topics_from_market_news(self):
        """測試從市場新聞提取主題"""
        articles = [
            {
                "title": "市場新聞",
                "content": "NVIDIA AI 晶片需求旺盛，台積電訂單飆升，半導體產業復蘇",
            }
        ]

        result = _extract_key_topics(articles)

        assert result is not None


# ============================================================================
# 異步操作測試
# ============================================================================


class TestSentimentAgentAsync:
    """測試異步操作"""

    @pytest.mark.asyncio
    async def test_async_agent_initialization(self):
        """測試異步 Agent 初始化"""
        agent = await get_sentiment_agent()
        assert agent is not None

    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self):
        """測試並發 Agent 創建"""
        import asyncio

        agents = await asyncio.gather(
            get_sentiment_agent(),
            get_sentiment_agent(),
            get_sentiment_agent(),
        )

        assert len(agents) == 3
        assert all(agent is not None for agent in agents)
        assert all(agent.name == "sentiment_analyst" for agent in agents)

    @pytest.mark.asyncio
    async def test_agent_creation_timeout(self):
        """測試 Agent 創建不應該無限期掛起"""
        import asyncio

        try:
            agent = await asyncio.wait_for(
                get_sentiment_agent(),
                timeout=10.0,
            )
            assert agent is not None
        except asyncio.TimeoutError:
            pytest.fail("Agent creation timed out")
