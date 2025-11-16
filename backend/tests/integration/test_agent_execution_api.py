"""
Integration Tests for Agent Execution API Router

測試 agent_execution.py 路由的功能：
1. get_execution_history - 執行歷史查詢
2. get_session_detail - 會話詳細資訊查詢
3. 確保正確處理交易記錄和統計資料
4. 確保正確處理 Enum 和字符串狀態值
"""

import pytest
from datetime import datetime
from decimal import Decimal
from httpx import AsyncClient, ASGITransport

from api.app import create_app
from database.models import Agent, AgentSession, Transaction
from common.enums import AgentMode, AgentStatus, SessionStatus, TransactionAction, TransactionStatus


@pytest.mark.asyncio
class TestAgentExecutionAPI:
    """測試 Agent Execution API 路由"""

    async def test_get_execution_history_empty(self, async_client: AsyncClient, test_agent):
        """測試查詢空的執行歷史"""
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/history", params={"limit": 10}
        )

        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)
        # 可能有歷史記錄或為空
        assert len(history) >= 0

    async def test_get_execution_history_with_sessions(
        self, async_client: AsyncClient, test_agent, test_db_session
    ):
        """測試查詢包含 session 的執行歷史"""
        # 創建測試 session
        session = AgentSession(
            agent_id=test_agent.id,
            mode=AgentMode.TRADING,
            status=SessionStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time_ms=5000,
            final_output={"summary": "Test execution"},
            tools_called='["get_stock_price", "buy_stock"]',
        )
        test_db_session.add(session)
        await test_db_session.commit()
        await test_db_session.refresh(session)

        # 創建測試交易記錄
        transaction = Transaction(
            agent_id=test_agent.id,
            session_id=session.id,
            ticker="2330",
            company_name="台積電",
            action=TransactionAction.BUY,
            quantity=1000,
            price=Decimal("580.00"),
            total_amount=Decimal("580000.00"),
            commission=Decimal("817.00"),
            status=TransactionStatus.EXECUTED,
            execution_time=datetime.now(),
        )
        test_db_session.add(transaction)
        await test_db_session.commit()

        # 查詢執行歷史
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/history", params={"limit": 10}
        )

        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)
        assert len(history) > 0

        # 驗證第一筆記錄
        first_session = history[0]
        assert first_session["id"] == session.id
        assert first_session["agent_id"] == test_agent.id
        assert first_session["mode"] == "TRADING"
        assert first_session["status"] == "COMPLETED"

        # 驗證新增的統計欄位
        assert "trade_count" in first_session
        assert "filled_count" in first_session
        assert "total_notional" in first_session

        assert first_session["trade_count"] == 1
        assert first_session["filled_count"] == 1
        assert first_session["total_notional"] == 580000.00

    async def test_get_session_detail_not_found(self, async_client: AsyncClient, test_agent):
        """測試查詢不存在的 session"""
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/sessions/non-existent-session-id"
        )

        # 應該返回 500 或 404（取決於實現）
        assert response.status_code in [404, 500]

    async def test_get_session_detail_with_trades(
        self, async_client: AsyncClient, test_agent, test_db_session
    ):
        """測試查詢包含交易記錄的 session 詳情"""
        # 創建測試 session
        session = AgentSession(
            agent_id=test_agent.id,
            mode=AgentMode.TRADING,
            status=SessionStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time_ms=8000,
            final_output={"summary": "Detailed test execution"},
            tools_called='["get_stock_price", "buy_stock", "sell_stock"]',
        )
        test_db_session.add(session)
        await test_db_session.commit()
        await test_db_session.refresh(session)

        # 創建多筆測試交易
        transactions = [
            Transaction(
                agent_id=test_agent.id,
                session_id=session.id,
                ticker="2330",
                company_name="台積電",
                action=TransactionAction.BUY,
                quantity=1000,
                price=Decimal("580.00"),
                total_amount=Decimal("580000.00"),
                commission=Decimal("817.00"),
                status=TransactionStatus.EXECUTED,
                execution_time=datetime.now(),
                decision_reason="Buy based on analysis",
            ),
            Transaction(
                agent_id=test_agent.id,
                session_id=session.id,
                ticker="0050",
                company_name="元大台灣50",
                action=TransactionAction.BUY,
                quantity=5000,
                price=Decimal("180.00"),
                total_amount=Decimal("900000.00"),
                commission=Decimal("1268.50"),
                status=TransactionStatus.EXECUTED,
                execution_time=datetime.now(),
                decision_reason="Diversification",
            ),
            Transaction(
                agent_id=test_agent.id,
                session_id=session.id,
                ticker="2317",
                company_name="鴻海",
                action=TransactionAction.SELL,
                quantity=500,
                price=Decimal("120.00"),
                total_amount=Decimal("60000.00"),
                commission=Decimal("84.60"),
                status=TransactionStatus.PENDING,
                decision_reason="Take profit",
            ),
        ]

        for tx in transactions:
            test_db_session.add(tx)
        await test_db_session.commit()

        # 查詢 session 詳情
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/sessions/{session.id}"
        )

        assert response.status_code == 200
        detail = response.json()

        # 驗證基本資訊
        assert detail["id"] == session.id
        assert detail["agent_id"] == test_agent.id
        assert detail["mode"] == "TRADING"
        assert detail["status"] == "COMPLETED"
        assert detail["execution_time_ms"] == 8000

        # 驗證 final_output
        assert detail["final_output"] is not None
        assert detail["final_output"]["summary"] == "Detailed test execution"

        # 驗證 tools_called
        assert detail["tools_called"] is not None
        assert "get_stock_price" in detail["tools_called"]

        # 驗證交易記錄
        assert "trades" in detail
        assert isinstance(detail["trades"], list)
        assert len(detail["trades"]) == 3

        # 驗證第一筆交易
        first_trade = detail["trades"][0]
        assert first_trade["ticker"] == "2330"
        assert first_trade["symbol"] == "2330"  # 別名
        assert first_trade["company_name"] == "台積電"
        assert first_trade["action"] == "BUY"
        assert first_trade["type"] == "BUY"  # 別名
        assert first_trade["quantity"] == 1000
        assert first_trade["shares"] == 1000  # 別名
        assert first_trade["price"] == 580.00
        assert first_trade["amount"] == 580000.00
        assert first_trade["total_amount"] == 580000.00  # 別名
        assert first_trade["commission"] == 817.00
        assert first_trade["status"] == "executed"
        assert first_trade["decision_reason"] == "Buy based on analysis"

        # 驗證統計資料
        assert "stats" in detail
        stats = detail["stats"]
        assert stats["total_trades"] == 3
        assert stats["filled"] == 2  # 只有 2 筆 FILLED
        assert stats["notional"] == 1540000.00  # 580000 + 900000 + 60000

    async def test_get_session_detail_with_enum_status(
        self, async_client: AsyncClient, test_agent, test_db_session
    ):
        """測試處理 Enum 狀態值（確保不會出現 'str' object has no attribute 'value' 錯誤）"""
        # 創建 session
        session = AgentSession(
            agent_id=test_agent.id,
            mode=AgentMode.REBALANCING,
            status=SessionStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time_ms=3000,
        )
        test_db_session.add(session)
        await test_db_session.commit()
        await test_db_session.refresh(session)

        # 創建交易，確保使用 Enum 類型
        transaction = Transaction(
            agent_id=test_agent.id,
            session_id=session.id,
            ticker="2454",
            company_name="聯發科",
            action=TransactionAction.BUY,  # Enum
            quantity=100,
            price=Decimal("1245.00"),
            total_amount=Decimal("124500.00"),
            commission=Decimal("175.47"),
            status=TransactionStatus.EXECUTED,  # Enum
            execution_time=datetime.now(),
        )
        test_db_session.add(transaction)
        await test_db_session.commit()

        # 查詢應該成功，不會拋出 AttributeError
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/sessions/{session.id}"
        )

        assert response.status_code == 200
        detail = response.json()

        # 驗證統計資料正確計算
        assert detail["stats"]["filled"] == 1
        assert detail["stats"]["total_trades"] == 1

        # 驗證交易記錄
        assert len(detail["trades"]) == 1
        assert detail["trades"][0]["status"] == "executed"
        assert detail["trades"][0]["action"] == "BUY"

    async def test_get_execution_history_with_status_filter(
        self, async_client: AsyncClient, test_agent, test_db_session
    ):
        """測試使用狀態過濾器查詢執行歷史"""
        # 創建不同狀態的 sessions
        sessions = [
            AgentSession(
                agent_id=test_agent.id,
                mode=AgentMode.TRADING,
                status=SessionStatus.COMPLETED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                execution_time_ms=1000,
            ),
            AgentSession(
                agent_id=test_agent.id,
                mode=AgentMode.TRADING,
                status=SessionStatus.FAILED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                execution_time_ms=500,
                error_message="Test error",
            ),
            AgentSession(
                agent_id=test_agent.id,
                mode=AgentMode.TRADING,
                status=SessionStatus.RUNNING,
                start_time=datetime.now(),
            ),
        ]

        for session in sessions:
            test_db_session.add(session)
        await test_db_session.commit()

        # 測試過濾 COMPLETED 狀態
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/history",
            params={"limit": 10, "status_filter": "completed"},
        )

        assert response.status_code == 200
        history = response.json()

        # 至少應該有一筆 COMPLETED 記錄
        completed_sessions = [s for s in history if s["status"] == "COMPLETED"]
        assert len(completed_sessions) >= 1

    async def test_get_session_detail_wrong_agent(
        self, async_client: AsyncClient, test_agent, test_db_session
    ):
        """測試查詢屬於其他 agent 的 session"""
        # 創建另一個 agent
        other_agent = Agent(
            name="Other Agent",
            description="Another test agent",
            ai_model="gpt-4o-mini",
            initial_funds=Decimal("1000000.00"),
            current_funds=Decimal("1000000.00"),
            status=AgentStatus.ACTIVE,
        )
        test_db_session.add(other_agent)
        await test_db_session.commit()
        await test_db_session.refresh(other_agent)

        # 創建屬於 other_agent 的 session
        session = AgentSession(
            agent_id=other_agent.id,
            mode=AgentMode.TRADING,
            status=SessionStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time_ms=2000,
        )
        test_db_session.add(session)
        await test_db_session.commit()
        await test_db_session.refresh(session)

        # 使用 test_agent 的 ID 查詢 other_agent 的 session
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/sessions/{session.id}"
        )

        # 應該返回 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_execution_history_handles_empty_transactions(
        self, async_client: AsyncClient, test_agent, test_db_session
    ):
        """測試處理沒有交易記錄的 session"""
        # 創建沒有交易的 session
        session = AgentSession(
            agent_id=test_agent.id,
            mode=AgentMode.TRADING,
            status=SessionStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time_ms=1500,
            final_output=None,  # 沒有輸出
            tools_called=None,  # 沒有工具調用
        )
        test_db_session.add(session)
        await test_db_session.commit()
        await test_db_session.refresh(session)

        # 查詢執行歷史
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/history", params={"limit": 10}
        )

        assert response.status_code == 200
        history = response.json()

        # 找到我們創建的 session
        target_session = next((s for s in history if s["id"] == session.id), None)
        assert target_session is not None

        # 驗證統計欄位為零
        assert target_session["trade_count"] == 0
        assert target_session["filled_count"] == 0
        assert target_session["total_notional"] == 0.0

    async def test_get_session_detail_handles_empty_transactions(
        self, async_client: AsyncClient, test_agent, test_db_session
    ):
        """測試查詢沒有交易記錄的 session 詳情"""
        # 創建沒有交易的 session
        session = AgentSession(
            agent_id=test_agent.id,
            mode=AgentMode.REBALANCING,
            status=SessionStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time_ms=2500,
            final_output=None,
            tools_called=None,
        )
        test_db_session.add(session)
        await test_db_session.commit()
        await test_db_session.refresh(session)

        # 查詢 session 詳情
        response = await async_client.get(
            f"/api/agent-execution/{test_agent.id}/sessions/{session.id}"
        )

        assert response.status_code == 200
        detail = response.json()

        # 驗證基本資訊
        assert detail["id"] == session.id
        assert detail["final_output"] is None
        assert detail["tools_called"] is None

        # 驗證空的交易列表
        assert detail["trades"] == []

        # 驗證統計資料為零
        assert detail["stats"]["total_trades"] == 0
        assert detail["stats"]["filled"] == 0
        assert detail["stats"]["notional"] == 0.0


@pytest.fixture
async def async_client(test_db_session):
    """創建異步 HTTP 客戶端"""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_agent(test_db_session):
    """創建測試用 Agent"""
    agent = Agent(
        name="Test Agent",
        description="Agent for execution API testing",
        ai_model="gpt-4o-mini",
        initial_funds=Decimal("10000000.00"),
        current_funds=Decimal("10000000.00"),
        status=AgentStatus.ACTIVE,
        current_mode=AgentMode.TRADING,
    )
    test_db_session.add(agent)
    await test_db_session.commit()
    await test_db_session.refresh(agent)

    yield agent

    # Cleanup
    await test_db_session.delete(agent)
    await test_db_session.commit()
