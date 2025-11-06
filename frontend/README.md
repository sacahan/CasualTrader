# CasualTrader Frontend

✅ **Status**: Phase 4 完成 - OBSERVATION 模式已移除，支援 2 種執行模式

CasualTrader AI 股票交易模擬器的前端應用程式，使用 Vite + Svelte + Tailwind CSS 構建。

## 功能特性

- **2 種 Agent 執行模式** (Phase 4 新增):
  - **TRADING 模式**: 完整工具集（所有 MCP 伺服器、買賣工具、4 個 Sub-agents）
  - **REBALANCING 模式**: 簡化工具集（核心 MCP 伺服器、2 個 Sub-agents）
  - *OBSERVATION 模式已移除*
- **Prompt-Driven Agent 創建**: 使用自然語言描述投資偏好，無需複雜參數配置
- **即時狀態監控**: WebSocket 連接提供即時 Agent 狀態更新
- **策略演進追蹤**: 完整的策略變更歷史與視覺化時間軸
- **配置鎖定機制**: 執行中的 Agent 無法修改配置，確保策略一致性
- **績效圖表**: 使用 Chart.js 展示投資組合價值與總報酬率走勢
- **響應式設計**: 支援桌面與移動設備

## 技術棧

- **框架**: Svelte 4
- **建置工具**: Vite 5
- **樣式**: Tailwind CSS 3
- **圖表**: Chart.js 4
- **狀態管理**: Svelte Stores
- **API 通訊**: Fetch API + WebSocket

## 專案結構

```
frontend/
├── src/
│   ├── components/         # Svelte 組件
│   │   ├── Agent/         # Agent 相關組件
│   │   ├── Chart/         # 圖表組件
│   │   ├── Layout/        # 佈局組件
│   │   └── UI/            # 基礎 UI 組件
│   ├── stores/            # Svelte Stores (狀態管理)
│   ├── lib/               # 工具函數庫
│   ├── App.svelte         # 主應用程式組件
│   └── main.js            # 應用程式入口
└── package.json           # 依賴管理
```

## 開發指南

### 安裝依賴

```bash
npm install
```

### 開發模式

```bash
npm run dev
```

應用程式將運行在 <http://localhost:3000>

### 建置生產版本

```bash
npm run build
```

### 程式碼品質檢查

專案已配置 pre-commit hooks 進行自動程式碼品質檢查:

- **Prettier**: 自動格式化 JavaScript、Svelte、JSON、CSS、HTML 文件
- **ESLint**: 檢查 JavaScript 和 Svelte 程式碼品質

提交代碼時會自動運行檢查,也可手動執行:

```bash
# 運行 Prettier
npx prettier --write "src/**/*.{js,svelte,json,css,html}"

# 運行 ESLint
npx eslint "src/**/*.{js,svelte}" --fix

# 手動運行 pre-commit hooks
pre-commit run --all-files
```

### 環境變數配置

建立 `.env` 文件:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## 詳細文件

- [系統設計](../docs/SYSTEM_DESIGN.md)
- [前端實作規格](../docs/FRONTEND_IMPLEMENTATION.md)
- [專案結構](../docs/PROJECT_STRUCTURE.md)
- [Phase 4 完成摘要](../PHASE4_COMPLETION_SUMMARY.md) - 重構完成說明
- [遷移和部署指南](../docs/MIGRATION_GUIDE_OBSERVATION_TO_2MODES.md) - Agent 模式遷移指南

---

## 🆕 Phase 4 更新 (2025-10-31)

### ✅ Agent 模式變更

- **移除**: OBSERVATION 模式 (觀察模式已過時)
- **新增**: 動態模式選擇器
  - TRADING 模式: 完整功能
  - REBALANCING 模式: 簡化功能

### ✅ UI 更新

- ✅ 移除 OBSERVATION 按鈕
- ✅ 更新模式選擇下拉菜單
- ✅ 新增模式說明文本
- ✅ API 調用已相應更新

### 📊 測試驗證

- ✅ 18 個新的 E2E 迴歸測試通過
- ✅ 67 個核心功能測試 100% 通過
- ✅ 向後兼容性完全保持

---

**最後更新**: 2025年11月6日 (Phase 4 - Agent 模式重構完成)
