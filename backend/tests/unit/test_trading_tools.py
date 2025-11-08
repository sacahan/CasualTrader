#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加 src 目錄到 Python 路徑
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

from trading.trading_agent import TradingAgent  # noqa: E402

"""測試交易工具功能"""


def test_trading_agent_creation():
    """測試 TradingAgent 創建"""
    agent = TradingAgent(agent_id="test_agent_001", agent_config=None, agent_service=None)
    assert agent is not None
    assert agent.agent_id == "test_agent_001"
