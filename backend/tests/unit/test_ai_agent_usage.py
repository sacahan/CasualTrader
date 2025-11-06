#!/usr/bin/env python
"""
AI Agent 使用方式測試

測試改進的工具是否能在 AI Agent 的實際呼叫方式下工作
"""

import sys
from pathlib import Path

# 添加src到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_sentiment_agent_tools():
    """測試 Sentiment Agent 工具"""
    print("\n" + "=" * 60)
    print("測試 Sentiment Agent 工具")
    print("=" * 60)

    try:
        from trading.tools.sentiment_agent import (
            analyze_money_flow,
            analyze_news_sentiment,
            analyze_social_sentiment,
            generate_sentiment_signals,
        )

        # 測試 1: 缺少參數
        print("\n✓ 測試 1: analyze_money_flow() 無參數呼叫")
        result = analyze_money_flow()
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 2: JSON 字串參數
        print("\n✓ 測試 2: analyze_news_sentiment() JSON 字串參數")
        json_str = '{"ticker":"2330"}'
        result = analyze_news_sentiment(args=json_str)
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 3: 字典參數
        print("\n✓ 測試 3: analyze_social_sentiment() 字典參數")
        result = analyze_social_sentiment(ticker="2330", social_data={"positive_posts": 100})
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 4: generate_sentiment_signals 字典參數
        print("\n✓ 測試 4: generate_sentiment_signals() 字典參數")
        result = generate_sentiment_signals(
            money_flow_data={}, news_sentiment_data={}, social_sentiment_data={}, fear_greed_data={}
        )
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        print("\n✅ Sentiment Agent 所有測試通過")
        return True

    except Exception as e:
        print(f"\n❌ Sentiment Agent 測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_technical_agent_tools():
    """測試 Technical Agent 工具"""
    print("\n" + "=" * 60)
    print("測試 Technical Agent 工具")
    print("=" * 60)

    try:
        from trading.tools.technical_agent import (
            calculate_technical_indicators,
            identify_chart_patterns,
            analyze_trend,
        )

        # 測試 1: 無參數
        print("\n✓ 測試 1: calculate_technical_indicators() 無參數")
        result = calculate_technical_indicators()
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 2: 字典參數
        print("\n✓ 測試 2: identify_chart_patterns() 字典參數")
        result = identify_chart_patterns(ticker="2330", price_data=[])
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 3: JSON 字串參數
        print("\n✓ 測試 3: analyze_trend() JSON 字串參數")
        result = analyze_trend(args='{"ticker":"2330","price_data":[]}')
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        print("\n✅ Technical Agent 所有測試通過")
        return True

    except Exception as e:
        print(f"\n❌ Technical Agent 測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_fundamental_agent_tools():
    """測試 Fundamental Agent 工具"""
    print("\n" + "=" * 60)
    print("測試 Fundamental Agent 工具")
    print("=" * 60)

    try:
        from trading.tools.fundamental_agent import (
            calculate_financial_ratios,
            analyze_financial_health,
            evaluate_valuation,
        )

        # 測試 1: 無參數
        print("\n✓ 測試 1: calculate_financial_ratios() 無參數")
        result = calculate_financial_ratios()
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 2: 字典參數
        print("\n✓ 測試 2: analyze_financial_health() 字典參數")
        result = analyze_financial_health(ticker="2330", financial_ratios={})
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 3: JSON 字串參數
        print("\n✓ 測試 3: evaluate_valuation() JSON 字串參數")
        result = evaluate_valuation(args='{"ticker":"2330"}')
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        print("\n✅ Fundamental Agent 所有測試通過")
        return True

    except Exception as e:
        print(f"\n❌ Fundamental Agent 測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_risk_agent_tools():
    """測試 Risk Agent 工具"""
    print("\n" + "=" * 60)
    print("測試 Risk Agent 工具")
    print("=" * 60)

    try:
        from trading.tools.risk_agent import (
            calculate_position_risk,
            analyze_portfolio_concentration,
            perform_stress_test,
        )

        # 測試 1: 無參數
        print("\n✓ 測試 1: calculate_position_risk() 無參數")
        result = calculate_position_risk()
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 2: 字典參數
        print("\n✓ 測試 2: analyze_portfolio_concentration() 字典參數")
        result = analyze_portfolio_concentration(positions=[], total_value=0)
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        # 測試 3: JSON 字串參數
        print("\n✓ 測試 3: perform_stress_test() JSON 字串參數")
        result = perform_stress_test(args='{"positions":[],"scenarios":[]}')
        assert isinstance(result, dict), "應返回字典"
        print(f"  結果: {result}")

        print("\n✅ Risk Agent 所有測試通過")
        return True

    except Exception as e:
        print(f"\n❌ Risk Agent 測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 開始 AI Agent 使用方式測試\n")

    results = []
    results.append(("Sentiment Agent", test_sentiment_agent_tools()))
    results.append(("Technical Agent", test_technical_agent_tools()))
    results.append(("Fundamental Agent", test_fundamental_agent_tools()))
    results.append(("Risk Agent", test_risk_agent_tools()))

    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} {name}")

    all_passed = all(passed for _, passed in results)
    print("\n" + ("🎉 所有測試通過!" if all_passed else "❌ 部分測試失敗"))

    sys.exit(0 if all_passed else 1)
