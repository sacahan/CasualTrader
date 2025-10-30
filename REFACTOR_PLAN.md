# Agent 執行模式重構方案 - 完全重構版

## 文件概述

本文檔提供**完整的重構方案**，目標是將系統從三模式架構簡化為二模式架構，實現動態工具配置、記憶體深度整合，打造清晰、高效、易維護的系統。

**不討論漸進式方案，直接執行完全重構。**

---

## 當前狀態分析

### 現有執行模式的問題

**三種執行模式：**
1. **TRADING** - 尋找和執行交易機會
2. **REBALANCING** - 調整投資組合配置
3. **OBSERVATION** - 監控市場但不交易

**核心痛點：**
- 三種模式的分析邏輯高度重複（代碼重複率 ~40%）
- 全量加載所有工具，資源占用高且低效
- OBSERVATION 使用率低，維護成本高
- 難以添加新的模式或工具差異化需求
- 當前結構難以支持模式間的差異化工具配置

---

## 目標架構設計

### 二層架構

#### 第1層：執行模式 → 簡化為 2 個

```python
class AgentMode(str, Enum):
    """Agent 交易模式枚舉 - 最終簡化版"""

    TRADING = "TRADING"
    """
    主動搜尋模式 - 完整交易流程
    - 分析市場機會
    - 識別新的投資機會
    - 執行買賣交易
    """

    REBALANCING = "REBALANCING"
    """
    被動調整模式 - 聚焦現有持股
    - 分析現有投資組合效益
    - 識別風險和調整需求
    - 執行投資組合調整
    - 不搜尋新標的
    """
```

#### 第2層：執行流程控制 → 分為 3 個子階段（內部）

```python
class ExecutionPhase(str, Enum):
    """執行階段 - 內部使用，不暴露給用戶"""

    ANALYSIS = "analysis"
    DECISION = "decision"
    EXECUTION = "execution"
```

---

## 模式職責分配

### TRADING 模式（主動搜尋 + 完整交易）

```
流程：ANALYSIS → DECISION → EXECUTION

指令：
"分析市場機會，識別符合投資策略的標的，
評估風險，然後根據分析結果執行交易。"

任務：
1. 使用所有分析工具（技術、基本面、風險、情緒）
2. 識別新的投資機會
3. 決策是否進行交易
4. 執行買賣操作
5. 記錄決策理由

工具配置（完整套裝）：
├─ OpenAI Tools: WebSearch + CodeInterpreter
├─ Trading Tools: 買/賣工具 + 投資組合管理
├─ Sub-agents: 技術 + 基本面 + 情緒 + 風險 (4個)
└─ MCP: memory_mcp + casual_market_mcp + tavily_mcp
```

### REBALANCING 模式（被動調整 + 現有持股）

```
流程：ANALYSIS → DECISION

指令：
"分析當前投資組合的效益狀況，
評估各持股的風險回報比，
根據策略進行被動調整。不尋找新標的。"

任務：
1. 分析現有持股表現和風險
2. 評估持股比例是否適當
3. 識別需調整的高風險持股
4. 決策是否進行調整
5. 執行調整交易
6. 記錄調整理由

工具配置（簡化套裝）：
├─ OpenAI Tools: CodeInterpreter only (無WebSearch)
├─ Trading Tools: 投資組合管理 (無買/賣通用工具)
├─ Sub-agents: 技術 + 風險 (2個，無基本面、無情緒)
└─ MCP: memory_mcp + casual_market_mcp (無tavily)
```

---

## 實施方案詳細設計

### Phase 1：移除 OBSERVATION 並重構枚舉

#### 1.1 修改 `common/enums.py`

```python
from enum import Enum

class AgentMode(str, Enum):
    """Agent 交易模式枚舉 - 簡化版"""

    TRADING = "TRADING"
    """
    主動搜尋模式
    - 分析市場機會
    - 識別新的投資機會
    - 執行買賣交易
    """

    REBALANCING = "REBALANCING"
    """
    被動調整模式
    - 分析現有投資組合效益
    - 識別風險和調整需求
    - 執行投資組合調整
    - 不搜尋新標的
    """

# 完全移除 OBSERVATION
```

#### 1.2 更新 `database/models.py`

```python
# Agent model 中
current_mode: Mapped[AgentMode] = mapped_column(
    String(50),
    default=AgentMode.TRADING.value,
    doc="當前交易模式 (TRADING 或 REBALANCING)"
)

# 移除 OBSERVATION 相關的默認值和驗證
```

#### 1.3 遷移現有數據

```sql
-- 遷移 OBSERVATION session 到 TRADING
UPDATE agent_sessions
SET mode = 'TRADING'
WHERE mode = 'OBSERVATION';

-- 驗證遷移
SELECT DISTINCT mode FROM agent_sessions;
```

---

### Phase 2：動態工具配置架構

#### 2.1 新增工具配置管理類

**文件：`src/trading/tool_config.py`** (新建)

```python
from enum import Enum
from dataclasses import dataclass
from common.enums import AgentMode

@dataclass
class ToolRequirements:
    """工具需求配置"""

    # OpenAI 內建工具
    include_web_search: bool
    include_code_interpreter: bool

    # 交易工具
    include_buy_sell_tools: bool        # 買賣工具
    include_portfolio_tools: bool       # 投資組合管理

    # Sub-agents
    include_technical_agent: bool
    include_fundamental_agent: bool
    include_sentiment_agent: bool
    include_risk_agent: bool

    # MCP Servers
    include_memory_mcp: bool
    include_casual_market_mcp: bool
    include_tavily_mcp: bool


class ToolConfig:
    """根據執行模式返回工具配置"""

    @staticmethod
    def get_requirements(mode: AgentMode) -> ToolRequirements:
        """
        返回指定模式的工具需求

        Args:
            mode: 執行模式

        Returns:
            ToolRequirements 實例
        """
        if mode == AgentMode.TRADING:
            return ToolRequirements(
                # OpenAI 工具 - 完整
                include_web_search=True,
                include_code_interpreter=True,

                # 交易工具 - 完整
                include_buy_sell_tools=True,
                include_portfolio_tools=True,

                # Sub-agents - 完整
                include_technical_agent=True,
                include_fundamental_agent=True,
                include_sentiment_agent=True,
                include_risk_agent=True,

                # MCP - 完整
                include_memory_mcp=True,
                include_casual_market_mcp=True,
                include_tavily_mcp=True,
            )

        elif mode == AgentMode.REBALANCING:
            return ToolRequirements(
                # OpenAI 工具 - 僅代碼解釋（用於數據分析）
                include_web_search=False,
                include_code_interpreter=True,

                # 交易工具 - 僅投資組合管理（無買賣）
                include_buy_sell_tools=False,
                include_portfolio_tools=True,

                # Sub-agents - 僅技術 + 風險（聚焦現有持股）
                include_technical_agent=True,
                include_fundamental_agent=False,
                include_sentiment_agent=False,
                include_risk_agent=True,

                # MCP - 簡化（無 tavily）
                include_memory_mcp=True,
                include_casual_market_mcp=True,
                include_tavily_mcp=False,
            )
```

#### 2.2 修改 `trading_agent.py` 初始化邏輯

```python
async def initialize(self, mode: AgentMode | None = None):
    """
    初始化 Agent，根據執行模式動態配置工具

    Args:
        mode: 執行模式 (TRADING 或 REBALANCING)
              如果不提供，使用 agent_config 的默認模式
    """
    if self.is_initialized:
        logger.debug(f"Agent {self.agent_id} already initialized, skipping...")
        return

    if not self.agent_config:
        raise AgentConfigurationError(
            f"Agent config must be set before initialization for {self.agent_id}"
        )

    try:
        # 確定執行模式
        execution_mode = mode or self.agent_config.current_mode or AgentMode.TRADING

        # 獲取工具需求
        tool_requirements = ToolConfig.get_requirements(execution_mode)

        # 1. 根據模式初始化 MCP 伺服器
        await self._setup_mcp_servers(tool_requirements)

        # 2. 初始化 OpenAI 工具
        self.openai_tools = self._setup_openai_tools(tool_requirements)

        # 3. 初始化交易工具
        self.trading_tools = self._setup_trading_tools(tool_requirements)

        # 4. 創建 LiteLLM 模型
        self.llm_model, self.extra_headers = await self._create_llm_model()

        # 5. 根據模式載入 Sub-agents
        self.subagent_tools = await self._load_subagents_as_tools(tool_requirements)

        # 6. 合併工具
        all_tools = self.trading_tools + self.subagent_tools

        # 7. 創建 OpenAI Agent
        mcp_servers_list = []
        if self.memory_mcp:
            mcp_servers_list.append(self.memory_mcp)
        if self.casual_market_mcp:
            mcp_servers_list.append(self.casual_market_mcp)
        if self.tavily_mcp:
            mcp_servers_list.append(self.tavily_mcp)

        self.agent = Agent(
            name=self.agent_id,
            model=self.llm_model,
            instructions=await self._build_instructions(
                self.agent_config.description,
                execution_mode
            ),
            tools=all_tools,
            mcp_servers=mcp_servers_list,
            model_settings=ModelSettings(
                include_usage=True,
            ),
        )

        self.is_initialized = True
        logger.info(
            f"✅ Agent initialized: {self.agent_id} "
            f"(mode: {execution_mode.value}, model: {self.agent_config.ai_model})"
        )

    except Exception as e:
        logger.error(f"Failed to initialize agent {self.agent_id}: {e}", exc_info=True)
        raise AgentInitializationError(f"Agent initialization failed: {str(e)}")
```

---

### Phase 3：記憶體工作流程深度整合

#### 3.1 執行流程與記憶體形成有機循環

```
[上一輪記憶] ──→ 構建指令 ──→ [執行分析] ──→ [決策]
    ↓                                        ↓
  記憶庫                                [交易/調整]
  (過往分析、                               ↓
   進場條件、                          [記錄決策]
   失敗原因)                               ↓
                                      [規劃下一步]
                                           ↓
                                      [存入記憶庫]
```

#### 3.2 實施示例

```python
async def run(self, mode: AgentMode | None = None) -> dict[str, Any]:
    """
    執行 Agent，整合記憶體工作流程

    流程：
    1. 加載上輪記憶 → 融入指令上下文
    2. 執行分析 → 決策 → 交易/調整
    3. 記錄決策和規劃下一步
    """
    # 1. 加載上輪記憶 → 融入指令
    memory = await self._load_execution_memory()
    enhanced_instructions = await self._build_instructions(
        self.agent_config.description,
        execution_mode,
        memory=memory
    )

    # 2. 執行分析 → 決策 → 交易
    analysis = await self._execute_analysis_phase(execution_mode)
    decision = await self._execute_decision_phase(execution_mode, analysis)
    result = await self._execute_trading_phase(decision)

    # 3. 記錄決策和規劃下一步
    await self._save_execution_memory(
        analysis=analysis,
        decision=decision,
        result=result,
        next_steps=await self._plan_next_steps(result)
    )

    return result
```

---

### Phase 4：文件修改清單

| 文件 | 操作 | 說明 |
|------|------|------|
| `common/enums.py` | 修改 | 移除 OBSERVATION，簡化為 2 模式 |
| `database/models.py` | 修改 | 更新 current_mode 默認值 |
| `trading/tool_config.py` | 新建 | 工具配置管理 |
| `trading/trading_agent.py` | 修改 | 動態初始化和記憶體整合 |
| `trading/tools/trading_tools.py` | 修改 | 根據模式返回工具 |
| `service/trading_service.py` | 修改 | 更新模式驗證邏輯 |
| `api/routers/agent_execution.py` | 修改 | 移除 OBSERVATION 支持 |
| `api/models.py` | 修改 | 更新執行模式選項 |

---

## 預期效果對比

### 重構前後指標對比

| 指標 | 當前 | 重構後 | 改進 |
|------|------|--------|------|
| 支持的模式數 | 3 個 | 2 個 | 簡化 33% |
| 代碼重複率 | ~40% | ~12% | 減少 70% |
| 全量加載工具 | 是 | 否 | 動態加載 |
| MCP 伺服器數 | 3 (全量) | 動態 (2-3) | 按需加載 |
| Sub-agents 數 | 4 (全量) | 動態 (2-4) | 按需加載 |
| 記憶體深度整合 | 否 | 是 | 完整集成 |
| 代碼改動量 | - | 大 | - |
| API 兼容性 | 100% | 90% | 需適配 |
| 升級難度 | - | 中等 | - |
| 時間投入 | - | 13-18 小時 | - |

---

## 風險評估與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| 數據遺失 | 高 | 執行遷移前完整備份數據庫 |
| 前端兼容破壞 | 中 | 全面測試各前端端點，漸進遷移 |
| 性能下降 | 中 | 動態加載應優化，監控關鍵指標 |
| 測試覆蓋不足 | 中 | 新增 15+ 集成測試，覆蓋各模式 |
| 用戶困惑 | 中 | 充分溝通、文檔更新、UI 清晰提示 |

---

## 成功指標

✅ **架構層面**
- 只支持 TRADING 和 REBALANCING 兩種模式
- 工具配置完全動態化
- 模式初始化邏輯清晰

✅ **功能層面**
- TRADING 模式包含完整的分析→決策→執行流程
- REBALANCING 模式聚焦於現有持股分析和被動調整
- 記憶庫與執行流程深度集成

✅ **代碼品質**
- 代碼重複減少 >25%（達到 12-15%）
- 測試覆蓋率 >80%
- 文檔完整和最新

✅ **用戶體驗**
- 前端 UI 簡化清晰
- 執行結果更易理解
- 記憶體功能透明可見

---

## 實施檢查清單

### 通用檢查項

- [ ] 備份現有代碼和數據庫
- [ ] 建立代碼分支
- [ ] 編寫詳細的測試計劃
- [ ] 準備回滾方案
- [ ] 與團隊同步需求和時間表

### 數據遷移

- [ ] 運行遷移腳本：OBSERVATION → TRADING
- [ ] 驗證數據完整性
- [ ] 備份原始數據

### 測試

- [ ] 單元測試：工具配置邏輯
- [ ] 集成測試：TRADING 模式完整流程
- [ ] 集成測試：REBALANCING 模式完整流程
- [ ] 記憶體工作流程測試
- [ ] 前端兼容性測試

### 前端調整

- [ ] 移除 OBSERVATION 按鈕
- [ ] 更新模式選擇下拉菜單
- [ ] 更新 API 調用邏輯
- [ ] 更新文檔和幫助文本

---

## 時間估算

| 階段 | 任務 | 時間 |
|------|------|------|
| Phase 1 | 移除 OBSERVATION、遷移數據 | 2-3 小時 |
| Phase 2 | 動態工具配置實現 | 4-6 小時 |
| Phase 3 | 記憶體工作流程集成 | 3-4 小時 |
| Phase 4 | 測試和文檔 | 4-5 小時 |
| **合計** | | **13-18 小時** |

---

## 決策檢查點

**檢查點 1：模式確認**
- ✓ OBSERVATION 完全移除
- ✓ TRADING 為主動搜尋模式
- ✓ REBALANCING 為被動調整模式

**檢查點 2：工具配置**
- ✓ 工具根據模式動態加載
- ✓ 性能提升（減少不必要的初始化）

**檢查點 3：記憶體整合**
- ✓ 上一輪執行記憶自動融入指令
- ✓ 下一步行動規劃存入知識庫
- ✓ 形成有機循環

**檢查點 4：向後兼容性**
- ✗ 不考慮向後兼容（用戶要求）
- ✓ 明確的遷移路徑

---

**文檔版本：** 1.0 (完全重構版)
**最後更新：** 2025-10-30
**狀態：** 待執行
