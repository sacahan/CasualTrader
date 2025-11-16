"""
Simple Integration Test for Agent Execution API Bug Fix

測試目標:
1. 驗證 get_execution_history() 和 get_session_detail() 不會拋出 AttributeError
2. 驗證狀態值安全提取邏輯正確運行
3. 不依賴複雜的資料庫設置
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import get_agents_service, get_trading_service
from common.enums import TransactionStatus, TransactionAction


class TestAgentExecutionApiBugFix:
    """測試 Bug 修復 - 狀態值提取"""

    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def mock_agent_service(self):
        """Mock AgentsService"""
        service = AsyncMock()
        return service

    @pytest.fixture
    def mock_trading_service(self):
        """Mock TradingService"""
        service = AsyncMock()
        return service

    def create_mock_session(self, session_id="session-001", status="completed"):
        """創建 mock session"""
        mock = MagicMock()
        mock.id = session_id
        mock.agent_id = "agent-001"
        mock.status = status
        mock.mode = "ANALYSIS"
        mock.created_at = "2025-01-01T00:00:00"
        mock.updated_at = "2025-01-01T00:10:00"
        mock.started_at = "2025-01-01T00:00:00"
        mock.ended_at = "2025-01-01T00:10:00"
        mock.final_output = "Test output"
        mock.tools_called = []
        return mock

    def create_mock_transaction(
        self, tx_id="tx-001", status=TransactionStatus.EXECUTED, action=TransactionAction.BUY
    ):
        """創建 mock transaction"""
        mock = MagicMock()
        mock.id = tx_id
        mock.session_id = "session-001"
        mock.symbol = "2330"
        mock.action = action  # Enum 類型
        mock.status = status  # Enum 類型
        mock.quantity = 1000
        mock.price = 500.0
        mock.total_amount = 500000.0
        mock.commission = 1425.0
        mock.decision_reason = "Test decision"
        mock.execution_time = None
        mock.created_at = "2025-01-01T00:05:00"
        return mock

    def test_get_execution_history_with_enum_status(
        self, client, mock_agent_service, mock_trading_service, monkeypatch
    ):
        """
        測試 get_execution_history 處理 Enum 狀態

        驗證:
        - API 不會拋出 AttributeError
        - 正確計算 filled_count
        - 正確計算 total_notional
        """
        # 準備 mock 資料
        mock_session = self.create_mock_session()
        mock_agent_service.get_sessions_by_agent.return_value = [mock_session]

        # 創建包含 Enum 狀態的交易
        mock_tx1 = self.create_mock_transaction("tx-001", status=TransactionStatus.EXECUTED)  # Enum
        mock_tx2 = self.create_mock_transaction("tx-002", status=TransactionStatus.PENDING)  # Enum
        mock_trading_service.get_transactions_by_session.return_value = [mock_tx1, mock_tx2]

        # 覆蓋依賴
        app = create_app()
        app.dependency_overrides[get_agents_service] = lambda: mock_agent_service
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        # 調用 API
        client = TestClient(app)
        response = client.get("/api/agent-execution/agent-001/history")

        # 驗證
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "session-001"
        assert "filled_count" in data[0]
        assert "total_notional" in data[0]
        # 應該計算出 1 筆 EXECUTED
        assert data[0]["filled_count"] == 1

    def test_get_execution_history_with_string_status(
        self, client, mock_agent_service, mock_trading_service, monkeypatch
    ):
        """
        測試 get_execution_history 處理字符串狀態

        驗證:
        - API 不會拋出 AttributeError
        - 正確處理字符串狀態
        """
        # 準備 mock 資料
        mock_session = self.create_mock_session()
        mock_agent_service.get_sessions_by_agent.return_value = [mock_session]

        # 創建包含字符串狀態的交易
        mock_tx1 = MagicMock()
        mock_tx1.status = "executed"  # 字符串，不是 Enum
        mock_tx1.total_amount = 500000.0
        mock_trading_service.get_transactions_by_session.return_value = [mock_tx1]

        # 覆蓋依賴
        app = create_app()
        app.dependency_overrides[get_agents_service] = lambda: mock_agent_service
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        # 調用 API（不應拋出錯誤）
        client = TestClient(app)
        response = client.get("/api/agent-execution/agent-001/history")

        # 驗證 - 主要確保沒有拋出 AttributeError
        assert response.status_code == 200

    def test_get_session_detail_with_mixed_status(
        self, client, mock_agent_service, mock_trading_service
    ):
        """
        測試 get_session_detail 處理混合狀態類型

        驗證:
        - API 不會拋出 AttributeError
        - 正確處理 Enum + 字符串混合狀態
        - 正確計算統計
        """
        # 準備 mock 資料
        mock_session = self.create_mock_session()
        mock_agent_service.get_session_by_id.return_value = mock_session

        # 創建混合狀態的交易
        mock_tx1 = self.create_mock_transaction("tx-001", status=TransactionStatus.EXECUTED)  # Enum
        mock_tx2 = MagicMock()
        mock_tx2.id = "tx-002"
        mock_tx2.session_id = "session-001"
        mock_tx2.symbol = "2317"
        mock_tx2.action = "SELL"  # 字符串
        mock_tx2.status = "executed"  # 字符串
        mock_tx2.quantity = 1000
        mock_tx2.price = 300.0
        mock_tx2.total_amount = 300000.0
        mock_tx2.commission = 855.0
        mock_tx2.decision_reason = "Test"
        mock_tx2.execution_time = None
        mock_tx2.created_at = "2025-01-01T00:06:00"

        mock_trading_service.get_transactions_by_session.return_value = [mock_tx1, mock_tx2]

        # 覆蓋依賴
        app = create_app()
        app.dependency_overrides[get_agents_service] = lambda: mock_agent_service
        app.dependency_overrides[get_trading_service] = lambda: mock_trading_service

        # 調用 API
        client = TestClient(app)
        response = client.get("/api/agent-execution/agent-001/sessions/session-001")

        # 驗證
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert "stats" in data
        # 應該計算出 2 筆 executed (1 Enum + 1 字符串)
        assert data["stats"]["filled"] == 2
        assert data["stats"]["total"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
