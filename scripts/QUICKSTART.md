# 🚀 CasualTrader Docker 快速部署指南

## 最快速部署（3 步驟）

### 1️⃣ 設定 Docker Hub 帳號

```bash
export DOCKER_USERNAME=你的DockerHub用戶名
```

### 2️⃣ 執行自動化部署

```bash
cd scripts
./build-and-deploy.sh
```

### 3️⃣ 在 Ubuntu 伺服器上執行

```bash
# 腳本會自動生成 deploy-on-server.sh
# 將此檔案複製到伺服器後執行：
./deploy-on-server.sh
```

完成！應用將在 `http://your-server:8000` 運行

---

## 本地測試（使用 Docker Compose）

```bash
cd scripts

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 訪問應用
open http://localhost:8000
```

---

## 驗證部署

```bash
# 檢查健康狀態
curl http://localhost:8000/api/health

# 查看容器狀態
docker ps | grep casualtrader

# 查看日誌
docker logs -f casualtrader
```

---

## 常見問題

**Q: 構建失敗？**
```bash
# 清理並重建
docker system prune -a
docker-compose build --no-cache
```

**Q: 前端無法訪問？**
```bash
# 檢查前端是否已構建
ls -la ../frontend/dist

# 如果沒有，先構建前端
./build-frontend.sh
```

**Q: 需要更新部署？**
```bash
# 重新執行部署腳本
./build-and-deploy.sh

# 在伺服器上拉取最新版本
docker pull $DOCKER_USERNAME/casualtrader:latest
docker-compose up -d
```

---

完整文檔請查看 [README.md](./README.md)
