#!/usr/bin/env python
"""
驗證工具定義是否對 agents 框架有效

這個測試確認了所有改進的工具都能被 agents 框架成功加載
"""

import sys
import asyncio
from pathlib import Path

# 添加src到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from trading.tools.fundamental_agent import get_fundamental_agent
from trading.tools.risk_agent import get_risk_agent
from trading.tools.sentiment_agent import get_sentiment_agent
from trading.tools.technical_agent import get_technical_agent


async def main():
    """驗證所有 Agent 都能成功初始化"""
    print("\n🔍 驗證工具定義對 agents 框架的有效性\n")

    tests_passed = 0
    tests_total = 4

    # 測試 1: 基本面代理
    try:
        print("1️⃣  初始化 Fundamental Agent...")
        fundamental = await get_fundamental_agent()
        print("   ✓ Fundamental Agent 已成功初始化和載入")
        if fundamental and hasattr(fundamental, "tools"):
            print(f"   ✓ 已加載 {len(fundamental.tools)} 個工具")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Fundamental Agent 初始化失敗: {e}")

    # 測試 2: 風險代理
    try:
        print("\n2️⃣  初始化 Risk Agent...")
        risk = await get_risk_agent()
        print("   ✓ Risk Agent 已成功初始化和載入")
        if risk and hasattr(risk, "tools"):
            print(f"   ✓ 已加載 {len(risk.tools)} 個工具")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Risk Agent 初始化失敗: {e}")

    # 測試 3: 情感代理
    try:
        print("\n3️⃣  初始化 Sentiment Agent...")
        sentiment = await get_sentiment_agent()
        print("   ✓ Sentiment Agent 已成功初始化和載入")
        if sentiment and hasattr(sentiment, "tools"):
            print(f"   ✓ 已加載 {len(sentiment.tools)} 個工具")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Sentiment Agent 初始化失敗: {e}")

    # 測試 4: 技術面代理
    try:
        print("\n4️⃣  初始化 Technical Agent...")
        technical = await get_technical_agent()
        print("   ✓ Technical Agent 已成功初始化和載入")
        if technical and hasattr(technical, "tools"):
            print(f"   ✓ 已加載 {len(technical.tools)} 個工具")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Technical Agent 初始化失敗: {e}")

    # 總結
    print("\n" + "=" * 60)
    print(f"📊 測試結果: {tests_passed}/{tests_total} 通過")
    print("=" * 60)

    if tests_passed == tests_total:
        print("\n✅ 所有工具定義都有效！")
        print("\n這表示:")
        print("  • 所有 @function_tool 裝飾器都已正確配置")
        print("  • strict_mode=False 使工具避免了 JSON schema 驗證失敗")
        print("  • 移除 Pydantic 嵌套模型避免了 additionalProperties 問題")
        print("  • 所有 4 個 Agent 都能成功創建並加載其工具")
        return 0
    else:
        print(f"\n❌ {tests_total - tests_passed} 個 Agent 初始化失敗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
