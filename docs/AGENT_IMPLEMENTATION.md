# Agent 系統實作規格

**版本**: 3.2
**日期**: 2025-10-10
**相關設計**: SYSTEM_DESIGN.md
**基於**: OpenAI Agents SDK + Prompt-Based Strategy Management

> **⚠️ 重要架構變更 (v3.2)**
>
> - **移除**: `src/agents/integrations/mcp_client.py` (包裝層已移除)
> - **移動**: `database_service.py` → `src/database/agent_database_service.py`
> - **改用**: Trading Agent 直接透過 OpenAI SDK 的 `mcp_servers` 參數連接 Casual Market MCP
> - **簡化**: 移除中間包裝層,降低複雜度,直接使用 MCP protocol

---

## 📋 概述

本文檔定義 CasualTrader AI 股票交易模擬器中 Agent 系統的完整實作規格，採用 **Prompt 驅動** 的 Agent 架構：

1. **TradingAgent 主體** - 基於 prompt 指令的智能交易Agent
2. **動態策略架構** - 四種自主交易模式與策略演化系統
3. **豐富分析工具** - 基本面分析、技術分析、風險評估等專門化工具
4. **OpenAI Hosted Tools** - WebSearchTool、CodeInterpreterTool等內建工具
5. **CasualMarket MCP 整合** - 台股即時數據和交易模擬
6. **策略變更記錄系統** - 追蹤Agent策略演進歷史
7. **前端配置介面** - 簡潔的Agent創建和監控界面

### 核心設計理念

- **Prompt 驅動**: 透過自然語言描述投資偏好和策略調整依據
- **自主模式選擇**: Agent 根據市場條件自主選擇適當的交易模式
- **工具豐富**: 提供全面的市場分析和交易執行工具
- **策略自主演化**: 基於績效表現和設定條件自動調整策略
- **完整記錄追蹤**: 記錄所有策略變更的時點、原因和效果
- **用戶完全控制**: 用戶透過前端介面設定投資個性和調整依據

### 台股交易時間考量

- **交易時間**: 週一至週五 09:00-13:30
- **模式選擇**: Agent 根據交易時間、市場條件和策略需求自主選擇
- **交易限制**: 僅在開盤時間執行實際買賣操作
- **非交易時間**: 進行觀察分析和策略檢討

---

## 🔌 MCP 整合架構 (v3.2 更新)

### 整合方式說明

CasualTrader v3.2 採用**直接 MCP 整合**,Trading Agent 透過 OpenAI Agent SDK 的 `mcp_servers` 參數直接連接 Casual Market MCP server,移除了中間包裝層以降低複雜度。

### 配置方式

```python
from agents import Agent

# 創建 Trading Agent 時傳入 MCP servers 配置
trading_agent = Agent(
    name="Stock Trading Agent",
    instructions="你是一個專業的台股交易AI Agent...",
    tools=[...],  # FunctionTool 等自定義工具
    mcp_servers={
        "casual-market": {
            "command": "uvx",
            "args": ["casual-market-mcp"]
        }
    }
)
```

### 架構變更對比

**舊架構 (v3.1及之前):**

```
TradingAgent → mcp_client.py wrapper → Casual Market MCP
                      ↓
               yfinance fallback
```

**新架構 (v3.2+):**

```
TradingAgent → OpenAI SDK (mcp_servers) → Casual Market MCP (direct)
```

### 遷移指南

**1. 移除 mcp_client import:**

```python
# ❌ 舊版
from src.agents.integrations.mcp_client import get_mcp_client
mcp_client = get_mcp_client()
await mcp_client.get_stock_price("2330")

# ✅ 新版: MCP tools 在 Agent 創建時自動可用
# 工具直接透過 Agent SDK 調用,無需手動 import
```

**2. database_service 導入路徑變更:**

```python
# ❌ 舊版
from src.agents.integrations.database_service import AgentDatabaseService

# ✅ 新版
from src.database.agent_database_service import AgentDatabaseService
# 或
from src.database import AgentDatabaseService
```

---

## 💾 資料庫管理

### Database Migration 系統

CasualTrader 使用 Python 的異步 SQLAlchemy 進行資料庫管理，並提供完整的 migration 系統來管理資料庫 schema 變更。

#### 快速開始

```bash
# 查看 Migration 狀態
./scripts/db_migrate.sh status

# 執行所有待執行的 Migrations
./scripts/db_migrate.sh up

# 執行到特定版本
./scripts/db_migrate.sh up 1.2.0

# 回滾到特定版本
./scripts/db_migrate.sh down 1.0.0

# 重置資料庫 (危險操作!)
./scripts/db_migrate.sh reset
```

#### Migration 版本

**v1.0.0 - Initial Schema**

檔案: `backend/src/database/migrations.py` - `InitialSchemaMigration`

功能:

- 創建所有核心資料表 (agents, agent_sessions, agent_holdings, transactions, etc.)
- 創建資料庫視圖 (agent_overview, agent_latest_performance)
- 創建觸發器 (自動更新 updated_at 時間戳)

**v1.1.0 - Performance Indexes**

檔案: `backend/src/database/migrations.py` - `AddPerformanceIndexesMigration`

功能:

- 新增複合索引以優化查詢效能
- idx_transactions_agent_ticker, idx_performance_agent_date, etc.

**v1.2.0 - AI Model Configuration**

檔案: `backend/src/database/migrations.py` - `AddAIModelConfigMigration`

功能:

- 創建 ai_model_configs 表
- 插入 AI 模型種子資料 (9 個模型)
- 支援 LiteLLM 多模型整合

資料表結構:

```sql
CREATE TABLE ai_model_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_key TEXT UNIQUE NOT NULL,           -- 模型唯一識別碼
    display_name TEXT NOT NULL,               -- 顯示名稱
    provider TEXT NOT NULL,                   -- 提供商
    group_name TEXT NOT NULL,                 -- 分組名稱
    model_type TEXT NOT NULL,                 -- openai/litellm
    litellm_prefix TEXT,                      -- LiteLLM 前綴
    full_model_name TEXT NOT NULL,            -- 完整模型名稱
    is_enabled BOOLEAN DEFAULT TRUE,          -- 是否啟用
    requires_api_key BOOLEAN DEFAULT TRUE,    -- 是否需要 API key
    api_key_env_var TEXT,                     -- 環境變數名稱
    api_base_url TEXT,                        -- 自訂 API URL
    max_tokens INTEGER,                       -- 最大 token 數
    cost_per_1k_tokens NUMERIC(10,6),        -- 每 1K tokens 成本
    display_order INTEGER DEFAULT 999,        -- 顯示順序
    description TEXT,                         -- 描述
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 使用場景

**首次部署**:

```bash
# 1. 查看狀態
./scripts/db_migrate.sh status

# 2. 執行所有 migrations
./scripts/db_migrate.sh up

# 3. 驗證結果
./scripts/db_migrate.sh status
```

**生產環境**:

```bash
# 1. 備份現有資料庫
cp casualtrader.db casualtrader.db.backup

# 2. 查看待執行的 migrations
./scripts/db_migrate.sh status

# 3. 執行 migrations
./scripts/db_migrate.sh up

# 4. 驗證
./scripts/db_migrate.sh status
```

#### 驗證 Migration

**檢查資料表**:

```bash
sqlite3 casualtrader.db ".tables"
```

預期輸出:

```
agent_config_cache    agent_performance     market_data_cache
agent_holdings        agent_sessions        schema_migrations
agent_overview        agents                strategy_changes
agent_latest_performance  ai_model_configs  transactions
```

**檢查 AI 模型種子資料**:

```bash
sqlite3 casualtrader.db "SELECT model_key, display_name, provider FROM ai_model_configs ORDER BY display_order;"
```

### AI 模型配置管理

#### 概覽

本系統整合了分散在前後端的 AI 模型配置，提供單一資料來源 (Single Source of Truth) 的統一管理方案：

- **後端**: 資料庫驅動的模型配置，支援 OpenAI 原生模型和 LiteLLM 代理模型
- **前端**: 動態從 API 獲取模型列表，自動分組顯示
- **API**: RESTful 端點提供模型 CRUD 操作

#### 核心特性

**1. 資料庫驅動配置**

- 所有模型配置儲存在 `ai_model_configs` 表
- 支援模型啟用/停用狀態管理
- 包含完整的模型元數據 (tokens, 成本, 描述等)
- 透過 DB migration 管理 schema 和 seed data

**2. LiteLLM 整合**

根據 [OpenAI Agents Python SDK](https://openai.github.io/openai-agents-python/models/litellm/) 官方文檔整合：

```python
from agents.extensions.models.litellm_model import LitellmModel

# 使用 LiteLLM 模型
model = LitellmModel(name="gemini/gemini-2.5-pro-preview-05-06")
```

**支援的模型類型**:

- **OpenAI Native** (`model_type: openai`): GPT-5 Mini, GPT-4o Mini, GPT-4.1 Mini
- **LiteLLM Proxy** (`model_type: litellm`): Gemini, Claude, DeepSeek, Grok

**3. 前端動態加載**

- 應用啟動時自動加載模型列表
- 按 `group_name` 分組顯示 (OpenAI, Google Gemini, Anthropic 等)
- Svelte 5 Runes 響應式狀態管理
- 下拉選單自動適配最新模型列表

#### 種子資料

系統預設包含 5 個 AI 模型配置 (`backend/src/database/seed_ai_models.py`):

**OpenAI Models**:

1. **GPT-5 Mini** (`gpt-5-mini`) - Max Tokens: 128K, Cost: $0.01/1K tokens
2. **GPT-4o Mini** (`gpt-4o-mini`) - Max Tokens: 128K, Cost: $0.003/1K tokens
3. **GPT-4.1 Mini** (`gpt-4.1-mini`) - Max Tokens: 128K, Cost: $0.008/1K tokens

**Google Gemini Models (via LiteLLM)**:

4. **Gemini 2.5 Pro** (`gemini-2.5-pro`) - Full Name: `gemini/gemini-2.5-pro-preview-05-06`, Max Tokens: 1M
5. **Gemini 2.0 Flash** (`gemini-2.0-flash`) - Full Name: `gemini/gemini-2.0-flash`, Max Tokens: 1M

#### API 端點

**獲取所有可用模型 (已啟用)**:

```bash
GET /api/models/available
```

Response:

```json
{
  "total": 5,
  "models": [
    {
      "model_key": "gpt-5-mini",
      "display_name": "GPT-5 Mini",
      "provider": "OpenAI",
      "group_name": "OpenAI",
      "model_type": "openai",
      "full_model_name": "gpt-5-mini",
      "max_tokens": 128000,
      "cost_per_1k_tokens": 0.01,
      "description": "Most capable OpenAI model for complex tasks"
    }
  ]
}
```

**獲取分組模型列表**:

```bash
GET /api/models/available/grouped
```

**獲取特定模型**:

```bash
GET /api/models/{model_key}
```

#### Agent 配置載入

**基礎 Agent**:

`backend/src/agents/core/base_agent.py` 中的 `_setup_openai_agent()` 方法會根據 `model_type` 自動選擇：

- **OpenAI Native**: 直接使用 model string
- **LiteLLM**: 創建 `LitellmModel` 實例

```python
async def _setup_openai_agent(self) -> None:
    model_config = await self._get_model_config(self.config.model)

    if model_config and model_config.get("model_type") == "litellm":
        # LiteLLM 模型
        model_instance = LitellmModel(name=model_config["full_model_name"])
        self._openai_agent = Agent(model=model_instance, ...)
    else:
        # OpenAI 原生模型
        self._openai_agent = Agent(model=self.config.model, ...)
```

**Persistent Agent**:

`backend/src/agents/integrations/persistent_agent.py` 覆寫 `_get_model_config()` 方法，從資料庫獲取配置：

```python
async def _get_model_config(self, model_key: str) -> dict[str, Any] | None:
    model_config = await self.db_service.get_ai_model_config(model_key)
    return model_config if model_config else None
```

#### 新增模型

編輯 `backend/src/database/seed_ai_models.py`，在 `SEED_AI_MODELS` 列表中添加新模型配置：

```python
{
    "model_key": "claude-opus-4",
    "display_name": "Claude Opus 4",
    "provider": "Anthropic",
    "group_name": "Anthropic",
    "model_type": ModelType.LITELLM,
    "litellm_prefix": "anthropic/",
    "full_model_name": "anthropic/claude-opus-4",
    "is_enabled": True,
    "requires_api_key": True,
    "api_key_env_var": "ANTHROPIC_API_KEY",
    "max_tokens": 200000,
    "cost_per_1k_tokens": Decimal("0.015"),
    "display_order": 4,
    "description": "Anthropic's most capable model",
}
```

然後重置資料庫: `./scripts/db_migrate.sh reset`

#### 環境變數配置

確保設定相應的 API keys:

```bash
# .env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
```

---

## 🤖 TradingAgent 主體架構

### 設計理念

TradingAgent 採用 **Prompt 驅動** 的設計，通過豐富的分析工具和明確的投資指令來做出交易決策。Agent 的行為模式完全由用戶透過自然語言設定的投資偏好和策略調整依據控制。

### 簡化的 Agent 架構

```python
from agents import Agent, WebSearchTool, CodeInterpreterTool

def create_trading_agent(agent_config: AgentConfig) -> Agent:
    """創建基於用戶配置的交易Agent"""

    # 根據用戶輸入生成完整的投資指令
    instructions = generate_trading_instructions(agent_config)

    trading_agent = Agent(
        name=agent_config.name,
        instructions=instructions,
        tools=[
            # ========================================
            # 專門化分析工具（自主型 Agent as Tool）
            # ========================================
            # 每個工具本身就是一個完整的 Agent，具備：
            # - 自主分析決策能力
            # - 內建 WebSearchTool（搜尋最新資訊）
            # - 內建 CodeInterpreterTool（執行進階計算）
            # - 明確的成本控制準則
            # - 標準化的輸出格式

            fundamental_agent.as_tool(
                tool_name="fundamental_analysis",
                tool_description="Comprehensive fundamental analysis including financial statements, ratios, valuation, and growth potential. Has access to web search and code interpreter for advanced DCF models."
            ),
            technical_agent.as_tool(
                tool_name="technical_analysis",
                tool_description="Technical analysis with chart patterns, indicators (RSI, MACD, MA), trend analysis, and support/resistance levels. Can execute custom indicator calculations and backtests."
            ),
            risk_agent.as_tool(
                tool_name="risk_assessment",
                tool_description="Portfolio risk evaluation including concentration risk, VaR calculations, stress testing, and position sizing recommendations. Capable of Monte Carlo simulations."
            ),
            sentiment_agent.as_tool(
                tool_name="market_sentiment",
                tool_description="Market sentiment analysis from news, social media, foreign investment flows, and fear/greed indicators. Provides timing recommendations based on sentiment extremes."
            ),

            # ========================================
            # OpenAI Hosted Tools（TradingAgent 直接使用）
            # ========================================
            # 注意：專門化 Agent 內部也有這些工具，但 TradingAgent 可以直接使用

            WebSearchTool(),           # 搜尋市場新聞、政策變化、突發事件
            CodeInterpreterTool(),     # 執行投資組合優化、複雜計算、數據分析

            # ========================================
            # CasualMarket MCP Tools（台股專業數據）
            # ========================================

            # 核心交易工具
            get_taiwan_stock_price,
            buy_taiwan_stock,
            sell_taiwan_stock,

            # 基本面數據工具
            get_company_fundamentals,
            get_company_income_statement,
            get_company_balance_sheet,
            get_company_monthly_revenue,
            get_stock_valuation_ratios,
            get_company_dividend,

            # 市場數據工具
            get_market_index_info,
            get_stock_daily_trading,
            get_real_time_trading_stats,
            get_foreign_investment_by_industry,
            get_top_foreign_holdings,

            # 市場狀態工具
            check_taiwan_trading_day,
            get_taiwan_holiday_info,

            # ========================================
            # 交易驗證與投資組合查詢工具
            # ========================================

            check_trading_hours,           # 檢查是否在交易時間
            get_current_holdings,          # 獲取當前持股
            get_available_cash,            # 獲取可用資金
            validate_trade_parameters,     # 驗證交易參數
            get_portfolio_summary,         # 獲取投資組合摘要

            # ========================================
            # 策略演化記錄工具
            # ========================================

            record_strategy_change,        # 記錄策略變更
        ],
        model=agent_config.ai_model or "gpt-4o",  # 支援多種 AI 模型
        max_turns=agent_config.max_turns or 30
    )

    return trading_agent

def generate_trading_instructions(config: AgentConfig) -> str:
    """根據用戶配置生成Agent指令"""
  # embed structured auto-adjust settings into the prompt so the Agent
  # can reason about when and how to propose/apply strategy changes.
  # auto_adjust is required and defaults to autonomous behavior.
  # Expect config.auto_adjust to be provided (from frontend). If missing,
  # fall back to safe defaults that enable fully-autonomous adjustments.
  auto_adjust = getattr(config, "auto_adjust", None) or {
    "triggers": "連續三天虧損超過2% ; 單日跌幅超過3% ; 最大回撤超過10%",
    "auto_apply": True,
  }

  # Provide a short, clear template that includes both human-readable
  # guidance and a machine-friendly settings summary the Agent can refer to.
  return f"""
你是 {config.name}，一個智能台灣股票交易代理人。

核心任務：
{config.description}

投資偏好：
{config.investment_preferences}

策略調整標準（使用者提供）：
{config.strategy_adjustment_criteria}

自動調整設定（結構化 - 代理人自主）：
- 觸發條件（自由文字範例/優先順序）：{auto_adjust.get('triggers')}
- 自動套用：{bool(auto_adjust.get('auto_apply', True))}

交易限制：
- 可用資金：NT${config.initial_funds:,}
- 最大單筆部位：每檔股票 {config.max_position_size or 5}%
- 台灣股市交易時間：09:00-13:30（週一至週五）
- 最小交易單位：1000 股

策略演化：
當你的績效或市場條件建議進行策略調整時，你應該：
1. 評估觸發條件是否符合上述使用者配置的觸發條件。
2. 生成清晰的變更提案和簡要說明。

始終使變更與你的核心投資偏好保持一致。

{config.additional_instructions or ""}
"""
```

### 模式選擇邏輯

Agent 會根據以下因素自主選擇適當的模式：

- 台股交易時間（09:00-13:30）
- 當前市場條件和機會
- 投資組合狀況和風險水平
- 設定的策略調整依據
- 近期績效表現

---

## 🔄 策略演化與自主調整系統

### 策略演化設計理念

Agent 採用 **基於 Prompt 的策略演化**,透過自主學習和用戶設定的調整依據來優化投資策略:

1. **用戶定義調整依據**: 創建 Agent 時設定策略調整的觸發條件
2. **Agent 自主判斷**: 根據績效和市場條件自主決定是否調整
3. **完整變更記錄**: 記錄所有策略變更的原因、內容和效果
4. **透明可追溯**: 用戶可查看完整的策略演進歷史

### 策略調整機制詳解

#### 1. 用戶定義的調整依據

用戶在創建 Agent 時設定策略調整的觸發條件:

```text
範例調整依據:
"當連續三天虧損超過2%時,轉為保守觀察模式;
 當發現技術突破信號且基本面支撐時,可以增加部位;
 每週檢討一次績效,若月報酬率低於大盤2%以上,考慮調整選股邏輯。"
```

#### 2. 策略演化實際範例

**觸發條件**: 連續三天虧損超過2%

**策略調整內容**:

```text
DEFENSIVE ADJUSTMENT ACTIVATED:
- 降低新增部位的風險暴露
- 優先選擇低波動率、高股息的防禦性股票
- 增加現金部位至15-20%
- 暫停成長股投資,專注價值股
- 加強停損執行,單股最大虧損限制在5%
- 每日檢討持股表現,及時汰弱留強
```

**Agent 說明**:

```text
"基於近期連續虧損的情況,我判斷當前市場環境不利於積極投資策略。
根據您設定的調整依據,我啟動防禦模式來保護資本。
主要調整包括:降低風險暴露、增加現金部位、專注防禦性標的。
預期這些調整能減少波動、保護本金,待市場回穩後再恢復積極策略。"
```

### 策略演化的優勢

1. **高度個人化**: 每個 Agent 的策略調整依據完全由用戶定義
2. **自主性**: Agent 可以根據市場變化和績效表現自主調整
3. **透明性**: 所有策略變更都有詳細記錄和說明
4. **可追溯性**: 用戶可以查看策略演進歷史和效果分析
5. **靈活性**: 策略調整不受複雜的程式邏輯限制

---

## 📊 策略變更記錄系統

### 資料模型設計

所有策略變更都會被詳細記錄,包括變更原因、時點、內容和績效影響,確保投資決策的可追溯性和透明度。

### 策略變更資料模型

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class StrategyChange(BaseModel):
    id: str
    agent_id: str
    timestamp: datetime

    # 變更觸發資訊
    trigger_reason: str  # 觸發策略變更的具體原因
    change_type: str     # 'auto' | 'manual' | 'performance_driven'

    # 策略內容變更
    old_strategy: Optional[str] = None  # 變更前的完整策略
    new_strategy: str                   # 變更後的完整策略
    change_summary: str                 # 變更重點摘要

    # 績效背景資料
    performance_at_change: Optional[Dict] = None  # 觸發變更時的績效狀況

    # Agent 自主說明
    agent_explanation: Optional[str] = None  # Agent 對變更的解釋
```

### 自動策略變更機制

```python
@function_tool
async def record_strategy_change(
    agent_id: str,
    trigger_reason: str,
    new_strategy_addition: str,
    change_summary: str,
    agent_explanation: str
) -> dict:
    """Agent 記錄策略變更的工具"""

    # 獲取當前策略和績效
    current_agent = await get_agent(agent_id)
    current_performance = await get_current_performance(agent_id)

    # 創建策略變更記錄
    change = StrategyChange(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        timestamp=datetime.now(),
        trigger_reason=trigger_reason,
        change_type="auto",
        old_strategy=current_agent.instructions,
        new_strategy=current_agent.instructions + "\n\n" + new_strategy_addition,
        change_summary=change_summary,
        performance_at_change=current_performance,
        agent_explanation=agent_explanation
    )

    # 儲存變更記錄
    await strategy_change_service.save(change)

    # 更新 Agent 指令
    current_agent.instructions = change.new_strategy
    await update_agent(current_agent)

    return {
        "success": True,
        "change_id": change.id,
        "message": "Strategy change recorded successfully"
    }

# Agent 使用範例
async def agent_strategy_adjustment_example():
    """Agent 如何使用策略變更工具的範例"""

    # 當Agent發現需要調整策略時
    trigger_reason = "連續三天虧損超過2%，市場波動加劇"
    new_strategy = """
RISK ADJUSTMENT - DEFENSIVE MODE ACTIVATED:
- 降低單筆最大投資比例至3%
- 優先選擇低波動率股票
- 增加現金部位至20%
- 暫停成長股投資，專注價值股
- 每日檢討風險暴露，適時減倉
"""

    change_summary = "啟動防禦模式：降低風險暴露，增加現金部位"
    explanation = """
基於近期績效表現和市場環境變化，我決定調整為更保守的投資策略。
主要考量：
1. 連續虧損顯示當前策略與市場環境不匹配
2. 市場波動加劇，需要降低風險暴露
3. 保護資本是當前首要任務
4. 待市場穩定後再恢復積極策略
"""

    # 記錄策略變更
    result = await record_strategy_change(
        agent_id="agent_123",
        trigger_reason=trigger_reason,
        new_strategy_addition=new_strategy,
        change_summary=change_summary,
        agent_explanation=explanation
    )
```

---

## 🎨 前端 Agent 配置介面

### Agent 創建表單設計

```typescript
interface AgentCreationForm {
  // 基本資訊
  name: string;
  description: string;
  ai_model: string;                      // AI 模型選擇（下拉選單）
  initial_funds: number;

  // 核心投資設定（開放式文字輸入）
  investment_preferences: string;        // 基本投資偏好
  strategy_adjustment_criteria: string;  // 投資策略調整依據

  // 自動調整設定（前端表單可讓使用者設定）
  auto_adjust?: {
    enabled?: boolean;              // 是否啟用自動調整（預設 true）
    triggers?: string;              // 自由文字描述的觸發規則（可多條用分號分隔）
  };

  // 可選的進階設定
  max_position_size?: number;
  excluded_tickers?: string[];
  additional_instructions?: string;
}

const AgentCreationForm = () => {
  return (
    <form className="agent-creation-form">
      {/* 基本資訊區塊 */}
      <div className="basic-info-section">
        <h3>基本資訊</h3>
        <input
          placeholder="Agent 名稱"
          className="form-input"
        />
        <textarea
          placeholder="簡短描述這個Agent的投資目標"
          className="form-textarea"
          rows={2}
        />

        {/* AI 模型選擇 */}
        <div className="input-group">
          <label>AI 模型</label>
          <select className="form-select" defaultValue="gpt-4o">
            <optgroup label="OpenAI">
              <option value="gpt-4o">GPT-4o (推薦)</option>
              <option value="gpt-4o-mini">GPT-4o Mini (成本優化)</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
            </optgroup>
            <optgroup label="Anthropic Claude">
              <option value="claude-sonnet-4.5">Claude Sonnet 4.5</option>
              <option value="claude-opus-4">Claude Opus 4</option>
            </optgroup>
            <optgroup label="Google Gemini">
              <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
              <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
            </optgroup>
            <optgroup label="其他">
              <option value="deepseek-v3">DeepSeek V3</option>
              <option value="grok-2">Grok 2</option>
            </optgroup>
          </select>
          <small className="form-hint">
            選擇用於投資決策的 AI 模型，不同模型具有不同的推理風格與成本
          </small>
        </div>

        <input
          type="number"
          placeholder="初始資金 (TWD)"
          className="form-input"
        />
      </div>

      {/* 投資策略設定區塊 */}
      <div className="strategy-section">
        <h3>投資策略設定</h3>

        <div className="input-group">
          <label>基本投資偏好</label>
          <textarea
            placeholder="請詳細描述您的投資風格、偏好的股票類型、風險承受度等。

範例：
'我偏好穩健成長的大型股，主要關注半導體和金融股，風險承受度中等，希望長期持有優質企業，避免過度頻繁交易。'"
            className="form-textarea strategy-input"
            rows={6}
          />
        </div>

        <div className="input-group">
          <label>投資策略調整依據</label>
          <textarea
            placeholder="說明何時以及如何調整投資策略。

範例：
'當連續三天虧損超過2%時，轉為保守觀察模式；當發現技術突破信號且基本面支撐時，可以增加部位；每週檢討一次績效，若月報酬率低於大盤2%以上，考慮調整選股邏輯。'"
            className="form-textarea strategy-input"
            rows={6}
          />
        </div>

        <div className="input-group">
          <label>自動調整設定 (選填)</label>
          <div className="form-row">
            <label>
              <input type="checkbox" name="auto_adjust.enabled" defaultChecked /> 啟用自動調整
            </label>
          </div>

          <textarea
            name="auto_adjust.triggers"
            placeholder="輸入觸發規則，使用分號(;)分隔，例如：連續3天虧損>2%; 單日跌幅>3%"
            className="form-textarea"
            rows={3}
          />
        </div>
      </div>

      {/* 進階設定區塊 */}
      <div className="advanced-settings">
        <h3>進階設定（可選）</h3>
        <input
          type="number"
          placeholder="最大單筆投資比例 (%, 預設5%)"
          className="form-input"
        />
        <input
          placeholder="排除股票代號 (逗號分隔，如: 2498,2328)"
          className="form-input"
        />
        <textarea
          placeholder="其他特殊指令或限制"
          className="form-textarea"
          rows={3}
        />
      </div>

      {/* 預覽區塊 */}
      <div className="preview-section">
        <h3>Agent 指令預覽</h3>
        <div className="instruction-preview">
          <pre>{generateInstructionPreview(formData)}</pre>
        </div>
      </div>

      <button type="submit" className="create-agent-btn">
        創建 Trading Agent
      </button>
    </form>
  );
};
```

### 策略變更歷史查看介面

```typescript
interface StrategyChange {
  id: string;
  timestamp: string;
  trigger_reason: string;
  change_type: 'auto' | 'manual' | 'performance_driven';
  change_summary: string;
  performance_at_change?: {
    total_return: number;
    win_rate: number;
    drawdown: number;
  };
  agent_explanation?: string;
}

const StrategyHistoryView = ({ agentId }: { agentId: string }) => {
  const [changes, setChanges] = useState<StrategyChange[]>([]);
  const [selectedChange, setSelectedChange] = useState<StrategyChange | null>(null);

  return (
    <div className="strategy-history-container">
      <div className="history-header">
        <h3>策略變更歷史</h3>
        <div className="filter-controls">
          <select>
            <option value="all">所有變更</option>
            <option value="auto">自動調整</option>
            <option value="manual">手動變更</option>
            <option value="performance_driven">績效驅動</option>
          </select>
        </div>
      </div>

      {/* 時間線視圖 */}
      <div className="timeline-container">
        {changes.map((change, index) => (
          <div key={change.id} className="timeline-item">
            <div className="timeline-marker">
              <span className={`change-type-badge ${change.change_type}`}>
                {change.change_type === 'auto' ? '自動' :
                 change.change_type === 'manual' ? '手動' : '績效'}
              </span>
            </div>

            <div className="timeline-content">
              <div className="change-header">
                <span className="timestamp">
                  {new Date(change.timestamp).toLocaleString('zh-TW')}
                </span>
                <button
                  onClick={() => setSelectedChange(change)}
                  className="view-details-btn"
                >
                  查看詳情
                </button>
              </div>

              <h4 className="trigger-reason">{change.trigger_reason}</h4>
              <p className="change-summary">{change.change_summary}</p>

              {change.performance_at_change && (
                <div className="performance-snapshot">
                  <div className="metric">
                    <span className="label">總報酬:</span>
                    <span className={`value ${change.performance_at_change.total_return >= 0 ? 'positive' : 'negative'}`}>
                      {change.performance_at_change.total_return.toFixed(2)}%
                    </span>
                  </div>
                  <div className="metric">
                    <span className="label">勝率:</span>
                    <span className="value">{change.performance_at_change.win_rate.toFixed(1)}%</span>
                  </div>
                  <div className="metric">
                    <span className="label">回撤:</span>
                    <span className="value negative">{change.performance_at_change.drawdown.toFixed(2)}%</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 策略變更詳情彈窗 */}
      {selectedChange && (
        <StrategyChangeModal
          change={selectedChange}
          onClose={() => setSelectedChange(null)}
        />
      )}
    </div>
  );
};
```

---

## 📊 API 端點設計

### 策略變更 API

```python
from fastapi import APIRouter, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/api/agents", tags=["strategy"])

@router.post("/{agent_id}/strategy-changes")
async def record_strategy_change(
    agent_id: str,
    change_data: StrategyChangeRequest
) -> StrategyChange:
    """記錄Agent策略變更"""
    try:
        change = await strategy_service.record_change(agent_id, change_data)
        return change
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/strategy-changes")
async def get_strategy_changes(
    agent_id: str,
    limit: int = 50,
    offset: int = 0,
    change_type: Optional[str] = None
) -> List[StrategyChange]:
    """獲取Agent策略變更歷史"""
    return await strategy_service.get_changes(
        agent_id, limit, offset, change_type
    )

@router.get("/{agent_id}/strategy-changes/latest")
async def get_latest_strategy(agent_id: str) -> StrategyChange:
    """獲取最新策略配置"""
    change = await strategy_service.get_latest_change(agent_id)
    if not change:
        raise HTTPException(status_code=404, detail="No strategy found")
    return change
```

---

## ⚙️ 配置管理

### 基於 SQLite 的配置持久化

**AgentConfig** 表結構:

- agent_id, config_key, config_value
- 支援動態配置更新
- 預設配置透過環境變數設定

**常用配置項目**:

- `max_turns`: Agent 最大執行回合數 (預設: 30)
- `execution_timeout`: 執行超時時間 (預設: 300秒)
- `trace_retention_days`: 內部執行日誌保留天數 (預設: 30天)

### 配置操作

**載入順序**:

1. 環境變數預設值
2. SQLite 中的全域設定
3. 個別 Agent 設定 (優先順序最高)

**配置更新**:

- 透過 API 動態更新配置
- 立即生效，無需重啟服務
- 設定變更記錄到操作日誌

---

## 📊 執行追蹤

CasualTrader 整合兩種互補的執行追蹤機制:

### 1. OpenAI Agents SDK Trace (自動啟用)

**用途**: 即時可視化和調試 Agent 執行流程

- **位置**: 上傳到 OpenAI Dashboard (https://platform.openai.com/traces)
- **啟用方式**: 使用 `trace()` context manager 自動記錄
- **適用場景**: 開發、調試、問題排查
- **特點**:
  - 自動記錄所有 `Runner.run()` 調用
  - 可視化工具調用和 LLM 響應
  - 預設使用 OpenAI API key (無需額外配置)
  - 使用 `group_id` 將多個 run 關聯為同一工作流

**實作位置**: `backend/src/agents/core/base_agent.py:238`

```python
# 使用 OpenAI Agents SDK trace context manager 包裹執行過程
trace_name = f"{self.config.name}-{execution_mode.value}"
with trace(trace_name, group_id=self.agent_id):
    # Agent 執行邏輯
```

### 2. 內部執行日誌 (trace_data)

**用途**: 業務分析、績效追蹤、審計記錄

- **位置**: 存儲在資料庫 `AgentExecutionResult.trace_data` 欄位
- **記錄內容**:
  - 執行步驟詳細日誌 (turn_start, turn_end, tool_call, agent_decision)
  - 會話摘要 (session_summary)
  - 執行統計資訊
- **適用場景**: 生產環境、長期數據分析、合規審計
- **特點**:
  - 持久化存儲
  - 可查詢和分析
  - 包含業務相關的上下文資訊

**實作位置**: `backend/src/agents/core/agent_session.py:386`

**查詢功能**:

- 按 Agent ID 查詢歷史記錄
- 按模式過濾追蹤記錄
- 提供統計資訊 (成功率、平均執行時間、最常用工具)

### 整合原則

- **OpenAI trace**: 專注於技術層面的可觀察性 (工具調用、LLM 交互)
- **內部 trace_data**: 專注於業務層面的可追溯性 (決策歷程、績效分析)
- **兩者互補**: 不重複記錄相同資訊,各司其職

---

## 🧠 專門化 Agent Tools（自主型 Agent 架構）

### 設計理念

所有專業分析工具（基本面、技術面、風險評估、市場情緒）都採用 **自主型 Agent (Agent as Tool)** 架構：

- **完整的 Agent 能力**: 每個工具本身就是一個具備自主決策能力的 Agent
- **內建增強工具**: 整合 WebSearchTool 和 CodeInterpreterTool 提升分析能力
- **MCP 資料存取**: 透過 Casual Market MCP Server 獲取即時市場數據
- **成本優化設計**: 包含明確的工具使用準則，避免不必要的計算成本
- **標準化輸出**: 統一的分析報告格式，便於 TradingAgent 整合

### 基本面分析 Agent Tool

```python
"""Fundamental Agent - 基本面分析自主型 Agent

這個模組實作具有自主分析能力的基本面分析 Agent。
"""

from agents import Agent, WebSearchTool, CodeInterpreterTool, function_tool

def fundamental_agent_instructions() -> str:
    """基本面分析 Agent 的指令定義"""
    return f"""你是一位資深的基本面分析師,專精於公司財務分析和價值評估。

## 你的專業能力

1. 財務報表分析
   - 資產負債表: 財務結構、償債能力
   - 損益表: 獲利能力、營運效率
   - 現金流量表: 現金創造能力

2. 財務比率分析
   - 獲利能力: ROE、ROA、毛利率、淨利率
   - 償債能力: 負債比、流動比率
   - 效率指標: 存貨周轉率、應收帳款周轉率
   - 成長指標: 營收成長率、EPS 成長率

3. 價值評估
   - 本益比 (P/E)、股價淨值比 (P/B)
   - 股利殖利率分析
   - 相對估值與絕對估值

4. 質化分析
   - 產業地位與競爭優勢
   - 經營團隊評估
   - 商業模式分析

## 分析方法

1. 收集數據: 使用 MCP Server 獲取財務報表
2. 計算比率: 使用工具計算財務指標
3. 評估質量: 分析財務體質
4. 估值分析: 評估股價合理性
5. 成長評估: 分析成長潛力
6. 綜合建議: 產生投資建議

## 可用工具

### 專業分析工具
- calculate_financial_ratios: 計算財務比率
- analyze_financial_health: 分析財務體質
- evaluate_valuation: 評估估值水準
- analyze_growth_potential: 分析成長潛力
- generate_investment_rating: 產生投資評級
- Casual Market MCP Server: 獲取財報數據

### 增強能力工具
- WebSearchTool: 搜尋產業研究報告、競爭對手分析、法說會資訊
- CodeInterpreterTool: 執行財務模型計算、DCF 估值、敏感度分析

## CodeInterpreterTool 使用準則 ⚠️

為了控制成本和執行時間，請遵守以下原則：

1. **優先使用自訂工具**
   - 先嘗試使用提供的財務分析工具
   - 只有當需要複雜模型時才使用 CodeInterpreterTool

2. **適用場景**
   - ✅ DCF（現金流折現）估值計算
   - ✅ 敏感度分析（不同假設下的估值變化）
   - ✅ 三表財務模型建構
   - ❌ 不要用於簡單的財務比率計算
   - ❌ 不要用於已有自訂工具的功能

3. **程式碼效率要求**
   - 保持程式碼簡潔（< 150 行）
   - 避免過度複雜的模型
   - 使用 pandas 進行高效數據處理

4. **執行頻率限制**
   - 每次分析最多使用 2 次 CodeInterpreterTool
   - 優先執行最關鍵的估值計算

## 輸出格式

1. 財務體質: 健康度評分、關鍵指標
2. 估值評估: 合理價位區間、買賣建議
3. 成長分析: 成長動能評估、預期報酬
4. 風險因素: 需要注意的財務風險
5. 投資建議: BUY/HOLD/SELL 及理由
6. 信心評估: 0-100% 信心度
"""

# CasualMarket MCP 工具整合
@function_tool
async def get_company_fundamentals(ticker: str) -> dict:
    """Get comprehensive company fundamental data"""
    return await mcp_client.call_tool("get_company_profile", {"ticker": symbol})

@function_tool
async def calculate_financial_ratios(ticker: str, period: str = "latest") -> dict:
    """Calculate key financial ratios from financial statements"""
    # 實作財務比率計算邏輯
    pass

@function_tool
async def analyze_financial_health(ticker: str) -> dict:
    """Analyze overall financial health and stability"""
    # 實作財務健康度分析邏輯
    pass

@function_tool
async def evaluate_valuation(ticker: str) -> dict:
    """Evaluate stock valuation using multiple methods"""
    # 實作估值評估邏輯
    pass

@function_tool
async def analyze_growth_potential(ticker: str) -> dict:
    """Analyze company's growth potential and prospects"""
    # 實作成長潛力分析邏輯
    pass

@function_tool
async def generate_investment_rating(ticker: str) -> dict:
    """Generate investment rating and recommendation"""
    # 實作投資評級生成邏輯
    pass

# 創建基本面分析 Agent
fundamental_agent = Agent(
    name="Fundamental Analysis Agent",
    instructions=fundamental_agent_instructions(),
    tools=[
        # 專業分析工具
        calculate_financial_ratios,
        analyze_financial_health,
        evaluate_valuation,
        analyze_growth_potential,
        generate_investment_rating,

        # CasualMarket MCP Tools（透過 function_tool 包裝）
        get_company_fundamentals,
        get_company_income_statement,
        get_company_balance_sheet,
        get_company_monthly_revenue,
        get_stock_valuation_ratios,
        get_company_dividend,

        # 增強能力工具
        WebSearchTool(),
        CodeInterpreterTool(),
    ],
    model="gpt-4"
)
```

### 技術分析 Agent Tool

```python
"""Technical Agent - 技術分析自主型 Agent

這個模組實作具有自主分析能力的技術分析 Agent。
"""

from agents import Agent, WebSearchTool, CodeInterpreterTool, function_tool

def technical_agent_instructions() -> str:
    """技術分析 Agent 的指令定義"""
    return f"""你是一位專業的技術分析師,專精於股票圖表分析和技術指標解讀。

## 你的專業能力

1. 圖表型態識別
   - 經典型態: 頭肩頂底、雙重頂底、三角型態
   - 整理型態: 旗型、楔形、矩形
   - 反轉型態: 島狀反轉、V型反轉

2. 技術指標分析
   - 趨勢指標: MA、MACD
   - 動能指標: RSI、KD
   - 波動指標: 布林通道

3. 趨勢判斷與風險管理
   - 趨勢方向和強度
   - 支撐壓力位
   - 進場停損建議

## 分析方法

1. 收集數據: 使用 MCP Server 獲取價格資料
2. 計算指標: 使用工具計算技術指標
3. 識別型態: 分析圖表找出型態
4. 判斷趨勢: 評估趨勢方向和強度
5. 找關鍵價位: 確定支撐和壓力位
6. 給出建議: 綜合分析產生交易訊號

## 可用工具

### 專業分析工具
- calculate_technical_indicators: 計算 MA、RSI、MACD 等指標
- identify_chart_patterns: 識別圖表型態
- analyze_trend: 分析趨勢
- analyze_support_resistance: 找支撐壓力位
- generate_trading_signals: 產生交易訊號
- Casual Market MCP Server: 獲取市場數據

### 增強能力工具
- WebSearchTool: 主動搜尋最新的技術分析報告、專家觀點、市場評論
- CodeInterpreterTool: 執行自訂的技術指標計算、統計分析、回測驗證

## CodeInterpreterTool 使用準則 ⚠️

為了控制成本和執行時間，請遵守以下原則：

1. **優先使用自訂工具**
   - 先嘗試使用提供的專業分析工具
   - 只有當自訂工具無法滿足需求時才使用 CodeInterpreterTool

2. **適用場景**
   - ✅ 複雜的自訂指標計算（如改良版 RSI、特殊加權均線）
   - ✅ 統計檢定（如相關性分析、顯著性測試）
   - ✅ 簡短的回測驗證（< 100 行程式碼）
   - ❌ 不要用於簡單的數學計算（加減乘除）
   - ❌ 不要用於可以用自訂工具完成的任務

3. **程式碼效率要求**
   - 保持程式碼簡潔（< 100 行）
   - 避免不必要的迴圈和複雜邏輯
   - 使用向量化操作（numpy, pandas）

4. **執行頻率限制**
   - 每次分析最多使用 2 次 CodeInterpreterTool
   - 必要時將多個計算合併為一次執行

## 輸出格式

1. 趨勢分析: 方向、強度、延續性評估
2. 技術指標: 數值、訊號、背離情況
3. 關鍵價位: 支撐位、壓力位
4. 交易建議: 方向、進場價、停損價、目標價
5. 風險提示: 風險因素、注意事項
6. 信心評估: 0-100% 信心度
"""

@function_tool
async def calculate_technical_indicators(ticker: str, indicators: list[str]) -> dict:
    """Calculate specified technical indicators"""
    # 實作技術指標計算邏輯
    pass

@function_tool
async def identify_chart_patterns(ticker: str, timeframe: str = "daily") -> dict:
    """Identify chart patterns in price data"""
    # 實作圖表型態識別邏輯
    pass

@function_tool
async def analyze_trend(ticker: str) -> dict:
    """Analyze price trend direction and strength"""
    # 實作趨勢分析邏輯
    pass

@function_tool
async def analyze_support_resistance(ticker: str) -> dict:
    """Identify key support and resistance levels"""
    # 實作支撐壓力位分析邏輯
    pass

@function_tool
async def generate_trading_signals(ticker: str) -> dict:
    """Generate trading signals based on technical analysis"""
    # 實作交易訊號生成邏輯
    pass

technical_agent = Agent(
    name="Technical Analysis Agent",
    instructions=technical_agent_instructions(),
    tools=[
        # 專業分析工具
        calculate_technical_indicators,
        identify_chart_patterns,
        analyze_trend,
        analyze_support_resistance,
        generate_trading_signals,

        # CasualMarket MCP Tools
        get_stock_daily_trading,
        get_stock_monthly_trading,
        get_stock_monthly_average,
        get_taiwan_stock_price,

        # 增強能力工具
        WebSearchTool(),
        CodeInterpreterTool(),
    ],
    model="gpt-4"
)
```

### 風險評估 Agent Tool

```python
"""Risk Agent - 風險評估自主型 Agent

這個模組實作具有自主分析能力的風險評估 Agent。
"""

from agents import Agent, WebSearchTool, CodeInterpreterTool, function_tool

def risk_agent_instructions() -> str:
    """風險評估 Agent 的指令定義"""
    return f"""你是一位專業的風險管理專家,專精於投資組合風險分析和風險控制。

## 你的專業能力

1. 風險度量
   - 波動性風險: 標準差、Beta 係數
   - 下檔風險: VaR、最大回撤
   - 流動性風險: 成交量、買賣價差

2. 投資組合風險
   - 集中度風險: HHI 指數
   - 產業曝險分析
   - 相關性分析

3. 風險管理建議
   - 部位大小建議
   - 停損點設置
   - 避險策略
   - 風險預算分配

## 分析方法

1. 收集數據: 使用 MCP Server 獲取價格和部位數據
2. 計算風險: 使用工具計算風險指標
3. 評估集中度: 分析投資組合集中度
4. 壓力測試: 模擬極端情況
5. 給出建議: 產生風險管理建議

## 可用工具

### 專業分析工具
- calculate_position_risk: 計算個別部位風險
- analyze_portfolio_concentration: 分析投資組合集中度
- calculate_portfolio_risk: 計算整體投資組合風險
- perform_stress_test: 執行壓力測試
- generate_risk_recommendations: 產生風險管理建議
- Casual Market MCP Server: 獲取市場數據

### 增強能力工具
- WebSearchTool: 搜尋風險管理最佳實踐、市場風險事件、監管規範
- CodeInterpreterTool: 執行 VaR 計算、蒙地卡羅模擬、相關性矩陣分析

## CodeInterpreterTool 使用準則 ⚠️

為了控制成本和執行時間，請遵守以下原則：

1. **優先使用自訂工具**
   - 先嘗試使用提供的風險分析工具
   - 只有當需要進階風險模型時才使用 CodeInterpreterTool

2. **適用場景**
   - ✅ VaR（風險值）計算（歷史模擬法、蒙地卡羅法）
   - ✅ 投資組合相關性矩陣分析
   - ✅ 壓力測試情境模擬
   - ❌ 不要用於簡單的風險比率計算
   - ❌ 不要用於已有自訂工具的功能

3. **程式碼效率要求**
   - 保持程式碼簡潔（< 150 行）
   - 蒙地卡羅模擬限制在 10,000 次以內
   - 使用 numpy 進行高效數值計算

4. **執行頻率限制**
   - 每次分析最多使用 2 次 CodeInterpreterTool
   - 優先執行最關鍵的風險計算

## 輸出格式

1. 風險評分: 0-100 分,越高越危險
2. 風險等級: 低/中低/中/中高/高
3. 關鍵風險: 需要注意的主要風險
4. 風險警示: 需要立即處理的風險
5. 管理建議: 具體的風險控制措施
6. 信心評估: 0-100% 信心度
"""

@function_tool
async def calculate_position_risk(ticker: str, quantity: int, entry_price: float) -> dict:
    """Calculate risk metrics for a single position"""
    # 實作個別部位風險計算邏輯
    pass

@function_tool
async def analyze_portfolio_concentration(agent_id: str) -> dict:
    """Analyze portfolio concentration risk"""
    # 實作集中度分析邏輯
    pass

@function_tool
async def calculate_portfolio_risk(agent_id: str) -> dict:
    """Calculate overall portfolio risk metrics"""
    # 實作投資組合風險計算邏輯
    pass

@function_tool
async def perform_stress_test(agent_id: str, scenario: str) -> dict:
    """Perform stress testing under various scenarios"""
    # 實作壓力測試邏輯
    pass

@function_tool
async def generate_risk_recommendations(agent_id: str) -> dict:
    """Generate risk management recommendations"""
    # 實作風險管理建議生成邏輯
    pass

risk_agent = Agent(
    name="Risk Assessment Agent",
    instructions=risk_agent_instructions(),
    tools=[
        # 專業分析工具
        calculate_position_risk,
        analyze_portfolio_concentration,
        calculate_portfolio_risk,
        perform_stress_test,
        generate_risk_recommendations,

        # CasualMarket MCP Tools
        get_current_portfolio,
        get_market_index_info,
        get_foreign_investment_by_industry,
        get_margin_trading_info,

        # 增強能力工具
        WebSearchTool(),
        CodeInterpreterTool(),
    ],
    model="gpt-4"
)
```

### 市場情緒分析 Agent Tool

```python
"""Sentiment Agent - 市場情緒分析自主型 Agent

這個模組實作具有自主分析能力的市場情緒分析 Agent。
"""

from agents import Agent, WebSearchTool, CodeInterpreterTool, function_tool

def sentiment_agent_instructions() -> str:
    """市場情緒分析 Agent 的指令定義"""
    return f"""你是一位專業的市場情緒分析師,專精於市場心理、資金流向和群眾行為分析。

## 你的專業能力

1. 市場情緒評估
   - 恐懼貪婪指數
   - 波動率指數 (VIX)
   - 市場寬度指標

2. 資金流向分析
   - 大單追蹤
   - 外資法人動向
   - 散戶行為

3. 新聞與社群情緒
   - 新聞情緒分析
   - 社群媒體情緒
   - 話題熱度追蹤

4. 情緒交易策略
   - 反向操作時機
   - 動能追蹤策略
   - 情緒極端點識別

## 分析方法

1. 收集數據: 使用 MCP Server 獲取市場、新聞、社群數據
2. 計算指標: 使用工具計算情緒指標
3. 評估心理: 分析市場心理狀態
4. 資金追蹤: 分析資金流向
5. 給出建議: 產生情緒交易策略

## 可用工具

### 專業分析工具
- calculate_fear_greed_index: 計算恐懼貪婪指數
- analyze_money_flow: 分析資金流向
- analyze_news_sentiment: 分析新聞情緒
- analyze_social_sentiment: 分析社群媒體情緒
- generate_sentiment_signals: 產生情緒交易訊號
- Casual Market MCP Server: 獲取市場數據

### 增強能力工具
- WebSearchTool: 即時搜尋最新市場新聞、社群熱議話題、情緒指標變化
- CodeInterpreterTool: 執行情緒指數計算、文字情緒分析、統計顯著性檢驗

## CodeInterpreterTool 使用準則 ⚠️

為了控制成本和執行時間，請遵守以下原則：

1. **優先使用自訂工具**
   - 先嘗試使用提供的情緒分析工具
   - 只有當需要進階文字分析時才使用 CodeInterpreterTool

2. **適用場景**
   - ✅ 文字情緒分析（NLP 情緒評分）
   - ✅ 統計檢定（情緒與價格相關性）
   - ✅ 時間序列分析（情緒趨勢預測）
   - ❌ 不要用於簡單的情緒指標計算
   - ❌ 不要用於已有自訂工具的功能

3. **程式碼效率要求**
   - 保持程式碼簡潔（< 100 行）
   - 文字分析限制在 1000 條以內
   - 使用簡化的 NLP 方法（避免複雜模型）

4. **執行頻率限制**
   - 每次分析最多使用 2 次 CodeInterpreterTool
   - 優先執行最關鍵的情緒計算

## 輸出格式

1. 情緒評分: -100 (極度恐慌) 到 +100 (極度貪婪)
2. 市場階段: 恐慌/悲觀/中性/樂觀/亢奮
3. 資金流向: 流入/流出/平衡
4. 重要新聞: 影響市場的關鍵事件
5. 交易建議: 情緒交易策略建議
6. 信心評估: 0-100% 信心度
"""

@function_tool
async def calculate_fear_greed_index() -> dict:
    """Calculate market fear & greed index"""
    # 實作恐懼貪婪指數計算邏輯
    pass

@function_tool
async def analyze_money_flow(timeframe: str = "daily") -> dict:
    """Analyze institutional and retail money flow"""
    # 實作資金流向分析邏輯
    pass

@function_tool
async def analyze_news_sentiment(keywords: list[str] = None) -> dict:
    """Analyze sentiment from recent news articles"""
    # 實作新聞情緒分析邏輯
    pass

@function_tool
async def analyze_social_sentiment(platform: str = "all") -> dict:
    """Analyze sentiment from social media platforms"""
    # 實作社群媒體情緒分析邏輯
    pass

@function_tool
async def generate_sentiment_signals(ticker: str = None) -> dict:
    """Generate trading signals based on sentiment analysis"""
    # 實作情緒交易訊號生成邏輯
    pass

sentiment_agent = Agent(
    name="Market Sentiment Agent",
    instructions=sentiment_agent_instructions(),
    tools=[
        # 專業分析工具
        calculate_fear_greed_index,
        analyze_money_flow,
        analyze_news_sentiment,
        analyze_social_sentiment,
        generate_sentiment_signals,

        # CasualMarket MCP Tools
        get_real_time_trading_stats,
        get_top_foreign_holdings,
        get_foreign_investment_by_industry,
        get_etf_regular_investment_ranking,
        get_market_index_info,

        # 增強能力工具
        WebSearchTool(),
        CodeInterpreterTool(),
    ],
    model="gpt-4"
)
```

---

## 🌐 OpenAI Hosted Tools 整合

### WebSearchTool - 即時市場資訊

```python
from agents import WebSearchTool

# WebSearchTool 自動搜尋最新市場資訊
web_search = WebSearchTool()

# TradingAgent 可透過此工具獲取：
# - 最新財經新聞和市場分析
# - 公司公告和重大事件
# - 產業趨勢和政策變化
# - 國際市場動態和影響
```

### CodeInterpreterTool - 量化分析

```python
from agents import CodeInterpreterTool

# CodeInterpreterTool 用於高級數據分析
code_interpreter = CodeInterpreterTool()

# 技術分析應用：
# - 股價技術指標計算 (RSI, MACD, KD, 布林通道)
# - 圖表模式識別和趨勢分析
# - 回測策略和績效評估
# - 風險指標計算 (VaR, 最大回撤, 夏普比率)
# - 投資組合最佳化
```

### FileSearchTool - 研究文檔檢索

```python
from agents import FileSearchTool

# 整合研究文檔和歷史分析
file_search = FileSearchTool(
    max_num_results=5,
    vector_store_ids=["RESEARCH_REPORTS_STORE"]
)

# 可搜尋內容：
# - 歷史分析報告
# - 投資策略文檔
# - 風險管理指引
# - 市場研究資料
```

---

## 🔧 交易驗證 Function Tools

### 市場狀態驗證工具

```python
from agents import function_tool
from datetime import datetime, time
import pytz

@function_tool
async def check_trading_hours() -> dict:
    """Check if Taiwan stock market is currently open for trading"""
    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)

    # 台股交易時間：週一到週五 09:00-13:30
    is_weekday = now.weekday() < 5
    is_trading_time = time(9, 0) <= now.time() <= time(13, 30)

    return {
        "is_market_open": is_weekday and is_trading_time,
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "next_open": "下個交易日 09:00" if not (is_weekday and is_trading_time) else None
    }

@function_tool
async def get_available_cash(agent_id: str) -> dict:
    """Get current available cash for trading"""
    # 從資料庫查詢Agent的現金餘額
    portfolio = await db.get_agent_portfolio(agent_id)
    return {
        "available_cash": portfolio.cash_balance,
        "reserved_cash": portfolio.reserved_cash,
        "total_portfolio_value": portfolio.total_value
    }

@function_tool
async def get_current_holdings(agent_id: str) -> dict:
    """Get current stock holdings for the agent"""
    holdings = await db.get_agent_holdings(agent_id)
    return {
        "holdings": [
            {
                "ticker": holding.ticker,
                "company_name": holding.company_name,
                "quantity": holding.quantity,
                "average_cost": holding.average_cost,
                "current_price": holding.current_price,
                "unrealized_pnl": holding.unrealized_pnl,
                "weight": holding.weight
            }
            for holding in holdings
        ],
        "total_holdings_value": sum(h.market_value for h in holdings)
    }

@function_tool
async def validate_trade_parameters(
    ticker: str,
    action: str,
    quantity: int,
    price: float = None
) -> dict:
    """Validate trading parameters before execution"""

    # 股票代號驗證
    if not re.match(r'^\d{4}[A-Z]?$', ticker):
        return {"valid": False, "error": "Invalid stock ticker format"}

    # 交易數量驗證 (台股最小單位1000股)
    if quantity % 1000 != 0:
        return {"valid": False, "error": "Quantity must be multiple of 1000 shares"}

    # 價格驗證
    if price is not None and price <= 0:
        return {"valid": False, "error": "Price must be positive"}

    # 漲跌停價格檢查
    current_data = await get_taiwan_stock_price(ticker)
    if price and (price > current_data.limit_up or price < current_data.limit_down):
        return {
            "valid": False,
            "error": f"Price outside daily limit: {current_data.limit_down}-{current_data.limit_up}"
        }

    return {
        "valid": True,
        "estimated_cost": quantity * (price or current_data.current_price),
        "commission": calculate_commission(quantity, price or current_data.current_price)
    }
```

### 進階市場狀態檢查器 (MarketStatusChecker)

為了提供更準確的市場狀態判斷，系統整合了 `MarketStatusChecker` 組件，支援動態查詢台灣股市交易日和假日資訊。

#### 核心改進與更新

##### 從硬編碼到動態查詢 (2025-10-07 更新)

**修改前 (硬編碼方式):**

```python
# 假日列表硬編碼在類別中
self.market_holidays = [
    MarketHoliday(date="2024-01-01", name="元旦", type="national"),
    # ... 需要每年手動更新
]
```

**修改後 (MCP 動態查詢):**

```python
# 透過 MCP 工具動態查詢
checker = MarketStatusChecker(
    mcp_check_trading_day=mcp_client.check_trading_day,
    mcp_get_holiday_info=mcp_client.get_holiday_info
)
```

#### 主要改進優勢

1. ✅ **自動更新** - 假日資訊由 MCP 服務維護
2. ✅ **準確性** - 使用官方資料來源
3. ✅ **向後相容** - 現有代碼無需修改
4. ✅ **容錯性** - 自動 fallback 到基本邏輯

#### Agent 中的整合使用

```python
from agents.functions.market_status import MarketStatusChecker
from agents.core.base_agent import CasualTradingAgent

class TradingAgent(CasualTradingAgent):
    def __init__(self):
        super().__init__()

        # 初始化市場狀態檢查器 (整合 MCP 工具)
        self.market_checker = MarketStatusChecker(
            mcp_check_trading_day=self._mcp_check_trading_day,
            mcp_get_holiday_info=self._mcp_get_holiday_info
        )

    async def _mcp_check_trading_day(self, date: str):
        """透過 MCP 客戶端檢查交易日"""
        return await self.mcp_client.call_tool(
            "check_taiwan_trading_day",
            {"date": date}
        )

    async def _mcp_get_holiday_info(self, date: str):
        """透過 MCP 客戶端取得假日資訊"""
        return await self.mcp_client.call_tool(
            "get_taiwan_holiday_info",
            {"date": date}
        )

    async def execute_trade(self, ticker: str, quantity: int):
        """執行交易前檢查市場狀態"""
        # 檢查市場是否開盤
        status = await self.market_checker.get_market_status()

        if not status.is_open:
            return {
                "success": False,
                "error": f"市場未開盤 (當前時段: {status.current_session})"
            }

        # 執行交易...
        return await self._execute_order(ticker, quantity)
```

#### 使用的 MCP 工具

**1. `check_taiwan_trading_day`**

用途: 檢查指定日期是否為交易日

參數:

- `date`: 日期字串 (YYYY-MM-DD)

回應格式:

```python
{
    "success": True,
    "data": {
        "date": "2025-10-10",
        "is_trading_day": False,
        "is_weekend": False,
        "is_holiday": True,
        "holiday_name": "國慶日",
        "reason": "國定假日"
    }
}
```

**2. `get_taiwan_holiday_info`**

用途: 取得假日詳細資訊

參數:

- `date`: 日期字串 (YYYY-MM-DD)

回應格式:

```python
{
    "success": True,
    "data": {
        "date": "2025-10-10",
        "is_holiday": True,
        "name": "國慶日",
        "holiday_category": "national",
        "description": "中華民國國慶日"
    }
}
```

#### Fallback 機制

當 MCP 工具不可用或呼叫失敗時，系統會自動使用基本的週末判斷邏輯：

- 週一到週五 → 視為可能的交易日
- 週六日 → 視為非交易日
- 記錄警告訊息但不會中斷執行

#### 完整 API 參考

**MarketStatusChecker 初始化:**

```python
MarketStatusChecker(
    mcp_check_trading_day: Callable[[str], Any] | None = None,
    mcp_get_holiday_info: Callable[[str], Any] | None = None
)
```

**主要方法:**

- `get_market_status(check_time=None)`: 取得市場開盤狀態
- `get_market_calendar(start_date, end_date)`: 取得交易日曆
- `clear_holiday_cache()`: 清除假日快取

**快取機制:**

- 使用 `_holiday_cache` 避免重複查詢同一日期
- 快取僅在單次執行期間有效，程序重啟後會清空

#### 最佳實踐建議

1. **注入 MCP 工具**: 在初始化時提供 MCP 工具函數，獲得最準確的交易日資訊
2. **快取管理**: 如需更新假日資訊，呼叫 `clear_holiday_cache()`
3. **錯誤處理**: MCP 呼叫失敗時會自動 fallback，無需額外處理
4. **日誌監控**: 檢查日誌中的 warning，了解 MCP 呼叫狀態

#### 測試狀態

✅ 所有測試通過 (8/8)

- ✓ 基本功能 (無 MCP)
- ✓ MCP 整合
- ✓ 假日偵測
- ✓ 週末偵測
- ✓ 交易時段識別
- ✓ 交易日曆整合
- ✓ 快取機制
- ✓ MCP 失敗 fallback

---

## 🛠️ CasualMarket MCP 服務整合

### 外部專案依賴

**CasualMarket 專案**:

- **GitHub**: <https://github.com/sacahan/CasualMarket>
- **功能**: 提供台灣股票市場數據的 MCP 服務
- **安裝**: `uvx --from git+https://github.com/sacahan/CasualMarket.git market-mcp-server`
- **用途**: Agent 透過 MCP 協定調用股票價格、交易模擬等功能

### 外部 MCP 服務設定

````python
from agents import HostedMCPTool

# 整合 CasualMarket MCP Server (獨立專案)
casualmarket_mcp = HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "casualmarket",
        "server_url": "uvx://casualmarket/market-mcp-server",
        "require_approval": "never",
    }
)

# TradingAgent 可使用的 CasualMarket 工具：

### 核心交易工具

#### 股票價格查詢

```python
# 工具: get_taiwan_stock_price
# 用途: 獲取即時股票價格和交易資訊
response = await mcp_client.call_tool("get_taiwan_stock_price", {
    "ticker": "2330"  # 台積電
})
# 返回: 即時價格、漲跌幅、成交量、五檔報價等
````

#### 模擬交易執行

```python
# 工具: buy_taiwan_stock
# 用途: 模擬股票買入操作
response = await mcp_client.call_tool("buy_taiwan_stock", {
    "ticker": "2330",
    "quantity": 1000,  # 1張
    "price": None      # 市價單
})

# 工具: sell_taiwan_stock
# 用途: 模擬股票賣出操作
response = await mcp_client.call_tool("sell_taiwan_stock", {
    "ticker": "2330",
    "quantity": 1000,
    "price": 520.0     # 限價單
})
```

### 基本面分析工具

#### 公司基本資料

```python
# 工具: get_company_profile
# 用途: 獲取公司基本資訊、產業分類、主要業務
response = await mcp_client.call_tool("get_company_profile", {
    "ticker": "2330"
})
```

#### 財務報表工具

```python
# 工具: get_company_income_statement
# 用途: 獲取綜合損益表數據
income_data = await mcp_client.call_tool("get_company_income_statement", {
    "ticker": "2330"
})

# 工具: get_company_balance_sheet
# 用途: 獲取資產負債表數據
balance_data = await mcp_client.call_tool("get_company_balance_sheet", {
    "ticker": "2330"
})

# 工具: get_company_monthly_revenue
# 用途: 獲取月營收資料
revenue_data = await mcp_client.call_tool("get_company_monthly_revenue", {
    "ticker": "2330"
})
```

#### 估值分析工具

```python
# 工具: get_stock_valuation_ratios
# 用途: 獲取本益比、股價淨值比、殖利率等估值指標
valuation = await mcp_client.call_tool("get_stock_valuation_ratios", {
    "ticker": "2330"
})
```

### 市場數據工具

#### 交易統計工具

```python
# 工具: get_stock_daily_trading
# 用途: 獲取日交易資訊
daily_stats = await mcp_client.call_tool("get_stock_daily_trading", {
    "ticker": "2330"
})

# 工具: get_real_time_trading_stats
# 用途: 獲取即時交易統計(5分鐘資料)
realtime_stats = await mcp_client.call_tool("get_real_time_trading_stats")
```

#### 市場指數工具

```python
# 工具: get_market_index_info
# 用途: 獲取大盤指數資訊
market_index = await mcp_client.call_tool("get_market_index_info", {
    "category": "major",
    "count": 20
})
```

### Agent中的MCP工具使用範例

#### 分析Agent使用範例

```python
class AnalysisAgent:
    async def analyze_stock_fundamentals(self, ticker: str):
        # 獲取基本資料
        profile = await self.call_mcp_tool("get_company_profile", {"ticker": symbol})

        # 獲取財務數據
        income = await self.call_mcp_tool("get_company_income_statement", {"ticker": symbol})
        balance = await self.call_mcp_tool("get_company_balance_sheet", {"ticker": symbol})

        # 獲取估值指標
        valuation = await self.call_mcp_tool("get_stock_valuation_ratios", {"ticker": symbol})

        # 綜合分析邏輯
        return self._combine_fundamental_analysis(profile, income, balance, valuation)
```

#### 執行Agent使用範例

```python
class ExecutionAgent:
    async def execute_trade_decision(self, decision: TradeDecision):
        # 獲取即時價格
        price_data = await self.call_mcp_tool("get_taiwan_stock_price", {
            "ticker": decision.ticker
        })

        # 執行交易
        if decision.action == "BUY":
            result = await self.call_mcp_tool("buy_taiwan_stock", {
                "ticker": decision.ticker,
                "quantity": decision.quantity,
                "price": decision.target_price
            })
        elif decision.action == "SELL":
            result = await self.call_mcp_tool("sell_taiwan_stock", {
                "ticker": decision.ticker,
                "quantity": decision.quantity,
                "price": decision.target_price
            })

        return result
```

### 錯誤處理和重試機制

#### MCP工具調用的統一錯誤處理

```python
class MCPToolWrapper:
    async def safe_call_tool(self, tool_name: str, params: dict, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                result = await self.mcp_client.call_tool(tool_name, params)
                return result
            except MCPConnectionError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指數退避
                    continue
                raise
            except MCPToolError as e:
                # 記錄工具錯誤，不重試
                logger.error(f"Tool {tool_name} failed: {e}")
                raise
```

---

## 🎨 前端 Agent 管理介面

### Agent 創建和配置

```typescript
interface AgentCreationForm {
  name: string;
  description: string;
  strategy_type: "conservative" | "balanced" | "aggressive";
  initial_funds: number;
  max_turns: number;
  risk_tolerance: number;

  // Agent Tools 選擇
  enabled_tools: {
    fundamental_analysis: boolean;
    technical_analysis: boolean;
    risk_assessment: boolean;
    sentiment_analysis: boolean;
    web_search: boolean;
    code_interpreter: boolean;
  };

  // 投資偏好設定
  investment_preferences: {
    preferred_sectors: string[];
    excluded_stocks: string[];
    max_position_size: number;
    rebalance_frequency: "daily" | "weekly" | "monthly";
  };

  // 客製化指令
  custom_instructions?: string;
}
```

### Agent 狀態監控

```typescript
interface AgentDashboard {
  agent_id: string;
  current_mode: "TRADING" | "REBALANCING" | "OBSERVATION";

  // 即時狀態
  is_active: boolean;
  last_execution: Date;
  next_scheduled: Date;

  // 績效指標
  performance: {
    total_return: number;
    win_rate: number;
    max_drawdown: number;
    sharpe_ratio: number;
    current_positions: Position[];
    cash_balance: number;
  };

  // 執行歷史
  recent_decisions: AgentDecision[];
  error_logs: AgentError[];
}
```

### 前端 API 端點

```typescript
// Agent 管理 API
class AgentManagementAPI {
  // 創建新 Agent
  async createAgent(config: AgentCreationForm): Promise<Agent> {
    return await fetch("/api/agents", {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  // 更新 Agent 配置
  async updateAgent(
    agentId: string,
    updates: Partial<AgentCreationForm>,
  ): Promise<Agent> {
    return await fetch(`/api/agents/${agentId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  }

  // 啟動/停止 Agent
  async toggleAgent(agentId: string, action: "start" | "stop"): Promise<void> {
    return await fetch(`/api/agents/${agentId}/${action}`, {
      method: "POST",
    });
  }

  // 手動切換執行模式
  async changeMode(
    agentId: string,
    mode: AgentMode,
    reason?: string,
  ): Promise<void> {
    return await fetch(`/api/agents/${agentId}/mode`, {
      method: "PUT",
      body: JSON.stringify({ mode, reason }),
    });
  }

  // 即時狀態查詢
  async getAgentStatus(agentId: string): Promise<AgentDashboard> {
    return await fetch(`/api/agents/${agentId}/status`);
  }

  // 執行歷史查詢
  async getExecutionHistory(
    agentId: string,
    limit: number = 50,
  ): Promise<AgentTrace[]> {
    return await fetch(`/api/agents/${agentId}/history?limit=${limit}`);
  }
}
```

### 即時通知系統

```typescript
// WebSocket 即時更新
class AgentNotificationService {
  private ws: WebSocket;

  constructor(agentId: string) {
    this.ws = new WebSocket(
      `wss://api.casualtrader.com/agents/${agentId}/notifications`,
    );
  }

  onAgentStateChange(callback: (state: AgentState) => void) {
    this.ws.addEventListener("message", (event) => {
      const notification = JSON.parse(event.data);
      if (notification.type === "state_change") {
        callback(notification.data);
      }
    });
  }

  onTradeExecution(callback: (trade: TradeExecution) => void) {
    this.ws.addEventListener("message", (event) => {
      const notification = JSON.parse(event.data);
      if (notification.type === "trade_executed") {
        callback(notification.data);
      }
    });
  }

  onError(callback: (error: AgentError) => void) {
    this.ws.addEventListener("message", (event) => {
      const notification = JSON.parse(event.data);
      if (notification.type === "error") {
        callback(notification.data);
      }
    });
  }
}
```

---

## 🔄 簡化實作架構

### 核心工作流程

1. **Agent 創建** - 用戶透過前端表單設定投資偏好和策略條件
2. **指令生成** - 後端根據用戶輸入生成完整的 Agent instructions
3. **Agent 執行** - OpenAI Agent 根據指令和工具自主進行交易決策
4. **策略調整** - Agent 根據績效和市場條件自主調整策略
5. **變更記錄** - 所有策略變更自動記錄到資料庫
6. **前端監控** - 用戶可即時查看 Agent 狀態和策略演進歷史

### 簡化設計優勢

- **實作簡單**: 移除複雜的狀態機和時間管理
- **用戶友好**: 直觀的自然語言配置介面
- **高度靈活**: Agent 可自主適應市場變化
- **完全透明**: 所有決策和變更都有完整記錄
- **易於維護**: 主要邏輯集中在 prompt 設計

---

## 📁 檔案結構

> **注意**: 完整的專案結構定義請參閱 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
> 本節僅列出與 Agent 系統直接相關的檔案。

### Agent 系統相關檔案

```bash
backend/src/agents/           # Agent 系統模塊
├── core/                     # 核心 Agent 實作
│   ├── trading_agent.py      # 簡化的TradingAgent實作
│   ├── instruction_generator.py  # Agent指令生成器
│   ├── strategy_tracker.py       # 策略變更追蹤
│   └── models.py             # Agent 資料模型定義
├── tools/                    # 專門化分析工具
│   ├── fundamental_agent.py  # 基本面分析工具
│   ├── technical_agent.py    # 技術分析工具
│   ├── risk_agent.py         # 風險評估工具
│   └── sentiment_agent.py    # 市場情緒分析工具
├── functions/                # 交易驗證功能
│   ├── trading_validation.py # 交易參數驗證
│   ├── market_status.py      # 市場狀態檢查
│   └── portfolio_queries.py  # 投資組合查詢
└── integrations/             # 外部服務整合
    ├── mcp_client.py         # CasualMarket MCP客戶端
    └── mcp_function_wrappers.py  # MCP工具Function包裝

backend/src/api/              # Agent 相關 API 端點
├── routers/
│   ├── agents.py             # Agent CRUD操作路由
│   ├── strategy_changes.py   # 策略變更API路由
│   └── traces.py             # Agent執行追蹤路由
└── services/
    ├── agent_service.py      # Agent 業務邏輯
    ├── strategy_service.py   # 策略變更服務
    └── websocket_service.py  # 即時通知服務

frontend/src/components/Agent/  # Agent 前端組件
├── AgentCreationForm.svelte    # 簡化的Agent創建表單
├── AgentDashboard.svelte       # Agent監控儀表板
├── StrategyHistoryView.svelte  # 策略變更歷史查看
├── StrategyChangeModal.svelte  # 策略變更詳情彈窗
├── AgentCard.svelte            # Agent基礎卡片
├── AgentGrid.svelte            # Agent網格布局
└── AgentPerformancePanel.svelte # Agent績效面板

frontend/src/stores/
├── agents.js                 # Agent 狀態管理
└── websocket.js              # WebSocket 連線狀態

tests/backend/agents/         # Agent 系統測試
├── core/
│   ├── test_trading_agent.py
│   ├── test_instruction_generator.py
│   ├── test_strategy_tracker.py
│   └── test_models.py
├── tools/
│   ├── test_fundamental_agent.py
│   ├── test_technical_agent.py
│   ├── test_risk_agent.py
│   └── test_sentiment_agent.py
├── functions/
│   ├── test_trading_validation.py
│   ├── test_market_status.py
│   └── test_portfolio_queries.py
└── integrations/
    ├── test_mcp_client.py
    └── test_mcp_integration.py

tests/frontend/unit/components/Agent/  # Agent 組件測試
├── AgentCard.test.js
├── AgentDashboard.test.js
├── AgentCreationForm.test.js
├── StrategyHistoryView.test.js
└── AgentConfigEditor.test.js
```

---

## ✅ 簡化實作檢查清單

### 核心 TradingAgent 架構

- [ ] 基於 Prompt 的 TradingAgent 實作
- [ ] Agent 指令生成器 (`instruction_generator.py`)
- [ ] 四種交易模式提示詞設計 (TRADING/REBALANCING/STRATEGY_REVIEW/OBSERVATION)
- [ ] Agent Tool 整合機制
- [ ] OpenAI Agents SDK 整合
- [ ] 基本配置管理

### 策略變更記錄系統

- [ ] 策略變更資料模型 (`StrategyChange`)
- [ ] 策略變更記錄工具 (`record_strategy_change`)
- [ ] 策略變更追蹤服務 (`strategy_tracker.py`)
- [ ] 策略變更 API 端點
- [ ] 策略變更歷史查詢功能

### 專門化 Agent Tools

- [ ] 基本面分析 Agent Tool (`fundamental_agent.py`)
  - [ ] 財務報表分析功能
  - [ ] 估值指標計算
  - [ ] 投資建議生成
- [ ] 技術分析 Agent Tool (`technical_agent.py`)
  - [ ] CodeInterpreterTool 整合
  - [ ] 技術指標計算
  - [ ] 圖表模式識別
- [ ] 風險評估 Agent Tool (`risk_agent.py`)
  - [ ] 投資組合風險分析
  - [ ] 部位大小建議
  - [ ] VaR 和最大回撤計算
- [ ] 市場情緒分析 Agent Tool (`sentiment_agent.py`)
  - [ ] WebSearchTool 整合
  - [ ] 新聞情緒分析
  - [ ] 市場趨勢判斷

### OpenAI Hosted Tools 整合

- [ ] WebSearchTool 設定和使用
- [ ] CodeInterpreterTool 量化分析功能
- [ ] FileSearchTool 研究文檔檢索
- [ ] Tool 權限和安全控制

### 交易驗證 Function Tools

- [ ] 市場開盤時間檢查 (`check_trading_hours`)
- [ ] 可用現金查詢 (`get_available_cash`)
- [ ] 持倉狀況查詢 (`get_current_holdings`)
- [ ] 交易參數驗證 (`validate_trade_parameters`)
- [ ] 台股交易規則驗證

### CasualMarket MCP 整合

- [ ] 外部 MCP 服務設定 (CasualMarket 專案)
- [ ] CasualMarket MCP Server 連接
- [ ] MCP工具Function包裝器
- [ ] MCP工具錯誤處理和重試機制

### 前端 Agent 管理介面

- [ ] 簡化的 Agent 創建表單 (`AgentCreationForm.svelte`)
- [ ] Agent 監控儀表板 (`AgentDashboard.svelte`)
- [ ] 策略變更歷史查看 (`StrategyHistoryView.svelte`)
- [ ] 策略變更詳情彈窗 (`StrategyChangeModal.svelte`)
- [ ] Agent 管理 API
- [ ] WebSocket 即時通知服務

### 基礎功能

- [ ] Agent 基本執行和監控
- [ ] 投資組合績效追蹤
- [ ] 基本風險管理機制
- [ ] Agent 執行歷史記錄
- [ ] 策略變更透明度和可追溯性

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
