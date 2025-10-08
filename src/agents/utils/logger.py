"""統一 Logger 配置模組

提供專案統一的日誌記錄機制，支援：
- 結構化日誌輸出
- 檔案和控制台雙輸出
- 不同模組的日誌隔離
- 日誌等級控制
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class AgentLogger:
    """Agent 專用 Logger 包裝類"""

    # 預設日誌目錄
    LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"

    # 已初始化的 logger 快取
    _loggers: dict[str, logging.Logger] = {}

    # 日誌格式
    LOG_FORMAT = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def get_logger(
        cls,
        name: str,
        level: str = "INFO",
        enable_file: bool = True,
        enable_console: bool = True,
    ) -> logging.Logger:
        """取得或建立 Logger 實例

        Args:
            name: Logger 名稱，建議使用模組名稱
            level: 日誌等級 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_file: 是否輸出到檔案
            enable_console: 是否輸出到控制台

        Returns:
            logging.Logger: 設定好的 Logger 實例

        Example:
            >>> logger = AgentLogger.get_logger("technical_agent")
            >>> logger.info("分析開始")
            >>> logger.error("發生錯誤", exc_info=True)
        """
        # 如果已存在，直接返回
        if name in cls._loggers:
            return cls._loggers[name]

        # 建立新的 logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        logger.propagate = False  # 避免重複輸出

        # 清除現有 handlers（避免重複添加）
        logger.handlers.clear()

        # 建立 formatter
        formatter = logging.Formatter(cls.LOG_FORMAT, cls.DATE_FORMAT)

        # 控制台 handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # 檔案 handler
        if enable_file:
            cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

            # 依日期建立日誌檔案
            log_date = datetime.now().strftime("%Y%m%d")
            log_file = cls.LOG_DIR / f"agent_{log_date}.log"

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # 快取 logger
        cls._loggers[name] = logger
        return logger

    @classmethod
    def log_agent_call(
        cls,
        logger: logging.Logger,
        agent_name: str,
        operation: str,
        params: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        """記錄 Agent 呼叫日誌

        統一格式記錄 Agent 的操作，便於追蹤和除錯。

        Args:
            logger: Logger 實例
            agent_name: Agent 名稱
            operation: 操作名稱
            params: 輸入參數
            result: 執行結果
            error: 錯誤資訊（如果有）
        """
        log_msg = f"[{agent_name}] {operation}"

        if params:
            # 過濾敏感資訊
            safe_params = cls._sanitize_params(params)
            log_msg += f" | 參數: {safe_params}"

        if error:
            logger.error(f"{log_msg} | 失敗: {str(error)}", exc_info=True)
        elif result:
            # 簡化結果輸出
            result_summary = cls._summarize_result(result)
            logger.info(f"{log_msg} | 成功: {result_summary}")
        else:
            logger.info(log_msg)

    @classmethod
    def log_tool_execution(
        cls,
        logger: logging.Logger,
        tool_name: str,
        symbol: str | None = None,
        duration: float | None = None,
        success: bool = True,
        message: str = "",
    ) -> None:
        """記錄工具執行日誌

        Args:
            logger: Logger 實例
            tool_name: 工具名稱
            symbol: 股票代碼（如適用）
            duration: 執行時間（秒）
            success: 是否成功
            message: 附加訊息
        """
        status = "✓" if success else "✗"
        log_parts = [f"{status} [{tool_name}]"]

        if symbol:
            log_parts.append(f"股票: {symbol}")

        if duration is not None:
            log_parts.append(f"耗時: {duration:.3f}s")

        if message:
            log_parts.append(message)

        log_msg = " | ".join(log_parts)

        if success:
            logger.info(log_msg)
        else:
            logger.warning(log_msg)

    @staticmethod
    def _sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
        """過濾敏感參數

        Args:
            params: 原始參數

        Returns:
            dict: 過濾後的參數
        """
        sensitive_keys = {"password", "token", "api_key", "secret"}
        return {
            k: "***" if k.lower() in sensitive_keys else v for k, v in params.items()
        }

    @staticmethod
    def _summarize_result(result: dict[str, Any]) -> str:
        """簡化結果輸出

        避免日誌過於冗長。

        Args:
            result: 執行結果

        Returns:
            str: 簡化後的結果摘要
        """
        if isinstance(result, dict):
            if "error" in result:
                return f"錯誤: {result['error']}"

            # 提取關鍵資訊
            summary_keys = ["status", "signal", "recommendation", "score", "level"]
            summary = {k: v for k, v in result.items() if k in summary_keys}

            if summary:
                return str(summary)

            # 如果結果太大，只顯示鍵
            if len(result) > 5:
                return f"包含 {len(result)} 個欄位: {list(result.keys())[:5]}..."

            return str(result)

        return str(result)


# 便利函數：快速取得 logger
def get_agent_logger(name: str, level: str = "INFO") -> logging.Logger:
    """快速取得 Agent Logger

    Args:
        name: Logger 名稱
        level: 日誌等級

    Returns:
        logging.Logger: 設定好的 Logger

    Example:
        >>> from agents.utils.logger import get_agent_logger
        >>> logger = get_agent_logger("my_agent")
        >>> logger.info("開始執行")
    """
    return AgentLogger.get_logger(name, level)
