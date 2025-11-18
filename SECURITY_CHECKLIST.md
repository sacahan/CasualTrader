# CasualTrader 安全部署檢查清單

## 部署前必檢項目

### 🔒 環境配置

- [ ] **設置生產環境標誌**
  ```bash
  ENVIRONMENT=production
  DEBUG=false
  ```

- [ ] **配置適當的日誌級別**
  ```bash
  LOG_LEVEL=WARNING  # 或 ERROR
  ```

- [ ] **設置嚴格的 CORS 來源**
  ```bash
  # ❌ 不要這樣做
  CORS_ORIGINS='["*"]'
  
  # ✅ 應該這樣做
  CORS_ORIGINS='["https://yourdomain.com", "https://www.yourdomain.com"]'
  ```

### 🔑 敏感資訊管理

- [ ] **確保所有 API 金鑰已正確設置**
  - [ ] `OPENAI_API_KEY` 已設置且有效
  - [ ] `TAVILY_API_KEY` 已設置且有效
  - [ ] `GITHUB_PERSONAL_ACCESS_TOKEN` 已設置且有效

- [ ] **驗證 .env 文件權限**
  ```bash
  chmod 600 .env
  ```

- [ ] **確認 .env 文件不在版本控制中**
  ```bash
  # 檢查 .gitignore 包含 .env
  grep "^\.env$" .gitignore
  ```

### 🌐 網路安全

- [ ] **限制 API 監聽地址**（如果不需要外部訪問）
  ```bash
  API_HOST=127.0.0.1  # 僅本地訪問
  # 或
  API_HOST=0.0.0.0    # 允許外部訪問（確保有防火牆保護）
  ```

- [ ] **使用反向代理（如 Nginx）**
  - [ ] 配置 HTTPS/SSL 證書
  - [ ] 設置適當的請求大小限制
  - [ ] 配置請求頻率限制

- [ ] **配置防火牆規則**
  ```bash
  # 僅允許必要的端口
  ufw allow 443/tcp    # HTTPS
  ufw allow 80/tcp     # HTTP (重定向到 HTTPS)
  ufw enable
  ```

### 📊 資料庫安全

- [ ] **檢查資料庫文件權限**
  ```bash
  chmod 600 casualtrader.db
  ```

- [ ] **設置資料庫備份策略**
  ```bash
  # 建議每日備份
  0 2 * * * /path/to/backup_script.sh
  ```

- [ ] **（未來考慮）遷移到支持加密的資料庫**
  - PostgreSQL with encryption
  - 或 SQLCipher (加密的 SQLite)

### 🔍 監控與日誌

- [ ] **配置日誌輪換**
  ```bash
  LOG_ROTATION="500 MB"
  LOG_RETENTION="30 days"
  LOG_COMPRESSION="zip"
  ```

- [ ] **設置日誌監控**
  - [ ] 監控錯誤日誌
  - [ ] 監控異常訪問模式
  - [ ] 設置告警機制

- [ ] **定期審查訪問日誌**
  ```bash
  # 每週審查一次
  tail -n 1000 logs/api_*.log | grep "ERROR\|WARNING"
  ```

### 📦 依賴管理

- [ ] **檢查依賴套件漏洞**
  ```bash
  pip install safety pip-audit
  safety check
  pip-audit
  ```

- [ ] **保持依賴套件更新**
  ```bash
  pip list --outdated
  ```

- [ ] **設置自動依賴更新（可選）**
  - 使用 Dependabot 或 Renovate

### 🚀 應用程序配置

- [ ] **設置合理的超時時間**
  ```bash
  DEFAULT_AGENT_TIMEOUT=300  # 5 分鐘
  ```

- [ ] **限制最大並發 Agent 數量**
  ```bash
  MAX_AGENTS=10  # 根據服務器資源調整
  ```

- [ ] **配置 WebSocket 連接限制**
  ```bash
  WS_MAX_CONNECTIONS=100
  ```

### 🧪 測試驗證

- [ ] **運行安全測試**
  ```bash
  # 運行單元測試
  pytest tests/
  
  # 運行 Bandit 安全掃描
  pip install bandit
  bandit -r backend/src -ll
  ```

- [ ] **驗證 CORS 設置**
  ```bash
  curl -H "Origin: http://malicious.com" \
       -H "Access-Control-Request-Method: POST" \
       -X OPTIONS http://your-api.com/api/agents
  ```

- [ ] **測試錯誤處理**
  - [ ] 確認生產環境不洩露內部錯誤資訊
  - [ ] 驗證所有異常都被適當處理

### 📋 文檔與溝通

- [ ] **更新部署文檔**
  - [ ] 記錄部署步驟
  - [ ] 記錄安全配置
  - [ ] 記錄應急響應流程

- [ ] **團隊安全培訓**
  - [ ] 培訓團隊成員關於安全最佳實踐
  - [ ] 建立安全事件響應流程

## 部署後持續監控

### 每日檢查

- [ ] 檢查應用程序運行狀態
- [ ] 檢查錯誤日誌
- [ ] 監控資源使用情況

### 每週檢查

- [ ] 審查訪問日誌
- [ ] 檢查異常訪問模式
- [ ] 審查資料庫大小和性能

### 每月檢查

- [ ] 運行安全掃描 (safety check, pip-audit)
- [ ] 更新依賴套件
- [ ] 審查和更新安全策略

### 每季度檢查

- [ ] 進行完整的安全審計
- [ ] 更新威脅模型
- [ ] 審查和更新應急響應計劃

## 應急響應計劃

### 發現安全事件時

1. **立即行動**
   - 隔離受影響的系統
   - 停止可疑的訪問
   - 保存日誌和證據

2. **評估影響**
   - 確定受影響的範圍
   - 評估資料洩露風險
   - 通知相關人員

3. **修復和恢復**
   - 修補漏洞
   - 更新憑證
   - 恢復正常服務

4. **事後分析**
   - 分析事件原因
   - 更新安全措施
   - 記錄經驗教訓

## 聯絡資訊

**安全問題報告**:
- Email: security@casualtrader.com
- GitHub Issues: [標記為 security]

**緊急聯絡**:
- 系統管理員: [聯絡資訊]
- 技術負責人: [聯絡資訊]

---

**檢查清單版本**: 1.0  
**最後更新**: 2025-11-18  
**下次審查**: 2025-12-18
