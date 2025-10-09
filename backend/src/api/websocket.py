"""
WebSocket 管理器

本模組負責管理 WebSocket 連線，並處理即時事件廣播。
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


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
        self, agent_id: str, status: str, details: dict[str, Any] | None = None
    ):
        """
        廣播代理人狀態變更事件。
        會將狀態與細節資料廣播給所有客戶端。
        """
        message = {
            "type": "agent_status",
            "agent_id": agent_id,
            "status": status,
            "data": details or {},
        }
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
            "error": error_message,
            "data": error_details or {},
        }
        await self.broadcast(message)


# 全域 WebSocket 管理器實例
websocket_manager = WebSocketManager()  # 供 API 其他模組直接使用
