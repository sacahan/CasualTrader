# Agent 重構快速參考

## 文件變更清單

### 需要創建的新文件
```
src/trading/tool_config.py
├─ ToolRequirements (dataclass)
├─ ToolConfig (class)
└─ ToolConfig.get_requirements(mode: AgentMode) -> ToolRequirements
```

### 需要修改的文件

| 文件 | 修改內容 | 優先級 |
|------|---------|--------|
| `common/enums.py` | 移除 OBSERVATION | ⭐⭐⭐ |
| `database/models.py` | 更新 current_mode 默認值 | ⭐⭐⭐ |
| `trading/trading_agent.py` | 重構整個初始化和執行流程 | ⭐⭐⭐ |
| `trading/tools/trading_tools.py` | 添加 mode 參數到 create_trading_tools() | ⭐⭐⭐ |
| `service/trading_service.py` | 移除 OBSERVATION 驗證 | ⭐⭐ |
| `api/routers/agent_execution.py` | 移除或遷移 OBSERVATION 端點 | ⭐⭐ |
| `api/models.py` | 更新 ExecutionMode 枚舉 | ⭐⭐ |
| 前端代碼 | 更新模式選擇 UI | ⭐⭐ |

### 需要刪除的代碼

```
❌ OBSERVATION 模式所有相關代碼
❌ OBSERVATION 相關的 API 端點（或遷移到 TRADING）
❌ OBSERVATION 的前端 UI
❌ 所有 OBSERVATION 測試
```

---

## 代碼片段（快速實現）

### 1. 新建 tool_config.py
```python
from enum import Enum
from dataclasses import dataclass
from common.enums import AgentMode

@dataclass
class ToolRequirements:
    """工具需求配置"""
    include_web_search: bool
    include_code_interpreter: bool
    include_buy_sell_tools: bool
    include_portfolio_tools: bool
    include_technical_agent: bool
    include_fundamental_agent: bool
    include_sentiment_agent: bool
    include_risk_agent: bool
    include_memory_mcp: bool
    include_casual_market_mcp: bool
    include_tavily_mcp: bool

class ToolConfig:
    """根據執行模式返回工具配置"""

    TRADING_CONFIG = ToolRequirements(
        include_web_search=True,
        include_code_interpreter=True,
        include_buy_sell_tools=True,
        include_portfolio_tools=True,
        include_technical_agent=True,
        include_fundamental_agent=True,
        include_sentiment_agent=True,
        include_risk_agent=True,
        include_memory_mcp=True,
        include_casual_market_mcp=True,
        include_tavily_mcp=True,
    )

    REBALANCING_CONFIG = ToolRequirements(
        include_web_search=False,
        include_code_interpreter=True,
        include_buy_sell_tools=False,
        include_portfolio_tools=True,
        include_technical_agent=True,
        include_fundamental_agent=False,
        include_sentiment_agent=False,
        include_risk_agent=True,
        include_memory_mcp=True,
        include_casual_market_mcp=True,
        include_tavily_mcp=False,
    )

    @staticmethod
    def get_requirements(mode: AgentMode) -> ToolRequirements:
        if mode == AgentMode.TRADING:
            return ToolConfig.TRADING_CONFIG
        elif mode == AgentMode.REBALANCING:
            return ToolConfig.REBALANCING_CONFIG
        else:
            raise ValueError(f"Unknown mode: {mode}")
```

### 2. 修改 enums.py (關鍵部分)
```python
class AgentMode(str, Enum):
    """Agent 交易模式枚舉"""
    TRADING = "TRADING"
    REBALANCING = "REBALANCING"
    # ❌ 移除 OBSERVATION
```

### 3. 修改 trading_agent.py (initialize 方法簽名)
```python
async def initialize(self, mode: AgentMode | None = None) -> None:
    """初始化 Agent，支持指定模式"""
    if self.is_initialized:
        return

    if not self.agent_config:
        raise AgentConfigurationError(...)

    try:
        # 確定執行模式
        execution_mode = mode or self.agent_config.current_mode or AgentMode.TRADING

        # 驗證模式
        if execution_mode not in {AgentMode.TRADING, AgentMode.REBALANCING}:
            raise ValueError(f"Invalid mode: {execution_mode}")

        # 獲取工具配置
        self.tool_requirements = ToolConfig.get_requirements(execution_mode)

        # 初始化組件
        await self._setup_mcp_servers(execution_mode)
        self.openai_tools = self._setup_openai_tools()
        self.trading_tools = self._setup_trading_tools(execution_mode)
        # ... 繼續
```

### 4. 修改 run() 方法簽名
```python
async def run(
    self,
    mode: AgentMode | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """執行 Agent 任務"""
    if not self.is_initialized:
        raise AgentInitializationError(...)

    if not self.agent_config:
        raise AgentConfigurationError(...)

    execution_mode = mode or self.agent_config.current_mode or AgentMode.TRADING

    # 驗證模式
    if execution_mode not in {AgentMode.TRADING, AgentMode.REBALANCING}:
        raise ValueError(f"Invalid mode: {execution_mode}")

    # ... 繼續執行
```

---

## 快速測試清單

### 單元測試
```python
def test_tool_config_trading():
    """TRADING 模式配置"""
    req = ToolConfig.get_requirements(AgentMode.TRADING)
    assert req.include_web_search == True
    assert req.include_tavily_mcp == True

def test_tool_config_rebalancing():
    """REBALANCING 模式配置"""
    req = ToolConfig.get_requirements(AgentMode.REBALANCING)
    assert req.include_web_search == False
    assert req.include_tavily_mcp == False
    assert req.include_fundamental_agent == False
```

### 集成測試
```python
async def test_trading_mode_execution():
    """測試 TRADING 模式完整流程"""
    # 初始化
    # 執行
    # 驗證記憶庫

async def test_rebalancing_mode_execution():
    """測試 REBALANCING 模式完整流程"""
    # 初始化
    # 執行
    # 驗證記憶庫
```

---

## 記憶庫集成檢查清單

### _build_instructions() 中
- [ ] 包含上一輪執行記憶的查詢指令
- [ ] TRADING 模式的完整指令
- [ ] REBALANCING 模式的被動調整指令

### _build_task_prompt() 中
- [ ] 包含記憶庫查詢步驟
- [ ] 包含分析步驟
- [ ] 包含決策步驟
- [ ] 包含記錄到記憶庫的指令
- [ ] 包含下一步規劃指令

### Agent 執行時
- [ ] 自動查詢記憶庫上下文
- [ ] 執行完成後驗證記憶庫記錄
- [ ] 記錄執行統計信息

---

## 數據遷移 SQL

### 備份
```sql
-- 備份原始數據
CREATE TABLE agent_sessions_backup AS
SELECT * FROM agent_sessions;
```

### 遷移 OBSERVATION → TRADING
```sql
UPDATE agent_sessions
SET mode = 'TRADING'
WHERE mode = 'OBSERVATION';

-- 驗證
SELECT COUNT(*) FROM agent_sessions
WHERE mode = 'OBSERVATION';  -- 應為 0

SELECT COUNT(*) FROM agent_sessions
WHERE mode = 'TRADING';  -- 數字應增加
```

### 更新 Agent 默認模式
```sql
UPDATE agents
SET current_mode = 'TRADING'
WHERE current_mode = 'OBSERVATION'
OR current_mode IS NULL;
```

---

## 前端改動要點

### 移除
- ❌ OBSERVATION 模式按鈕
- ❌ OBSERVATION 相關的 API 調用
- ❌ OBSERVATION 的文檔和幫助文本

### 添加
- ✅ TRADING 模式說明（新標的搜尋 + 交易）
- ✅ REBALANCING 模式說明（現有持股調整）
- ✅ 模式選擇提示

### 更新
- 🔄 模式選擇下拉菜單（只保留 2 個選項）
- 🔄 執行按鈕邏輯
- 🔄 結果展示（根據模式差異化）

---

## 常見錯誤和解決方案

### 錯誤 1：`ValueError: Invalid mode: OBSERVATION`
**原因**：代碼中還在使用舊的 OBSERVATION 模式
**解決**：
1. 搜尋所有 `OBSERVATION` 引用
2. 根據上下文遷移到 `TRADING` 或 `REBALANCING`
3. 重新運行測試

### 錯誤 2：`AttributeError: 'TradingAgent' has no attribute 'tool_requirements'`
**原因**：沒有正確初始化 `tool_requirements`
**解決**：
1. 確保 `initialize()` 被調用
2. 確保 `_setup_mcp_servers()` 中設置了 `self.tool_requirements`

### 錯誤 3：缺少 MCP 伺服器
**原因**：REBALANCING 模式中不應加載 tavily_mcp
**解決**：
1. 檢查 `tool_requirements` 配置
2. 確保 `_setup_mcp_servers()` 正確檢查 `include_tavily_mcp`

### 錯誤 4：Sub-agent 未加載
**原因**：根據模式跳過了某些 agent
**解決**：
1. 檢查 `tool_requirements` 配置
2. 驗證 `_load_subagents_as_tools()` 中的條件邏輯
3. 查看日誌確認加載狀態

---

## 性能提升預估

### TRADING 模式
- 初始化時間：無變化（加載相同工具）
- 執行時間：可能略微提升（代碼優化）

### REBALANCING 模式
- 初始化時間：提升 ~15-20%（少加載 1 個 MCP + 2 個 sub-agents）
- 執行時間：提升 ~10-15%（分析工具更少）
- 記憶占用：降低 ~20-30%（更少的 MCP 進程）

---

## 驗收標準

### 功能驗收
- ✅ TRADING 模式完整執行（分析 + 決策 + 交易）
- ✅ REBALANCING 模式完整執行（分析 + 調整）
- ✅ 記憶庫查詢正常工作
- ✅ 記憶庫記錄正常工作
- ✅ 下一步規劃記錄正常工作

### 性能驗收
- ✅ TRADING 模式初始化 < 30 秒
- ✅ REBALANCING 模式初始化 < 25 秒
- ✅ 執行時間與 V1 相當或更快

### 測試驗收
- ✅ 單元測試通過率 100%
- ✅ 集成測試通過率 100%
- ✅ 代碼覆蓋率 > 80%

### 代碼質量驗收
- ✅ 無遺留的 OBSERVATION 引用
- ✅ 所有新代碼都有註釋
- ✅ Linter 檢查通過
- ✅ Type hint 完整
