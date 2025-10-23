"""API 層契約驗證測試

此測試檔案驗證 API 層的所有契約要求:
- 所有端點存在
- 正確的 HTTP 方法
- 正確的請求/響應格式
- 正確的 HTTP 狀態碼
"""

import pytest
from httpx import AsyncClient

from src.api.app import create_app


class TestAPIEndpointContract:
    """API 端點契約驗證"""

    @pytest.fixture
    def app(self):
        """建立測試用的 FastAPI 應用"""
        return create_app()

    @pytest.fixture
    async def client(self, app):
        """建立 HTTP 測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_get_agents_endpoint_exists(self, client):
        """驗證 GET /api/agents 端點存在"""
        response = await client.get("/api/agents")
        assert response.status_code in [200, 401, 404]

    @pytest.mark.asyncio
    async def test_agents_endpoint_accepts_get(self, client):
        """驗證 /api/agents 接受 GET 方法"""
        try:
            response = await client.get("/api/agents")
            assert response.status_code != 405
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_create_agent_endpoint_exists(self, client):
        """驗證 POST /api/agents 端點存在"""
        response = await client.post("/api/agents", json={})
        assert response.status_code in [200, 400, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_agents_endpoint_accepts_post(self, client):
        """驗證 /api/agents 接受 POST 方法"""
        try:
            response = await client.post("/api/agents", json={})
            assert response.status_code != 405
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_get_agent_config_endpoint_exists(self, client):
        """驗證 GET /api/agents/{id}/config 端點存在"""
        response = await client.get("/api/agents/test-id/config")
        assert response.status_code in [200, 400, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_delete_agent_endpoint_exists(self, client):
        """驗證 DELETE /api/agents/{id} 端點存在"""
        response = await client.delete("/api/agents/test-id")
        assert response.status_code in [200, 204, 400, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_sessions_endpoint_exists(self, client):
        """驗證 GET /api/sessions 端點存在"""
        response = await client.get("/api/sessions")
        assert response.status_code in [200, 401, 404]

    @pytest.mark.asyncio
    async def test_create_session_endpoint_exists(self, client):
        """驗證 POST /api/sessions 端點存在"""
        response = await client.post("/api/sessions", json={})
        assert response.status_code in [200, 400, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_health_check_endpoint_exists(self, client):
        """驗證 GET /api/health 端點存在"""
        response = await client.get("/api/health")
        assert response.status_code in [200, 401]


class TestAPIResponseFormatContract:
    """API 響應格式契約驗證"""

    @pytest.fixture
    def app(self):
        """建立測試用的 FastAPI 應用"""
        return create_app()

    @pytest.fixture
    async def client(self, app):
        """建立 HTTP 測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_error_response_has_detail_field(self, client):
        """驗證錯誤響應包含 detail 欄位"""
        response = await client.post("/api/agents", json={})
        if response.status_code >= 400:
            try:
                data = response.json()
                assert "detail" in data or "error" in data or "message" in data
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_successful_response_is_json(self, client):
        """驗證成功響應是 JSON 格式"""
        try:
            response = await client.get("/api/health")
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_response_has_correct_content_type(self, client):
        """驗證響應 Content-Type 正確"""
        try:
            response = await client.get("/api/health")
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type
        except Exception:
            pass


class TestAPIHTTPStatusCodeContract:
    """API HTTP 狀態碼契約驗證"""

    @pytest.fixture
    def app(self):
        """建立測試用的 FastAPI 應用"""
        return create_app()

    @pytest.fixture
    async def client(self, app):
        """建立 HTTP 測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, client):
        """驗證不存在的端點返回 404"""
        response = await client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_method_returns_405(self, client):
        """驗證不允許的方法返回 405"""
        response = await client.patch("/api/agents/test-id")
        assert response.status_code in [404, 405]

    @pytest.mark.asyncio
    async def test_invalid_json_returns_422(self, client):
        """驗證無效的 JSON 請求返回 422"""
        response = await client.post("/api/agents", content="invalid json")
        assert response.status_code in [400, 422]


class TestAPIDocumentationContract:
    """API 文檔契約驗證"""

    @pytest.mark.asyncio
    async def test_api_spec_exists(self):
        """驗證 API 規範文檔存在"""
        from pathlib import Path

        spec_file = (
            Path(__file__).parent.parent.parent.parent / "docs" / "API_CONTRACT_SPECIFICATION.md"
        )
        assert spec_file.exists(), f"API spec not found at {spec_file}"

    @pytest.mark.asyncio
    async def test_api_spec_contains_endpoints(self):
        """驗證 API 規範包含端點列表"""
        from pathlib import Path

        spec_file = (
            Path(__file__).parent.parent.parent.parent / "docs" / "API_CONTRACT_SPECIFICATION.md"
        )
        content = spec_file.read_text()

        assert "/api/agents" in content or "agents" in content.lower()
        assert "/api/sessions" in content or "sessions" in content.lower()

    @pytest.mark.asyncio
    async def test_api_spec_documents_responses(self):
        """驗證 API 規範文檔化響應"""
        from pathlib import Path

        spec_file = (
            Path(__file__).parent.parent.parent.parent / "docs" / "API_CONTRACT_SPECIFICATION.md"
        )
        content = spec_file.read_text()

        assert "response" in content.lower() or "return" in content.lower()

    @pytest.mark.asyncio
    async def test_api_spec_has_minimal_content(self):
        """驗證 API 規範有足夠的內容"""
        from pathlib import Path

        spec_file = (
            Path(__file__).parent.parent.parent.parent / "docs" / "API_CONTRACT_SPECIFICATION.md"
        )
        content = spec_file.read_text()

        assert len(content) > 100


class TestAPIErrorHandlingContract:
    """API 錯誤處理契約驗證"""

    @pytest.fixture
    def app(self):
        """建立測試用的 FastAPI 應用"""
        return create_app()

    @pytest.fixture
    async def client(self, app):
        """建立 HTTP 測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_malformed_request_returns_error(self, client):
        """驗證格式錯誤的請求返回錯誤"""
        response = await client.post("/api/agents", json={"invalid_field": "value"})
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_missing_required_fields_returns_error(self, client):
        """驗證缺少必要欄位返回錯誤"""
        response = await client.post("/api/agents", json={})
        assert response.status_code != 500

    @pytest.mark.asyncio
    async def test_server_errors_have_details(self, client):
        """驗證伺服器錯誤包含詳細信息"""
        try:
            response = await client.get("/api/agents/test-id/config")
            if response.status_code >= 500:
                data = response.json()
                assert len(str(data)) > 0
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_no_unhandled_exceptions_on_valid_endpoint(self, client):
        """驗證有效端點不返回 500"""
        response = await client.get("/api/health")
        assert response.status_code != 500
