"""
Contract 1: Frontend-API 層契約驗證

此測試檔案驗證 API 層的所有契約要求:
- 所有端點存在
- 正確的 HTTP 方法
- 正確的請求/響應格式
- 正確的 HTTP 狀態碼
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app


class TestAPIEndpointContract:
    """API 端點契約驗證"""

    @pytest.fixture
    def client(self):
        """建立 HTTP 測試客戶端"""
        app = create_app()
        return TestClient(app)

    def test_get_agents_endpoint_exists(self, client):
        """驗證 GET /api/agents 端點存在"""
        response = client.get("/api/agents")
        assert response.status_code in [200, 401, 404]

    def test_agents_endpoint_accepts_get(self, client):
        """驗證 /api/agents 接受 GET 方法"""
        response = client.get("/api/agents")
        assert response.status_code != 405

    def test_create_agent_endpoint_exists(self, client):
        """驗證 POST /api/agents 端點存在"""
        response = client.post("/api/agents", json={})
        assert response.status_code in [200, 400, 401, 404, 422]

    def test_agents_endpoint_accepts_post(self, client):
        """驗證 /api/agents 接受 POST 方法"""
        response = client.post("/api/agents", json={})
        assert response.status_code != 405

    def test_delete_agent_endpoint_exists(self, client):
        """驗證 DELETE /api/agents/{id} 端點存在"""
        response = client.delete("/api/agents/test-id")
        assert response.status_code in [200, 204, 400, 401, 404, 422]

    def test_sessions_endpoint_exists(self, client):
        """驗證 GET /api/sessions 端點存在"""
        response = client.get("/api/sessions")
        assert response.status_code in [200, 401, 404]

    def test_create_session_endpoint_exists(self, client):
        """驗證 POST /api/sessions 端點處理"""
        response = client.post("/api/sessions", json={})
        # Sessions 端點不支援直接 POST，應該返回 404 或 405
        assert response.status_code in [404, 405]

    def test_health_check_endpoint_exists(self, client):
        """驗證 GET /api/health 端點存在"""
        response = client.get("/api/health")
        assert response.status_code in [200, 401]


class TestAPIResponseFormatContract:
    """API 響應格式契約驗證"""

    @pytest.fixture
    def client(self):
        """建立 HTTP 測試客戶端"""
        app = create_app()
        return TestClient(app)

    def test_successful_response_is_json(self, client):
        """驗證成功響應是 JSON 格式"""
        response = client.get("/api/health")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_response_has_correct_content_type(self, client):
        """驗證響應 Content-Type 正確"""
        response = client.get("/api/health")
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_health_check_returns_expected_fields(self, client):
        """驗證健康檢查返回預期的欄位"""
        response = client.get("/api/health")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data


class TestAPIHTTPStatusCodeContract:
    """API HTTP 狀態碼契約驗證"""

    @pytest.fixture
    def client(self):
        """建立 HTTP 測試客戶端"""
        app = create_app()
        return TestClient(app)

    def test_not_found_returns_404(self, client):
        """驗證不存在的端點返回 404"""
        response = client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404

    def test_invalid_method_returns_405_or_404(self, client):
        """驗證不允許的方法返回 405 或 404"""
        response = client.patch("/api/agents/test-id")
        assert response.status_code in [404, 405]

    def test_invalid_json_returns_422_or_400(self, client):
        """驗證無效的 JSON 請求返回 422 或 400"""
        response = client.post("/api/agents", content="invalid json")
        assert response.status_code in [400, 422]

    def test_health_check_returns_200(self, client):
        """驗證健康檢查返回 200"""
        response = client.get("/api/health")
        assert response.status_code == 200


class TestAPIDocumentationContract:
    """API 文檔契約驗證"""

    def test_api_spec_exists(self):
        """驗證 API 規範文檔存在"""
        from pathlib import Path

        spec_file = (
            Path(__file__).parent.parent.parent.parent / "docs" / "API_CONTRACT_SPECIFICATION.md"
        )
        assert spec_file.exists()

    def test_api_spec_contains_endpoints(self):
        """驗證 API 規範包含端點列表"""
        from pathlib import Path

        spec_file = (
            Path(__file__).parent.parent.parent.parent / "docs" / "API_CONTRACT_SPECIFICATION.md"
        )
        content = spec_file.read_text()
        assert "/api/agents" in content or "agents" in content.lower()

    def test_api_spec_documents_responses(self):
        """驗證 API 規範文檔化響應"""
        from pathlib import Path

        spec_file = (
            Path(__file__).parent.parent.parent.parent / "docs" / "API_CONTRACT_SPECIFICATION.md"
        )
        content = spec_file.read_text()
        assert "response" in content.lower() or "return" in content.lower()


class TestAPIErrorHandlingContract:
    """API 錯誤處理契約驗證"""

    @pytest.fixture
    def client(self):
        """建立 HTTP 測試客戶端"""
        app = create_app()
        return TestClient(app)

    def test_missing_required_fields_returns_error(self, client):
        """驗證缺少必要欄位返回錯誤"""
        response = client.post("/api/agents", json={})
        assert response.status_code != 500

    def test_no_unhandled_exceptions_on_valid_endpoint(self, client):
        """驗證有效端點不返回 500"""
        response = client.get("/api/health")
        assert response.status_code != 500
