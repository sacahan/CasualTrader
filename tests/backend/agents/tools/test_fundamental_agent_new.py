"""基本面分析工具測試

測試 FundamentalAgent 的功能，包括：
- 財務比率計算
- 財務體質分析
- 估值評估
- 成長潛力分析
- 投資評級產生
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from agents.tools.fundamental_agent import FundamentalAnalysisTools  # noqa: E402


@pytest.fixture
def sample_financial_data() -> dict[str, Any]:
    """提供測試用財務數據"""
    return {
        "revenue": 1000000000,
        "net_income": 100000000,
        "total_assets": 500000000,
        "total_equity": 300000000,
        "total_liabilities": 200000000,
        "current_assets": 250000000,
        "current_liabilities": 100000000,
        "market_cap": 1000000000,
    }


@pytest.fixture
def tools() -> FundamentalAnalysisTools:
    """建立 FundamentalAnalysisTools 實例"""
    return FundamentalAnalysisTools()


class TestCalculateFinancialRatios:
    """測試財務比率計算功能"""

    def test_calculate_ratios_structure(self, tools, sample_financial_data):
        """測試財務比率結構"""
        result = tools.calculate_financial_ratios("2330", sample_financial_data)
        assert "symbol" in result
        assert "profitability" in result
        assert "solvency" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
