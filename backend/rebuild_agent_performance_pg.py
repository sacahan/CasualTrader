#!/usr/bin/env python3
"""
重建 agent_performance 表的腳本 (PostgreSQL 版本)
1. 為每個 Agent 創建初始記錄（使用 initial_funds）
2. 根據 transactions 和 agent_holdings 逐日重新計算績效
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal

import asyncpg


# PostgreSQL 連線設定
DATABASE_URL = "postgresql://cstrader_user:2Ts9zM2%@sacahan-ubunto:5432/cstrader"


def _to_float(value: float | int | Decimal | None) -> float:
    """Convert possible numeric values to float safely."""
    if value is None:
        return 0.0
    return float(value)


async def get_connection():
    """建立資料庫連線"""
    return await asyncpg.connect(DATABASE_URL)


async def clear_performance_table(conn):
    """清空 agent_performance 表"""
    print("🧹 清空 agent_performance 表...")
    await conn.execute("DELETE FROM agent_performance")
    print("✅ 已清空")


async def get_all_agents(conn):
    """取得所有 Agent"""
    rows = await conn.fetch("SELECT id, name, initial_funds FROM agents ORDER BY created_at")
    return [(row["id"], row["name"], row["initial_funds"]) for row in rows]


async def create_initial_records(conn, agents):
    """為每個 Agent 創建初始績效記錄"""
    print("\n📝 為每個 Agent 創建初始績效記錄...")

    for agent_id, agent_name, initial_funds in agents:
        # 使用第一筆交易日期的前一天作為初始記錄日期
        result = await conn.fetchrow(
            """
            SELECT MIN(DATE(created_at)) as first_trade_date
            FROM transactions
            WHERE agent_id = $1
            """,
            agent_id,
        )

        first_trade_date = result["first_trade_date"] if result else None
        if first_trade_date:
            initial_date = first_trade_date - timedelta(days=1)
        else:
            initial_date = date(2025, 11, 1)

        await conn.execute(
            """
            INSERT INTO agent_performance (
                agent_id, date, total_value, cash_balance, unrealized_pnl,
                realized_pnl, daily_return, total_return, win_rate, max_drawdown,
                total_trades, sell_trades_count, winning_trades_correct,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
            ON CONFLICT (agent_id, date) DO UPDATE SET
                total_value = EXCLUDED.total_value,
                cash_balance = EXCLUDED.cash_balance,
                updated_at = NOW()
            """,
            agent_id,
            initial_date,
            float(initial_funds),
            float(initial_funds),
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0,
            0,
            0,
        )

        print(f"  ✓ {agent_name} ({agent_id}): 初始資金 {initial_funds:,.0f} @ {initial_date}")

    print("✅ 初始記錄建立完成")


async def get_agent_transactions(conn, agent_id):
    """取得 Agent 全部交易（依時間排序）"""
    rows = await conn.fetch(
        """
        SELECT
            DATE(created_at) as trade_date,
            ticker,
            action,
            quantity,
            price,
            total_amount,
            commission
        FROM transactions
        WHERE agent_id = $1
          AND status = 'executed'
        ORDER BY created_at
        """,
        agent_id,
    )

    transactions = []
    for row in rows:
        transactions.append(
            {
                "trade_date": row["trade_date"],
                "ticker": row["ticker"],
                "action": row["action"],
                "quantity": int(row["quantity"]),
                "price": _to_float(row["price"]),
                "total_amount": _to_float(row["total_amount"]),
                "commission": _to_float(row["commission"]),
            }
        )

    return transactions


def calculate_daily_snapshots(transactions, initial_funds):
    """根據交易歷史計算每日績效快照"""

    if not transactions:
        return {}

    holdings: dict[str, dict[str, float]] = {}
    cash_balance = _to_float(initial_funds)
    total_trades = 0
    sell_trades_count = 0
    winning_trades = 0  # 獲利交易數
    snapshots: dict[str, dict[str, float]] = {}

    # 用於計算已實現損益
    cost_basis: dict[str, list[tuple[int, float]]] = {}  # {ticker: [(qty, price), ...]}
    realized_pnl = 0.0

    def holdings_value() -> float:
        value = 0.0
        for state in holdings.values():
            qty = state.get("quantity", 0.0)
            avg_cost = state.get("average_cost", 0.0)
            if qty > 0:
                value += qty * avg_cost
        return value

    for trade in transactions:
        ticker = trade["ticker"]
        action = trade["action"].upper()
        quantity = float(trade["quantity"])
        price = trade["price"]
        total_amount = trade["total_amount"]
        commission = trade["commission"]

        holding = holdings.setdefault(
            ticker,
            {"quantity": 0.0, "average_cost": 0.0},
        )

        if action == "BUY":
            total_cost = total_amount + commission
            cash_balance -= total_cost

            prev_qty = holding["quantity"]
            prev_cost = holding["average_cost"]
            new_qty = prev_qty + quantity

            if new_qty > 0:
                holding["average_cost"] = (prev_qty * prev_cost + total_amount) / new_qty

            holding["quantity"] = new_qty

            # 記錄成本基礎
            if ticker not in cost_basis:
                cost_basis[ticker] = []
            cost_basis[ticker].append((int(quantity), price))

        elif action == "SELL":
            net_proceeds = total_amount - commission
            cash_balance += net_proceeds

            prev_qty = holding["quantity"]
            new_qty = prev_qty - quantity

            # 計算已實現損益 (FIFO)
            sell_qty_remaining = int(quantity)
            sell_pnl = 0.0

            if ticker in cost_basis:
                while sell_qty_remaining > 0 and cost_basis[ticker]:
                    buy_qty, buy_price = cost_basis[ticker][0]

                    matched_qty = min(sell_qty_remaining, buy_qty)
                    # 損益 = (賣出價 - 買入價) × 數量
                    trade_pnl = (price - buy_price) * matched_qty
                    sell_pnl += trade_pnl

                    sell_qty_remaining -= matched_qty

                    if matched_qty >= buy_qty:
                        cost_basis[ticker].pop(0)
                    else:
                        cost_basis[ticker][0] = (buy_qty - matched_qty, buy_price)

            realized_pnl += sell_pnl

            # 判斷是否為獲利交易
            if sell_pnl > 0:
                winning_trades += 1

            holding["quantity"] = max(new_qty, 0.0)

            if holding["quantity"] == 0:
                holding["average_cost"] = 0.0

            sell_trades_count += 1
        else:
            raise ValueError(f"Unsupported action: {action}")

        total_trades += 1

        day_key = trade["trade_date"]
        portfolio_value = cash_balance + holdings_value()
        initial = _to_float(initial_funds)
        total_return = ((portfolio_value - initial) / initial) if initial else 0.0

        # 計算勝率
        win_rate = (winning_trades / sell_trades_count * 100) if sell_trades_count > 0 else 0.0

        snapshots[day_key] = {
            "total_value": portfolio_value,
            "cash_balance": cash_balance,
            "unrealized_pnl": holdings_value(),  # 未實現損益 = 持倉市值
            "realized_pnl": realized_pnl,
            "total_trades": total_trades,
            "sell_trades_count": sell_trades_count,
            "winning_trades": winning_trades,
            "total_return": total_return,
            "win_rate": win_rate,
        }

    return snapshots


async def rebuild_performance_records(conn, agents):
    """重建所有績效記錄"""
    print("\n🔄 根據交易歷史重新計算績效...")

    for agent_id, agent_name, initial_funds in agents:
        print(f"\n  處理 {agent_name} ({agent_id})...")

        transactions = await get_agent_transactions(conn, agent_id)
        print(f"    找到 {len(transactions)} 筆交易")

        snapshots = calculate_daily_snapshots(transactions, float(initial_funds))

        if not snapshots:
            print("    ⚠️ 沒有交易記錄，保留初始資料")
            continue

        for trade_date in sorted(snapshots.keys()):
            perf = snapshots[trade_date]

            await conn.execute(
                """
                INSERT INTO agent_performance (
                    agent_id, date, total_value, cash_balance, unrealized_pnl,
                    realized_pnl, total_return, win_rate, total_trades,
                    sell_trades_count, winning_trades_correct,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                ON CONFLICT (agent_id, date) DO UPDATE SET
                    total_value = EXCLUDED.total_value,
                    cash_balance = EXCLUDED.cash_balance,
                    unrealized_pnl = EXCLUDED.unrealized_pnl,
                    realized_pnl = EXCLUDED.realized_pnl,
                    total_return = EXCLUDED.total_return,
                    win_rate = EXCLUDED.win_rate,
                    total_trades = EXCLUDED.total_trades,
                    sell_trades_count = EXCLUDED.sell_trades_count,
                    winning_trades_correct = EXCLUDED.winning_trades_correct,
                    updated_at = NOW()
                """,
                agent_id,
                trade_date,
                perf["total_value"],
                perf["cash_balance"],
                perf["unrealized_pnl"],
                perf["realized_pnl"],
                perf["total_return"],
                perf["win_rate"],
                perf["total_trades"],
                perf["sell_trades_count"],
                perf["winning_trades"],
            )

            print(
                f"    ✓ {trade_date}: 總資產 {perf['total_value']:,.0f}, "
                f"現金 {perf['cash_balance']:,.0f}, "
                f"已實現損益 {perf['realized_pnl']:,.0f}, "
                f"勝率 {perf['win_rate']:.1f}%"
            )

    print("\n✅ 績效記錄重建完成")


async def show_transactions_summary(conn):
    """顯示 transactions 表的摘要"""
    print("\n📊 Transactions 表摘要:")

    # 按 Agent 統計
    rows = await conn.fetch("""
        SELECT
            agent_id,
            COUNT(*) as total_count,
            COUNT(CASE WHEN action = 'BUY' THEN 1 END) as buy_count,
            COUNT(CASE WHEN action = 'SELL' THEN 1 END) as sell_count,
            SUM(total_amount) as total_amount,
            MIN(created_at) as first_trade,
            MAX(created_at) as last_trade
        FROM transactions
        WHERE status = 'executed'
        GROUP BY agent_id
        ORDER BY agent_id
    """)

    for row in rows:
        print(f"\n  Agent: {row['agent_id']}")
        print(
            f"    總交易數: {row['total_count']} (買入: {row['buy_count']}, 賣出: {row['sell_count']})"
        )
        print(f"    總金額: {row['total_amount']:,.0f}")
        print(f"    交易期間: {row['first_trade']} ~ {row['last_trade']}")


async def verify_results(conn):
    """驗證結果"""
    print("\n📊 驗證 agent_performance 結果...")

    rows = await conn.fetch("""
        SELECT
            agent_id,
            COUNT(*) as record_count,
            MIN(date) as first_date,
            MAX(date) as last_date,
            MAX(total_value) as max_value,
            MAX(realized_pnl) as total_realized_pnl,
            MAX(win_rate) as final_win_rate
        FROM agent_performance
        GROUP BY agent_id
        ORDER BY agent_id
    """)

    for row in rows:
        print(f"\n  {row['agent_id']}:")
        print(f"    記錄數: {row['record_count']}")
        print(f"    日期範圍: {row['first_date']} ~ {row['last_date']}")
        print(f"    最高資產: {row['max_value']:,.0f}")
        print(f"    累計已實現損益: {row['total_realized_pnl']:,.0f}")
        print(f"    最終勝率: {row['final_win_rate']:.1f}%")


async def main():
    """主程序"""
    conn = await get_connection()

    try:
        print("=" * 80)
        print("🚀 開始重建 agent_performance 表 (PostgreSQL)")
        print("=" * 80)

        # 0. 顯示 transactions 摘要
        await show_transactions_summary(conn)

        # 1. 清空表
        await clear_performance_table(conn)

        # 2. 取得所有 Agent
        agents = await get_all_agents(conn)
        print(f"\n找到 {len(agents)} 個 Agent")

        # 3. 創建初始記錄
        await create_initial_records(conn, agents)

        # 4. 根據交易重新計算
        await rebuild_performance_records(conn, agents)

        # 5. 驗證結果
        await verify_results(conn)

        print("\n✅ 所有變更已提交到資料庫")

    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        raise

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
