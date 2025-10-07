#!/usr/bin/env python3
"""
CasualTrader Phase 2 基礎測試
驗證 Phase 2 核心功能實作
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class Phase2BasicTest:
    """Phase 2 基礎功能測試"""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.tests = []

    def log_test(self, test_name: str, result: bool, message: str = "") -> None:
        """記錄測試結果"""
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if message:
            print(f"      {message}")

        if result:
            self.passed += 1
        else:
            self.failed += 1

        self.tests.append((test_name, result, message))

    async def test_agent_tools_integration(self) -> None:
        """測試專業分析工具整合"""
        print("\n🔧 測試專業分析工具整合...")

        try:
            # 測試 FundamentalAgent
            from src.agents.tools.fundamental_agent import FundamentalAgent

            fundamental_agent = FundamentalAgent()
            tool_config = fundamental_agent.as_tool(
                "fundamental_analysis", "分析公司基本面"
            )

            assert tool_config["type"] == "function"
            assert "fundamental_analysis" in tool_config["function"]["name"]
            assert "implementation" in tool_config
            self.log_test("FundamentalAgent.as_tool()", True, "工具配置正確")

            # 測試 TechnicalAgent
            from src.agents.tools.technical_agent import TechnicalAgent

            technical_agent = TechnicalAgent()
            tool_config = technical_agent.as_tool("technical_analysis", "技術分析")

            assert tool_config["type"] == "function"
            self.log_test("TechnicalAgent.as_tool()", True, "工具配置正確")

            # 測試 RiskAgent
            from src.agents.tools.risk_agent import RiskAgent

            risk_agent = RiskAgent()
            tool_config = risk_agent.as_tool("risk_assessment", "風險評估")

            assert tool_config["type"] == "function"
            self.log_test("RiskAgent.as_tool()", True, "工具配置正確")

            # 測試 SentimentAgent
            from src.agents.tools.sentiment_agent import SentimentAgent

            sentiment_agent = SentimentAgent()
            tool_config = sentiment_agent.as_tool("market_sentiment", "市場情緒分析")

            assert tool_config["type"] == "function"
            self.log_test("SentimentAgent.as_tool()", True, "工具配置正確")

        except Exception as e:
            self.log_test("專業分析工具整合", False, f"錯誤: {e}")

    async def test_openai_tools_integration(self) -> None:
        """測試 OpenAI Tools 整合"""
        print("\n🌐 測試 OpenAI Tools 整合...")

        try:
            from src.agents.integrations.openai_tools import OpenAIToolsIntegrator

            integrator = OpenAIToolsIntegrator()

            # 測試 WebSearchTool
            web_tool = integrator.get_web_search_tool()
            assert web_tool["type"] == "web_search"
            self.log_test("WebSearchTool 配置", True, "工具配置正確")

            # 測試 CodeInterpreterTool
            code_tool = integrator.get_code_interpreter_tool()
            assert code_tool["type"] == "code_interpreter"
            self.log_test("CodeInterpreterTool 配置", True, "工具配置正確")

        except Exception as e:
            self.log_test("OpenAI Tools 整合", False, f"錯誤: {e}")

    async def test_strategy_change_recording(self) -> None:
        """測試策略變更記錄功能"""
        print("\n📝 測試策略變更記錄功能...")

        try:
            from src.agents.functions.strategy_change_recorder import (
                StrategyChangeRecorder,
            )

            recorder = StrategyChangeRecorder()

            # 測試工具配置
            tool_config = recorder.as_tool()
            assert tool_config["type"] == "function"
            assert tool_config["function"]["name"] == "record_strategy_change"
            self.log_test("StrategyChangeRecorder.as_tool()", True, "工具配置正確")

        except Exception as e:
            self.log_test("策略變更記錄功能", False, f"錯誤: {e}")

    async def test_trading_functions(self) -> None:
        """測試交易功能"""
        print("\n💼 測試交易功能...")

        try:
            # 測試市場狀態檢查
            from src.agents.functions.market_status import MarketStatusChecker

            market_checker = MarketStatusChecker()
            tool_config = market_checker.as_tool()
            assert tool_config["type"] == "function"
            self.log_test("MarketStatusChecker.as_tool()", True, "工具配置正確")

            # 測試交易驗證
            from src.agents.functions.trading_validation import TradingValidator

            validator = TradingValidator()
            tool_config = validator.as_tool()
            assert tool_config["type"] == "function"
            self.log_test("TradingValidator.as_tool()", True, "工具配置正確")

        except Exception as e:
            self.log_test("交易功能測試", False, f"錯誤: {e}")

    async def test_instruction_generator(self) -> None:
        """測試指令生成器"""
        print("\n📋 測試 TradingAgent 指令生成系統...")

        try:
            from src.agents.core.instruction_generator import InstructionGenerator
            from src.agents.core.models import AgentConfig

            generator = InstructionGenerator()

            # 創建測試配置
            config = AgentConfig(
                agent_id="test_agent",
                name="Test Agent",
                description="Test trading agent",
                investment_preferences="成長型投資，重視科技股",
                strategy_adjustment_criteria="當連續虧損超過3%時調整策略",
                additional_instructions="專注於台股市場",
            )

            # 生成指令
            instructions = generator.generate_trading_instructions(config)

            assert isinstance(instructions, str)
            assert len(instructions) > 100
            assert "Test Agent" in instructions
            self.log_test(
                "InstructionGenerator 指令生成",
                True,
                f"生成指令長度: {len(instructions)}",
            )

        except Exception as e:
            self.log_test("指令生成系統", False, f"錯誤: {e}")

    async def test_existing_trading_agent(self) -> None:
        """測試現有的 TradingAgent"""
        print("\n🤖 測試現有 TradingAgent 實作...")

        try:
            from src.agents.core.models import AgentConfig
            from src.agents.trading.trading_agent import TradingAgent

            # 創建測試配置
            config = AgentConfig(
                agent_id="test_trading_agent",
                name="Test Trading Agent",
                description="測試交易代理人",
                investment_preferences="平衡型投資策略",
                strategy_adjustment_criteria="基於市場波動調整",
            )

            # 創建 TradingAgent
            agent = TradingAgent(config)

            # 測試基本屬性
            assert agent.agent_id == config.agent_id
            assert agent.config.name == config.name
            self.log_test("TradingAgent 基本實例化", True, "Agent 創建成功")

            # 測試工具設定
            tools = await agent._setup_tools()
            assert isinstance(tools, list)
            assert len(tools) > 0
            self.log_test("TradingAgent 工具設定", True, f"配置了 {len(tools)} 個工具")

        except Exception as e:
            self.log_test("TradingAgent 測試", False, f"錯誤: {e}")

    async def run_all_tests(self) -> None:
        """運行所有測試"""
        print("=" * 70)
        print("🧪 CasualTrader Phase 2 基礎功能測試")
        print("=" * 70)

        await self.test_agent_tools_integration()
        await self.test_openai_tools_integration()
        await self.test_strategy_change_recording()
        await self.test_trading_functions()
        await self.test_instruction_generator()
        await self.test_existing_trading_agent()

        # 測試結果總結
        print("\n" + "=" * 70)
        print("📊 測試結果總結")
        print("=" * 70)
        print(f"✅ 通過: {self.passed}")
        print(f"❌ 失敗: {self.failed}")
        print(f"📈 通過率: {self.passed / (self.passed + self.failed) * 100:.1f}%")

        if self.failed == 0:
            print("\n🎉 Phase 2 基礎功能測試全部通過！")
            print("✅ 可以進入 Phase 3 開發")
        else:
            print(f"\n⚠️  有 {self.failed} 個測試失敗，需要修復")

            # 顯示失敗的測試
            print("\n❌ 失敗的測試:")
            for test_name, result, message in self.tests:
                if not result:
                    print(f"  - {test_name}: {message}")


async def main():
    """主函數"""
    tester = Phase2BasicTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
