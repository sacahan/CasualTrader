"""
前後台契約 E2E 測試

測試完整的前後台資料流，確保 investment_preferences
在整個生命週期中都維持正確的格式。
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
def mock_frontend_request():
    """模擬前端請求資料格式"""
    return {
        "name": "前後台契約測試代理",
        "description": "用於測試前後台資料格式一致性",
        "ai_model": "gpt-4o-mini",
        "strategy_prompt": "契約測試：確保資料格式正確轉換",
        "color_theme": "34, 197, 94",
        "initial_funds": 1000000.0,
        "max_turns": 50,
        "investment_preferences": "2330,2454,0050,1101",  # 前端提交：字串格式
        "enabled_tools": {
            "fundamental_analysis": True,
            "technical_analysis": True,
            "risk_assessment": True,
            "sentiment_analysis": False,
            "web_search": True,
            "code_interpreter": False,
        },
    }


@pytest.fixture
def expected_backend_response():
    """預期的後端回應格式"""
    return {
        "id": "agent_contract_test",
        "name": "前後台契約測試代理",
        "description": "用於測試前後台資料格式一致性",
        "ai_model": "gpt-4o-mini",
        "strategy_prompt": "契約測試：確保資料格式正確轉換",
        "color_theme": "34, 197, 94",
        "current_mode": "TRADING",
        "status": "idle",
        "initial_funds": 1000000.0,
        "current_funds": 1000000.0,
        "max_turns": 50,
        "investment_preferences": ["2330", "2454", "0050", "1101"],  # 後端回應：列表格式
        "enabled_tools": {
            "fundamental_analysis": True,
            "technical_analysis": True,
            "risk_assessment": True,
            "sentiment_analysis": False,
            "web_search": True,
            "code_interpreter": False,
        },
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }


class TestFrontendBackendContract:
    """前後台契約測試"""

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_frontend_to_backend_data_flow(
        self, mock_service, mock_db, client, mock_frontend_request, expected_backend_response
    ):
        """測試前端到後端的資料流程"""
        # Mock 服務層行為
        mock_instance = mock_service.return_value
        mock_instance.create_agent = AsyncMock(return_value="agent_contract_test")
        mock_instance.get_agent = AsyncMock(
            return_value=type("Agent", (), expected_backend_response)()
        )

        # 1. 前端提交資料（字串格式）
        response = client.post("/api/agents", json=mock_frontend_request)
        assert response.status_code == 201

        # 2. 驗證後端回應格式（列表格式）
        created_agent = response.json()
        assert isinstance(created_agent["investment_preferences"], list)
        assert created_agent["investment_preferences"] == ["2330", "2454", "0050", "1101"]

        # 3. 驗證服務層收到正確的輸入格式
        mock_instance.create_agent.assert_called_once()
        service_input = mock_instance.create_agent.call_args[0][0]

        # 服務層應該收到前端的原始格式（字串）
        assert isinstance(service_input["investment_preferences"], str)
        assert service_input["investment_preferences"] == "2330,2454,0050,1101"

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_backend_response_consistency(
        self, mock_service, mock_db, client, expected_backend_response
    ):
        """測試後端回應的一致性"""
        mock_instance = mock_service.return_value

        # Mock 不同端點的回應都應該有相同的格式
        mock_agent = type("Agent", (), expected_backend_response)()
        mock_instance.list_agents = AsyncMock(return_value=[mock_agent])
        mock_instance.get_agent = AsyncMock(return_value=mock_agent)

        agent_id = "agent_contract_test"

        # 測試 GET /api/agents（列表）
        list_response = client.get("/api/agents")
        assert list_response.status_code == 200
        agents_list = list_response.json()

        assert len(agents_list) == 1
        agent_from_list = agents_list[0]
        assert isinstance(agent_from_list["investment_preferences"], list)
        assert agent_from_list["investment_preferences"] == ["2330", "2454", "0050", "1101"]

        # 測試 GET /api/agents/{id}（單一）
        get_response = client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 200
        individual_agent = get_response.json()

        assert isinstance(individual_agent["investment_preferences"], list)
        assert individual_agent["investment_preferences"] == ["2330", "2454", "0050", "1101"]

        # 確保兩個端點回應的格式完全一致
        assert (
            agent_from_list["investment_preferences"] == individual_agent["investment_preferences"]
        )
        assert isinstance(
            agent_from_list["investment_preferences"],
            type(individual_agent["investment_preferences"]),
        )

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_update_operation_data_flow(self, mock_service, mock_db, client):
        """測試更新操作的資料流程"""
        agent_id = "agent_contract_test"
        mock_instance = mock_service.return_value

        # Mock 更新後的回應
        updated_response = {
            "id": agent_id,
            "name": "更新後的契約測試代理",
            "investment_preferences": ["1101", "2882", "2891"],  # 更新後的列表
            "enabled_tools": {"fundamental_analysis": True},
            "ai_model": "gpt-4o-mini",
            "strategy_prompt": "更新後的策略",
            "color_theme": "220, 38, 127",
            "current_mode": "ANALYSIS",
            "status": "idle",
            "initial_funds": 1000000.0,
            "current_funds": 1000000.0,
            "max_turns": 50,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T01:00:00Z",
        }

        mock_instance.update_agent = AsyncMock(return_value=type("Agent", (), updated_response)())

        # 前端提交更新資料（字串格式）
        update_data = {
            "name": "更新後的契約測試代理",
            "investment_preferences": "1101,2882,2891",  # 字串格式
            "strategy_prompt": "更新後的策略",
            "color_theme": "220, 38, 127",
            "current_mode": "ANALYSIS",
        }

        response = client.put(f"/api/agents/{agent_id}", json=update_data)
        assert response.status_code == 200

        # 驗證後端回應格式（列表）
        updated_agent = response.json()
        assert isinstance(updated_agent["investment_preferences"], list)
        assert updated_agent["investment_preferences"] == ["1101", "2882", "2891"]

        # 驗證服務層收到正確的輸入格式
        mock_instance.update_agent.assert_called_once()
        update_call_args = mock_instance.update_agent.call_args[0]
        service_input = update_call_args[1]

        # 服務層應該收到前端的原始格式（字串）
        assert isinstance(service_input["investment_preferences"], str)
        assert service_input["investment_preferences"] == "1101,2882,2891"

    def test_json_serialization_consistency(self):
        """測試 JSON 序列化的一致性"""
        import json

        # 模擬後端內部的資料結構
        internal_data = {
            "id": "agent_json_test",
            "name": "JSON 測試代理",
            "investment_preferences": ["2330", "2454", "0050"],  # Python 列表
            "enabled_tools": {"fundamental_analysis": True, "technical_analysis": False},
        }

        # 序列化為 JSON
        json_string = json.dumps(internal_data)

        # 反序列化
        deserialized_data = json.loads(json_string)

        # 確保型別保持一致
        assert isinstance(deserialized_data["investment_preferences"], list)
        assert isinstance(deserialized_data["enabled_tools"], dict)

        # 確保內容沒有改變
        assert (
            deserialized_data["investment_preferences"] == internal_data["investment_preferences"]
        )
        assert deserialized_data["enabled_tools"] == internal_data["enabled_tools"]

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_error_response_format_consistency(self, mock_service, mock_db, client):
        """測試錯誤回應的格式一致性"""
        mock_instance = mock_service.return_value
        mock_instance.create_agent = AsyncMock(
            side_effect=ValueError("Invalid investment preferences format")
        )

        # 提交無效資料
        invalid_data = {
            "name": "錯誤測試代理",
            "ai_model": "gpt-4o-mini",
            "strategy_prompt": "測試策略",
            "investment_preferences": "INVALID,,,FORMAT",  # 無效格式
            "enabled_tools": {"fundamental_analysis": True},
        }

        response = client.post("/api/agents", json=invalid_data)

        # 驗證錯誤回應格式
        assert response.status_code in [400, 422, 500]
        error_data = response.json()

        # 標準錯誤格式應該包含 detail 欄位
        assert "detail" in error_data
        assert isinstance(error_data["detail"], str)

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_empty_database_scenario(self, mock_service, mock_db, client):
        """測試空資料庫情境（這是之前測試的盲點）"""
        mock_instance = mock_service.return_value
        mock_instance.list_agents = AsyncMock(return_value=[])  # 空列表

        # 請求 agents 列表
        response = client.get("/api/agents")
        assert response.status_code == 200

        agents_list = response.json()
        assert isinstance(agents_list, list)
        assert len(agents_list) == 0

        # 確保空列表的情況下也不會有序列化問題
        # （這是之前測試沒有覆蓋到的情況）

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_large_dataset_performance(self, mock_service, mock_db, client):
        """測試大量資料的情況"""
        mock_instance = mock_service.return_value

        # 建立大量模擬資料
        large_dataset = []
        for i in range(100):
            agent_data = {
                "id": f"agent_{i:03d}",
                "name": f"大量測試代理_{i}",
                "investment_preferences": [f"{2330 + i}", f"{2454 + i}"],  # 確保都是列表
                "enabled_tools": {"fundamental_analysis": True},
                "ai_model": "gpt-4o-mini",
                "strategy_prompt": f"策略_{i}",
                "color_theme": "34, 197, 94",
                "current_mode": "TRADING",
                "status": "idle",
                "initial_funds": 1000000.0,
                "current_funds": 1000000.0,
                "max_turns": 50,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
            large_dataset.append(type("Agent", (), agent_data)())

        mock_instance.list_agents = AsyncMock(return_value=large_dataset)

        # 請求大量資料
        response = client.get("/api/agents")
        assert response.status_code == 200

        agents_list = response.json()
        assert isinstance(agents_list, list)
        assert len(agents_list) == 100

        # 驗證每個 agent 的格式都正確
        for agent in agents_list:
            assert isinstance(agent["investment_preferences"], list)
            assert isinstance(agent["enabled_tools"], dict)

            # 驗證 investment_preferences 內容
            for pref in agent["investment_preferences"]:
                assert isinstance(pref, str)


class TestContractValidation:
    """契約驗證輔助測試"""

    def validate_agent_contract(self, agent_data: dict) -> list[str]:
        """
        驗證 Agent 資料是否符合前後台契約
        Returns: 違反契約的錯誤列表
        """
        errors = []

        # 必要欄位檢查
        required_fields = {
            "id": str,
            "name": str,
            "investment_preferences": list,
            "enabled_tools": dict,
            "ai_model": str,
            "strategy_prompt": str,
            "current_mode": str,
            "status": str,
            "initial_funds": (int, float),
            "current_funds": (int, float),
            "max_turns": int,
        }

        for field, expected_type in required_fields.items():
            if field not in agent_data:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(agent_data[field], expected_type):
                errors.append(
                    f"Field '{field}' must be {expected_type.__name__}, got {type(agent_data[field]).__name__}"
                )

        # investment_preferences 特別檢查
        if "investment_preferences" in agent_data:
            prefs = agent_data["investment_preferences"]
            if isinstance(prefs, list):
                for i, pref in enumerate(prefs):
                    if not isinstance(pref, str):
                        errors.append(
                            f"investment_preferences[{i}] must be string, got {type(pref).__name__}"
                        )
                    elif len(pref) < 4:
                        errors.append(
                            f"investment_preferences[{i}] '{pref}' is too short for stock code"
                        )

        return errors

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_contract_validation_helper(
        self, mock_service, mock_db, client, expected_backend_response
    ):
        """測試契約驗證輔助函數"""
        # ✅ 正確格式
        errors = self.validate_agent_contract(expected_backend_response)
        assert len(errors) == 0, f"Valid contract should have no errors, got: {errors}"

        # ❌ 錯誤格式：investment_preferences 是字串
        invalid_agent = expected_backend_response.copy()
        invalid_agent["investment_preferences"] = '["2330", "2454"]'  # 字串而非列表

        errors = self.validate_agent_contract(invalid_agent)
        assert len(errors) > 0
        assert any(
            "investment_preferences" in error and "must be list" in error for error in errors
        )

        # ❌ 缺失欄位
        incomplete_agent = {"name": "Test", "id": "test"}
        errors = self.validate_agent_contract(incomplete_agent)
        assert len(errors) > 5  # 應該有多個缺失欄位的錯誤

    @patch("api.config.get_db_session")
    @patch("service.agents_service.AgentsService")
    def test_real_api_contract_compliance(
        self, mock_service, mock_db, client, expected_backend_response
    ):
        """測試真實 API 回應是否符合契約"""
        mock_instance = mock_service.return_value
        mock_instance.list_agents = AsyncMock(
            return_value=[type("Agent", (), expected_backend_response)()]
        )

        # 獲取真實 API 回應
        response = client.get("/api/agents")
        assert response.status_code == 200

        agents_list = response.json()

        # 驗證每個 agent 都符合契約
        for agent in agents_list:
            errors = self.validate_agent_contract(agent)
            assert len(errors) == 0, f"API response violates contract: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
