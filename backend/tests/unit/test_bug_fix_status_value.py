"""
Direct Test for Agent Execution Bug Fix - Core Logic

測試目標:
1. 直接測試狀態值提取邏輯
2. 驗證 filled_count 計算邏輯
3. 不依賴 FastAPI 或資料庫

這是最小化的單元測試，專注於 bug 修復的核心邏輯。
"""

import pytest
from common.enums import TransactionStatus, TransactionAction


class TestStatusValueExtraction:
    """測試狀態值提取邏輯 - Bug 修復核心"""

    def test_enum_status_extraction(self):
        """測試 Enum 狀態值提取"""
        status = TransactionStatus.EXECUTED
        result = status.value if hasattr(status, "value") else status
        assert result == "executed"
        assert isinstance(result, str)

    def test_string_status_extraction(self):
        """測試字符串狀態值提取"""
        status = "executed"
        result = status.value if hasattr(status, "value") else status
        assert result == "executed"
        assert isinstance(result, str)

    def test_none_status_extraction(self):
        """測試 None 狀態值提取"""
        status = None
        result = status.value if hasattr(status, "value") else status
        assert result is None

    def test_filled_count_with_enum_status(self):
        """測試成交數計算 - Enum 狀態"""

        class MockTransaction:
            def __init__(self, status):
                self.status = status

        transactions = [
            MockTransaction(TransactionStatus.EXECUTED),
            MockTransaction(TransactionStatus.EXECUTED),
            MockTransaction(TransactionStatus.PENDING),
            MockTransaction(TransactionStatus.FAILED),
        ]

        # 使用修復後的邏輯
        filled_count = len(
            [
                tx
                for tx in transactions
                if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
            ]
        )

        assert filled_count == 2

    def test_filled_count_with_string_status(self):
        """測試成交數計算 - 字符串狀態"""

        class MockTransaction:
            def __init__(self, status):
                self.status = status

        transactions = [
            MockTransaction("executed"),
            MockTransaction("executed"),
            MockTransaction("pending"),
            MockTransaction("failed"),
        ]

        # 使用修復後的邏輯
        filled_count = len(
            [
                tx
                for tx in transactions
                if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
            ]
        )

        assert filled_count == 2

    def test_filled_count_with_mixed_status(self):
        """測試成交數計算 - 混合狀態類型 (Enum + 字符串)"""

        class MockTransaction:
            def __init__(self, status):
                self.status = status

        transactions = [
            MockTransaction(TransactionStatus.EXECUTED),  # Enum
            MockTransaction("executed"),  # String
            MockTransaction(TransactionStatus.PENDING),  # Enum
            MockTransaction("pending"),  # String
            MockTransaction(None),  # None
        ]

        # 使用修復後的邏輯（這就是 bug 修復的核心）
        filled_count = len(
            [
                tx
                for tx in transactions
                if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
            ]
        )

        # 應該計算出 2 筆 (1 Enum + 1 String)
        assert filled_count == 2

    def test_action_value_extraction(self):
        """測試動作值提取 - 確保適用於所有 Enum 類型"""
        # Enum 類型
        action_enum = TransactionAction.BUY
        result1 = action_enum.value if hasattr(action_enum, "value") else action_enum
        assert result1 == "BUY"

        # 字符串類型
        action_str = "SELL"
        result2 = action_str.value if hasattr(action_str, "value") else action_str
        assert result2 == "SELL"

    def test_total_notional_calculation(self):
        """測試總金額計算"""

        class MockTransaction:
            def __init__(self, status, total_amount):
                self.status = status
                self.total_amount = total_amount

        transactions = [
            MockTransaction(TransactionStatus.EXECUTED, 100000),
            MockTransaction("executed", 200000),
            MockTransaction(TransactionStatus.PENDING, 300000),
        ]

        # 計算總金額
        total_notional = sum(float(tx.total_amount) for tx in transactions)
        assert total_notional == 600000


class TestBugScenario:
    """模擬原始 bug 情境"""

    def test_original_bug_would_fail(self):
        """
        驗證原始 bug 會導致錯誤

        原始代碼:
        if tx.status.value == "executed"

        當 tx.status 是字符串時會拋出:
        AttributeError: 'str' object has no attribute 'value'
        """

        class MockTransaction:
            def __init__(self, status):
                self.status = status

        tx = MockTransaction("executed")

        # 原始（有 bug）的方式會失敗
        with pytest.raises(AttributeError):
            _ = tx.status.value  # 'str' object has no attribute 'value'

    def test_fixed_version_works(self):
        """
        驗證修復後的版本正常工作

        修復代碼:
        tx.status.value if hasattr(tx.status, "value") else tx.status
        """

        class MockTransaction:
            def __init__(self, status):
                self.status = status

        # 測試字符串
        tx_str = MockTransaction("executed")
        result = tx_str.status.value if hasattr(tx_str.status, "value") else tx_str.status
        assert result == "executed"

        # 測試 Enum
        tx_enum = MockTransaction(TransactionStatus.EXECUTED)
        result = tx_enum.status.value if hasattr(tx_enum.status, "value") else tx_enum.status
        assert result == "executed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
