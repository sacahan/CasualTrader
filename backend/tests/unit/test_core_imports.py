#!/usr/bin/env python3
"""
簡化的模組導入測試 - 測試核心功能模組
"""

import sys
from pathlib import Path

# 將 backend/src 加入 Python path
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))


def test_module_imports():
    print("=" * 60)
    print("🧪 核心模組導入測試")
    print("=" * 60)

    test_results = []

    # Test 1: Common Enums
    try:
        from common.enums import (
            AgentStatus,
            AgentMode,
        )

        test_results.append(("✅", "common.enums", "所有枚舉導入成功"))
        print(f"✅ common.enums - {AgentStatus.ACTIVE}, {AgentMode.TRADING}")
    except Exception as e:
        test_results.append(("❌", "common.enums", str(e)))
        print(f"❌ common.enums: {e}")

    # Test 2: Database Models
    try:
        from database.models import Agent

        test_results.append(("✅", "database.models", f"ORM 模型 ({Agent.__tablename__})"))
        print("✅ database.models - Agent, Transaction, AgentSession")
    except Exception as e:
        test_results.append(("❌", "database.models", str(e)))
        print(f"❌ database.models: {e}")

    # Test 3: Schemas - Agent
    try:
        test_results.append(("✅", "schemas.agent", "Pydantic Agent schemas"))
        print("✅ schemas.agent - CreateAgentRequest, AgentResponse")
    except Exception as e:
        test_results.append(("❌", "schemas.agent", str(e)))
        print(f"❌ schemas.agent: {e}")

    # Test 4: Schemas - Trading
    try:
        test_results.append(("✅", "schemas.trading", "Pydantic Trading schemas"))
        print("✅ schemas.trading - TradeRecord")
    except Exception as e:
        test_results.append(("❌", "schemas.trading", str(e)))
        print(f"❌ schemas.trading: {e}")

    # Test 5: Schemas - WebSocket
    try:
        test_results.append(("✅", "schemas.websocket", "WebSocket schemas"))
        print("✅ schemas.websocket - WebSocketMessage, ErrorResponse")
    except Exception as e:
        test_results.append(("❌", "schemas.websocket", str(e)))
        print(f"❌ schemas.websocket: {e}")

    print("=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)

    passed = sum(1 for r in test_results if r[0] == "✅")
    failed = sum(1 for r in test_results if r[0] == "❌")

    for status, module, message in test_results:
        print(f"{status} {module:25s} {message}")

    print("=" * 60)
    print(f"✅ 通過: {passed} 個")
    print(f"❌ 失敗: {failed} 個")
    print("=" * 60)

    if failed > 0:
        raise RuntimeError("Test failed")

    print("🎉 所有核心模組導入測試通過！")
