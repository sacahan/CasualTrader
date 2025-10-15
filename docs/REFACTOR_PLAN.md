# CasualTrader 重構計劃

## 🎯 目標

簡化過度複雜的架構，提升開發效率和可維護性，實現多個獨立 Trading Agent 的異步執行

## 📊 現況問題與重構方向

### 1. Agent 架構問題

**現況**: 4 層不必要的抽象 (Manager → Session → BaseAgent → TradingAgent)
**重構方向**:

- 保留現有資料庫 schema (已經設計良好)
- 簡化為直接的 TradingAgent 實現
- 支援多個獨立 Agent 異步執行
- **直接在代碼中配置** Tools/MCP/Sub-agents

### 2. Tools/MCP/Sub-agents 整合問題

**現況**: 缺乏直觀的工具配置方式
**重構方向**:

- **移除複雜的配置系統**，改為直接在 TradingAgent 中配置
- MCP Server、Sub-agents、Tools 直接在初始化時設定
- **Subagent 保持獨立檔案**，但配置從 TradingAgent 統一傳入
- 所有配置參數直接寫在代碼中，易於理解和修改

## 🚀 重構方案

### 階段 1: Agent 架構重構

#### 1.1 新的 TradingAgent 架構

**設計理念**: 簡單直接，配置集中但保留模組化

```text
簡化前:
AgentManager → AgentSession → CasualTradingAgent → TradingAgent
  └── UnifiedToolManager → ToolConfig → 動態參數...

簡化後:
TradingAgent (主配置在這裡)
  ├── 直接配置 MCP servers
  ├── 直接配置 OpenAI tools
  ├── 載入 Sub-agents (tools/ 目錄)
  │   └── 統一配置傳入 (MCP, OpenAI tools, model)
  └── 沿用現有資料庫 schema
```

#### 1.2 簡化的 TradingAgent 配置

**核心原則**: 主配置在 TradingAgent，Subagent 從參數接收共享配置

```python
class TradingAgent:
    """簡化後的 TradingAgent - 配置從資料庫載入"""

    # 類別級別的預設常數（僅作為 fallback）
    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_MAX_TURNS = 30

    # MCP Server 配置 (所有 agent 共享，可從環境變數或配置檔案載入)
    MCP_SERVERS = [
        {
            "name": "casual_market",
            "command": "uvx",
            "args": ["--from", "/Users/sacahan/Documents/workspace/CasualMarket", "casual-market-mcp"],
        },
        {
            "name": "agent_memory",
            "command": "uvx",
            "args": ["mcp-memory-libsql"],
            "env_template": {"LIBSQL_URL": "file://memory/agent_{agent_id}.db"}
        }
    ]

    def __init__(self, agent_id: str, db_config: Agent):
        """
        初始化 TradingAgent

        Args:
            agent_id: Agent ID
            db_config: 從資料庫載入的 Agent 模型實例
        """
        self.agent_id = agent_id
        self.db_config = db_config  # 儲存資料庫配置
        self.session_id = str(uuid.uuid4().hex[:16])  # 用於分組 trace

        # 從資料庫載入配置
        self.name = db_config.name
        self.ai_model = db_config.ai_model
        self.instructions = db_config.instructions
        self.initial_funds = float(db_config.initial_funds)
        self.max_position_size = float(db_config.max_position_size)
        self.current_mode = db_config.current_mode

        # 解析 JSON 配置
        self.investment_preferences = (
            json.loads(db_config.investment_preferences)
            if db_config.investment_preferences
            else {}
        )

    async def initialize(self):
        """初始化 Agent - 配置 MCP 和工具"""

        # 1. 初始化 MCP Servers (主 Agent 管理)
        self.mcp_servers = await self._setup_mcp_servers()

        # 2. 初始化 OpenAI Tools (主 Agent 管理)
        self.openai_tools = self._setup_openai_tools()

        # 3. 載入 Sub-agents (從 tools/ 目錄，傳入共享配置)
        self.subagents = await self._load_subagents()

        # 4. 合併所有 tools
        all_tools = self.openai_tools + [
            agent.as_tool() for agent in self.subagents
        ]

        # 5. 創建主 Agent
        self.agent = Agent(
            model=self.ai_model,  # 從資料庫載入
            tools=all_tools,
            mcp_servers=self.mcp_servers,
            instructions=self.instructions,  # 從資料庫載入
            max_turns=self.DEFAULT_MAX_TURNS
        )

    async def _setup_mcp_servers(self) -> list[MCPServer]:
        """設置 MCP Servers"""
        servers = []
        for mcp_config in self.MCP_SERVERS:
            # 處理環境變數模板
            env = {}
            if "env_template" in mcp_config:
                env = {
                    k: v.format(agent_id=self.agent_id)
                    for k, v in mcp_config["env_template"].items()
                }

            servers.append(
                MCPServer(
                    name=mcp_config["name"],
                    command=mcp_config["command"],
                    args=mcp_config["args"],
                    env=env
                )
            )
        return servers

    def _setup_openai_tools(self) -> list[Any]:
        """設置 OpenAI 內建工具（根據資料庫配置）"""
        tools = []

        # 可以從 investment_preferences 讀取啟用的工具
        enabled_tools = self.investment_preferences.get("enabled_tools", {})

        if enabled_tools.get("web_search", True):
            tools.append(WebSearchTool())

        if enabled_tools.get("code_interpreter", True):
            tools.append(CodeInterpreterTool(container={"type": "auto"}))

        return tools

    async def _load_subagents(self) -> list[Agent]:
        """載入 Sub-agents (從 tools/ 目錄，根據資料庫配置）"""
        from .tools.fundamental_agent import create_fundamental_agent
        from .tools.technical_agent import create_technical_agent
        from .tools.risk_agent import create_risk_agent
        from .tools.sentiment_agent import create_sentiment_agent

        subagents = []

        # 統一的 subagent 配置參數
        subagent_config = {
            "model": self.ai_model,  # 從資料庫載入
            "mcp_servers": self.mcp_servers,  # 傳入相同的 MCP servers
            "openai_tools": self.openai_tools,  # 傳入相同的 OpenAI tools
            "max_turns": 15
        }

        # 從資料庫配置讀取啟用的工具
        enabled_tools = self.investment_preferences.get("enabled_tools", {})

        # 根據啟用狀態載入 subagents
        if enabled_tools.get("fundamental_analysis", True):
            subagents.append(await create_fundamental_agent(**subagent_config))

        if enabled_tools.get("technical_analysis", True):
            subagents.append(await create_technical_agent(**subagent_config))

        if enabled_tools.get("risk_assessment", True):
            subagents.append(await create_risk_agent(**subagent_config))

        if enabled_tools.get("sentiment_analysis", True):
            subagents.append(await create_sentiment_agent(**subagent_config))

        return subagents

    def _get_base_instructions(self) -> str:
        """
        基礎指令（從資料庫載入，可動態插入變數）

        注意：主要的 instructions 已經存在 self.instructions (從資料庫)
        這個方法用於動態插入運行時變數
        """
        # 使用資料庫的 instructions 作為基礎模板
        base_instructions = self.instructions

        # 動態插入運行時資訊
        runtime_context = f"""

運行時資訊：
- Agent ID: {self.agent_id}
- 當前模式: {self.current_mode.value}
- 初始資金: TWD {self.initial_funds:,.0f}
- 最大倉位: {self.max_position_size}%
- 投資偏好: {json.dumps(self.investment_preferences, ensure_ascii=False)}

可用工具：
- FundamentalAnalyst: 基本面分析
- TechnicalAnalyst: 技術分析
- RiskManager: 風險管理
- SentimentAnalyst: 市場情緒分析
- WebSearch: 網路搜尋
- CodeInterpreter: 數據分析
        """

        return base_instructions + runtime_context

    def _build_mode_prompt(self, mode: AgentMode, context: dict[str, Any]) -> str:
        """根據模式生成動態 prompt（基於資料庫的 instructions）"""
        base = self._get_base_instructions()

        if mode == AgentMode.TRADING:
            return f"""{base}

【交易模式】
目標: 尋找並執行交易機會
可用資金: TWD {context.get('available_cash', 0):,.0f}
當前持倉: {len(context.get('current_holdings', []))} 支股票
最大單筆投資: {self.max_position_size}%

請執行以下步驟:
1. 使用 FundamentalAnalyst 和 TechnicalAnalyst 分析潛在標的
2. 使用 SentimentAnalyst 確認市場情緒
3. 使用 RiskManager 評估風險和建議倉位
4. 如果找到機會，生成交易計劃
5. 等待用戶確認後執行交易
"""

        elif mode == AgentMode.REBALANCING:
            holdings = context.get('current_holdings', [])
            return f"""{base}

【再平衡模式】
當前持倉: {len(holdings)} 支股票
投資組合價值: TWD {context.get('portfolio_value', 0):,.0f}
未實現損益: TWD {context.get('unrealized_pnl', 0):,.0f}

持倉明細:
{self._format_holdings(holdings)}

請執行以下步驟:
1. 使用 RiskManager 評估當前組合風險
2. 使用 FundamentalAnalyst 重新評估每個持倉
3. 使用 TechnicalAnalyst 判斷當前趨勢
4. 提出再平衡建議（調整倉位、減倉、加倉）
5. 生成詳細的再平衡計劃
"""

        elif mode == AgentMode.STRATEGY_REVIEW:
            performance = context.get('performance_summary', {})
            return f"""{base}

【策略檢討模式】
檢討期間: {context.get('review_period', '最近30天')}

績效摘要:
- 總報酬率: {performance.get('total_return', 0):.2f}%
- 最大回撤: {performance.get('max_drawdown', 0):.2f}%
- 勝率: {performance.get('win_rate', 0):.1f}%
- 交易次數: {performance.get('total_trades', 0)} 次

請執行以下步驟:
1. 分析交易紀錄，找出成功和失敗的模式
2. 使用 RiskManager 評估風險控制效果
3. 檢討投資策略是否需要調整
4. 提出具體的策略改進建議
5. 如果需要，生成新的投資策略文件
"""

        elif mode == AgentMode.OBSERVATION:
            watchlist = context.get('watchlist', [])
            return f"""{base}

【觀察模式】
關注清單: {len(watchlist)} 支股票

請執行以下步驟:
1. 使用 FundamentalAnalyst 監控關注股票的基本面變化
2. 使用 TechnicalAnalyst 觀察價格走勢
3. 使用 SentimentAnalyst 追蹤市場情緒和新聞
4. 記錄重要的市場動態
5. 如發現潛在機會，標記並說明理由（不執行交易）
"""

        return base

    def _format_holdings(self, holdings: list[dict]) -> str:
        """格式化持倉資訊"""
        if not holdings:
            return "無持倉"

        lines = []
        for holding in holdings:
            lines.append(
                f"- {holding['ticker']}: "
                f"{holding['quantity']} 股, "
                f"成本 TWD {holding['avg_cost']:.2f}, "
                f"損益 {holding['unrealized_pnl_percent']:.2f}%"
            )
        return "\n".join(lines)

    async def execute_trading_session(
        self,
        mode: AgentMode = AgentMode.TRADING,
        context: dict[str, Any] | None = None
    ) -> dict:
        """執行交易會話（模式驅動，自動記錄 trace）"""
        if context is None:
            context = await self._prepare_context(mode)

        # 根據模式生成動態 prompt
        mode_prompt = self._build_mode_prompt(mode, context)

        # 生成 trace ID
        trace_id = gen_trace_id()

        # 使用 trace context manager 包裝執行
        with trace(
            workflow_name=f"Trading Session - {mode.value}",
            group_id=self.session_id,
            trace_id=trace_id
        ):
            # 執行 Agent（trace 自動記錄到 OpenAI Platform）
            result = await Runner.run(
                self.agent,
                mode_prompt
            )

        return {
            "success": True,
            "mode": mode.value,
            "result": result,
            "context": context,
            "trace_id": trace_id,
            "trace_url": f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        }

    async def _prepare_context(self, mode: AgentMode) -> dict[str, Any]:
        """準備執行上下文（從資料庫和運行時狀態）"""
        # 從資料庫載入當前狀態
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "mode": mode.value,
            "available_cash": self.initial_funds,  # 應從 holdings 計算實際可用資金
            "current_holdings": await self._get_current_holdings(),
            "portfolio_value": await self._calculate_portfolio_value(),
            "max_position_size": self.max_position_size,
            "investment_preferences": self.investment_preferences,
            # ...其他上下文資料
        }
```

#### 1.3 獨立 Subagent 檔案範例

**保留在 `tools/` 目錄，但接收統一配置**:

```python
# filepath: backend/src/agents/tools/fundamental_agent.py
"""
基本面分析 Sub-agent
從主 TradingAgent 接收共享配置
"""

from agents import Agent, function_tool

async def create_fundamental_agent(
    model: str,
    mcp_servers: list,
    openai_tools: list,
    max_turns: int = 15
) -> Agent:
    """
    創建基本面分析 Agent

    Args:
        model: AI 模型名稱（從主 Agent 傳入）
        mcp_servers: MCP Servers 列表（從主 Agent 傳入）
        openai_tools: OpenAI 工具列表（從主 Agent 傳入）
        max_turns: 最大執行輪數
    """

    # 定義專業分析工具
    @function_tool
    def analyze_financial_ratios(ticker: str) -> dict:
        """分析公司財務比率"""
        # 使用 casual_market MCP 獲取財報數據
        # 實現邏輯...
        pass

    @function_tool
    def evaluate_company_value(ticker: str) -> dict:
        """評估公司估值"""
        # 實現邏輯...
        pass

    @function_tool
    def compare_industry_peers(ticker: str) -> dict:
        """產業同業比較"""
        # 實現邏輯...
        pass

    # 專業工具列表
    fundamental_tools = [
        analyze_financial_ratios,
        evaluate_company_value,
        compare_industry_peers
    ]

    # 創建 Agent（使用傳入的共享配置）
    return Agent(
        name="FundamentalAnalyst",
        model=model,  # 從主 Agent 傳入
        instructions="""
你是專業的基本面分析師。

你的職責:
1. 使用 casual_market MCP 獲取公司財務數據
2. 分析財務比率（ROE, ROA, P/E, P/B 等）
3. 評估公司內在價值
4. 比較產業同業表現
5. 提供基本面投資建議

分析要點:
- 營收和獲利成長性
- 財務結構健全度
- 現金流狀況
- 產業競爭力
- 管理層素質
        """,
        tools=fundamental_tools,
        mcp_servers=mcp_servers,  # 使用主 Agent 的 MCP servers
        max_turns=max_turns
    )
```

```python
# filepath: backend/src/agents/tools/technical_agent.py
"""
技術分析 Sub-agent
"""

from agents import Agent, function_tool

async def create_technical_agent(
    model: str,
    mcp_servers: list,
    openai_tools: list,
    max_turns: int = 15
) -> Agent:
    """創建技術分析 Agent"""

    @function_tool
    def calculate_indicators(ticker: str, period: int = 20) -> dict:
        """計算技術指標（MA, RSI, MACD, KD）"""
        pass

    @function_tool
    def identify_chart_patterns(ticker: str) -> dict:
        """識別圖表型態（頭肩頂、雙底、三角收斂等）"""
        pass

    @function_tool
    def analyze_volume_price(ticker: str) -> dict:
        """量價關係分析"""
        pass

    technical_tools = [
        calculate_indicators,
        identify_chart_patterns,
        analyze_volume_price
    ]

    return Agent(
        name="TechnicalAnalyst",
        model=model,
        instructions="""
你是專業的技術分析師。

你的職責:
1. 使用技術指標分析價格走勢
2. 識別圖表型態和支撐壓力
3. 分析量價關係
4. 判斷買賣時機
5. 提供技術面交易建議

重點指標:
- 均線系統（MA5, MA20, MA60）
- 動能指標（RSI, MACD）
- 隨機指標（KD）
- 成交量分析
- 趨勢線和型態
        """,
        tools=technical_tools,
        mcp_servers=mcp_servers,
        max_turns=max_turns
    )
```

```python
# filepath: backend/src/agents/tools/risk_agent.py
"""
風險管理 Sub-agent
"""

from agents import Agent, function_tool

async def create_risk_agent(
    model: str,
    mcp_servers: list,
    openai_tools: list,
    max_turns: int = 15
) -> Agent:
    """創建風險管理 Agent"""

    @function_tool
    def assess_portfolio_risk(holdings: list[dict]) -> dict:
        """評估投資組合風險"""
        pass

    @function_tool
    def calculate_position_size(
        ticker: str,
        account_value: float,
        risk_percent: float = 2.0
    ) -> dict:
        """計算建議倉位大小"""
        pass

    @function_tool
    def validate_portfolio_rules(holdings: list[dict]) -> dict:
        """驗證投資組合是否符合風控規則"""
        pass

    risk_tools = [
        assess_portfolio_risk,
        calculate_position_size,
        validate_portfolio_rules
    ]

    return Agent(
        name="RiskManager",
        model=model,
        instructions="""
你是風險管理專家。

你的職責:
1. 評估投資組合風險水平
2. 計算合理的倉位大小
3. 監控風險指標（最大回撤、波動率）
4. 驗證投資組合是否符合風控規則
5. 提供風險控制建議

風控原則:
- 單一持股不超過 20%
- 總持倉不超過 80%
- 停損嚴格執行
- 避免過度集中
- 動態調整倉位
        """,
        tools=risk_tools,
        mcp_servers=mcp_servers,
        max_turns=max_turns
    )
```

#### 1.4 簡化的多 Agent 執行管理

```python
class AgentExecutor:
    """簡化的多 Agent 執行管理"""

    def __init__(self):
        self._running_agents: dict[str, asyncio.Task] = {}
        self._agent_trace_ids: dict[str, str] = {}  # 儲存 trace ID

    async def _load_agent_from_db(self, agent_id: str) -> Agent:
        """從資料庫載入 Agent 配置"""
        from ..database import get_db_session
        from ..database.models import Agent
        from sqlalchemy import select

        async with get_db_session() as session:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await session.execute(stmt)
            db_agent = result.scalar_one_or_none()

            if not db_agent:
                raise ValueError(f"Agent {agent_id} not found in database")

            return db_agent

    async def launch_agent(
        self,
        agent_id: str,
        mode: AgentMode = AgentMode.TRADING,
        context: dict[str, Any] | None = None
    ):
        """啟動 Agent 異步執行（從資料庫載入配置）"""
        if agent_id in self._running_agents:
            raise ValueError(f"Agent {agent_id} is already running")

        # 從資料庫載入 Agent 配置
        db_config = await self._load_agent_from_db(agent_id)

        # 創建和初始化 TradingAgent（使用資料庫配置）
        trading_agent = TradingAgent(agent_id, db_config)
        await trading_agent.initialize()

        # 啟動異步執行
        task = asyncio.create_task(
            trading_agent.execute_trading_session(mode=mode, context=context)
        )
        self._running_agents[agent_id] = task

        return {
            "agent_id": agent_id,
            "agent_name": db_config.name,
            "mode": mode.value,
            "status": "launched",
            "session_id": trading_agent.session_id,
            "ai_model": db_config.ai_model
        }

    async def get_status(self, agent_id: str):
        """查詢執行狀態"""
        if agent_id not in self._running_agents:
            return {"status": "not_found"}

        task = self._running_agents[agent_id]

        if task.done():
            try:
                result = task.result()
                return {
                    "status": "completed",
                    "result": result,
                    "trace_id": result.get("trace_id"),
                    "trace_url": result.get("trace_url")
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": str(e)
                }
        else:
            return {"status": "running"}

    async def stop_agent(self, agent_id: str):
        """停止執行"""
        if agent_id in self._running_agents:
            self._running_agents[agent_id].cancel()
            del self._running_agents[agent_id]

        if agent_id in self._agent_trace_ids:
            del self._agent_trace_ids[agent_id]

        return {"agent_id": agent_id, "status": "stopped"}
```

### 階段 2: 保留現有資料庫 Schema ✅

#### 2.1 Agent 配置表結構

TradingAgent 的配置完全從資料庫的 `agents` 表載入：

```sql
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,                    -- Agent 唯一 ID
    name TEXT NOT NULL,                     -- Agent 顯示名稱
    description TEXT,                       -- Agent 描述
    instructions TEXT NOT NULL,             -- Agent 完整指令 (Prompt)
    ai_model TEXT NOT NULL DEFAULT 'gpt-4o-mini', -- AI 模型選擇
    color TEXT DEFAULT '34, 197, 94',       -- UI 卡片顏色 (RGB 格式)

    -- 投資配置
    initial_funds DECIMAL(15,2) NOT NULL,   -- 初始資金
    max_position_size DECIMAL(5,2) DEFAULT 5.0, -- 最大單筆投資比例 (%)

    -- Agent 狀態
    status TEXT NOT NULL DEFAULT 'inactive',
    current_mode TEXT DEFAULT 'OBSERVATION',

    -- 配置參數 (JSON 格式)
    investment_preferences TEXT,            -- 投資偏好和工具啟用設定

    -- 時間戳記
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active_at DATETIME
);
```

#### 2.2 investment_preferences JSON 格式範例

```json
{
  "enabled_tools": {
    "fundamental_analysis": true,
    "technical_analysis": true,
    "risk_assessment": true,
    "sentiment_analysis": true,
    "web_search": true,
    "code_interpreter": true
  },
  "risk_tolerance": "moderate",
  "preferred_sectors": ["Technology", "Finance"],
  "excluded_sectors": ["Tobacco", "Gambling"],
  "max_single_position": 10.0,
  "target_portfolio_size": 10,
  "rebalance_threshold": 5.0,
  "stop_loss_percent": 8.0,
  "take_profit_percent": 15.0
}
```

#### 2.3 資料庫配置的優勢

1. **動態配置** - 可通過 UI 或 API 即時更新 agent 配置
2. **多租戶支援** - 每個 agent 有獨立的配置
3. **版本控制** - 透過 `updated_at` 追蹤配置變更
4. **持久化** - 配置不會因為重啟而丟失
5. **集中管理** - 所有配置在資料庫中統一管理

#### 2.4 配置載入流程

```text
1. API 收到啟動請求 (agent_id, mode)
   ↓
2. AgentExecutor.launch_agent()
   ↓
3. 從資料庫載入 Agent 記錄
   SELECT * FROM agents WHERE id = ?
   ↓
4. 創建 TradingAgent(agent_id, db_config)
   ↓
5. 解析 investment_preferences JSON
   ↓
6. 初始化 MCP/Tools/Subagents
   ↓
7. 執行交易會話
```

（其他章節維持不變）

### 階段 3: API 重構

#### 3.1 支援多模式和 Trace 的 API 設計

```python
@router.post("/agents/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    mode: AgentMode = AgentMode.TRADING,
    context: dict[str, Any] | None = None
):
    """
    執行 Agent（支援多種模式）

    模式說明:
    - TRADING: 尋找和執行交易機會
    - REBALANCING: 調整投資組合配置
    - STRATEGY_REVIEW: 檢討策略和績效
    - OBSERVATION: 監控市場但不交易

    Trace 功能:
    - 自動記錄所有 LLM 呼叫和工具使用
    - Trace 自動上傳到 OpenAI Platform
    - 返回 trace_id 和 trace_url 供查看
    """
    executor = AgentExecutor()
    return await executor.launch_agent(agent_id, mode, context)

@router.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """
    查詢狀態（包含 trace 資訊）

    Returns:
        包含執行狀態、結果、trace_id 和 trace_url
    """
    executor = AgentExecutor()
    return await executor.get_status(agent_id)

@router.post("/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """停止執行"""
    executor = AgentExecutor()
    return await executor.stop_agent(agent_id)

@router.post("/agents/tracing/disable")
async def disable_tracing(disabled: bool = True):
    """
    全局停用/啟用 tracing

    Args:
        disabled: True 停用，False 啟用

    注意：通常在生產環境中停用以節省成本
    """
    from agents import set_tracing_disabled
    set_tracing_disabled(disabled)
    return {
        "tracing_disabled": disabled,
        "message": f"Tracing {'disabled' if disabled else 'enabled'}"
    }
```

## 📋 實施步驟（更新版）

### Step 1: 重構 TradingAgent 和 Subagents

1. [ ] 更新 `backend/src/agents/trading_agent.py`
   - [ ] **修改 `__init__` 接收資料庫 Agent 模型實例**
   - [ ] **從 `db_config` 載入所有配置參數**
   - [ ] **解析 `investment_preferences` JSON**
   - [ ] 實現統一的 MCP/OpenAI tools 管理
   - [ ] 實現模式驅動的 prompt 生成
   - [ ] 載入 subagents 時傳入共享配置
   - [ ] 添加 trace context manager 支援
   - [ ] 導入 `trace`, `gen_trace_id` from agents

2. [ ] 更新 `backend/src/agents/tools/*.py`
   - [ ] 統一 create_*_agent() 函數簽名
   - [ ] 接收 model, mcp_servers, openai_tools 參數
   - [ ] 移除重複的配置邏輯
   - [ ] 保持專業工具函數

3. [ ] 更新 `backend/src/agents/core/models.py`
   - [ ] 確保 AgentMode 枚舉完整
   - [ ] 添加模式相關的上下文模型
   - [ ] **移除不必要的 AgentConfig 類別（改用資料庫模型）**

4. [ ] **更新 AgentExecutor**
   - [ ] 實現 `_load_agent_from_db()` 方法
   - [ ] 從資料庫載入配置後再創建 TradingAgent
   - [ ] 處理資料庫查詢錯誤

### Step 2: 更新 API

1. [ ] 更新 API routes
   - [ ] 支援 mode 參數
   - [ ] 支援 context 傳遞
   - [ ] 添加模式說明文檔
   - [ ] **返回 trace_id 和 trace_url**
   - [ ] **在 status endpoint 返回 trace 資訊**
   - [ ] **添加全局 tracing 控制 endpoint**

### Step 3: 測試

1. [ ] **測試資料庫配置載入**
   - [ ] 測試從資料庫正確載入 agent 配置
   - [ ] 測試 investment_preferences JSON 解析
   - [ ] 測試配置缺失時的 fallback 行為
2. [ ] 測試各種模式執行
3. [ ] 測試 subagent 配置共享
4. [ ] 測試多 Agent 並發
5. [ ] **測試 trace 記錄功能**
6. [ ] **驗證 trace 在 OpenAI Platform 上可見**
7. [ ] **測試 trace_id 追蹤**
8. [ ] **測試動態更新 agent 配置（更新資料庫後重啟 agent）**

## 🎯 簡化後的優勢

### 1. **配置清晰且集中**

- ✅ **所有 Agent 配置從資料庫載入** - 真正的配置中心化
- ✅ MCP 和 OpenAI tools 在 TradingAgent 統一管理
- ✅ Subagent 保持模組化，但不重複配置
- ✅ 配置傳遞路徑直接明確
- ✅ **Trace 功能使用 OpenAI SDK 內建，開箱即用**

### 2. **架構圖**

```text
Database (agents table)
    ↓ (載入配置)
TradingAgent
├── 配置層（從資料庫）
│   ├── name, ai_model, instructions
│   ├── initial_funds, max_position_size
│   ├── investment_preferences (JSON)
│   │   └── enabled_tools, risk_tolerance, etc.
│   ├── MCP servers (共享)
│   ├── OpenAI tools (根據 enabled_tools)
│   └── Session ID (用於分組 trace) ✨
│
├── Sub-agents（tools/ 目錄）
│   ├── fundamental_agent.py
│   │   └── create_fundamental_agent(model, mcp_servers, openai_tools)
│   ├── technical_agent.py
│   │   └── create_technical_agent(model, mcp_servers, openai_tools)
│   ├── risk_agent.py
│   └── sentiment_agent.py
│
└── 執行層
    ├── _build_mode_prompt(mode, context)
    └── execute_trading_session(mode, context)
        └── with trace() ✨
            └── Runner.run()
```

### 3. **Trace 功能整合** ✨

```python
from agents import trace, gen_trace_id, Runner

# 執行 Agent（trace 自動記錄到 OpenAI Platform）
trace_id = gen_trace_id()
with trace("Trading Session", group_id=session_id, trace_id=trace_id):
    result = await Runner.run(agent, prompt)

# 查看 trace（在 OpenAI Platform）
print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
```

### 4. **Trace 自動記錄包含**

- LLM 呼叫（prompt, response, token usage）
- 工具使用（tool name, parameters, results）
- MCP Server 互動
- Sub-agent 呼叫
- 錯誤和異常
- 執行時間和效能指標

**所有資料自動上傳到 OpenAI Platform，無需手動實現持久化！**

## 📊 對比

| 項目 | 原方案 | 新方案 |
|------|--------|--------|
| 配置位置 | 分散在多處 | **統一在資料庫 agents 表** ✨ |
| 配置管理 | 硬編碼在代碼中 | **動態從資料庫載入** ✨ |
| Subagent 結構 | 獨立檔案但重複配置 | 獨立檔案 + 統一配置傳入 |
| 模式支援 | 需要手動改 prompt | 自動根據模式生成 |
| 代碼重複 | MCP/tools 重複初始化 | 一次初始化，多處共享 |
| 學習成本 | 中等 | 低 |
| **配置更新** | **需要改代碼重啟** | **更新資料庫即可** ✨ |
| **多租戶支援** | **困難** | **原生支援** ✨ |
| **Trace 功能** | **需要手動實現** | **使用 OpenAI SDK 內建** ✨ |
| **Trace 持久化** | **需要自建資料庫** | **自動上傳到 OpenAI Platform** ✨ |
| **Trace 查看** | **需要自建界面** | **使用 OpenAI Dashboard** ✨ |

## 🎊 結論

重構後的 CasualTrader 將：

1. **配置從資料庫載入** - 真正的配置中心化，易於管理和更新 ✨
2. **動態配置更新** - 修改資料庫即可，無需改代碼重啟 ✨
3. **模組化保留** - Subagent 獨立檔案，易於維護
4. **模式驅動** - 根據 AgentMode 自動生成合適的 prompt
5. **避免重複** - MCP 和 OpenAI tools 一次配置，多處共享
6. **易於擴展** - 新增 subagent 或模式都很簡單
7. **內建 Trace** - 使用 OpenAI SDK 的 trace 功能，自動上傳到 OpenAI Platform ✨

### 關鍵原則

- ✅ **資料庫驅動配置** - 所有 Agent 配置從 agents 表載入 ✨
- ✅ **動態配置管理** - 支援運行時配置更新
- ✅ **模組獨立檔案** - Subagent 保持獨立，易於維護
- ✅ **參數明確傳遞** - 從主 Agent 傳入，不埋在深處
- ✅ **模式驅動行為** - 根據模式自動調整 prompt 和行為
- ✅ **簡單優於複雜** - 直接的參數傳遞勝過複雜的配置系統
- ✅ **使用內建 Trace** - 依賴 OpenAI SDK 的 trace 功能，無需自建 ✨

---
*創建時間: 2025-01-14*
*版本: 3.3 (配置從資料庫載入)*

---

## 📚 附錄：正確的 Trace 使用方式

### A. 基本 Trace 用法

```python
from agents import Agent, Runner, trace, gen_trace_id
import uuid

class TradingAgent:
    """正確使用 OpenAI Agents SDK Trace 的範例"""

    def __init__(self, agent_id: str, config: AgentConfig):
        self.agent_id = agent_id
        self.config = config
        self.session_id = str(uuid.uuid4().hex[:16])

    async def execute_trading_session(
        self,
        mode: AgentMode = AgentMode.TRADING,
        context: dict[str, Any] | None = None
    ) -> dict:
        """執行交易會話（正確使用 trace）"""

        # 1. 生成 trace ID
        trace_id = gen_trace_id()

        # 2. 使用 trace context manager 包裝執行
        with trace(
            workflow_name=f"Trading Session - {mode.value}",
            group_id=self.session_id,  # 用於分組相關的 trace
            trace_id=trace_id
        ):
            # 3. 執行 Agent（trace 自動記錄）
            result = await Runner.run(
                self.agent,
                self._build_mode_prompt(mode, context)
            )

        # 4. 返回結果和 trace 資訊
        return {
            "success": True,
            "result": result,
            "trace_id": trace_id,
            "trace_url": f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        }
```

### B. 多步驟分組到單一 Trace

```python
async def execute_multi_step_analysis(self):
    """多個步驟統一到一個 trace"""

    with trace(
        workflow_name="Complete Market Analysis",
        group_id=self.session_id
    ):
        # 所有這些步驟會被記錄在同一個 trace 中

        # Step 1: 基本面分析
        fundamental = await Runner.run(
            self.agent,
            "Analyze fundamentals of 2330.TW"
        )

        # Step 2: 技術分析
        technical = await Runner.run(
            self.agent,
            f"Technical analysis based on: {fundamental.final_output}"
        )

        # Step 3: 風險評估
        risk = await Runner.run(
            self.agent,
            f"Risk assessment for: {technical.final_output}"
        )

    return {
        "fundamental": fundamental,
        "technical": technical,
        "risk": risk
    }
```

### C. 生產環境停用 Trace

```python
from agents import set_tracing_disabled

# 在生產環境中停用 trace（節省成本）
if os.getenv("ENVIRONMENT") == "production":
    set_tracing_disabled(True)
```

### D. 非 OpenAI 模型使用 Trace

```python
import os
from agents import set_tracing_export_api_key, Agent
from agents.extensions.models.litellm_model import LitellmModel

# 設定 tracing 專用的 API key
tracing_api_key = os.environ["OPENAI_API_KEY"]
set_tracing_export_api_key(tracing_api_key)

# 使用非 OpenAI 模型（如 Claude）但仍可 trace
model = LitellmModel(
    model="anthropic/claude-3-5-sonnet-20240620",
    api_key=os.environ["ANTHROPIC_API_KEY"]
)

agent = Agent(
    name="Assistant",
    model=model,
    instructions="You are helpful."
)

# Trace 仍然會上傳到 OpenAI Platform
with trace("Claude Agent Session"):
    result = await Runner.run(agent, "Help me analyze this data")
```

### E. 啟用詳細 Logging

```python
from agents import enable_verbose_stdout_logging
import logging

# 方法 1: 使用 SDK 提供的便捷函數
enable_verbose_stdout_logging()

# 方法 2: 自定義 logging 配置
logger = logging.getLogger("openai.agents")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# 只看 tracing 相關的 log
trace_logger = logging.getLogger("openai.agents.tracing")
trace_logger.setLevel(logging.INFO)
```

### F. 查看 Trace 的方式

1. **通過 trace_id 直接查看**：

   ```
   https://platform.openai.com/traces/trace?trace_id={trace_id}
   ```

2. **在 OpenAI Dashboard 中瀏覽**：

   ```
   https://platform.openai.com/traces
   ```

3. **按 group_id 篩選**：
   - 在 OpenAI Platform 的 Traces 頁面使用 filter

### G. 常見錯誤和解決方案

#### 錯誤 1: 401 Tracing Upload Error

```python
# 原因：沒有設定 OpenAI API Key
# 解決方案：
import os
os.environ["OPENAI_API_KEY"] = "sk-..."

# 或者為 tracing 設定專用 key
from agents import set_tracing_export_api_key
set_tracing_export_api_key("sk-...")
```

#### 錯誤 2: 嘗試在 Agent 初始化時設定 trace

```python
# ❌ 錯誤：Agent 沒有 trace 參數
agent = Agent(
    name="Assistant",
    trace=my_handler  # 不存在！
)

# ✅ 正確：在執行時使用 trace context manager
with trace("My Workflow"):
    result = await Runner.run(agent, "task")
```

#### 錯誤 3: 嘗試自定義 trace handler

```python
# ❌ 錯誤：SDK 不支援自定義 trace handler
def my_trace_handler(event):
    print(event)

# ✅ 正確：如需自定義邏輯，使用 logging 或 RunHooks
import logging
logger = logging.getLogger("openai.agents")
logger.addHandler(MyCustomHandler())
```

### H. 最佳實踐

1. **為每個會話生成唯一的 session_id**

   ```python
   self.session_id = str(uuid.uuid4().hex[:16])
   ```

2. **使用描述性的 workflow_name**

   ```python
   with trace(workflow_name="Trading: Buy Decision for TSMC"):
       ...
   ```

3. **在關鍵流程使用 trace 分組**

   ```python
   with trace("Daily Trading Routine", group_id=date.today().isoformat()):
       # 當天所有交易都在這個 trace 下
       ...
   ```

4. **生產環境考慮成本**

   ```python
   # 只在開發和 staging 環境啟用 trace
   if os.getenv("ENABLE_TRACING", "false").lower() == "true":
       # trace enabled
       pass
   else:
       set_tracing_disabled(True)
   ```

---

## 🔗 參考資源

- [OpenAI Agents Python SDK - Tracing Documentation](https://github.com/openai/openai-agents-python/blob/main/docs/tracing.md)
- [OpenAI Platform - Traces Dashboard](https://platform.openai.com/traces)
- [OpenAI Agents SDK - Configuration](https://github.com/openai/openai-agents-python/blob/main/docs/config.md)

---

## 🔄 版本歷史

### v3.3 (2025-01-14)

- 🔧 **配置從資料庫載入**：TradingAgent 配置完全從 `agents` 表讀取
- ✨ 支援動態配置更新（修改資料庫即可）
- 📚 添加資料庫 schema 和 JSON 格式說明
- 🎯 實現 `_load_agent_from_db()` 方法
- 📝 更新測試步驟包含資料庫配置測試

### v3.2 (2025-01-14)

- 🔧 **修正 Trace 用法**：移除錯誤的自定義實現
- ✨ 改用 OpenAI Agents SDK 內建的 trace 功能
- 📚 添加正確的 trace 使用範例和最佳實踐
- 🗑️ 移除不必要的 TraceManager 和持久化邏輯

### v3.1 (2025-01-14)

- ~~添加 OpenAI Agents SDK trace 功能整合~~（實現方式錯誤）
- ~~實現 TraceManager 和完整的 trace 持久化~~（不需要）

### v3.0 (2025-01-14)

- 🎯 簡化 Agent 架構，移除多層抽象
- 🔧 配置集中化，統一在 TradingAgent 管理
- 🚀 支援多種執行模式

---

## 📞 聯絡與支援

如有問題或建議，請聯繫開發團隊或提交 Issue。

**文檔維護**: CasualTrader Development Team
**最後更新**: 2025-01-14
