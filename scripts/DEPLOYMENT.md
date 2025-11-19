# 🚀 CasualTrader 部署指南

## 架構說明

CasualTrader 採用 **前後端整合部署** 的方式：

```
┌─────────────────────────────────────────┐
│         Docker Container                │
│  ┌───────────────────────────────────┐  │
│  │   FastAPI Backend (Port 8000)     │  │
│  │                                   │  │
│  │   ├─ API Endpoints (/api/*)      │  │
│  │   │   - /api/agents              │  │
│  │   │   - /api/trading             │  │
│  │   │   - /api/health              │  │
│  │   │                               │  │
│  │   └─ Static Files (/)            │  │
│  │       - Frontend SPA (Svelte)    │  │
│  │       - Built from frontend/dist │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Volumes:                               │
│  - casualtrader-data (Database)        │
│  - casualtrader-logs (Logs)            │
└─────────────────────────────────────────┘
```

### 為什麼這樣設計？

1. **簡化部署** - 只需要一個 Docker 映像和一個容器
2. **降低複雜度** - 不需要配置 Nginx 或其他反向代理
3. **統一管理** - 前後端版本一致，便於維護
4. **開發友好** - 本地開發可以繼續分離，生產環境合併

## 快速開始

### 方法 1: 自動化腳本（推薦）

```bash
# 1. 設定 Docker Hub 帳號
export DOCKER_USERNAME=你的用戶名

# 2. 執行自動化部署
cd scripts
./build-and-deploy.sh

# 3. 在 Ubuntu 伺服器執行生成的腳本
./deploy-on-server.sh
```

### 方法 2: Docker Compose

```bash
cd scripts

# 本地測試
docker-compose up -d

# 生產環境
docker-compose -f docker-compose.yml up -d
```

### 方法 3: 手動部署

```bash
# 構建映像
docker build -f scripts/Dockerfile -t casualtrader:latest .

# 運行容器
docker run -d \
  --name casualtrader \
  -p 8000:8000 \
  -v casualtrader-data:/app/data \
  casualtrader:latest
```

## 部署流程

### 完整流程圖

```
[開發環境 Mac]
    ↓
[1] 編譯前端 (npm run build)
    ↓ frontend/dist
[2] Docker 多階段構建
    ├─ Stage 1: 構建前端 (Node.js)
    ├─ Stage 2: 安裝後端依賴 (Python)
    └─ Stage 3: 組裝生產映像
    ↓
[3] 推送到 Docker Hub
    ↓
[Ubuntu Server]
    ↓
[4] Pull 映像
    ↓
[5] 運行容器
    ↓
[6] 訪問應用
```

### 各階段說明

#### Stage 1: Frontend Build
- 使用 Node.js 20 Alpine
- 安裝前端依賴
- 執行 `npm run build`
- 產生 `dist` 目錄

#### Stage 2: Backend Build
- 使用 Python 3.12 Slim
- 安裝系統依賴（PostgreSQL 客戶端等）
- 使用 `uv` 安裝 Python 套件
- 準備後端執行環境

#### Stage 3: Production Image
- 複製 Python 環境
- 複製後端源碼
- **複製前端 dist 到 /app/static**
- 設定環境變數 `STATIC_DIR=/app/static`
- FastAPI 掛載靜態檔案服務

## 檔案結構

```
CasualTrader/
├── frontend/                   # 前端專案
│   ├── src/                   # Svelte 源碼
│   ├── dist/                  # 編譯後的靜態檔案 (構建後生成)
│   └── package.json
│
├── backend/                    # 後端專案
│   ├── src/
│   │   └── api/
│   │       └── app.py        # FastAPI 應用（掛載靜態檔案）
│   ├── run_server.py         # 啟動腳本
│   └── pyproject.toml
│
└── scripts/                    # 部署腳本
    ├── Dockerfile             # 多階段構建
    ├── docker-compose.yml     # Docker Compose 配置
    ├── build-frontend.sh      # 單獨構建前端
    ├── build-backend.sh       # 單獨構建後端
    ├── build-and-deploy.sh    # 完整部署流程
    ├── test-docker-build.sh   # 測試 Docker 構建
    ├── README.md              # 詳細文檔
    └── QUICKSTART.md          # 快速開始
```

## 環境變數

### 必要變數

```bash
# FastAPI 靜態檔案路徑
STATIC_DIR=/app/static

# 資料庫連接
DATABASE_URL=sqlite:///app/data/casualtrader.db
```

### 可選變數

```bash
# API 配置
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production
DEBUG=false

# CORS（重要：生產環境不要用 *）
CORS_ORIGINS=http://localhost:8000,https://yourdomain.com

# AI API Keys
OPENAI_API_KEY=sk-xxx
```

## 資料持久化

使用 Docker Volumes 保存資料：

```bash
docker volume ls | grep casualtrader
# casualtrader-data         # 資料庫
# casualtrader-logs         # 日誌
# casualtrader-memory       # Agent 記憶
# casualtrader-custom-logs  # 自訂日誌
```

### 備份資料

```bash
# 備份
docker run --rm \
  -v casualtrader-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz /data

# 恢復
docker run --rm \
  -v casualtrader-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/backup-YYYYMMDD.tar.gz -C /
```

## 監控和維護

### 健康檢查

```bash
# API 健康檢查
curl http://localhost:8000/api/health

# 容器健康狀態
docker ps
docker inspect casualtrader | grep -A 5 Health
```

### 查看日誌

```bash
# 實時日誌
docker logs -f casualtrader

# 最近 100 行
docker logs --tail 100 casualtrader

# 導出日誌
docker logs casualtrader > casualtrader.log 2>&1
```

### 資源監控

```bash
# 容器資源使用
docker stats casualtrader

# 詳細資訊
docker inspect casualtrader
```

## 更新部署

### 方法 1: 自動化（推薦）

```bash
# 本機：重新構建並推送
./build-and-deploy.sh

# 伺服器：拉取並重啟
./deploy-on-server.sh
```

### 方法 2: Docker Compose

```bash
# 拉取最新映像並重啟
docker-compose pull
docker-compose up -d
```

### 方法 3: 手動

```bash
# 停止舊容器
docker stop casualtrader
docker rm casualtrader

# 拉取新映像
docker pull yourusername/casualtrader:latest

# 啟動新容器
docker run -d [same parameters] yourusername/casualtrader:latest
```

## 故障排除

### 問題 1: 前端無法訪問

**症狀**: API 可以訪問，但前端顯示 404

**解決方案**:

```bash
# 1. 確認前端已構建
ls -la frontend/dist/

# 2. 檢查容器內靜態檔案
docker exec casualtrader ls -la /app/static

# 3. 檢查 STATIC_DIR 環境變數
docker exec casualtrader env | grep STATIC_DIR

# 4. 重新構建（如果需要）
./build-and-deploy.sh
```

### 問題 2: 容器無法啟動

**症狀**: 容器啟動後立即停止

**解決方案**:

```bash
# 查看詳細日誌
docker logs casualtrader

# 檢查常見問題：
# - 連接埠衝突 (8000)
# - 資料庫權限
# - 環境變數配置
```

### 問題 3: API 502 錯誤

**症狀**: Nginx 或反向代理返回 502

**解決方案**:

```bash
# 1. 確認容器運行
docker ps | grep casualtrader

# 2. 檢查容器內部健康
docker exec casualtrader curl http://localhost:8000/api/health

# 3. 檢查網路連接
docker network inspect casualtrader-network
```

## 安全建議

### 生產環境檢查清單

- [ ] 關閉 DEBUG 模式 (`DEBUG=false`)
- [ ] 配置正確的 CORS_ORIGINS（不使用 `*`）
- [ ] 使用 HTTPS（配置 Nginx + Let's Encrypt）
- [ ] 設定防火牆規則（只開放必要連接埠）
- [ ] 定期更新 Docker 映像
- [ ] 設定自動備份
- [ ] 監控容器資源使用
- [ ] 配置日誌輪替
- [ ] 使用環境變數或 Secret 管理敏感資訊

### HTTPS 配置（Nginx）

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## 效能優化

### 1. 資源限制

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 512M
```

### 2. 日誌管理

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 3. 使用 PostgreSQL（可選）

對於高負載場景，建議使用 PostgreSQL 替代 SQLite：

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: casualtrader
      POSTGRES_USER: casualtrader
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres-data:/var/lib/postgresql/data

  casualtrader:
    environment:
      - DATABASE_URL=postgresql://casualtrader:your_password@db:5432/casualtrader
    depends_on:
      - db
```

## 開發環境 vs 生產環境

### 開發環境
- 前後端分離運行
- 前端：`npm run dev` (Vite, Port 5173)
- 後端：`python run_server.py` (FastAPI, Port 8000)
- 支援 Hot Reload

### 生產環境
- 前後端整合在一個容器
- FastAPI 同時服務 API 和靜態檔案
- 統一通過 Port 8000 訪問
- 優化的生產構建

## 相關資源

- **詳細部署文檔**: [scripts/README.md](./scripts/README.md)
- **快速開始**: [scripts/QUICKSTART.md](./scripts/QUICKSTART.md)
- **專案文檔**: [README.md](./README.md)
- **Docker Hub**: https://hub.docker.com/

## 支援

如遇問題，請：
1. 查看 [故障排除](#故障排除) 章節
2. 檢查 Docker 日誌
3. 提交 GitHub Issue

---

**Last Updated**: 2025-11-19
**Version**: 1.0.0
