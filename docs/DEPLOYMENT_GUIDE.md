# 部署和配置指南

**版本**: 1.0
**日期**: 2025-10-06
**相關設計**: SYSTEM_DESIGN.md

---

## 📋 概述

本文檔詳述 CasualTrader AI 股票交易模擬器的完整部署和配置指南，包含：

1. **開發環境設置** - 本地開發環境配置
2. **生產環境部署** - Docker 容器化部署
3. **環境變數配置** - 系統參數配置
4. **監控和維護** - 運維監控設置
5. **故障排除** - 常見問題解決方案

---

## 🛠️ 開發環境設置

### 1. 系統需求

**最低需求**:

- Python 3.12+
- Node.js 18+ (用於前端工具)
- Git
- 8GB RAM
- 20GB 硬碟空間

**建議需求**:

- Python 3.12
- Node.js 20+
- 16GB RAM
- SSD 硬碟

### 2. 環境安裝

#### 2.1 Python 環境

```bash
# 使用 uv 安裝和管理 Python 依賴
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆專案
git clone https://github.com/yourusername/CasualTrader.git
cd CasualTrader

# 安裝依賴
uv sync --dev

# 啟動虛擬環境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

#### 2.2 MCP 工具配置

```bash
# 安裝 casual-market-mcp 伺服器
pip install casual-market-mcp

# 或從本地安裝（如果有本地版本）
uvx --from . market-mcp-server
```

#### 2.3 資料庫初始化

```bash
# 執行資料庫遷移
uv run alembic upgrade head

# 創建初始資料（可選）
uv run python scripts/seed_data.py
```

### 3. 開發服務器啟動

```bash
# 啟動後端 API 服務器
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 在另一個終端啟動前端開發服務器（如果使用構建工具）
cd frontend
npm install
npm run dev

# 或直接使用 Python 提供靜態文件服務
uv run python -m http.server 3000 --directory frontend
```

---

## 🐳 Docker 容器化部署

### 1. Dockerfile 配置

#### 1.1 後端 Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 複製依賴文件
COPY pyproject.toml uv.lock ./

# 安裝 Python 依賴
RUN uv sync --no-dev

# 複製應用程式代碼
COPY src/ ./src/
COPY scripts/ ./scripts/

# 設置環境變數
ENV PYTHONPATH=/app/src
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/system/health || exit 1

# 啟動命令
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.2 前端 Dockerfile

```dockerfile
# frontend/Dockerfile
FROM nginx:alpine

# 複製前端文件
COPY . /usr/share/nginx/html/

# 複製 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 啟動 Nginx
CMD ["nginx", "-g", "daemon off;"]
```

### 2. Docker Compose 配置

```yaml
# docker-compose.yml
version: "3.8"

services:
  # 後端 API 服務
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: casualtrader-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://casualtrader:password@postgres:5432/casualtrader
      - REDIS_URL=redis://redis:6379/0
      - ENABLE_AGENT_TRACING=true
      - TRACE_STORAGE_PATH=/app/traces
      - LOG_LEVEL=INFO
    volumes:
      - ./traces:/app/traces
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - casualtrader-network

  # 前端服務
  frontend:
    build:
      context: frontend
      dockerfile: Dockerfile
    container_name: casualtrader-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - casualtrader-network

  # PostgreSQL 資料庫
  postgres:
    image: postgres:15-alpine
    container_name: casualtrader-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=casualtrader
      - POSTGRES_USER=casualtrader
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - casualtrader-network

  # Redis 快取服務
  redis:
    image: redis:7-alpine
    container_name: casualtrader-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - casualtrader-network

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: casualtrader-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - casualtrader-network

volumes:
  postgres_data:
  redis_data:

networks:
  casualtrader-network:
    driver: bridge
```

### 3. 部署命令

```bash
# 構建和啟動所有服務
docker-compose up -d --build

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f backend

# 停止服務
docker-compose down

# 清理數據（小心使用）
docker-compose down -v
```

---

## ⚙️ 環境變數配置

### 1. 生產環境配置

創建 `.env.production` 文件：

```bash
# 應用程式設定
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,yourdomain.com

# 資料庫設定
DATABASE_URL=postgresql://user:password@localhost:5432/casualtrader
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis 設定
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=20

# Agent 配置
AGENT_MAX_TURNS=30
RESEARCH_AGENT_MAX_TURNS=15
TECHNICAL_AGENT_MAX_TURNS=10
RISK_AGENT_MAX_TURNS=10
AGENT_EXECUTION_TIMEOUT=300

# 追蹤設定
ENABLE_AGENT_TRACING=true
TRACE_STORAGE_PATH=/app/traces
TRACE_RETENTION_DAYS=30

# API 限制
API_RATE_LIMIT_PER_IP=100
API_RATE_LIMIT_WINDOW=60

# 日誌設定
LOG_LEVEL=INFO
LOG_FILE_PATH=/app/logs/app.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5

# OpenAI 設定
OPENAI_API_KEY=your-openai-api-key
OPENAI_DEFAULT_MODEL=gpt-4o-mini

# 監控設定
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# 安全設定
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET_KEY=your-jwt-secret
SESSION_COOKIE_SECURE=true
```

### 2. 開發環境配置

創建 `.env.development` 文件：

```bash
# 應用程式設定
APP_ENV=development
APP_DEBUG=true
SECRET_KEY=dev-secret-key

# 資料庫設定
DATABASE_URL=sqlite:///./casualtrader_dev.db

# Redis 設定（開發環境可選）
REDIS_URL=redis://localhost:6379/1

# Agent 配置（開發環境較寬鬆）
AGENT_MAX_TURNS=10
ENABLE_AGENT_TRACING=true
TRACE_STORAGE_PATH=./traces

# 日誌設定
LOG_LEVEL=DEBUG

# OpenAI 設定
OPENAI_API_KEY=your-openai-api-key

# CORS 設定（開發環境允許所有來源）
CORS_ORIGINS=*
```

---

## 📊 監控和維護

### 1. 健康檢查端點

```python
# src/api/routers/system.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    """系統健康檢查"""
    try:
        # 檢查資料庫連線
        db_status = await check_database_connection()

        # 檢查 Redis 連線
        redis_status = await check_redis_connection()

        # 檢查系統資源
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_status,
                "redis": redis_status
            },
            "system": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@router.get("/metrics")
async def get_metrics():
    """取得系統指標"""
    return {
        "active_agents": await count_active_agents(),
        "total_trades": await count_total_trades(),
        "api_requests_per_minute": await get_api_request_rate(),
        "websocket_connections": get_websocket_connection_count(),
        "uptime": get_system_uptime()
    }
```

### 2. 日誌配置

```python
# src/utils/logging_config.py
import logging
import logging.handlers
import os

def setup_logging():
    """設置日誌配置"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE_PATH', './logs/app.log')

    # 創建日誌目錄
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 設置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 文件處理器（輪轉日誌）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=100*1024*1024,  # 100MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 設置根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

### 3. Nginx 配置

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    # 速率限制
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com;

        # 重定向到 HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL 配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # 前端靜態文件
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API 端點
        location /api/ {
            limit_req zone=api burst=20 nodelay;

            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket 支援
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # WebSocket 端點
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket 超時設定
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }
    }
}
```

---

## 🔧 故障排除

### 1. 常見問題

#### 1.1 Agent 無法啟動

**症狀**: Agent 創建後無法啟動

**可能原因和解決方案**:

```bash
# 檢查 OpenAI API 金鑰
export OPENAI_API_KEY=your-api-key

# 檢查 MCP 工具連線
uv run python -c "import casual_market_mcp; print('MCP tools available')"

# 檢查資料庫連線
uv run python -c "
from src.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection OK')
"

# 檢查 Agent 配置
uv run python scripts/test_agent_config.py
```

#### 1.2 WebSocket 連線失敗

**症狀**: 前端無法建立 WebSocket 連線

**解決方案**:

```bash
# 檢查後端服務狀態
curl http://localhost:8000/api/system/health

# 檢查 WebSocket 端點
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     http://localhost:8000/ws

# 檢查防火牆設定
sudo ufw status
sudo ufw allow 8000/tcp
```

#### 1.3 性能問題

**症狀**: API 響應緩慢或超時

**診斷和優化**:

```bash
# 檢查系統資源
htop
iostat -x 1 5

# 檢查資料庫查詢性能
docker exec -it casualtrader-postgres psql -U casualtrader -d casualtrader
EXPLAIN ANALYZE SELECT * FROM agents WHERE status = 'running';

# 檢查 Redis 性能
redis-cli info stats
redis-cli slowlog get 10

# 檢查 API 日誌
docker logs casualtrader-backend --tail 100
```

### 2. 維護腳本

#### 2.1 備份腳本

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups/casualtrader"
DATE=$(date +%Y%m%d_%H%M%S)

# 創建備份目錄
mkdir -p $BACKUP_DIR

# 備份資料庫
docker exec casualtrader-postgres pg_dump -U casualtrader casualtrader > \
    $BACKUP_DIR/database_$DATE.sql

# 備份追蹤文件
tar -czf $BACKUP_DIR/traces_$DATE.tar.gz ./traces/

# 備份配置文件
cp .env.production $BACKUP_DIR/env_$DATE.backup

# 清理舊備份（保留 30 天）
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### 2.2 清理腳本

```bash
#!/bin/bash
# scripts/cleanup.sh

# 清理舊的追蹤文件
find ./traces -name "*.json" -mtime +30 -delete

# 清理舊的日誌文件
find ./logs -name "*.log.*" -mtime +7 -delete

# 清理 Docker 資源
docker system prune -f
docker volume prune -f

# 重啟服務以釋放記憶體
docker-compose restart backend

echo "Cleanup completed"
```

### 3. 監控設置

#### 3.1 Prometheus 配置

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "casualtrader-backend"
    static_configs:
      - targets: ["backend:9090"]
    metrics_path: /api/metrics
    scrape_interval: 30s

  - job_name: "node-exporter"
    static_configs:
      - targets: ["node-exporter:9100"]
```

#### 3.2 Grafana 儀表板

```json
{
  "dashboard": {
    "title": "CasualTrader Monitoring",
    "panels": [
      {
        "title": "Active Agents",
        "type": "stat",
        "targets": [
          {
            "expr": "casualtrader_active_agents_total"
          }
        ]
      },
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(casualtrader_api_request_duration_seconds[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## 📁 部署檔案結構

```
deployment/
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── nginx/
│   ├── nginx.conf
│   └── ssl/
├── scripts/
│   ├── deploy.sh
│   ├── backup.sh
│   ├── cleanup.sh
│   └── health_check.sh
├── monitoring/
│   ├── prometheus.yml
│   ├── grafana/
│   └── alerts/
├── env/
│   ├── .env.production
│   ├── .env.staging
│   └── .env.development
└── systemd/
    ├── casualtrader-backend.service
    └── casualtrader-worker.service
```

---

## ✅ 部署檢查清單

### 前期準備

- [ ] 確認系統需求和依賴
- [ ] 準備 SSL 證書
- [ ] 設置域名和 DNS
- [ ] 配置防火牆規則

### 環境配置

- [ ] 創建生產環境配置文件
- [ ] 設置資料庫連線
- [ ] 配置 Redis 快取
- [ ] 設置 OpenAI API 金鑰

### 服務部署

- [ ] 構建 Docker 映像
- [ ] 啟動所有服務
- [ ] 執行資料庫遷移
- [ ] 驗證服務健康狀態

### 監控設置

- [ ] 配置日誌輪轉
- [ ] 設置健康檢查
- [ ] 配置監控儀表板
- [ ] 設置告警規則

### 安全檢查

- [ ] 驗證 HTTPS 配置
- [ ] 檢查 API 速率限制
- [ ] 驗證身份認證
- [ ] 檢查數據備份

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
