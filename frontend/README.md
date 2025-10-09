# CasualTrader Frontend

✅ **Status**: Phase 4 實作完成

CasualTrader AI 股票交易模擬器的前端應用程式,使用 Vite + Svelte + Tailwind CSS 構建。

## 功能特性

- **Prompt-Driven Agent 創建**: 使用自然語言描述投資偏好,無需複雜參數配置
- **即時狀態監控**: WebSocket 連接提供即時 Agent 狀態更新
- **策略演進追蹤**: 完整的策略變更歷史與視覺化時間軸
- **配置鎖定機制**: 執行中的 Agent 無法修改配置,確保策略一致性
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

應用程式將運行在 http://localhost:3000

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
