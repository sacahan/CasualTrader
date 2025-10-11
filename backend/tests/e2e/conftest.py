"""
E2E Test Fixtures and Configuration

Provides shared fixtures for end-to-end testing including:
- Test database setup
- Test API client
- Mock MCP server
- Agent lifecycle management
"""

import asyncio
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.app import create_app
from src.database.models import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database for each test function.

    Uses in-memory SQLite for fast test execution.
    """
    # Create in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture(scope="function")
def test_client():
    """Create a test client for API testing."""
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def mock_env_vars(monkeypatch):
    """Set up test environment variables."""
    test_vars = {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
    }

    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)

    return test_vars


@pytest.fixture(scope="function")
async def cleanup_agents(test_client):
    """Cleanup all agents after test."""
    yield

    # Cleanup: Delete all test agents
    try:
        response = test_client.get("/api/agents")
        if response.status_code == 200:
            agents = response.json().get("agents", [])
            for agent in agents:
                test_client.delete(f"/api/agents/{agent['id']}")
    except Exception:
        pass  # Ignore cleanup errors
