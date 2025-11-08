"""
WebSocket 管理器測試

測試 WebSocketManager 的所有功能，包括連線管理、消息廣播和錯誤處理。
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket, WebSocketDisconnect

from api.websocket import WebSocketManager, websocket_manager


class TestWebSocketManagerInitialization:
    """測試 WebSocket 管理器初始化"""

    def test_initialization(self):
        """測試：WebSocketManager 正確初始化"""
        manager = WebSocketManager()
        assert manager.active_connections == []
        assert manager._lock is not None

    @pytest.mark.asyncio
    async def test_startup(self):
        """測試：startup 方法初始化成功"""
        manager = WebSocketManager()
        await manager.startup()
        # 驗證初始化完成（不會拋出異常）
        assert manager is not None

    @pytest.mark.asyncio
    async def test_shutdown_empty(self):
        """測試：shutdown 時沒有活躍連線"""
        manager = WebSocketManager()
        await manager.shutdown()
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_shutdown_with_connections(self):
        """測試：shutdown 時正確關閉所有連線"""
        manager = WebSocketManager()

        # 創建模擬的 WebSocket 連線
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        manager.active_connections = [mock_ws1, mock_ws2]

        await manager.shutdown()

        # 驗證所有連線都被關閉
        mock_ws1.close.assert_called_once()
        mock_ws2.close.assert_called_once()

        # 驗證列表被清空
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_shutdown_handles_close_errors(self):
        """測試：shutdown 時處理連線關閉錯誤"""
        manager = WebSocketManager()

        # 創建會拋出異常的模擬 WebSocket
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.close.side_effect = Exception("Connection already closed")

        manager.active_connections = [mock_ws]

        # 不應該拋出異常
        await manager.shutdown()

        assert len(manager.active_connections) == 0


class TestWebSocketConnection:
    """測試連線管理"""

    @pytest.mark.asyncio
    async def test_connect(self):
        """測試：正確連線新的 WebSocket"""
        manager = WebSocketManager()
        mock_ws = AsyncMock(spec=WebSocket)

        await manager.connect(mock_ws)

        # 驗證 accept 被呼叫
        mock_ws.accept.assert_called_once()

        # 驗證連線被加入清單
        assert mock_ws in manager.active_connections
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_connect_multiple(self):
        """測試：同時連線多個 WebSocket"""
        manager = WebSocketManager()

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws3 = AsyncMock(spec=WebSocket)

        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)
        await manager.connect(mock_ws3)

        assert len(manager.active_connections) == 3
        assert mock_ws1 in manager.active_connections
        assert mock_ws2 in manager.active_connections
        assert mock_ws3 in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """測試：正確斷線 WebSocket"""
        manager = WebSocketManager()
        mock_ws = AsyncMock(spec=WebSocket)

        # 先連線
        await manager.connect(mock_ws)
        assert len(manager.active_connections) == 1

        # 再斷線
        await manager.disconnect(mock_ws)

        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_disconnect_non_existent(self):
        """測試：斷線不存在的連線（應該安全處理）"""
        manager = WebSocketManager()
        mock_ws = AsyncMock(spec=WebSocket)

        # 沒有先連線就斷線
        await manager.disconnect(mock_ws)

        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect(self):
        """測試：並發連線和斷線操作"""
        manager = WebSocketManager()
        mock_sockets = [AsyncMock(spec=WebSocket) for _ in range(5)]

        # 並發連線
        await asyncio.gather(*[manager.connect(ws) for ws in mock_sockets])
        assert len(manager.active_connections) == 5

        # 並發斷線
        await asyncio.gather(*[manager.disconnect(ws) for ws in mock_sockets])
        assert len(manager.active_connections) == 0


class TestWebSocketBroadcast:
    """測試消息廣播"""

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self):
        """測試：廣播訊息到多個客戶端"""
        manager = WebSocketManager()

        # 創建多個模擬 WebSocket
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws3 = AsyncMock(spec=WebSocket)

        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)
        await manager.connect(mock_ws3)

        # 廣播訊息
        message = {"type": "test", "data": "hello"}
        await manager.broadcast(message)

        # 驗證所有客戶端都收到訊息
        assert mock_ws1.send_text.call_count == 1
        assert mock_ws2.send_text.call_count == 1
        assert mock_ws3.send_text.call_count == 1

    @pytest.mark.asyncio
    async def test_broadcast_adds_timestamp(self):
        """測試：廣播時自動添加時間戳"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        message = {"type": "test"}
        await manager.broadcast(message)

        # 驗證 send_text 被呼叫
        assert mock_ws.send_text.call_count == 1

        # 驗證訊息包含時間戳
        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert "timestamp" in sent_message

    @pytest.mark.asyncio
    async def test_broadcast_preserves_existing_timestamp(self):
        """測試：如果訊息已含時間戳，則不覆蓋"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        original_timestamp = "2025-01-01T00:00:00"
        message = {"type": "test", "timestamp": original_timestamp}

        await manager.broadcast(message)

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["timestamp"] == original_timestamp

    @pytest.mark.asyncio
    async def test_broadcast_empty_connections(self):
        """測試：沒有客戶端時廣播應該安全返回"""
        manager = WebSocketManager()

        message = {"type": "test"}
        # 不應該拋出異常
        await manager.broadcast(message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_clients(self):
        """測試：廣播時處理已斷線的客戶端"""
        manager = WebSocketManager()

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws3 = AsyncMock(spec=WebSocket)

        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)
        await manager.connect(mock_ws3)

        # 設定 mock_ws2 拋出 WebSocketDisconnect
        mock_ws2.send_text.side_effect = WebSocketDisconnect(code=1000)

        message = {"type": "test"}
        await manager.broadcast(message)

        # 驗證斷線的客戶端被移除
        assert len(manager.active_connections) == 2
        assert mock_ws2 not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_handles_general_exceptions(self):
        """測試：廣播時處理其他異常"""
        manager = WebSocketManager()

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)

        # 設定 mock_ws1 拋出一般異常
        mock_ws1.send_text.side_effect = Exception("Network error")

        message = {"type": "test"}
        await manager.broadcast(message)

        # 驗證異常客戶端也被移除
        assert len(manager.active_connections) == 1
        assert mock_ws1 not in manager.active_connections


class TestWebSocketSendToClient:
    """測試發送訊息到指定客戶端"""

    @pytest.mark.asyncio
    async def test_send_to_client(self):
        """測試：成功發送訊息到指定客戶端"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        message = {"type": "test", "data": "hello"}
        await manager.send_to_client(mock_ws, message)

        # 驗證 send_json 被呼叫
        assert mock_ws.send_json.call_count == 1

        # 驗證訊息內容
        sent_message = mock_ws.send_json.call_args[0][0]
        assert sent_message["type"] == "test"
        assert sent_message["data"] == "hello"

    @pytest.mark.asyncio
    async def test_send_to_client_adds_timestamp(self):
        """測試：send_to_client 自動添加時間戳"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        message = {"type": "test"}
        await manager.send_to_client(mock_ws, message)

        sent_message = mock_ws.send_json.call_args[0][0]
        assert "timestamp" in sent_message

    @pytest.mark.asyncio
    async def test_send_to_client_error_disconnects(self):
        """測試：send_to_client 發生錯誤時自動斷線"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        # 設定 send_json 拋出異常
        mock_ws.send_json.side_effect = Exception("Send failed")

        message = {"type": "test"}
        await manager.send_to_client(mock_ws, message)

        # 驗證客戶端被斷線
        assert len(manager.active_connections) == 0


class TestWebSocketBroadcastEvents:
    """測試各種廣播事件方法"""

    @pytest.mark.asyncio
    async def test_broadcast_agent_status(self):
        """測試：broadcast_agent_status 方法"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        await manager.broadcast_agent_status(
            agent_id="agent-1",
            status="active",
            runtime_status="running",
            details={"profit": 100},
        )

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "agent_status"
        assert sent_message["agent_id"] == "agent-1"
        assert sent_message["status"] == "active"
        assert sent_message["runtime_status"] == "running"
        assert sent_message["data"]["profit"] == 100

    @pytest.mark.asyncio
    async def test_broadcast_trade_execution(self):
        """測試：broadcast_trade_execution 方法"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        trade_data = {"symbol": "2330", "quantity": 1000, "price": 500}
        await manager.broadcast_trade_execution(agent_id="agent-1", trade_data=trade_data)

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "trade_execution"
        assert sent_message["agent_id"] == "agent-1"
        assert sent_message["data"] == trade_data

    @pytest.mark.asyncio
    async def test_broadcast_strategy_change(self):
        """測試：broadcast_strategy_change 方法"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        change_data = {"strategy": "momentum", "threshold": 0.05}
        await manager.broadcast_strategy_change(agent_id="agent-1", change_data=change_data)

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "strategy_change"
        assert sent_message["data"] == change_data

    @pytest.mark.asyncio
    async def test_broadcast_portfolio_update(self):
        """測試：broadcast_portfolio_update 方法"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        portfolio_data = {
            "total_value": 50000,
            "cash": 10000,
            "positions": [{"symbol": "2330", "quantity": 100}],
        }
        await manager.broadcast_portfolio_update(agent_id="agent-1", portfolio_data=portfolio_data)

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "portfolio_update"
        assert sent_message["data"] == portfolio_data

    @pytest.mark.asyncio
    async def test_broadcast_performance_update(self):
        """測試：broadcast_performance_update 方法"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        performance_data = {"roi": 0.15, "sharpe_ratio": 1.5, "max_drawdown": 0.08}
        await manager.broadcast_performance_update(
            agent_id="agent-1", performance_data=performance_data
        )

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "performance_update"
        assert sent_message["data"] == performance_data

    @pytest.mark.asyncio
    async def test_broadcast_error(self):
        """測試：broadcast_error 方法"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        error_details = {"error_code": "INSUFFICIENT_FUNDS", "required": 50000, "available": 10000}
        await manager.broadcast_error(
            agent_id="agent-1",
            error_message="Insufficient funds",
            error_details=error_details,
        )

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "error"
        assert sent_message["agent_id"] == "agent-1"
        assert sent_message["error"] == "Insufficient funds"
        assert sent_message["data"] == error_details

    @pytest.mark.asyncio
    async def test_broadcast_error_without_details(self):
        """測試：broadcast_error 不提供詳細資訊"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        await manager.broadcast_error(agent_id="agent-1", error_message="Unknown error")

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "error"
        assert sent_message["data"] == {}


class TestWebSocketGlobalInstance:
    """測試全域 websocket_manager 實例"""

    def test_global_instance_exists(self):
        """測試：websocket_manager 全域實例存在"""
        assert websocket_manager is not None
        assert isinstance(websocket_manager, WebSocketManager)

    def test_global_instance_is_singleton(self):
        """測試：websocket_manager 在多次導入中是同一實例"""
        from api.websocket import websocket_manager as manager_import

        assert manager_import is websocket_manager


class TestWebSocketConcurrency:
    """測試並發操作的安全性"""

    @pytest.mark.asyncio
    async def test_concurrent_broadcast_and_connect(self):
        """測試：並發廣播和連線操作"""
        manager = WebSocketManager()

        mock_sockets = [AsyncMock(spec=WebSocket) for _ in range(5)]

        async def connect_and_broadcast():
            for ws in mock_sockets:
                await manager.connect(ws)
            for _ in range(3):
                await manager.broadcast({"type": "test"})

        # 執行並發操作
        await connect_and_broadcast()

        # 驗證所有連線都被保持
        assert len(manager.active_connections) == 5

    @pytest.mark.asyncio
    async def test_concurrent_disconnect_and_broadcast(self):
        """測試：並發斷線和廣播操作"""
        manager = WebSocketManager()

        mock_sockets = [AsyncMock(spec=WebSocket) for _ in range(5)]

        for ws in mock_sockets:
            await manager.connect(ws)

        async def disconnect_and_broadcast():
            # 並發斷線一些連線
            await asyncio.gather(*[manager.disconnect(mock_sockets[i]) for i in range(3)])
            # 繼續廣播
            await manager.broadcast({"type": "test"})

        await disconnect_and_broadcast()

        # 驗證正確的連線數
        assert len(manager.active_connections) == 2


class TestWebSocketJSONSerialization:
    """測試 JSON 序列化"""

    @pytest.mark.asyncio
    async def test_broadcast_with_custom_objects(self):
        """測試：廣播包含自訂物件的訊息"""
        manager = WebSocketManager()

        mock_ws = AsyncMock(spec=WebSocket)
        await manager.connect(mock_ws)

        # 訊息包含 datetime 物件
        now = datetime.now()
        message = {"type": "test", "timestamp": now, "data": {"value": 100}}

        await manager.broadcast(message)

        # 驗證訊息被序列化並發送
        assert mock_ws.send_text.call_count == 1
        sent_text = mock_ws.send_text.call_args[0][0]
        # 應該能被解析為 JSON
        parsed = json.loads(sent_text)
        assert parsed["type"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
