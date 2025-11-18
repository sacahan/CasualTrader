#!/usr/bin/env python3
"""
重建 agent_performance 表的腳本
1. 為每個 Agent 創建初始記錄（使用 initial_funds）
2. 根據 transactions 和 agent_holdings 逐日重新計算績效
"""

import sqlite3
from datetime import datetime, date, timedelta


def _to_float(value: float | int | None) -> float:
    """Convert possible SQLite numeric values to float safely."""

    if value is None:
        return 0.0
    return float(value)


def get_connection():
    """建立資料庫連線"""
    return sqlite3.connect("casualtrader.db")


def clear_performance_table(cursor):
    """清空 agent_performance 表"""
    print("🧹 清空 agent_performance 表...")
    cursor.execute("DELETE FROM agent_performance")
    print("✅ 已清空")


def get_all_agents(cursor):
    """取得所有 Agent"""
    cursor.execute("SELECT id, name, initial_funds FROM agents ORDER BY created_at")
    return cursor.fetchall()


def create_initial_records(cursor, agents):
    """為每個 Agent 創建初始績效記錄"""
    print("\n📝 為每個 Agent 創建初始績效記錄...")

    for agent_id, agent_name, initial_funds in agents:
        # 使用第一筆交易日期的前一天作為初始記錄日期
        cursor.execute(
            """
            SELECT MIN(DATE(created_at)) as first_trade_date
            FROM transactions
            WHERE agent_id = ?
        """,
            (agent_id,),
        )

        result = cursor.fetchone()
        first_trade_date = result[0] if result[0] else str(date.today())
        initial_date = (
            (datetime.strptime(first_trade_date, "%Y-%m-%d") - timedelta(days=1)).date()
            if first_trade_date
            else date(2025, 11, 1)
        )

        cursor.execute(
            """
            INSERT INTO agent_performance (
                agent_id, date, total_value, cash_balance, unrealized_pnl,
                realized_pnl, daily_return, total_return, win_rate, max_drawdown,
                total_trades, sell_trades_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
            (
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
            ),
        )

        print(f"  ✓ {agent_name} ({agent_id}): 初始資金 {initial_funds:,.0f} @ {initial_date}")

    print("✅ 初始記錄建立完成")


def get_agent_transactions(cursor, agent_id):
    """取得 Agent 全部交易（依時間排序）。"""

    cursor.execute(
        """
        SELECT
            DATE(created_at) as trade_date,
            ticker,
            action,
            quantity,
            total_amount,
            commission
        FROM transactions
        WHERE agent_id = ?
        ORDER BY created_at
    """,
        (agent_id,),
    )

    transactions = []
    for row in cursor.fetchall():
        transactions.append(
            {
                "trade_date": row[0],
                "ticker": row[1],
                "action": row[2],
                "quantity": int(row[3]),
                "total_amount": _to_float(row[4]),
                "commission": _to_float(row[5]),
            }
        )

    return transactions


def calculate_daily_snapshots(transactions, initial_funds):
    """根據交易歷史計算每日績效快照。"""

    if not transactions:
        return {}

    holdings: dict[str, dict[str, float]] = {}
    cash_balance = _to_float(initial_funds)
    total_trades = 0
    sell_trades_count = 0
    snapshots: dict[str, dict[str, float]] = {}

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

        elif action == "SELL":
            net_proceeds = total_amount - commission
            cash_balance += net_proceeds

            prev_qty = holding["quantity"]
            new_qty = prev_qty - quantity

            holding["quantity"] = max(new_qty, 0.0)

            if holding["quantity"] == 0:
                holding["average_cost"] = 0.0

            sell_trades_count += 1
        else:
            raise ValueError(f"Unsupported action: {action}")

        total_trades += 1

        day_key = trade["trade_date"]
        portfolio_value = cash_balance + holdings_value()
        # 保持與服務層一致：total_return 儲存為小數比例（例如 0.012 表示 1.2%）
        total_return = ((portfolio_value - initial_funds) / initial_funds) if initial_funds else 0.0

        snapshots[day_key] = {
            "total_value": portfolio_value,
            "cash_balance": cash_balance,
            "unrealized_pnl": 0.0,
            "total_trades": total_trades,
            "sell_trades_count": sell_trades_count,
            "total_return": total_return,
        }

    return snapshots


def rebuild_performance_records(cursor, agents):
    """重建所有績效記錄"""
    print("\n🔄 根據交易歷史重新計算績效...")

    for agent_id, agent_name, initial_funds in agents:
        print(f"\n  處理 {agent_name} ({agent_id})...")

        transactions = get_agent_transactions(cursor, agent_id)
        snapshots = calculate_daily_snapshots(transactions, float(initial_funds))

        if not snapshots:
            print("    ⚠️ 沒有交易記錄，保留初始資料")
            continue

        for trade_date in sorted(snapshots.keys()):
            perf = snapshots[trade_date]

            cursor.execute(
                """
                INSERT INTO agent_performance (
                    agent_id, date, total_value, cash_balance, unrealized_pnl,
                    realized_pnl, total_return, total_trades, sell_trades_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(agent_id, date) DO UPDATE SET
                    total_value = excluded.total_value,
                    cash_balance = excluded.cash_balance,
                    unrealized_pnl = excluded.unrealized_pnl,
                    total_return = excluded.total_return,
                    total_trades = excluded.total_trades,
                    sell_trades_count = excluded.sell_trades_count,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (
                    agent_id,
                    trade_date,
                    perf["total_value"],
                    perf["cash_balance"],
                    perf["unrealized_pnl"],
                    0.0,  # realized_pnl
                    perf["total_return"],
                    perf["total_trades"],
                    perf["sell_trades_count"],
                ),
            )

            print(
                f"    ✓ {trade_date}: 總資產 {perf['total_value']:,.0f}, 現金 {perf['cash_balance']:,.0f}"
            )

    print("\n✅ 績效記錄重建完成")


def verify_results(cursor):
    """驗證結果"""
    print("\n📊 驗證結果...")

    cursor.execute("""
        SELECT
            agent_id,
            COUNT(*) as record_count,
            MIN(date) as first_date,
            MAX(date) as last_date
        FROM agent_performance
        GROUP BY agent_id
        ORDER BY agent_id
    """)

    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 筆記錄 ({row[2]} ~ {row[3]})")


def main():
    """主程序"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("=" * 80)
        print("🚀 開始重建 agent_performance 表")
        print("=" * 80)

        # 1. 清空表
        clear_performance_table(cursor)

        # 2. 取得所有 Agent
        agents = get_all_agents(cursor)
        print(f"\n找到 {len(agents)} 個 Agent")

        # 3. 創建初始記錄
        create_initial_records(cursor, agents)

        # 4. 根據交易重新計算
        rebuild_performance_records(cursor, agents)

        # 5. 驗證結果
        verify_results(cursor)

        # 提交所有變更
        conn.commit()
        print("\n✅ 所有變更已提交到資料庫")

    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
