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

        # CasualMarket MCP Tools (透過外部MCP服務整合)
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

### 台股交易時間限定的四種執行模式系統

TradingAgent 嚴格遵循台股交易時間，採用四種智能模式在交易時段循環運作：

#### 台股交易時間模式架構

**核心設計理念**：

- 模式切換完全配合台股交易時間（週一至週五 09:00-13:30）
- 交易時間外進行深度分析和策略優化
- 非交易日執行週度策略檢討

**交易日時間分配**：

- **08:30-09:00 (30分鐘)**: 開盤前準備 (OBSERVATION)
- **09:00-11:00 (120分鐘)**: 早盤交易 (TRADING)
- **11:00-11:30 (30分鐘)**: 中場調整 (REBALANCING)
- **11:30-13:00 (90分鐘)**: 午盤交易 (TRADING)
- **13:00-13:30 (30分鐘)**: 收盤檢討 (STRATEGY_REVIEW)

#### 台股交易時間狀態機架構

```python
from enum import Enum
from datetime import datetime, timedelta, time
import pytz

class AgentMode(Enum):
    # 交易時間模式
    OBSERVATION = "OBSERVATION"           # 開盤前準備
    TRADING = "TRADING"                   # 主動交易
    REBALANCING = "REBALANCING"           # 中場調整
    STRATEGY_REVIEW = "STRATEGY_REVIEW"   # 收盤檢討

    # 非交易時間模式
    DEEP_OBSERVATION = "DEEP_OBSERVATION"  # 深度分析
    WEEKLY_REVIEW = "WEEKLY_REVIEW"        # 週末檢討
    STANDBY = "STANDBY"                    # 待機模式

class TaiwanStockTradingTimeManager:
    """台股交易時間管理器"""

    def __init__(self):
        self.taiwan_tz = pytz.timezone('Asia/Taipei')
        self.trading_schedule = {
            'pre_market': {
                'start': time(8, 30),
                'end': time(9, 0),
                'mode': AgentMode.OBSERVATION,
                'duration': timedelta(minutes=30)
            },
            'morning_trading': {
                'start': time(9, 0),
                'end': time(11, 0),
                'mode': AgentMode.TRADING,
                'duration': timedelta(minutes=120)
            },
            'mid_session': {
                'start': time(11, 0),
                'end': time(11, 30),
                'mode': AgentMode.REBALANCING,
                'duration': timedelta(minutes=30)
            },
            'afternoon_trading': {
                'start': time(11, 30),
                'end': time(13, 0),
                'mode': AgentMode.TRADING,
                'duration': timedelta(minutes=90)
            },
            'closing_review': {
                'start': time(13, 0),
                'end': time(13, 30),
                'mode': AgentMode.STRATEGY_REVIEW,
                'duration': timedelta(minutes=30)
            }
        }

    def is_trading_day(self, dt: datetime = None) -> bool:
        """檢查是否為交易日（週一到週五）"""
        if dt is None:
            dt = datetime.now(self.taiwan_tz)
        return dt.weekday() < 5

    def get_current_mode(self, dt: datetime = None) -> AgentMode:
        """根據當前時間決定應該執行的模式"""
        if dt is None:
            dt = datetime.now(self.taiwan_tz)

        # 週末執行週度檢討
        if dt.weekday() >= 5:
            return AgentMode.WEEKLY_REVIEW

        # 交易日檢查交易時間
        if self.is_trading_day(dt):
            current_time = dt.time()
            for phase, schedule in self.trading_schedule.items():
                if schedule['start'] <= current_time < schedule['end']:
                    return schedule['mode']

        # 非交易時間執行深度觀察
        return AgentMode.DEEP_OBSERVATION

class AgentState:
    def __init__(self):
        self.current_mode: AgentMode = AgentMode.STANDBY
        self.mode_start_time: datetime = datetime.now()
        self.trading_time_manager = TaiwanStockTradingTimeManager()
        self.performance_metrics: Dict[str, float] = {}
        self.strategy_evolution_history: List[Dict] = []

    def update_mode(self) -> bool:
        """更新當前模式，返回是否發生模式切換"""
        new_mode = self.trading_time_manager.get_current_mode()
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.mode_start_time = datetime.now()
            return True
        return False
```

#### 台股交易時間限定的四種模式詳細說明

**OBSERVATION 模式** - 開盤前準備 (08:30-09:00)

- **時間窗口**: 30分鐘的開盤前準備時間
- **核心任務**: 檢視隔夜重要資訊、分析美股收盤影響、確認今日交易計畫
- **工具使用**: WebSearchTool搜尋盤前新聞、基本面工具檢查重要公告
- **目標**: 為開盤後交易做好充分準備
- **觸發條件**: 交易日08:30自動啟動、重大突發事件

**TRADING 模式** - 主動交易決策 (09:00-11:00 + 11:30-13:00)

- **時間窗口**: 早盤120分鐘 + 午盤90分鐘，總計210分鐘
- **早盤重點**: 開盤動能捕捉、主要部位建立、趨勢確認
- **午盤重點**: 機會補強、部位優化、收盤準備
- **目標**: 每日1-3筆主要交易，單日超額報酬0.5%
- **觸發條件**: 定時調度、技術突破、成交量異常

**REBALANCING 模式** - 中場組合調整 (11:00-11:30)

- **時間窗口**: 30分鐘的中場調整時間
- **核心任務**: 早盤效果評估、風險檢視、午盤策略調整
- **快速執行**: 必要的風險控制調整和部位優化
- **目標**: 確保風險可控、為午盤做好準備
- **觸發條件**: 11:00固定啟動、早盤虧損>3%、集中度警示

**STRATEGY_REVIEW 模式** - 收盤檢討 (13:00-13:30)

- **時間窗口**: 30分鐘的收盤前檢討時間
- **核心任務**: 當日總結、部位檢查、隔夜風險評估、明日準備
- **重要產出**: 當日學習點記錄、明日策略調整
- **目標**: 經驗累積和持續改進
- **觸發條件**: 13:00固定啟動、異常績效、重大消息

**非交易時間模式**:

**DEEP_OBSERVATION 模式** - 深度分析 (13:30-次日08:30)

- **收盤後分析**: 市場深度檢討、個股研究、策略全面評估
- **隔夜監控**: 國際市場追蹤、新聞事件監控、模型優化
- **策略優化**: 基於當日結果進行深度策略調整

**WEEKLY_REVIEW 模式** - 週末檢討 (週六、週日)

- **週度績效**: 完整的一週交易表現分析
- **策略演化**: 決定是否需要重大策略調整
- **下週準備**: 制定下週交易計畫和重點

#### 模式專用提示詞策略

```python
class ModePromptStrategy:
    @staticmethod
    def get_mode_instructions(mode: AgentMode, trader_name: str, context: Dict) -> str:
        mode_instructions = {
            AgentMode.TRADING: f"""
You are {trader_name} in ACTIVE TRADING mode.

TRADING FOCUS:
- Identify immediate trading opportunities
- Execute trades based on technical and fundamental analysis
- Monitor market momentum and volatility
- Risk management: max 5% position size per trade
- Target: 2-4 trades within this session

PERFORMANCE TARGET: Beat benchmark by 1.5% this session
""",

            AgentMode.STRATEGY_REVIEW: f"""
You are {trader_name} in STRATEGY REVIEW mode.

REVIEW FOCUS:
- Analyze recent performance vs benchmark
- Identify strategy strengths and weaknesses
- Review market regime changes
- Consider strategy modifications or pivots
- Update risk parameters if needed

DECISION FRAMEWORK: Evidence-based strategy evolution
""",
            # ... 其他模式
        }
        return mode_instructions[mode]
```

#### 動態策略演化系統

**策略管理器**

```python
class StrategyManager:
    def __init__(self, trader_name: str):
        self.trader_name = trader_name
        self.base_strategy = self._load_base_strategy()
        self.strategy_variants: List[StrategyVariant] = []
        self.performance_tracker = StrategyPerformanceTracker()

    def create_strategy_variant(self, performance_feedback: Dict) -> StrategyVariant:
        """基於性能回饋創建策略變體"""
        variant = StrategyVariant(
            base_strategy=self.base_strategy,
            modifications=self._generate_modifications(performance_feedback),
            creation_time=datetime.now(),
            expected_improvement=self._estimate_improvement(performance_feedback)
        )
        return variant

    def _generate_modifications(self, performance_feedback: Dict) -> Dict:
        """根據表現生成策略修改建議"""
        modifications = {}

        if performance_feedback.get('sharpe_ratio', 0) < 0.5:
            modifications['risk_reduction'] = {
                'max_position_size': 0.03,  # 降低至3%
                'stop_loss_tighter': True,
                'volatility_filter': True
            }

        if performance_feedback.get('win_rate', 0) < 0.4:
            modifications['entry_criteria'] = {
                'technical_confirmation': True,
                'volume_confirmation': True,
                'trend_alignment': True
            }

        return modifications
```

**性能評估和模式切換**

```python
class AgentModeController:
    def __init__(self, trader: EnhancedTrader):
        self.trader = trader
        self.mode_transition_rules = self._define_transition_rules()

    async def check_mode_transition(self):
        """檢查是否需要切換Agent模式"""
        current_mode = self.trader.agent_state.current_mode
        mode_duration = datetime.now() - self.trader.agent_state.mode_start_time

        # 時間驅動的切換
        if mode_duration >= self.trader.agent_state.mode_duration_config[current_mode]:
            next_mode = self._get_next_scheduled_mode(current_mode)
            await self._transition_to_mode(next_mode, "scheduled_transition")
            return

        # 性能驅動的切換
        performance_metrics = await self.trader.performance_evaluator.get_current_metrics()

        # 緊急停止條件
        if performance_metrics.get('max_drawdown', 0) > 0.10:  # 10%回撤
            await self._transition_to_mode(AgentMode.STRATEGY_REVIEW, "emergency_stop")
            return

        # 優異表現觸發策略檢討
        if (performance_metrics.get('daily_return', 0) > 0.05 and
            current_mode == AgentMode.TRADING):
            await self._transition_to_mode(AgentMode.STRATEGY_REVIEW, "high_performance")
```

**增強的TradingAgent架構**

```python
class EnhancedTradingAgent(Agent):
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.agent_state = AgentState()
        self.strategy_manager = StrategyManager(name)
        self.performance_evaluator = PerformanceEvaluator(name)
        self.mode_controller = AgentModeController(self)

    async def run_mode_cycle(self):
        """執行完整的Agent模式循環"""
        while True:
            current_mode = self.agent_state.current_mode

            # 根據當前模式執行對應邏輯
            match current_mode:
                case AgentMode.TRADING:
                    await self._execute_trading_mode()
                case AgentMode.REBALANCING:
                    await self._execute_rebalancing_mode()
                case AgentMode.STRATEGY_REVIEW:
                    await self._execute_strategy_review_mode()
                case AgentMode.OBSERVATION:
                    await self._execute_observation_mode()

            # 檢查是否需要切換模式
            await self.mode_controller.check_mode_transition()

    async def _execute_strategy_review_mode(self):
        """執行策略檢討模式"""
        # 獲取性能指標
        performance = await self.performance_evaluator.get_comprehensive_metrics()

        # 如需演化策略，創建新變體
        if performance['needs_evolution']:
            variant = self.strategy_manager.create_strategy_variant(performance)

            # 更新Agent指令以包含新策略
            self.instructions = self._build_strategy_review_instructions(variant)

            # 執行策略檢討任務
            await self._run_agent_with_mode_prompt(AgentMode.STRATEGY_REVIEW)
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

# CasualMarket MCP 工具整合
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
        # CasualMarket MCP Tools 作為 function_tool 包裝
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
src/
├── agents/                    # Agent 系統模塊
│   ├── core/                  # 核心 Agent 實作
│   │   ├── trading_agent.py   # 主TradingAgent實作
│   │   ├── config_manager.py  # SQLite 配置管理
│   │   ├── trace_logger.py    # 執行追蹤記錄
│   │   └── models.py          # Agent 資料模型定義
│   ├── tools/                 # 專門化Agent Tools
│   │   ├── fundamental_agent.py   # 基本面分析Agent Tool
│   │   ├── technical_agent.py     # 技術分析Agent Tool
│   │   ├── risk_agent.py         # 風險評估Agent Tool
│   │   └── sentiment_agent.py     # 市場情緒分析Agent Tool
│   ├── functions/             # 交易驗證Function Tools
│   │   ├── trading_validation.py  # 交易參數驗證
│   │   ├── market_status.py       # 市場狀態檢查
│   │   └── portfolio_queries.py   # 投資組合查詢
│   └── integrations/          # 外部服務整合
│       ├── mcp_client.py          # CasualMarket MCP客戶端
│       └── mcp_function_wrappers.py # MCP工具Function包裝
├── api/                       # FastAPI 應用 (Agent管理API整合在此)
│   ├── routers/
│   │   ├── agents.py          # Agent CRUD操作路由
│   │   └── agent_monitoring.py # Agent狀態監控路由
│   ├── services/
│   │   ├── agent_service.py   # Agent 業務邏輯
│   │   └── websocket_service.py # 即時通知服務
│   └── models/
│       └── agent_models.py    # Agent API 模型
└── shared/                    # 共享組件
    ├── database/              # 資料庫相關
    │   ├── models.py          # 共享資料模型
    │   └── connection.py      # 資料庫連接
    ├── utils/                 # 共享工具
    │   ├── logging.py         # 統一日誌
    │   └── config.py          # 配置管理
    └── types/                 # 共享類型定義
        └── agent_types.py     # Agent類型定義

frontend/src/
├── components/
│   └── Agent/                 # Agent管理組件
│       ├── AgentCreationForm.svelte  # Agent創建表單
│       ├── AgentDashboard.svelte     # Agent監控儀表板
│       ├── AgentConfigEditor.svelte  # Agent配置編輯器
│       ├── AgentCard.svelte          # Agent基礎卡片
│       ├── AgentGrid.svelte          # Agent網格布局
│       ├── AgentModal.svelte         # Agent彈窗組件
│       ├── AgentToolsSelector.svelte # Agent Tools選擇器
│       └── AgentPerformancePanel.svelte # Agent績效面板
├── stores/
│   ├── agents.js             # Agent狀態管理
│   └── websocket.js          # WebSocket連線狀態
├── lib/
│   ├── api.js                # API客戶端 (包含Agent API)
│   └── websocket.js          # WebSocket管理
└── types/
    └── agent.ts              # Agent相關TypeScript類型定義

tests/
├── agents/                   # Agent系統測試
│   ├── core/
│   │   ├── test_trading_agent.py
│   │   ├── test_config_manager.py
│   │   └── test_trace_logger.py
│   ├── tools/
│   │   ├── test_fundamental_agent.py
│   │   ├── test_technical_agent.py
│   │   ├── test_risk_agent.py
│   │   └── test_sentiment_agent.py
│   ├── functions/
│   │   ├── test_trading_validation.py
│   │   └── test_market_status.py
│   └── integrations/
│       └── test_mcp_integration.py
├── api/
│   ├── routers/
│   │   └── test_agents.py    # Agent路由測試
│   └── services/
│       └── test_agent_service.py # Agent服務測試
└── frontend/
    ├── unit/
    │   └── components/
    │       └── Agent/
    │           ├── AgentCard.test.js
    │           └── AgentDashboard.test.js
    └── integration/
        └── agent-api.test.js
```

---

## ✅ 實作檢查清單

### 主 TradingAgent 架構

- [ ] EnhancedTradingAgent 基礎架構實作
- [ ] 四種執行模式 (TRADING/REBALANCING/STRATEGY_REVIEW/OBSERVATION)
- [ ] 動態策略演化系統整合
- [ ] Agent模式狀態機實作
- [ ] 模式切換控制器 (AgentModeController)
- [ ] 策略管理器 (StrategyManager)
- [ ] 性能評估器 (PerformanceEvaluator)
- [ ] Agent Tool 整合機制
- [ ] OpenAI Agents SDK 整合
- [ ] SQLite 配置管理和持久化

### 動態策略演化系統

- [ ] 策略變體生成機制 (`StrategyVariant`)
- [ ] 性能回饋分析系統
- [ ] 策略修改建議生成
- [ ] 模式專用提示詞策略 (`ModePromptStrategy`)
- [ ] 自動策略參數調整
- [ ] 策略演化歷史追蹤
- [ ] 緊急切換機制實作
- [ ] 時間和性能雙重驅動切換

### 模式切換和控制系統

- [ ] AgentState 狀態管理
- [ ] 模式持續時間配置
- [ ] 觸發條件檢測系統
- [ ] 緊急停止機制 (10%回撤觸發)
- [ ] 優異表現檢測 (5%日報酬觸發)
- [ ] 模式切換日誌記錄
- [ ] 切換原因追蹤

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
