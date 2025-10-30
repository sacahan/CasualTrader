"""
Contract Test: TransactionStatus 有效值驗證

驗證 TransactionStatus Enum 包含正確的值，
防止使用無效的值如 "COMPLETED"
"""

from src.common.enums import TransactionStatus


def test_transaction_status_valid_values():
    """驗證 TransactionStatus 有效值"""
    valid_values = {status.value for status in TransactionStatus}

    # ✅ 應該存在的值
    assert "executed" in valid_values, "TransactionStatus 應包含 'executed'"
    assert "pending" in valid_values, "TransactionStatus 應包含 'pending'"
    assert "failed" in valid_values, "TransactionStatus 應包含 'failed'"
    assert "cancelled" in valid_values, "TransactionStatus 應包含 'cancelled'"


def test_transaction_status_invalid_values():
    """驗證 TransactionStatus 不包含無效值"""
    valid_values = {status.value for status in TransactionStatus}

    # ❌ 不應該存在的值
    assert "COMPLETED" not in valid_values, "COMPLETED 不是有效的 TransactionStatus"
    assert "completed" not in valid_values, "completed 不是有效的 TransactionStatus"
    assert "EXECUTED" not in valid_values, "EXECUTED (大寫) 不是有效的，應為 executed"


def test_transaction_status_enum_members():
    """驗證 TransactionStatus 的所有成員"""
    members = {member.name for member in TransactionStatus}

    # 應該有的成員
    assert "EXECUTED" in members
    assert "PENDING" in members
    assert "FAILED" in members
    assert "CANCELLED" in members


def test_transaction_status_executed_exists():
    """驗證 TransactionStatus.EXECUTED 存在且有正確的值"""
    assert hasattr(TransactionStatus, "EXECUTED"), "TransactionStatus 應有 EXECUTED 屬性"
    assert TransactionStatus.EXECUTED.value == "executed"


def test_transaction_status_no_completed():
    """驗證 TransactionStatus 沒有 COMPLETED 屬性"""
    assert not hasattr(
        TransactionStatus, "COMPLETED"
    ), "TransactionStatus 不應有 COMPLETED 屬性（應使用 EXECUTED）"


def test_transaction_status_value_case_sensitive():
    """驗證 TransactionStatus 值大小寫"""
    # 所有值都應該是小寫
    for status in TransactionStatus:
        assert status.value == status.value.lower(), f"{status.name} 的值應為小寫"


def test_transaction_status_all_values_unique():
    """驗證所有 TransactionStatus 值唯一"""
    values = [status.value for status in TransactionStatus]
    assert len(values) == len(set(values)), "所有 TransactionStatus 值應唯一"
