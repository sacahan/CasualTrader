# Agent 系統實作規格

**版本**: 3.1
**日期**: 2025-10-07
**相關設計**: SYSTEM_DESIGN.md
**基於**: OpenAI Agents SDK + Prompt-Based Strategy Management

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
            # 專門化分析工具
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
            sentiment_agent.as_tool(
                tool_name="market_sentiment",
                tool_description="Analyze market sentiment and news impact"
            ),

            # OpenAI Hosted Tools
            WebSearchTool(),
            CodeInterpreterTool(),

            # CasualMarket MCP Tools
            get_taiwan_stock_price,
            buy_taiwan_stock,
            sell_taiwan_stock,
            get_company_fundamentals,
            get_stock_valuation_ratios,

            # 交易驗證工具
            check_trading_hours,
            get_current_holdings,
            get_available_cash,
            validate_trade_parameters,

            # 策略變更記錄工具
            record_strategy_change,
        ],
        model="gpt-4",
        max_turns=30
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
  excluded_symbols?: string[];
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
          placeholder="排除股票代碼 (逗號分隔，如: 2498,2328)"
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

    async def execute_trade(self, symbol: str, quantity: int):
        """執行交易前檢查市場狀態"""
        # 檢查市場是否開盤
        status = await self.market_checker.get_market_status()

        if not status.is_open:
            return {
                "success": False,
                "error": f"市場未開盤 (當前時段: {status.current_session})"
            }

        # 執行交易...
        return await self._execute_order(symbol, quantity)
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
    "symbol": "2330"  # 台積電
})
# 返回: 即時價格、漲跌幅、成交量、五檔報價等
````

#### 模擬交易執行

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

#### 公司基本資料

```python
# 工具: get_company_profile
# 用途: 獲取公司基本資訊、產業分類、主要業務
response = await mcp_client.call_tool("get_company_profile", {
    "symbol": "2330"
})
```

#### 財務報表工具

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

#### 估值分析工具

```python
# 工具: get_stock_valuation_ratios
# 用途: 獲取本益比、股價淨值比、殖利率等估值指標
valuation = await mcp_client.call_tool("get_stock_valuation_ratios", {
    "symbol": "2330"
})
```

### 市場數據工具

#### 交易統計工具

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

#### 執行Agent使用範例

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
