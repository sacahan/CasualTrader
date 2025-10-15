"""POC TradingAgent - 基於 OpenAI Agents SDK 的簡化實作"""

from __future__ import annotations

import logging
from typing import Any

from agents import (
    Agent,
    ModelSettings,
    RunConfig,
    Runner,
    gen_trace_id,
    trace,
)
from agents.mcp import MCPServerStdio

logger = logging.getLogger(__name__)


class POCTradingAgent:
    """POC Trading Agent"""

    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_MAX_TURNS = 30

    MCP_SERVERS = [
        {
            "name": "casual_market",
            "command": "uvx",
            "args": [
                "--from",
                "/Users/sacahan/Documents/workspace/CasualMarket",
                "casual-market-mcp",
            ],
        }
    ]

    def __init__(self, agent_id: str, db_config: Any):
        self.agent_id = agent_id
        self.db_config = db_config
        self.name = db_config.name
        self.ai_model = db_config.ai_model
        self.instructions = db_config.instructions
        self.agent = None

    async def initialize(self):
        """Initialize agent"""
        servers = []
        for cfg in self.MCP_SERVERS:
            servers.append(
                MCPServerStdio(
                    name=cfg["name"], params={"command": cfg["command"], "args": cfg["args"]}
                )
            )

        self.agent = Agent(
            name=self.name,
            model=self.ai_model,
            instructions=self.instructions,
            mcp_servers=servers,
            model_settings=ModelSettings(temperature=0.7),
        )

    async def run(self, context: dict = None) -> dict:
        """Run agent"""
        trace_id = gen_trace_id()
        with trace(workflow_name="POC Agent", trace_id=trace_id):
            result = await Runner.run(
                self.agent, "分析台股市場", config=RunConfig(max_turns=self.DEFAULT_MAX_TURNS)
            )
            return {"success": True, "output": result.final_output, "trace_id": trace_id}
