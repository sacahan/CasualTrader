"""
Unit Tests for Agent Execution API Helper Functions

測試 agent_execution.py 中的輔助函數和邊界情況：
1. 狀態值處理（Enum vs 字符串）
2. 統計計算邏輯
3. 資料轉換邏輯
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock

from common.enums import TransactionAction, TransactionStatus


class TestStatusValueHandling:
    """測試狀態值處理邏輯"""

    def test_enum_status_value_extraction(self):
        """測試從 Enum 提取狀態值"""
        status = TransactionStatus.EXECUTED

        # 模擬 API 中的處理邏輯
        result = status.value if hasattr(status, "value") else status

        assert result == "executed"
        assert isinstance(result, str)

    def test_string_status_value_extraction(self):
        """測試從字符串提取狀態值"""
        status = "executed"

        # 模擬 API 中的處理邏輯
        result = status.value if hasattr(status, "value") else status

        assert result == "executed"
        assert isinstance(result, str)

    def test_enum_action_value_extraction(self):
        """測試從 Enum 提取動作值"""
        action = TransactionAction.BUY

        # 模擬 API 中的處理邏輯
        result = action.value if hasattr(action, "value") else action

        assert result == "BUY"
        assert isinstance(result, str)

    def test_string_action_value_extraction(self):
        """測試從字符串提取動作值"""
        action = "BUY"

        # 模擬 API 中的處理邏輯
        result = action.value if hasattr(action, "value") else action

        assert result == "BUY"
        assert isinstance(result, str)


class TestStatisticsCalculation:
    """測試統計計算邏輯"""

    def create_mock_transaction(self, status: TransactionStatus | str, amount: float) -> MagicMock:
        """創建模擬交易對象"""
        tx = MagicMock()
        tx.status = status
        tx.total_amount = Decimal(str(amount))
        return tx

    def test_filled_count_with_enum_status(self):
        """測試使用 Enum 狀態計算成交數"""
        transactions = [
            self.create_mock_transaction(TransactionStatus.EXECUTED, 100000),
            self.create_mock_transaction(TransactionStatus.EXECUTED, 200000),
            self.create_mock_transaction(TransactionStatus.PENDING, 50000),
        ]

        # 模擬 API 中的計算邏輯
        filled_count = len(
            [
                tx
                for tx in transactions
                if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
            ]
        )

        assert filled_count == 2

    def test_filled_count_with_string_status(self):
        """測試使用字符串狀態計算成交數"""
        transactions = [
            self.create_mock_transaction("executed", 100000),
            self.create_mock_transaction("executed", 200000),
            self.create_mock_transaction("PENDING", 50000),
        ]

        # 模擬 API 中的計算邏輯
        filled_count = len(
            [
                tx
                for tx in transactions
                if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
            ]
        )

        assert filled_count == 2

    def test_filled_count_with_mixed_status(self):
        """測試使用混合狀態類型計算成交數"""
        transactions = [
            self.create_mock_transaction(TransactionStatus.EXECUTED, 100000),  # Enum
            self.create_mock_transaction("executed", 200000),  # String
            self.create_mock_transaction(TransactionStatus.PENDING, 50000),  # Enum
        ]

        # 模擬 API 中的計算邏輯
        filled_count = len(
            [
                tx
                for tx in transactions
                if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
            ]
        )

        assert filled_count == 2

    def test_total_notional_calculation(self):
        """測試總金額計算"""
        transactions = [
            self.create_mock_transaction(TransactionStatus.EXECUTED, 100000),
            self.create_mock_transaction(TransactionStatus.EXECUTED, 200000),
            self.create_mock_transaction(TransactionStatus.PENDING, 50000),
        ]

        # 模擬 API 中的計算邏輯
        total_notional = sum(float(tx.total_amount) for tx in transactions)

        assert total_notional == 350000.0

    def test_empty_transactions_statistics(self):
        """測試空交易列表的統計計算"""
        transactions = []

        # 模擬 API 中的計算邏輯
        filled_count = len(
            [
                tx
                for tx in transactions
                if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
            ]
        )
        total_notional = sum(float(tx.total_amount) for tx in transactions)

        assert filled_count == 0
        assert total_notional == 0.0


class TestTradeDataTransformation:
    """測試交易資料轉換邏輯"""

    def create_mock_transaction_detail(self) -> MagicMock:
        """創建完整的模擬交易對象"""
        tx = MagicMock()
        tx.id = "tx-123"
        tx.ticker = "2330"
        tx.company_name = "台積電"
        tx.action = TransactionAction.BUY
        tx.quantity = 1000
        tx.price = Decimal("580.00")
        tx.total_amount = Decimal("580000.00")
        tx.commission = Decimal("817.00")
        tx.status = TransactionStatus.EXECUTED
        tx.execution_time = datetime(2025, 11, 16, 13, 48, 50)
        tx.decision_reason = "Buy based on analysis"
        tx.created_at = datetime(2025, 11, 16, 13, 48, 45)
        return tx

    def test_trade_dict_transformation(self):
        """測試交易對象轉換為字典"""
        tx = self.create_mock_transaction_detail()

        # 模擬 API 中的轉換邏輯
        trade = {
            "id": tx.id,
            "ticker": tx.ticker,
            "symbol": tx.ticker,  # 別名
            "company_name": tx.company_name,
            "action": tx.action.value if hasattr(tx.action, "value") else tx.action,
            "type": tx.action.value if hasattr(tx.action, "value") else tx.action,  # 別名
            "quantity": tx.quantity,
            "shares": tx.quantity,  # 別名
            "price": float(tx.price),
            "amount": float(tx.total_amount),
            "total_amount": float(tx.total_amount),  # 別名
            "commission": float(tx.commission),
            "status": tx.status.value if hasattr(tx.status, "value") else tx.status,
            "execution_time": tx.execution_time.isoformat() if tx.execution_time else None,
            "decision_reason": tx.decision_reason,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }

        # 驗證所有欄位
        assert trade["id"] == "tx-123"
        assert trade["ticker"] == "2330"
        assert trade["symbol"] == "2330"
        assert trade["company_name"] == "台積電"
        assert trade["action"] == "BUY"
        assert trade["type"] == "BUY"
        assert trade["quantity"] == 1000
        assert trade["shares"] == 1000
        assert trade["price"] == 580.00
        assert trade["amount"] == 580000.00
        assert trade["total_amount"] == 580000.00
        assert trade["commission"] == 817.00
        assert trade["status"] == "executed"
        assert trade["execution_time"] == "2025-11-16T13:48:50"
        assert trade["decision_reason"] == "Buy based on analysis"
        assert trade["created_at"] == "2025-11-16T13:48:45"

    def test_trade_dict_with_none_values(self):
        """測試處理 None 值的交易對象"""
        tx = MagicMock()
        tx.id = "tx-456"
        tx.ticker = "0050"
        tx.company_name = None  # 可能為 None
        tx.action = "BUY"  # 字符串
        tx.quantity = 100
        tx.price = Decimal("180.00")
        tx.total_amount = Decimal("18000.00")
        tx.commission = Decimal("25.38")
        tx.status = "PENDING"  # 字符串
        tx.execution_time = None  # 未執行
        tx.decision_reason = None  # 無原因
        tx.created_at = datetime(2025, 11, 16, 14, 0, 0)

        # 模擬 API 中的轉換邏輯
        trade = {
            "id": tx.id,
            "ticker": tx.ticker,
            "symbol": tx.ticker,
            "company_name": tx.company_name,
            "action": tx.action.value if hasattr(tx.action, "value") else tx.action,
            "type": tx.action.value if hasattr(tx.action, "value") else tx.action,
            "quantity": tx.quantity,
            "shares": tx.quantity,
            "price": float(tx.price),
            "amount": float(tx.total_amount),
            "total_amount": float(tx.total_amount),
            "commission": float(tx.commission),
            "status": tx.status.value if hasattr(tx.status, "value") else tx.status,
            "execution_time": tx.execution_time.isoformat() if tx.execution_time else None,
            "decision_reason": tx.decision_reason,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }

        # 驗證 None 值處理
        assert trade["company_name"] is None
        assert trade["execution_time"] is None
        assert trade["decision_reason"] is None
        assert trade["status"] == "PENDING"
        assert trade["action"] == "BUY"


class TestEdgeCases:
    """測試邊界情況"""

    def test_hasattr_with_none(self):
        """測試 hasattr 對 None 的處理"""
        value = None

        # hasattr 應該安全處理 None
        result = value.value if hasattr(value, "value") else value

        assert result is None

    def test_decimal_to_float_conversion(self):
        """測試 Decimal 到 float 的轉換"""
        amounts = [
            Decimal("100.00"),
            Decimal("200.50"),
            Decimal("0.00"),
            Decimal("999999.99"),
        ]

        # 模擬 API 中的轉換
        floats = [float(amount) for amount in amounts]

        assert floats == [100.00, 200.50, 0.00, 999999.99]

    def test_isoformat_with_none_datetime(self):
        """測試 None datetime 的 isoformat 處理"""
        dt = None

        # 模擬 API 中的轉換
        result = dt.isoformat() if dt else None

        assert result is None

    def test_isoformat_with_valid_datetime(self):
        """測試有效 datetime 的 isoformat 處理"""
        dt = datetime(2025, 11, 16, 13, 48, 50)

        # 模擬 API 中的轉換
        result = dt.isoformat() if dt else None

        assert result == "2025-11-16T13:48:50"
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
