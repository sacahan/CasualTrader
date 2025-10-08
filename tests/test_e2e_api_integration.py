"""
End-to-End API Integration Tests

This test suite validates the complete flow from API requests through
Agent Manager to Trading Agent execution, ensuring all parameters are
correctly transformed and transmitted.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def app():
    """Create FastAPI test app."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestEndToEndAgentCreation:
    """Test complete agent creation flow."""

    def test_create_agent_parameter_transformation(self, client) -> None:
        """
        Test that API parameters are correctly transformed to Agent parameters.

        This is the CRITICAL test that validates:
        1. API receives CreateAgentRequest
        2. Parameters are correctly converted to AgentConfig
        3. Agent is created with proper configuration
        4. Response contains correct data
        """
        # API Request payload
        request_payload = {
            "name": "測試代理",
            "description": "端對端測試代理",
            "ai_model": "gpt-4o",
            "strategy_type": "balanced",
            "strategy_prompt": "測試策略：尋找台灣科技股中具有穩定成長潛力的標的",
            "color_theme": "#007bff",
            "initial_funds": 1000000.0,
            "max_turns": 50,
            "risk_tolerance": 0.5,  # Float: 0.0-1.0
            "enabled_tools": {
                "fundamental_analysis": True,
                "technical_analysis": True,
                "risk_assessment": True,
                "sentiment_analysis": False,
                "web_search": True,
                "code_interpreter": False,
            },
            "investment_preferences": {
                "preferred_sectors": ["科技", "半導體"],
                "excluded_stocks": ["1234"],
                "max_position_size": 0.15,  # 15%
                "rebalance_frequency": "weekly",
            },
            "custom_instructions": "每次決策前先分析大盤走勢",
        }

        # Execute API call
        response = client.post("/api/agents", json=request_payload)

        # Validate response
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()

        # Validate basic fields
        assert data["name"] == "測試代理"
        assert data["description"] == "端對端測試代理"
        assert data["ai_model"] == "gpt-4o"
        assert data["strategy_type"] == "balanced"
        assert (
            data["strategy_prompt"]
            == "測試策略：尋找台灣科技股中具有穩定成長潛力的標的"
        )
        assert data["color_theme"] == "#007bff"
        assert data["initial_funds"] == 1000000.0
        assert data["max_turns"] == 50

        # Validate risk_tolerance conversion (float -> str -> float)
        assert "risk_tolerance" in data
        assert (
            0.4 <= data["risk_tolerance"] <= 0.6
        ), f"Risk tolerance {data['risk_tolerance']} not in expected range"

        # Validate enabled_tools
        assert data["enabled_tools"]["fundamental_analysis"] is True
        assert data["enabled_tools"]["technical_analysis"] is True
        assert data["enabled_tools"]["sentiment_analysis"] is False

        # Validate investment_preferences
        assert "科技" in data["investment_preferences"]["preferred_sectors"]
        assert "半導體" in data["investment_preferences"]["preferred_sectors"]
        assert "1234" in data["investment_preferences"]["excluded_stocks"]
        assert abs(data["investment_preferences"]["max_position_size"] - 0.15) < 0.01

        # Validate status
        assert data["status"] in [
            "idle",
            "inactive",
            "active",
        ], f"Unexpected status: {data['status']}"
        assert data["current_mode"] in [
            "OBSERVATION",
            "TRADING",
        ], f"Unexpected mode: {data['current_mode']}"

        print(f"✅ Agent created successfully with ID: {data['id']}")
        print(
            f"   Risk tolerance transformed correctly: {request_payload['risk_tolerance']} -> {data['risk_tolerance']}"
        )

    def test_create_agent_risk_tolerance_low(self, client):
        """Test risk tolerance conversion: low risk (0.2) -> 'low' -> 0.2"""
        request_payload = {
            "name": "低風險代理",
            "ai_model": "gpt-4o-mini",
            "strategy_type": "conservative",
            "strategy_prompt": "保守型投資策略，重視資本保全和穩定收益",
            "risk_tolerance": 0.2,  # Low risk
        }

        response = client.post("/api/agents", json=request_payload)
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()
        assert (
            data["risk_tolerance"] <= 0.35
        ), f"Low risk not preserved: {data['risk_tolerance']}"
        print(f"✅ Low risk tolerance: 0.2 -> {data['risk_tolerance']}")

    def test_create_agent_risk_tolerance_high(self, client):
        """Test risk tolerance conversion: high risk (0.8) -> 'high' -> 0.8"""
        request_payload = {
            "name": "高風險代理",
            "ai_model": "gpt-4o-mini",
            "strategy_type": "aggressive",
            "strategy_prompt": "積極型投資策略，追求高成長機會並接受較高波動",
            "risk_tolerance": 0.8,  # High risk
        }

        response = client.post("/api/agents", json=request_payload)
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()
        assert (
            data["risk_tolerance"] >= 0.70
        ), f"High risk not preserved: {data['risk_tolerance']}"
        print(f"✅ High risk tolerance: 0.8 -> {data['risk_tolerance']}")


class TestEndToEndAgentRetrieval:
    """Test agent retrieval after creation."""

    def test_get_agent_returns_correct_format(self, client):
        """Test that GET /agents/{id} returns correct format matching the creation response."""
        # First create an agent
        create_payload = {
            "name": "檢索測試代理",
            "ai_model": "gpt-4o-mini",
            "strategy_type": "balanced",
            "strategy_prompt": "測試策略用於驗證檢索功能",
            "risk_tolerance": 0.6,
        }

        create_response = client.post("/api/agents", json=create_payload)
        assert create_response.status_code == 201
        agent_id = create_response.json()["id"]

        # Now retrieve the agent
        get_response = client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 200

        data = get_response.json()

        # Validate format matches creation response
        assert data["id"] == agent_id
        assert data["name"] == "檢索測試代理"
        assert data["ai_model"] == "gpt-4o-mini"
        assert data["strategy_type"] == "balanced"
        assert "risk_tolerance" in data
        assert "enabled_tools" in data
        assert "investment_preferences" in data

        print(f"✅ Agent retrieval format correct for {agent_id}")

    def test_list_agents_returns_correct_format(self, client):
        """Test that GET /agents returns list with correct format."""
        # Create at least one agent
        create_payload = {
            "name": "列表測試代理",
            "ai_model": "gpt-4o-mini",
            "strategy_type": "balanced",
            "strategy_prompt": "測試策略",
        }

        client.post("/api/agents", json=create_payload)

        # List agents
        response = client.get("/api/agents")
        assert response.status_code == 200

        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert data["total"] > 0
        assert len(data["agents"]) > 0

        # Validate first agent format
        agent = data["agents"][0]
        required_fields = [
            "id",
            "name",
            "ai_model",
            "strategy_type",
            "status",
            "risk_tolerance",
            "enabled_tools",
            "investment_preferences",
        ]
        for field in required_fields:
            assert field in agent, f"Missing required field: {field}"

        print(f"✅ Agent list format correct, found {data['total']} agents")


class TestEndToEndParameterValidation:
    """Test parameter validation at API level."""

    def test_invalid_risk_tolerance_rejected(self, client):
        """Test that invalid risk_tolerance values are rejected."""
        invalid_payloads = [
            {"risk_tolerance": -0.1},  # Negative
            {"risk_tolerance": 1.5},  # > 1.0
            {"risk_tolerance": 2.0},  # Way too high
        ]

        for payload in invalid_payloads:
            full_payload = {
                "name": "Invalid Agent",
                "ai_model": "gpt-4o-mini",
                "strategy_type": "balanced",
                "strategy_prompt": "Test",
                **payload,
            }

            response = client.post("/api/agents", json=full_payload)
            assert (
                response.status_code == 422
            ), f"Should reject invalid payload: {payload}"
            print(
                f"✅ Correctly rejected invalid risk_tolerance: {payload['risk_tolerance']}"
            )

    def test_invalid_ai_model_rejected(self, client):
        """Test that invalid AI model is rejected."""
        payload = {
            "name": "Invalid Model Agent",
            "ai_model": "invalid-model-xyz",
            "strategy_type": "balanced",
            "strategy_prompt": "Test",
        }

        response = client.post("/api/agents", json=payload)
        assert response.status_code == 422
        print("✅ Correctly rejected invalid AI model")

    def test_missing_required_fields_rejected(self, client):
        """Test that missing required fields are rejected."""
        incomplete_payload = {
            "name": "Incomplete Agent",
            # Missing strategy_prompt (required)
        }

        response = client.post("/api/agents", json=incomplete_payload)
        assert response.status_code == 422
        print("✅ Correctly rejected incomplete payload")


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v", "-s"])
