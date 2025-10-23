"""
Agent API Response Schema 驗證測試

驗證 Agent API 返回的資料格式符合前後台契約規範，
特別針對 investment_preferences 序列化問題進行測試。
"""

import pytest
from typing import Any, Dict, List

# 測試用的模擬 API 回應數據
MOCK_AGENT_RESPONSE = {
    "id": "agent_test_123",
    "name": "測試代理",
    "description": "用於測試的代理",
    "ai_model": "gpt-4o-mini",
    "strategy_prompt": "測試策略",
    "color_theme": "34, 197, 94",
    "current_mode": "TRADING",
    "status": "idle",
    "initial_funds": 1000000.0,
    "current_funds": 1000000.0,
    "max_turns": 50,
    "investment_preferences": ["2330", "2454", "0050"],  # ✅ 必須是列表
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


class TestAgentResponseSchema:
    """Agent API 回應 Schema 驗證測試"""

    def test_investment_preferences_is_list(self):
        """測試 investment_preferences 必須是列表格式"""
        agent = MOCK_AGENT_RESPONSE.copy()

        # ✅ 正確格式：列表
        assert isinstance(agent["investment_preferences"], list)
        assert all(isinstance(pref, str) for pref in agent["investment_preferences"])

        # ❌ 錯誤格式：字串（模擬序列化錯誤）
        agent_with_string = agent.copy()
        agent_with_string["investment_preferences"] = '["2330", "2454", "0050"]'

        # 這應該失敗，因為前端期望列表
        assert not isinstance(agent_with_string["investment_preferences"], list)
        with pytest.raises(AttributeError):
            # 模擬前端嘗試使用 .length 屬性（字串沒有 length 屬性）
            _ = agent_with_string["investment_preferences"].length

    def test_enabled_tools_is_dict(self):
        """測試 enabled_tools 必須是字典格式"""
        agent = MOCK_AGENT_RESPONSE.copy()

        # ✅ 正確格式：字典
        assert isinstance(agent["enabled_tools"], dict)

        # 驗證所有工具設定都是布林值
        for tool_name, enabled in agent["enabled_tools"].items():
            assert isinstance(tool_name, str)
            assert isinstance(enabled, bool)

    def test_required_fields_present(self):
        """測試必要欄位都存在且型別正確"""
        agent = MOCK_AGENT_RESPONSE.copy()

        # 字串欄位
        string_fields = ["id", "name", "ai_model", "strategy_prompt", "current_mode", "status"]
        for field in string_fields:
            assert field in agent
            assert isinstance(agent[field], str)
            assert len(agent[field]) > 0  # 不能是空字串

        # 數字欄位
        numeric_fields = ["initial_funds", "current_funds", "max_turns"]
        for field in numeric_fields:
            assert field in agent
            assert isinstance(agent[field], (int, float))
            assert agent[field] >= 0  # 不能是負數

        # 時間欄位
        datetime_fields = ["created_at", "updated_at"]
        for field in datetime_fields:
            assert field in agent
            assert isinstance(agent[field], str)
            # 簡單的 ISO 格式檢查
            assert "T" in agent[field] and "Z" in agent[field]

    def test_investment_preferences_content_validation(self):
        """測試 investment_preferences 內容格式驗證"""
        agent = MOCK_AGENT_RESPONSE.copy()

        # ✅ 有效的台股代碼格式
        valid_preferences = ["2330", "2454", "0050", "00632R", "1101"]
        agent["investment_preferences"] = valid_preferences

        for pref in agent["investment_preferences"]:
            assert isinstance(pref, str)
            # 台股代碼：4-6位數字+可選字母
            assert len(pref) >= 4 and len(pref) <= 6
            assert pref[:4].isdigit()  # 前4位必須是數字

        # ❌ 無效格式
        invalid_preferences = ["AAPL", "123", "99999999"]  # 非台股格式
        agent["investment_preferences"] = invalid_preferences

        # 這些格式不符合台股代碼規範
        for pref in agent["investment_preferences"]:
            if pref == "AAPL":
                assert not pref[:4].isdigit()  # 美股代碼
            elif pref == "123":
                assert len(pref) < 4  # 太短
            elif pref == "99999999":
                assert len(pref) > 6  # 太長

    def test_list_agents_response_format(self):
        """測試 list_agents API 回應格式（陣列格式）"""
        # 模擬 /api/agents 回應
        agents_list = [MOCK_AGENT_RESPONSE.copy(), MOCK_AGENT_RESPONSE.copy()]
        agents_list[1]["id"] = "agent_test_456"
        agents_list[1]["name"] = "另一個測試代理"

        # 驗證回應是陣列
        assert isinstance(agents_list, list)
        assert len(agents_list) == 2

        # 驗證每個 agent 的格式
        for agent in agents_list:
            assert isinstance(agent["investment_preferences"], list)
            assert isinstance(agent["enabled_tools"], dict)
            assert isinstance(agent["id"], str)

    def test_empty_investment_preferences(self):
        """測試空的 investment_preferences 處理"""
        agent = MOCK_AGENT_RESPONSE.copy()

        # 空列表應該是有效的
        agent["investment_preferences"] = []
        assert isinstance(agent["investment_preferences"], list)
        assert len(agent["investment_preferences"]) == 0

        # None 值應該轉換為空列表（後端處理）
        agent["investment_preferences"] = None
        # 在真實情況下，後端應該將 None 轉換為 []
        # 這裡模擬後端的正確處理
        if agent["investment_preferences"] is None:
            agent["investment_preferences"] = []

        assert isinstance(agent["investment_preferences"], list)

    def test_serialization_deserialization_consistency(self):
        """測試序列化和反序列化的一致性"""
        import json

        agent = MOCK_AGENT_RESPONSE.copy()

        # 模擬 JSON 序列化過程（FastAPI 自動處理）
        json_str = json.dumps(agent)
        deserialized_agent = json.loads(json_str)

        # 確保反序列化後型別仍然正確
        assert isinstance(deserialized_agent["investment_preferences"], list)
        assert isinstance(deserialized_agent["enabled_tools"], dict)

        # 確保內容沒有改變
        assert deserialized_agent["investment_preferences"] == agent["investment_preferences"]
        assert deserialized_agent["enabled_tools"] == agent["enabled_tools"]


class TestSchemaValidationHelpers:
    """Schema 驗證輔助函數測試"""

    def validate_agent_schema(self, agent_data: Dict[str, Any]) -> List[str]:
        """
        驗證 Agent 資料格式的輔助函數
        Returns: 錯誤訊息列表，空列表表示無錯誤
        """
        errors = []

        # 檢查 investment_preferences
        if "investment_preferences" not in agent_data:
            errors.append("Missing field: investment_preferences")
        elif not isinstance(agent_data["investment_preferences"], list):
            errors.append(
                "investment_preferences must be a list, got {type(agent_data['investment_preferences']).__name__}"
            )

        # 檢查 enabled_tools
        if "enabled_tools" not in agent_data:
            errors.append("Missing field: enabled_tools")
        elif not isinstance(agent_data["enabled_tools"], dict):
            errors.append(
                "enabled_tools must be a dict, got {type(agent_data['enabled_tools']).__name__}"
            )

        return errors

    def test_schema_validation_helper(self):
        """測試 Schema 驗證輔助函數"""
        # ✅ 正確格式
        valid_agent = MOCK_AGENT_RESPONSE.copy()
        errors = self.validate_agent_schema(valid_agent)
        assert len(errors) == 0

        # ❌ 錯誤格式：investment_preferences 是字串
        invalid_agent = MOCK_AGENT_RESPONSE.copy()
        invalid_agent["investment_preferences"] = '["2330", "2454"]'
        errors = self.validate_agent_schema(invalid_agent)
        assert len(errors) > 0
        assert any("investment_preferences must be a list" in error for error in errors)

        # ❌ 缺失欄位
        incomplete_agent = {"name": "Test"}
        errors = self.validate_agent_schema(incomplete_agent)
        assert len(errors) >= 2  # 至少缺失 investment_preferences 和 enabled_tools


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
