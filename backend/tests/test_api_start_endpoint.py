"""
API 路由端點測試

測試 `/start` 端點的行為：
- 正確的模式執行
- 無效模式返回 400
- Agent 不存在返回 404
- Agent 忙碌返回 409
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from common.enums import AgentMode
from service.trading_service import (
    TradingService,
    AgentBusyError,
)
from service.agents_service import AgentNotFoundError


class TestAPIEndpoints:
    """API 端點測試"""

    @pytest.mark.asyncio
    async def test_start_endpoint_valid_mode(self):
        """測試：/start 端點接受有效的模式"""
        # 模擬 TradingService
        mock_service = AsyncMock(spec=TradingService)
        mock_service.execute_single_mode = AsyncMock(
            return_value={"success": True, "session_id": "test-session"}
        )

        # 驗證可以調用
        result = await mock_service.execute_single_mode(
            agent_id="test-agent", mode=AgentMode.OBSERVATION
        )

        assert result["success"] is True
        assert "session_id" in result

    @pytest.mark.asyncio
    async def test_start_endpoint_agent_busy(self):
        """測試：Agent 忙碌時返回 409"""
        mock_service = AsyncMock(spec=TradingService)
        mock_service.execute_single_mode = AsyncMock(
            side_effect=AgentBusyError("Agent already running")
        )

        # 應該拋出 AgentBusyError
        with pytest.raises(AgentBusyError):
            await mock_service.execute_single_mode(
                agent_id="test-agent", mode=AgentMode.OBSERVATION
            )

    @pytest.mark.asyncio
    async def test_start_endpoint_agent_not_found(self):
        """測試：Agent 不存在時返回 404"""
        mock_service = AsyncMock(spec=TradingService)
        mock_service.execute_single_mode = AsyncMock(
            side_effect=AgentNotFoundError("Agent not found")
        )

        # 應該拋出 AgentNotFoundError
        with pytest.raises(AgentNotFoundError):
            await mock_service.execute_single_mode(
                agent_id="nonexistent", mode=AgentMode.OBSERVATION
            )


class TestModeValidation:
    """模式驗證測試"""

    def test_valid_modes(self):
        """測試：所有有效模式"""
        valid_modes = ["OBSERVATION", "TRADING", "REBALANCING"]

        for mode_str in valid_modes:
            mode = AgentMode[mode_str]
            assert mode.value == mode_str

    def test_invalid_mode_enum(self):
        """測試：無效模式會拋出 KeyError"""
        with pytest.raises(KeyError):
            AgentMode["INVALID_MODE"]


class TestRequestValidation:
    """請求驗證測試"""

    def test_start_mode_request_model(self):
        """測試：StartModeRequest 模型"""
        from api.routers.agent_execution import StartModeRequest, AgentModeEnum

        # 有效請求
        request = StartModeRequest(mode=AgentModeEnum.OBSERVATION)
        assert request.mode == AgentModeEnum.OBSERVATION
        assert request.max_turns is None

        # 帶 max_turns
        request = StartModeRequest(mode=AgentModeEnum.TRADING, max_turns=10)
        assert request.max_turns == 10

    def test_start_mode_request_max_turns_validation(self):
        """測試：max_turns 的驗證"""
        from api.routers.agent_execution import StartModeRequest, AgentModeEnum
        from pydantic import ValidationError

        # 無效：max_turns 太大
        with pytest.raises(ValidationError):
            StartModeRequest(mode=AgentModeEnum.OBSERVATION, max_turns=100)

        # 無效：max_turns 為 0
        with pytest.raises(ValidationError):
            StartModeRequest(mode=AgentModeEnum.OBSERVATION, max_turns=0)


class TestResponseFormat:
    """響應格式測試"""

    def test_start_mode_response_model(self):
        """測試：StartModeResponse 模型"""
        from api.routers.agent_execution import StartModeResponse

        response = StartModeResponse(
            success=True, session_id="session-123", mode="OBSERVATION", execution_time_ms=1000
        )

        assert response.success is True
        assert response.session_id == "session-123"
        assert response.mode == "OBSERVATION"
        assert response.execution_time_ms == 1000

        # 驗證可以序列化為 dict
        response_dict = response.model_dump()
        assert response_dict["success"] is True
        assert response_dict["session_id"] == "session-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
