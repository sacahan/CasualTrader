#!/usr/bin/env python
"""
簡單的語法和結構驗證腳本
不需要導入模組，只檢查程式碼結構
"""

import ast
from pathlib import Path


def check_trading_agent():
    """檢查 TradingAgent 的修改"""
    print("🔍 檢查 TradingAgent...")

    file_path = Path("src/agents/trading/trading_agent.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析 AST
    tree = ast.parse(content)

    # 找到 TradingAgent 類
    trading_agent_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "TradingAgent":
            trading_agent_class = node
            break

    assert trading_agent_class is not None, "找不到 TradingAgent 類"

    # 收集所有方法名
    method_names = [
        n.name
        for n in trading_agent_class.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    # 檢查已刪除的方法
    assert "auto_mode_selection" not in method_names, "❌ auto_mode_selection 方法應該已被移除"
    assert (
        "execute_with_auto_mode" not in method_names
    ), "❌ execute_with_auto_mode 方法應該已被移除"

    # 檢查應該保留的方法
    assert "get_strategy_changes" in method_names, "❌ get_strategy_changes 方法應該保留"
    assert "record_strategy_change" in method_names, "❌ record_strategy_change 方法應該保留"

    print(f"✅ TradingAgent 有 {len(method_names)} 個方法")
    print("✅ 已確認移除 auto_mode_selection 和 execute_with_auto_mode")


def check_agent_manager():
    """檢查 AgentManager 的修改"""
    print("\n🔍 檢查 AgentManager...")

    file_path = Path("src/agents/core/agent_manager.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析 AST
    tree = ast.parse(content)

    # 找到 AgentManager 類
    agent_manager_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "AgentManager":
            agent_manager_class = node
            break

    assert agent_manager_class is not None, "找不到 AgentManager 類"

    # 收集所有方法名
    method_names = [
        n.name
        for n in agent_manager_class.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    # 檢查新增的方法
    assert "start_agent" in method_names, "❌ start_agent 方法應該存在"

    # 找到 start_agent 方法並檢查參數
    start_agent_method = None
    for node in agent_manager_class.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "start_agent":
            start_agent_method = node
            break

    assert start_agent_method is not None

    # 檢查參數
    param_names = [arg.arg for arg in start_agent_method.args.args]
    assert "agent_id" in param_names, "❌ 應該有 agent_id 參數"
    assert "max_cycles" in param_names, "❌ 應該有 max_cycles 參數"
    assert "stop_loss_threshold" in param_names, "❌ 應該有 stop_loss_threshold 參數"

    print(f"✅ AgentManager 有 {len(method_names)} 個方法")
    print("✅ 已確認新增 start_agent 方法，包含正確的參數")


def check_test_file():
    """檢查測試檔案的修改"""
    print("\n🔍 檢查測試檔案...")

    file_path = Path("tests/database/test_agent_infrastructure.py")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 檢查是否還有對已刪除方法的引用
    assert "auto_mode_selection" not in content, "❌ 測試檔案不應該再引用 auto_mode_selection"
    assert "execute_with_auto_mode" not in content, "❌ 測試檔案不應該再引用 execute_with_auto_mode"

    print("✅ 測試檔案已正確更新")


def main():
    """主驗證流程"""
    print("=" * 60)
    print("開始驗證程式碼修改...")
    print("=" * 60)

    try:
        check_trading_agent()
        check_agent_manager()
        check_test_file()

        print("\n" + "=" * 60)
        print("🎉 所有驗證通過！")
        print("=" * 60)
        print("\n修改摘要:")
        print("━" * 60)
        print("📝 TradingAgent (trading_agent.py)")
        print("  ❌ 已移除: auto_mode_selection()")
        print("  ❌ 已移除: execute_with_auto_mode()")
        print("  ✅ 保留: record_strategy_change()")
        print("  ✅ 保留: get_strategy_changes()")
        print()
        print("📝 AgentManager (agent_manager.py)")
        print("  ✅ 新增: start_agent(agent_id, max_cycles, stop_loss_threshold)")
        print("     └─ 修復 API 呼叫問題")
        print()
        print("📝 測試檔案 (test_agent_infrastructure.py)")
        print("  ✅ 移除對已刪除方法的測試")
        print("━" * 60)
        print("\n🔧 影響範圍:")
        print("  • API 現在可以正常呼叫 start_agent()")
        print("  • 移除了未使用的自動模式選擇功能")
        print("  • 簡化了程式碼結構，降低維護成本")

        return 0

    except AssertionError as e:
        print(f"\n❌ 驗證失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys

    exit_code = main()
    sys.exit(exit_code)
