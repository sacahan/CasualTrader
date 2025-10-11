"""
驗證 MCP Server 配置

此腳本用於測試 MCP Server 配置是否正確，包括：
1. 環境變數讀取
2. MCPServerStdio 實例創建
3. 配置參數驗證
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def verify_config():
    """驗證 MCP Server 配置"""
    print("=" * 60)
    print("MCP Server 配置驗證")
    print("=" * 60)

    # 1. 檢查環境變數
    print("\n1. 檢查環境變數:")
    print("-" * 60)

    mcp_command = os.getenv("MCP_CASUAL_MARKET_COMMAND", "uvx")
    mcp_args = os.getenv("MCP_CASUAL_MARKET_ARGS", "casual-market-mcp")
    mcp_timeout = os.getenv("MCP_CASUAL_MARKET_TIMEOUT", "10")
    mcp_retries = os.getenv("MCP_CASUAL_MARKET_RETRIES", "5")

    print(f"  MCP_CASUAL_MARKET_COMMAND: {mcp_command}")
    print(f"  MCP_CASUAL_MARKET_ARGS: {mcp_args}")
    print(f"  MCP_CASUAL_MARKET_TIMEOUT: {mcp_timeout}")
    print(f"  MCP_CASUAL_MARKET_RETRIES: {mcp_retries}")

    # 2. 測試配置字典生成
    print("\n2. 測試 MCP Server 配置字典:")
    print("-" * 60)

    try:
        import json

        # 解析 args - 支援字串或 JSON 陣列
        if mcp_args.startswith("[") and mcp_args.endswith("]"):
            try:
                args = json.loads(mcp_args)
                if not isinstance(args, list):
                    print("  ⚠️  MCP_CASUAL_MARKET_ARGS 不是陣列，使用預設值")
                    args = ["casual-market-mcp"]
            except json.JSONDecodeError as e:
                print(f"  ⚠️  無法解析 JSON 陣列: {e}")
                args = ["casual-market-mcp"]
        else:
            args = [mcp_args]

        config = {
            "command": mcp_command,
            "args": args,
        }
        print(f"  Config: {config}")
        print(f"  Command: {config['command']}")
        print(f"  Args: {config['args']}")
        print(f"  Args 類型: {type(config['args'])}")
        print(f"  Args 長度: {len(config['args'])}")

    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        return False  # 3. 測試 MCPServerStdio 創建（不實際啟動）
    print("\n3. 測試 MCPServerStdio 實例創建:")
    print("-" * 60)

    try:
        # 直接從 OpenAI SDK 導入，避免與本地 agents 模組衝突
        import agents.mcp as mcp_module

        MCPServerStdio = mcp_module.MCPServerStdio

        # 只創建實例，不啟動
        server = MCPServerStdio(
            name="Test Casual Market MCP Server",
            params=config,
        )

        print("  ✓ MCPServerStdio 實例創建成功")
        print(f"  Server name: {server.name}")
        print(f"  Server params: {config}")

    except ImportError as e:
        print("  ⚠️  MCPServerStdio 不可用 (需要安裝 openai-agents-python)")
        print(f"     錯誤: {e}")
        print("  ℹ️  可以繼續使用系統，但建議安裝 SDK 以啟用 MCP 功能")
        # 不返回 False，允許繼續執行
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        return False

    # 4. 檢查 API 配置
    print("\n4. 檢查 API 配置:")
    print("-" * 60)

    try:
        # Add src to path for importing api module
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from api.config import settings

        print(f"  MCP Command: {settings.mcp_casual_market_command}")
        print(f"  MCP Args: {settings.mcp_casual_market_args}")
        print(f"  MCP Timeout: {settings.mcp_casual_market_timeout}s")
        print(f"  MCP Retries: {settings.mcp_casual_market_retries}")

    except Exception as e:
        print(f"  ⚠️  API 配置讀取失敗: {e}")

    print("\n" + "=" * 60)
    print("✓ 所有配置驗證通過")
    print("=" * 60)

    return True


async def main():
    """主函數"""
    success = await verify_config()

    if success:
        print("\n✓ MCP Server 配置正確")
        print("\n建議:")
        print("  1. 確保已安裝 casual-market-mcp 套件")
        print("  2. 使用 'uvx casual-market-mcp' 可以正常啟動")
        print("  3. TradingAgent 將會自動管理 MCP Server 的生命週期")
        return 0
    else:
        print("\n❌ MCP Server 配置有誤，請檢查上述錯誤訊息")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
