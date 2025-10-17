# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📊 Project Overview

CasualTrader is an AI-powered trading simulation platform that combines:

- **FastAPI Backend**: RESTful API + WebSocket real-time communication
- **AI Trading Agents**: Multi-model support (GPT-4, Claude, Gemini, DeepSeek) with dynamic strategy evolution
- **MCP Integration**: Market data via Model Context Protocol (casual-market-mcp)
- **Database Persistence**: SQLAlchemy async ORM with SQLite support
- **Frontend Dashboard**: Svelte 5 + Vite + Chart.js for real-time visualization
- **Monorepo Structure**: Unified backend + frontend codebase

### Core Architecture

The system uses a **service-oriented layered architecture**:

- **Trading Agent** (`backend/src/trading/trading_agent.py`): Main AI agent with strategy execution and decision-making
- **Trading Tools** (`backend/src/trading/tools/`): Specialized analysis agents (technical, fundamental, risk, sentiment)
- **Service Layer** (`backend/src/service/`): Business logic and agent lifecycle management
- **API Layer** (`backend/src/api/`): FastAPI routers and WebSocket communication
- **Database Layer** (`backend/src/database/`): SQLAlchemy async ORM models and migrations

### MCP Integration (Model Context Protocol)

**CasualMarket MCP Server** provides Taiwan stock market data:

- **Market Data Tools**: Real-time stock prices, trading info, market indices
- **Financial Analysis**: Company profiles, financial statements (income/balance sheet)
- **Portfolio Management**: Simulated trading operations (buy/sell with fee calculation)
- **Market Analytics**: Margin trading info, dividend schedules, valuation ratios

Trading Agents connect to the Casual Market MCP server directly via the OpenAI Agent SDK's `mcp_servers` parameter. This provides access to:

- Real-time Taiwan stock prices and trading data
- Company financial statements and analysis
- Simulated trading execution with accurate fee calculation
- Market calendar and trading day verification

**MCP Server Configuration Example:**

```python
from agents import Agent

agent = Agent(
    name="Trading Agent",
    instructions="...",
    tools=[...],
    mcp_servers={
        "casual-market": {
            "command": "uvx",
            "args": ["casual-market-mcp"]
        }
    }
)
```

## 🔧 Development Commands

### Quick Start

```bash
# From project root - Start both frontend and backend (recommended)
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
# Backend setup (from backend/ directory)
cd backend
uv sync --dev

# Frontend setup (from frontend/ directory)
cd frontend
npm install

# Run database migrations (from project root or backend/)
./scripts/db_migrate.sh up
# or
cd backend && uv run python -m src.database.migrations

# Start FastAPI server manually (from backend/)
cd backend
uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Start frontend dev server manually (from frontend/)
cd frontend
npm run dev
```

### Testing

```bash
# Run all backend tests (from backend/)
cd backend
uv run pytest

# Run specific test files
uv run pytest tests/test_core_imports.py
uv run pytest tests/test_complete_verification.py
uv run pytest tests/test_trading_integration.py

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run with verbose output
uv run pytest -v

# Run frontend tests (from frontend/)
cd frontend
npm run check        # Type checking
npm run build        # Build test
```

### Code Quality

```bash
# Backend linting and formatting (from backend/)
cd backend
uv run ruff check src/
uv run ruff format src/

# Type checking
uv run mypy src/

# Frontend linting (from frontend/)
cd frontend
npm run check        # Svelte type checking
```

## 🏗️ Architecture & Code Structure

### Backend Structure (`backend/src/`)

**Trading Agent System** (`backend/src/trading/`):

- `trading_agent.py`: Main AI trading agent with OpenAI Agent SDK integration
- `config.py`: Trading agent configuration and parameters
- `models.py`: Trading-related data models (AgentState, Position, etc.)
- `state.py`: Agent state management and tracking
- `tools/`: Specialized analysis agents
  - `technical_agent.py`: Technical analysis (indicators, patterns)
  - `fundamental_agent.py`: Fundamental analysis (financials, ratios)
  - `risk_agent.py`: Risk metrics (VaR, Sharpe, drawdown)
  - `sentiment_agent.py`: Market sentiment analysis
  - `trading_tools.py`: Trading execution and portfolio queries

**Service Layer** (`backend/src/service/`):

- Business logic for agent lifecycle management
- Session management and execution control
- Integration with database and trading systems

**API Layer** (`backend/src/api/`):

- `app.py`: FastAPI application factory with lifespan management
- `config.py`: Pydantic settings with environment variables
- `docs.py`: OpenAPI documentation tags
- `models.py`: API request/response Pydantic models
- `websocket.py`: WebSocket connection manager
- `routers/`:
  - `agents.py`: Agent CRUD endpoints
  - `agent_execution.py`: Agent execution and control endpoints
  - `trading.py`: Portfolio, trades, performance endpoints
  - `ai_models.py`: AI model configuration endpoints
  - `websocket_router.py`: WebSocket endpoint

**Database Layer** (`backend/src/database/`):

- `models.py`: SQLAlchemy async ORM models
  - `Agent`: Agent metadata and configuration
  - `AgentSession`: Execution session tracking
  - `Transaction`: Trade records with audit trail
  - `AgentHolding`: Current portfolio positions
  - `PortfolioSnapshot`: Historical portfolio state
  - `AIModel`: AI model configurations
- `migrations.py`: Database schema migrations and versioning
- `schema.sql`: SQL schema reference

**Common Layer** (`backend/src/common/`):

- Shared utilities and helper functions
- Common data models and types

**Schemas** (`backend/src/schemas/`):

- Shared Pydantic schemas for data validation
- Cross-layer data transfer objects

### Frontend Structure (`frontend/src/`)

**Components** (`frontend/src/components/`):

- `Agent/`: Agent-related UI components
- `Chart/`: Chart.js visualization components
- `Layout/`: Page layout and structure
- `Market/`: Market data display components
- `UI/`: Reusable UI components

**Libraries** (`frontend/src/lib/`):

- `api/`: API client functions
- `api.js`: Common API utilities
- `constants.js`: Application constants
- `utils.js`: Helper functions

**Stores** (`frontend/src/stores/`):

- Svelte stores for state management
- WebSocket connection state
- Agent and portfolio data

**Types** (`frontend/src/types/`):

- TypeScript type definitions
- API response types

### Data Flow Architecture

**Agent Execution Flow**:

1. API Request → `api/routers/agent_execution.py`
2. Service Layer → Business logic and validation
3. Trading Agent → `trading/trading_agent.py` (OpenAI Agent SDK)
4. MCP Tools → Direct calls to casual-market-mcp via Agent SDK
5. Trading Tools → Sub-agents for analysis (technical, fundamental, risk, sentiment)
6. Database → Persist state, transactions, holdings
7. WebSocket → Broadcast updates to connected frontend clients

**Trading Agent Workflow**:

```
1. Initialize Agent → Load strategy and state
2. Analyze Market → Call MCP tools for data
3. Consult Sub-Agents → Technical/Fundamental/Risk/Sentiment analysis
4. Make Decision → Based on strategy and analysis
5. Execute Trade → Validate and record transaction
6. Update State → Persist to database
7. Broadcast Event → WebSocket to frontend
```

### Key Design Patterns

- **Async-First Architecture**: All I/O operations use async/await (Python), promises (JS)
- **Factory Pattern**: FastAPI app creation, agent initialization
- **Service Layer Pattern**: Business logic separated from API layer
- **Repository Pattern**: Database operations encapsulated in service classes
- **Observer Pattern**: WebSocket broadcasts for real-time updates
- **Strategy Pattern**: Trading strategy as configurable parameters
- **MCP Integration**: Direct MCP server integration via OpenAI Agent SDK's `mcp_servers` parameter

## 🧪 Testing Strategy

### Test Organization

```
backend/tests/
├── test_core_imports.py              # Core module import verification
├── test_complete_verification.py     # Complete system verification
├── test_trading_integration.py       # Trading system integration
├── test_trading_tools_standalone.py  # Trading tools unit tests
├── test_trading_tools.py             # Trading tools integration
├── test_full_import.py               # Full module import tests
├── test_imports.py                   # Import validation
└── test_import.py                    # Basic import tests

frontend/tests/
└── (Frontend test suite to be implemented)
```

### Test Categories

- **Core Import Tests**: Verify all modules can be imported without errors
- **Integration Tests**: Multi-component interaction and data flow
- **Trading Tests**: Trading agent, tools, and execution logic
- **Verification Tests**: Complete system functionality validation

### Test Execution

- Run tests from `backend/` directory
- Use `pytest` with async support via `pytest-asyncio`
- Tests use in-memory SQLite for isolation
- Mock MCP responses for predictable testing

### Test Data

- Use real Taiwan stock tickers: 2330 (台積電), 2412 (中華電), 2454 (聯發科)
- Test accounts start with 1,000,000 TWD initial capital
- Mock external API calls and MCP responses
- Use fixtures for common test data setup

## 🐛 Common Development Patterns

### Adding New Trading Tools (Sub-Agents)

1. Create new tool file in `backend/src/trading/tools/`
2. Define the agent function with proper docstring for AI understanding
3. Register tool in `trading_agent.py`'s tool list
4. Add tests in `backend/tests/`

Example:

```python
# backend/src/trading/tools/my_analysis_agent.py
def analyze_something(ticker: str, agent_id: str) -> dict:
    """
    Analyze something about a stock.

    Args:
        ticker: Stock ticker symbol
        agent_id: Agent identifier

    Returns:
        Analysis results with recommendations
    """
    # Implementation
    return {"analysis": "result", "recommendation": "action"}
```

### Adding New API Endpoints

1. Choose appropriate router in `backend/src/api/routers/`
2. Define request/response models in `backend/src/api/models.py` or create schema in `backend/src/schemas/`
3. Implement endpoint with proper error handling
4. Update OpenAPI tags in `backend/src/api/docs.py`
5. Test endpoint manually via Swagger UI at http://localhost:8000/api/docs

Example:

```python
# backend/src/api/routers/my_router.py
from fastapi import APIRouter, HTTPException
from ..models import MyRequest, MyResponse

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

@router.post("/action", response_model=MyResponse)
async def perform_action(request: MyRequest):
    """Perform some action."""
    # Implementation
    return MyResponse(result="success")
```

### Database Schema Changes

1. Modify ORM models in `backend/src/database/models.py`
2. Create new migration in `backend/src/database/migrations.py`
3. Update version number and migration logic
4. Run migration: `./scripts/db_migrate.sh up` or `cd backend && uv run python -m src.database.migrations`
5. Verify schema with `./scripts/db_migrate.sh status`

### Adding Frontend Components

1. Create component in `frontend/src/components/` (organized by feature)
2. Use Svelte 5 syntax with proper TypeScript types
3. Import and use in parent components or `App.svelte`
4. Style with Tailwind CSS classes
5. Test in browser with hot reload

Example:

```svelte
<!-- frontend/src/components/MyComponent.svelte -->
<script>
  let { data = [] } = $props();
  let count = $state(0);
</script>

<div class="p-4 bg-white rounded shadow">
  <h2 class="text-xl font-bold">{count}</h2>
  <button onclick={() => count++} class="btn btn-primary">
    Increment
  </button>
</div>
```

## 🚀 API Documentation

### Running the API Server

```bash
# From backend/ directory
cd backend

# Development mode with auto-reload (recommended)
uv run uvicorn src.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

# Or use the start script from project root
cd ..
./scripts/start.sh -b

# Production mode (multiple workers)
cd backend
uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --workers 4
```

### API Documentation URLs

- **API Docs**: http://localhost:8000/api/docs (Swagger UI - Interactive)
- **ReDoc**: http://localhost:8000/api/redoc (Alternative documentation)
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json (JSON schema)
- **Health Check**: http://localhost:8000/api/health (Server status)

### Core Endpoints

**Agent Management** (`/api/agents`):

- `POST /api/agents` - Create new trading agent
- `GET /api/agents` - List all agents
- `GET /api/agents/{agent_id}` - Get agent details
- `PATCH /api/agents/{agent_id}` - Update agent configuration
- `DELETE /api/agents/{agent_id}` - Delete agent

**Agent Execution** (`/api/agent-execution`):

- `POST /api/agent-execution/agents/{agent_id}/start` - Start agent execution
- `POST /api/agent-execution/agents/{agent_id}/stop` - Stop agent execution
- `POST /api/agent-execution/agents/{agent_id}/execute` - Execute one agent cycle
- `GET /api/agent-execution/agents/{agent_id}/status` - Get execution status

**Trading Data** (`/api/trading`):

- `GET /api/trading/agents/{agent_id}/portfolio` - Get current portfolio
- `GET /api/trading/agents/{agent_id}/transactions` - Get transaction history
- `GET /api/trading/agents/{agent_id}/holdings` - Get current holdings
- `GET /api/trading/agents/{agent_id}/performance` - Get performance metrics

**AI Models** (`/api/ai-models`):

- `GET /api/ai-models` - List available AI models
- `GET /api/ai-models/{model_id}` - Get model details

**WebSocket** (`/ws`):

- `WS /ws` - Real-time agent events and state updates

### Environment Variables

Located in `backend/.env` (copy from `backend/.env.example`):

```bash
# OpenAI API (required for AI agents)
OPENAI_API_KEY=your-api-key-here

# MCP Server Configuration
MCP_CASUAL_MARKET_COMMAND=uvx
MCP_CASUAL_MARKET_ARGS=["casual-market-mcp"]
MCP_CASUAL_MARKET_TIMEOUT=10
MCP_CASUAL_MARKET_RETRIES=5

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# Database
DATABASE_URL=sqlite+aiosqlite:///casualtrader.db
DATABASE_ECHO=false

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
CORS_ALLOW_CREDENTIALS=true

# Agent Configuration
MAX_AGENTS=10
DEFAULT_AI_MODEL=gpt-4o-mini
DEFAULT_INITIAL_CAPITAL=1000000
DEFAULT_MAX_TURNS=30
DEFAULT_AGENT_TIMEOUT=300
DEFAULT_SUBAGENT_MAX_TURNS=15

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>
LOG_FILE=logs/api_{time:YYYY-MM-DD}.log
LOG_ROTATION=500 MB
LOG_RETENTION=30 days

# Environment
ENVIRONMENT=development
DEBUG=true
```

## 📚 Documentation Structure

### Core Documentation

- **`CLAUDE.md`**: This file - guidance for Claude Code instances
- **`README.md`**: Project overview, quick start, and documentation roadmap
- **`backend/.env.example`**: Environment variable template with detailed explanations
- **`docs/`**: Technical documentation (architecture, implementation, deployment guides)

### Quick Reference

- **Backend Entry Point**: `backend/src/api/app.py` (FastAPI application factory)
- **Trading Agent**: `backend/src/trading/trading_agent.py` (Main AI agent logic)
- **Database Models**: `backend/src/database/models.py` (SQLAlchemy ORM)
- **API Routers**: `backend/src/api/routers/` (REST endpoints)
- **Frontend Entry**: `frontend/src/App.svelte` (Main Svelte component)

### Scripts

- **`./scripts/start.sh`**: Unified development server launcher (frontend + backend)
- **`./scripts/db_migrate.sh`**: Database migration management tool

## 🔍 Debugging Tips

### Backend Debugging

```bash
# Enable debug logging (in backend/.env)
LOG_LEVEL=DEBUG
DEBUG=true
DATABASE_ECHO=true  # Show SQL queries

# Run with verbose pytest output
cd backend
uv run pytest -v -s

# Check API health
curl http://localhost:8000/api/health

# View API logs
tail -f backend/logs/api_*.log
```

### Database Debugging

```bash
# Check migration status
./scripts/db_migrate.sh status

# View database schema
cd backend
sqlite3 casualtrader.db ".schema"

# Query agents
sqlite3 casualtrader.db "SELECT * FROM agents;"

# Enable SQLAlchemy echo (shows all SQL queries)
# In backend/.env: DATABASE_ECHO=true
```

### Frontend Debugging

```bash
# Run dev server with verbose output
cd frontend
npm run dev

# Check Svelte syntax
npm run check

# Build and check for errors
npm run build
```

### WebSocket Testing

```bash
# Using websocat (install: brew install websocat)
websocat ws://localhost:8000/ws

# Using wscat (install: npm install -g wscat)
wscat -c ws://localhost:8000/ws

# Using Python
python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        msg = await ws.recv()
        print(f'Received: {msg}')

asyncio.run(test())
"
```

### Common Issues

**Port Already in Use**:

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use the start script which handles this
./scripts/start.sh
```

**Database Locked**:

```bash
# Close all connections and restart
cd backend
rm casualtrader.db
uv run python -m src.database.migrations
```

**MCP Connection Issues**:

```bash
# Test MCP server directly
uvx casual-market-mcp

# Check MCP configuration in backend/.env
# Ensure OPENAI_API_KEY is set
```

## 📊 Project Status & Implementation Notes

### Monorepo Structure

CasualTrader uses a monorepo structure with backend and frontend in separate directories:

```
CasualTrader/
├── backend/          # Python FastAPI backend
├── frontend/         # Svelte 5 frontend
├── scripts/          # Unified development scripts
├── docs/            # Technical documentation
└── CLAUDE.md        # This file
```

### Key Implementation Details

**Backend (Python 3.12+)**:

- Uses `uv` for dependency management (fast pip replacement)
- Async-first with SQLAlchemy 2.0+ async API
- OpenAI Agent SDK for AI agent orchestration
- MCP integration via `casual-market-mcp` package
- Pydantic v2 for data validation and settings

**Frontend (Svelte 5 + Vite)**:

- Modern Svelte 5 syntax with runes (`$state`, `$props`, `$derived`)
- Vite for fast HMR and builds
- Chart.js for data visualization
- WebSocket client for real-time updates
- Tailwind CSS for styling

**Database**:

- SQLite with async driver (`aiosqlite`)
- Versioned migrations via `migrations.py`
- ORM models use Python 3.12+ type syntax
- Database file: `backend/casualtrader.db`

**Development Workflow**:

1. Use `./scripts/start.sh` to launch both backend and frontend
2. Backend auto-reloads on code changes (uvicorn --reload)
3. Frontend has HMR via Vite
4. Database migrations via `./scripts/db_migrate.sh`

### Performance Considerations

- **Async I/O**: All database and API operations are async
- **Agent Concurrency**: Controlled by `MAX_AGENTS` setting
- **WebSocket Broadcasting**: Efficient message distribution to connected clients
- **MCP Client**: Market data fetched on-demand via MCP protocol
- **Database**: Single SQLite file, suitable for development and moderate production use

### Important Notes

- **Working Directory**: Most commands assume you're in the project root or appropriate subdirectory
- **Environment Variables**: Backend requires `OPENAI_API_KEY` at minimum
- **MCP Server**: Requires `casual-market-mcp` package (installed via `uvx`)
- **Python Version**: Requires Python 3.12+ for modern syntax features
- **Node Version**: Requires Node.js 18+ for frontend

### Security Considerations

- API keys should be in `backend/.env`, never committed to git
- CORS origins should be restricted in production
- WebSocket connections should add authentication in production
- Rate limiting should be enabled for production use
