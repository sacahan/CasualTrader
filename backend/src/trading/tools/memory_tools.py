"""
Memory Tools - memory_mcp 操作的統一封裝

提供 Agent 與 memory_mcp 互動的高級接口，
類似 trading_tools.py 的設計方式。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from common.logger import logger


# ==========================================
# Memory MCP 工具函數
# ==========================================


async def load_execution_memory(
    memory_mcp,
    agent_id: str,
) -> str | None:
    """
    從 memory_mcp 加載過往 3 天的執行記憶體和決策

    Args:
        memory_mcp: memory_mcp 伺服器實例
        agent_id: Agent ID

    Returns:
        記憶體內容字串，若無記憶體則返回 None

    Example:
        {
            "entities": [
                {
                    "name": "trading_decision_buy_tsmc",
                    "entityType": "trading_decision",
                    "observations": [
                        "買入 TSMC 2330",
                        "數量 1000 股"
                    ]
                },
                {
                    "name": "trading_decision_sell_amd",
                    "entityType": "trading_decision",
                    "observations": [
                        "賣出 AMD",
                        "獲利了結"
                    ]
                },
                {
                    "name": "trading_decision_2025_01_15",
                    "entityType": "trading_decision",
                    "observations": [
                        "時間: 2025-01-15 10:30",
                        "決策: 買入 TSMC 2330",
                        "數量: 1000 股",
                        "目標價: 620 元",
                        "技術指標: RSI 35(超賣), MACD 正向交叉",
                        "理由: 基於市場分析和技術信號"
                    ]
                }
            ],
            "relations": []
        }
    """
    try:
        if not memory_mcp:
            logger.debug(f"Memory MCP not available for {agent_id}, returning empty memory")
            return None

        # 使用 search_nodes 工具查詢過往交易決定
        result = await memory_mcp.session.call_tool(
            "search_nodes",
            {
                "query": "trading_decision",
                "limit": 3,
            },
        )

        # 解析 memory_mcp 的回應
        if result and hasattr(result, "content") and result.content:
            content_item = result.content[0]
            text_content = content_item.text if hasattr(content_item, "text") else str(content_item)

            try:
                data = json.loads(text_content)
                entities = data.get("entities", [])

                # 轉換為記憶體格式 - 只取最近一筆決策
                past_decisions = [entity.get("observations", []) for entity in entities[:1]]

                logger.debug(
                    f"Loaded {len(past_decisions)} decisions from memory_mcp for {agent_id}"
                )

                memory_context = "\n**📚 過往決策參考：**\n"
                for i, decision in enumerate(past_decisions, 1):
                    memory_context += f"\n{i}. {decision}\n"
                    return memory_context

            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.warning(f"Failed to parse memory_mcp response for {agent_id}: {e}")
                return

        return None

    except Exception as e:
        logger.warning(f"Failed to load execution memory from memory_mcp: {e}")
        return None


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

        # 使用 create_entities 工具保存記憶體
        result = await memory_mcp.session.call_tool(
            "create_entities",
            {
                "entities": [
                    {
                        "name": f"{agent_id}@{datetime.now().isoformat()}",
                        "entityType": "trading_decision",
                        "observations": [execution_result],
                    }
                ]
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

        # 使用 search_nodes 工具查詢
        search_query = query or f"agent {agent_id} decision"

        result = await memory_mcp.session.call_tool(
            "search_nodes",
            {
                "query": search_query,
                "limit": limit,
            },
        )

        if result and hasattr(result, "content") and result.content:
            content_item = result.content[0]
            text_content = content_item.text if hasattr(content_item, "text") else str(content_item)

            try:
                data = json.loads(text_content)
                nodes = data.get("nodes", [])
                logger.info(f"Recalled {len(nodes)} decisions for {agent_id}")
                return nodes
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

        # Use read_graph to get all entities and filter old ones manually
        result = await memory_mcp.session.call_tool(
            "read_graph",
            {},
        )

        if result and hasattr(result, "content") and result.content:
            content_item = result.content[0]
            text_content = content_item.text if hasattr(content_item, "text") else str(content_item)

            try:
                data = json.loads(text_content)
                nodes = data.get("nodes", [])
                cutoff_time = datetime.now() - timedelta(days=days_old)

                deleted_count = 0
                for node in nodes:
                    # Only process nodes belonging to this agent
                    if f"agent_{agent_id}" not in node.get("name", ""):
                        continue

                    created_at_str = node.get("created_at", "")
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at < cutoff_time:
                            # Delete old entity
                            delete_result = await memory_mcp.session.call_tool(
                                "delete_entity",
                                {"name": node.get("name")},
                            )
                            if delete_result and hasattr(delete_result, "content"):
                                deleted_count += 1
                    except (ValueError, AttributeError):
                        continue

                logger.info(
                    f"Cleaned up {deleted_count} old memories (>{days_old} days) for {agent_id}"
                )
                return True

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse read_graph response for {agent_id}")
                return False

        logger.warning(f"Failed to clear old memories for {agent_id}")
        return False

    except Exception as e:
        logger.warning(f"Failed to clear old memories: {e}")
        return False
