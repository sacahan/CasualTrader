"""
Unit tests for Agent graph visualization utilities

測試 save_agent_graph 函數的各種使用場景
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from common.agent_utils import save_agent_graph


def create_mock_agent():
    """建立一個通過 isinstance(agent, Agent) 檢查的 Mock Agent"""
    mock_agent = MagicMock()
    # 這將使 isinstance 檢查通過
    mock_agent.__class__ = type("Agent", (), {})
    return mock_agent


class TestSaveAgentGraph:
    """save_agent_graph 函數的測試套件"""

    def test_save_agent_graph_with_valid_agent(self):
        """測試使用有效的 Agent 實例保存圖形"""
        mock_agent = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
                with patch("common.agent_utils.isinstance") as mock_isinstance:
                    mock_isinstance.return_value = True
                    with patch("common.agent_utils.draw_graph") as mock_draw:
                        success, result = save_agent_graph(
                            agent=mock_agent,
                            agent_id="test_agent",
                            output_dir=temp_dir,
                        )

                        # 驗證 draw_graph 被呼叫
                        mock_draw.assert_called_once()

                        # 驗證回傳值
                        assert success is True
                        assert "test_agent.svg" in result
                        assert result.endswith(".svg")

    def test_save_agent_graph_with_default_output_dir(self):
        """測試使用預設輸出目錄"""
        mock_agent = Mock()

        with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
            with patch("common.agent_utils.isinstance") as mock_isinstance:
                mock_isinstance.return_value = True
                with patch("common.agent_utils.draw_graph") as mock_draw:
                    success, result = save_agent_graph(
                        agent=mock_agent,
                        agent_id="test_agent",
                        output_dir=None,  # 使用預設
                    )

                    # 驗證呼叫成功
                    mock_draw.assert_called_once()
                    assert success is True
                    assert "test_agent.svg" in result

    def test_save_agent_graph_with_relative_path(self):
        """測試使用相對路徑作為輸出目錄"""
        mock_agent = Mock()

        with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
            with patch("common.agent_utils.isinstance") as mock_isinstance:
                mock_isinstance.return_value = True
                with patch("common.agent_utils.draw_graph") as mock_draw:
                    # 使用相對路徑
                    success, result = save_agent_graph(
                        agent=mock_agent,
                        agent_id="test_agent",
                        output_dir="custom_logs",  # 相對路徑
                    )

                    mock_draw.assert_called_once()
                    assert success is True
                    assert "test_agent.svg" in result

    def test_save_agent_graph_with_absolute_path(self):
        """測試使用絕對路徑作為輸出目錄"""
        mock_agent = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
                with patch("common.agent_utils.isinstance") as mock_isinstance:
                    mock_isinstance.return_value = True
                    with patch("common.agent_utils.draw_graph") as mock_draw:
                        success, result = save_agent_graph(
                            agent=mock_agent,
                            agent_id="test_agent",
                            output_dir=temp_dir,
                        )

                        mock_draw.assert_called_once()
                        assert success is True
                    assert temp_dir in result

    def test_save_agent_graph_with_invalid_agent_type(self):
        """測試使用錯誤的 Agent 類型"""
        # 不是 Agent 的對象
        invalid_agent = "not_an_agent"

        with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
            success, result = save_agent_graph(
                agent=invalid_agent,
                agent_id="test_agent",
            )

            # 應該失敗
            assert success is False
            assert "Invalid agent type" in result or "Expected" in result

    def test_save_agent_graph_with_draw_graph_exception(self):
        """測試 draw_graph 拋出異常時的處理"""
        mock_agent = Mock()

        with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
            with patch("common.agent_utils.isinstance") as mock_isinstance:
                mock_isinstance.return_value = True
                with patch("common.agent_utils.draw_graph") as mock_draw:
                    # 模擬 draw_graph 拋出異常
                    mock_draw.side_effect = RuntimeError("Failed to draw graph")

                    with tempfile.TemporaryDirectory() as temp_dir:
                        success, result = save_agent_graph(
                            agent=mock_agent,
                            agent_id="test_agent",
                            output_dir=temp_dir,
                        )

                        # 應該捕獲異常並返回失敗
                        assert success is False
                        assert "Failed to draw graph" in result or "RuntimeError" in result

    def test_save_agent_graph_creates_directory(self):
        """測試自動創建不存在的目錄"""
        mock_agent = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 創建一個不存在的子目錄路徑
            non_existent_dir = Path(temp_dir) / "subdir" / "logs"

            with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
                with patch("common.agent_utils.isinstance") as mock_isinstance:
                    mock_isinstance.return_value = True
                    with patch("common.agent_utils.draw_graph") as mock_draw:
                        success, result = save_agent_graph(
                            agent=mock_agent,
                            agent_id="test_agent",
                            output_dir=str(non_existent_dir),
                        )

                        # 應該成功
                        assert success is True
                        mock_draw.assert_called_once()

    def test_save_agent_graph_returns_correct_filepath(self):
        """測試返回的文件路徑格式正確"""
        mock_agent = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
                with patch("common.agent_utils.isinstance") as mock_isinstance:
                    mock_isinstance.return_value = True
                    with patch("common.agent_utils.draw_graph"):
                        agent_id = "my_special_agent"
                        success, result = save_agent_graph(
                            agent=mock_agent,
                            agent_id=agent_id,
                            output_dir=temp_dir,
                        )

                        # 驗證返回的路徑包含正確的 agent_id 和副檔名
                        assert success is True
                        assert agent_id in result
                        assert result.endswith(".svg")

    def test_save_agent_graph_with_special_characters_in_agent_id(self):
        """測試處理包含特殊字符的 agent_id"""
        mock_agent = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
                with patch("common.agent_utils.isinstance") as mock_isinstance:
                    mock_isinstance.return_value = True
                    with patch("common.agent_utils.draw_graph"):
                        agent_id = "agent-test_001"
                        success, result = save_agent_graph(
                            agent=mock_agent,
                            agent_id=agent_id,
                            output_dir=temp_dir,
                        )

                        assert success is True
                        assert agent_id in result


class TestSaveAgentGraphIntegration:
    """save_agent_graph 的集成測試"""

    def test_save_agent_graph_with_path_object(self):
        """測試使用 Path 對象作為輸出目錄"""
        mock_agent = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
                with patch("common.agent_utils.isinstance") as mock_isinstance:
                    mock_isinstance.return_value = True
                    with patch("common.agent_utils.draw_graph"):
                        success, result = save_agent_graph(
                            agent=mock_agent,
                            agent_id="test_agent",
                            output_dir=temp_path,
                        )

                        assert success is True

    def test_save_agent_graph_error_handling_robustness(self):
        """測試錯誤處理的健壯性"""
        mock_agent = Mock()

        with patch("common.agent_utils.SKIP_AGENT_GRAPH", False):
            with patch("common.agent_utils.isinstance") as mock_isinstance:
                mock_isinstance.return_value = True
                with patch("common.agent_utils.draw_graph") as mock_draw:
                    # 模擬各種異常
                    mock_draw.side_effect = Exception("Generic error")

                    success, result = save_agent_graph(
                        agent=mock_agent,
                        agent_id="test_agent",
                        output_dir=None,
                    )

                    assert success is False
                    assert len(result) > 0  # 應該有錯誤訊息
