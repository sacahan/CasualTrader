# API 套件依賴清單

**版本**: 1.0
**日期**: 2025-10-06
**相關**: API_IMPLEMENTATION.md

---

## 📦 核心依賴套件

### 1. Web 框架和 API

```toml
# 主要 Web 框架
"fastapi>=0.104.0"          # 現代化異步 Web 框架
"uvicorn[standard]>=0.24.0" # ASGI 服務器
"websockets>=12.0"          # WebSocket 支援

# 中間件和擴展
"fastapi-cors>=1.0.0"       # CORS 支援
"fastapi-limiter>=0.1.5"    # API 速率限制
```

### 2. 數據驗證和模型

```toml
"pydantic>=2.5.0"           # 數據驗證和序列化
"pydantic-settings>=2.1.0"  # 設定管理
"typing-extensions>=4.8.0"  # 類型提示擴展
```

### 3. 資料庫和 ORM

```toml
"sqlalchemy>=2.0.0"         # ORM 框架
"alembic>=1.13.0"          # 資料庫遷移
"asyncpg>=0.29.0"          # PostgreSQL 異步驅動
"aiosqlite>=0.19.0"        # SQLite 異步驅動（開發用）
```

### 4. 快取和會話

```toml
"redis>=5.0.0"             # Redis 客戶端
"aioredis>=2.0.0"          # Redis 異步客戶端
"python-memcached>=1.62"   # Memcached 支援（可選）
```

### 5. AI 和 Agent 整合

```toml
"openai>=1.30.0"           # OpenAI API 客戶端
"openai-agents>=0.1.0"     # OpenAI Agent SDK
"anthropic>=0.25.0"        # Claude API（可選）
```

### 6. MCP 工具整合

```toml
"casual-market-mcp>=1.0.0" # 台灣股市 MCP 工具
"mcp>=1.0.0"               # Model Context Protocol 核心
"fastmcp>=2.7.0"           # FastMCP 框架
```

### 7. HTTP 客戶端和網路

```toml
"httpx>=0.25.0"            # 現代化 HTTP 客戶端
"aiohttp>=3.9.0"           # 異步 HTTP 客戶端
"requests>=2.31.0"         # 傳統 HTTP 客戶端（相容性）
```

### 8. 日誌和監控

```toml
"structlog>=23.2.0"        # 結構化日誌
"loguru>=0.7.0"            # 簡化日誌記錄
"prometheus-client>=0.19.0" # Prometheus 指標
"sentry-sdk[fastapi]>=1.38.0" # 錯誤追蹤（生產環境）
```

### 9. 安全性

```toml
"passlib[bcrypt]>=1.7.4"   # 密碼雜湊
"python-jose[cryptography]>=3.3.0" # JWT 處理
"python-multipart>=0.0.6"  # 表單數據處理
"cryptography>=41.0.0"     # 加密工具
```

### 10. 環境和配置

```toml
"python-dotenv>=1.0.0"     # 環境變數載入
"pyyaml>=6.0.1"            # YAML 配置支援
"click>=8.1.0"             # CLI 工具
```

### 11. 資料處理

```toml
"pandas>=2.1.0"            # 數據分析
"numpy>=1.24.0"            # 數值計算
"python-dateutil>=2.8.0"   # 日期時間處理
"pytz>=2023.3"             # 時區處理
```

### 12. 工具和輔助

```toml
"rich>=13.7.0"             # 美化終端輸出
"psutil>=5.9.0"            # 系統監控
"schedule>=1.2.0"          # 任務排程
"celery>=5.3.0"            # 異步任務隊列（可選）
```

---

## 🧪 開發依賴套件

```toml
[project.optional-dependencies]
dev = [
    # 測試框架
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-xdist>=3.5.0",     # 並行測試

    # 代碼品質
    "ruff>=0.1.0",              # Linting 和格式化
    "mypy>=1.7.0",              # 類型檢查
    "black>=23.11.0",           # 代碼格式化
    "isort>=5.12.0",            # import 排序

    # 開發工具
    "pre-commit>=3.6.0",        # Git hooks
    "ipython>=8.17.0",          # 互動式 Python
    "jupyter>=1.0.0",           # Jupyter Notebook
    "watchdog>=3.0.0",          # 檔案監控

    # 文檔生成
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
    "mkdocs-mermaid2-plugin>=1.1.0",

    # 效能分析
    "memory-profiler>=0.61.0",
    "py-spy>=0.3.14",
]
```

---

## 🚀 生產環境依賴

```toml
production = [
    # 生產服務器
    "gunicorn>=21.2.0",         # WSGI 服務器（備用）
    "supervisor>=4.2.5",        # 進程管理

    # 監控和告警
    "sentry-sdk[fastapi]>=1.38.0", # 錯誤追蹤
    "newrelic>=8.10.0",         # 應用監控（可選）

    # 安全性增強
    "slowapi>=0.1.9",           # 速率限制
    "authlib>=1.2.1",           # OAuth/JWT 擴展
]
```

---

## 📋 套件安裝指令

### 使用 uv (推薦)

```bash
# 安裝基本依賴
uv add fastapi uvicorn[standard] sqlalchemy alembic pydantic

# 安裝 AI 相關套件
uv add openai openai-agents casual-market-mcp

# 安裝資料庫驅動
uv add asyncpg aiosqlite redis aioredis

# 安裝開發依賴
uv add --dev pytest pytest-asyncio ruff mypy

# 一次安裝所有核心依賴
uv add fastapi uvicorn[standard] sqlalchemy alembic pydantic \
       openai openai-agents casual-market-mcp \
       asyncpg redis aioredis httpx structlog \
       passlib[bcrypt] python-jose[cryptography] \
       python-dotenv pyyaml click rich psutil
```

### 使用 pip

```bash
# 從 requirements.txt 安裝
pip install -r requirements.txt

# 開發依賴
pip install -r requirements-dev.txt
```

---

## 🔧 套件配置範例

### 1. FastAPI 應用設定

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="CasualTrader API",
    description="AI 股票交易模擬器 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 資料庫配置

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# PostgreSQL
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/casualtrader"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

### 3. Redis 配置

```python
import aioredis
from aioredis import Redis

async def get_redis() -> Redis:
    redis = aioredis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True
    )
    return redis
```

### 4. OpenAI Agent 配置

```python
from openai import AsyncOpenAI
from openai_agents import Agent

client = AsyncOpenAI(api_key="your-api-key")

agent = Agent(
    name="trading_agent",
    instructions="你是一個專業的股票交易助手...",
    model="gpt-4o-mini",
    tools=[...]  # MCP 工具
)
```

---

## ⚠️ 注意事項

### 版本相容性

- **Python**: 需要 3.12+
- **FastAPI**: 使用最新穩定版
- **SQLAlchemy**: 必須使用 2.0+ 版本（異步支援）
- **OpenAI**: 需要支援 Agent SDK 的版本

### 效能考量

- 使用異步版本的套件（aio 前綴）
- Redis 用於快取和會話管理
- PostgreSQL 作為主要資料庫

### 安全性

- 所有密碼相關操作使用 `passlib`
- JWT 處理使用 `python-jose`
- 環境變數管理避免硬編碼敏感資訊

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
