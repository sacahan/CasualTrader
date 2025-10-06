# 專案結構調整指南

**版本**: 1.0  
**日期**: 2025-10-06  
**目的**: 統一 API、Agent、Frontend 三大模塊的檔案結構

---

## 📋 調整概述

為了解決三個實作文檔（API_IMPLEMENTATION.md、AGENT_IMPLEMENTATION.md、FRONTEND_IMPLEMENTATION.md）中檔案結構的衝突問題，我們採用了 **統一 Monorepo 架構**。

---

## 🔄 主要變更

### 1. 創建統一結構文檔

新增 **PROJECT_STRUCTURE.md** 作為專案結構的唯一真實來源（Single Source of Truth）：

- 定義完整的 Monorepo 結構
- 清楚分離 backend/ 和 frontend/ 目錄
- 統一測試目錄組織方式
- 提供檔案命名規範和檢查清單

### 2. 目錄結構調整

#### 調整前（原有衝突）

```
❌ 原有結構 - 存在衝突:

src/                    # 後端代碼（不清楚）
  ├── api/              # API 模塊
  ├── agents/           # Agent 模塊  
  └── shared/           # 共享組件

frontend/src/           # 前端代碼（部分文檔寫法不一致）
  ├── components/
  └── ...

tests/                  # 測試目錄（組織方式不統一）
  ├── api/
  ├── agents/
  └── frontend/
```

**主要問題**:

- `src/` 目錄同時包含多個模塊，職責不清
- 前端路徑在不同文檔中表達不一致
- 測試目錄結構不統一，難以維護

#### 調整後（統一 Monorepo）

```
✅ 新結構 - 清晰的 Monorepo:

CasualTrader/
├── backend/            # 後端應用（Python/FastAPI）
│   ├── src/
│   │   ├── agents/     # Agent 系統
│   │   ├── api/        # API 層
│   │   └── shared/     # 共享組件
│   ├── pyproject.toml
│   └── requirements.txt
│
├── frontend/           # 前端應用（Vite + Svelte）
│   ├── src/
│   │   ├── components/
│   │   ├── routes/
│   │   ├── stores/
│   │   └── lib/
│   ├── package.json
│   └── vite.config.js
│
└── tests/              # 統一測試目錄
    ├── backend/        # 後端測試
    │   ├── agents/
    │   ├── api/
    │   └── shared/
    ├── frontend/       # 前端測試
    │   ├── unit/
    │   ├── integration/
    │   └── e2e/
    └── integration/    # 跨模塊整合測試
```

**改進優勢**:

- ✅ 前後端完全分離，職責清晰
- ✅ 每個模塊有獨立的配置和依賴管理
- ✅ 測試目錄鏡像源碼結構，易於維護
- ✅ 支持獨立開發、測試和部署

---

## 📝 文檔更新內容

### 1. PROJECT_STRUCTURE.md（新增）

**內容**:

- 完整的 Monorepo 結構定義
- Backend、Frontend、Tests 詳細結構
- 檔案命名規範
- 模塊職責說明
- 結構驗證檢查清單

**用途**: 所有開發者和文檔的結構參考標準

### 2. AGENT_IMPLEMENTATION.md（更新）

**變更**:

- 在「檔案結構」章節引用 PROJECT_STRUCTURE.md
- 只列出與 Agent 系統直接相關的檔案
- 路徑統一使用 `backend/src/agents/` 前綴
- 測試路徑統一使用 `tests/backend/agents/` 前綴

**示例**:

```
backend/src/agents/
├── core/
│   ├── trading_agent.py
│   └── instruction_generator.py
├── tools/
└── integrations/
```

### 3. API_IMPLEMENTATION.md（更新）

**變更**:

- 在「檔案結構」章節引用 PROJECT_STRUCTURE.md
- 只列出與 API 系統直接相關的檔案
- 路徑統一使用 `backend/src/api/` 前綴
- 補充缺失的 strategy_changes.py 路由
- 測試路徑統一使用 `tests/backend/api/` 前綴

**示例**:

```
backend/src/api/
├── main.py
├── routers/
│   ├── agents.py
│   ├── strategy_changes.py
│   └── traces.py
├── services/
└── middleware/
```

### 4. FRONTEND_IMPLEMENTATION.md（更新）

**變更**:

- 在「專案檔案結構」章節引用 PROJECT_STRUCTURE.md
- 保持完整的前端結構列表（因為前端是獨立應用）
- 測試路徑統一使用 `tests/frontend/` 前綴

**示例**:

```
frontend/
├── src/
│   ├── components/
│   ├── routes/
│   ├── stores/
│   └── lib/
└── package.json
```

---

## 🚀 遷移步驟

### 階段 1: 文檔更新 ✅ (已完成)

- [x] 創建 PROJECT_STRUCTURE.md
- [x] 更新 AGENT_IMPLEMENTATION.md
- [x] 更新 API_IMPLEMENTATION.md  
- [x] 更新 FRONTEND_IMPLEMENTATION.md
- [x] 創建 STRUCTURE_MIGRATION_GUIDE.md（本文檔）

### 階段 2: 目錄結構重組（待執行）

```bash
# 1. 創建新的目錄結構
mkdir -p backend/src/{agents,api,shared}
mkdir -p frontend/src
mkdir -p tests/{backend,frontend,integration}

# 2. 移動後端代碼
mv src/agents backend/src/
mv src/api backend/src/
mv src/shared backend/src/

# 3. 移動配置文件
mv pyproject.toml backend/
mv requirements.txt backend/

# 4. 前端保持不變（已經在正確位置）
# frontend/ 目錄已經是獨立的

# 5. 重組測試目錄
mkdir -p tests/backend/{agents,api,shared}
mkdir -p tests/frontend/{unit,integration,e2e}
# 移動現有測試文件到新結構...

# 6. 更新導入路徑
# 需要批量更新 Python 導入路徑，從 src.agents 改為 backend.src.agents
# 或者使用相對導入

# 7. 更新配置文件中的路徑
# - 更新 pyproject.toml 中的路徑
# - 更新 pytest.ini 或 pytest 配置
# - 更新 vite.config.js 中的路徑（如果需要）
```

### 階段 3: 驗證和測試（待執行）

```bash
# 1. 驗證後端導入
cd backend
python -c "from src.agents.core.trading_agent import TradingAgent"

# 2. 運行後端測試
pytest tests/backend/

# 3. 驗證前端構建
cd frontend
npm run build

# 4. 運行前端測試
npm run test

# 5. 運行整合測試
pytest tests/integration/
```

### 階段 4: 更新 CI/CD（待執行）

- [ ] 更新 GitHub Actions 工作流程
- [ ] 更新 Docker Compose 配置
- [ ] 更新部署腳本
- [ ] 更新開發環境設置腳本

---

## 📊 影響範圍分析

### 最小影響項目

✅ **文檔**:

- 所有文檔已更新為統一結構
- 開發者可以立即參考新結構進行開發

### 中等影響項目

⚠️ **開發環境**:

- 需要重新組織目錄結構
- 需要更新 Python 導入路徑
- 前端基本不受影響（已經在正確位置）

### 高影響項目

🔴 **CI/CD 和部署**:

- Docker 構建路徑需要更新
- CI/CD 腳本需要更新
- 部署配置需要調整

---

## ✅ 遷移檢查清單

### 文檔層面 ✅

- [x] 創建 PROJECT_STRUCTURE.md
- [x] 更新 AGENT_IMPLEMENTATION.md 引用
- [x] 更新 API_IMPLEMENTATION.md 引用
- [x] 更新 FRONTEND_IMPLEMENTATION.md 引用
- [x] 創建遷移指南文檔

### 代碼層面 ⏳

- [ ] 創建 backend/ 目錄結構
- [ ] 移動 agents/ 模塊到 backend/src/
- [ ] 移動 api/ 模塊到 backend/src/
- [ ] 移動 shared/ 模塊到 backend/src/
- [ ] 重組 tests/ 目錄結構
- [ ] 更新 Python 導入路徑
- [ ] 更新配置文件路徑

### 配置層面 ⏳

- [ ] 更新 pyproject.toml
- [ ] 更新 pytest 配置
- [ ] 更新 Docker Compose
- [ ] 更新 Dockerfile（backend 和 frontend）
- [ ] 更新環境變數配置

### 測試驗證 ⏳

- [ ] 後端單元測試通過
- [ ] 前端單元測試通過
- [ ] 整合測試通過
- [ ] 本地開發環境運行正常
- [ ] Docker 環境運行正常

---

## 💡 最佳實踐建議

### 1. 分支策略

建議創建專門的重構分支:

```bash
git checkout -b refactor/unified-monorepo-structure
```

### 2. 漸進式遷移

不要一次性完成所有遷移，建議步驟：

1. **階段 1**: 完成文檔更新（✅ 已完成）
2. **階段 2**: 重組目錄結構，但保持舊路徑可用（符號連結）
3. **階段 3**: 更新所有導入和配置
4. **階段 4**: 移除舊路徑，完成遷移
5. **階段 5**: 更新 CI/CD 和部署

### 3. 向後兼容

在過渡期間，可以使用符號連結保持向後兼容：

```bash
# 創建符號連結，讓舊路徑仍然可用
ln -s backend/src src
```

### 4. 團隊溝通

- 📢 通知所有開發者即將進行的結構變更
- 📖 分享新的 PROJECT_STRUCTURE.md 文檔
- 🎓 進行團隊培訓，說明新結構的優勢
- 📝 更新 README.md 和新手入門指南

---

## 🔗 相關文檔

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 統一專案結構規範
- [AGENT_IMPLEMENTATION.md](AGENT_IMPLEMENTATION.md) - Agent 系統實作規格
- [API_IMPLEMENTATION.md](API_IMPLEMENTATION.md) - API 實作規格
- [FRONTEND_IMPLEMENTATION.md](FRONTEND_IMPLEMENTATION.md) - 前端實作規格
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 部署指南（需要同步更新）

---

## ❓ 常見問題

### Q1: 為什麼選擇 Monorepo 而不是多 Repo？

**A**:

- ✅ 統一的版本控制和發布流程
- ✅ 更容易進行跨模塊的整合測試
- ✅ 共享配置和工具鏈
- ✅ 適合緊密協作的前後端專案

### Q2: 前端為什麼放在頂層而不是 packages/frontend？

**A**:

- 這是簡化的 Monorepo 結構，適合中小型專案
- backend/ 和 frontend/ 是兩個主要的應用
- 如果未來有更多子專案，可以考慮 packages/ 結構

### Q3: 測試目錄為什麼獨立而不是放在各模塊內？

**A**:

- ✅ 清楚區分源碼和測試碼
- ✅ 方便集中管理測試配置
- ✅ 避免測試代碼被打包到生產環境
- ✅ 支持跨模塊的整合測試

### Q4: 導入路徑會變得很長嗎？

**A**:
可以通過配置簡化：

```python
# pyproject.toml 中配置路徑別名
[tool.pytest.ini_options]
pythonpath = ["backend/src"]

# 這樣就可以直接導入
from agents.core.trading_agent import TradingAgent
# 而不是
from backend.src.agents.core.trading_agent import TradingAgent
```

---

**文檔維護**: CasualTrader 開發團隊  
**最後更新**: 2025-10-06
