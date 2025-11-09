# CasualTrader 重構總結

**建立日期**: 2025-11-09
**最後更新**: 2025-11-09 13:02
**狀態**: 🟡 進行中 (33% 完成)

### 📊 即時進度
```
完成: 階段 0-2 ✅✅✅
待執行: 階段 3-6 ⏳⏳⏳⏳
─────────────────────
進度: 33% (2/6 完成)
```

---

## 📚 產出文件

本次審查和重構規劃產出以下文件：

### 1. **DATABASE_SCHEMA_SPECIFICATION.md** ⭐

- **用途**: **系統標準資料庫 schema 規格**
- **來源**: 從實際 `backend/casualtrader.db` 匯出
- **內容**:
  - 6 個表的完整定義
  - 所有欄位、型別、約束、索引
  - 業務邏輯規則
  - 查詢範例
  - 效能優化建議
- **重要性**: 🔴 **最高** - 這是系統的真理來源 (Source of Truth)

### 2. **SPECIFICATION_REVIEW_REPORT.md**

- **用途**: 現有規範文件與實際的差異分析
- **內容**:
  - 規範 vs 實作的對照表
  - 不一致問題清單
  - 修正建議 (方案 A / 方案 B)
- **重要性**: 🟡 中等 - 用於理解歷史問題

### 3. **PERFORMANCE_CALCULATION_ANALYSIS.md** ⭐

- **用途**: **績效計算邏輯完整分析**
- **內容**:
  - 8 個績效欄位的實現狀態
  - 已實現: 2/8
  - 需修正: 2/8 (語義錯誤)
  - 未實現: 4/8
  - 詳細修正方案和實施計劃
- **重要性**: 🔴 **高** - 發現關鍵邏輯錯誤

### 4. **REFACTORING_ACTION_PLAN.md** ⭐

- **用途**: **完整重構執行計劃**
- **內容**:
  - 整合前 3 份文件的分析結果
  - 詳細修改清單 (Backend + Frontend)
  - 8 個執行階段
  - 檢查清單
  - 破壞性變更說明
  - Migration 腳本引用
- **重要性**: 🔴 **最高** - 執行藍圖

### 5. **backend/migrations/20251109_0000_fix_performance_fields.sql**

- **用途**: 資料庫 Migration 腳本
- **內容**:
  - 重新命名 `winning_trades` → `sell_trades_count`
  - 新增 `winning_trades_correct` 欄位
  - 備份、回滾機制
- **重要性**: 🔴 高 - 必須執行的 Migration

---

## 🔍 主要發現

### 🔴 嚴重問題

1. **績效欄位語義錯誤** (PERFORMANCE_CALCULATION_ANALYSIS.md)
   - `winning_trades` 實際儲存的是「賣出交易數」，非「獲利交易數」
   - `win_rate` 計算的是「交易完成率」，非「真實勝率」
   - **影響**: 誤導使用者對交易績效的判斷

2. **Schema 與資料庫不一致** (SPECIFICATION_REVIEW_REPORT.md)
   - API Schema 定義了 5 個資料庫不存在的欄位
   - 這些欄位無法持久化
   - **影響**: 前後端資料不一致

3. **績效指標未實現** (PERFORMANCE_CALCULATION_ANALYSIS.md)
   - `unrealized_pnl`: 固定為 0 (需要實時股價)
   - `realized_pnl`: 固定為 0 (需要買賣配對邏輯)
   - `daily_return`: NULL (需要歷史資料)
   - `max_drawdown`: NULL (需要淨值曲線)
   - **影響**: 績效評估不完整

### ⚠️ 中等問題

4. **表名不一致** (SPECIFICATION_REVIEW_REPORT.md)
   - 規範: `agent`, `transaction`, `session` (單數)
   - 實際: `agents`, `transactions`, `agent_sessions` (複數)

5. **型別不一致**
   - `AgentSession.tools_called`: JSON vs TEXT
   - `Agent.max_position_size`: int vs float

---

## 📋 重構範圍

### Backend 修改 (破壞性變更)

#### 資料庫

- ✅ Migration 腳本已建立
- ❌ 執行 Migration (重新命名欄位)

#### ORM 模型

- ❌ `models.py`: 修正 2 個模型

#### API Schema

- ❌ `schemas/agent.py`: **刪除** 5 個不存在的欄位
- ❌ `schemas/agent.py`: **刪除** EnabledTools 定義

#### Service 層

- ❌ `agents_service.py`: 修正績效計算邏輯
- ❌ `trading_service.py`: 修正績效計算邏輯
- ❌ `session_service.py`: 修正 tools_called 處理

#### API 層

- ❌ `routers/agents.py`: 移除不存在欄位
- ❌ `routers/agent_execution.py`: 移除 max_turns 參數

### Frontend 修改

- ❌ `api.js`: 移除 startAgent() 的 maxTurns 參數
- ❌ UI 元件: 清理不存在欄位的顯示

### 文件更新

- ❌ `API_CONTRACT_SPECIFICATION.md`
- ❌ `ORM_CONTRACT_SPECIFICATION.md`
- ❌ `SERVICE_CONTRACT_SPECIFICATION.md`

---

## 🎯 執行優先級

### 階段 0: 資料庫修正 (最優先) ⚠️

**工作量**: 10 分鐘
**風險**: 低 (可回滾)

```bash
cd backend
sqlite3 casualtrader.db < migrations/20251109_0000_fix_performance_fields.sql
```

### 階段 1-5: Backend 修正

**工作量**: 4-6 小時
**風險**: 中等 (破壞性變更)

- 依照 `REFACTORING_ACTION_PLAN.md` 執行

### 階段 6: Frontend 修正

**工作量**: 2-3 小時
**風險**: 低

- 移除 1 個參數
- 清理 UI (如有使用)

### 階段 7: 文件同步

**工作量**: 1-2 小時
**風險**: 無

- 更新 3 份規格文件

### 階段 8: 測試驗證

**工作量**: 2-3 小時
**風險**: 無

- Backend + Frontend + E2E 測試

---

## ⚠️ 破壞性變更清單

### API 契約變更

1. **POST /api/agents** (建立 Agent)
   - ❌ 移除: `strategy_prompt`, `max_turns`, `enabled_tools`, `custom_instructions`

2. **PUT /api/agents/{id}** (更新 Agent)
   - ❌ 移除: `strategy_prompt`, `enabled_tools`, `custom_instructions`

3. **GET /api/agents/{id}** (查詢 Agent)
   - ❌ 移除: `strategy_prompt`, `max_turns`, `enabled_tools`, `custom_instructions`, `runtime_status`
   - ✅ 新增: `last_active_at`

4. **POST /api/agent-execution/{id}/start** (啟動 Agent)
   - ❌ 移除: `max_turns` 參數

### 資料庫 Schema 變更

1. **agent_performance 表**
   - 欄位重新命名: `winning_trades` → `sell_trades_count`
   - 新增欄位: `winning_trades_correct`

---

## 📊 預期影響範圍

| 範圍 | 影響程度 | 工作量 | 風險 | 檔案數 |
|------|---------|--------|------|--------|
| Backend | 🔴 高 | 4-6h | 🟡 中 | ~10 |
| Frontend | 🟡 中 | 2-3h | 🟢 低 | ~3 |
| Database | 🟡 中 | 10min | 🟢 低 | 1 |
| Docs | 🟡 中 | 1-2h | - | 3 |
| Tests | 🟡 中 | 2-3h | - | ~10 |
| **總計** | 🔴 高 | **10-16h** | 🟡 中 | **~27** |

---

## ✅ 檢查清單

### 準備階段 ✅

- [x] ✅ 審查實際資料庫 schema
- [x] ✅ 分析績效計算邏輯
- [x] ✅ 識別規範與實作差異
- [x] ✅ 制定重構計劃
- [x] ✅ 建立 Migration 腳本
- [x] ✅ 決策確認 (接受破壞性變更)
- [ ] ⏳ 通知前端團隊 API 變更 (階段 5 前)
- [ ] ⏳ 備份生產資料庫 (部署前)

### 執行階段

- [x] ✅ 階段 0: 資料庫 Migration (2025-11-09)
- [x] ✅ 階段 1: ORM 模型修正 (2025-11-09)
- [x] ✅ 階段 2: 績效計算修正 (2025-11-09)
- [ ] ⏳ 階段 3: API Schema 層修正 (當前)
- [ ] ⏳ 階段 4: API Router 修正
- [ ] ⏳ 階段 5: Frontend 修正
- [ ] ⏳ 階段 6: 文件同步
- [ ] ⏳ 階段 7: 測試驗證

### 驗證階段

- [ ] Backend 契約測試通過
- [ ] Backend 集成測試通過
- [ ] Backend API 手動測試通過
- [ ] Frontend 單元測試通過
- [ ] Frontend E2E 測試通過
- [ ] 前後端整合測試通過

### 部署階段

- [ ] 更新 CHANGELOG
- [ ] 更新 API 文件
- [ ] 發布版本 (含 Breaking Changes 警告)
- [ ] 監控錯誤日誌

---

## 📖 後續工作 (中長期)

基於 `PERFORMANCE_CALCULATION_ANALYSIS.md`，以下功能需要在未來實現：

### 優先級 1: 實現缺失的績效計算 (2-3 週)

1. **realized_pnl (已實現損益)**
   - 實現買賣配對邏輯 (FIFO)
   - 計算每筆賣出交易的真實損益
   - 測試多次買入賣出情境

2. **unrealized_pnl (未實現損益)**
   - 整合實時股價 API (Yahoo Finance / TWSE)
   - 建立股價快取機制
   - 每日收盤後更新

3. **daily_return (當日報酬率)**
   - 實現歷史績效資料查詢
   - 處理交易日判斷 (週末/假日)

### 優先級 2: 修正錯誤定義 (1-2 週)

4. **winning_trades_correct (真實獲利交易數)**
   - 實現買賣配對邏輯
   - 判斷每筆交易是否獲利
   - 計算真實勝率

5. **win_rate (勝率)**
   - 修正為: 獲利交易數 / 已完成交易對數
   - 而非當前的: 賣出交易數 / 總交易數

### 優先級 3: 實現進階指標 (4-6 週)

6. **max_drawdown (最大回撤)**
   - 建立歷史淨值曲線
   - 追蹤滾動最高點
   - 計算最大回撤百分比

7. **其他進階指標**
   - Sharpe Ratio (夏普比率)
   - Sortino Ratio (索提諾比率)
   - Calmar Ratio (卡瑪比率)
   - Alpha, Beta

---

## 📞 聯絡資訊

- **問題回報**: GitHub Issues
- **技術討論**: 開發團隊 Slack
- **文件維護**: CasualTrader 開發團隊

---

---

## 📝 版本記錄

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|---------|------|
| 1.0 | 2025-11-09 | 初版：審查報告 + 重構計劃 | Claude (AI) |
| 1.1 | 2025-11-09 13:02 | 更新進度追蹤：階段 0-2 完成 | Claude (AI) |

---

**審查完成日期**: 2025-11-09
**規劃完成日期**: 2025-11-09
**執行開始日期**: 2025-11-09
**最後更新**: 2025-11-09 13:02
**預計總時間**: 10-16 小時
**已花費時間**: 2.5 小時
**剩餘時間**: 7.5-13.5 小時
**狀態**: 🟡 進行中 (33% 完成)

**追蹤文件**:
1. `docs/REFACTORING_ACTION_PLAN.md` ⭐ - **即時進度追蹤**
2. `docs/REFACTORING_COMPLETION_REPORT.md` ⭐ - 階段 0-2 完成報告
3. `docs/DATABASE_SCHEMA_SPECIFICATION.md` - 資料庫標準
4. `docs/PERFORMANCE_CALCULATION_ANALYSIS.md` - 績效分析
5. `docs/SPECIFICATION_REVIEW_REPORT.md` - 審查報告
6. `backend/migrations/20251109_0000_fix_performance_fields.sql` - Migration 腳本
