# CasualTrader 重構快速啟動指南

**閱讀時間**: 5 分鐘
**執行時間**: 10-16 小時

---

## 📚 必讀文件 (優先順序)

### ⭐ 必須閱讀

1. **本文件** (REFACTORING_QUICKSTART.md) - 5 分鐘
   - 快速了解重構內容和步驟

2. **REFACTORING_SUMMARY.md** - 10 分鐘
   - 完整總覽、影響範圍、檢查清單

3. **REFACTORING_ACTION_PLAN.md** - 30 分鐘
   - 詳細執行步驟、程式碼修改範例

### 📖 參考文件

4. **DATABASE_SCHEMA_SPECIFICATION.md** - 參考用
   - 標準資料庫 schema (真理來源)

5. **PERFORMANCE_CALCULATION_ANALYSIS.md** - 參考用
   - 績效計算邏輯分析

---

## 🎯 重構目標

### 主要目標

1. **修正語義錯誤**: `winning_trades` 和 `win_rate` 定義不正確
2. **移除不存在欄位**: 5 個欄位在資料庫中不存在
3. **統一 Schema**: 前後端與資料庫保持一致

### 破壞性變更

⚠️ **這次重構不考慮向後相容，會有 API 契約變更**

---

## 🚀 快速執行步驟

### 步驟 0: 備份 (5 分鐘)

```bash
# 備份資料庫
cd /Users/sacahan/Documents/workspace/CasualTrader/backend
cp casualtrader.db casualtrader.db.backup.$(date +%Y%m%d_%H%M%S)

# 確認備份
ls -lh casualtrader.db*
```

### 步驟 1: 執行 Migration (10 分鐘)

```bash
# 執行 Migration
cd backend
sqlite3 casualtrader.db < migrations/20251109_0000_fix_performance_fields.sql

# 驗證
sqlite3 casualtrader.db "PRAGMA table_info(agent_performance);" | grep -E "sell_trades|winning_trades"
```

**預期輸出**:
```
12|sell_trades_count|INTEGER|1|0|0
13|winning_trades_correct|INTEGER|1|0|0
```

### 步驟 2: 修改 Backend (4-6 小時)

**按照此順序修改**:

#### 2.1 ORM 模型 (30 分鐘)
```bash
# 修改檔案
code backend/src/database/models.py
```

修改要點:
- `AgentSession.tools_called`: `JSON` → `Text`
- `AgentPerformance`: 重新命名 `winning_trades` → `sell_trades_count`
- `AgentPerformance`: 新增 `winning_trades_correct`

#### 2.2 Schema 定義 (1 小時)
```bash
# 修改檔案
code backend/src/schemas/agent.py
```

修改要點:
- **刪除** `EnabledTools` 類別
- **移除** 5 個不存在的欄位
- **新增** `last_active_at` 到 `AgentResponse`

#### 2.3 Service 層 (2 小時)
```bash
# 修改檔案
code backend/src/service/agents_service.py
code backend/src/service/trading_service.py
```

修改要點:
- 更新績效計算邏輯
- 移除不存在欄位的處理

#### 2.4 API 層 (1 小時)
```bash
# 修改檔案
code backend/src/api/routers/agents.py
```

修改要點:
- 移除不存在欄位的回應
- 確認 JSON 序列化處理

#### 2.5 測試 (1 小時)
```bash
# 執行測試
cd backend
pytest tests/contract/ -v
pytest tests/integration/ -v
```

### 步驟 3: 修改 Frontend (2-3 小時)

#### 3.1 API 層 (30 分鐘)
```bash
# 修改檔案
code frontend/src/shared/api.js
```

修改要點:
- 移除 `startAgent()` 的 `maxTurns` 參數

#### 3.2 UI 元件 (1-2 小時)
```bash
# 檢查並修改
grep -r "enabled_tools\|max_turns\|strategy_prompt" frontend/src/
```

修改要點:
- 移除這些欄位的顯示和輸入

#### 3.3 測試 (30 分鐘)
```bash
cd frontend
npm test
```

### 步驟 4: 更新文件 (1-2 小時)

```bash
# 修改文件
code docs/API_CONTRACT_SPECIFICATION.md
code docs/ORM_CONTRACT_SPECIFICATION.md
code docs/SERVICE_CONTRACT_SPECIFICATION.md
```

### 步驟 5: 整合測試 (1 小時)

```bash
# Backend 啟動
cd backend && uvicorn api.server:app --reload

# Frontend 啟動
cd frontend && npm run dev

# 手動測試
# 1. 建立 Agent (不帶移除的欄位)
# 2. 啟動 Agent (不帶 max_turns)
# 3. 查看績效 (確認欄位正確)
```

---

## 📋 詳細檢查清單

### 準備階段
- [ ] 閱讀 REFACTORING_SUMMARY.md
- [ ] 閱讀 REFACTORING_ACTION_PLAN.md
- [ ] 備份資料庫
- [ ] 確認開發環境正常

### Backend 修改
- [ ] 執行 Migration
- [ ] 修改 models.py
- [ ] 修改 schemas/agent.py (刪除 EnabledTools + 5 個欄位)
- [ ] 修改 agents_service.py (績效計算)
- [ ] 修改 trading_service.py (績效計算)
- [ ] 修改 routers/agents.py
- [ ] Backend 測試通過

### Frontend 修改
- [ ] 修改 api.js (移除 maxTurns)
- [ ] 清理 UI 元件
- [ ] Frontend 測試通過

### 文件更新
- [ ] 更新 API_CONTRACT_SPECIFICATION.md
- [ ] 更新 ORM_CONTRACT_SPECIFICATION.md
- [ ] 更新 SERVICE_CONTRACT_SPECIFICATION.md

### 最終驗證
- [ ] 手動測試完整流程
- [ ] 所有測試通過
- [ ] 文件同步完成

---

## 🔧 常見問題

### Q1: Migration 執行失敗怎麼辦？

```bash
# 回滾
cd backend
sqlite3 casualtrader.db "
DROP TABLE IF EXISTS agent_performance;
ALTER TABLE agent_performance_backup_20251109 RENAME TO agent_performance;
"

# 還原索引
sqlite3 casualtrader.db "
CREATE INDEX idx_performance_agent_id ON agent_performance (agent_id);
CREATE INDEX idx_performance_date ON agent_performance (date);
"
```

### Q2: 測試失敗怎麼辦？

1. 檢查是否所有欄位都已修改
2. 檢查 JSON 序列化處理是否正確
3. 查看 `REFACTORING_ACTION_PLAN.md` 的詳細修改指南

### Q3: 前端報錯怎麼辦？

1. 檢查 API 回應格式
2. 確認所有移除的欄位都已清理
3. 清除瀏覽器快取和 localStorage

---

## 📊 時間估算

| 階段 | 預計時間 | 可壓縮到 |
|------|---------|---------|
| 準備 | 30 分鐘 | 15 分鐘 |
| Backend | 4-6 小時 | 3 小時 * |
| Frontend | 2-3 小時 | 1.5 小時 * |
| 文件 | 1-2 小時 | 30 分鐘 * |
| 測試 | 1 小時 | 30 分鐘 |
| **總計** | **10-16 小時** | **6 小時** |

\* 如果使用 AI 輔助工具 (如 Copilot, Claude) 可大幅縮短時間

---

## 🎬 開始執行

```bash
# 1. 切換到專案目錄
cd /Users/sacahan/Documents/workspace/CasualTrader

# 2. 建立新分支
git checkout -b refactor/fix-schema-and-performance

# 3. 開始執行步驟 0
# ... (按照上面的步驟執行)

# 4. 提交變更
git add .
git commit -m "refactor: fix schema inconsistencies and performance calculation logic

BREAKING CHANGES:
- Remove 5 non-existent fields from Agent API
- Rename winning_trades to sell_trades_count
- Remove max_turns parameter from agent execution

See docs/REFACTORING_SUMMARY.md for details"

# 5. 推送並建立 PR
git push origin refactor/fix-schema-and-performance
```

---

## 📞 需要幫助？

1. 查看 `REFACTORING_ACTION_PLAN.md` 的詳細步驟
2. 查看 `DATABASE_SCHEMA_SPECIFICATION.md` 的標準定義
3. 查看 Migration 腳本的註解
4. 聯絡開發團隊

---

**開始執行時間**: _________
**預計完成時間**: _________
**實際完成時間**: _________

Good luck! 🚀
