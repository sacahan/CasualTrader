# CasualTrader 重構實施指南

**配合文檔**: [REFACTOR_PLAN.md](./REFACTOR_PLAN.md)
**版本**: 1.0
**日期**: 2025-10-15

## 📋 目錄

1. [檔案變更清單](#檔案變更清單)
2. [資料庫服務層實作](#資料庫服務層實作)
3. [錯誤處理策略](#錯誤處理策略)
4. [測試策略](#測試策略)
5. [遷移計劃](#遷移計劃)
6. [效能和資源管理](#效能和資源管理)
7. [部署檢查清單](#部署檢查清單)

---

## 📁 檔案變更清單

### 需要刪除的檔案

```bash
# 舊的多層抽象（如果存在）
backend/src/agents/core/agent_manager.py          # AgentManager 類別
backend/src/agents/core/agent_session.py          # AgentSession 類別
backend/src/agents/core/tool_manager.py           # UnifiedToolManager
backend/src/agents/core/config_manager.py         # 複雜的配置系統

# 執行刪除命令
rm -f backend/src/agents/core/agent_manager.py
rm -f backend/src/agents/core/agent_session.py
rm -f backend/src/agents/core/tool_manager.py
rm -f backend/src/agents/core/config_manager.py
```

### 需要新增的檔案

```bash
# 核心 Agent 實作
backend/src/agents/trading_agent.py               # 新的簡化 TradingAgent

# Sub-agents（如果不存在）
backend/src/agents/tools/fundamental_agent.py     # 基本面分析
backend/src/agents/tools/technical_agent.py       # 技術分析
backend/src/agents/tools/risk_agent.py            # 風險管理
backend/src/agents/tools/sentiment_agent.py       # 市場情緒

# 執行管理
backend/src/agents/executor.py                    # AgentExecutor 類別

# 資料庫服務
backend/src/database/agent_service.py             # Agent 資料庫服務層

# 測試檔案
backend/tests/agents/test_trading_agent.py
backend/tests/agents/test_executor.py
backend/tests/database/test_agent_service.py
backend/tests/integration/test_agent_workflow.py
```

### 需要修改的檔案

```bash
# API 路由
backend/src/api/routers/agents.py                 # 支援新的執行模式

# 資料庫 models（可能需要小幅調整）
backend/src/database/models.py                    # 確保 Agent model 完整

# API 配置
backend/src/api/app.py                            # 註冊新的路由
```

---

## 🗄️ 資料庫服務層實作

### 1. Agent 資料庫服務

```python
# filepath: backend/src/database/agent_service.py
"""
Agent 資料庫服務層
提供 Agent 配置的 CRUD 操作和錯誤處理
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Agent, AgentHolding, AgentMode, AgentStatus

logger = logging.getLogger(__name__)


class AgentNotFoundError(Exception):
    """Agent 不存在於資料庫"""
    pass


class AgentConfigurationError(Exception):
    """Agent 配置錯誤"""
    pass


class AgentDatabaseService:
    """Agent 資料庫服務"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_agent_config(self, agent_id: str) -> Agent:
        """
        載入 Agent 配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent 模型實例

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentConfigurationError: 配置格式錯誤
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found in database")

            # 驗證必要欄位
            self._validate_agent_config(agent)

            logger.info(f"Loaded agent config: {agent_id} (model: {agent.ai_model})")
            return agent

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error loading agent config: {e}")
            raise AgentConfigurationError(f"Failed to load agent config: {str(e)}")

    async def get_agent_with_holdings(self, agent_id: str) -> Agent:
        """
        載入 Agent 配置和持倉資料

        Args:
            agent_id: Agent ID

        Returns:
            Agent 模型實例（包含 holdings 關聯）
        """
        stmt = (
            select(Agent)
            .where(Agent.id == agent_id)
            .options(selectinload(Agent.holdings))
        )
        result = await self.session.execute(stmt)
        agent = result.scalar_one_or_none()

        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found")

        return agent

    async def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
        mode: AgentMode | None = None
    ) -> None:
        """
        更新 Agent 狀態

        Args:
            agent_id: Agent ID
            status: 新狀態
            mode: 新模式（可選）
        """
        stmt = select(Agent).where(Agent.id == agent_id)
        result = await self.session.execute(stmt)
        agent = result.scalar_one_or_none()

        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found")

        agent.status = status
        if mode:
            agent.current_mode = mode

        await self.session.commit()
        logger.info(f"Updated agent {agent_id} status to {status.value}")

    async def list_active_agents(self) -> list[Agent]:
        """取得所有 ACTIVE 狀態的 Agents"""
        stmt = select(Agent).where(Agent.status == AgentStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _validate_agent_config(self, agent: Agent) -> None:
        """
        驗證 Agent 配置完整性

        Raises:
            AgentConfigurationError: 配置驗證失敗
        """
        # 驗證必要欄位
        if not agent.name:
            raise AgentConfigurationError("Agent name is required")

        if not agent.instructions:
            raise AgentConfigurationError("Agent instructions are required")

        if not agent.ai_model:
            raise AgentConfigurationError("AI model is required")

        # 驗證 JSON 格式
        if agent.investment_preferences:
            try:
                json.loads(agent.investment_preferences)
            except json.JSONDecodeError as e:
                raise AgentConfigurationError(
                    f"Invalid investment_preferences JSON: {str(e)}"
                )

    async def parse_investment_preferences(self, agent: Agent) -> dict[str, Any]:
        """
        解析 investment_preferences JSON

        Args:
            agent: Agent 模型實例

        Returns:
            解析後的字典（如果為空則返回預設值）
        """
        if not agent.investment_preferences:
            return self._get_default_preferences()

        try:
            return json.loads(agent.investment_preferences)
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to parse investment_preferences for agent {agent.id}, "
                "using defaults"
            )
            return self._get_default_preferences()

    def _get_default_preferences(self) -> dict[str, Any]:
        """預設投資偏好"""
        return {
            "enabled_tools": {
                "fundamental_analysis": True,
                "technical_analysis": True,
                "risk_assessment": True,
                "sentiment_analysis": True,
                "web_search": True,
                "code_interpreter": True
            },
            "risk_tolerance": "moderate",
            "max_single_position": 10.0,
            "stop_loss_percent": 8.0,
            "take_profit_percent": 15.0
        }
```

### 2. Session Factory

```python
# filepath: backend/src/database/__init__.py (添加到現有檔案)
"""
資料庫連線管理
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base

# 全域 engine 和 session factory
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_database(database_url: str, echo: bool = False) -> None:
    """
    初始化資料庫引擎

    Args:
        database_url: 資料庫連線 URL
        echo: 是否輸出 SQL 語句
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        database_url,
        echo=echo,
        pool_size=10,  # 連線池大小
        max_overflow=20,  # 最大溢出連線數
        pool_pre_ping=True,  # 連線前檢查
        pool_recycle=3600,  # 1小時回收連線
    )

    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    取得資料庫 session（context manager）

    Usage:
        async with get_db_session() as session:
            # 使用 session
            agent = await session.get(Agent, agent_id)
    """
    if not _session_factory:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_database() -> None:
    """關閉資料庫連線"""
    global _engine
    if _engine:
        await _engine.dispose()
```

---

## 🛡️ 錯誤處理策略

### 1. Agent 初始化失敗處理

```python
# filepath: backend/src/agents/trading_agent.py (錯誤處理部分)

class AgentInitializationError(Exception):
    """Agent 初始化失敗"""
    pass


class TradingAgent:
    async def initialize(self) -> None:
        """初始化 Agent（含錯誤處理）"""
        try:
            # 1. 初始化 MCP Servers
            try:
                self.mcp_servers = await self._setup_mcp_servers()
            except Exception as e:
                logger.error(f"Failed to setup MCP servers: {e}")
                raise AgentInitializationError(f"MCP setup failed: {str(e)}")

            # 2. 初始化 OpenAI Tools
            try:
                self.openai_tools = self._setup_openai_tools()
            except Exception as e:
                logger.error(f"Failed to setup OpenAI tools: {e}")
                raise AgentInitializationError(f"Tools setup failed: {str(e)}")

            # 3. 載入 Sub-agents
            try:
                self.subagents = await self._load_subagents()
            except Exception as e:
                logger.error(f"Failed to load subagents: {e}")
                # Sub-agents 失敗可以降級處理
                logger.warning("Continuing without subagents")
                self.subagents = []

            # 4. 創建主 Agent
            all_tools = self.openai_tools + [
                agent.as_tool() for agent in self.subagents
            ]

            self.agent = Agent(
                model=self.ai_model,
                tools=all_tools,
                mcp_servers=self.mcp_servers,
                instructions=self.instructions,
                max_turns=self.DEFAULT_MAX_TURNS
            )

            logger.info(f"Agent {self.agent_id} initialized successfully")

        except AgentInitializationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during agent initialization: {e}")
            raise AgentInitializationError(f"Initialization failed: {str(e)}")
```

### 2. MCP Server 啟動失敗處理

```python
async def _setup_mcp_servers(self) -> list[MCPServer]:
    """設置 MCP Servers（含重試邏輯）"""
    servers = []

    for mcp_config in self.MCP_SERVERS:
        try:
            # 處理環境變數
            env = {}
            if "env_template" in mcp_config:
                env = {
                    k: v.format(agent_id=self.agent_id)
                    for k, v in mcp_config["env_template"].items()
                }

            server = MCPServer(
                name=mcp_config["name"],
                command=mcp_config["command"],
                args=mcp_config["args"],
                env=env
            )

            # 可選：驗證 MCP server 是否可用
            # await self._verify_mcp_server(server)

            servers.append(server)
            logger.info(f"MCP server '{mcp_config['name']}' configured")

        except Exception as e:
            logger.error(f"Failed to setup MCP server '{mcp_config['name']}': {e}")
            # 根據策略決定是否繼續
            if mcp_config.get("required", True):
                raise
            else:
                logger.warning(f"Skipping optional MCP server '{mcp_config['name']}'")

    return servers
```

### 3. 執行時錯誤處理

```python
async def execute_trading_session(
    self,
    mode: AgentMode = AgentMode.TRADING,
    context: dict[str, Any] | None = None
) -> dict:
    """執行交易會話（含完整錯誤處理）"""

    if context is None:
        try:
            context = await self._prepare_context(mode)
        except Exception as e:
            logger.error(f"Failed to prepare context: {e}")
            return {
                "success": False,
                "error": f"Context preparation failed: {str(e)}",
                "mode": mode.value
            }

    trace_id = gen_trace_id()

    try:
        mode_prompt = self._build_mode_prompt(mode, context)

        with trace(
            workflow_name=f"Trading Session - {mode.value}",
            group_id=self.session_id,
            trace_id=trace_id
        ):
            result = await Runner.run(self.agent, mode_prompt)

        return {
            "success": True,
            "mode": mode.value,
            "result": result,
            "context": context,
            "trace_id": trace_id,
            "trace_url": f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        }

    except Exception as e:
        logger.error(f"Trading session execution failed: {e}", exc_info=True)
        return {
            "success": False,
            "mode": mode.value,
            "error": str(e),
            "error_type": type(e).__name__,
            "trace_id": trace_id,
            "trace_url": f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        }
```

---

## 🧪 測試策略

### 1. 單元測試範例

```python
# filepath: backend/tests/agents/test_trading_agent.py
"""
TradingAgent 單元測試
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.trading_agent import TradingAgent, AgentInitializationError
from src.database.models import Agent, AgentMode


@pytest.fixture
def mock_db_config():
    """Mock 的資料庫配置"""
    agent = Agent(
        id="test_agent_001",
        name="Test Trading Agent",
        instructions="Test instructions",
        ai_model="gpt-4o-mini",
        initial_funds=100000.00,
        max_position_size=10.0,
        investment_preferences='{"enabled_tools": {"fundamental_analysis": true}}'
    )
    return agent


@pytest.mark.asyncio
async def test_trading_agent_initialization(mock_db_config):
    """測試 TradingAgent 初始化"""

    with patch("src.agents.trading_agent.MCPServer"), \
         patch("src.agents.trading_agent.Agent"):

        trading_agent = TradingAgent("test_agent_001", mock_db_config)

        assert trading_agent.agent_id == "test_agent_001"
        assert trading_agent.name == "Test Trading Agent"
        assert trading_agent.ai_model == "gpt-4o-mini"
        assert float(trading_agent.initial_funds) == 100000.00


@pytest.mark.asyncio
async def test_trading_agent_mcp_setup_failure(mock_db_config):
    """測試 MCP Server 設置失敗"""

    with patch("src.agents.trading_agent.MCPServer", side_effect=Exception("MCP error")):

        trading_agent = TradingAgent("test_agent_001", mock_db_config)

        with pytest.raises(AgentInitializationError, match="MCP setup failed"):
            await trading_agent.initialize()


@pytest.mark.asyncio
async def test_parse_investment_preferences(mock_db_config):
    """測試解析 investment_preferences"""

    trading_agent = TradingAgent("test_agent_001", mock_db_config)
    prefs = trading_agent.investment_preferences

    assert isinstance(prefs, dict)
    assert "enabled_tools" in prefs
    assert prefs["enabled_tools"]["fundamental_analysis"] is True
```

### 2. 資料庫服務測試

```python
# filepath: backend/tests/database/test_agent_service.py
"""
AgentDatabaseService 測試
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database.agent_service import (
    AgentDatabaseService,
    AgentNotFoundError,
    AgentConfigurationError
)
from src.database.models import Base, Agent, AgentStatus


@pytest.fixture
async def db_session():
    """測試用資料庫 session"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_agent_config_success(db_session):
    """測試成功載入 agent 配置"""

    # 建立測試 agent
    agent = Agent(
        id="test_001",
        name="Test Agent",
        instructions="Test instructions",
        ai_model="gpt-4o-mini",
        initial_funds=100000.00,
        investment_preferences='{"enabled_tools": {}}'
    )
    db_session.add(agent)
    await db_session.commit()

    # 測試載入
    service = AgentDatabaseService(db_session)
    loaded_agent = await service.get_agent_config("test_001")

    assert loaded_agent.id == "test_001"
    assert loaded_agent.name == "Test Agent"


@pytest.mark.asyncio
async def test_get_agent_config_not_found(db_session):
    """測試 agent 不存在"""

    service = AgentDatabaseService(db_session)

    with pytest.raises(AgentNotFoundError, match="not found in database"):
        await service.get_agent_config("nonexistent")


@pytest.mark.asyncio
async def test_invalid_json_preferences(db_session):
    """測試無效的 JSON 配置"""

    agent = Agent(
        id="test_002",
        name="Test Agent",
        instructions="Test",
        ai_model="gpt-4o-mini",
        initial_funds=100000.00,
        investment_preferences='invalid json {'  # 無效 JSON
    )
    db_session.add(agent)
    await db_session.commit()

    service = AgentDatabaseService(db_session)

    with pytest.raises(AgentConfigurationError, match="Invalid investment_preferences"):
        await service.get_agent_config("test_002")
```

### 3. 整合測試範例

```python
# filepath: backend/tests/integration/test_agent_workflow.py
"""
完整 Agent 工作流程整合測試
"""

import pytest

from src.agents.executor import AgentExecutor
from src.database.models import AgentMode


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_agent_execution_workflow(test_db_session):
    """測試完整的 Agent 執行流程"""

    # 1. 建立測試 agent 在資料庫中
    # (假設已在 fixture 中建立)

    # 2. 啟動 agent
    executor = AgentExecutor()
    result = await executor.launch_agent(
        agent_id="test_agent_001",
        mode=AgentMode.OBSERVATION,
        context={"test": True}
    )

    assert result["status"] == "launched"
    assert result["agent_id"] == "test_agent_001"

    # 3. 檢查狀態
    status = await executor.get_status("test_agent_001")
    assert status["status"] in ["running", "completed"]

    # 4. 清理
    await executor.stop_agent("test_agent_001")
```

---

## 🚀 遷移計劃

### Phase 1: 準備階段（1-2天）

```bash
# 1. 建立新的分支
git checkout -b refactor/simplified-agent-architecture

# 2. 備份現有代碼
git tag backup-before-refactor

# 3. 建立測試資料庫
cp backend/casualtrader.db backend/casualtrader.db.backup
```

### Phase 2: 實施階段（3-5天）

**Day 1-2: 核心重構**

- [ ] 實作新的 `TradingAgent`
- [ ] 實作 `AgentDatabaseService`
- [ ] 實作 `AgentExecutor`
- [ ] 建立單元測試

**Day 3-4: Sub-agents 和工具**

- [ ] 重構 Sub-agents（fundamental, technical, risk, sentiment）
- [ ] 測試工具整合
- [ ] 建立整合測試

**Day 5: API 更新**

- [ ] 更新 API 路由
- [ ] 測試 API endpoints
- [ ] 更新 API 文檔

### Phase 3: 測試階段（2-3天）

```bash
# 運行所有測試
pytest backend/tests/ -v

# 運行整合測試
pytest backend/tests/integration/ -v --integration

# 檢查測試覆蓋率
pytest --cov=src --cov-report=html
```

### Phase 4: 部署階段（1天）

```bash
# 1. 合併到 main
git checkout main
git merge refactor/simplified-agent-architecture

# 2. 更新依賴
cd backend
pip install -r requirements.txt

# 3. 運行資料庫遷移（如果需要）
python -m src.database.migrations

# 4. 重啟服務
./scripts/start.sh
```

### 回滾計劃

```bash
# 如果遇到問題，快速回滾
git checkout backup-before-refactor
cp backend/casualtrader.db.backup backend/casualtrader.db
./scripts/start.sh
```

---

## ⚡ 效能和資源管理

### 1. 並發限制

```python
# filepath: backend/src/agents/executor.py (添加並發控制)

class AgentExecutor:
    """簡化的多 Agent 執行管理（含並發控制）"""

    MAX_CONCURRENT_AGENTS = 5  # 最多同時執行 5 個 agents

    def __init__(self):
        self._running_agents: dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_AGENTS)

    async def launch_agent(
        self,
        agent_id: str,
        mode: AgentMode = AgentMode.TRADING,
        context: dict[str, Any] | None = None
    ):
        """啟動 Agent（含並發限制）"""

        # 檢查並發限制
        if len(self._running_agents) >= self.MAX_CONCURRENT_AGENTS:
            raise ValueError(
                f"Maximum concurrent agents ({self.MAX_CONCURRENT_AGENTS}) reached"
            )

        async with self._semaphore:
            # 執行 agent...
            pass
```

### 2. 資源監控

```python
import psutil
import logging

logger = logging.getLogger(__name__)


async def monitor_resources():
    """監控系統資源使用"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)

    logger.info(
        f"System resources - "
        f"Memory: {memory.percent}%, "
        f"CPU: {cpu_percent}%"
    )

    # 警告閾值
    if memory.percent > 85:
        logger.warning("High memory usage detected!")

    if cpu_percent > 90:
        logger.warning("High CPU usage detected!")
```

### 3. MCP Server 生命週期管理

```python
class TradingAgent:
    async def cleanup(self):
        """清理資源（關閉 MCP servers）"""
        try:
            for server in self.mcp_servers:
                # MCP SDK 應該提供關閉方法
                await server.close()

            logger.info(f"Agent {self.agent_id} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
```

---

## ✅ 部署檢查清單

### 部署前檢查

- [ ] 所有測試通過（單元、整合、E2E）
- [ ] 測試覆蓋率 > 80%
- [ ] 代碼審查完成
- [ ] 文檔更新完成
- [ ] API 文檔更新
- [ ] 環境變數配置正確
- [ ] 資料庫備份完成
- [ ] 監控和日誌配置就緒

### 部署後驗證

- [ ] API 健康檢查通過
- [ ] 能夠成功啟動 agent
- [ ] Trace 功能正常運作
- [ ] 資料庫連線正常
- [ ] MCP servers 正常啟動
- [ ] 日誌正常輸出
- [ ] 前端能夠正常連接

### 監控指標

```python
# 關鍵監控指標
- agent_initialization_time_ms
- agent_execution_time_ms
- database_query_time_ms
- mcp_server_startup_time_ms
- concurrent_agents_count
- error_rate
- api_response_time_ms
```

---

## 📚 參考資源

- [REFACTOR_PLAN.md](./REFACTOR_PLAN.md) - 主要重構計劃
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [SQLAlchemy 2.0 文檔](https://docs.sqlalchemy.org/en/20/)
- [Pytest Async 指南](https://pytest-asyncio.readthedocs.io/)

---

**維護**: CasualTrader Development Team
**最後更新**: 2025-10-15
