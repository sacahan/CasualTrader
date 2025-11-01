"""
測試 TradingAgent 內部的 AgentMode 正規化與持久記憶保存流程

確保當資料庫欄位以字串型態提供 current_mode 時，不會因為使用 .value 而拋出例外。
"""

import asyncio

from common.enums import AgentMode
from trading.trading_agent import TradingAgent


class _DummyConfig:
    def __init__(self, current_mode):
        self.current_mode = current_mode


def test_normalize_agent_mode_accepts_string():
    """字串型模式應被正規化為 Enum。"""
    agent = TradingAgent(agent_id="test-agent", agent_config=_DummyConfig("TRADING"))
    enum_mode = agent._normalize_agent_mode("TRADING")
    assert enum_mode is AgentMode.TRADING

    enum_mode2 = agent._normalize_agent_mode("rebalancing")
    assert enum_mode2 is AgentMode.REBALANCING


def test_mode_to_str_for_variants():
    """_mode_to_str 應回傳正確的模式字串，不論輸入為 Enum 或字串。"""
    agent = TradingAgent(agent_id="test-agent", agent_config=_DummyConfig("TRADING"))
    assert agent._mode_to_str(AgentMode.TRADING) == "TRADING"
    assert agent._mode_to_str("TRADING") == "TRADING"
    assert agent._mode_to_str("rebalancing") == "REBALANCING"


def test_save_execution_memory_with_string_mode(monkeypatch):
    """
    當 agent_config.current_mode 為字串時，_save_execution_memory 不應該拋出 .value 相關錯誤，
    並且會以字串模式傳遞給 save_execution_memory。
    """

    # Arrange
    agent = TradingAgent(agent_id="test-agent", agent_config=_DummyConfig("TRADING"))

    captured = {}

    async def _fake_save(memory_mcp, agent_id, execution_result, mode=None):
        captured["memory_mcp"] = memory_mcp
        captured["agent_id"] = agent_id
        captured["execution_result"] = execution_result
        captured["mode"] = mode
        return None

    # 以 monkeypatch 將模組函式替換為假實作
    import trading.trading_agent as agent_mod

    # 注意：trading_agent 直接 from .tools.memory_tools import save_execution_memory
    # 因此需要在 trading_agent 模組命名空間中打補丁
    monkeypatch.setattr(agent_mod, "save_execution_memory", _fake_save, raising=True)

    # Act
    asyncio.run(agent._save_execution_memory("done", execution_memory=None))

    # Assert
    assert captured["agent_id"] == "test-agent"
    assert captured["execution_result"] == "done"
    # 應傳入標準化後的字串值
    assert captured["mode"] == "TRADING"
