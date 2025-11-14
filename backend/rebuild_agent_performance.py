#!/usr/bin/env python3
"""
重建 agent_performance 表的腳本
1. 為每個 Agent 創建初始記錄（使用 initial_funds）
2. 根據 transactions 和 agent_holdings 逐日重新計算績效
"""

import sqlite3
from datetime import datetime, date, timedelta
from collections import defaultdict


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


def get_trades_by_date(cursor, agent_id):
    """取得 Agent 按日期排序的所有交易"""
    cursor.execute(
        """
        SELECT
            DATE(created_at) as trade_date,
            ticker,
            action,
            quantity,
            price,
            total_amount
        FROM transactions
        WHERE agent_id = ?
        ORDER BY created_at
    """,
        (agent_id,),
    )

    # 按日期分組
    trades_by_date = defaultdict(list)
    for row in cursor.fetchall():
        trade_date = row[0]
        trades_by_date[trade_date].append(
            {
                "ticker": row[1],
                "action": row[2],
                "quantity": row[3],
                "price": row[4],
                "amount": row[5],
            }
        )

    return trades_by_date


def get_holdings_on_date(cursor, agent_id, target_date):
    """取得 Agent 在特定日期的持倉"""
    cursor.execute(
        """
        SELECT ticker, quantity, average_cost
        FROM agent_holdings
        WHERE agent_id = ?
    """,
        (agent_id,),
    )

    holdings = {}
    for row in cursor.fetchall():
        holdings[row[0]] = {"quantity": row[1], "average_cost": float(row[2])}

    return holdings


def calculate_holdings_after_trades(holdings, trades):
    """根據交易計算持倉"""
    for trade in trades:
        ticker = trade["ticker"]
        action = trade["action"]
        quantity = trade["quantity"]
        price = float(trade["price"])

        if ticker not in holdings:
            holdings[ticker] = {"quantity": 0, "average_cost": 0.0}

        holding = holdings[ticker]

        if action == "BUY":
            old_qty = holding["quantity"]
            old_cost = holding["average_cost"]
            new_qty = old_qty + quantity

            # 計算新的平均成本
            if new_qty > 0:
                holding["average_cost"] = (old_qty * old_cost + quantity * price) / new_qty

            holding["quantity"] = new_qty

        elif action == "SELL":
            holding["quantity"] -= quantity
            # 賣出不改變平均成本

    return holdings


def calculate_daily_performance(cursor, agent_id, target_date, initial_funds):
    """計算特定日期的績效"""
    # 取得該日期前的所有交易
    cursor.execute(
        """
        SELECT
            SUM(CASE WHEN action='BUY' THEN total_amount ELSE 0 END) as total_bought,
            SUM(CASE WHEN action='SELL' THEN total_amount ELSE 0 END) as total_sold,
            COUNT(CASE WHEN action='BUY' THEN 1 END) as buy_count,
            COUNT(CASE WHEN action='SELL' THEN 1 END) as sell_count
        FROM transactions
        WHERE agent_id = ? AND DATE(created_at) <= ?
    """,
        (agent_id, target_date),
    )

    result = cursor.fetchone()
    total_bought = float(result[0]) if result[0] else 0.0
    total_sold = float(result[1]) if result[1] else 0.0
    total_buy_count = result[2] or 0
    total_sell_count = result[3] or 0

    # 取得當前持倉
    holdings = get_holdings_on_date(cursor, agent_id, target_date)

    # 計算持倉市值（以平均成本作為市場價格的估計）
    # 實際應該用當日的收盤價，但這裡用平均成本作為基準
    holding_value = 0.0
    for ticker, holding in holdings.items():
        if holding["quantity"] > 0:
            holding_value += holding["quantity"] * holding["average_cost"]

    # 計算現金餘額
    cash_balance = initial_funds - total_bought + total_sold

    # 計算總資產
    total_value = cash_balance + holding_value

    # 計算未實現損益（這個需要實際市場價格，這裡無法精確計算）
    unrealized_pnl = 0.0  # 暫時設為 0

    # 計算累計報酬率
    total_return = (
        ((total_value - initial_funds) / initial_funds * 100) if initial_funds > 0 else 0.0
    )

    return {
        "total_value": total_value,
        "cash_balance": cash_balance,
        "unrealized_pnl": unrealized_pnl,
        "total_trades": total_buy_count + total_sell_count,
        "sell_trades_count": total_sell_count,
        "total_return": total_return,
    }


def rebuild_performance_records(cursor, agents):
    """重建所有績效記錄"""
    print("\n🔄 根據交易歷史重新計算績效...")

    for agent_id, agent_name, initial_funds in agents:
        print(f"\n  處理 {agent_name} ({agent_id})...")

        # 取得該 Agent 的所有交易日期
        cursor.execute(
            """
            SELECT DISTINCT DATE(created_at) as trade_date
            FROM transactions
            WHERE agent_id = ?
            ORDER BY trade_date
        """,
            (agent_id,),
        )

        trade_dates = [row[0] for row in cursor.fetchall()]

        for trade_date in trade_dates:
            perf = calculate_daily_performance(cursor, agent_id, trade_date, float(initial_funds))

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
                f"    ✓ {trade_date}: 總資產 {float(perf['total_value']):,.0f}, 現金 {float(perf['cash_balance']):,.0f}"
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
