"""
測試績效歷史 API 端點 - 包括進階風險指標

驗證:
1. API 返回正確的欄位名稱
2. 數據格式轉換正確 (小數 → 百分比)
3. 進階風險指標正確返回
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import get_agents_service


@pytest.mark.asyncio
class TestPerformanceHistoryAPI:
    """測試績效歷史 API 端點"""

    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        app = create_app()
        return TestClient(app), app

    def create_mock_performance_record(self, days_ago=0):
        """創建 mock 績效記錄"""
        record_date = date.today() - timedelta(days=days_ago)
        return {
            "date": record_date.isoformat(),
            "total_value": Decimal("1000000"),
            "total_return": Decimal("0.05"),  # 5% 小數格式
            "win_rate": Decimal("50.0"),  # 50% 百分比格式
            "daily_return": Decimal("0.01"),  # 1% 小數格式
            "max_drawdown": Decimal("2.5"),  # 2.5% 百分比格式
            "sharpe_ratio": Decimal("1.25"),  # 小數格式
            "sortino_ratio": Decimal("1.50"),  # 小數格式
            "calmar_ratio": Decimal("2.00"),  # 小數格式
            "cash_balance": Decimal("100000"),
            "realized_pnl": Decimal("50000"),
            "unrealized_pnl": Decimal("5000"),
            "total_trades": 10,
            "winning_trades_correct": 5,
        }

    async def test_performance_history_returns_correct_fields(self, client, monkeypatch):
        """
        測試 API 返回正確的欄位

        驗證:
        - portfolio_value (重命名自 total_value)
        - total_return (轉為百分比)
        - sharpe_ratio (新增進階指標)
        - sortino_ratio (新增進階指標)
        - calmar_ratio (新增進階指標)
        """
        test_client, app = client
        agent_id = "test-agent-001"

        # Mock AgentsService
        mock_service = AsyncMock()
        mock_service.get_performance_history.return_value = [
            self.create_mock_performance_record(0),
            self.create_mock_performance_record(1),
        ]

        # Mock dependency
        async def mock_get_service():
            return mock_service

        app.dependency_overrides[get_agents_service] = mock_get_service

        try:
            # 調用 API
            response = test_client.get(
                f"/api/trading/agents/{agent_id}/performance-history?limit=30&order=desc"
            )

            # 驗證響應
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # 驗證第一條記錄
            first_record = data[0]

            # 驗證欄位重命名
            assert "portfolio_value" in first_record
            assert first_record["portfolio_value"] == 1000000.0

            # 驗證百分比轉換
            assert first_record["total_return"] == 5.0  # 0.05 * 100
            assert first_record["daily_return"] == 1.0  # 0.01 * 100

            # 驗證進階指標
            assert "sharpe_ratio" in first_record
            assert first_record["sharpe_ratio"] == 1.25

            assert "sortino_ratio" in first_record
            assert first_record["sortino_ratio"] == 1.50

            assert "calmar_ratio" in first_record
            assert first_record["calmar_ratio"] == 2.00

            # 驗證其他欄位
            assert first_record["winning_trades"] == 5
            assert first_record["total_trades"] == 10

        finally:
            app.dependency_overrides.clear()

    async def test_performance_history_handles_null_advanced_metrics(self, client, monkeypatch):
        """
        測試 API 正確處理 NULL 的進階指標

        場景: 數據不足時，某些指標可能為 NULL
        """
        test_client, app = client
        agent_id = "test-agent-002"

        # 創建有 NULL 進階指標的記錄
        record = self.create_mock_performance_record(0)
        record["sharpe_ratio"] = None
        record["sortino_ratio"] = None
        record["calmar_ratio"] = None

        # Mock AgentsService
        mock_service = AsyncMock()
        mock_service.get_performance_history.return_value = [record]

        # Mock dependency
        async def mock_get_service():
            return mock_service

        app.dependency_overrides[get_agents_service] = mock_get_service

        try:
            # 調用 API
            response = test_client.get(
                f"/api/trading/agents/{agent_id}/performance-history?limit=30&order=desc"
            )

            # 驗證響應
            assert response.status_code == 200
            data = response.json()
            first_record = data[0]

            # 驗證 NULL 值正確返回
            assert first_record["sharpe_ratio"] is None
            assert first_record["sortino_ratio"] is None
            assert first_record["calmar_ratio"] is None

        finally:
            app.dependency_overrides.clear()

    async def test_performance_history_formats_all_metrics(self, client, monkeypatch):
        """
        測試 API 正確格式化所有指標

        驗證每個指標都被正確轉換:
        - 百分比指標 (%) : total_return, daily_return, max_drawdown, win_rate
        - 小數指標 : sharpe_ratio, sortino_ratio, calmar_ratio
        - 金額指標 (TWD) : portfolio_value, cash_balance, realized_pnl, unrealized_pnl
        """
        test_client, app = client
        agent_id = "test-agent-003"

        # Mock AgentsService
        mock_service = AsyncMock()
        mock_service.get_performance_history.return_value = [self.create_mock_performance_record(0)]

        # Mock dependency
        async def mock_get_service():
            return mock_service

        app.dependency_overrides[get_agents_service] = mock_get_service

        try:
            # 調用 API
            response = test_client.get(
                f"/api/trading/agents/{agent_id}/performance-history?limit=1&order=desc"
            )

            # 驗證響應
            assert response.status_code == 200
            data = response.json()
            record = data[0]

            # 驗證所有值都是 float 或 None
            assert isinstance(record["portfolio_value"], float)
            assert isinstance(record["total_return"], float)
            assert isinstance(record["daily_return"], float)
            assert isinstance(record["max_drawdown"], float)
            assert isinstance(record["win_rate"], float)
            assert isinstance(record["sharpe_ratio"], float)
            assert isinstance(record["sortino_ratio"], float)
            assert isinstance(record["calmar_ratio"], float)

            # 驗證百分比值的數值範圍
            assert 0 <= record["total_return"] <= 100
            assert 0 <= record["daily_return"] <= 10
            assert 0 <= record["max_drawdown"] <= 100
            assert 0 <= record["win_rate"] <= 100

        finally:
            app.dependency_overrides.clear()

    async def test_performance_history_invalid_limit(self, client):
        """測試無效的 limit 參數"""
        test_client, app = client
        agent_id = "test-agent-004"

        # 測試 limit 超過最大值
        response = test_client.get(
            f"/api/trading/agents/{agent_id}/performance-history?limit=400&order=desc"
        )
        assert response.status_code == 400

        # 測試 limit 為 0
        response = test_client.get(
            f"/api/trading/agents/{agent_id}/performance-history?limit=0&order=desc"
        )
        assert response.status_code == 400

    async def test_performance_history_invalid_order(self, client):
        """測試無效的 order 參數"""
        test_client, app = client
        agent_id = "test-agent-005"

        response = test_client.get(
            f"/api/trading/agents/{agent_id}/performance-history?limit=30&order=invalid"
        )
        assert response.status_code == 400
