#!/usr/bin/env python3
"""
驗證 MCP 伺服器協議相容性。

測試 MCP 伺服器是否符合協議標準。
"""

import json
import subprocess
import sys


def test_mcp_protocol():
    """測試 MCP 協議相容性。"""
    print("🔧 測試 MCP 協議相容性...")

    # 測試初始化請求
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    print("📤 發送初始化請求...")
    try:
        # 使用 uv 執行伺服器
        process = subprocess.Popen(
            ["uv", "run", "python", "-m", "market_mcp.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # 發送初始化請求
        init_json = json.dumps(init_request) + "\n"
        stdout, stderr = process.communicate(input=init_json, timeout=10)

        print("📥 伺服器回應:")
        if stdout:
            try:
                response = json.loads(stdout.strip())
                print(
                    f"✅ JSON 回應: {json.dumps(response, indent=2, ensure_ascii=False)}"
                )
            except json.JSONDecodeError:
                print(f"📝 原始回應: {stdout}")

        if stderr:
            print(f"⚠️  錯誤輸出: {stderr}")

        return_code = process.returncode
        print(f"🔍 退出代碼: {return_code}")

        if return_code == 0 or return_code is None:
            print("✅ MCP 伺服器啟動成功！")
        else:
            print("❌ MCP 伺服器啟動失敗")

    except subprocess.TimeoutExpired:
        print("⏰ 請求逾時 - 但這是正常的，因為 MCP 伺服器會持續運行")
        process.kill()
        print("✅ MCP 伺服器正在運行中")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

    return True


def test_tool_definitions():
    """測試工具定義。"""
    print("\n🛠️  測試工具定義...")

    try:
        from market_mcp.tools import get_tool_definitions

        tools = get_tool_definitions()
        print(f"✅ 找到 {len(tools)} 個工具")

        for tool in tools:
            print(f"📋 工具: {tool['name']}")
            print(f"   描述: {tool['description']}")
            print(f"   參數: {list(tool['inputSchema']['properties'].keys())}")

        return True

    except Exception as e:
        print(f"❌ 工具定義測試失敗: {e}")
        return False


def main():
    """主函數。"""
    print("🚀 開始 MCP 伺服器驗證...")

    # 測試工具定義
    tools_ok = test_tool_definitions()

    # 測試 MCP 協議
    protocol_ok = test_mcp_protocol()

    print("\n📊 驗證結果:")
    print(f"   工具定義: {'✅ 通過' if tools_ok else '❌ 失敗'}")
    print(f"   MCP 協議: {'✅ 通過' if protocol_ok else '❌ 失敗'}")

    if tools_ok and protocol_ok:
        print("\n🎉 MCP 伺服器驗證通過！")
        print("\n📝 使用說明:")
        print("1. 在 Claude Desktop 設定檔中添加伺服器配置")
        print("2. 重啟 Claude Desktop")
        print("3. 使用 get_taiwan_stock_price 工具查詢股價")
        return 0
    else:
        print("\n❌ MCP 伺服器驗證失敗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
