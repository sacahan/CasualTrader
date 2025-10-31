"""
Memory Tools - memory_mcp 操作的統一封裝

提供 Agent 與 memory_mcp 互動的高級接口，
類似 trading_tools.py 的設計方式。
"""

from __future__ import annotations

import json
from typing import Any

from common.logger import logger


# ==========================================
# Memory MCP 工具函數
# ==========================================


async def load_execution_memory(
    memory_mcp,
    agent_id: str,
) -> dict[str, Any]:
    """
    從 memory_mcp 加載過往 3 天的執行記憶體和決策

    Args:
        memory_mcp: memory_mcp 伺服器實例
        agent_id: Agent ID

    Returns:
        執行記憶體字典，包含 past_decisions 列表

    Example:
        memory = await load_execution_memory(memory_mcp, "agent_123")
        # 返回: {"past_decisions": [...]}
    """
    try:
        if not memory_mcp:
            logger.debug(f"Memory MCP not available for {agent_id}, returning empty memory")
            return {"past_decisions": []}

        # 使用 memory_mcp 工具查詢過往 3 天的記憶體
        result = await memory_mcp.session.call_tool(
            "recall",
            {
                "agent_id": agent_id,
                "query": "過去3天的交易決策和執行結果",
                "limit": 10,
            },
        )

        # 解析 memory_mcp 的回應
        if result and hasattr(result, "content") and result.content:
            content_item = result.content[0]
            text_content = content_item.text if hasattr(content_item, "text") else str(content_item)

            try:
                data = json.loads(text_content)
                memories = data.get("memories", [])

                # 轉換為記憶體格式
                past_decisions = [
                    {
                        "date": memory.get("timestamp", ""),
                        "action": memory.get("action", ""),
                        "reason": memory.get("reason", ""),
                        "result": memory.get("result", ""),
                    }
                    for memory in memories
                ]

                logger.info(
                    f"Loaded {len(past_decisions)} decisions from memory_mcp for {agent_id}"
                )

                return {"past_decisions": past_decisions}

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse memory_mcp response for {agent_id}")
                return {"past_decisions": []}

        return {"past_decisions": []}

    except Exception as e:
        logger.warning(f"Failed to load execution memory from memory_mcp: {e}")
        return {"past_decisions": []}


async def save_execution_memory(
    memory_mcp,
    agent_id: str,
    execution_result: str,
    mode: str | None = None,
) -> bool:
    """
    將本次執行結果保存到 memory_mcp

    Args:
        memory_mcp: memory_mcp 伺服器實例
        agent_id: Agent ID
        execution_result: 本次執行的結果
        mode: Agent 執行模式（可選）

    Returns:
        是否保存成功

    Example:
        success = await save_execution_memory(
            memory_mcp,
            "agent_123",
            "買入 2330 100股，技術指標看好"
        )
    """
    try:
        if not memory_mcp:
            logger.debug(f"Memory MCP not available for {agent_id}, skipping memory save")
            return False

        # 準備執行記錄
        execution_record = {
            "agent_id": agent_id,
            "mode": mode or "unknown",
            "result_summary": execution_result[:200] + "..."
            if len(execution_result) > 200
            else execution_result,
        }

        # 使用 memory_mcp 工具保存記憶體
        result = await memory_mcp.session.call_tool(
            "memorize",
            {
                "agent_id": agent_id,
                "content": json.dumps(execution_record),
                "tags": ["execution", mode or "general"],
            },
        )

        if result and hasattr(result, "content"):
            logger.info(f"Execution memory saved for {agent_id}")
            return True

        logger.warning(f"Failed to save execution memory for {agent_id}: invalid response")
        return False

    except Exception as e:
        logger.warning(f"Failed to save execution memory to memory_mcp: {e}")
        return False


async def recall_recent_decisions(
    memory_mcp,
    agent_id: str,
    query: str | None = None,
    days: int = 3,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    從 memory_mcp 回憶最近的決策

    Args:
        memory_mcp: memory_mcp 伺服器實例
        agent_id: Agent ID
        query: 查詢查詢（可選），例如 "買入決策"
        days: 回顧天數（預設 3 天）
        limit: 返回決策數量限制（預設 10）

    Returns:
        決策列表

    Example:
        decisions = await recall_recent_decisions(
            memory_mcp,
            "agent_123",
            query="買入決策",
            days=7
        )
    """
    try:
        if not memory_mcp:
            logger.debug(f"Memory MCP not available for {agent_id}")
            return []

        # 使用 memory_mcp 工具查詢
        result = await memory_mcp.session.call_tool(
            "recall",
            {
                "agent_id": agent_id,
                "query": query or f"過去{days}天的決策",
                "limit": limit,
            },
        )

        if result and hasattr(result, "content") and result.content:
            content_item = result.content[0]
            text_content = content_item.text if hasattr(content_item, "text") else str(content_item)

            try:
                data = json.loads(text_content)
                memories = data.get("memories", [])
                logger.info(f"Recalled {len(memories)} decisions for {agent_id}")
                return memories
            except json.JSONDecodeError:
                logger.warning("Failed to parse memory_mcp response")
                return []

        return []

    except Exception as e:
        logger.warning(f"Failed to recall decisions: {e}")
        return []


async def clear_old_memories(
    memory_mcp,
    agent_id: str,
    days_old: int = 30,
) -> bool:
    """
    清理 agent 超過指定天數的記憶體

    Args:
        memory_mcp: memory_mcp 伺服器實例
        agent_id: Agent ID
        days_old: 清理超過此天數的記憶體（預設 30 天）

    Returns:
        是否清理成功

    Example:
        success = await clear_old_memories(memory_mcp, "agent_123", days_old=30)
    """
    try:
        if not memory_mcp:
            logger.debug(f"Memory MCP not available for {agent_id}")
            return False

        result = await memory_mcp.session.call_tool(
            "forget",
            {
                "agent_id": agent_id,
                "older_than_days": days_old,
            },
        )

        if result and hasattr(result, "content"):
            logger.info(f"Cleaned up old memories (>{days_old} days) for {agent_id}")
            return True

        logger.warning(f"Failed to clear old memories for {agent_id}")
        return False

    except Exception as e:
        logger.warning(f"Failed to clear old memories: {e}")
        return False
