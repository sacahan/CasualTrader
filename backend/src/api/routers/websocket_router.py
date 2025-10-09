"""
WebSocket Router

WebSocket endpoint for real-time communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from ..websocket import websocket_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")

            # Echo back for now (can be extended for client commands)
            await websocket_manager.send_to_client(
                websocket, {"type": "pong", "data": {"received": data}}
            )

    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)
