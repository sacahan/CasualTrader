"""
錯誤處理模組。

提供統一的錯誤處理邏輯和異常轉換功能，確保 MCP 工具回應的一致性。
"""

import traceback
from typing import Any

from ..models.mcp_responses import MCPErrorCodes, MCPErrorResponse, MCPErrorTypes
from ..models.stock_data import APIError, ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MCPErrorHandler:
    """
    MCP 錯誤處理器。

    統一處理各種異常並轉換為標準化的 MCP 錯誤回應。
    """

    @staticmethod
    def handle_exception(
        exception: Exception, context: str = ""
    ) -> list[dict[str, Any]]:
        """
        處理異常並返回 MCP 格式的錯誤回應。

        Args:
            exception: 發生的異常
            context: 錯誤發生的上下文

        Returns:
            MCP 格式的錯誤回應列表
        """
        logger.error(f"處理異常: {type(exception).__name__}: {exception}")
        if context:
            logger.error(f"錯誤上下文: {context}")

        # 記錄完整的錯誤堆疊
        logger.debug(f"錯誤堆疊: {traceback.format_exc()}")

        try:
            # 根據異常類型決定處理方式
            if isinstance(exception, ValidationError):
                response = MCPErrorHandler._handle_validation_error(exception, context)
            elif isinstance(exception, APIError):
                response = MCPErrorHandler._handle_api_error(exception, context)
            elif isinstance(exception, (ConnectionError, TimeoutError)):
                response = MCPErrorHandler._handle_network_error(exception, context)
            elif isinstance(exception, ValueError):
                response = MCPErrorHandler._handle_value_error(exception, context)
            elif isinstance(exception, KeyError):
                response = MCPErrorHandler._handle_key_error(exception, context)
            else:
                response = MCPErrorHandler._handle_general_error(exception, context)

            return [{"type": "text", "text": response.text}]

        except Exception as handler_error:
            logger.error(f"錯誤處理器本身發生異常: {handler_error}")
            # 如果錯誤處理器本身失敗，回傳最基本的錯誤回應
            return [{"type": "text", "text": "❌ 系統發生未知錯誤，請稍後再試。"}]

    @staticmethod
    def _handle_validation_error(
        error: ValidationError, context: str
    ) -> MCPErrorResponse:
        """處理資料驗證錯誤。"""
        details = {
            "field": getattr(error, "field", "unknown"),
            "context": context,
            "original_message": str(error),
        }

        return MCPErrorResponse(
            error_code=MCPErrorCodes.INVALID_PARAMETERS,
            error_message=error.message,
            error_type=MCPErrorTypes.VALIDATION_ERROR,
            details=details,
        )

    @staticmethod
    def _handle_api_error(error: APIError, context: str) -> MCPErrorResponse:
        """處理 API 錯誤。"""
        details = {
            "status_code": getattr(error, "status_code", None),
            "response_data": getattr(error, "response_data", None),
            "context": context,
        }

        # 根據狀態碼決定錯誤類型和代碼
        status_code = getattr(error, "status_code", None)

        if status_code == 429:
            error_code = MCPErrorCodes.RATE_LIMIT_EXCEEDED
            error_type = MCPErrorTypes.RATE_LIMIT_ERROR
            message = "API 請求頻率過高，請稍後再試"
        elif status_code == 404:
            error_code = MCPErrorCodes.SYMBOL_NOT_FOUND
            error_type = MCPErrorTypes.SYMBOL_NOT_FOUND
            message = "找不到指定的股票代號"
        elif status_code == 503:
            error_code = MCPErrorCodes.API_UNAVAILABLE
            error_type = MCPErrorTypes.API_ERROR
            message = "API 服務暫時不可用"
        else:
            error_code = MCPErrorCodes.API_UNAVAILABLE
            error_type = MCPErrorTypes.API_ERROR
            message = f"API 呼叫失敗: {error.message}"

        return MCPErrorResponse(
            error_code=error_code,
            error_message=message,
            error_type=error_type,
            details=details,
        )

    @staticmethod
    def _handle_network_error(error: Exception, context: str) -> MCPErrorResponse:
        """處理網路連接錯誤。"""
        details = {
            "error_type": type(error).__name__,
            "context": context,
            "original_message": str(error),
        }

        if isinstance(error, TimeoutError):
            error_code = MCPErrorCodes.NETWORK_TIMEOUT
            error_type = MCPErrorTypes.TIMEOUT_ERROR
            message = "網路請求逾時，請檢查網路連線或稍後再試"
        else:
            error_code = MCPErrorCodes.API_UNAVAILABLE
            error_type = MCPErrorTypes.NETWORK_ERROR
            message = "網路連線發生問題，請檢查網路設定"

        return MCPErrorResponse(
            error_code=error_code,
            error_message=message,
            error_type=error_type,
            details=details,
        )

    @staticmethod
    def _handle_value_error(error: ValueError, context: str) -> MCPErrorResponse:
        """處理值錯誤。"""
        details = {"context": context, "original_message": str(error)}

        # 檢查是否為股票代號格式錯誤
        error_message = str(error).lower()
        if any(keyword in error_message for keyword in ["symbol", "代號", "格式"]):
            error_code = MCPErrorCodes.INVALID_SYMBOL
            message = "股票代號格式不正確，請輸入 4 位數字 (例如: 2330)"
        else:
            error_code = MCPErrorCodes.INVALID_PARAMETERS
            message = f"參數值錯誤: {error}"

        return MCPErrorResponse(
            error_code=error_code,
            error_message=message,
            error_type=MCPErrorTypes.VALIDATION_ERROR,
            details=details,
        )

    @staticmethod
    def _handle_key_error(error: KeyError, context: str) -> MCPErrorResponse:
        """處理鍵值錯誤 (通常是缺少必要參數)。"""
        missing_key = str(error).strip("'\"")
        details = {"missing_parameter": missing_key, "context": context}

        return MCPErrorResponse(
            error_code=MCPErrorCodes.INVALID_PARAMETERS,
            error_message=f"缺少必要參數: {missing_key}",
            error_type=MCPErrorTypes.VALIDATION_ERROR,
            details=details,
        )

    @staticmethod
    def _handle_general_error(error: Exception, context: str) -> MCPErrorResponse:
        """處理一般性錯誤。"""
        details = {
            "error_type": type(error).__name__,
            "context": context,
            "original_message": str(error),
            "traceback": traceback.format_exc()[:500],  # 限制長度
        }

        return MCPErrorResponse(
            error_code=MCPErrorCodes.INTERNAL_SERVER_ERROR,
            error_message="系統發生內部錯誤，請稍後再試",
            error_type=MCPErrorTypes.GENERAL_ERROR,
            details=details,
        )

    @staticmethod
    def create_user_friendly_error(
        error_code: str,
        user_message: str,
        technical_details: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        建立使用者友善的錯誤回應。

        Args:
            error_code: 錯誤代碼
            user_message: 使用者友善的錯誤訊息
            technical_details: 技術詳細資訊

        Returns:
            MCP 格式的錯誤回應
        """
        # 根據錯誤代碼提供建議解決方案
        suggestions = MCPErrorHandler._get_error_suggestions(error_code)

        details = technical_details or {}
        if suggestions:
            details["suggestions"] = suggestions

        response = MCPErrorResponse(
            error_code=error_code, error_message=user_message, details=details
        )

        return [{"type": "text", "text": response.text}]

    @staticmethod
    def _get_error_suggestions(error_code: str) -> list[str]:
        """
        根據錯誤代碼提供解決建議。

        Args:
            error_code: 錯誤代碼

        Returns:
            建議解決方案列表
        """
        suggestions = {
            MCPErrorCodes.INVALID_SYMBOL: [
                "請確認股票代號是 4 位數字",
                "常見股票代號範例: 2330 (台積電), 2317 (鴻海)",
                "可到證交所網站查詢正確的股票代號",
            ],
            MCPErrorCodes.SYMBOL_NOT_FOUND: [
                "請檢查股票代號是否正確",
                "該股票可能已下市或暫停交易",
                "請嘗試查詢其他股票",
            ],
            MCPErrorCodes.RATE_LIMIT_EXCEEDED: [
                "請稍等片刻後再試",
                "避免短時間內大量查詢",
                "可考慮使用批次查詢減少請求次數",
            ],
            MCPErrorCodes.NETWORK_TIMEOUT: [
                "請檢查網路連線狀態",
                "稍後再試一次",
                "如問題持續，請聯繫系統管理員",
            ],
            MCPErrorCodes.API_UNAVAILABLE: [
                "API 服務可能正在維護",
                "請稍後再試",
                "如需緊急查詢，請使用其他股價查詢管道",
            ],
        }

        return suggestions.get(
            error_code, ["如問題持續發生，請聯繫技術支援", "請檢查輸入參數是否正確"]
        )


def safe_execute(func, *args, **kwargs):
    """
    安全執行函數，自動處理異常。

    Args:
        func: 要執行的函數
        *args: 函數位置參數
        **kwargs: 函數關鍵字參數

    Returns:
        函數執行結果或錯誤回應
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        context = f"執行函數 {func.__name__}"
        return MCPErrorHandler.handle_exception(e, context)


def log_error_metrics(error_code: str, error_type: str, context: str = ""):
    """
    記錄錯誤指標用於監控和分析。

    Args:
        error_code: 錯誤代碼
        error_type: 錯誤類型
        context: 錯誤上下文
    """
    logger.info(
        f"ERROR_METRIC | code={error_code} | type={error_type} | context={context}"
    )


# 錯誤回應範本
ERROR_RESPONSE_TEMPLATES = {
    "invalid_symbol": {
        "message": "股票代號格式不正確",
        "help": "請輸入 4 位數字的台灣股票代號 (例如: 2330)",
    },
    "symbol_not_found": {
        "message": "找不到指定的股票",
        "help": "請確認股票代號是否正確，或該股票是否仍在交易",
    },
    "api_error": {
        "message": "無法取得股價資訊",
        "help": "請稍後再試，或檢查網路連線狀態",
    },
    "rate_limit": {"message": "查詢頻率過高", "help": "請稍等片刻後再查詢"},
    "network_error": {"message": "網路連線問題", "help": "請檢查網路設定或稍後再試"},
}
