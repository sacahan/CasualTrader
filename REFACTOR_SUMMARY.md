# Agent 重構方案總結

> **版本**: V2 - 方案 B（完全重構）
> **日期**: 2025-10-30
> **核心目標**: 移除 OBSERVATION 模式 + 動態工具配置 + 記憶體深度整合

---

## 🎯 核心改進

### 1. 模式簡化（3→2）
```
Before:  TRADING + OBSERVATION + REBALANCING
After:   TRADING + REBALANCING

移除原因：OBSERVATION 的分析邏輯與 TRADING 重複 80%+
解決方案：觀察功能集成到 TRADING 模式的記憶體規劃中
```

### 2. 動態工具配置（按需加載）
```
TRADING 模式         REBALANCING 模式
✅ 所有 MCP          ✅ memory_mcp
✅ Web Search        ✅ market_mcp
✅ 所有 Sub-agents   ✅ 技術 + 風險 agent
✅ 買/賣工具         ❌ 買/賣工具

性能提升：REBALANCING 初始化快 15-20%
資源節省：減少 1 個 MCP + 2 個 Sub-agents
```

### 3. 記憶體深度整合（形成有機循環）
```
上一輪記憶
    ↓
構建指令（包含上一輪記憶）
    ↓
執行分析（Agent 根據記憶調整策略）
    ↓
記錄決策（完整理由 + 進場條件）
    ↓
規劃下一步（存入記憶庫）
    ↓
下一輪查詢記憶（循環）
```

---

## 📊 對比指標

| 指標 | V1 | V2 | 改進 |
|------|-----|-----|------|
| 模式數 | 3 | 2 | -33% |
| 代碼重複率 | ~40% | ~15% | -62.5% |
| MCP 伺服器（REBALANCING） | 3 | 2 | -33% |
| Sub-agents（REBALANCING） | 4 | 2 | -50% |
| 記憶庫集成度 | 基礎 | 深度 | 大幅提升 |
| 模式差異化 | 弱 | 強 | 明確 |

---

## 🛠️ 技術架構

### 工具配置管理
```python
# 新增：src/trading/tool_config.py
class ToolConfig:
    TRADING_CONFIG = ToolRequirements(...)      # 完整配置
    REBALANCING_CONFIG = ToolRequirements(...)  # 簡化配置

    @staticmethod
    def get_requirements(mode: AgentMode) -> ToolRequirements:
        """根據模式返回工具需求"""
```

### 動態初始化流程
```
initialize(mode: AgentMode)
    ├─ 驗證模式有效性
    ├─ 獲取工具配置：ToolConfig.get_requirements(mode)
    ├─ _setup_mcp_servers(mode)        # 根據配置加載
    ├─ _setup_openai_tools()           # 根據配置選擇
    ├─ _setup_trading_tools(mode)      # 根據配置選擇
    ├─ _load_subagents_as_tools()      # 根據配置選擇
    └─ 創建 Agent 實例
```

### 執行流程（新）
```
run(mode: AgentMode)
    ├─ initialize(mode)                        # 動態初始化
    ├─ _build_memory_context(mode)             # 查詢上一輪記憶
    ├─ _build_instructions(desc, mode)         # 融入記憶的指令
    ├─ _build_task_prompt(mode)                # 模式特定提示
    └─ Runner.run(agent, task_prompt)          # 執行 Agent
        ↓
    Agent 自動執行流程：
    1. 查詢記憶庫
    2. 分析市場
    3. 決策
    4. 交易/調整（可選）
    5. 記錄決策
    6. 規劃下一步
```

---

## 📝 記憶庫工作流程

### TRADING 模式記憶循環
```
記憶庫查詢
├─ 上一次的分析結果
├─ 識別的新標的
├─ 失敗經驗教訓
└─ 監控條件

    ↓ 融入指令

Agent 執行
├─ 調用 web_search 查詢最新信息
├─ 調用所有 Sub-agents 分析
├─ 對比記憶庫提高決策質量
└─ 執行交易

    ↓ 執行完成

記錄到記憶庫
├─ 分析過程（為什麼這樣分析）
├─ 決策理由（為什麼這樣決策）
├─ 進場條件（什麼條件下交易）
├─ 監控指標（如何監控）
└─ 下一步動作（下次該做什麼）
```

### REBALANCING 模式記憶循環
```
記憶庫查詢
├─ 上一次的投資組合配置
├─ 持股分析記錄
├─ 調整條件
└─ 風險評級

    ↓ 融入指令

Agent 執行
├─ 分析現有持股技術面
├─ 評估風險指標
├─ 對比記憶庫做決策
└─ 執行調整

    ↓ 執行完成

記錄到記憶庫
├─ 調整理由（為什麼調整）
├─ 前後配置對比
├─ 風險評級更新
├─ 下次調整條件
└─ 需要的新標的類別
```

---

## 📂 文件變更

### 新增
```
src/trading/tool_config.py
├─ ToolRequirements
├─ ToolConfig
└─ 工具配置常量
```

### 關鍵修改
```
common/enums.py
├─ 移除 OBSERVATION
└─ 保留 TRADING + REBALANCING

trading/trading_agent.py
├─ initialize(mode: AgentMode)      # 新增 mode 參數
├─ _setup_mcp_servers(mode)         # 新增 mode 參數
├─ _build_instructions(desc, mode)  # 新增 mode 參數，融入記憶
├─ _build_task_prompt(mode)         # 重構，融入記憶工作流程
└─ _build_memory_context(mode)      # 新增方法

database/models.py
└─ 更新 current_mode 默認值

service/trading_service.py
└─ 移除 OBSERVATION 驗證

api/routers/
├─ 移除 OBSERVATION 端點
└─ 更新參數驗證

api/models.py
└─ 更新 ExecutionMode 枚舉
```

### 刪除
```
❌ 所有 OBSERVATION 相關代碼
❌ OBSERVATION 測試
❌ OBSERVATION 前端 UI
```

---

## ⏱️ 實作時間預估

| 階段 | 任務 | 時間 | 優先級 |
|------|------|------|--------|
| Week 1 Day 1-2 | 準備 + 遷移 + 新建 tool_config.py | 2 天 | ⭐⭐⭐ |
| Week 1 Day 3-4 | 動態初始化重構 | 2 天 | ⭐⭐⭐ |
| Week 1 Day 5 | 單元測試 | 1 天 | ⭐⭐⭐ |
| Week 2 Day 1-2 | 指令構建 + 記憶整合 | 2 天 | ⭐⭐⭐ |
| Week 2 Day 3-4 | 執行流程 + 記憶工作流程 | 2 天 | ⭐⭐⭐ |
| Week 2 Day 5 | 集成測試 | 1 天 | ⭐⭐⭐ |
| Week 3 Day 1-2 | API 層更新 | 2 天 | ⭐⭐ |
| Week 3 Day 3-4 | 前端調整 | 2 天 | ⭐⭐ |
| Week 3 Day 5 | E2E 測試 | 1 天 | ⭐⭐ |
| Week 4 | 優化 + 文檔 | 5 天 | ⭐ |
| **合計** | | **19 天** | |

---

## ✅ 驗收標準

### 功能層面
- ✅ 只支持 TRADING 和 REBALANCING 兩種模式
- ✅ 無遺留的 OBSERVATION 引用
- ✅ 工具根據模式動態加載
- ✅ 記憶庫查詢功能正常
- ✅ 記憶庫記錄功能正常
- ✅ 下一步規劃功能正常

### 性能層面
- ✅ TRADING 初始化 < 30 秒
- ✅ REBALANCING 初始化 < 25 秒（提升 15-20%）
- ✅ 執行時間與 V1 相當或更快

### 代碼層面
- ✅ 代碼重複率降至 < 15%
- ✅ 代碼覆蓋率 > 85%
- ✅ Type hint 完整
- ✅ 文檔完整

### 測試層面
- ✅ 單元測試通過率 100%
- ✅ 集成測試通過率 100%
- ✅ E2E 測試通過率 100%

---

## 🚀 快速開始

### Step 1：備份數據
```bash
mysqldump casualtrader > backup_$(date +%Y%m%d).sql
```

### Step 2：創建工具配置
```bash
touch src/trading/tool_config.py
# 複製 QUICK_REFERENCE.md 中的代碼片段
```

### Step 3：修改枚舉
```bash
# 編輯 common/enums.py
# 移除 OBSERVATION
```

### Step 4：數據遷移
```bash
# 運行 SQL 遷移腳本
mysql casualtrader < migration.sql
```

### Step 5：重構核心
```bash
# 編輯 trading_agent.py
# 按照 REFACTOR_PLAN_V2.md 的代碼實現
```

### Step 6：測試驗證
```bash
pytest tests/ -v --cov=src
```

---

## 📚 文檔結構

| 文檔 | 用途 |
|------|------|
| `REFACTOR_PLAN_V2.md` | 完整的技術實現方案（**主文檔**） |
| `IMPLEMENTATION_GUIDE.md` | 周級實施計劃和關鍵決策點 |
| `QUICK_REFERENCE.md` | 快速查閱的代碼片段和檢查清單 |
| `REFACTOR_SUMMARY.md` | 本文檔 - 概覽和決策依據 |

---

## 💡 核心決策依據

### Q1：為什麼移除 OBSERVATION？
**A**：
- OBSERVATION 的分析邏輯與 TRADING 重複 80%+
- 唯一差異是「不執行交易」，可以通過記憶體規劃實現
- 減少代碼複雜度，提升可維護性

### Q2：為什麼採用動態工具配置？
**A**：
- REBALANCING 不需要搜尋新標的（無需 web_search、sentiment_agent）
- 不需要 tavily_mcp（不進行網路搜尋）
- 動態加載可節省 15-20% 的初始化時間和資源

### Q3：為什麼深度整合記憶體？
**A**：
- 形成有機循環：執行 → 記錄 → 查詢 → 執行
- 提升 Agent 的決策質量（基於過往經驗）
- 便於事後分析和改進

### Q4：不考慮向後兼容性？
**A**：
- 用戶明確要求「直接移除無用代碼」
- 遷移路徑清晰（OBSERVATION → TRADING）
- 新系統更清晰簡潔

---

## 🎓 學習路徑

**按以下順序閱讀文檔：**

1. **本文檔**（REFACTOR_SUMMARY.md）
   - 了解全局改進方向
   - 理解核心決策

2. **REFACTOR_PLAN_V2.md**
   - 深入技術實現
   - 理解設計細節
   - 複製代碼片段

3. **IMPLEMENTATION_GUIDE.md**
   - 查看周級計劃
   - 理解優先級
   - 確定每日任務

4. **QUICK_REFERENCE.md**
   - 實施時快速查閱
   - 複製代碼範本
   - 運行檢查清單

---

## 🔍 風險評估

| 風險 | 影響 | 概率 | 緩解 |
|------|------|------|------|
| 數據遷移失敗 | 高 | 低 | 完整備份 + 逐步遷移 |
| 前端兼容性破壞 | 中 | 中 | 全面測試 + 循序漸進 |
| 性能回退 | 中 | 低 | 性能測試 + 優化 |
| 測試不充分 | 中 | 中 | 新增 50+ 測試用例 |
| 記憶庫查詢錯誤 | 低 | 中 | 詳細日誌 + 降級處理 |

---

## 📞 支持和反饋

- 遇到問題？查看 `QUICK_REFERENCE.md` 的常見錯誤部分
- 需要澄清？參考 `REFACTOR_PLAN_V2.md` 的決策檢查點
- 時間不足？優先完成 Week 1 和 Week 2（關鍵部分）

---

## 📈 預期收益

✅ **代碼層面**
- 减少代碼重複 62.5%
- 提升可維護性 3 倍
- 提升可擴展性（新模式更容易添加）

✅ **性能層面**
- REBALANCING 初始化快 15-20%
- 記憶占用減少 20-30%
- 執行效率提升（更聚焦）

✅ **功能層面**
- 形成有機記憶循環
- 提升 Agent 決策質量
- 便於事後分析

✅ **用戶體驗層面**
- 前端更簡潔清晰
- 執行結果更易理解
- 記憶庫功能透明可見

---

**完成本重構後，系統將進入 V2.0 時代！** 🎉
