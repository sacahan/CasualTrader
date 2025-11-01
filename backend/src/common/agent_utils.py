"""
Agent 通用工具函數

提供符合 OpenAI Agents SDK 標準的 Agent 操作工具。
"""

from __future__ import annotations

import os
from pathlib import Path

from agents import Agent
from agents.extensions.visualization import draw_graph
from dotenv import load_dotenv

from common.logger import logger

load_dotenv()

SKIP_AGENT_GRAPH = os.getenv("SKIP_AGENT_GRAPH", "true").lower() == "true"


def save_agent_graph(
    agent: Agent,
    agent_id: str,
    output_dir: Path | str | None = None,
) -> tuple[bool, str]:
    """
    繪製並保存符合 OpenAI Agents SDK 標準的 Agent 結構圖

    通用工具函數，可用於任何符合 OpenAI Agent SDK 標準的 Agent 實例。
    將 Agent 的結構圖保存為 SVG 文件。

    Args:
        agent: OpenAI Agents SDK 的 Agent 實例
        agent_id: Agent 的唯一識別符（用於文件命名）
        output_dir: 輸出目錄路徑
                   - 若為 None，使用 backend/logs
                   - 若為相對路徑，相對於 backend 目錄
                   - 若為絕對路徑，直接使用

    Returns:
        tuple[bool, str]: (成功標誌, 文件路徑或錯誤訊息)
                         - 成功時: (True, "完整的SVG文件路徑")
                         - 失敗時: (False, "錯誤訊息")

    Example:
        >>> # 簡單使用（使用預設 logs 目錄）
        >>> success, result = save_agent_graph(agent, "my_agent")
        >>> if success:
        ...     print(f"Graph saved to: {result}")
        >>> else:
        ...     print(f"Error: {result}")

        >>> # 自訂輸出目錄
        >>> success, result = save_agent_graph(
        ...     agent,
        ...     "my_agent",
        ...     output_dir="/custom/path"
        ... )

    Raises:
        TypeError: Agent 不是 OpenAI Agents SDK 的 Agent 實例
    """

    if SKIP_AGENT_GRAPH:
        logger.info("Skipping agent graph generation as per configuration.")
        return True, "Agent graph generation skipped."

    try:
        # 驗證 agent 是否為正確的類型
        if not isinstance(agent, Agent):
            error_msg = f"Expected OpenAI Agents SDK Agent instance, got {type(agent).__name__}"
            logger.warning(f"Failed to generate agent graph: {error_msg}")
            return False, error_msg

        # 決定輸出目錄
        if output_dir is None:
            # 使用預設的 backend/logs 目錄
            current_file = Path(__file__).resolve()
            backend_root = current_file.parent.parent.parent
            output_path = backend_root / "logs"
        else:
            output_path = Path(output_dir)

            # 若為相對路徑，相對於 backend 目錄
            if not output_path.is_absolute():
                current_file = Path(__file__).resolve()
                backend_root = current_file.parent.parent.parent
                output_path = backend_root / output_path

        # 確保輸出目錄存在
        output_path.mkdir(parents=True, exist_ok=True)

        # 構建完整的圖形文件路徑（不含副檔名，draw_graph 會自動添加 .svg）
        graph_filepath = output_path / agent_id

        # 繪製並保存圖形
        draw_graph(agent, filename=str(graph_filepath))

        # 完整路徑（加上副檔名）
        full_filepath = str(graph_filepath) + ".svg"

        logger.info(f"Agent graph saved: {full_filepath}")
        return True, full_filepath

    except TypeError as type_error:
        error_msg = f"Invalid agent type: {type_error}"
        logger.warning(f"Failed to generate agent graph: {error_msg}")
        return False, error_msg

    except Exception as graph_error:
        error_msg = str(graph_error)
        logger.warning(f"Failed to generate agent graph: {error_msg}")
        return False, error_msg


__all__ = ["save_agent_graph"]
