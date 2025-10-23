"""
Agent CRUD 整合測試

測試完整的 Agent 建立、讀取、更新、刪除週期，
特別關注 investment_preferences 的資料完整性驗證。
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastapi.testclient import TestClient
from api.app import create_app


@pytest.fixture
def client():
    """建立測試客戶端"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_agent_data():
    """測試用的 Agent 資料"""
    return {
        "name": "CRUD 測試代理",
        "description": "用於測試 CRUD 操作的代理",
        "ai_model": "gpt-4o-mini",
        "strategy_prompt": "測試策略：專注於技術分析和風險控制",
        "color_theme": "34, 197, 94",
        "initial_funds": 1000000.0,
        "max_turns": 30,  # 修正：改為 30
        "investment_preferences": ["2330", "2454", "0050"],  # 修正：改為列表格式
        "enabled_tools": {
            "fundamental_analysis": True,
            "technical_analysis": True,
            "risk_assessment": True,
            "sentiment_analysis": False,
            "web_search": True,
            "code_interpreter": False,
        },
    }


class TestAgentCRUDLifecycle:
    """Agent CRUD 完整週期測試"""

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_create_agent_with_investment_preferences(
        self, mock_service, mock_db, client, sample_agent_data
    ):
        """測試建立 Agent 並驗證 investment_preferences 處理"""
        # Mock 服務回應
        mock_instance = mock_service.return_value
        mock_instance.create_agent = AsyncMock(return_value="agent_test_001")
        mock_instance.get_agent = AsyncMock(
            return_value=type(
                "Agent",
                (),
                {
                    "id": "agent_test_001",
                    "name": "CRUD 測試代理",
                    "investment_preferences": ["2330", "2454", "0050"],  # 模擬轉換後的格式
                    "enabled_tools": {
                        "fundamental_analysis": True,
                        "technical_analysis": True,
                        "risk_assessment": True,
                        "sentiment_analysis": False,
                        "web_search": True,
                        "code_interpreter": False,
                    },
                    "ai_model": "gpt-4o-mini",
                    "strategy_prompt": "測試策略：專注於技術分析和風險控制",
                    "color_theme": "34, 197, 94",
                    "current_mode": "TRADING",
                    "status": "idle",
                    "initial_funds": 1000000.0,
                    "current_funds": 1000000.0,
                    "max_turns": 50,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                },
            )()
        )

        # 1. 建立 Agent
        response = client.post("/api/agents", json=sample_agent_data)
        if response.status_code != 201:
            print(f"Response: {response.json()}")
        assert response.status_code == 201

        created_agent = response.json()
        print(f"Created agent response: {created_agent}")

        # 驗證回應格式
        assert "id" in created_agent
        assert isinstance(created_agent["investment_preferences"], list)
        assert created_agent["investment_preferences"] == ["2330", "2454", "0050"]
        if "enabled_tools" in created_agent:
            assert isinstance(created_agent["enabled_tools"], dict)

        # 驗證服務被正確呼叫
        mock_instance.create_agent.assert_called_once()
        create_call_args = mock_instance.create_agent.call_args[0][0]

        # 驗證傳給服務的資料格式
        assert isinstance(create_call_args["investment_preferences"], str)  # 前端提交字串

        return created_agent["id"]

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_list_agents_investment_preferences_format(self, mock_service, mock_db, client):
        """測試列出 Agents 時 investment_preferences 格式正確"""
        # Mock 服務回應
        mock_instance = mock_service.return_value
        mock_instance.list_agents = AsyncMock(
            return_value=[
                type(
                    "Agent",
                    (),
                    {
                        "id": "agent_001",
                        "name": "測試代理1",
                        "investment_preferences": ["2330", "2454"],  # 列表格式
                        "enabled_tools": {"fundamental_analysis": True},
                        "ai_model": "gpt-4o-mini",
                        "strategy_prompt": "策略1",
                        "color_theme": "34, 197, 94",
                        "current_mode": "TRADING",
                        "status": "idle",
                        "initial_funds": 1000000.0,
                        "current_funds": 1000000.0,
                        "max_turns": 50,
                        "created_at": "2025-01-01T00:00:00Z",
                        "updated_at": "2025-01-01T00:00:00Z",
                    },
                )(),
                type(
                    "Agent",
                    (),
                    {
                        "id": "agent_002",
                        "name": "測試代理2",
                        "investment_preferences": ["0050", "1101"],  # 列表格式
                        "enabled_tools": {"technical_analysis": True},
                        "ai_model": "gpt-4o",
                        "strategy_prompt": "策略2",
                        "color_theme": "220, 38, 127",
                        "current_mode": "ANALYSIS",
                        "status": "idle",
                        "initial_funds": 500000.0,
                        "current_funds": 500000.0,
                        "max_turns": 30,
                        "created_at": "2025-01-01T00:00:00Z",
                        "updated_at": "2025-01-01T00:00:00Z",
                    },
                )(),
            ]
        )

        # 2. 列出 Agents
        response = client.get("/api/agents")
        assert response.status_code == 200

        agents_list = response.json()
        assert isinstance(agents_list, list)
        assert len(agents_list) == 2

        # 驗證每個 Agent 的格式
        for agent in agents_list:
            assert isinstance(agent["investment_preferences"], list)
            assert isinstance(agent["enabled_tools"], dict)
            assert isinstance(agent["id"], str)

            # 驗證 investment_preferences 內容
            for pref in agent["investment_preferences"]:
                assert isinstance(pref, str)
                assert len(pref) >= 4  # 台股代碼最少4位

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_get_single_agent_investment_preferences_format(self, mock_service, mock_db, client):
        """測試獲取單一 Agent 時 investment_preferences 格式正確"""
        agent_id = "agent_test_001"

        # Mock 服務回應
        mock_instance = mock_service.return_value
        mock_instance.get_agent = AsyncMock(
            return_value=type(
                "Agent",
                (),
                {
                    "id": agent_id,
                    "name": "單一測試代理",
                    "investment_preferences": ["2330", "2454", "0050"],  # 列表格式
                    "enabled_tools": {
                        "fundamental_analysis": True,
                        "technical_analysis": False,
                        "risk_assessment": True,
                    },
                    "ai_model": "gpt-4o-mini",
                    "strategy_prompt": "單一代理測試策略",
                    "color_theme": "34, 197, 94",
                    "current_mode": "TRADING",
                    "status": "idle",
                    "initial_funds": 1000000.0,
                    "current_funds": 1000000.0,
                    "max_turns": 50,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                },
            )()
        )

        # 3. 獲取單一 Agent
        response = client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200

        agent = response.json()

        # 驗證格式
        assert isinstance(agent["investment_preferences"], list)
        assert agent["investment_preferences"] == ["2330", "2454", "0050"]
        assert isinstance(agent["enabled_tools"], dict)

        # 驗證內容正確性
        assert len(agent["investment_preferences"]) == 3
        for pref in agent["investment_preferences"]:
            assert isinstance(pref, str)
            assert pref in ["2330", "2454", "0050"]

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_update_agent_investment_preferences(self, mock_service, mock_db, client):
        """測試更新 Agent 的 investment_preferences"""
        agent_id = "agent_test_001"

        # Mock 服務回應
        mock_instance = mock_service.return_value
        mock_instance.update_agent = AsyncMock(
            return_value=type(
                "Agent",
                (),
                {
                    "id": agent_id,
                    "name": "更新測試代理",
                    "investment_preferences": ["1101", "2882", "2891"],  # 更新後的列表
                    "enabled_tools": {"fundamental_analysis": True},
                    "ai_model": "gpt-4o-mini",
                    "strategy_prompt": "更新後的策略",
                    "color_theme": "34, 197, 94",
                    "current_mode": "TRADING",
                    "status": "idle",
                    "initial_funds": 1000000.0,
                    "current_funds": 1000000.0,
                    "max_turns": 50,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T01:00:00Z",
                },
            )()
        )

        # 4. 更新 Agent
        update_data = {
            "investment_preferences": "1101,2882,2891",  # 字串格式（前端提交）
            "strategy_prompt": "更新後的策略",
        }

        response = client.put(f"/api/agents/{agent_id}", json=update_data)
        assert response.status_code == 200

        updated_agent = response.json()

        # 驗證更新後的格式
        assert isinstance(updated_agent["investment_preferences"], list)
        assert updated_agent["investment_preferences"] == ["1101", "2882", "2891"]
        assert updated_agent["strategy_prompt"] == "更新後的策略"

        # 驗證服務被正確呼叫
        mock_instance.update_agent.assert_called_once()
        update_call_args = mock_instance.update_agent.call_args[0]
        assert update_call_args[0] == agent_id

        # 驗證傳給服務的資料格式
        update_data_passed = update_call_args[1]
        assert isinstance(update_data_passed["investment_preferences"], str)  # 前端提交字串

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_delete_agent(self, mock_service, mock_db, client):
        """測試刪除 Agent"""
        agent_id = "agent_test_001"

        # Mock 服務回應
        mock_instance = mock_service.return_value
        mock_instance.delete_agent = AsyncMock(return_value=True)

        # 5. 刪除 Agent
        response = client.delete(f"/api/agents/{agent_id}")
        assert response.status_code == 204

        # 驗證服務被正確呼叫
        mock_instance.delete_agent.assert_called_once_with(agent_id)

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_complete_crud_lifecycle_integration(
        self, mock_service, mock_db, client, sample_agent_data
    ):
        """測試完整的 CRUD 週期整合"""
        mock_instance = mock_service.return_value
        agent_id = "agent_complete_test"

        # Mock 建立回應
        mock_instance.create_agent = AsyncMock(return_value=agent_id)

        # Mock 讀取回應（列表）
        mock_instance.list_agents = AsyncMock(
            return_value=[
                type(
                    "Agent",
                    (),
                    {
                        "id": agent_id,
                        "name": sample_agent_data["name"],
                        "investment_preferences": ["2330", "2454", "0050"],
                        "enabled_tools": sample_agent_data["enabled_tools"],
                        "ai_model": sample_agent_data["ai_model"],
                        "strategy_prompt": sample_agent_data["strategy_prompt"],
                        "color_theme": sample_agent_data["color_theme"],
                        "current_mode": "TRADING",
                        "status": "idle",
                        "initial_funds": sample_agent_data["initial_funds"],
                        "current_funds": sample_agent_data["initial_funds"],
                        "max_turns": sample_agent_data["max_turns"],
                        "created_at": "2025-01-01T00:00:00Z",
                        "updated_at": "2025-01-01T00:00:00Z",
                    },
                )()
            ]
        )

        # Mock 讀取回應（單一）
        mock_instance.get_agent = AsyncMock(
            return_value=type(
                "Agent",
                (),
                {
                    "id": agent_id,
                    "name": sample_agent_data["name"],
                    "investment_preferences": ["2330", "2454", "0050"],
                    "enabled_tools": sample_agent_data["enabled_tools"],
                    "ai_model": sample_agent_data["ai_model"],
                    "strategy_prompt": sample_agent_data["strategy_prompt"],
                    "color_theme": sample_agent_data["color_theme"],
                    "current_mode": "TRADING",
                    "status": "idle",
                    "initial_funds": sample_agent_data["initial_funds"],
                    "current_funds": sample_agent_data["initial_funds"],
                    "max_turns": sample_agent_data["max_turns"],
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                },
            )()
        )

        # Mock 更新回應
        mock_instance.update_agent = AsyncMock(
            return_value=type(
                "Agent",
                (),
                {
                    "id": agent_id,
                    "name": sample_agent_data["name"],
                    "investment_preferences": ["1101", "2882"],  # 更新後
                    "enabled_tools": sample_agent_data["enabled_tools"],
                    "ai_model": sample_agent_data["ai_model"],
                    "strategy_prompt": "更新後的策略",
                    "color_theme": sample_agent_data["color_theme"],
                    "current_mode": "TRADING",
                    "status": "idle",
                    "initial_funds": sample_agent_data["initial_funds"],
                    "current_funds": sample_agent_data["initial_funds"],
                    "max_turns": sample_agent_data["max_turns"],
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T01:00:00Z",
                },
            )()
        )

        # Mock 刪除回應
        mock_instance.delete_agent = AsyncMock(return_value=True)

        # 步驟 1: 建立
        create_response = client.post("/api/agents", json=sample_agent_data)
        assert create_response.status_code == 201
        created_agent = create_response.json()
        assert isinstance(created_agent["investment_preferences"], list)

        # 步驟 2: 列表讀取
        list_response = client.get("/api/agents")
        assert list_response.status_code == 200
        agents = list_response.json()
        agent_in_list = next(a for a in agents if a["id"] == agent_id)
        assert isinstance(agent_in_list["investment_preferences"], list)

        # 步驟 3: 單一讀取
        get_response = client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 200
        individual_agent = get_response.json()
        assert isinstance(individual_agent["investment_preferences"], list)

        # 步驟 4: 更新
        update_data = {"investment_preferences": "1101,2882"}
        update_response = client.put(f"/api/agents/{agent_id}", json=update_data)
        assert update_response.status_code == 200
        updated_agent = update_response.json()
        assert isinstance(updated_agent["investment_preferences"], list)
        assert updated_agent["investment_preferences"] == ["1101", "2882"]

        # 步驟 5: 刪除
        delete_response = client.delete(f"/api/agents/{agent_id}")
        assert delete_response.status_code == 204

        # 驗證所有服務方法都被正確呼叫
        assert mock_instance.create_agent.called
        assert mock_instance.list_agents.called
        assert mock_instance.get_agent.called
        assert mock_instance.update_agent.called
        assert mock_instance.delete_agent.called


class TestEdgeCases:
    """邊界情況測試"""

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_empty_investment_preferences(self, mock_service, mock_db, client):
        """測試空的 investment_preferences 處理"""
        mock_instance = mock_service.return_value
        mock_instance.create_agent = AsyncMock(return_value="agent_empty_test")
        mock_instance.get_agent = AsyncMock(
            return_value=type(
                "Agent",
                (),
                {
                    "id": "agent_empty_test",
                    "name": "空偏好測試",
                    "investment_preferences": [],  # 空列表
                    "enabled_tools": {"fundamental_analysis": True},
                    "ai_model": "gpt-4o-mini",
                    "strategy_prompt": "測試策略",
                    "color_theme": "34, 197, 94",
                    "current_mode": "TRADING",
                    "status": "idle",
                    "initial_funds": 1000000.0,
                    "current_funds": 1000000.0,
                    "max_turns": 50,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z",
                },
            )()
        )

        # 測試空字串
        agent_data = {
            "name": "空偏好測試",
            "ai_model": "gpt-4o-mini",
            "strategy_prompt": "測試策略",
            "investment_preferences": "",  # 空字串
            "enabled_tools": {"fundamental_analysis": True},
        }

        response = client.post("/api/agents", json=agent_data)
        assert response.status_code == 201

        created_agent = response.json()
        assert isinstance(created_agent["investment_preferences"], list)
        assert len(created_agent["investment_preferences"]) == 0

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_malformed_investment_preferences_input(self, mock_service, mock_db, client):
        """測試格式錯誤的 investment_preferences 輸入"""
        mock_instance = mock_service.return_value
        mock_instance.create_agent = AsyncMock(side_effect=ValueError("Invalid stock code format"))

        # 測試格式錯誤的輸入
        agent_data = {
            "name": "錯誤格式測試",
            "ai_model": "gpt-4o-mini",
            "strategy_prompt": "測試策略",
            "investment_preferences": "INVALID,,,2330,,AAPL",  # 包含無效格式
            "enabled_tools": {"fundamental_analysis": True},
        }

        response = client.post("/api/agents", json=agent_data)
        # 應該返回 400 錯誤（由 API 錯誤處理機制處理）
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
