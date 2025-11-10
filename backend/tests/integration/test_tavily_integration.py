"""
Tavily 搜尋功能集成測試

測試 _call_tavily_search 函數與 _parse_detailed_results 的集成。
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# 添加 src 目錄到 Python 路徑
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

import pytest  # noqa: E402

from trading.tools.sentiment_agent import _call_tavily_search  # noqa: E402


class TestTavilySearchIntegration:
    """測試 Tavily 搜尋功能的集成"""

    @pytest.mark.asyncio
    async def test_tavily_search_with_detailed_results_format(self):
        """測試解析 'Detailed Results' 格式的完整搜尋流程"""

        # 模擬 Tavily MCP 伺服器返回結果
        mock_server = AsyncMock()
        mock_content = MagicMock()
        mock_content.text = """Detailed Results:

Title: 台積電股票分析 - PTT 看板
URL: https://www.pttweb.cc/bbs/Stock/test
Content: 台積電基本面強勁，建議長期持有"""

        mock_result = MagicMock()
        mock_result.content = [mock_content]

        mock_server.session.call_tool = AsyncMock(return_value=mock_result)

        # 執行搜尋
        results = await _call_tavily_search(mock_server, "台積電分析", max_results=5)

        # 驗證結果
        assert len(results) == 1
        assert results[0]["title"] == "台積電股票分析 - PTT 看板"
        assert results[0]["url"] == "https://www.pttweb.cc/bbs/Stock/test"
        assert "基本面強勁" in results[0]["content"]
        assert results[0]["source"] == "tavily-search"

    @pytest.mark.asyncio
    async def test_tavily_search_with_multiple_results(self):
        """測試解析多筆搜尋結果"""

        mock_server = AsyncMock()
        mock_content = MagicMock()
        mock_content.text = """Detailed Results:

Title: First Result
URL: https://example1.com
Content: First content

Title: Second Result
URL: https://example2.com
Content: Second content"""

        mock_result = MagicMock()
        mock_result.content = [mock_content]

        mock_server.session.call_tool = AsyncMock(return_value=mock_result)

        # 執行搜尋
        results = await _call_tavily_search(mock_server, "test query", max_results=5)

        # 驗證結果
        assert len(results) == 2
        assert results[0]["title"] == "First Result"
        assert results[1]["title"] == "Second Result"

    @pytest.mark.asyncio
    async def test_tavily_search_with_json_format(self):
        """測試仍能解析 JSON 格式（向後相容）"""

        import json

        mock_server = AsyncMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps(
            {
                "results": [
                    {
                        "title": "JSON Result",
                        "url": "https://json.example.com",
                        "content": "JSON formatted content",
                        "source": "tavily",
                        "timestamp": "2025-11-10T18:20:00",
                    }
                ]
            }
        )

        mock_result = MagicMock()
        mock_result.content = [mock_content]

        mock_server.session.call_tool = AsyncMock(return_value=mock_result)

        # 執行搜尋
        results = await _call_tavily_search(mock_server, "test", max_results=5)

        # 驗證結果
        assert len(results) == 1
        assert results[0]["title"] == "JSON Result"

    @pytest.mark.asyncio
    async def test_tavily_search_empty_result(self):
        """測試處理空返回結果"""

        mock_server = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = []

        mock_server.session.call_tool = AsyncMock(return_value=mock_result)

        # 執行搜尋
        results = await _call_tavily_search(mock_server, "test", max_results=5)

        # 驗證結果為空
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_tavily_search_no_mcp_server(self):
        """測試 MCP 伺服器不可用的情況"""

        # 執行搜尋，mcp_server 為 None
        results = await _call_tavily_search(None, "test", max_results=5)

        # 驗證結果為空
        assert len(results) == 0


# 只在有 pytest-asyncio 時運行
try:
    import pytest

    pytest
except ImportError:
    # 如果沒有 pytest，跳過這些測試
    pass
