#!/usr/bin/env python3
"""
完整重建 agent_holdings 表的腳本
清空後根據 transactions 表重新計算每個 agent 的持股
"""

import asyncio
from decimal import Decimal
from datetime import datetime, UTC

import asyncpg


DATABASE_URL = "postgresql://cstrader_user:2Ts9zM2%@sacahan-ubunto:5432/cstrader"


async def get_connection():
    """建立資料庫連線"""
    return await asyncpg.connect(DATABASE_URL)


async def rebuild_holdings(conn):
    """完整重建 agent_holdings 表"""

    print("🔍 開始完整重建 agent_holdings 表...\n")

    # 1. 清空 agent_holdings 表
    print("🧹 清空 agent_holdings 表...")
    await conn.execute("DELETE FROM agent_holdings")
    print("✅ 已清空\n")

    # 2. 從 transactions 計算每個 agent 的持股
    print("📊 從 transactions 計算持股...\n")

    holdings = await conn.fetch("""
        SELECT
            agent_id,
            ticker,
            MAX(company_name) as company_name,
            SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) as net_quantity,
            SUM(CASE WHEN action = 'BUY' THEN total_amount ELSE 0 END) as total_buy_cost,
            SUM(CASE WHEN action = 'BUY' THEN quantity ELSE 0 END) as total_buy_qty
        FROM transactions
        WHERE LOWER(status) = 'executed'
        GROUP BY agent_id, ticker
        HAVING SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) > 0
        ORDER BY agent_id, ticker
    """)

    print(f"找到 {len(holdings)} 個持股記錄需要建立\n")

    # 3. 取得 agent 名稱對照
    agents = await conn.fetch("SELECT id, name FROM agents")
    agent_names = {a["id"]: a["name"] for a in agents}

    # 4. 插入新記錄
    now = datetime.now(UTC)
    current_agent = None

    for h in holdings:
        agent_id = h["agent_id"]
        ticker = h["ticker"]
        company_name = h["company_name"]
        net_quantity = int(h["net_quantity"])
        total_buy_cost = float(h["total_buy_cost"]) if h["total_buy_cost"] else 0
        total_buy_qty = int(h["total_buy_qty"]) if h["total_buy_qty"] else 0

        # 計算平均成本（使用總買入成本 / 總買入數量）
        avg_cost = total_buy_cost / total_buy_qty if total_buy_qty > 0 else 0

        # 計算當前持股的總成本
        total_cost = avg_cost * net_quantity

        if agent_id != current_agent:
            current_agent = agent_id
            print(f"  📊 {agent_names.get(agent_id, agent_id)}:")

        await conn.execute(
            """
            INSERT INTO agent_holdings (
                agent_id, ticker, company_name, quantity,
                average_cost, total_cost,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
            agent_id,
            ticker,
            company_name,
            net_quantity,
            Decimal(str(round(avg_cost, 2))),
            Decimal(str(round(total_cost, 2))),
            now,
            now,
        )

        print(f"      ✓ {ticker}: {net_quantity} 股 @ 平均成本 {avg_cost:.2f}")

    print(f"\n✅ 已建立 {len(holdings)} 個持股記錄")


async def verify_holdings(conn):
    """驗證結果"""

    print("\n🔍 驗證結果...\n")

    # 取得 agent 名稱對照
    agents = await conn.fetch("SELECT id, name FROM agents")
    agent_names = {a["id"]: a["name"] for a in agents}

    # 從 transactions 計算預期
    expected = await conn.fetch("""
        SELECT
            agent_id,
            ticker,
            SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) as expected_qty
        FROM transactions
        WHERE LOWER(status) = 'executed'
        GROUP BY agent_id, ticker
        HAVING SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) > 0
        ORDER BY agent_id, ticker
    """)

    expected_dict = {}
    for r in expected:
        agent_id = r["agent_id"]
        if agent_id not in expected_dict:
            expected_dict[agent_id] = {}
        expected_dict[agent_id][r["ticker"]] = int(r["expected_qty"])

    # 取得實際 holdings
    actual = await conn.fetch("""
        SELECT agent_id, ticker, quantity
        FROM agent_holdings
        ORDER BY agent_id, ticker
    """)

    actual_dict = {}
    for r in actual:
        agent_id = r["agent_id"]
        if agent_id not in actual_dict:
            actual_dict[agent_id] = {}
        actual_dict[agent_id][r["ticker"]] = r["quantity"]

    # 比對
    all_correct = True
    for agent_id in set(expected_dict.keys()) | set(actual_dict.keys()):
        exp = expected_dict.get(agent_id, {})
        act = actual_dict.get(agent_id, {})

        if exp == act:
            print(f"✅ {agent_names.get(agent_id, agent_id)}: 所有持股正確")
            for ticker, qty in sorted(act.items()):
                print(f"      {ticker}: {qty} 股")
        else:
            print(f"❌ {agent_names.get(agent_id, agent_id)}: 不一致")
            print(f"   預期: {exp}")
            print(f"   實際: {act}")
            all_correct = False
        print()

    return all_correct


async def main():
    """主函數"""
    conn = await get_connection()

    try:
        print("=" * 60)
        print("🚀 開始完整重建 agent_holdings 表")
        print("=" * 60)
        print()

        # 重建
        await rebuild_holdings(conn)

        # 驗證
        all_correct = await verify_holdings(conn)

        if all_correct:
            print("✅ 所有重建已完成並驗證成功！")
        else:
            print("⚠️ 仍有不一致項目，請手動檢查")

    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
