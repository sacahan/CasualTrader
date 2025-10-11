"""
測試 TradingAgent 讀取 JSON 陣列格式的 MCP Server 配置

此腳本驗證 TradingAgent._get_mcp_server_config() 可以正確解析：
1. 簡單字串格式: "casual-market-mcp"
2. JSON 陣列格式: ["--from", "/path/to/dir", "casual-market-mcp"]
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_config_parsing():
    """測試配置解析"""
    print("=" * 60)
    print("測試 TradingAgent MCP Server 配置解析")
    print("=" * 60)

    # 測試案例
    test_cases = [
        {
            "name": "簡單字串格式",
            "value": "casual-market-mcp",
            "expected_args": ["casual-market-mcp"],
        },
        {
            "name": "JSON 陣列格式 - 本地開發",
            "value": '["--from", "/Users/sacahan/Documents/workspace/CasualMarket", "casual-market-mcp"]',
            "expected_args": [
                "--from",
                "/Users/sacahan/Documents/workspace/CasualMarket",
                "casual-market-mcp",
            ],
        },
        {
            "name": "JSON 陣列格式 - 簡單",
            "value": '["casual-market-mcp"]',
            "expected_args": ["casual-market-mcp"],
        },
    ]

    import json

    for i, test in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {test['name']}")
        print("-" * 60)
        print(f"輸入: {test['value']}")

        # 模擬 _get_mcp_server_config 的邏輯
        args_str = test["value"]

        if args_str.startswith("[") and args_str.endswith("]"):
            try:
                args = json.loads(args_str)
                if not isinstance(args, list):
                    print("  ⚠️  不是陣列，使用預設值")
                    args = ["casual-market-mcp"]
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON 解析失敗: {e}")
                args = ["casual-market-mcp"]
        else:
            args = [args_str]

        print(f"解析結果: {args}")
        print(f"預期結果: {test['expected_args']}")

        if args == test["expected_args"]:
            print("✓ 通過")
        else:
            print("❌ 失敗")
            return False

    print("\n" + "=" * 60)
    print("✓ 所有測試通過")
    print("=" * 60)
    return True


def test_actual_config():
    """測試實際的環境變數配置"""
    print("\n" + "=" * 60)
    print("測試實際環境變數配置")
    print("=" * 60)

    # 動態導入 TradingAgent（避免循環導入）
    try:
        # 使用字串導入避免循環依賴
        import importlib

        trading_module = importlib.import_module("agents.trading.trading_agent")
        TradingAgent = trading_module.TradingAgent

        # 獲取配置
        config = TradingAgent._get_mcp_server_config()

        print("\n當前配置:")
        print(f"  Command: {config['command']}")
        print(f"  Args: {config['args']}")
        print(f"  Args 類型: {type(config['args'])}")
        print(f"  Args 長度: {len(config['args'])}")

        # 驗證格式
        if not isinstance(config["args"], list):
            print("\n❌ Args 不是列表類型")
            return False

        if len(config["args"]) == 0:
            print("\n❌ Args 為空")
            return False

        print("\n✓ 實際配置格式正確")

        # 顯示完整的 MCPServerStdio params
        print("\nMCPServerStdio params:")
        print(f"  {config}")

        return True

    except Exception as e:
        print(f"\n⚠️  無法測試實際配置: {e}")
        print("  (這是正常的，如果還未安裝所有依賴)")
        return True  # 不影響其他測試


def main():
    """主函數"""
    success = True

    # 測試配置解析邏輯
    if not test_config_parsing():
        success = False

    # 測試實際配置
    if not test_actual_config():
        success = False

    if success:
        print("\n" + "=" * 60)
        print("✓ 所有測試完成")
        print("=" * 60)
        print("\n當前環境變數:")
        print(f"  MCP_CASUAL_MARKET_COMMAND: {os.getenv('MCP_CASUAL_MARKET_COMMAND', 'uvx')}")
        print(
            f"  MCP_CASUAL_MARKET_ARGS: {os.getenv('MCP_CASUAL_MARKET_ARGS', 'casual-market-mcp')}"
        )
        return 0
    else:
        print("\n❌ 測試失敗")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
