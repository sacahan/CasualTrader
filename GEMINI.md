# Developer Guide for CasualTrader

## Project Overview

This project, "CasualTrader", is a Python-based Market Context Protocol (MCP) server designed to provide real-time and simulated trading data for the Taiwanese stock market. It is built using the `FastMCP` framework for simplicity and performance.

The core of the project is a sophisticated AI agent system that can operate in several modes:

* **TRADING:** Actively seeks investment opportunities and executes trades.
* **REBALANCING:** Adjusts the investment portfolio to maintain a desired asset allocation.
* **OBSERVATION:** Monitors the market and gathers data without executing trades.

The project uses a SQLite database to store information about agents, transactions, and performance.

**Key Technologies:**

* **Programming Language:** Python 3.11+
* **Frameworks:** FastMCP, SQLAlchemy
* **AI:** OpenAI Agents
* **Database:** SQLite
* **Package Management:** uv

## Building and Running

### Prerequisites

* Python 3.12+
* `uv` package manager

### Installation

To set up the development environment and install dependencies, run:

```bash
uv sync --dev
```

### Running the MCP Server

The MCP server can be started using the following command:

```bash
uvx --from . market-mcp-server
```

### Running Tests

To run the test suite, use the following command:

```bash
uv run pytest
```

### Linting and Type-Checking

To check the code for style and type errors, run:

```bash
uv run ruff check .
uv run mypy .
```

## Development Conventions

* **Code Style:** The project uses `ruff` for linting and `black` for formatting, with a line length of 88 characters.
* **Type-Hinting:** The project uses `mypy` for static type checking, and all new code should be fully type-hinted.
* **Testing:** The project uses `pytest` for testing. New features should be accompanied by corresponding tests.
* **Database:** The database schema is defined in `src/database/schema.sql`. Any changes to the database schema should be reflected in this file.
* **AI Agents:** The AI agent logic is implemented in the `src/agents` directory. The `AgentManager` class in `src/agents/core/agent_manager.py` is the central point for managing agents. The `TradingAgent` class in `src/agents/trading/trading_agent.py` contains the core trading logic.
* **Python Programming Conventions:** Follow Python 3.12 above style guidelines for Python code. Use meaningful variable and function names, and include docstrings for all public functions and classes.
* **Commenting:** Use Traditional Chinese language comments to explain complex logic, but avoid over-commenting. The code should be self-explanatory where possible.
