"""
風險評估工具測試
測試 RiskAgent 的功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestRiskAgent:
    """RiskAgent 測試類"""

    def test_tools_class_exists(self):
        """測試工具類別存在"""
        try:
            from src.agents.tools.risk_agent import RiskAnalysisTools

            tools = RiskAnalysisTools()
            assert tools is not None
            assert hasattr(tools, "logger")

        except ImportError:
            pytest.skip("RiskAnalysisTools not available")

    def test_calculate_position_risk(self):
        """測試個別部位風險計算"""
        try:
            from src.agents.tools.risk_agent import RiskAnalysisTools

            tools = RiskAnalysisTools()

            # 模擬部位數據
            position_data = {
                "quantity": 1000,
                "avg_cost": 500,
                "current_price": 550,
            }

            market_data = {
                "volatility": 0.30,
                "beta": 1.2,
            }

            result = tools.calculate_position_risk("2330", position_data, market_data)

            # 檢查結果結構
            assert "symbol" in result
            assert result["symbol"] == "2330"
            assert "position_value" in result
            assert "unrealized_pnl" in result
            assert "pnl_percent" in result
            assert "volatility" in result
            assert "var_95" in result
            assert "risk_score" in result

            # 驗證計算正確性
            assert result["position_value"] == 550000
            assert result["unrealized_pnl"] == 50000

        except ImportError:
            pytest.skip("RiskAnalysisTools not available")

    def test_analyze_portfolio_concentration(self):
        """測試投資組合集中度分析"""
        try:
            from src.agents.tools.risk_agent import RiskAnalysisTools

            tools = RiskAnalysisTools()

            # 模擬投資組合
            positions = [
                {"value": 300000, "sector": "科技"},
                {"value": 200000, "sector": "金融"},
                {"value": 150000, "sector": "科技"},
                {"value": 100000, "sector": "傳產"},
            ]

            total_value = 750000

            result = tools.analyze_portfolio_concentration(positions, total_value)

            # 檢查結果結構
            assert "hhi_index" in result
            assert "concentration_level" in result
            assert "effective_stocks" in result
            assert "top5_concentration" in result
            assert "sector_concentration" in result

            # 檢查集中度等級有效性
            valid_levels = ["低", "中低", "中", "中高", "高"]
            assert result["concentration_level"] in valid_levels

        except ImportError:
            pytest.skip("RiskAnalysisTools not available")

    def test_calculate_portfolio_risk(self):
        """測試整體投資組合風險計算"""
        try:
            from src.agents.tools.risk_agent import RiskAnalysisTools

            tools = RiskAnalysisTools()

            # 模擬部位風險
            position_risks = [
                {
                    "symbol": "2330",
                    "position_value": 300000,
                    "risk_score": 40,
                    "var_95": 30000,
                },
                {
                    "symbol": "2317",
                    "position_value": 200000,
                    "risk_score": 35,
                    "var_95": 20000,
                },
            ]

            total_value = 500000

            # 需要先計算集中度
            concentration = {
                "hhi_index": 0.26,
                "concentration_level": "中",
            }

            result = tools.calculate_portfolio_risk(
                position_risks, concentration, total_value
            )

            # 檢查結果結構
            assert "total_value" in result
            assert "portfolio_var" in result
            assert "overall_risk_score" in result
            assert "risk_level" in result

            # 檢查風險等級有效性
            valid_levels = ["低", "中低", "中", "中高", "高"]
            assert result["risk_level"] in valid_levels

        except ImportError:
            pytest.skip("RiskAnalysisTools not available")

    def test_error_handling(self):
        """測試錯誤處理"""
        try:
            from src.agents.tools.risk_agent import RiskAnalysisTools

            tools = RiskAnalysisTools()

            # 測試空投資組合
            result = tools.analyze_portfolio_concentration([], 0)
            assert "error" in result

        except ImportError:
            pytest.skip("RiskAnalysisTools not available")


if __name__ == "__main__":
    pytest.main([__file__])
