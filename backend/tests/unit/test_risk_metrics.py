"""
測試進階風險指標計算邏輯

測試場景:
1. Sharpe Ratio - 衡量風險調整後的報酬
2. Sortino Ratio - 只考慮下行風險
3. Calmar Ratio - 報酬與最大回撤比值
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from service.agents_service import AgentsService


@pytest.mark.asyncio
class TestSharpeRatio:
    """測試夏普比率計算"""

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

    async def test_sharpe_ratio_basic(self, agents_service, mock_session):
        """
        測試基本夏普比率計算

        當所有日報酬率相同時，標準差為 0，波動率為 0
        此時返回 0（無風險但也無變異）
        """
        agent_id = "test-agent-001"

        # 模擬日報酬率數據（相同值）
        daily_returns = [Decimal("0.5")] * 20
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算夏普比率
        sharpe_ratio = await agents_service.calculate_sharpe_ratio(agent_id)

        # 驗證結果 - 波動率為 0，所以夏普比率為 0
        assert sharpe_ratio is not None
        assert sharpe_ratio == Decimal("0")

    async def test_sharpe_ratio_insufficient_data(self, agents_service, mock_session):
        """
        測試資料不足情況 (< 20 個資料點)

        應返回 None
        """
        agent_id = "test-agent-002"

        # 只有 10 個交易日
        daily_returns = [Decimal("0.5")] * 10
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算夏普比率
        sharpe_ratio = await agents_service.calculate_sharpe_ratio(agent_id)

        # 驗證結果 - 資料不足
        assert sharpe_ratio is None

    async def test_sharpe_ratio_negative_return(self, agents_service, mock_session):
        """
        測試負報酬情況

        日報酬率: -0.5% (20個交易日，但都相同)
        波動率為 0，所以返回 0
        """
        agent_id = "test-agent-003"

        # 模擬負日報酬率（都相同）
        daily_returns = [Decimal("-0.5")] * 20
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算夏普比率
        sharpe_ratio = await agents_service.calculate_sharpe_ratio(agent_id)

        # 驗證結果 - 波動率為 0，所以夏普比率為 0
        assert sharpe_ratio is not None
        assert sharpe_ratio == Decimal("0")

    async def test_sharpe_ratio_mixed_returns(self, agents_service, mock_session):
        """
        測試混合報酬情況（上升和下降）

        模擬實際交易的波動
        """
        agent_id = "test-agent-004"

        # 模擬波動的日報酬率
        daily_returns = [
            Decimal("0.5"),
            Decimal("-0.2"),
            Decimal("0.8"),
            Decimal("0.1"),
            Decimal("-0.5"),
            Decimal("0.6"),
            Decimal("0.3"),
            Decimal("-0.1"),
            Decimal("0.7"),
            Decimal("0.4"),
            Decimal("-0.3"),
            Decimal("0.9"),
            Decimal("0.2"),
            Decimal("-0.4"),
            Decimal("0.5"),
            Decimal("0.6"),
            Decimal("-0.2"),
            Decimal("0.8"),
            Decimal("0.1"),
            Decimal("0.7"),
        ]
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算夏普比率
        sharpe_ratio = await agents_service.calculate_sharpe_ratio(agent_id)

        # 驗證結果
        assert sharpe_ratio is not None
        # 平均正報酬應該得到正夏普比率
        assert sharpe_ratio > 0

    async def test_sharpe_ratio_high_volatility(self, agents_service, mock_session):
        """
        測試高波動率情況

        大幅上下波動的報酬，應該有較低的夏普比率
        """
        agent_id = "test-agent-005"

        # 高波動率數據
        daily_returns = [
            Decimal("2.0"),
            Decimal("-3.0"),
            Decimal("2.5"),
            Decimal("-1.5"),
            Decimal("3.0"),
            Decimal("-2.0"),
            Decimal("1.5"),
            Decimal("-2.5"),
            Decimal("2.0"),
            Decimal("-1.0"),
            Decimal("2.5"),
            Decimal("-3.0"),
            Decimal("2.0"),
            Decimal("-2.0"),
            Decimal("1.5"),
            Decimal("-1.5"),
            Decimal("2.5"),
            Decimal("-2.5"),
            Decimal("3.0"),
            Decimal("1.0"),
        ]
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算夏普比率
        sharpe_ratio = await agents_service.calculate_sharpe_ratio(agent_id)

        # 驗證結果
        assert sharpe_ratio is not None
        # 高波動應該導致較低的夏普比率
        assert isinstance(sharpe_ratio, Decimal)


@pytest.mark.asyncio
class TestSortinoRatio:
    """測試索提諾比率計算"""

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

    async def test_sortino_ratio_no_downside(self, agents_service, mock_session):
        """
        測試無下行風險情況

        所有日報酬率都是正數，無下行波動
        應該返回很大的正數
        """
        agent_id = "test-agent-001"

        # 所有正報酬
        daily_returns = [Decimal("0.5")] * 20
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算索提諾比率
        sortino_ratio = await agents_service.calculate_sortino_ratio(agent_id)

        # 驗證結果 - 應該是很大的正數
        assert sortino_ratio is not None
        assert sortino_ratio > 100

    async def test_sortino_ratio_with_downside(self, agents_service, mock_session):
        """
        測試有下行風險情況

        混合正負報酬，索提諾比率應該低於夏普比率
        """
        agent_id = "test-agent-002"

        # 混合正負報酬，但平均為正
        daily_returns = [
            Decimal("0.5"),
            Decimal("-0.5"),
            Decimal("0.8"),
            Decimal("-0.3"),
            Decimal("0.6"),
            Decimal("-0.2"),
            Decimal("0.7"),
            Decimal("-0.1"),
            Decimal("0.9"),
            Decimal("-0.4"),
            Decimal("0.5"),
            Decimal("-0.1"),
            Decimal("0.8"),
            Decimal("-0.2"),
            Decimal("0.6"),
            Decimal("-0.3"),
            Decimal("0.7"),
            Decimal("-0.1"),
            Decimal("0.9"),
            Decimal("0.5"),
        ]
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算索提諾比率
        sortino_ratio = await agents_service.calculate_sortino_ratio(agent_id)

        # 驗證結果
        assert sortino_ratio is not None
        # 有下行風險，所以比率應該低於無下行風險的情況
        assert sortino_ratio > 0

    async def test_sortino_ratio_insufficient_data(self, agents_service, mock_session):
        """
        測試資料不足情況 (< 20 個資料點)

        應返回 None
        """
        agent_id = "test-agent-003"

        # 只有 10 個交易日
        daily_returns = [Decimal("0.5")] * 10
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算索提諾比率
        sortino_ratio = await agents_service.calculate_sortino_ratio(agent_id)

        # 驗證結果 - 資料不足
        assert sortino_ratio is None


@pytest.mark.asyncio
class TestCalmarRatio:
    """測試卡瑪比率計算"""

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

    async def test_calmar_ratio_basic(self, agents_service, mock_session):
        """
        測試基本卡瑪比率計算

        需要調用 calculate_max_drawdown，測試整合
        """
        agent_id = "test-agent-001"

        # Mock calculate_max_drawdown 返回 10%
        agents_service.calculate_max_drawdown = AsyncMock(return_value=Decimal("10"))

        # 模擬日報酬率
        daily_returns = [Decimal("0.5")] * 20

        # 需要一個額外的查詢（calculate_calmar_ratio 中的 daily_returns 查詢）
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算卡瑪比率
        calmar_ratio = await agents_service.calculate_calmar_ratio(agent_id)

        # 驗證結果
        assert calmar_ratio is not None
        # 正報酬 / 正回撤 應該是正數
        assert calmar_ratio > 0
        # 驗證調用了 calculate_max_drawdown
        agents_service.calculate_max_drawdown.assert_called_once_with(agent_id)

    async def test_calmar_ratio_no_max_drawdown(self, agents_service, mock_session):
        """
        測試無最大回撤情況

        當 max_drawdown 為 0 或 None 時應返回 None
        """
        agent_id = "test-agent-002"

        # Mock calculate_max_drawdown 返回 0
        agents_service.calculate_max_drawdown = AsyncMock(return_value=Decimal("0"))

        # 計算卡瑪比率
        calmar_ratio = await agents_service.calculate_calmar_ratio(agent_id)

        # 驗證結果 - 應返回 None
        assert calmar_ratio is None

    async def test_calmar_ratio_no_data(self, agents_service, mock_session):
        """
        測試無日報酬率數據情況

        應返回 None
        """
        agent_id = "test-agent-003"

        # Mock calculate_max_drawdown 返回有效值
        agents_service.calculate_max_drawdown = AsyncMock(return_value=Decimal("15"))

        # 無日報酬率數據
        daily_returns = []
        mock_result = self.create_mock_result(daily_returns)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 計算卡瑪比率
        calmar_ratio = await agents_service.calculate_calmar_ratio(agent_id)

        # 驗證結果 - 應返回 None
        assert calmar_ratio is None
