# CasualTrader 部署腳本

本目錄包含 CasualTrader 專案的 Docker 構建和部署腳本。

## 📁 檔案說明

### Docker 相關
- `Dockerfile` - 多階段構建的 Docker 映像檔
- `docker-compose.yml` - 生產環境 Docker Compose 配置
- `docker-compose.dev.yml` - 開發環境 Docker Compose 配置
- `.dockerignore` - Docker 構建時排除的檔案

### 構建腳本
- `build-frontend.sh` - 單獨構建前端
- `build-backend.sh` - 單獨構建後端（安裝依賴、檢查代碼）
- `build-and-deploy.sh` - 完整的構建、推送和部署流程

### 部署腳本
- `deploy-on-server.sh` - 在 Ubuntu 伺服器上執行的部署腳本（自動生成）

## 🚀 使用方式

### 方式一：完整自動化部署（推薦）

```bash
# 設定 Docker Hub 用戶名
export DOCKER_USERNAME=yourusername
export DOCKER_PASSWORD=yourpassword  # 可選，不設定會提示輸入

# 構建並推送到 Docker Hub
./build-and-deploy.sh
```

這個腳本會：
1. ✅ 構建 Docker 映像（包含前端和後端）
2. ✅ 推送映像到 Docker Hub
3. ✅ 生成伺服器部署腳本

### 方式二：分步驟構建

```bash
# 1. 單獨構建前端
./build-frontend.sh

# 2. 單獨構建後端
./build-backend.sh

# 3. 構建 Docker 映像
docker build -f Dockerfile -t casualtrader:latest ..

# 4. 推送到 Docker Hub
docker tag casualtrader:latest yourusername/casualtrader:latest
docker push yourusername/casualtrader:latest
```

### 方式三：使用 Docker Compose（本地測試）

```bash
# 生產環境配置
docker-compose up -d

# 開發環境配置
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

## 🖥️ 在 Ubuntu 伺服器上部署

### 前置需求

```bash
# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 將用戶加入 docker 群組（可選）
sudo usermod -aG docker $USER
```

### 部署步驟

1. **使用自動生成的腳本**

```bash
# 在本機執行 build-and-deploy.sh 後，會生成 deploy-on-server.sh
# 將此腳本複製到伺服器並執行

# 在伺服器上：
chmod +x deploy-on-server.sh
./deploy-on-server.sh
```

2. **手動部署**

```bash
# 拉取映像
docker pull yourusername/casualtrader:latest

# 停止舊容器
docker stop casualtrader 2>/dev/null || true
docker rm casualtrader 2>/dev/null || true

# 啟動新容器
docker run -d \
  --name casualtrader \
  --restart unless-stopped \
  -p 8000:8000 \
  -v casualtrader-data:/app/data \
  -v casualtrader-logs:/app/logs \
  -e DATABASE_URL=sqlite:///app/data/casualtrader.db \
  yourusername/casualtrader:latest

# 查看日誌
docker logs -f casualtrader
```

3. **使用 Docker Compose 部署**

```bash
# 下載 docker-compose.yml
wget https://raw.githubusercontent.com/yourusername/CasualTrader/main/scripts/docker-compose.yml

# 編輯環境變數（如需要）
nano docker-compose.yml

# 啟動服務
docker-compose up -d

# 查看狀態
docker-compose ps
docker-compose logs -f
```

## 🔧 配置說明

### 環境變數

在 `docker-compose.yml` 中可以設定以下環境變數：

```yaml
environment:
  # 資料庫配置
  - DATABASE_URL=sqlite:///app/data/casualtrader.db

  # API 配置
  - API_HOST=0.0.0.0
  - API_PORT=8000
  - ENVIRONMENT=production
  - DEBUG=false

  # CORS 配置（調整為你的域名）
  - CORS_ORIGINS=http://localhost:8000,https://yourdomain.com

  # OpenAI API Key（如需要）
  # - OPENAI_API_KEY=sk-xxx

  # Agent 配置
  - MAX_AGENTS=10
```

### 資料持久化

Docker volumes 用於保存以下資料：

- `casualtrader-data` - SQLite 資料庫
- `casualtrader-logs` - 應用日誌
- `casualtrader-memory` - Agent 記憶
- `casualtrader-custom-logs` - 自訂日誌

### 連接埠

- `8000` - HTTP 服務（API + 前端）

## 📊 監控和維護

### 查看日誌

```bash
# Docker Compose
docker-compose logs -f

# Docker 容器
docker logs -f casualtrader

# 只看最近 100 行
docker logs --tail 100 casualtrader
```

### 健康檢查

```bash
# 檢查容器狀態
docker ps | grep casualtrader

# 手動健康檢查
curl http://localhost:8000/api/health

# 查看容器資源使用
docker stats casualtrader
```

### 更新部署

```bash
# 拉取最新映像
docker pull yourusername/casualtrader:latest

# 使用新映像重新創建容器
docker-compose up -d

# 或手動重啟
docker stop casualtrader
docker rm casualtrader
docker run -d [same parameters as before] yourusername/casualtrader:latest
```

### 備份資料

```bash
# 備份 Docker volume
docker run --rm \
  -v casualtrader-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/casualtrader-backup-$(date +%Y%m%d).tar.gz /data

# 恢復備份
docker run --rm \
  -v casualtrader-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/casualtrader-backup-YYYYMMDD.tar.gz -C /
```

## 🐛 故障排除

### 容器無法啟動

```bash
# 查看詳細錯誤
docker logs casualtrader

# 檢查映像是否存在
docker images | grep casualtrader

# 重新構建
docker-compose build --no-cache
```

### 前端無法訪問

1. 確認前端已正確編譯：
   ```bash
   ls -la ../frontend/dist
   ```

2. 檢查 STATIC_DIR 環境變數：
   ```bash
   docker exec casualtrader env | grep STATIC_DIR
   ```

3. 檢查靜態檔案是否存在於容器中：
   ```bash
   docker exec casualtrader ls -la /app/static
   ```

### API 無法訪問

```bash
# 檢查連接埠是否開放
netstat -tulpn | grep 8000

# 檢查防火牆設定
sudo ufw status

# 測試 API
curl http://localhost:8000/api/health
```

## 📚 進階配置

### 使用 PostgreSQL 替代 SQLite

1. 在 `docker-compose.yml` 中添加 PostgreSQL 服務
2. 修改 `DATABASE_URL` 環境變數
3. 確保資料庫遷移正確執行

### 設定反向代理（Nginx）

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 啟用 HTTPS

使用 Let's Encrypt + Nginx：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## 🔐 安全建議

1. ✅ 不要在生產環境開啟 DEBUG 模式
2. ✅ 設定正確的 CORS_ORIGINS（不要使用 `*`）
3. ✅ 定期更新 Docker 映像和依賴
4. ✅ 使用環境變數管理敏感資訊（不要寫在 docker-compose.yml）
5. ✅ 定期備份資料
6. ✅ 監控容器資源使用情況
7. ✅ 使用 HTTPS（生產環境）

## 📝 版本歷史

- **v1.0.0** (2025-11-19)
  - ✨ 初始版本
  - ✅ 前後端整合部署
  - ✅ Docker 多階段構建
  - ✅ 自動化部署腳本
