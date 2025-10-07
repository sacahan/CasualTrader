#!/usr/bin/env python3
"""
整合功能測試腳本
測試新整合的 MCP、資料庫、技術指標、風險計算功能
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_mcp_client():
    """測試 MCP 客戶端"""
    print("\n" + "=" * 60)
    print("🔍 測試 MCP 客戶端")
    print("=" * 60)

    from src.agents.integrations.mcp_client import get_mcp_client

    mcp = get_mcp_client()
    await mcp.initialize()

    # 測試股票價格查詢
    print("\n📊 測試股票價格查詢...")
    price_data = await mcp.get_stock_price("2330")
    print(f"  ✓ 台積電 (2330) 價格: {price_data['current_price']}")
    print(f"  ✓ 漲跌: {price_data['change']} ({price_data['change_percent']:.2f}%)")

    # 測試公司基本資料
    print("\n🏢 測試公司基本資料...")
    profile = await mcp.get_company_profile("2330")
    print(f"  ✓ 公司名稱: {profile['company_name']}")
    print(f"  ✓ 產業: {profile['industry']}")

    # 測試模擬交易
    print("\n💰 測試模擬交易...")
    buy_result = await mcp.simulate_buy("2330", 1000, 600.0)
    print("  ✓ 買入 1000 股，價格 600 元")
    print(f"  ✓ 總金額: {buy_result['total_amount']:,.0f}")
    print(f"  ✓ 手續費: {buy_result['fee']:,.0f}")
    print(f"  ✓ 實付: {buy_result['net_amount']:,.0f}")

    await mcp.close()
    print("\n✅ MCP 客戶端測試完成")


async def test_technical_indicators():
    """測試技術指標計算"""
    print("\n" + "=" * 60)
    print("📈 測試技術指標計算")
    print("=" * 60)

    from src.agents.utils.technical_indicators import get_indicator_calculator

    calculator = get_indicator_calculator()

    # 模擬價格數據
    prices = [
        100.0,
        102.0,
        101.0,
        103.0,
        105.0,
        104.0,
        106.0,
        108.0,
        107.0,
        109.0,
        111.0,
        110.0,
        112.0,
        114.0,
        113.0,
        115.0,
        117.0,
        116.0,
        118.0,
        120.0,
    ]

    highs = [p + 2 for p in prices]
    lows = [p - 2 for p in prices]
    volumes = [1000000 + i * 10000 for i in range(len(prices))]

    # 測試移動平均
    print("\n📊 測試移動平均線...")
    ma5 = calculator.calculate_ma(prices, 5)
    ma10 = calculator.calculate_ma(prices, 10)
    print(f"  ✓ MA5: {ma5[-1]:.2f}")
    print(f"  ✓ MA10: {ma10[-1]:.2f}")

    # 測試 RSI
    print("\n📊 測試 RSI 指標...")
    rsi = calculator.calculate_rsi(prices, 14)
    print(f"  ✓ RSI(14): {rsi[-1]:.2f}")

    # 測試 MACD
    print("\n📊 測試 MACD 指標...")
    macd_result = calculator.calculate_macd(prices)
    print(f"  ✓ MACD: {macd_result['macd'][-1]:.2f}")
    print(f"  ✓ 訊號線: {macd_result['signal'][-1]:.2f}")
    print(f"  ✓ 柱狀圖: {macd_result['histogram'][-1]:.2f}")

    # 測試布林通道
    print("\n📊 測試布林通道...")
    bollinger = calculator.calculate_bollinger_bands(prices, 20, 2.0)
    print(f"  ✓ 上軌: {bollinger['upper'][-1]:.2f}")
    print(f"  ✓ 中軌: {bollinger['middle'][-1]:.2f}")
    print(f"  ✓ 下軌: {bollinger['lower'][-1]:.2f}")

    # 測試 KD 指標
    print("\n📊 測試 KD 指標...")
    stochastic = calculator.calculate_stochastic(highs, lows, prices, 14, 3)
    print(f"  ✓ K 值: {stochastic['k'][-1]:.2f}")
    print(f"  ✓ D 值: {stochastic['d'][-1]:.2f}")

    # 測試成交量指標
    print("\n📊 測試成交量指標...")
    volume_indicators = calculator.calculate_volume_indicators(volumes, 5)
    print(f"  ✓ 平均成交量: {volume_indicators['average_volume']:,.0f}")
    print(f"  ✓ 量比: {volume_indicators['volume_ratio']:.2f}")

    print("\n✅ 技術指標計算測試完成")


async def test_risk_calculator():
    """測試風險計算"""
    print("\n" + "=" * 60)
    print("⚠️  測試風險計算")
    print("=" * 60)

    from src.agents.utils.risk_analytics import get_risk_calculator

    risk_calc = get_risk_calculator()

    # 模擬價格數據
    prices = [
        100,
        102,
        99,
        103,
        101,
        104,
        100,
        105,
        103,
        107,
        105,
        108,
        104,
        110,
        108,
        112,
        109,
        114,
        111,
        115,
    ]

    # 計算報酬率
    print("\n📊 計算報酬率...")
    returns = risk_calc.calculate_returns(prices)
    print(f"  ✓ 平均日報酬率: {returns.mean():.4f}")

    # 計算波動率
    print("\n📊 計算波動率...")
    volatility = risk_calc.calculate_volatility(returns, annualize=True)
    print(f"  ✓ 年化波動率: {volatility:.2%}")

    # 計算最大回撤
    print("\n📊 計算最大回撤...")
    max_dd = risk_calc.calculate_max_drawdown(prices)
    print(f"  ✓ 最大回撤: {max_dd:.2%}")

    # 計算 VaR
    print("\n📊 計算風險值 (VaR)...")
    var_95 = risk_calc.calculate_var(returns, 0.95)
    var_99 = risk_calc.calculate_var(returns, 0.99)
    print(f"  ✓ VaR (95%): {var_95:.2%}")
    print(f"  ✓ VaR (99%): {var_99:.2%}")

    # 計算夏普比率
    print("\n📊 計算夏普比率...")
    sharpe = risk_calc.calculate_sharpe_ratio(returns, risk_free_rate=0.01)
    print(f"  ✓ 夏普比率: {sharpe:.2f}")

    # 計算索提諾比率
    print("\n📊 計算索提諾比率...")
    sortino = risk_calc.calculate_sortino_ratio(returns, risk_free_rate=0.01)
    print(f"  ✓ 索提諾比率: {sortino:.2f}")

    # 測試投資組合計算
    print("\n📊 測試投資組合風險計算...")
    returns_dict = {
        "2330": returns.tolist(),
        "2317": [r * 0.9 for r in returns.tolist()],
        "2454": [r * 1.1 for r in returns.tolist()],
    }
    weights = [0.5, 0.3, 0.2]

    portfolio_vol = risk_calc.calculate_portfolio_volatility(weights, returns_dict)
    print(f"  ✓ 投資組合波動率: {portfolio_vol:.2%}")

    hhi = risk_calc.calculate_concentration_hhi(weights)
    print(f"  ✓ 集中度 (HHI): {hhi:.3f}")

    print("\n✅ 風險計算測試完成")


async def test_sentiment_analyzer():
    """測試情緒分析"""
    print("\n" + "=" * 60)
    print("😊 測試情緒分析")
    print("=" * 60)

    from src.agents.utils.risk_analytics import get_sentiment_analyzer

    sentiment = get_sentiment_analyzer()

    # 模擬價格和成交量數據
    prices = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109, 111, 113]
    volumes = [
        1000000,
        1200000,
        1500000,
        1100000,
        1800000,
        1600000,
        1300000,
        1900000,
        2000000,
        1400000,
        2200000,
        2500000,
    ]

    # 分析價格動能
    print("\n📊 分析價格動能...")
    momentum = sentiment.analyze_price_momentum(prices, period=10)
    print(f"  ✓ 動能分數: {momentum['momentum_score']:.1f}/100")
    print(f"  ✓ 趨勢: {momentum['trend']}")
    print(f"  ✓ 強度: {momentum['strength']}")
    print(f"  ✓ 期間報酬: {momentum['period_return']:.2%}")

    # 分析成交量情緒
    print("\n📊 分析成交量情緒...")
    volume_sentiment = sentiment.analyze_volume_sentiment(volumes, prices)
    print(f"  ✓ 量比: {volume_sentiment['volume_ratio']:.2f}")
    print(f"  ✓ 情緒: {volume_sentiment['sentiment']}")
    print(
        f"  ✓ 當前成交量: {volume_sentiment['current_volume']:,.0f} vs 平均: {volume_sentiment['average_volume']:,.0f}"
    )

    print("\n✅ 情緒分析測試完成")


async def test_portfolio_queries():
    """測試投資組合查詢"""
    print("\n" + "=" * 60)
    print("💼 測試投資組合查詢")
    print("=" * 60)

    from src.agents.functions.portfolio_queries import PortfolioQueries

    # 創建查詢器 (無資料庫連接，使用模擬數據)
    queries = PortfolioQueries()

    # 測試取得投資組合摘要
    print("\n📊 測試投資組合摘要...")
    summary = await queries.get_portfolio_summary("test_agent_001")
    print(f"  ✓ 總資產: {summary.total_value:,.0f}")
    print(f"  ✓ 現金: {summary.cash_balance:,.0f}")
    print(f"  ✓ 投資金額: {summary.invested_amount:,.0f}")
    print(f"  ✓ 未實現損益: {summary.total_unrealized_pnl:,.0f}")
    print(f"  ✓ 未實現損益%: {summary.total_unrealized_pnl_percent:.2%}")
    print(f"  ✓ 持倉數: {summary.positions_count}")

    print("\n✅ 投資組合查詢測試完成")


async def main():
    """主程式"""
    print("\n" + "=" * 60)
    print("🚀 CasualTrader 整合功能測試")
    print("=" * 60)

    try:
        # 測試 MCP 客戶端
        await test_mcp_client()

        # 測試技術指標計算
        await test_technical_indicators()

        # 測試風險計算
        await test_risk_calculator()

        # 測試情緒分析
        await test_sentiment_analyzer()

        # 測試投資組合查詢
        await test_portfolio_queries()

        print("\n" + "=" * 60)
        print("✅ 所有測試完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
