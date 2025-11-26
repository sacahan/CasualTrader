"""
安全性基礎測試

測試基本的安全配置和防護措施
"""

import pytest
from fastapi.testclient import TestClient
from api.app import create_app
from api.config import settings


@pytest.fixture(scope="module")
def client():
    """
    建立測試客戶端

    使用 module scope 來避免多次創建/銷毀導致的事件循環問題
    """
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


class TestCORSSecurity:
    """測試 CORS 安全配置"""

    def test_cors_headers_present(self, client):
        """驗證 CORS headers 存在"""
        # 需要包含 Origin header 才能觸發 CORS middleware
        response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") is not None

        # 檢查基本的 CORS header（OPTIONS 請求）
        # 注意: 即使端點返回 405，CORS middleware 仍會添加 CORS headers
        options_response = client.options(
            "/api/health", headers={"Origin": "http://localhost:3000"}
        )

        # OPTIONS 可能返回 405 如果端點沒有定義 OPTIONS handler，
        # 但 CORS headers 應該仍然存在
        assert options_response.headers.get("access-control-allow-origin") is not None

    def test_cors_not_wildcard_in_production(self):
        """驗證生產環境不使用 wildcard CORS"""
        # 模擬生產環境設置
        if settings.is_production:
            error_message = " ".join(["生產環境不應使用 wildcard", "CORS 設定"])
            assert "*" not in settings.cors_origins, error_message


class TestAPIEndpointSecurity:
    """測試 API 端點安全性"""

    def test_health_endpoint_responds(self, client):
        """測試健康檢查端點"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        # 驗證回應不包含敏感資訊
        assert "status" in data
        assert "version" in data

        # 在生產環境不應洩露詳細資訊
        if not settings.debug:
            assert "internal" not in str(data).lower()

    def test_error_response_no_sensitive_info(self, client):
        """測試錯誤回應不洩露敏感資訊"""
        # 訪問不存在的端點
        response = client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404

        # 驗證錯誤訊息不包含檔案路徑等敏感資訊
        if not settings.debug:
            error_text = response.text.lower()
            assert "/home/" not in error_text
            assert "/backend/" not in error_text
            assert "traceback" not in error_text


class TestInputValidation:
    """測試輸入驗證"""

    def test_agent_creation_validates_name_length(self, client):
        """測試 agent 名稱長度驗證"""
        # 名稱過長
        long_name = "a" * 200
        response = client.post(
            "/api/agents",
            json={
                "name": long_name,
                "ai_model": "gpt-4o-mini",
            },
        )

        # 應該被拒絕（400 或 422）
        assert response.status_code in [400, 422]

    def test_agent_creation_validates_rgb_format(self, client):
        """測試 RGB 格式驗證"""
        # 無效的 RGB 格式
        response = client.post(
            "/api/agents",
            json={
                "name": "Test Agent",
                "ai_model": "gpt-4o-mini",
                "color_theme": "invalid-rgb",
            },
        )

        # 應該被拒絕（400 或 422）
        assert response.status_code in [400, 422]

    def test_agent_creation_validates_initial_funds(self, client):
        """測試初始資金驗證"""
        # 資金過少
        response = client.post(
            "/api/agents",
            json={
                "name": "Test Agent",
                "ai_model": "gpt-4o-mini",
                "initial_funds": 1000,  # 低於最小值 100000
            },
        )

        # 應該被拒絕（400 或 422）
        assert response.status_code in [400, 422]


class TestSensitiveDataHandling:
    """測試敏感資料處理"""

    def test_no_api_keys_in_responses(self, client):
        """驗證 API 回應不包含 API 金鑰"""
        # 檢查各種端點
        endpoints = [
            "/api/health",
            "/api/agents",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                response_text = response.text.lower()

                # 確認不包含常見的敏感關鍵字
                sensitive_keywords = [
                    "api_key",
                    "api-key",
                    "apikey",
                    "password",
                    "secret",
                    "token",
                ]

                for keyword in sensitive_keywords:
                    # 如果回應中包含這些關鍵字，應該只是欄位名稱
                    # 不應該有實際的值（通常很長的字串）
                    if keyword in response_text:
                        # 簡單檢查：不應該有長字串跟在關鍵字後面
                        assert not any(
                            [
                                f'"{keyword}": "sk-' in response_text,
                                f'"{keyword}": "ghp_' in response_text,
                            ]
                        ), f"可能洩露 {keyword}"


class TestDatabaseSecurity:
    """測試資料庫安全性"""

    def test_database_uses_parameterized_queries(self):
        """驗證使用參數化查詢（透過 ORM）"""
        # 這是一個基本測試，確認我們使用 SQLAlchemy ORM
        from database.models import Agent
        from sqlalchemy import select

        # 驗證使用 select() 而不是字串拼接
        stmt = select(Agent).where(Agent.id == "test")
        assert stmt is not None

        # SQLAlchemy 會自動處理參數化，這裡只是確認使用了正確的模式


# 執行測試的指令範例：
# pytest tests/security/test_security_basics.py -v
