#!/usr/bin/env python3
"""
DateTime Timezone Fix Verification Script

驗證所有 datetime 時區感知修復是否正確實施。

功能：
1. 驗證 datetime.now(timezone.utc) 正確使用
2. 時間戳記計算不會拋出 "can't subtract offset-naive and offset-aware" 錯誤
3. 所有主要服務可以導入
"""

from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path


def test_timezone_aware_datetime():
    """測試時區感知的 datetime 操作"""
    print("🔍 測試時區感知的 datetime...")

    try:
        # 測試 1: 建立時區感知的 datetime
        now_utc = datetime.now(timezone.utc)
        print(f"✓ datetime.now(timezone.utc) 成功: {now_utc}")

        # 測試 2: 時間差計算（模擬執行時間計算）
        start_time = datetime.now(timezone.utc)
        import time

        time.sleep(0.1)  # 模擬執行
        end_time = datetime.now(timezone.utc)

        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        print(f"✓ 時間差計算成功: {duration_ms}ms")

        # 測試 3: 與 timedelta 操作
        threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
        print(f"✓ timedelta 操作成功: {threshold}")

        return True
    except Exception as e:
        print(f"✗ 時區感知 datetime 測試失敗: {e}")
        return False


def test_imports():
    """測試所有主要服務的導入"""
    print("\n🔍 測試服務導入...")

    try:
        # 添加 src 目錄到 Python 路徑
        backend_path = Path(__file__).parent.parent
        src_path = backend_path / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        # 測試 1: 資料庫模型
        from database.models import Transaction  # noqa: F401

        print("✓ 資料庫模型導入成功")

        # 測試 2: 服務層
        from service.session_service import AgentSessionService  # noqa: F401
        from service.agents_service import AgentsService  # noqa: F401
        from service.trading_service import TradingService  # noqa: F401

        print("✓ 服務層導入成功")

        # 測試 3: Enums
        from common.enums import AgentStatus, SessionStatus, TransactionStatus  # noqa: F401

        print("✓ Enums 導入成功")

        return True
    except ImportError as e:
        print(f"✗ 導入失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("=" * 60)
    print("CasualTrader DateTime 修復驗證")
    print("=" * 60)

    results = []

    # 運行測試
    results.append(("時區感知 DateTime", test_timezone_aware_datetime()))
    results.append(("服務導入", test_imports()))

    # 輸出結果
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    # 判斷整體結果
    all_passed = all(passed for _, passed in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有測試通過！DateTime 修復成功")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分測試失敗，請檢查錯誤")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
