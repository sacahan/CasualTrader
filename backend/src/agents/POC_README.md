# CasualTrader 重構概念驗證 (POC)

本目錄包含重構方案的概念驗證實作，用於驗證新架構的可行性。

## 📋 POC 檔案說明

### 核心檔案

1. **`poc_trading_agent.py`**
   - 簡化的 TradingAgent 實作
   - 展示從資料庫載入配置
   - 展示 MCP/Tools 整合
   - 展示 Trace 功能

2. **`poc_agent_service.py`**
   - 資料庫服務層概念驗證
   - 展示配置載入和驗證
   - 展示錯誤處理

3. **`poc_full_workflow.py`**
   - 完整工作流程展示
   - 從資料庫載入 → 初始化 → 執行
   - 可直接運行的測試腳本

## 🚀 運行 POC

### 前置需求

```bash
# 1. Python 3.12+
python --version

# 2. 安裝依賴
cd backend
pip install -r requirements.txt

# 3. 設置 OpenAI API Key
export OPENAI_API_KEY='your-api-key-here'
```

### 運行完整工作流程測試

```bash
# 從 backend 目錄運行
cd backend
python -m src.agents.poc_full_workflow
```

### 運行個別測試

```bash
# 測試 TradingAgent
python -m src.agents.poc_trading_agent

# 測試資料庫服務
python -m src.database.poc_agent_service
```

## 📊 預期輸出

### 成功輸出範例

```
================================================================================
CasualTrader Agent POC - 完整工作流程測試
================================================================================

【Step 1】設置測試資料庫...
✓ Database schema created

【Step 2】建立測試 Agent 資料...
✓ Test agent created: poc_agent_001

【Step 3】從資料庫載入 Agent 配置...
✓ 載入成功:
  - Agent ID: poc_agent_001
  - 名稱: POC 交易分析助手
  - AI 模型: gpt-4o-mini
  - 初始資金: TWD 100,000
  - 啟用工具: web_search, fundamental_analysis, technical_analysis

【Step 4】創建 TradingAgent 實例...
✓ TradingAgent 創建成功

【Step 5】初始化 Agent (設置 MCP/Tools)...
✓ Agent 初始化成功
  - MCP Servers: 1
  - OpenAI Tools: 1

【Step 6】執行交易會話 (OBSERVATION 模式)...
⏳ 正在執行 Agent（這可能需要幾秒鐘）...

================================================================================
執行結果
================================================================================
✓ 執行成功

模式: OBSERVATION
Trace ID: abc123...
Trace URL: https://platform.openai.com/traces/trace?trace_id=abc123...

--- Agent 輸出 ---
根據市場分析，台股大盤...
--- 輸出結束 ---

================================================================================
POC 工作流程完成
================================================================================

✓ 概念驗證完成！

總結:
1. ✓ 成功從資料庫載入 Agent 配置
2. ✓ 成功創建 TradingAgent 實例
3. ✓ 配置解析正常運作
4. ✓ 架構設計驗證通過
```

## 🎯 POC 驗證目標

### 已驗證

- [x] 資料庫配置載入流程
- [x] TradingAgent 初始化邏輯
- [x] 配置解析和驗證
- [x] 錯誤處理機制
- [x] Trace 整合

### 待完整實作

- [ ] Sub-agents 載入和配置
- [ ] 完整的 MCP Server 生命週期管理
- [ ] API 整合
- [ ] 完整的測試套件
- [ ] 效能優化

## 🔍 驗證重點

### 1. 資料庫驅動配置 ✅

POC 展示了如何從資料庫的 `agents` 表載入配置：

```python
# 從資料庫載入
db_config = await service.get_agent_config(agent_id)

# 創建 Agent（使用資料庫配置）
trading_agent = POCTradingAgent(agent_id, db_config)
```

### 2. 配置驗證 ✅

展示了配置驗證和錯誤處理：

```python
# 驗證必要欄位
if not agent.name:
    raise AgentConfigurationError("Agent name is required")

# 驗證 JSON 格式
try:
    json.loads(agent.investment_preferences)
except json.JSONDecodeError:
    raise AgentConfigurationError("Invalid JSON")
```

### 3. Trace 整合 ✅

展示了正確的 trace 用法：

```python
trace_id = gen_trace_id()
with trace(workflow_name="Trading Session", group_id=session_id, trace_id=trace_id):
    result = await Runner.run(agent, prompt)
```

## ⚠️ 已知限制

### POC 簡化部分

1. **MCP Server 路徑**
   - POC 使用硬編碼的路徑
   - 實際部署需要從環境變數或配置檔讀取

2. **Sub-agents**
   - POC 暫時不載入 Sub-agents
   - 完整實作需要實作 Sub-agent 工廠

3. **資料庫**
   - POC 使用記憶體資料庫
   - 實際使用需要連接到 `casualtrader.db`

4. **錯誤處理**
   - POC 基本錯誤處理已實作
   - 需要更完善的重試邏輯和降級策略

## 📝 後續步驟

### Phase 1: 完善 POC（1-2天）

1. [ ] 實作 Sub-agents 載入邏輯
2. [ ] 添加更多錯誤情境測試
3. [ ] 完善 MCP Server 配置管理
4. [ ] 添加效能監控

### Phase 2: 正式重構（3-5天）

1. [ ] 替換現有的 `trading_agent.py`
2. [ ] 更新 API 路由
3. [ ] 建立完整測試套件
4. [ ] 整合到實際資料庫

### Phase 3: 部署（1-2天）

1. [ ] 運行所有測試
2. [ ] 效能測試
3. [ ] 部署到測試環境
4. [ ] 監控和調整

## 🐛 疑難排解

### 問題: MCP Server 啟動失敗

```bash
# 檢查 MCP Server 路徑
ls /Users/sacahan/Documents/workspace/CasualMarket

# 或者修改 POC 代碼中的路徑
```

### 問題: OpenAI API 錯誤

```bash
# 確認 API Key 已設置
echo $OPENAI_API_KEY

# 重新設置
export OPENAI_API_KEY='your-key'
```

### 問題: 模組導入錯誤

```bash
# 確保從正確的目錄運行
cd backend
python -m src.agents.poc_full_workflow
```

## 📚 相關文檔

- [REFACTOR_PLAN.md](../../docs/REFACTOR_PLAN.md) - 完整重構計劃
- [REFACTOR_IMPLEMENTATION_GUIDE.md](../../docs/REFACTOR_IMPLEMENTATION_GUIDE.md) - 實施指南
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) - 官方文檔

## 💡 貢獻

如果您在運行 POC 時發現問題或有改進建議，請：

1. 記錄詳細的錯誤訊息
2. 提供運行環境資訊
3. 提交 Issue 或 PR

---

**維護**: CasualTrader Development Team
**最後更新**: 2025-10-15
