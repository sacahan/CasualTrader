"""
統一的 Logger 配置

使用 loguru 作為統一的日誌解決方案，並提供標準 logging 的兼容性。

Features:
- 彩色 console 輸出
- 文件日誌輪轉
- 標準 logging 模組的攔截器
- 結構化日誌格式
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger

# 禁用 LiteLLM 的詳細輸出 - 使用官方推薦的環境變數方式
# 根據 LiteLLM 官方文檔：https://github.com/BerriAI/litellm
os.environ["LITELLM_LOG"] = "ERROR"  # 禁用詳細日誌
os.environ["LITELLM_DROP_PARAMS"] = "True"  # 拋下不支援的參數以避免警告

# ==========================================
# Logger 配置
# ==========================================


def _filter_noisy_loggers(record):
    """
    過濾掉不需要的第三方庫日誌

    Returns:
        bool: True 表示保留日誌，False 表示過濾掉
    """
    # 過濾掉 aiosqlite 的 DEBUG 日誌
    if record["name"].startswith("aiosqlite") and record["level"].name == "DEBUG":
        return False

    # 過濾掉 sqlite3 相關的 DEBUG 日誌
    if "sqlite" in record["name"].lower() and record["level"].name == "DEBUG":
        return False

    # 過濾掉 httpcore._trace 的 DEBUG 日誌
    if record["name"].startswith("httpcore._trace") and record["level"].name == "DEBUG":
        return False

    # 過濾掉 OpenAI SDK 的 DEBUG 日誌
    if record["name"].startswith("openai") and record["level"].name == "DEBUG":
        return False

    # 過濾掉 httpx 和 httpcore 的 DEBUG 日誌
    if record["name"].startswith(("httpx", "httpcore")) and record["level"].name == "DEBUG":
        return False

    # 過濾掉 agents SDK 的 DEBUG 日誌
    if record["name"].startswith("agents") and record["level"].name == "DEBUG":
        return False

    # 過濾掉 litellm 的 DEBUG 日誌
    if record["name"].startswith("litellm") and record["level"].name == "DEBUG":
        return False

    return True


def setup_logger(
    log_level: str = "INFO",
    log_file: Path | None = None,
    rotation: str = "100 MB",
    retention: str = "30 days",
    enable_console: bool = True,
) -> None:
    """
    設置統一的 logger 配置

    Args:
        log_level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日誌文件路徑（可選）
        rotation: 日誌輪轉條件
        retention: 日誌保留期限
        enable_console: 是否啟用 console 輸出
    """
    # 移除預設的 handler
    logger.remove()

    # Console handler - 彩色輸出
    if enable_console:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
            filter=_filter_noisy_loggers,  # 添加過濾器
        )

    # File handler - JSON 格式
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True,  # 非同步寫入
            filter=_filter_noisy_loggers,  # 添加過濾器
        )

    logger.info(f"Logger initialized with level: {log_level}")
    if log_file:
        logger.info(f"Logging to file: {log_file}")


def intercept_standard_logging() -> None:
    """
    攔截標準 logging 模組的日誌，重定向到 loguru

    這樣可以讓使用 logging.getLogger() 的代碼也輸出到 loguru
    """
    import logging

    class InterceptHandler(logging.Handler):
        """攔截標準 logging 並重定向到 loguru"""

        def emit(self, record: logging.LogRecord) -> None:
            # 獲取對應的 loguru level
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # 找到呼叫者的 frame
            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # 設置根 logger
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 攔截第三方套件的 logger
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "sqlalchemy"]:
        logging.getLogger(name).handlers = [InterceptHandler()]

    # 提高第三方套件的日誌級別，避免過多的 DEBUG 訊息
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("agents").setLevel(logging.WARNING)  # Agents SDK 日誌級別調整為 WARNING


# ==========================================
# 便利的 logger 實例
# ==========================================


def get_logger(name: str | None = None):
    """
    獲取 logger 實例

    Args:
        name: logger 名稱（可選）

    Returns:
        logger 實例

    Usage:
        from common.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Hello")
    """
    if name:
        return logger.bind(name=name)
    return logger


# 預設初始化
_default_log_file = Path(__file__).parent.parent.parent / "logs" / "backend.log"
setup_logger(log_level="INFO", log_file=_default_log_file)
intercept_standard_logging()

# 匯出給其他模組使用
__all__ = ["logger", "setup_logger", "intercept_standard_logging", "get_logger"]
