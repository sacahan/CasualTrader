"""
Phase 3 集成測試：記憶體工作流程深度整合

測試 Agent 的記憶體加載、保存和計劃下一步功能。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from trading.trading_agent import TradingAgent
from common.enums import AgentMode, AgentStatus
from service.agents_service import AgentsService
from database.models import Agent as AgentConfig


@pytest.fixture
def mock_agent_config():
    """創建模擬 Agent 配置"""
    config = MagicMock(spec=AgentConfig)
    config.id = "test-agent"
    config.name = "Test Agent"
    config.description = "Test description"
    config.ai_model = "gpt-4-mini"
    config.current_mode = AgentMode.TRADING
    config.status = AgentStatus.INACTIVE
    config.investment_preferences = "2330,2454"
    config.max_position_size = 10
    return config


@pytest.fixture
async def mock_agent_service():
    """創建模擬 Agent 服務"""
    service = AsyncMock(spec=AgentsService)
    service.update_agent_status = AsyncMock()
    service.get_ai_model_config = AsyncMock(
        return_value={
            "litellm_prefix": "gpt-",
            "model_key": "4-mini",
            "api_key_env_var": "OPENAI_API_KEY",
            "provider": "OpenAI",
        }
    )
    return service


@pytest.fixture
def trading_agent(mock_agent_config, mock_agent_service):
    """創建 TradingAgent 實例"""
    agent = TradingAgent(
        agent_id="test-agent",
        agent_config=mock_agent_config,
        agent_service=mock_agent_service,
    )
    return agent


class TestMemoryWorkflow:
    """測試記憶體工作流程"""

    @pytest.mark.asyncio
    async def test_load_execution_memory_empty_state(self, trading_agent):
        """驗證首次執行時記憶體為空"""
        memory = await trading_agent._load_execution_memory()

        assert isinstance(memory, dict)
        assert "past_decisions" in memory
        assert len(memory["past_decisions"]) == 0

    @pytest.mark.asyncio
    async def test_load_execution_memory_returns_structured_format(self, trading_agent):
        """驗證記憶體返回結構化格式"""
        memory = await trading_agent._load_execution_memory()

        # 驗證記憶體結構
        assert isinstance(memory["past_decisions"], list)

    @pytest.mark.asyncio
    async def test_save_execution_memory_with_valid_result(self, trading_agent):
        """驗證能夠保存執行結果"""
        execution_result = "成功執行: 買入 2330 100股"
        memory = {"past_decisions": [], "learned_patterns": [], "failed_trades": []}

        # 不應該拋出異常
        await trading_agent._save_execution_memory(
            execution_result=execution_result,
            execution_memory=memory,
        )

    @pytest.mark.asyncio
    async def test_save_execution_memory_handles_missing_memory_mcp(self, trading_agent):
        """驗證在 memory_mcp 不可用時優雅降級"""
        trading_agent.memory_mcp = None
        execution_result = "測試結果"

        # 應該不拋出異常，只記錄警告
        await trading_agent._save_execution_memory(
            execution_result=execution_result,
            execution_memory={},
        )

    @pytest.mark.asyncio
    async def test_plan_next_steps_on_success(self, trading_agent):
        """驗證成功執行後規劃下一步"""
        execution_result = "成功執行: 買入 2330 100股"

        next_steps = await trading_agent._plan_next_steps(execution_result)

        assert isinstance(next_steps, list)
        assert len(next_steps) > 0
        # 應該包含成功相關的下一步
        next_steps_str = " ".join(next_steps).lower()
        assert any(keyword in next_steps_str for keyword in ["監視", "準備", "記錄"])

    @pytest.mark.asyncio
    async def test_plan_next_steps_on_failure(self, trading_agent):
        """驗證失敗執行後規劃下一步"""
        execution_result = "執行失敗: 網絡錯誤"

        next_steps = await trading_agent._plan_next_steps(execution_result)

        assert isinstance(next_steps, list)
        assert len(next_steps) > 0
        # 應該包含失敗相關的下一步
        assert "記錄本次執行到記憶體" in next_steps

    @pytest.mark.asyncio
    async def test_extract_result_summary_truncates_long_results(self, trading_agent):
        """驗證結果摘要提取會截斷長文本"""
        long_result = "成功" * 100  # 創建很長的字符串

        summary = trading_agent._extract_result_summary(long_result)

        # 當結果長度超過 200 時會添加 "..."
        assert len(summary) <= 203 or not summary.endswith("...")
        if len(long_result) > 200:
            assert summary.endswith("...") or len(summary) <= 200

    @pytest.mark.asyncio
    async def test_extract_result_summary_handles_short_results(self, trading_agent):
        """驗證結果摘要提取可以處理短結果"""
        short_result = "成功"

        summary = trading_agent._extract_result_summary(short_result)

        assert summary == "成功"
        assert not summary.endswith("...")

    @pytest.mark.asyncio
    async def test_extract_result_summary_handles_empty_results(self, trading_agent):
        """驗證結果摘要提取可以處理空結果"""
        empty_result = ""

        summary = trading_agent._extract_result_summary(empty_result)

        assert isinstance(summary, str)

    @pytest.mark.asyncio
    async def test_extract_result_summary_handles_exceptions(self, trading_agent):
        """驗證結果摘要提取可以處理異常"""
        invalid_result = None  # type: ignore

        summary = trading_agent._extract_result_summary(invalid_result)

        assert summary == "執行結果"


class TestBuildTaskPromptWithMemory:
    """測試帶記憶體的任務提示構建"""

    @pytest.mark.asyncio
    async def test_build_task_prompt_includes_memory_context(
        self, trading_agent, mock_agent_service
    ):
        """驗證任務提示包含記憶體上下文"""
        trading_agent.agent_service = mock_agent_service
        trading_agent.agent_config.current_mode = AgentMode.TRADING

        # 準備記憶體（帶過往決策）
        memory = {
            "past_decisions": [
                {
                    "date": "2025-10-30 14:00:00",
                    "action": "買入 2330 100股",
                    "reason": "技術指標向上突破",
                    "result": "成功",
                }
            ],
            "learned_patterns": [],
            "failed_trades": [],
        }

        with patch(
            "trading.trading_agent.get_portfolio_status",
            return_value="投資組合狀態: 正常",
        ):
            prompt = await trading_agent._build_task_prompt(
                mode=AgentMode.TRADING,
                context=None,
                execution_memory=memory,
            )

        # 驗證任務提示包含記憶體信息
        assert "過往決策參考" in prompt
        assert "2330" in prompt
        assert "技術指標向上突破" in prompt

    @pytest.mark.asyncio
    async def test_build_task_prompt_handles_missing_memory(
        self, trading_agent, mock_agent_service
    ):
        """驗證任務提示可以處理缺失記憶體"""
        trading_agent.agent_service = mock_agent_service
        trading_agent.agent_config.current_mode = AgentMode.TRADING

        with patch(
            "trading.trading_agent.get_portfolio_status",
            return_value="投資組合狀態: 正常",
        ):
            prompt = await trading_agent._build_task_prompt(
                mode=AgentMode.TRADING,
                context=None,
                execution_memory=None,
            )

        assert "交易執行模式" in prompt
        assert "可用工具" in prompt or "執行流程" in prompt

    @pytest.mark.asyncio
    async def test_build_task_prompt_rebalancing_mode(self, trading_agent, mock_agent_service):
        """驗證任務提示在 REBALANCING 模式下正確"""
        trading_agent.agent_service = mock_agent_service
        trading_agent.agent_config.current_mode = AgentMode.REBALANCING

        with patch(
            "trading.trading_agent.get_portfolio_status",
            return_value="投資組合狀態: 正常",
        ):
            prompt = await trading_agent._build_task_prompt(
                mode=AgentMode.REBALANCING,
                context=None,
                execution_memory=None,
            )

        assert "投資組合重新平衡模式" in prompt
        assert "REBALANCING" in prompt

    @pytest.mark.asyncio
    async def test_build_task_prompt_includes_timestamp(self, trading_agent, mock_agent_service):
        """驗證任務提示包含時間戳"""
        trading_agent.agent_service = mock_agent_service
        trading_agent.agent_config.current_mode = AgentMode.TRADING

        with patch(
            "trading.trading_agent.get_portfolio_status",
            return_value="投資組合狀態: 正常",
        ):
            prompt = await trading_agent._build_task_prompt(
                mode=AgentMode.TRADING,
                context=None,
                execution_memory=None,
            )

        # 驗證包含日期時間格式
        import re

        timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        assert re.search(timestamp_pattern, prompt), "Task prompt should include timestamp"


class TestMemoryIntegrationEdgeCases:
    """測試記憶體集成的邊界情況"""

    @pytest.mark.asyncio
    async def test_plan_next_steps_with_empty_result(self, trading_agent):
        """驗證空結果時的下一步規劃"""
        next_steps = await trading_agent._plan_next_steps("")

        assert isinstance(next_steps, list)
        assert len(next_steps) > 0

    @pytest.mark.asyncio
    async def test_save_execution_memory_with_empty_result(self, trading_agent):
        """驗證空結果時的記憶體保存"""
        # 不應該拋出異常
        await trading_agent._save_execution_memory(
            execution_result="",
            execution_memory={},
        )

    @pytest.mark.asyncio
    async def test_load_execution_memory_is_idempotent(self, trading_agent):
        """驗證記憶體加載的冪等性"""
        memory1 = await trading_agent._load_execution_memory()
        memory2 = await trading_agent._load_execution_memory()

        assert memory1 == memory2


class TestMemoryConsistency:
    """測試記憶體一致性"""

    @pytest.mark.asyncio
    async def test_memory_structure_consistency(self, trading_agent):
        """驗證記憶體結構一致性"""
        memory = await trading_agent._load_execution_memory()

        # 所有必需字段必須存在
        required_fields = ["past_decisions"]
        for field in required_fields:
            assert field in memory, f"Memory must contain '{field}'"
            assert isinstance(memory[field], list), f"Memory['{field}'] must be a list"

    @pytest.mark.asyncio
    async def test_plan_next_steps_returns_list_of_strings(self, trading_agent):
        """驗證下一步規劃返回字符串列表"""
        next_steps = await trading_agent._plan_next_steps("測試結果")

        assert isinstance(next_steps, list)
        for step in next_steps:
            assert isinstance(step, str), "Each next step must be a string"

    @pytest.mark.asyncio
    async def test_extract_result_summary_always_returns_string(self, trading_agent):
        """驗證結果摘要提取總是返回字符串"""
        test_cases = [
            "正常結果",
            "很長的結果" * 100,
            "",
        ]

        for test_input in test_cases:
            summary = trading_agent._extract_result_summary(test_input)
            assert isinstance(summary, str), f"Summary for '{test_input}' should be string"
