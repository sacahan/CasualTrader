# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📊 Project Overview

CasualTrader is an AI-powered trading simulation platform that combines:

- **FastAPI Backend**: RESTful API + WebSocket real-time communication
- **AI Trading Agents**: Multi-model support (GPT-4, Claude, Gemini, DeepSeek) with dynamic strategy evolution
- **MCP Integration**: Market data via Model Context Protocol
- **Database Persistence**: SQLAlchemy async ORM with SQLite/PostgreSQL support
- **Agent Lifecycle Management**: Session-based trading with portfolio tracking and performance analytics

### Core Architecture

The system uses a **multi-layered agent architecture**:

- **Agent Manager** (`src/agents/core/agent_manager.py`): Manages multiple AI agents concurrently
- **Base Agent** (`src/agents/core/base_agent.py`): Abstract base class for all trading agents
- **Trading Agent** (`src/agents/trading/trading_agent.py`): Concrete implementation with strategy execution
- **Persistent Agent** (`src/agents/integrations/persistent_agent.py`): Database-backed agent with session management

### MCP Integration (Model Context Protocol)

**CasualMarket MCP Server** provides Taiwan stock market data:

- **Market Data Tools**: Real-time stock prices, trading info, market indices
- **Financial Analysis**: Company profiles, financial statements (income/balance sheet)
- **Portfolio Management**: Simulated trading operations (buy/sell with fee calculation)
- **Market Analytics**: Margin trading info, dividend schedules, valuation ratios

The MCP client (`src/agents/integrations/mcp_client.py`) connects to the FastMCP-based server for all market operations, providing agents with:

- Real-time Taiwan stock prices and trading data
- Company financial statements and analysis
- Simulated trading execution with accurate fee calculation
- Market calendar and trading day verification

## 🔧 Development Commands

### Quick Start

```bash
# Start both frontend and backend (recommended)
./scripts/start.sh

# Start backend only
./scripts/start.sh -b

# Start frontend only
./scripts/start.sh -f

# Show help
./scripts/start.sh -h
```

### Environment Setup

```bash
# Install dependencies
uv sync --dev

# Run database migrations
./scripts/db_migrate.sh up
# or
uv run python -m src.database.migrations

# Start FastAPI server manually
uv run python src/api/server.py
# or
uv run uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test suites
uv run pytest tests/backend/                    # Backend unit tests
uv run pytest tests/integration/                # Integration tests
uv run pytest tests/test_e2e_complete_flow.py   # End-to-end flow
uv run pytest tests/test_e2e_api_integration.py # API integration

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run e2e tests (bash script)
./tests/run_e2e_tests.sh
```

### Code Quality

```bash
# Linting and formatting
uv run ruff check
uv run ruff format

# Type checking
uv run mypy src
```

## 🏗️ Architecture & Code Structure

### Agent System Core

**Agent Lifecycle** (`src/agents/core/`):

- `base_agent.py`: Abstract base defining agent interface and state management
- `agent_manager.py`: Multi-agent orchestration with concurrent execution control
- `agent_session.py`: Session-based execution tracking with context management
- `models.py`: Type-safe data models (AgentConfig, AgentState, AgentMode, etc.)
- `instruction_generator.py`: Dynamic prompt generation based on agent state
- `strategy_tracker.py`: Strategy evolution tracking and performance monitoring
- `strategy_auto_adjuster.py`: Automatic strategy adjustment based on performance

**Integration Layer** (`src/agents/integrations/`):

- `persistent_agent.py`: Main agent implementation with database persistence
- `database_service.py`: Async database operations wrapper
- `mcp_client.py`: Market data client using MCP protocol
- `openai_tools.py`: AI model integration (OpenAI, Claude, etc.)

**Trading Functions** (`src/agents/functions/`):

- `trading_validation.py`: Pre-trade validation and risk checks
- `market_status.py`: Market hours and trading day verification
- `portfolio_queries.py`: Portfolio analytics and position queries
- `strategy_change_recorder.py`: Strategy change logging and versioning

**Agent Tools** (`src/agents/tools/`):

- `technical_agent.py`: Technical analysis (indicators, patterns)
- `fundamental_agent.py`: Fundamental analysis (financials, ratios)
- `risk_agent.py`: Risk metrics (VaR, Sharpe, drawdown)
- `sentiment_agent.py`: Market sentiment analysis

### API Layer

**FastAPI Application** (`src/api/`):

- `app.py`: Application factory with lifespan management
- `server.py`: Server entry point
- `config.py`: Pydantic settings with environment variables
- `models.py`: API request/response models
- `routers/agents.py`: Agent CRUD and execution endpoints
- `routers/trading.py`: Portfolio, trades, performance endpoints
- `routers/websocket_router.py`: WebSocket endpoint for real-time updates
- `websocket.py`: WebSocket connection manager

### Database Layer

**SQLAlchemy Models** (`src/database/`):

- `models.py`: ORM models using Python 3.12+ syntax with AsyncAttrs
  - `Agent`: Agent metadata and configuration
  - `AgentSession`: Execution session tracking
  - `Transaction`: Trade records with full audit trail
  - `Holding`: Current portfolio positions
  - `PortfolioSnapshot`: Historical portfolio state
  - `StrategyChange`: Strategy evolution history
- `migrations.py`: Database schema initialization and migration logic

### Data Flow Architecture

**Agent Execution Flow**:

1. API Request → `routers/agents.py` (endpoint handler)
2. Agent Manager → `agent_manager.py` (lifecycle management)
3. Trading Agent → `trading_agent.py` (strategy execution)
4. MCP Client → `mcp_client.py` (market data fetch)
5. Trading Functions → validation, execution, recording
6. Database Service → `database_service.py` (persistence)
7. WebSocket → `websocket.py` (real-time broadcast)

**Agent Modes Cycle**:

```
OBSERVATION → TRADING → REBALANCING → STRATEGY_REVIEW → OBSERVATION
```

- **OBSERVATION**: Market analysis and knowledge accumulation
- **TRADING**: Execute trades based on current strategy
- **REBALANCING**: Portfolio adjustment to target allocation
- **STRATEGY_REVIEW**: Performance analysis and strategy evolution

### Key Design Patterns

- **Async-First Architecture**: All I/O operations use async/await
- **Dependency Injection**: Services injected via constructors (database_service, mcp_client)
- **Session Pattern**: Agent execution wrapped in database sessions for atomicity
- **Event Broadcasting**: WebSocket manager broadcasts agent state changes
- **Strategy Evolution**: Performance-driven strategy adjustment with rollback capability

## 🧪 Testing Strategy

### Test Organization

Tests follow the project structure with clear separation:

```
tests/
├── backend/              # Backend unit tests
│   ├── agents/          # Agent system tests
│   │   ├── functions/   # Trading function tests
│   │   └── tools/       # Agent tool tests
│   └── shared/
│       └── database/    # Database integration tests
├── integration/         # MCP and multi-component tests
├── database/           # Database migration tests
└── test_e2e_*.py       # End-to-end workflow tests
```

### Test Categories

- **Unit Tests** (`tests/backend/`): Individual component testing with mocks
- **Integration Tests** (`tests/integration/`): Multi-component interaction
- **Database Tests** (`tests/database/`): Schema validation and migrations
- **E2E Tests** (`tests/test_e2e_*.py`): Complete user workflows

### Test Data

- Use real Taiwan stock symbols: 2330 (台積電), 2412 (中華電), 2454 (聯發科)
- Test accounts start with 1,000,000 TWD initial capital
- Mock MCP responses for predictable testing
- Use in-memory SQLite for test isolation

## 🐛 Common Development Patterns

### Adding New Agent Functions

1. Create function in `src/agents/functions/`
2. Define input/output models in function file
3. Register in agent's `enabled_functions` list
4. Add integration tests in `tests/backend/agents/functions/`

Example:

```python
# src/agents/functions/my_function.py
async def my_function(agent_id: str, param: str) -> dict:
    """Function docstring for AI model."""
    # Implementation
    return {"result": "success"}
```

### Adding New API Endpoints

1. Define request/response models in `src/api/models.py`
2. Add endpoint to appropriate router in `src/api/routers/`
3. Update OpenAPI tags in `src/api/docs.py`
4. Add endpoint tests in `tests/test_e2e_api_integration.py`

### Database Schema Changes

1. Modify models in `src/database/models.py`
2. Update migration logic in `src/database/migrations.py`
3. Test migration in `tests/database/test_migration.py`
4. Run migration: `uv run python -m src.database.migrations`

### Adding New Agent Tools

1. Create tool class in `src/agents/tools/`
2. Inherit from base tool class or define standalone
3. Register tool in agent's tool registry
4. Add tool tests in `tests/backend/agents/tools/`

## 🚀 API Documentation

### Running the API Server

```bash
# Development mode with auto-reload
uv run uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000

# Production mode
uv run uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Endpoints

- **API Docs**: http://localhost:8000/api/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/api/redoc (Alternative documentation)
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json

### Core Endpoints

**Agent Management**:

- `POST /api/agents` - Create agent
- `GET /api/agents` - List all agents
- `GET /api/agents/{agent_id}` - Get agent details
- `DELETE /api/agents/{agent_id}` - Remove agent
- `POST /api/agents/{agent_id}/start` - Start agent
- `POST /api/agents/{agent_id}/stop` - Stop agent
- `POST /api/agents/{agent_id}/execute` - Execute agent cycle

**Trading Data**:

- `GET /api/trading/agents/{agent_id}/portfolio` - Get portfolio
- `GET /api/trading/agents/{agent_id}/trades` - Get trade history
- `GET /api/trading/agents/{agent_id}/performance` - Get performance metrics
- `GET /api/trading/agents/{agent_id}/strategy-changes` - Get strategy evolution

**WebSocket**:

- `WS /ws` - Real-time agent events and state updates

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./casualtrader.db

# CORS
CORS_ORIGINS=["http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true

# Agent Limits
MAX_AGENTS=10
MAX_CONCURRENT_EXECUTIONS=5

# Logging
LOG_LEVEL=INFO
```

## 📋 SpecPilot Workflow Integration

### Workflow Commands

```bash
# Check project status
./scripts/specpilot-workflow.sh status

# Start task
./scripts/specpilot-workflow.sh start-task <task-id>

# Prepare PR
./scripts/specpilot-workflow.sh prepare-pr <task-id> [title]

# Close task
./scripts/specpilot-workflow.sh close-task <task-id> [merge-method]

# Next action
./scripts/specpilot-workflow.sh next-action
```

### Specification Documents

- **PRD** (`specs/prd/`): Product Requirements
- **TSD** (`specs/tsd/`): Technical Specifications
- **Epics** (`specs/epics/`): Feature breakdowns
- **Tasks** (`specs/tasks/`): Development tasks

## 📚 Documentation Structure

### Core Documentation

- **`CLAUDE.md`**: This file - guidance for Claude Code instances
- **`README.md`**: Project overview and FastMCP architecture
- **`docs/PROJECT_STRUCTURE.md`**: Complete project structure reference
- **`docs/AGENT_IMPLEMENTATION.md`**: Agent system implementation details (includes database migration and AI model management)
- **`docs/API_IMPLEMENTATION.md`**: API endpoints and usage guide
- **`docs/FRONTEND_ARCHITECTURE.md`**: Frontend architecture (Svelte)

### Important Notes

- Database migration documentation is consolidated in `docs/AGENT_IMPLEMENTATION.md` under "💾 資料庫管理"
- AI model configuration management is also in `docs/AGENT_IMPLEMENTATION.md`
- Scripts have been unified: use `./scripts/start.sh` instead of separate API/dev scripts

## 🔍 Debugging Tips

### Agent Execution Debugging

```python
# Enable detailed logging in agent execution
import logging
logging.getLogger("agent_manager").setLevel(logging.DEBUG)
logging.getLogger("trading_agent").setLevel(logging.DEBUG)
```

### Database Query Debugging

```python
# Enable SQLAlchemy query logging
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

### WebSocket Connection Testing

```bash
# Test WebSocket endpoint
wscat -c ws://localhost:8000/ws
```

## 📊 Performance Considerations

- **Concurrent Agent Execution**: Limited by `MAX_CONCURRENT_EXECUTIONS` semaphore
- **Database Connection Pool**: Async SQLAlchemy with connection pooling
- **MCP Client Caching**: Market data cached with TTL to reduce API calls
- **WebSocket Broadcasting**: Efficient fanout to connected clients
- **Agent Session Cleanup**: Automatic cleanup of old sessions (configurable retention)

## 🎯 Current Implementation Status

Based on the codebase, the following systems are fully implemented:

- ✅ **Agent Core System**: Multi-agent management with lifecycle control
- ✅ **Database Integration**: SQLAlchemy async ORM with complete schema
- ✅ **FastAPI Backend**: RESTful API + WebSocket support
- ✅ **Trading Functions**: Buy/sell validation, market status, portfolio queries
- ✅ **Strategy Evolution**: Automatic strategy adjustment based on performance
- ✅ **Agent Tools**: Technical, fundamental, risk, sentiment analysis
- ✅ **Session Management**: Database-backed execution tracking
- ✅ **Real-time Events**: WebSocket broadcasting of agent state

## 🔐 Security Notes

- API keys for AI models should be set in environment variables
- Database credentials should not be committed to git
- CORS origins should be restricted in production
- WebSocket connections should be authenticated in production
