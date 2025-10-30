# 重構快速參考卡片 (Quick Reference Card)

## 🎯 一頁概覽

### 項目信息
- **項目名稱：** Agent 執行模式重構
- **開始日期：** 2025-10-30
- **完成期限：** 2025-11-13 (13-18 小時)
- **狀態：** 🔵 未開始
- **風險等級：** 🔴 高（破壞性更新）

### 目標
```
3 模式 → 2 模式（TRADING + REBALANCING）
移除 OBSERVATION，實現動態工具配置和記憶體深度整合
```

---

## 📊 進度速查表

| Phase | 名稱 | 時間 | 狀態 | 完成% |
|-------|------|------|------|-------|
| 1 | 移除 OBSERVATION | 2-3h | ⬜ | 0% |
| 2 | 動態工具配置 | 4-6h | ⬜ | 0% |
| 3 | 記憶體整合 | 3-4h | ⬜ | 0% |
| 4 | 測試和文檔 | 4-5h | ⬜ | 0% |
| **合計** | | **13-18h** | **⬜** | **0%** |

---

## 🔄 Phase 1：移除 OBSERVATION (2-3 小時)

### 關鍵檢查點
- [ ] `common/enums.py` - 移除 OBSERVATION
- [ ] `database/models.py` - 更新默認值
- [ ] SQL 遷移 - OBSERVATION → TRADING
- [ ] 代碼掃描 - 清理所有引用

### 驗收條件
✅ 只有 2 個模式
✅ 所有 session 已遷移
✅ 無代碼引用遺漏
✅ 測試通過

### 風險
🔴 數據遺失 → 備份數據庫
🟡 引用遺漏 → 完整掃描

---

## 🎛️ Phase 2：動態工具配置 (4-6 小時)

### 關鍵檢查點
- [ ] `src/trading/tool_config.py` - 新建（ToolRequirements + ToolConfig）
- [ ] `trading_agent.py` - initialize() 支持模式參數
- [ ] 初始化方法 - 支持工具配置
- [ ] 集成測試 - 工具加載驗證

### 驗收條件
✅ ToolConfig 實現完整
✅ TRADING 完整工具集加載
✅ REBALANCING 簡化工具集加載
✅ 集成測試通過

### 工具配置對比

**TRADING 模式（完整）**
```
OpenAI Tools: WebSearch + CodeInterpreter
Trading Tools: Buy/Sell + Portfolio
Sub-agents: Tech + Fundamental + Sentiment + Risk (4個)
MCP: memory + casual_market + tavily (3個)
```

**REBALANCING 模式（簡化）**
```
OpenAI Tools: CodeInterpreter only
Trading Tools: Portfolio only (無Buy/Sell)
Sub-agents: Tech + Risk (2個)
MCP: memory + casual_market (無tavily)
```

---

## 🧠 Phase 3：記憶體整合 (3-4 小時)

### 關鍵檢查點
- [ ] `_load_execution_memory()` - 加載上輪記憶
- [ ] `_save_execution_memory()` - 保存本輪記憶
- [ ] `_plan_next_steps()` - 規劃下一步
- [ ] `_build_instructions()` - 融入記憶到 prompt

### 驗收條件
✅ 記憶體工作流完整
✅ 記憶體融入 system prompt
✅ 下一步規劃實現
✅ 集成測試通過

### 記憶體流程
```
[上一輪記憶] → [System Prompt] → [執行] → [決策]
                                    ↓
                              [記錄結果] → [規劃下一步] → [存入記憶庫]
```

---

## ✅ Phase 4：測試和文檔 (4-5 小時)

### 關鍵檢查點
- [ ] 單元測試 - 覆蓋率 > 85%
- [ ] 集成測試 - 兩種模式完整流程
- [ ] 迴歸測試 - 現有功能無破壞
- [ ] 文檔更新 - API / 實施 / 用戶 / 開發
- [ ] 前端更新 - 移除 OBSERVATION

### 驗收條件
✅ 單元測試通過 100%
✅ 集成測試通過 100%
✅ 迴歸測試通過 100%
✅ 文檔完整清晰
✅ 前端無 OBSERVATION 代碼

---

## 🚀 部署檢查清單

### 部署前 24 小時
- [ ] 代碼審查通過（2 人以上）
- [ ] 性能基準測試完成
- [ ] 安全掃描通過
- [ ] 數據庫備份確認

### 部署執行
- [ ] 通知相關團隊
- [ ] 部署後端代碼
- [ ] 運行數據庫遷移
- [ ] 部署前端代碼
- [ ] 系統啟動驗證

### 部署後 1 小時
- [ ] 冒煙測試通過
- [ ] 兩種模式都能執行
- [ ] 記憶體工作流程正常
- [ ] 系統日誌無錯誤

### 部署後 24 小時
- [ ] 監控系統性能
- [ ] 監控錯誤率
- [ ] 收集用戶反饋
- [ ] 確認無重大問題

---

## 📝 文件修改速查

| 文件 | 操作 | 優先級 | 複雜度 |
|------|------|--------|--------|
| `common/enums.py` | 修改 | 🔴 高 | 低 |
| `database/models.py` | 修改 | 🔴 高 | 低 |
| `trading/tool_config.py` | **新建** | 🔴 高 | 中 |
| `trading/trading_agent.py` | 修改 | 🔴 高 | 高 |
| `trading/tools/trading_tools.py` | 修改 | 🟡 中 | 中 |
| `service/trading_service.py` | 修改 | 🟡 中 | 低 |
| `api/routers/agent_execution.py` | 修改 | 🟡 中 | 低 |
| `api/models.py` | 修改 | 🟡 中 | 低 |

---

## 🚨 高風險項目

| 風險 | 影響 | 檢測 | 應對 |
|------|------|------|------|
| 數據遺失 | 🔴 高 | SQL 驗證 | 恢復備份 |
| 工具加載失敗 | 🔴 高 | 初始化測試 | 調試配置 |
| 記憶體異常 | 🟡 中 | 功能測試 | 調整邏輯 |
| 前端不兼容 | 🟡 中 | 集成測試 | API 適配 |

---

## 📞 快速支援

### 遇到問題？
1. **數據遷移失敗** → 恢復備份，檢查 SQL 語法
2. **工具加載失敗** → 檢查 ToolConfig 配置
3. **記憶體問題** → 檢查 memory_mcp 連接
4. **測試失敗** → 檢查依賴模式是否完成

### 關鍵文檔
- 🔗 [詳細方案](REFACTOR_PLAN.md)
- 🔗 [Milestone 追蹤](REFACTOR_MILESTONE.md)
- 🔗 [進度看板](REFACTOR_PROGRESS.md)
- 🔗 [本卡片](REFACTOR_QUICK_REF.md)

---

## ⏰ 時間管理建議

### Day 1 - Phase 1 (2-3 小時)
```
09:00 - 準備環境、備份數據庫 (30分鐘)
09:30 - 修改代碼、遷移數據 (90分鐘)
11:00 - 代碼掃描、清理引用 (30分鐘)
11:30 - 驗收、代碼審查 (30分鐘)
12:00 ✅ Phase 1 完成
```

### Day 2 - Phase 2 (4-6 小時)
```
09:00 - 新建 tool_config.py (60分鐘)
10:00 - 修改 trading_agent.py (120分鐘)
12:00 - 午餐休息
13:00 - 修改初始化方法 (90分鐘)
14:30 - 集成測試 (60分鐘)
15:30 ✅ Phase 2 完成
```

### Day 2.5 - Phase 3 (3-4 小時)
```
16:00 - 分析記憶體系統 (30分鐘)
16:30 - 實現記憶體方法 (90分鐘)
18:00 - 修改 run() 方法 (60分鐘)
19:00 - 集成測試 (30分鐘)
19:30 ✅ Phase 3 完成
```

### Day 3 - Phase 4 + 部署 (4-5 小時 + 部署)
```
09:00 - 單元測試 (90分鐘)
10:30 - 集成測試 (60分鐘)
11:30 - 文檔更新、前端調整 (60分鐘)
12:30 - 午餐休息
13:30 - 部署前檢查 (60分鐘)
14:30 - 部署執行 (60分鐘)
15:30 ✅ 部署完成
16:00 - 監控和驗證 (持續 24小時)
```

---

## 📱 快速命令

### 數據遷移
```sql
-- 遷移 OBSERVATION session 到 TRADING
UPDATE agent_sessions SET mode = 'TRADING' WHERE mode = 'OBSERVATION';

-- 驗證遷移
SELECT DISTINCT mode FROM agent_sessions;
SELECT COUNT(*) FROM agent_sessions WHERE mode = 'OBSERVATION';
```

### 代碼掃描
```bash
# 後端掃描
grep -r "OBSERVATION" backend/src/

# 前端掃描
grep -r "OBSERVATION" frontend/

# 測試文件掃描
grep -r "observation" backend/tests/
```

### 測試運行
```bash
# 單元測試
pytest backend/tests/unit/ -v --cov=backend/src/trading/

# 集成測試
pytest backend/tests/integration/ -v

# 特定 Phase 測試
pytest backend/tests/ -k "trading_mode" -v
```

---

## ✨ 成功標誌

🟢 **Phase 1 成功標誌**
- ✅ 枚舉中只有 2 種模式
- ✅ 數據庫中無 OBSERVATION session
- ✅ 無代碼引用遺漏
- ✅ 測試 100% 通過

🟢 **Phase 2 成功標誌**
- ✅ TRADING 工具集完整加載
- ✅ REBALANCING 工具集簡化加載
- ✅ 初始化時間符合預期
- ✅ 集成測試 100% 通過

🟢 **Phase 3 成功標誌**
- ✅ 記憶體工作流程完整
- ✅ 記憶體融入 prompt
- ✅ 下一步規劃正常工作
- ✅ 集成測試 100% 通過

🟢 **Phase 4 成功標誌**
- ✅ 測試覆蓋率 > 85%
- ✅ 所有測試 100% 通過
- ✅ 文檔完整清晰
- ✅ 前端無舊代碼

🟢 **部署成功標誌**
- ✅ 系統正常啟動
- ✅ 冒煙測試通過
- ✅ 兩種模式都能執行
- ✅ 監控 24 小時無重大錯誤

---

**版本：** 1.0
**最後更新：** 2025-10-30
**打印建議：** 每日隨身攜帶，便於快速查詢
