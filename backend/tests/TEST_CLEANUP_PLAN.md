# 測試代碼清理計劃

## 📊 當前測試狀況分析

### 測試文件清單 (42個文件)

#### ❌ 需要移除/更新的測試（基於舊架構）

##### 1. 舊架構測試 - 移到 DEPRECATED/

- `tests/agents/core/test_mcp_config_parsing.py` - 測試舊的 MCP 配置解析
- `tests/e2e/test_refactor.py` - 測試舊的 AgentConfig/TradingAgent
- `tests/e2e/test_refactor_simple.py` - 舊重構測試
- `tests/e2e/test_tc001_fix.py` - 特定 bug 修復測試
- `tests/database/test_agent_infrastructure.py` - 測試舊的 AgentManager/AgentSession

##### 2. 需要更新的測試（可能有用）

- `tests/agents/tools/test_*_agent.py` - Sub-agent 測試，需要更新為新 API
- `tests/agents/integrations/test_trading_agent_tools.py` - 工具整合測試
- `tests/database/test_migration.py` - 資料庫遷移測試（保留）
- `tests/api/test_phase3_api.py` - API 測試（需要更新）

##### 3. 保留的測試

- `tests/e2e/test_complete_user_workflow.py` - 完整用戶流程（需要更新）
- `tests/e2e/test_database_verification.py` - 資料庫驗證（保留）
- `tests/e2e/test_performance.py` - 性能測試（保留）
- `tests/e2e/conftest.py` - Pytest fixtures（需要更新）

## 🎯 清理執行計劃

### Phase 1: 移動過時測試到 DEPRECATED/ ✅

```bash
# 移動舊架構測試
mv tests/agents/core/test_mcp_config_parsing.py tests/DEPRECATED/
mv tests/e2e/test_refactor.py tests/DEPRECATED/
mv tests/e2e/test_refactor_simple.py tests/DEPRECATED/
mv tests/e2e/test_tc001_fix.py tests/DEPRECATED/
mv tests/database/test_agent_infrastructure.py tests/DEPRECATED/
```

### Phase 2: 移動待更新的 Sub-agent 測試

```bash
# 這些測試需要在重構 Sub-agents 後重寫
mkdir -p tests/DEPRECATED/agents_tools_old
mv tests/agents/tools/test_fundamental_agent.py tests/DEPRECATED/agents_tools_old/
mv tests/agents/tools/test_fundamental_agent_new.py tests/DEPRECATED/agents_tools_old/
mv tests/agents/tools/test_technical_agent.py tests/DEPRECATED/agents_tools_old/
mv tests/agents/tools/test_risk_agent.py tests/DEPRECATED/agents_tools_old/
mv tests/agents/tools/test_sentiment_agent.py tests/DEPRECATED/agents_tools_old/
mv tests/agents/integrations/test_trading_agent_tools.py tests/DEPRECATED/agents_tools_old/
```

### Phase 3: 清理空目錄

```bash
# 移除空的目錄結構
rmdir tests/agents/core 2>/dev/null || true
rmdir tests/agents/functions 2>/dev/null || true
rmdir tests/agents/trading 2>/dev/null || true
rmdir tests/agents/utils 2>/dev/null || true
```

### Phase 4: 更新保留的測試

在後續任務中更新：

- `tests/api/test_phase3_api.py` → Task 9 (更新 API 路由)
- `tests/e2e/test_complete_user_workflow.py` → Task 8 (編寫測試)
- `tests/e2e/conftest.py` → Task 8 (編寫測試)

## ✅ 執行結果

### 移動的文件

- 5 個舊架構測試 → `DEPRECATED/`
- 6 個 Sub-agent 測試 → `DEPRECATED/agents_tools_old/`

### 保留的文件

- `tests/database/test_migration.py` - 資料庫遷移測試
- `tests/e2e/test_complete_user_workflow.py` - E2E 測試（待更新）
- `tests/e2e/test_database_verification.py` - 資料庫驗證
- `tests/e2e/test_performance.py` - 性能測試
- `tests/e2e/conftest.py` - Pytest fixtures（待更新）
- `tests/api/test_phase3_api.py` - API 測試（待更新）

## 📝 下一步

在 Task 8 (編寫測試) 時，我們將：

1. 為新的 `agent_service.py` 編寫單元測試
2. 為新的 `trading_agent.py` 編寫單元測試
3. 為新的 `executor.py` 編寫單元測試
4. 更新 E2E 測試適配新架構
5. 更新 API 測試
