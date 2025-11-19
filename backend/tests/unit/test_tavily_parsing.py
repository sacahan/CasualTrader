"""
測試 Perplexity 搜尋結果解析函數

這個模組測試 _parse_detailed_results 函數，確保它能正確解析
Perplexity 返回的 'Detailed Results' 格式。
"""

import sys
from pathlib import Path

# 添加 src 目錄到 Python 路徑
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from trading.tools.sentiment_agent import _parse_detailed_results  # noqa: E402


class TestParseDetailedResults:
    """測試 _parse_detailed_results 函數"""

    def test_parse_single_result(self):
        """測試解析單筆搜尋結果"""
        test_content = """Detailed Results:

Title: [標的] 2881富邦金說好的教訓呢QQ? - 看板Stock - PTT網頁版
URL: https://www.pttweb.cc/bbs/Stock/M.1652840005.A.CB4
Content: 標的：2881.TW 富邦金2. 分類：討論3. 分析/正文： 這幾天大家一直保單問題氣噗噗"""

        results = _parse_detailed_results(test_content)

        assert len(results) == 1
        assert results[0]["title"] == "[標的] 2881富邦金說好的教訓呢QQ? - 看板Stock - PTT網頁版"
        assert results[0]["url"] == "https://www.pttweb.cc/bbs/Stock/M.1652840005.A.CB4"
        assert "2881.TW 富邦金2" in results[0]["content"]
        assert results[0]["source"] == "perplexity-search"

    def test_parse_multiple_results(self):
        """測試解析多筆搜尋結果"""
        test_content = """Detailed Results:

Title: First Result Title
URL: https://example1.com
Content: First result content here

Title: Second Result Title
URL: https://example2.com
Content: Second result content here"""

        results = _parse_detailed_results(test_content)

        assert len(results) == 2
        assert results[0]["title"] == "First Result Title"
        assert results[0]["url"] == "https://example1.com"
        assert results[1]["title"] == "Second Result Title"
        assert results[1]["url"] == "https://example2.com"

    def test_parse_without_content_label(self):
        """測試解析沒有 'Content:' 標籤的結果"""
        test_content = """Detailed Results:

Title: Some Title
URL: https://example.com
This is the content line without label"""

        results = _parse_detailed_results(test_content)

        assert len(results) == 1
        assert results[0]["title"] == "Some Title"
        assert results[0]["url"] == "https://example.com"

    def test_parse_empty_content(self):
        """測試解析空內容"""
        test_content = ""

        results = _parse_detailed_results(test_content)

        assert len(results) == 0

    def test_parse_missing_url(self):
        """測試解析缺少 URL 的結果（應被跳過）"""
        test_content = """Detailed Results:

Title: Title without URL
Content: Some content"""

        results = _parse_detailed_results(test_content)

        # 因為沒有 URL，不應該被包含
        assert len(results) == 0

    def test_parse_preserves_timestamp(self):
        """測試解析結果包含時間戳"""
        test_content = """Detailed Results:

Title: Test Title
URL: https://test.com
Content: Test content"""

        results = _parse_detailed_results(test_content)

        assert len(results) == 1
        assert "timestamp" in results[0]
        assert results[0]["timestamp"] is not None

    def test_parse_real_format_from_logs(self):
        """測試根據日誌中的實際格式解析"""
        # 這是從日誌中提取的實際格式
        test_content = """Detailed Results:

Title: [標的] 2881富邦金說好的教訓呢QQ? - 看板Stock - PTT網頁版
URL: https://www.pttweb.cc/bbs/Stock/M.1652840005.A.CB4
Content: 標的：2881.TW 富邦金2. 分類：討論3. 分析/正文： 這幾天大家一直保單問題氣噗噗，說什麼乃哥金、富崩金之類的"""

        results = _parse_detailed_results(test_content)

        assert len(results) == 1
        result = results[0]
        assert result["title"] == "[標的] 2881富邦金說好的教訓呢QQ? - 看板Stock - PTT網頁版"
        assert result["url"] == "https://www.pttweb.cc/bbs/Stock/M.1652840005.A.CB4"
        assert "富邦金" in result["content"]
        assert result["source"] == "perplexity-search"
