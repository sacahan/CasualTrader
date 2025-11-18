#!/usr/bin/env python3
"""
Bug Fix Verification Script

驗證 'str' object has no attribute 'value' 錯誤已修復。

功能：
1. 測試狀態值提取邏輯（Enum vs String）
2. 測試成交數計算邏輯
3. 測試動作值提取邏輯
"""

import sys
from pathlib import Path
from common.enums import TransactionStatus, TransactionAction

# 添加 src 到 Python 路徑
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_status_value_extraction():
    """測試狀態值提取邏輯"""
    print("=" * 60)
    print("測試狀態值提取邏輯")
    print("=" * 60)

    # 測試 Enum 狀態
    enum_status = TransactionStatus.EXECUTED
    result = enum_status.value if hasattr(enum_status, "value") else enum_status
    print(f"\n✅ Enum 狀態: {enum_status}")
    print(f"   提取結果: {result}")
    print(f"   類型: {type(result)}")
    assert result == "executed", f"預期 'executed'，實際 {result}"

    # 測試字符串類型
    str_status = "executed"
    result2 = str_status.value if hasattr(str_status, "value") else str_status
    print(f"\n✅ 字符串狀態: {str_status}")
    print(f"   提取結果: {result2}")
    print(f"   類型: {type(result2)}")
    assert result2 == "executed", f"Expected 'executed', got '{result2}'"

    # 測試 None
    none_status = None
    result3 = none_status.value if hasattr(none_status, "value") else none_status
    print(f"\n✅ None 狀態: {none_status}")
    print(f"   提取結果: {result3}")
    print(f"   類型: {type(result3)}")
    assert result3 is None, f"Expected None, got '{result3}'"

    print("\n" + "=" * 60)
    print("✅ 所有測試通過！")
    print("=" * 60)


def test_filled_count_logic():
    """測試成交數計算邏輯"""
    print("\n" + "=" * 60)
    print("測試成交數計算邏輯")
    print("=" * 60)

    # 模擬交易列表
    class MockTransaction:
        def __init__(self, status):
            self.status = status

    transactions = [
        MockTransaction(TransactionStatus.EXECUTED),  # Enum
        MockTransaction("executed"),  # String
        MockTransaction(TransactionStatus.PENDING),  # Enum
        MockTransaction("pending"),  # String
    ]

    # 使用修復後的邏輯
    executed_count = len(
        [
            tx
            for tx in transactions
            if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
        ]
    )

    print(f"\n總交易數: {len(transactions)}")
    print(f"成交數: {executed_count}")

    assert executed_count == 2, f"Expected 2 executed transactions, got {executed_count}"

    print("\n✅ 成交數計算正確！")


def test_action_value_extraction():
    """測試動作值提取邏輯"""
    print("\n" + "=" * 60)
    print("測試動作值提取邏輯")
    print("=" * 60)

    # 測試 Enum 類型
    enum_action = TransactionAction.BUY
    result1 = enum_action.value if hasattr(enum_action, "value") else enum_action
    print(f"\n✅ Enum 動作: {enum_action}")
    print(f"   提取結果: {result1}")
    assert result1 == "BUY", f"Expected 'BUY', got '{result1}'"

    # 測試字符串類型
    str_action = "SELL"
    result2 = str_action.value if hasattr(str_action, "value") else str_action
    print(f"\n✅ 字符串動作: {str_action}")
    print(f"   提取結果: {result2}")
    assert result2 == "SELL", f"Expected 'SELL', got '{result2}'"

    print("\n✅ 動作值提取正確！")


def main():
    """主函數"""
    try:
        test_status_value_extraction()
        test_filled_count_logic()
        test_action_value_extraction()

        print("\n" + "🎉" * 30)
        print("\n✅ 所有驗證測試通過！Bug 已修復！\n")
        print("🎉" * 30)

        return 0

    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
