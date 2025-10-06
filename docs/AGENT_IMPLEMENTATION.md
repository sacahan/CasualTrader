# Agent 系統實作規格

**版本**: 2.0
**日期**: 2025-10-06
**相關設計**: SYSTEM_DESIGN.md
**基於**: OpenAI Agents SDK

---

## 📋 概述

本文檔定義 CasualTrader AI 股票交易模擬器中 Agent 系統的實作規格，採用 OpenAI Agents SDK 的 **Agent as Tool** 架構：

1. **TradingAgent 主體** - 協調所有交易決策的中央Agent
2. **專門化 Agent Tools** - 基本面分析、技術分析、風險評估等子Agent作為tool
3. **OpenAI Hosted Tools** - WebSearchTool、CodeInterpreterTool等內建工具
4. **交易驗證 Function Tools** - 開盤時間、持倉查詢、現金查詢等獨立工具
5. **前端管理介面** - Agent創建、配置和監控的Web界面

---

## 🤖 TradingAgent 主體架構

### 設計理念

TradingAgent 作為中央協調者，透過 OpenAI Agents SDK 的 `as_tool()` 功能整合多個專門化Agent和工具，形成完整的交易決策系統。

### Agent as Tool 架構

```python
from agents import Agent, Runner, WebSearchTool, CodeInterpreterTool

# 主要TradingAgent
trading_agent = Agent(
    name="Trading Agent",
    instructions="You are a sophisticated trading agent...",
    tools=[
        # 專門化 Agent Tools
        fundamental_agent.as_tool(
            tool_name="fundamental_analysis",
            tool_description="Analyze company fundamentals and financial health"
        ),
        technical_agent.as_tool(
            tool_name="technical_analysis",
            tool_description="Perform technical analysis and chart patterns"
        ),
        risk_agent.as_tool(
            tool_name="risk_assessment",
            tool_description="Evaluate portfolio risk and position sizing"
        ),

        # OpenAI Hosted Tools
        WebSearchTool(),
        CodeInterpreterTool(),

        # CasualTrader MCP Tools (透過HostedMCPTool整合)
        get_taiwan_stock_price,
        buy_taiwan_stock,
        sell_taiwan_stock,

        # 交易驗證 Function Tools
        check_trading_hours,
        get_current_holdings,
        get_available_cash,
        validate_trade_parameters,
    ],
    model="gpt-4",
    max_turns=50
)
```

### 三種執行模式

TradingAgent 根據市場條件和用戶設定動態調整執行策略：

**TRADING 模式** - 主動交易決策

- 調用所有分析Agent Tools獲取市場洞察
- 使用WebSearchTool獲取最新市場新聞
- 執行買賣決策並追蹤績效

**REBALANCING 模式** - 投資組合調整

- 重點使用風險評估和現金查詢工具
- 調整持股配置以符合目標分配
- 考慮交易成本和稅務優化

**OBSERVATION 模式** - 純分析不交易

- 只使用分析類工具，不執行交易
- 建立觀察清單和市場研究報告
- 提供投資建議但不採取行動

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
- `enable_tracing`: 是否啟用追蹤 (預設: true)
- `trace_retention_days`: 追蹤保留天數 (預設: 30天)

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

### 輕量級操作記錄

**AgentTrace** 表結構:

- trace*id (格式: `{agent_id}*{mode}\_{timestamp}`)
- agent_id, mode, timestamp, execution_time
- final_output, tools_called, error_message
- 保留天數可配置 (預設 30 天)

### 追蹤操作

**基本功能**:

- 自動記錄 Agent 執行開始和結束時間
- 記錄最終輸出和調用的工具列表
- 錯誤情況下記錄異常訊息

**查詢功能**:

- 按 Agent ID 查詢歷史記錄
- 按模式過濾追蹤記錄
- 提供統計資訊 (成功率、平均執行時間、最常用工具)

---

## 🧠 專門化 Agent Tools

### 基本面分析 Agent Tool

```python
from agents import Agent, function_tool

# CasualTrader MCP 工具整合
@function_tool
async def get_company_fundamentals(symbol: str) -> dict:
    """Get comprehensive company fundamental data"""
    return await mcp_client.call_tool("get_company_profile", {"symbol": symbol})

fundamental_agent = Agent(
    name="Fundamental Analysis Agent",
    instructions="""
    You are a fundamental analysis expert for Taiwan stock market.
    Analyze company financial health, business model, and growth prospects.

    Key analysis areas:
    - Financial statement analysis (revenue, profit, debt ratios)
    - Business model and competitive advantages
    - Industry trends and market position
    - Management quality and corporate governance
    - Valuation metrics (P/E, P/B, ROE, etc.)

    Provide clear buy/hold/sell recommendations with rationale.
    """,
    tools=[
        # CasualTrader MCP Tools 作為 function_tool 包裝
        get_company_fundamentals,
        get_company_income_statement,
        get_company_balance_sheet,
        get_company_monthly_revenue,
        get_stock_valuation_ratios,
        get_company_dividend,
    ],
    model="gpt-4"
)
```

### 技術分析 Agent Tool

```python
technical_agent = Agent(
    name="Technical Analysis Agent",
    instructions="""
    You are a technical analysis expert specializing in Taiwan stock market.
    Use CodeInterpreterTool to perform advanced technical analysis.

    Analysis capabilities:
    - Chart pattern recognition (head & shoulders, triangles, flags)
    - Technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
    - Volume analysis and momentum indicators
    - Support and resistance levels
    - Trend analysis and breakout detection

    Generate trading signals with entry/exit points and stop-loss levels.
    """,
    tools=[
        CodeInterpreterTool(),  # 用於技術分析計算和圖表生成
        get_stock_daily_trading,
        get_stock_monthly_trading,
        get_stock_monthly_average,
    ],
    model="gpt-4"
)
```

### 風險評估 Agent Tool

```python
risk_agent = Agent(
    name="Risk Assessment Agent",
    instructions="""
    You are a risk management specialist for portfolio optimization.

    Risk evaluation areas:
    - Portfolio diversification analysis
    - Position sizing and concentration risk
    - Market volatility and correlation analysis
    - Drawdown and Value-at-Risk calculations
    - Sector and geographical exposure
    - Liquidity risk assessment

    Recommend position sizing and risk mitigation strategies.
    """,
    tools=[
        CodeInterpreterTool(),  # 風險計算和統計分析
        get_current_portfolio,
        get_market_index_info,
        get_foreign_investment_by_industry,
        get_margin_trading_info,
    ],
    model="gpt-4"
)
```

### 市場情緒分析 Agent Tool

```python
sentiment_agent = Agent(
    name="Market Sentiment Agent",
    instructions="""
    You are a market sentiment and news analysis expert.
    Monitor market mood and external factors affecting Taiwan stocks.

    Analysis focus:
    - Recent news and market developments
    - Foreign investment flows and institutional activity
    - Market breadth and sentiment indicators
    - Economic data and policy changes
    - Sector rotation and market themes

    Provide market sentiment scoring and timing recommendations.
    """,
    tools=[
        WebSearchTool(),  # 搜尋最新市場新聞和分析
        get_real_time_trading_stats,
        get_top_foreign_holdings,
        get_foreign_investment_by_industry,
        get_etf_regular_investment_ranking,
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
                "symbol": holding.symbol,
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
    symbol: str,
    action: str,
    quantity: int,
    price: float = None
) -> dict:
    """Validate trading parameters before execution"""

    # 股票代碼驗證
    if not re.match(r'^\d{4}[A-Z]?$', symbol):
        return {"valid": False, "error": "Invalid stock symbol format"}

    # 交易數量驗證 (台股最小單位1000股)
    if quantity % 1000 != 0:
        return {"valid": False, "error": "Quantity must be multiple of 1000 shares"}

    # 價格驗證
    if price is not None and price <= 0:
        return {"valid": False, "error": "Price must be positive"}

    # 漲跌停價格檢查
    current_data = await get_taiwan_stock_price(symbol)
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

---

## 🛠️ CasualTrader MCP工具整合

### HostedMCPTool 設定

````python
from agents import HostedMCPTool

# 整合 CasualTrader MCP Server
casualtrader_mcp = HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "casualtrader",
        "server_url": "uvx://casualtrader/market-mcp-server",
        "require_approval": "never",
    }
)

# TradingAgent 可使用的 CasualTrader 工具：

### 核心交易工具

**股票價格查詢**

```python
# 工具: get_taiwan_stock_price
# 用途: 獲取即時股票價格和交易資訊
response = await mcp_client.call_tool("get_taiwan_stock_price", {
    "symbol": "2330"  # 台積電
})
# 返回: 即時價格、漲跌幅、成交量、五檔報價等
````

**模擬交易執行**

```python
# 工具: buy_taiwan_stock
# 用途: 模擬股票買入操作
response = await mcp_client.call_tool("buy_taiwan_stock", {
    "symbol": "2330",
    "quantity": 1000,  # 1張
    "price": None      # 市價單
})

# 工具: sell_taiwan_stock
# 用途: 模擬股票賣出操作
response = await mcp_client.call_tool("sell_taiwan_stock", {
    "symbol": "2330",
    "quantity": 1000,
    "price": 520.0     # 限價單
})
```

### 基本面分析工具

**公司基本資料**

```python
# 工具: get_company_profile
# 用途: 獲取公司基本資訊、產業分類、主要業務
response = await mcp_client.call_tool("get_company_profile", {
    "symbol": "2330"
})
```

**財務報表工具**

```python
# 工具: get_company_income_statement
# 用途: 獲取綜合損益表數據
income_data = await mcp_client.call_tool("get_company_income_statement", {
    "symbol": "2330"
})

# 工具: get_company_balance_sheet
# 用途: 獲取資產負債表數據
balance_data = await mcp_client.call_tool("get_company_balance_sheet", {
    "symbol": "2330"
})

# 工具: get_company_monthly_revenue
# 用途: 獲取月營收資料
revenue_data = await mcp_client.call_tool("get_company_monthly_revenue", {
    "symbol": "2330"
})
```

**估值分析工具**

```python
# 工具: get_stock_valuation_ratios
# 用途: 獲取本益比、股價淨值比、殖利率等估值指標
valuation = await mcp_client.call_tool("get_stock_valuation_ratios", {
    "symbol": "2330"
})
```

### 市場數據工具

**交易統計工具**

```python
# 工具: get_stock_daily_trading
# 用途: 獲取日交易資訊
daily_stats = await mcp_client.call_tool("get_stock_daily_trading", {
    "symbol": "2330"
})

# 工具: get_real_time_trading_stats
# 用途: 獲取即時交易統計(5分鐘資料)
realtime_stats = await mcp_client.call_tool("get_real_time_trading_stats")
```

**市場指數工具**

```python
# 工具: get_market_index_info
# 用途: 獲取大盤指數資訊
market_index = await mcp_client.call_tool("get_market_index_info", {
    "category": "major",
    "count": 20
})
```

### Agent中的MCP工具使用範例

**分析Agent使用範例**

```python
class AnalysisAgent:
    async def analyze_stock_fundamentals(self, symbol: str):
        # 獲取基本資料
        profile = await self.call_mcp_tool("get_company_profile", {"symbol": symbol})

        # 獲取財務數據
        income = await self.call_mcp_tool("get_company_income_statement", {"symbol": symbol})
        balance = await self.call_mcp_tool("get_company_balance_sheet", {"symbol": symbol})

        # 獲取估值指標
        valuation = await self.call_mcp_tool("get_stock_valuation_ratios", {"symbol": symbol})

        # 綜合分析邏輯
        return self._combine_fundamental_analysis(profile, income, balance, valuation)
```

**執行Agent使用範例**

```python
class ExecutionAgent:
    async def execute_trade_decision(self, decision: TradeDecision):
        # 獲取即時價格
        price_data = await self.call_mcp_tool("get_taiwan_stock_price", {
            "symbol": decision.symbol
        })

        # 執行交易
        if decision.action == "BUY":
            result = await self.call_mcp_tool("buy_taiwan_stock", {
                "symbol": decision.symbol,
                "quantity": decision.quantity,
                "price": decision.target_price
            })
        elif decision.action == "SELL":
            result = await self.call_mcp_tool("sell_taiwan_stock", {
                "symbol": decision.symbol,
                "quantity": decision.quantity,
                "price": decision.target_price
            })

        return result
```

### 錯誤處理和重試機制

**MCP工具調用的統一錯誤處理**

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

## 🔄 實作架構

### 核心工作流程

1. **載入配置** - 從 SQLite 讀取 Agent 設定
2. **檢查模式切換** - 根據自動條件或手動請求
3. **創建 Agent 實例** - 使用 OpenAI Agent SDK
4. **執行交易決策** - 根據當前模式執行對應策略
5. **記錄追蹤資料** - 儲存執行結果到 SQLite
6. **更新狀態** - 同步投資組合和模式狀態

---

## 📁 檔案結構

```
src/agents/
├── trading_agent.py           # 主TradingAgent實作
├── agent_tools/               # 專門化Agent Tools
│   ├── fundamental_agent.py   # 基本面分析Agent Tool
│   ├── technical_agent.py     # 技術分析Agent Tool
│   ├── risk_agent.py         # 風險評估Agent Tool
│   └── sentiment_agent.py     # 市場情緒分析Agent Tool
├── function_tools/            # 交易驗證Function Tools
│   ├── trading_validation.py  # 交易參數驗證
│   ├── market_status.py       # 市場狀態檢查
│   └── portfolio_queries.py   # 投資組合查詢
├── mcp_integration/           # CasualTrader MCP整合
│   ├── hosted_mcp_setup.py   # HostedMCPTool設定
│   └── mcp_function_wrappers.py # MCP工具Function包裝
├── frontend_api/              # 前端管理API
│   ├── agent_management.py   # Agent CRUD操作
│   ├── agent_monitoring.py   # 狀態監控API
│   └── websocket_service.py  # 即時通知服務
├── config_manager.py          # SQLite 配置管理
├── trace_logger.py            # 執行追蹤記錄
└── models.py                 # 資料模型定義

frontend/src/
├── components/agents/         # Agent管理組件
│   ├── AgentCreationForm.tsx  # Agent創建表單
│   ├── AgentDashboard.tsx     # Agent監控儀表板
│   └── AgentConfigEditor.tsx  # Agent配置編輯器
├── services/
│   ├── AgentAPI.ts           # Agent管理API客戶端
│   └── NotificationService.ts # WebSocket通知服務
└── types/
    └── agent.ts              # Agent相關TypeScript類型定義
```

---

## ✅ 實作檢查清單

### 主 TradingAgent 架構

- [ ] TradingAgent 基礎架構實作
- [ ] 三種執行模式 (TRADING/REBALANCING/OBSERVATION)
- [ ] Agent Tool 整合機制
- [ ] OpenAI Agents SDK 整合
- [ ] SQLite 配置管理和持久化

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

### CasualTrader MCP 整合

- [ ] HostedMCPTool 設定
- [ ] CasualTrader MCP Server 連接
- [ ] MCP工具Function包裝器
- [ ] MCP工具錯誤處理和重試機制

### 前端 Agent 管理介面

- [ ] Agent 創建表單 (`AgentCreationForm.tsx`)
- [ ] Agent 監控儀表板 (`AgentDashboard.tsx`)
- [ ] Agent 配置編輯器 (`AgentConfigEditor.tsx`)
- [ ] Agent 管理 API (`AgentAPI.ts`)
- [ ] WebSocket 即時通知服務

### 進階功能

- [ ] 即時狀態監控和通知
- [ ] 決策結果可解釋性
- [ ] 投資組合績效追蹤
- [ ] 風險管理和停損機制
- [ ] Agent 執行歷史和審計
- [ ] 多Agent並行執行和資源管理

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
