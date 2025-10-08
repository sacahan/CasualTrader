"""
WebSocket Manager

Handles WebSocket connections and real-time event broadcasting.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class WebSocketManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def startup(self):
        """Initialize manager on startup."""
        logger.info("WebSocket Manager initialized")

    async def shutdown(self):
        """Cleanup on shutdown."""
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")
            self.active_connections.clear()
        logger.info("WebSocket Manager shut down")

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        message_text = json.dumps(message, default=str)

        # Create a copy of connections to avoid modification during iteration
        async with self._lock:
            connections = self.active_connections.copy()

        disconnected = []
        for connection in connections:
            try:
                await connection.send_text(message_text)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)
            logger.info(f"Removed {len(disconnected)} disconnected clients")

    async def send_to_client(self, websocket: WebSocket, message: dict[str, Any]):
        """Send message to a specific client."""
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
        """Broadcast agent status change."""
        message = {
            "type": "agent_status",
            "agent_id": agent_id,
            "status": status,
            "data": details or {},
        }
        await self.broadcast(message)

    async def broadcast_trade_execution(
        self, agent_id: str, trade_data: dict[str, Any]
    ):
        """Broadcast trade execution event."""
        message = {"type": "trade_execution", "agent_id": agent_id, "data": trade_data}
        await self.broadcast(message)

    async def broadcast_strategy_change(
        self, agent_id: str, change_data: dict[str, Any]
    ):
        """Broadcast strategy change event."""
        message = {"type": "strategy_change", "agent_id": agent_id, "data": change_data}
        await self.broadcast(message)

    async def broadcast_portfolio_update(
        self, agent_id: str, portfolio_data: dict[str, Any]
    ):
        """Broadcast portfolio update."""
        message = {
            "type": "portfolio_update",
            "agent_id": agent_id,
            "data": portfolio_data,
        }
        await self.broadcast(message)

    async def broadcast_performance_update(
        self, agent_id: str, performance_data: dict[str, Any]
    ):
        """Broadcast performance metrics update."""
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
        """Broadcast error event."""
        message = {
            "type": "error",
            "agent_id": agent_id,
            "error": error_message,
            "data": error_details or {},
        }
        await self.broadcast(message)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
