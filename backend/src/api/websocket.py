"""
WebSocket 管理器

本模組負責管理 WebSocket 連線，並處理即時事件廣播。
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from common.logger import logger


class WebSocketManager:
    """
    WebSocket 連線管理類別。
    負責管理所有 WebSocket 連線，並提供事件廣播功能。
    """

    def __init__(self):
        """
        初始化 WebSocket 管理器。
        active_connections 儲存所有目前連線的 WebSocket 實例。
        _lock 用於確保多協程操作安全。
        """
        self.active_connections: list[WebSocket] = []  # 目前所有連線
        self._lock = asyncio.Lock()  # 協程鎖

    async def startup(self):
        """
        啟動時初始化管理器。
        僅記錄初始化訊息。
        """
        logger.info("WebSocket Manager initialized")

    async def shutdown(self):
        """
        關閉管理器時清理所有連線。
        逐一關閉所有 WebSocket，並清空連線列表。
        """
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")
            self.active_connections.clear()
        logger.info("WebSocket Manager shut down")

    async def connect(self, websocket: WebSocket):
        """
        接受新的 WebSocket 連線。
        先呼叫 accept()，再加入 active_connections。
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """
        移除指定 WebSocket 連線。
        若連線存在則移除，並記錄剩餘連線數。
        """
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]):
        """
        廣播訊息給所有已連線的客戶端。
        會自動補上 timestamp 欄位。
        若有斷線則移除。
        """
        if not self.active_connections:
            return

        # 若 message 未含 timestamp，則補上目前時間
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        message_text = json.dumps(message, default=str)  # 轉成 JSON 字串

        # 複製連線列表，避免迭代時被修改
        async with self._lock:
            connections = self.active_connections.copy()

        disconnected = []  # 記錄斷線的連線
        for connection in connections:
            try:
                await connection.send_text(message_text)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)

        # 移除斷線的客戶端
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)
            logger.info(f"Removed {len(disconnected)} disconnected clients")

    async def send_to_client(self, websocket: WebSocket, message: dict[str, Any]):
        """
        傳送訊息給指定客戶端。
        若發生錯誤則自動斷線。
        """
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            await self.disconnect(websocket)

    async def broadcast_agent_status(
        self,
        agent_id: str,
        status: str,
        runtime_status: str | None = None,
        details: dict[str, Any] | None = None,
        financial_data: dict[str, Any] | None = None,
    ):
        """
        廣播代理人狀態變更事件。
        會將持久化狀態、執行時狀態、財務數據與細節資料廣播給所有客戶端。

        Args:
            agent_id: Agent ID
            status: 持久化狀態 (active/inactive/error/suspended)
            runtime_status: 執行時狀態 (idle/running/stopped)
            details: 其他詳細資訊
            financial_data: 財務數據 (current_funds, total_portfolio_value, holdings_value 等)
        """
        message = {
            "type": "agent_status",
            "agent_id": agent_id,
            "status": status,
            "runtime_status": runtime_status,
            "data": details or {},
        }

        # 如果提供了財務數據，將其合併到消息中
        if financial_data:
            message["financial_data"] = financial_data

        await self.broadcast(message)

    async def broadcast_trade_execution(self, agent_id: str, trade_data: dict[str, Any]):
        """
        廣播代理人交易執行事件。
        會將交易資料廣播給所有客戶端。
        """
        message = {"type": "trade_execution", "agent_id": agent_id, "data": trade_data}
        await self.broadcast(message)

    async def broadcast_strategy_change(self, agent_id: str, change_data: dict[str, Any]):
        """
        廣播代理人策略變更事件。
        會將策略變更資料廣播給所有客戶端。
        """
        message = {"type": "strategy_change", "agent_id": agent_id, "data": change_data}
        await self.broadcast(message)

    async def broadcast_portfolio_update(self, agent_id: str, portfolio_data: dict[str, Any]):
        """
        廣播代理人投資組合更新事件。
        會將最新投資組合資料廣播給所有客戶端。
        """
        message = {
            "type": "portfolio_update",
            "agent_id": agent_id,
            "data": portfolio_data,
        }
        await self.broadcast(message)

    async def broadcast_performance_update(self, agent_id: str, performance_data: dict[str, Any]):
        """
        廣播代理人績效指標更新事件。
        會將最新績效資料廣播給所有客戶端。
        """
        message = {
            "type": "performance_update",
            "agent_id": agent_id,
            "data": performance_data,
        }
        await self.broadcast(message)

    async def broadcast_error(
        self,
        agent_id: str,
        error_message: str,
        error_details: dict[str, Any] | None = None,
    ):
        """
        廣播錯誤事件。
        會將錯誤訊息與細節廣播給所有客戶端。
        """
        message = {
            "type": "error",
            "agent_id": agent_id,
            "message": error_message,
            "details": error_details or {},
        }
        await self.broadcast(message)

    async def broadcast_execution_completed(
        self,
        agent_id: str,
        execution_time_ms: int,
        financial_data: dict[str, Any] | None = None,
    ):
        """
        廣播執行完成事件，包含完整的財務狀態。

        Args:
            agent_id: Agent ID
            execution_time_ms: 執行時間（毫秒）
            financial_data: 財務數據，包含：
                - current_funds: 當前資金
                - initial_funds: 初始資金
                - total_portfolio_value: 總投資組合價值
                - holdings_value: 持倉總市值
                - cash_percentage: 現金比例
                - stocks_percentage: 股票比例
        """
        message = {
            "type": "execution_completed",
            "agent_id": agent_id,
            "execution_time_ms": execution_time_ms,
        }

        if financial_data:
            message["financial_data"] = financial_data

        await self.broadcast(message)

    async def broadcast_execution_started(
        self,
        agent_id: str,
        session_id: str,
        mode: str,
    ):
        """
        廣播執行開始事件。

        Args:
            agent_id: Agent ID
            session_id: 會話 ID
            mode: 執行模式 (TRADING/REBALANCING)
        """
        message = {
            "type": "execution_started",
            "agent_id": agent_id,
            "session_id": session_id,
            "mode": mode,
        }
        await self.broadcast(message)

    async def broadcast_execution_failed(
        self,
        agent_id: str,
        error: str,
        financial_data: dict[str, Any] | None = None,
    ):
        """
        廣播執行失敗事件，包含財務狀態。

        Args:
            agent_id: Agent ID
            error: 錯誤訊息
            financial_data: 財務數據
        """
        message = {
            "type": "execution_failed",
            "agent_id": agent_id,
            "error": error,
        }

        if financial_data:
            message["financial_data"] = financial_data

        await self.broadcast(message)

    async def broadcast_execution_stopped(
        self,
        agent_id: str,
        status: str,
        financial_data: dict[str, Any] | None = None,
    ):
        """
        廣播執行停止事件，包含財務狀態。

        Args:
            agent_id: Agent ID
            status: 停止狀態
            financial_data: 財務數據
        """
        message = {
            "type": "execution_stopped",
            "agent_id": agent_id,
            "status": status,
        }

        if financial_data:
            message["financial_data"] = financial_data

        await self.broadcast(message)


# 全域 WebSocket 管理器實例
websocket_manager = WebSocketManager()  # 供 API 其他模組直接使用
