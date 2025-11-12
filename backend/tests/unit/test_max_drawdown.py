"""
測試最大回撤 (max_drawdown) 計算邏輯

測試場景:
1. 基本情況 - 有回撤
2. 持續上漲 - 無回撤
3. 持續下跌 - 最大回撤
4. 多次回撤 - 選擇最大值
5. 資料不足 - 返回 None
6. 邊界情況 - 淨值為 0
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from service.agents_service import AgentsService


@pytest.mark.asyncio
class TestMaxDrawdown:
    """測試最大回撤計算"""

    @pytest.fixture
    def mock_session(self):
        """創建 mock session"""
        return AsyncMock()

    @pytest.fixture
    def agents_service(self, mock_session):
        """創建 AgentsService 實例"""
        return AgentsService(mock_session)

    def create_mock_result(self, values):
        """創建 mock SQLAlchemy 查詢結果"""
        mock_result = MagicMock()
        mock_result.all.return_value = [(value,) for value in values]
        return mock_result

    async def test_basic_drawdown(self, agents_service, mock_session):
        """
        測試基本回撤情況

        淨值曲線: 1000000 → 1100000 → 1050000 → 1200000
        最高點: 1100000
        最低點: 1050000 (在 1100000 之後)
        最大回撤: (1100000 - 1050000) / 1100000 = 4.55%
        """
        agent_id = "test-agent-001"

        # Mock 歷史淨值數據
        values = [
            Decimal("1000000"),
            Decimal("1100000"),
            Decimal("1050000"),
            Decimal("1200000"),
        ]
        mock_result = self.create_mock_result(values)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算最大回撤
        max_drawdown = await agents_service.calculate_max_drawdown(agent_id)

        # 驗證結果
        assert max_drawdown is not None
        # (1100000 - 1050000) / 1100000 * 100 = 4.545454...
        assert abs(max_drawdown - Decimal("4.545454545454545454545454545")) < Decimal("0.01")

    async def test_no_drawdown_uptrend(self, agents_service, mock_session):
        """
        測試持續上漲無回撤情況

        淨值曲線: 1000000 → 1100000 → 1200000 → 1300000
        最大回撤: 0%
        """
        agent_id = "test-agent-002"

        # Mock 歷史淨值數據（持續上漲）
        values = [
            Decimal("1000000"),
            Decimal("1100000"),
            Decimal("1200000"),
            Decimal("1300000"),
        ]
        mock_result = self.create_mock_result(values)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算最大回撤
        max_drawdown = await agents_service.calculate_max_drawdown(agent_id)

        # 驗證結果 - 無回撤
        assert max_drawdown is not None
        assert max_drawdown == Decimal("0")

    async def test_maximum_drawdown_downtrend(self, agents_service, mock_session):
        """
        測試持續下跌最大回撤情況

        淨值曲線: 1000000 → 900000 → 800000 → 700000
        最高點: 1000000
        最低點: 700000
        最大回撤: (1000000 - 700000) / 1000000 = 30%
        """
        agent_id = "test-agent-003"

        # Mock 歷史淨值數據（持續下跌）
        values = [
            Decimal("1000000"),
            Decimal("900000"),
            Decimal("800000"),
            Decimal("700000"),
        ]
        mock_result = self.create_mock_result(values)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算最大回撤
        max_drawdown = await agents_service.calculate_max_drawdown(agent_id)

        # 驗證結果
        assert max_drawdown is not None
        assert max_drawdown == Decimal("30")

    async def test_multiple_drawdowns(self, agents_service, mock_session):
        """
        測試多次回撤，選擇最大值

        淨值曲線: 1000000 → 1100000 → 1050000 (回撤4.55%)
                  → 1200000 → 1000000 (回撤16.67%) ← 最大
        """
        agent_id = "test-agent-004"

        # Mock 歷史淨值數據（多次回撤）
        values = [
            Decimal("1000000"),
            Decimal("1100000"),
            Decimal("1050000"),
            Decimal("1200000"),
            Decimal("1000000"),
        ]
        mock_result = self.create_mock_result(values)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算最大回撤
        max_drawdown = await agents_service.calculate_max_drawdown(agent_id)

        # 驗證結果 - 應該是第二次回撤
        # (1200000 - 1000000) / 1200000 * 100 = 16.666666...
        assert max_drawdown is not None
        assert abs(max_drawdown - Decimal("16.666666666666666666666666667")) < Decimal("0.01")

    async def test_insufficient_data(self, agents_service, mock_session):
        """
        測試資料不足情況 (< 2 個資料點)

        應返回 None
        """
        agent_id = "test-agent-005"

        # Mock 歷史淨值數據（只有 1 筆）
        values = [Decimal("1000000")]
        mock_result = self.create_mock_result(values)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算最大回撤
        max_drawdown = await agents_service.calculate_max_drawdown(agent_id)

        # 驗證結果 - 資料不足
        assert max_drawdown is None

    async def test_no_data(self, agents_service, mock_session):
        """
        測試無資料情況

        應返回 None
        """
        agent_id = "test-agent-006"

        # Mock 歷史淨值數據（無資料）
        values = []
        mock_result = self.create_mock_result(values)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算最大回撤
        max_drawdown = await agents_service.calculate_max_drawdown(agent_id)

        # 驗證結果 - 無資料
        assert max_drawdown is None

    async def test_zero_value_handling(self, agents_service, mock_session):
        """
        測試淨值為 0 的邊界情況

        淨值曲線: 1000000 → 0 → 500000
        最大回撤: (1000000 - 0) / 1000000 = 100%
        """
        agent_id = "test-agent-007"

        # Mock 歷史淨值數據（包含 0）
        values = [
            Decimal("1000000"),
            Decimal("0"),
            Decimal("500000"),
        ]
        mock_result = self.create_mock_result(values)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算最大回撤
        max_drawdown = await agents_service.calculate_max_drawdown(agent_id)

        # 驗證結果 - 最大回撤 100%
        assert max_drawdown is not None
        assert max_drawdown == Decimal("100")

    async def test_recovery_after_drawdown(self, agents_service, mock_session):
        """
        測試回撤後恢復的情況

        淨值曲線: 1000000 → 1200000 → 900000 (回撤25%) → 1300000 (新高)
        最大回撤: (1200000 - 900000) / 1200000 = 25%
        """
        agent_id = "test-agent-008"

        # Mock 歷史淨值數據（回撤後恢復）
        values = [
            Decimal("1000000"),
            Decimal("1200000"),
            Decimal("900000"),
            Decimal("1300000"),
        ]
        mock_result = self.create_mock_result(values)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算最大回撤
        max_drawdown = await agents_service.calculate_max_drawdown(agent_id)

        # 驗證結果
        # (1200000 - 900000) / 1200000 * 100 = 25%
        assert max_drawdown is not None
        assert max_drawdown == Decimal("25")
