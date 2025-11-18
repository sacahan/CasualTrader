# CasualTrader 安全漏洞檢視報告

**日期**: 2025-11-18  
**版本**: 1.0.0  
**狀態**: 初步檢視完成

## 執行摘要

本次安全檢視針對 CasualTrader 專案進行了全面的安全漏洞分析，檢查範圍包括：
- SQL 注入漏洞
- 命令注入漏洞
- 路徑穿越漏洞
- 敏感資訊洩露
- 認證與授權問題
- CORS 配置
- 輸入驗證

## 檢視結果總覽

### ✅ 安全做法 (良好實踐)

1. **SQL 注入防護**
   - ✅ 使用 SQLAlchemy ORM 進行資料庫操作
   - ✅ 所有查詢使用參數化語句
   - ✅ 無直接字串拼接 SQL 查詢

2. **敏感資訊管理**
   - ✅ API 金鑰通過環境變數管理
   - ✅ 有 `.env.example` 範本文件
   - ✅ 無硬編碼的敏感憑證

3. **錯誤處理**
   - ✅ 適當的異常處理機制
   - ✅ 生產環境隱藏詳細錯誤資訊

4. **代碼結構**
   - ✅ 使用 Type Hints 提高代碼可讀性
   - ✅ 遵循 PEP 8 編碼規範

### ⚠️ 需要關注的安全問題

#### 1. 【中等】CORS 配置過於寬鬆 (生產環境風險)

**位置**: `backend/src/api/app.py:213-219`

**問題描述**:
在 DEBUG 模式下，CORS 設置為允許所有來源 (`allow_origins=["*"]`)，這在生產環境中可能導致跨站請求偽造 (CSRF) 攻擊。

**受影響代碼**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.debug else ["*"],
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**風險等級**: 中等

**建議修復**:
1. 即使在開發環境，也應限制 CORS 來源為具體的域名列表
2. 生產環境必須明確設置允許的來源
3. 考慮實施 CSRF token 機制

**修復範例**:
```python
# 建議的配置
if settings.is_production:
    # 生產環境：嚴格限制
    allowed_origins = settings.cors_origins
else:
    # 開發環境：允許本地開發域名
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

#### 2. 【低】缺少 API 認證機制

**位置**: 所有 API 端點 (`backend/src/api/routers/`)

**問題描述**:
當前所有 API 端點都沒有實施認證和授權機制，任何人都可以訪問和操作系統。

**風險等級**: 低 (目前為模擬器系統，但未來擴展可能需要)

**建議修復**:
1. 實施 API Key 認證或 OAuth2 認證
2. 為不同用戶角色設置權限控制
3. 實施請求頻率限制 (Rate Limiting)

**修復範例**:
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=403, detail="無效的 API Key"
        )
    return api_key

# 在路由中使用
@router.get("/agents", dependencies=[Depends(verify_api_key)])
async def list_agents():
    ...
```

---

#### 3. 【低】硬編碼路徑風險

**位置**: `backend/src/api/mcp_client.py:40-46`

**問題描述**:
MCP 客戶端中硬編碼了本地開發路徑，可能導致在其他環境無法正常運行。

**受影響代碼**:
```python
self.server_params = {
    "command": "uvx",
    "args": [
        "--from",
        "/Users/sacahan/Documents/workspace/CasualMarket",  # 硬編碼路徑
        "casual-market-mcp",
    ],
}
```

**風險等級**: 低 (主要是可維護性問題)

**建議修復**:
1. 將路徑配置移至環境變數
2. 使用相對路徑或自動檢測機制

**修復範例**:
```python
import os
from pathlib import Path

# 從環境變數讀取，或使用預設值
casual_market_path = os.getenv(
    "CASUAL_MARKET_PATH",
    "casual-market-mcp"  # 如果已安裝到 PATH，直接使用命令名
)

self.server_params = {
    "command": "uvx",
    "args": ["--from", casual_market_path, "casual-market-mcp"]
    if os.path.isabs(casual_market_path)
    else ["casual-market-mcp"],
}
```

---

#### 4. 【低】缺少請求頻率限制

**位置**: 所有 API 端點

**問題描述**:
沒有實施請求頻率限制，可能導致 DoS 攻擊或資源濫用。

**風險等級**: 低

**建議修復**:
使用 slowapi 或類似庫實施請求頻率限制。

**修復範例**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.get("/agents")
@limiter.limit("10/minute")
async def list_agents(request: Request):
    ...
```

---

#### 5. 【資訊】錯誤訊息可能洩露系統資訊

**位置**: `backend/src/api/app.py:199-209`

**問題描述**:
在 DEBUG 模式下，錯誤訊息會返回完整的異常資訊，可能洩露系統結構。

**受影響代碼**:
```python
return JSONResponse(
    status_code=500,
    content={
        "detail": "Internal server error",
        "error": str(exc) if settings.debug else "An error occurred",
    },
)
```

**風險等級**: 資訊洩露

**建議修復**:
確保生產環境 DEBUG 設為 False。

---

## 安全最佳實踐建議

### 1. 部署前檢查清單

- [ ] 確保 `DEBUG=false` 在生產環境
- [ ] 確保 `ENVIRONMENT=production`
- [ ] 設置嚴格的 CORS 來源列表
- [ ] 檢查所有 API 金鑰已設置且安全
- [ ] 審查日誌級別設置 (`LOG_LEVEL=WARNING` 或 `ERROR`)
- [ ] 確保資料庫連接使用加密 (如未來使用 PostgreSQL)

### 2. 環境變數安全

**必須設置的環境變數**:
```bash
# 生產環境配置範例
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# 嚴格的 CORS 設置
CORS_ORIGINS='["https://yourdomain.com"]'
CORS_ALLOW_CREDENTIALS=true

# API 金鑰 (確保安全)
OPENAI_API_KEY=<secure-key>
TAVILY_API_KEY=<secure-key>
GITHUB_PERSONAL_ACCESS_TOKEN=<secure-token>
```

### 3. 監控與日誌

建議實施：
1. 日誌監控和告警機制
2. 異常活動檢測
3. API 訪問日誌分析
4. 定期安全審計

### 4. 資料保護

目前使用 SQLite：
1. 確保資料庫文件權限正確 (僅應用程序可讀寫)
2. 定期備份資料庫
3. 未來考慮遷移到支持加密的資料庫 (如 PostgreSQL with encryption)

---

## 依賴套件安全

### 已知漏洞檢查

建議定期運行：
```bash
# 檢查 Python 依賴漏洞
pip install safety
safety check

# 或使用 pip-audit
pip install pip-audit
pip-audit
```

### 建議的安全依賴

可考慮添加以下安全相關套件：
```toml
[project.optional-dependencies]
security = [
    "slowapi>=0.1.9",          # API 請求頻率限制
    "python-multipart>=0.0.6", # 檔案上傳安全處理
    "cryptography>=41.0.0",    # 加密支持
]
```

---

## 修復優先級建議

### 高優先級 (立即修復)
- 無

### 中優先級 (生產環境前修復)
1. ⚠️ CORS 配置優化
2. ⚠️ 實施基本認證機制 (如計劃公開部署)

### 低優先級 (持續改進)
1. MCP 客戶端路徑配置優化
2. 添加請求頻率限制
3. 實施完整的日誌監控

---

## 結論

**整體安全評級**: ⭐⭐⭐⭐ (4/5 - 良好)

CasualTrader 專案在代碼層面展現了良好的安全實踐：
- ✅ 正確使用 ORM 防止 SQL 注入
- ✅ 妥善管理敏感資訊
- ✅ 無明顯的高危漏洞

**主要建議**:
1. 在生產環境部署前，必須優化 CORS 配置
2. 如果系統對外開放，應實施認證機制
3. 持續監控和更新依賴套件

**下一步行動**:
1. 實施本報告中的中優先級修復
2. 建立安全測試流程
3. 定期進行安全審計

---

## 附錄

### A. 安全測試工具推薦

1. **靜態代碼分析**
   - Bandit: Python 安全問題檢測
   - Safety: 依賴漏洞檢查
   - pip-audit: PyPI 套件漏洞掃描

2. **動態測試**
   - OWASP ZAP: Web 應用程序安全測試
   - Burp Suite: 滲透測試工具

3. **依賴管理**
   - Dependabot: GitHub 自動依賴更新
   - Snyk: 持續漏洞監控

### B. 參考資源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI 安全最佳實踐](https://fastapi.tiangolo.com/tutorial/security/)
- [Python 安全編碼指南](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**報告生成時間**: 2025-11-18  
**檢視人員**: GitHub Copilot Security Agent  
**下次審查建議**: 3-6 個月後或重大功能更新時
