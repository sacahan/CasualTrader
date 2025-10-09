"""
Portfolio Queries - Real database portfolio query functions

Based on actual database schema:
- Agent (agents table)
- AgentHolding (agent_holdings table)
- Transaction (transactions table)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.models import Agent, AgentHolding, Transaction, TransactionAction


class PortfolioQueries:
    """Portfolio query functions using real database"""

    def __init__(self, db_session: AsyncSession, mcp_client=None):
        self.db_session = db_session
        self.mcp_client = mcp_client
        self.logger = logging.getLogger("portfolio_queries")

    async def get_portfolio_summary(self, agent_id: str) -> dict[str, Any]:
        """Get portfolio summary from database"""
        try:
            agent = await self._get_agent(agent_id)
            if not agent:
                return {
                    "agent_id": agent_id,
                    "error": "Agent not found",
                    "num_positions": 0,
                    "cash_balance": 0.0,
                }

            positions = await self._get_positions_data(agent_id)
            cash_balance = await self._get_cash_balance(agent_id, agent.initial_funds)
            total_market_value = sum(p["market_value"] for p in positions)
            total_cost = sum(p["quantity"] * p["average_cost"] for p in positions)
            unrealized_pnl = total_market_value - total_cost

            return {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "num_positions": len(positions),
                "positions": positions,
                "cash_balance": cash_balance,
                "total_market_value": total_market_value,
                "total_value": cash_balance + total_market_value,
                "unrealized_pnl": unrealized_pnl,
            }
        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            raise

    async def _get_agent(self, agent_id: str) -> Agent | None:
        stmt = select(Agent).where(Agent.id == agent_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_positions_data(self, agent_id: str) -> list[dict]:
        stmt = select(AgentHolding).where(
            AgentHolding.agent_id == agent_id, AgentHolding.quantity > 0
        )
        result = await self.db_session.execute(stmt)
        holdings = result.scalars().all()

        positions = []
        for h in holdings:
            price = float(h.average_cost)
            if self.mcp_client:
                try:
                    data = await self.mcp_client.get_stock_price(h.symbol)
                    if data:
                        price = data.get("current_price", price)
                except Exception:
                    pass

            positions.append(
                {
                    "symbol": h.symbol,
                    "quantity": h.quantity,
                    "average_cost": float(h.average_cost),
                    "current_price": price,
                    "market_value": h.quantity * price,
                }
            )
        return positions

    async def _get_cash_balance(self, agent_id: str, initial: Decimal) -> float:
        from ...database.models import TransactionStatus

        stmt = select(Transaction).where(
            Transaction.agent_id == agent_id,
            Transaction.status == TransactionStatus.EXECUTED.value,
        )
        result = await self.db_session.execute(stmt)
        txns = result.scalars().all()

        balance = float(initial)
        for t in txns:
            if t.action == TransactionAction.BUY:
                balance -= float(t.total_amount) + float(t.commission)
            elif t.action == TransactionAction.SELL:
                balance += float(t.total_amount) - float(t.commission)
        return balance
