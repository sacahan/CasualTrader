"""
簡化的 TC-001 修復驗證測試
直接使用 SQL 查詢驗證資料庫記錄
"""

import sqlite3
import sys

DB_PATH = "./casualtrader.db"


def test_database_has_agent_records():
    """測試資料庫中是否有 Agent 記錄"""

    print("=" * 80)
    print("🧪 TC-001 資料庫記錄驗證測試")
    print("=" * 80)

    try:
        # 連接資料庫
        print(f"\n📦 連接資料庫：{DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 查詢 agents 表結構
        print("\n📊 查詢 agents 表結構...")
        cursor.execute("PRAGMA table_info(agents)")
        columns = cursor.fetchall()
        print(f"✅ agents 表有 {len(columns)} 個欄位")

        # 查詢現有 Agent 數量
        print("\n📊 查詢現有 Agent...")
        cursor.execute("SELECT COUNT(*) FROM agents")
        count = cursor.fetchone()[0]
        print(f"✅ 資料庫中有 {count} 個 Agent")

        # 如果有 Agent，顯示最近的 5 個
        if count > 0:
            cursor.execute("""
                SELECT id, name, model, status, initial_funds, created_at, updated_at
                FROM agents
                ORDER BY created_at DESC
                LIMIT 5
            """)
            agents = cursor.fetchall()

            print(f"\n📋 最近創建的 {len(agents)} 個 Agent:")
            print("-" * 80)
            for agent in agents:
                agent_id, name, model, status, initial_funds, created_at, updated_at = agent
                print(f"  ID: {agent_id}")
                print(f"  Name: {name}")
                print(f"  Model: {model}")
                print(f"  Status: {status}")
                print(f"  Initial Funds: {initial_funds:,.2f}")
                print(f"  Created At: {created_at}")
                print(f"  Updated At: {updated_at}")
                print("-" * 80)

        conn.close()

        print("\n" + "=" * 80)
        if count > 0:
            print("✅ 測試通過：資料庫中有 Agent 記錄")
            print(f"   共有 {count} 個 Agent")
        else:
            print("⚠️ 測試結果：資料庫中沒有 Agent 記錄")
            print("   請先透過 API 創建 Agent，然後重新執行此測試")
        print("=" * 80)

        return count > 0

    except sqlite3.Error as e:
        print(f"\n❌ 資料庫錯誤：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 測試錯誤：{e}")
        import traceback

        traceback.print_exc()
        return False


def test_specific_agent_by_name(agent_name: str):
    """根據名稱查詢特定 Agent"""

    print(f"\n🔍 查詢 Agent: {agent_name}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, model, status, initial_funds, max_position_size,
                   instructions, created_at, updated_at, last_active_at
            FROM agents
            WHERE name LIKE ?
            ORDER BY created_at DESC
            LIMIT 1
        """,
            (f"%{agent_name}%",),
        )

        agent = cursor.fetchone()

        if agent:
            print("✅ 找到 Agent:")
            print(f"   ID: {agent[0]}")
            print(f"   Name: {agent[1]}")
            print(f"   Model: {agent[2]}")
            print(f"   Status: {agent[3]}")
            print(f"   Initial Funds: {agent[4]:,.2f}")
            print(f"   Max Position Size: {agent[5]}%")
            print(f"   Instructions: {agent[6][:100]}...")
            print(f"   Created At: {agent[7]}")
            print(f"   Updated At: {agent[8]}")
            print(f"   Last Active At: {agent[9]}")
            conn.close()
            return True
        else:
            print(f"❌ 未找到名稱包含 '{agent_name}' 的 Agent")
            conn.close()
            return False

    except Exception as e:
        print(f"❌ 查詢錯誤：{e}")
        return False


def main():
    """主函數"""
    print("\n" + "🚀 開始測試".center(80, "="))

    # 測試 1: 檢查資料庫中的 Agent 記錄
    has_agents = test_database_has_agent_records()

    # 測試 2: 如果需要，可以查詢特定 Agent
    # 例如：test_specific_agent_by_name("巴菲特")

    print("\n" + "🏁 測試完成".center(80, "=") + "\n")

    # 返回結果
    sys.exit(0 if has_agents else 1)


if __name__ == "__main__":
    main()
