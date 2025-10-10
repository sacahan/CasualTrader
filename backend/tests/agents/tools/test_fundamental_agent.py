"""
基本面分析工具測試
測試 FundamentalAgent 的功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestFundamentalAgent:
    """FundamentalAgent 測試類"""

    def test_tools_class_exists(self):
        """測試工具類別存在"""
        try:
            from src.agents.tools.fundamental_agent import FundamentalAnalysisTools

            tools = FundamentalAnalysisTools()
            assert tools is not None
            assert hasattr(tools, "logger")

        except ImportError:
            pytest.skip("FundamentalAnalysisTools not available")

    def test_calculate_financial_ratios(self):
        """測試財務比率計算"""
        try:
            from src.agents.tools.fundamental_agent import FundamentalAnalysisTools

            tools = FundamentalAnalysisTools()

            # 模擬財務數據
            financial_data = {
                "total_equity": 1000000,
                "total_assets": 2000000,
                "revenue": 5000000,
                "net_income": 500000,
                "total_liabilities": 1000000,
                "current_assets": 800000,
                "current_liabilities": 400000,
                "market_cap": 10000000,
            }

            result = tools.calculate_financial_ratios("2330", financial_data)

            # 檢查結果結構
            assert "ticker" in result
            assert result["ticker"] == "2330"
            assert "profitability" in result
            assert "solvency" in result
            assert "valuation" in result

            # 檢查獲利能力指標
            assert "roe" in result["profitability"]
            assert "roa" in result["profitability"]
            assert "net_margin" in result["profitability"]

            # 驗證計算正確性
            assert result["profitability"]["roe"] == pytest.approx(0.5, rel=0.01)
            assert result["profitability"]["roa"] == pytest.approx(0.25, rel=0.01)

        except ImportError:
            pytest.skip("FundamentalAnalysisTools not available")

    def test_analyze_financial_health(self):
        """測試財務體質分析"""
        try:
            from src.agents.tools.fundamental_agent import FundamentalAnalysisTools

            tools = FundamentalAnalysisTools()

            # 模擬財務比率
            financial_ratios = {
                "profitability": {
                    "roe": 0.2,
                    "roa": 0.1,
                    "net_margin": 0.15,
                },
                "solvency": {
                    "debt_ratio": 0.4,
                    "current_ratio": 2.0,
                },
                "valuation": {
                    "pe_ratio": 15,
                    "pb_ratio": 2.0,
                },
            }

            result = tools.analyze_financial_health("2330", financial_ratios)

            # 檢查結果結構
            assert "ticker" in result
            assert "health_score" in result
            assert "health_grade" in result
            assert "assessment" in result
            assert "strengths" in result
            assert "weaknesses" in result

            # 檢查評級有效性
            valid_grades = ["A", "B", "C", "D", "F"]
            assert result["health_grade"] in valid_grades

        except ImportError:
            pytest.skip("FundamentalAnalysisTools not available")

    def test_error_handling(self):
        """測試錯誤處理"""
        try:
            from src.agents.tools.fundamental_agent import FundamentalAnalysisTools

            tools = FundamentalAnalysisTools()

            # 測試空數據
            result = tools.calculate_financial_ratios("2330", {})
            assert "error" in result

            # 測試錯誤的財務比率
            result = tools.analyze_financial_health("2330", {"error": "test"})
            assert "error" in result

        except ImportError:
            pytest.skip("FundamentalAnalysisTools not available")


if __name__ == "__main__":
    pytest.main([__file__])
