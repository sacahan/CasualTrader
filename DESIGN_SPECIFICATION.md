# AI 股票交易模擬器 - 設計規格書

**版本**: 2.0
**日期**: 2025-01-10
**專案**: CasualTrader AI Trading Simulator

## 📋 專案概述

### 產品願景

打造一個即時、可視化的 AI 股票交易模擬器，使用 OpenAI Agent SDK 構建智能交易代理人，支援多種 AI 模型同時進行股票交易，提供觀戰、分析和學習的平台。

### 核心價值

- **AI 競技場**：多 AI 模型交易策略競賽
- **即時觀戰**：實時觀察 AI 決策和執行過程
- **教育價值**：通過 AI 行為學習投資策略
- **策略分析**：比較不同投資方法的效果
- **智能決策**：AI 代理人基於市場數據和研究分析進行自主交易
- **策略持久化**：投資策略和決策過程完整記錄與追蹤

---

## 🎯 功能需求規格

### 1. AI 代理人管理系統 (基於 OpenAI Agent SDK)

#### 1.1 代理人生命週期管理

- **創建代理人**
  - 支援自定義名稱、策略類型、顏色主題
  - 預設初始資金：TWD 1,000,000
  - 支援的 AI 模型：GPT-4o-mini, GPT-4o, DeepSeek, Grok, Gemini
  - SQLiteSession 會話持久化管理

- **代理人狀態控制**
  - 啟動/停止交易
  - 暫停/恢復操作
  - 動態策略調整與重設
  - 資金重置
  - 交易時間驗證（台灣集中市場交易時間：週一至週五 09:00-13:30）

#### 1.2 Agent 創建與配置系統

系統支援從前端動態創建 AI Agent，每個 Agent 的配置包含：

- **Agent 名稱**：使用者自定義的 Agent 名稱
- **AI 模型**：GPT-4o-mini, GPT-4o, DeepSeek, Grok, Gemini
- **策略 Prompt**：完全自訂的投資策略描述（支援預設模板）
- **主體顏色**：Agent 在前端的識別色彩
- **初始資金**：Agent 的起始投資金額

#### 1.3 策略 Prompt 系統

策略透過純文字 prompt 定義，支援：

**Prompt Template 範例** (用於重設和初始值)：

```text
你是一位專業的穩健型投資者，投資目標是長期穩定增值，風險偏好較低。

投資原則：
- 優先考慮大型績優股和金融股
- 注重公司財務穩健性和股息配發紀錄
- 避免高波動性和投機性股票
- 分散投資降低風險

決策時請考慮：
1. 公司基本面分析（財務指標、營收穩定性）
2. 股息殖利率和配發紀錄
3. 產業地位和競爭優勢
4. 經濟環境對該產業的影響

你的投資組合目標是穩定成長，保護資本為優先考量。
```

**動態策略調整**：

- Agent 可以根據市場情況動態調整策略
- 所有策略變更都會持久化記錄
- 提供重設為初始 Template 的功能

#### 1.4 Agent 實作方式

```python
from agents import Agent

def create_trading_agent(agent_config: dict):
    """根據前端配置創建 Trading Agent"""

    # 創建 Agent 實例
    agent = Agent(
        name=agent_config["name"],
        model=agent_config["ai_model"],
        instructions=agent_config["strategy_prompt"],  # 直接使用使用者輸入的 prompt
    )

    # 配置所有可用工具（無需限制）
    configure_all_tools(agent)

    return agent

def configure_all_tools(agent: Agent):
    """為 Agent 配置所有可用工具"""
    # 所有工具都開放給 Agent 使用
    tools = [
        MarketMCPTool(),           # 市場數據與交易
        WebSearchTool(),           # 網路搜尋
        ResearchAgentTool(),       # 金融研究員 Agent
        TimeValidatorTool(),       # 交易時間驗證
        FundValidatorTool(),       # 資金驗證
        RiskCalculatorTool(),      # 風險計算
        PortfolioManagerTool(),    # 投資組合管理
        # 未來可擴展更多 custom tools
    ]

    for tool in tools:
        agent.add_tool(tool)
```

#### 1.5 Agent-to-Tool 架構設計

採用 OpenAI Agent SDK 的 agent-to-tool 功能，將專業功能 Agent 作為工具提供給交易 Agent：

### 基礎數據工具 (Basic Tools)

#### 🔧 **Market MCP Server** (已實作)

- **功能**：台灣股票即時價格查詢與模擬交易執行
- **職責**：
  - `get_taiwan_stock_price(symbol)`: 取得股票即時價格
  - `buy_taiwan_stock(symbol, quantity)`: 執行買入操作
  - `sell_taiwan_stock(symbol, quantity)`: 執行賣出操作
- **狀態**：✅ 已實作 (現有 market_mcp 模組)

#### 🔧 **WebSearchTool** (內建工具)

- **功能**：OpenAI Agent SDK 內建的網路搜尋工具
- **職責**：
  - 搜尋網路上的即時資訊
  - 取得市場新聞和公司資訊
  - 提供最新的財經資訊
- **狀態**：✅ 內建工具 (直接使用)
- **使用方式**：

  ```python
  from agents import WebSearchTool

  # 直接加入 Agent 的工具列表
  tools = [WebSearchTool()]
  ```

### 專業功能 Agent (Agent-as-Tool)

#### 🤖 **金融研究員 Agent** (需要實作)

- **Agent 專業**：專精財務分析和投資研究
- **作為工具提供的功能**：
  - `analyze_company_fundamentals(symbol)`: 公司基本面分析
  - `evaluate_financial_health(symbol)`: 財務健康度評估
  - `assess_industry_trends(sector)`: 產業趨勢分析
  - `generate_investment_recommendation(symbol, context)`: 投資建議生成
- **狀態**：🔨 需要 Custom 實作
- **Agent 設定**：
  ```python
  research_agent = Agent(
      name="金融研究員",
      model="gpt-4o",  # 使用較強模型進行分析
      instructions="你是專業的金融研究員，擅長基本面分析..."
  )
  ```

#### 🤖 **技術分析師 Agent** (需要實作)

- **Agent 專業**：專精技術指標和圖表分析
- **作為工具提供的功能**：
  - `analyze_technical_indicators(symbol, timeframe)`: 技術指標分析
  - `identify_chart_patterns(symbol)`: 圖表型態識別
  - `calculate_support_resistance(symbol)`: 支撐阻力計算
  - `assess_momentum_signals(symbol)`: 動量訊號評估
- **狀態**：🔨 需要 Custom 實作

#### 🤖 **風險評估師 Agent** (需要實作)

- **Agent 專業**：專精投資組合風險管理
- **作為工具提供的功能**：
  - `calculate_portfolio_risk(agent_id)`: 投資組合風險計算
  - `assess_position_sizing(symbol, portfolio_value)`: 部位大小建議
  - `evaluate_correlation_risk(holdings)`: 相關性風險評估
  - `suggest_diversification(portfolio)`: 分散化建議
- **狀態**：🔨 需要 Custom 實作

### 驗證與管理工具 (Validation Tools)

#### 🔧 **TimeValidatorTool** (需要實作)

- **功能**：驗證台灣股市交易時間
- **職責**：
  - `is_trading_hours()`: 檢查當前是否為交易時間
  - `get_next_trading_session()`: 取得下次交易時間
- **狀態**：🔨 需要 Custom 實作

#### 🔧 **FundValidatorTool** (需要實作)

- **功能**：驗證投資資金充足性
- **職責**：
  - `check_buying_power(agent_id, amount)`: 檢查購買力
  - `calculate_transaction_cost(symbol, quantity, price)`: 計算交易成本
- **狀態**：🔨 需要 Custom 實作

### Agent-to-Tool 實作範例 (基於官方文檔)

```python
from agents import Agent, Runner, function_tool, WebSearchTool

# 1. 創建專業功能 Agent
research_agent = Agent(
    name="金融研究員",
    model="gpt-4o",
    instructions="""你是專業的金融研究員，具備深厚的財務分析能力。
    你專精於：
    - 公司基本面分析
    - 財務報表解讀
    - 產業趨勢研究
    - 投資價值評估

    請基於使用者提供的股票代碼和分析需求，提供客觀、專業的分析報告。"""
)

technical_agent = Agent(
    name="技術分析師",
    model="gpt-4o",
    instructions="""你是專業的技術分析師，專精於股票技術面分析。
    你專精於：
    - 技術指標分析 (RSI, MACD, KD 等)
    - 圖表型態識別
    - 支撐阻力位分析
    - 趨勢和動量分析

    請基於股票代碼提供技術面分析建議。"""
)

risk_agent = Agent(
    name="風險評估師",
    model="gpt-4o",
    instructions="""你是專業的投資風險評估師，專精於投資組合風險管理。
    你專精於：
    - 投資組合風險計算
    - 相關性分析
    - 部位控制建議
    - 分散化策略

    請基於投資組合資訊提供風險評估和建議。"""
)

# 2. 基礎工具定義
@function_tool
async def get_stock_price(symbol: str) -> str:
    """取得台灣股票即時價格"""
    # 呼叫現有的 market_mcp_server
    from market_mcp.tools.stock_price_tool import get_taiwan_stock_price
    result = await get_taiwan_stock_price(symbol)
    return f"{symbol} 目前價格: {result}"

@function_tool
async def buy_taiwan_stock(symbol: str, quantity: int) -> str:
    """執行台灣股票買入操作"""
    # 呼叫現有的 market_mcp_server
    from market_mcp.tools.stock_price_tool import buy_taiwan_stock
    result = await buy_taiwan_stock(symbol, quantity)
    return f"已買入 {symbol} {quantity} 股"

@function_tool
async def sell_taiwan_stock(symbol: str, quantity: int) -> str:
    """執行台灣股票賣出操作"""
    # 呼叫現有的 market_mcp_server
    from market_mcp.tools.stock_price_tool import sell_taiwan_stock
    result = await sell_taiwan_stock(symbol, quantity)
    return f"已賣出 {symbol} {quantity} 股"

@function_tool
async def validate_trading_time() -> str:
    """驗證當前是否為台灣股市交易時間"""
    # TODO: 實作交易時間驗證
    import datetime
    import pytz

    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.datetime.now(taiwan_tz)

    # 簡化版本：週一到週五 09:00-13:30
    if now.weekday() < 5 and 9 <= now.hour < 14:
        return "當前為台灣股市交易時間，可以進行交易"
    else:
        return "當前非台灣股市交易時間，無法進行交易"

@function_tool
async def check_fund_availability(agent_id: str, amount: float) -> str:
    """檢查 Agent 資金是否充足"""
    # TODO: 實作資金驗證，整合帳戶系統
    return f"Agent {agent_id} 資金充足，可投資 {amount} TWD"

# 3. 創建交易 Agent 並配置工具
def create_trading_agent(agent_config: dict) -> Agent:
    """創建配置完整工具的交易 Agent"""

    trading_agent = Agent(
        name=agent_config["name"],
        model=agent_config["ai_model"],
        instructions=agent_config["strategy_prompt"],
        tools=[
            # 基礎工具
            get_stock_price,
            buy_taiwan_stock,
            sell_taiwan_stock,
            validate_trading_time,
            check_fund_availability,

            # OpenAI SDK 內建工具
            WebSearchTool(),  # 網路搜尋工具

            # 專業 Agent 作為工具
            research_agent.as_tool(
                tool_name="analyze_fundamentals",
                tool_description="分析股票基本面，包括財務狀況、成長潛力和投資價值評估"
            ),
            technical_agent.as_tool(
                tool_name="analyze_technicals",
                tool_description="分析股票技術面，包括技術指標、圖表型態和趨勢分析"
            ),
            risk_agent.as_tool(
                tool_name="assess_risk",
                tool_description="評估投資組合風險，提供部位控制和分散化建議"
            ),
        ]
    )

    return trading_agent

# 4. 使用範例
async def main():
    # 創建交易 Agent
    agent_config = {
        "name": "穩健投資者",
        "ai_model": "gpt-4o-mini",
        "strategy_prompt": "你是穩健型投資者，重視風險控制..."
    }

    trading_agent = create_trading_agent(agent_config)

    # 執行投資決策
    result = await Runner.run(
        trading_agent,
        "請分析台積電(2330)是否適合買入，我的投資組合目前有100萬現金"
    )

    print(result.final_output)

# 運行範例
import asyncio
asyncio.run(main())
```

### 架構優勢

1. **專業分工**：每個 Agent 專精特定領域，提供高品質分析
2. **模組化**：可以獨立開發、測試和優化每個專業 Agent
3. **可擴展性**：輕鬆添加新的專業 Agent（如總體經濟分析師）
4. **成本優化**：可為不同 Agent 選擇不同模型（分析用 GPT-4o，簡單任務用 GPT-4o-mini）
5. **重用性**：專業 Agent 可以被多個交易 Agent 共享使用

### 2. 即時交易監控系統

#### 2.1 實時數據流

- **WebSocket 事件類型**
  - `agent_status_update`: 代理人狀態變化
  - `trade_executed`: 交易執行通知
  - `portfolio_update`: 投資組合更新
  - `research_activity`: 研究活動記錄
  - `strategy_change`: 策略調整通知
  - `investment_rationale`: 投資決策原因記錄
  - `fund_verification`: 資金驗證結果
  - `trading_hours_check`: 交易時間驗證結果

#### 2.2 交易執行追蹤與驗證

- **交易前驗證**
  - 交易時間檢查：週一至週五 09:00-13:30（台灣時間）
  - 資金充足性驗證：確認買入前現金餘額足夠
  - 投資策略符合性檢查：單一持股比例限制
  - 風險評估：投資組合風險分析

- **買入/賣出操作**
  - 即時價格獲取（台灣證交所）
  - 手續費計算 (0.2% spread)
  - 交易確認與記錄
  - 投資原因持久化記錄
  - 前端動畫反饋

#### 2.3 投資決策追蹤

- **決策記錄系統**
  - 每筆交易記錄投資原因
  - AI 代理人決策過程記錄
  - 策略調整歷史追蹤
  - 市場分析結果保存
  - 工具使用記錄（WebSearch、金融研究員 Agent 等）

### 3. 視覺化儀表板

#### 3.1 主儀表板

- **代理人卡片**
  - 總資產、損益、現金餘額
  - 即時資產價值曲線圖
  - 持股分布顯示
  - 狀態指示燈（運行/停止/研究中）

#### 3.2 詳細模態視窗

- **資產變化圖表**
  - Chart.js 實現
  - 支援縮放和時間範圍選擇
  - 多條件篩選

- **持股詳情**
  - 股票代碼、名稱、持有數量
  - 平均成本、當前價格
  - 損益計算

- **交易歷史**
  - 時間序列顯示
  - 買入/賣出標記
  - 交易原因記錄

### 4. 台灣股市整合

#### 4.1 支援股票範圍

- **上市股票**: 4位數代碼 (如: 2330, 2317)
- **ETF**: 4-6位數 + 字母 (如: 0050, 00646)
- **熱門標的**: 台積電、鴻海、聯發科等

#### 4.2 市場資料

- **即時價格**: 透過 MCP 服務取得
- **公司資訊**: 名稱、產業分類
- **交易時間**: 台灣證交所營業時間

---

## 🏗️ 技術架構規格

### 1. 系統架構圖

```text
┌─────────────────────────────────────────────────────────┐
│                   前端層 (Frontend)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Vanilla JS  │ │ Chart.js    │ │ WebSocket Client    │  │
│  │ 儀表板+設定  │ │ 圖表視覺化   │ │ 即時通信            │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │ HTTP/WS
┌─────────────────────────────────────────────────────────┐
│                  Web 服務層 (Backend)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │  FastAPI    │ │ WebSocket   │ │ 靜態檔案服務         │  │
│  │  REST API   │ │ 即時推送    │ │ Static Files        │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │ 內部調用
┌─────────────────────────────────────────────────────────┐
│              AI 代理人層 (Agent Layer)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ OpenAI      │ │ SQLite      │ │ Tool Manager        │  │
│  │ Agent SDK   │ │ Session     │ │ 工具配置管理         │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Trading     │ │ Research    │ │ Risk Management     │  │
│  │ Agents      │ │ Agent       │ │ 風險控制            │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │ 工具調用
┌─────────────────────────────────────────────────────────┐
│                  工具層 (Tools Layer)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Market MCP  │ │ WebSearch   │ │ Trading Time        │  │
│  │ Server      │ │ Tool        │ │ Validator           │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Fund        │ │ Portfolio   │ │ Strategy            │  │
│  │ Validator   │ │ Manager     │ │ Manager             │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │ 資料存取
┌─────────────────────────────────────────────────────────┐
│                  資料層 (Data Layer)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Agent       │ │ Trading     │ │ Strategy &          │  │
│  │ Sessions    │ │ Records     │ │ Decision Logs       │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Portfolio   │ │ Market      │ │ Configuration       │  │
│  │ Data        │ │ Data Cache  │ │ Database            │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2. 技術堆疊

#### 2.1 後端技術

```yaml
Web框架: FastAPI 0.104+
AI代理人: OpenAI Agents SDK (Python)
會話管理: SQLiteSession (Agent SDK 內建)
資料庫: SQLite 3.x
通信協議: WebSocket, REST API
市場資料: MCP (Model Context Protocol)
非同步處理: asyncio, aiohttp
工具整合: MCP Tools, WebSearch, Custom Tools
```

#### 2.2 AI 代理人技術

```yaml
框架: OpenAI Agents Python SDK
支援模型:
  - OpenAI GPT-4o-mini
  - OpenAI GPT-4o
  - DeepSeek API
  - Grok API
  - Google Gemini API
會話持久化: SQLiteSession
多代理人協作: Agent Handoffs
工具調用: Function Calling
追蹤系統: Built-in Tracing
```

#### 2.3 前端技術

```yaml
核心框架: Vanilla JavaScript (ES2022+)
圖表庫: Chart.js 4.x
樣式框架: Tailwind CSS 3.x
字體: Inter + Noto Sans TC
即時通信: WebSocket API
模組系統: ES Modules
設定管理: 本地儲存 + 後端持久化
```

#### 2.4 外部服務與工具

```yaml
股價資料: 台灣證交所 API (透過 MCP)
研究工具: WebSearch API
金融分析: 金融研究員 Agent
技術分析: 自建技術指標工具
風險管理: 投資組合分析工具
時間驗證: 台灣交易時間檢查
資金驗證: 餘額檢查工具
```

### 3. 資料模型設計

#### 3.1 AI代理人模型

```python
from agents import Agent, SQLiteSession
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List

class TradingAgent(BaseModel):
    id: str
    name: str
    ai_model: str  # GPT-4o-mini, GPT-4o, DeepSeek, Grok, Gemini
    strategy_prompt: str  # 完整策略 prompt（來自前端輸入）
    color: str  # RGB values
    initial_balance: float
    current_balance: float
    portfolio_value: float
    status: AgentStatus  # running, stopped, researching, trading
    session_id: str  # SQLiteSession identifier（與資料庫整合）
    created_at: datetime
    last_active: datetime

class StrategyAdjustment(BaseModel):
    id: str
    agent_id: str
    timestamp: datetime
    old_prompt: str
    new_prompt: str
    reason: str
    agent_rationale: str
```

#### 3.2 交易記錄與決策模型

```python
class Transaction(BaseModel):
    id: str
    agent_id: str
    symbol: str
    company_name: str
    action: TradeAction  # BUY, SELL
    quantity: int
    price: float
    total_amount: float
    fees: float
    timestamp: datetime
    rationale: str  # AI 投資原因
    analysis_data: Dict[str, Any]  # 分析數據
    tools_used: List[str]  # 使用的工具記錄
    pre_trade_validation: PreTradeValidation

class PreTradeValidation(BaseModel):
    trading_hours_valid: bool
    fund_sufficient: bool
    risk_acceptable: bool
    strategy_compliant: bool
    validation_timestamp: datetime
    validation_details: Dict[str, Any]

class InvestmentDecision(BaseModel):
    id: str
    agent_id: str
    decision_type: str  # research, buy, sell, hold, strategy_adjust
    timestamp: datetime
    reasoning: str
    data_sources: List[str]  # WebSearch, 金融研究員Agent等
    market_context: Dict[str, Any]
    confidence_level: float  # 0.0 - 1.0

class Portfolio(BaseModel):
    agent_id: str
    holdings: Dict[str, HoldingInfo]
    cash_balance: float
    total_value: float
    risk_metrics: RiskMetrics
    last_updated: datetime

class HoldingInfo(BaseModel):
    symbol: str
    company_name: str
    quantity: int
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    percentage_of_portfolio: float
    purchase_rationale: List[str]  # 歷次買入原因

class RiskMetrics(BaseModel):
    concentration_risk: float  # 集中度風險
    sector_allocation: Dict[str, float]
    volatility_score: float
    diversification_score: float
```

#### 3.3 市場資料模型

```python
class StockPrice(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    timestamp: datetime

class MarketData(BaseModel):
    symbol: str
    company_name: str
    industry: str
    current_price: float
    day_high: float
    day_low: float
```

---

## 🔄 API 規格設計

### 1. REST API 端點

#### 1.1 代理人管理

```http
GET    /api/agents                    # 取得所有代理人
POST   /api/agents                    # 創建新代理人
GET    /api/agents/{id}               # 取得指定代理人
PUT    /api/agents/{id}               # 更新代理人設定
DELETE /api/agents/{id}               # 刪除代理人

POST   /api/agents/{id}/start         # 啟動代理人
POST   /api/agents/{id}/stop          # 停止代理人
PUT    /api/agents/{id}/strategy      # 更新策略
POST   /api/agents/{id}/reset         # 重置帳戶
```

#### 1.2 交易與帳戶

```http
GET    /api/agents/{id}/portfolio     # 取得投資組合
GET    /api/agents/{id}/transactions  # 取得交易歷史
GET    /api/agents/{id}/performance   # 取得績效數據
```

#### 1.3 市場資料

```http
GET    /api/market/stocks             # 取得股票清單
GET    /api/market/stocks/{symbol}    # 取得股票資訊
GET    /api/market/price/{symbol}     # 取得即時價格
```

### 2. WebSocket 事件規格

#### 2.1 事件類型定義

```typescript
interface WebSocketEvent {
  type:
    | "agent_status"
    | "trade_executed"
    | "portfolio_update"
    | "market_update";
  timestamp: string;
  data: any;
}

interface AgentStatusEvent {
  type: "agent_status";
  agent_id: string;
  status: "running" | "stopped" | "researching" | "trading";
  message?: string;
}

interface TradeExecutedEvent {
  type: "trade_executed";
  agent_id: string;
  trade: {
    action: "BUY" | "SELL";
    symbol: string;
    quantity: number;
    price: number;
    rationale: string;
  };
}
```

---

## 💻 用戶介面規格

### 1. 主儀表板設計

#### 1.1 布局結構

```
┌─────────────────────────────────────────────────────────┐
│                        標題列                           │
│          AI 股票交易模擬器 + 設定按鈕                    │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                      控制面板                           │
│     說明文字 + 全域控制按鈕 (全部啟動/停止)               │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                   代理人卡片網格                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Agent #1    │ │ Agent #2    │ │ Agent #3            │  │
│  │ 穩健型      │ │ 積極型      │ │ 平衡型              │  │
│  │ [圖表]      │ │ [圖表]      │ │ [圖表]              │  │
│  │ [持股清單]  │ │ [持股清單]  │ │ [持股清單]          │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### 1.2 代理人卡片元素

- **標題區域**: 代理人名稱 + 策略顏色
- **數據顯示**: 總資產、損益、現金餘額
- **圖表區域**: Chart.js 即時資產價值曲線
- **持股列表**: 當前持有股票的簡要信息
- **狀態指示**: 運行狀態的視覺指示器

### 2. 詳細模態視窗

#### 2.1 布局分割

```
┌─────────────────────────────────────────────────────────┐
│  標題: Agent名稱 (策略色彩) + 關閉按鈕                    │
├─────────────────────────────────────────────────────────┤
│ ┌───────────────────────┐ ┌─────────────────────────────┐ │
│ │     圖表與數據區      │ │        持股與歷史區         │ │
│ │                       │ │                             │ │
│ │  ┌─────────────────┐   │ │  ┌─────────────────────┐    │ │
│ │  │ 總資產|損益|現金 │   │ │  │      持有股票       │    │ │
│ │  └─────────────────┘   │ │  │  - 2330 台積電      │    │ │
│ │                       │ │  │  - 2317 鴻海        │    │ │
│ │  ┌─────────────────┐   │ │  └─────────────────────┘    │ │
│ │  │                 │   │ │                             │ │
│ │  │   Chart.js圖表  │   │ │  ┌─────────────────────┐    │ │
│ │  │                 │   │ │  │      交易歷史       │    │ │
│ │  └─────────────────┘   │ │  │  [時間] BUY 2330    │    │ │
│ └───────────────────────┘ │  │  [時間] SELL 2317   │    │ │
│                           │  └─────────────────────┘    │ │
│                           └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3. 設定管理介面 (基於前端原型)

#### 3.1 Agent 管理功能

- **Agent 列表**: 顯示所有已創建的 Agent 及其狀態
- **編輯功能**: 修改 Agent 配置
- **刪除功能**: 移除 Agent 及其所有資料
- **新增功能**: 創建新的 AI Agent

#### 3.2 新增/編輯 Agent 表單

```text
┌─────────────────────────────────────────┐
│              新增/編輯 AI Agent           │
├─────────────────────────────────────────┤
│  Agent 名稱: [輸入框]                    │
│  AI 模型:    [下拉選單] GPT-4o-mini     │
│                ○ GPT-4o-mini           │
│                ○ GPT-4o                │
│                ○ DeepSeek              │
│                ○ Grok                  │
│                ○ Gemini                │
├─────────────────────────────────────────┤
│  策略 Prompt: [大型文字框]               │
│  [預設模板] [穩健型] [積極型] [價值投資]  │
│                                         │
│  你是一位專業的投資者...                │
│  (支援完全自訂投資策略描述)              │
├─────────────────────────────────────────┤
│  主體顏色:   [顏色選擇器] #22C55E        │
│  初始資金:   [數字輸入] 1,000,000 TWD   │
├─────────────────────────────────────────┤
│  工具配置: 所有可用工具 (自動配置)        │
│  • Market MCP Server                   │
│  • WebSearch Tool                      │
│  • 金融研究員 Agent                     │
│  • 交易驗證工具                         │
├─────────────────────────────────────────┤
│          [重設 Prompt] [取消] [儲存]      │
└─────────────────────────────────────────┘
```

#### 3.3 策略歷史追蹤

```text
┌─────────────────────────────────────────┐
│            Agent 策略調整歷史             │
├─────────────────────────────────────────┤
│  [2025-01-10 14:30] 策略自主調整         │
│  變更原因: 市場波動加劇，降低風險偏好    │
│  AI 分析: 基於近期技術指標和市場數據...  │
│  [查看完整 Prompt 變更]                 │
├─────────────────────────────────────────┤
│  [2025-01-08 10:15] 手動策略重設         │
│  變更原因: 使用者重設為穩健型模板        │
│  [查看變更詳情]                         │
├─────────────────────────────────────────┤
│              [匯出歷史] [重設為初始 Prompt] │
└─────────────────────────────────────────┘
```

---

## 📱 響應式設計規格

### 1. 斷點設定

```css
/* 手機版 */
@media (max-width: 768px) {
  .agent-grid {
    grid-template-columns: 1fr;
  }
}

/* 平板版 */
@media (min-width: 769px) and (max-width: 1024px) {
  .agent-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 桌面版 */
@media (min-width: 1025px) {
  .agent-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### 2. 互動設計

- **懸停效果**: 卡片邊框高亮
- **點擊反饋**: 按鈕按下動畫
- **載入狀態**: 骨架屏顯示
- **交易動畫**: 閃爍效果表示交易執行

---

## 🚀 開發里程碑

### Phase 0: Hosted Tools POC 研究 (Week 0)

**目標**: 驗證 OpenAI Agent SDK Hosted Tools 在金融交易場景的可行性

#### 0.1 工具能力驗證研究

**CodeInterpreterTool 金融計算驗證**：

- [ ] 測試 Python 金融套件支援度（pandas, numpy, talib）
- [ ] 驗證技術指標計算能力（RSI, MACD, 布林通道）
- [ ] 測試股價數據處理和視覺化功能
- [ ] 評估執行時間限制和性能表現
- [ ] 測試數據持久化能力

**FileSearchTool 中文金融內容檢索驗證**：

- [ ] 建立測試用 Vector Store（台灣公司財報、研究報告）
- [ ] 測試中文金融內容的檢索準確度
- [ ] 評估檔案格式支援（PDF財報、Excel數據）
- [ ] 分析語義搜尋效果和相關性評分
- [ ] 評估建置和維護成本

**HostedMCPTool 外部服務整合研究**：

- [ ] 調研支援 MCP 協議的金融數據提供商
- [ ] 測試外部 API 認證和安全機制
- [ ] 驗證數據格式標準化可能性
- [ ] 評估服務延遲和可靠性指標
- [ ] 分析整合複雜度和維護成本

**LocalShellTool 安全性評估**：

- [ ] 分析 AI Agent 執行 shell 命令的安全風險
- [ ] 研究權限控制和命令範圍限制機制
- [ ] 測試跨平台相容性問題
- [ ] 評估在生產環境部署的可行性

#### 0.2 工具組合效果測試

- [ ] 建立 POC 測試環境
- [ ] 設計複合任務測試案例
- [ ] 測試多工具協作的實際效果
- [ ] 評估工具間數據傳遞的效率
- [ ] 分析錯誤處理和降級機制

#### 0.3 成本效益分析

- [ ] 計算 hosted tools 的使用成本
- [ ] 評估開發和維護工作量
- [ ] 與現有 custom tools 進行效能比較
- [ ] 制定工具導入的優先順序和策略

#### 0.4 技術架構調整

- [ ] 根據 POC 結果更新系統架構設計
- [ ] 調整 Agent 工具配置策略
- [ ] 更新風險控制和安全機制
- [ ] 制定分階段導入計畫

**預期產出**：

- Hosted Tools 可行性評估報告
- 工具能力對照表和限制說明
- 更新的技術架構設計
- Phase 1-6 開發計畫調整建議

### Phase 1: OpenAI Agent SDK 基礎整合 (Week 1-2)

- [ ] 設置 OpenAI Agents Python SDK 環境
- [ ] 實現 SQLiteSession 會話管理系統
- [ ] 建立基礎 Agent 框架和工具管理器
- [ ] 整合現有 Market MCP Server 作為 Agent 工具
- [ ] 實現交易時間和資金驗證工具

### Phase 2: AI 代理人核心功能 (Week 3-4)

- [ ] 實現交易代理人核心邏輯
- [ ] 建立投資策略系統（穩健型、積極型等）
- [ ] 整合 WebSearch 工具和金融研究員 Agent
- [ ] 實現決策記錄和投資原因持久化
- [ ] 建立風險評估和投資組合管理系統

### Phase 3: Web 服務層與前端基礎 (Week 5)

- [ ] 建立 FastAPI 後端服務架構
- [ ] 實現 WebSocket 即時通信系統
- [ ] 建立前端基礎結構（Vanilla JS + Tailwind）
- [ ] 實現代理人 CRUD API
- [ ] 建立基本的儀表板界面

### Phase 4: 前端進階功能與設定界面 (Week 6)

- [ ] 實現 AI 模型選擇界面
- [ ] 建立策略配置和歷史追蹤功能
- [ ] 實現工具配置管理界面
- [ ] 整合 Chart.js 圖表視覺化
- [ ] 添加即時交易動畫效果

### Phase 5: 進階分析與優化 (Week 7-8)

- [ ] 實現策略動態調整功能
- [ ] 建立多代理人協作機制
- [ ] 添加效能分析和回測功能
- [ ] 實現風險控制和預警系統
- [ ] 優化用戶體驗和響應式設計

### Phase 6: 生產部署與監控 (Week 9+)

- [ ] 實現系統監控和日誌記錄
- [ ] 建立自動化測試套件
- [ ] 部署配置和 CI/CD 設置
- [ ] 效能優化和壓力測試
- [ ] 文檔完善和使用者指南

---

## 🔧 技術實現細節

### 1. 專案目錄結構

```text
CasualTrader/
├── src/                        # 主要原始碼目錄
│   ├── agent/                  # AI 代理人層
│   │   ├── __init__.py
│   │   ├── trading_agent.py    # 交易代理人核心
│   │   ├── research_agent.py   # 金融研究員代理人
│   │   ├── agent_manager.py    # 代理人管理器
│   │   ├── session_manager.py  # SQLiteSession 管理
│   │   ├── prompts/            # 策略 Prompt Templates
│   │   │   ├── conservative_strategy.txt    # 穩健型策略
│   │   │   ├── aggressive_strategy.txt      # 積極型策略
│   │   │   ├── balanced_strategy.txt        # 平衡型策略
│   │   │   ├── value_investing.txt          # 價值投資策略
│   │   │   └── momentum_trading.txt         # 動量交易策略
│   │   ├── specialist_agents/  # 專業功能 Agent (Agent-as-Tool)
│   │   │   ├── __init__.py
│   │   │   ├── research_agent.py      # 金融研究員 Agent
│   │   │   ├── technical_agent.py     # 技術分析師 Agent
│   │   │   └── risk_agent.py          # 風險評估師 Agent
│   │   └── tools/              # 基礎工具集
│   │       ├── __init__.py
│   │       ├── market_tools.py        # 市場 MCP 工具包裝
│   │       ├── validation_tools.py    # 驗證工具 (時間、資金)
│   │       └── portfolio_tools.py     # 投資組合管理工具
│   ├── backend/                # Web 服務層
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 應用入口
│   │   ├── api/               # REST API 路由
│   │   │   ├── __init__.py
│   │   │   ├── agents.py      # 代理人 API
│   │   │   ├── trading.py     # 交易 API
│   │   │   ├── portfolio.py   # 投資組合 API
│   │   │   └── settings.py    # 設定 API
│   │   ├── websocket/         # WebSocket 處理
│   │   │   ├── __init__.py
│   │   │   ├── connection.py  # 連線管理
│   │   │   ├── events.py      # 事件處理
│   │   │   └── handlers.py    # 事件處理器
│   │   ├── models/            # 資料模型
│   │   │   ├── __init__.py
│   │   │   ├── agent.py       # 代理人模型
│   │   │   ├── trading.py     # 交易模型
│   │   │   ├── portfolio.py   # 投資組合模型
│   │   │   └── market.py      # 市場資料模型
│   │   ├── services/          # 業務邏輯服務
│   │   │   ├── __init__.py
│   │   │   ├── agent_service.py # 代理人服務
│   │   │   ├── trading_service.py # 交易服務
│   │   │   └── validation_service.py # 驗證服務
│   │   └── database/          # 資料庫操作
│   │       ├── __init__.py
│   │       ├── connection.py  # 資料庫連線
│   │       ├── models.py      # SQLAlchemy 模型
│   │       └── repositories.py # 資料存取層
│   └── frontend/              # 前端應用
│       ├── index.html         # 主儀表板頁面
│       ├── settings.html      # 設定頁面
│       ├── js/                # JavaScript 模組
│       │   ├── main.js        # 主要應用邏輯
│       │   ├── agents.js      # 代理人管理
│       │   ├── dashboard.js   # 儀表板功能
│       │   ├── settings.js    # 設定管理
│       │   ├── charts.js      # 圖表功能
│       │   ├── websocket.js   # WebSocket 客戶端
│       │   └── utils.js       # 工具函數
│       ├── css/               # 樣式檔案
│       │   ├── main.css       # 主要樣式
│       │   ├── dashboard.css  # 儀表板樣式
│       │   ├── settings.css   # 設定頁面樣式
│       │   └── components.css # 組件樣式
│       └── assets/            # 靜態資源
│           ├── icons/         # 圖標檔案
│           ├── images/        # 圖片資源
│           └── fonts/         # 字體檔案
├── market_mcp/                # MCP Server (現有)
│   └── ...                    # 現有 MCP 服務代碼
├── tests/                     # 測試檔案
│   ├── test_agents/
│   ├── test_backend/
│   └── test_integration/
├── docs/                      # 文件
├── scripts/                   # 部署與工具腳本
└── requirements.txt           # Python 依賴
```

### 2. 環境設定

```bash
# 核心依賴
fastapi[all]>=0.104.0
openai-agents-python>=0.2.9
websockets>=11.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
sqlalchemy>=2.0.0

# AI 模型 SDK
openai>=1.0.0
anthropic>=0.8.0  # 如果使用 Claude
requests>=2.31.0  # WebSearch 工具

# 時間與驗證
python-dateutil>=2.8.0
pytz>=2023.3  # 台灣時區支援

# 開發工具
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.5.0

# 測試工具
httpx>=0.25.0  # FastAPI 測試客戶端
pytest-mock>=3.11.0
```

### 3. Agent 工具配置規格

#### 3.1 工具註冊與管理

```python
from agents import Agent
from typing import List, Dict, Any

class ToolManager:
    """代理人工具管理器"""

    def __init__(self):
        self.available_tools = {
            "market_mcp": MarketMCPTool(),
            "websearch": WebSearchTool(),
            "research_agent": ResearchAgentTool(),
            "fund_validator": FundValidatorTool(),
            "time_validator": TimeValidatorTool(),
            "risk_calculator": RiskCalculatorTool(),
            "portfolio_manager": PortfolioManagerTool(),
            "strategy_advisor": StrategyAdvisorTool()
        }

    def configure_agent_tools(self, agent: Agent, tool_config: List[Dict[str, Any]]):
        """為代理人配置工具"""
        for config in tool_config:
            tool_name = config["tool_name"]
            if tool_name in self.available_tools and config["enabled"]:
                tool = self.available_tools[tool_name]
                tool.configure(config.get("config", {}))
                agent.add_tool(tool)

class MarketMCPTool:
    """Market MCP Server 工具包裝"""

    def __init__(self):
        self.name = "market_data"
        self.description = "台灣股票市場數據查詢與交易執行"

    async def get_stock_price(self, symbol: str) -> dict:
        """取得股票即時價格"""
        # 呼叫現有的 market-mcp-server
        pass

    async def execute_trade(self, symbol: str, action: str, quantity: int) -> dict:
        """執行股票交易"""
        # 整合交易驗證與執行邏輯
        pass

class WebSearchTool:
    """網路搜尋工具"""

    def __init__(self):
        self.name = "web_search"
        self.description = "搜尋網路上的股市相關資訊"

    async def search_market_news(self, query: str) -> List[dict]:
        """搜尋市場新聞"""
        pass

    async def search_company_info(self, symbol: str) -> dict:
        """搜尋公司基本資訊"""
        pass
```

#### 3.2 交易時間與資金驗證工具

```python
import pytz
from datetime import datetime, time

class TimeValidatorTool:
    """交易時間驗證工具"""

    def __init__(self):
        self.taiwan_tz = pytz.timezone('Asia/Taipei')
        self.trading_start = time(9, 0)    # 09:00
        self.trading_end = time(13, 30)    # 13:30
        self.trading_days = [0, 1, 2, 3, 4]  # 週一到週五

    async def validate_trading_time(self) -> dict:
        """驗證當前是否為交易時間"""
        now = datetime.now(self.taiwan_tz)

        is_trading_day = now.weekday() in self.trading_days
        is_trading_hours = self.trading_start <= now.time() <= self.trading_end

        return {
            "is_valid": is_trading_day and is_trading_hours,
            "current_time": now.isoformat(),
            "is_trading_day": is_trading_day,
            "is_trading_hours": is_trading_hours,
            "next_trading_session": self._get_next_trading_session(now)
        }

class FundValidatorTool:
    """資金驗證工具"""

    async def validate_purchase_funds(self, agent_id: str, symbol: str,
                                    quantity: int, price: float) -> dict:
        """驗證買入資金是否充足"""
        # 計算所需資金（含手續費）
        total_cost = quantity * price * 1.002  # 0.2% 手續費

        # 查詢代理人現金餘額
        portfolio = await self.get_agent_portfolio(agent_id)
        cash_balance = portfolio.cash_balance

        return {
            "is_sufficient": cash_balance >= total_cost,
            "required_amount": total_cost,
            "available_cash": cash_balance,
            "shortfall": max(0, total_cost - cash_balance)
        }
```

### 3. 部署配置

```yaml
# docker-compose.yml
version: "3.8"
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./accounts.db
    volumes:
      - ./data:/app/data
```

---

## 📊 效能與監控

### 1. 效能指標

- **WebSocket 延遲**: < 100ms
- **API 響應時間**: < 500ms
- **並發用戶**: 支援 100+ 同時連線
- **資料更新頻率**: 每 5 秒一次

### 2. 監控機制

- **應用程式監控**: 記錄 API 呼叫和錯誤
- **AI 代理人監控**: 追蹤決策時間和成功率
- **交易監控**: 記錄所有交易操作
- **系統資源監控**: CPU、記憶體使用情況

### 3. 錯誤處理

- **API 錯誤**: 標準化錯誤響應格式
- **WebSocket 斷線**: 自動重連機制
- **AI 代理人錯誤**: 優雅降級和錯誤報告
- **資料庫錯誤**: 事務回滾和資料一致性

---

## 🔒 安全性考量

### 1. 資料安全

- **輸入驗證**: 所有用戶輸入進行驗證
- **SQL 注入防護**: 使用參數化查詢
- **XSS 防護**: 輸出編碼和 CSP 設定

### 2. API 安全

- **CORS 設定**: 限制允許的來源
- **Rate Limiting**: API 呼叫頻率限制
- **驗證機制**: 基本的身份驗證（未來擴展）

### 3. 資料隱私

- **日誌管理**: 不記錄敏感資訊
- **資料清理**: 定期清理過期資料
- **備份策略**: 定期備份重要資料

---

## 📄 附錄

### A. 參考資料

- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [Chart.js 官方指南](https://www.chartjs.org/docs/)
- [WebSocket API 規範](https://websockets.spec.whatwg.org/)
- [台灣證交所 API](https://www.twse.com.tw/)

### B. 術語定義

- **AI 代理人**: 使用人工智能進行交易決策的自動化程式
- **MCP**: Model Context Protocol，用於模型間通信的協議
- **WebSocket**: 雙向通信協議，用於即時資料推送
- **Chart.js**: JavaScript 圖表庫

### C. 變更記錄

| 版本 | 日期       | 變更內容 | 作者   |
| ---- | ---------- | -------- | ------ |
| 1.0  | 2025-01-10 | 初始版本 | Claude |

---

**文件狀態**: 🔄 待確認
**下一步**: 等待確認後開始 Phase 1 開發
