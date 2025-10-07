# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📊 Project Overview

CasualTrader is a Market MCP Server providing real-time Taiwan stock price data through the Model Context Protocol. The project integrates with Taiwan Stock Exchange (TWSE) APIs and provides a standardized interface for stock price queries via MCP tools.

### Architecture Summary

- **MCP Server Core**: Python-based server implementing Model Context Protocol
- **Taiwan Stock API Integration**: Real-time stock price queries via TWSE APIs
- **Cache & Rate Limiting**: Multi-tier rate limiting and caching for API protection
- **SpecPilot Workflow**: AI-driven specification management and task execution system

## 🔧 Development Commands

### Environment Setup

```bash
# Install dependencies using uv
uv sync --dev

# Run the MCP server locally for testing
uvx --from . market-mcp-server
# or
uv run python -m market_mcp.server
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run python tests/debug_api.py                 # Debug API functionality
uv run python tests/test_mcp_tools.py            # Test MCP tool functionality
uv run python tests/verify_mcp_integration.py    # Verify MCP integration

# Test uvx execution
./tests/test_uvx_execution.sh
```

### Code Quality

```bash
# Linting and formatting
uv run ruff check
uv run ruff format

# Type checking
uv run mypy market_mcp
```

### MCP Server Testing

```bash
# Verify MCP server functionality
./tests/verify-mcp-server.sh

# Basic functionality test
uv run python tests/test_basic_functionality.py
```

## 🏗️ Architecture & Code Structure

### Core Components

**MCP Server Implementation** (`market_mcp/server.py`):

- Main MCP protocol handler using official MCP Python SDK
- Tool registration and dispatch system
- Stdio-based communication with MCP clients

**Stock Price Tool** (`market_mcp/tools/stock_price_tool.py`):

- Primary tool implementation for Taiwan stock price queries
- Integrates validation, API client, error handling, and response formatting
- Supports both regular stocks (4-digit codes) and ETFs (4-6 digit + letters)

**API Client Layer** (`market_mcp/api/`):

- `twse_client.py`: Basic TWSE API integration
- `enhanced_twse_client.py`: Advanced client with rate limiting and caching
- Handles HTTP requests, response parsing, and error handling

**Cache & Rate Limiting** (`market_mcp/cache/`):

- `rate_limiter.py`: Token bucket rate limiting implementation
- `cache_manager.py`: Memory-based caching with TTL
- `rate_limited_cache_service.py`: Combined rate limiting and caching service

### Entry Points

**uvx Execution** (`market_mcp/main.py`):

- Primary entry point for `uvx --from . market-mcp-server` command
- Handles startup, shutdown, and error handling

**Module Execution** (`market_mcp/server.py`):

- Alternative entry point for `python -m market_mcp.server`
- Same functionality as main.py but different invocation path

### Data Flow Architecture

1. **MCP Client Request** → `server.py` (protocol handling)
2. **Tool Dispatch** → `stock_price_tool.py` (business logic)
3. **Input Validation** → `validators/input_validator.py`
4. **API Call** → `api/enhanced_twse_client.py` (with caching/rate limiting)
5. **Response Formatting** → `models/mcp_responses.py`
6. **Error Handling** → `handlers/error_handler.py`

### Key Design Patterns

- **Layered Architecture**: Clear separation between MCP protocol, business logic, and data access
- **Dependency Injection**: Components receive dependencies through constructor injection
- **Error Boundary Pattern**: Centralized error handling with contextual error responses
- **Cache-Aside Pattern**: Manual cache management with fallback to API calls

## 📋 SpecPilot Workflow Integration

This project uses SpecPilot for AI-driven development workflow management:

### Workflow Commands

```bash
# Check project status and get recommendations
./scripts/specpilot-workflow.sh status

# Start working on a specific task
./scripts/specpilot-workflow.sh start-task <task-id>

# Prepare pull request after development
./scripts/specpilot-workflow.sh prepare-pr <task-id> [title]

# Complete task (merge PR and cleanup)
./scripts/specpilot-workflow.sh close-task <task-id> [merge-method]

# Get next recommended action
./scripts/specpilot-workflow.sh next-action
```

### Specification Documents

- **PRD** (`specs/prd/`): Product Requirements Documents
- **TSD** (`specs/tsd/`): Technical Specification Documents
- **Epics** (`specs/epics/`): Feature module breakdowns
- **Tasks** (`specs/tasks/`): Specific development tasks

### Development Workflow

1. Tasks are managed in isolated git worktrees (`workspaces/<task-id>/`)
2. Each task has its own feature branch (`<task-id>-feature`)
3. Status tracking in spec files (new → in_progress → review → done)
4. Automated PR creation with generated content from task specifications

## 🚀 Deployment & Integration

### Claude Desktop Integration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "casualtrader": {
      "command": "uvx",
      "args": ["--from", "/path/to/CasualTrader", "market-mcp-server"],
      "env": { "MARKET_MCP_SERVER_VERSION": "1.0.0" }
    }
  }
}
```

### Environment Variables

```bash
# Server configuration
export MARKET_MCP_SERVER_VERSION=1.0.0
export LOG_LEVEL=INFO

# API settings
export MARKET_MCP_API_TIMEOUT=5
export MARKET_MCP_API_RETRIES=3

# Rate limiting
export MARKET_MCP_RATE_LIMIT_PER_SYMBOL=30
export MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE=20

# Caching
export MARKET_MCP_CACHE_TTL=30
export MARKET_MCP_CACHE_MAXSIZE=1000
```

## 🧪 Testing Strategy

### Test Categories

- **Unit Tests**: Individual component testing with minimal mocking
- **Integration Tests**: MCP server and tool integration testing
- **API Tests**: TWSE API integration and response parsing
- **Rate Limiting Tests**: Cache and rate limiting functionality

### Test Data

- Use real Taiwan stock symbols (2330, 2317, 2454, etc.) for integration tests
- Mock external API calls for unit tests
- Test both success and error scenarios

### Performance Benchmarks

- API response time: < 2 seconds under normal conditions
- uvx startup time: < 10 seconds
- Memory usage: < 100MB for basic operations
- Rate limiting: 30 requests per symbol, 20 global per minute

## 🐛 Common Development Patterns

### Adding New Stock Data Fields

1. Update `market_mcp/models/stock_data.py` data model
2. Modify parser in `market_mcp/parsers/twse_parser.py`
3. Update response formatter in `market_mcp/models/mcp_responses.py`
4. Add tests in `tests/test_parser.py`

### Error Handling

- All exceptions should be handled through `MCPErrorHandler`
- Use `safe_execute` decorator for automatic error boundary handling
- Provide contextual error messages with suggested fixes

### Adding New Tools

1. Create tool class in `market_mcp/tools/`
2. Implement required methods: `get_tool_definition()`, main tool function
3. Register in `market_mcp/server.py`
4. Add comprehensive tests in `tests/`

## 📊 Development Status Tracking

Current implementation focuses on Task-001 through Task-004:

- ✅ **Task-001**: MCP Server基礎架構 (Complete)
- 🔧 **Task-002**: 台灣證交所 API 整合 (In Progress)
- 📋 **Task-003**: API 頻率限制和快取系統 (Planned)
- 🔧 **Task-004**: MCP 工具介面標準化 (In Progress)

Use SpecPilot workflow commands to check current status and get next recommended actions.
- 測試相關的 py 檔都收納到 test/ 內
