---
description: "Testing standards and best practices for test development"
applyTo: ["**/test*", "**/tests/**/*", "**/*test*", "**/conftest.py"]
---

# Testing Guidelines

## Core Principles

- **Mock only external dependencies**: databases, APIs, file systems
- **Test real business logic**: don't mock core functionality
- **Verify complete workflows**: unit → integration → E2E
- **Test lifecycle constraints**: initialization, cleanup, state transitions
- **Organize tests hierarchically**: 20-30% unit, 30-40% integration, 30-50% E2E
- **Write meaningful assertions**: verify actual behavior, not mock calls

## Mock Strategy

| Category | Mock? | Rationale |
|----------|-------|-----------|
| Database connections | ✅ | External system |
| External APIs/HTTP | ✅ | External system |
| File system | ✅ | External system |
| Business logic | ❌ | Core functionality to test |
| Service interactions | ❌ | Integration point |
| Lifecycle management | ❌ | State transitions to verify |

## Test Architecture

### Unit Tests (< 100ms each)

Test individual methods in isolation.

```python
def test_agent_initialization_check():
    """Verify initial state and constraints"""
    agent = TradingAgent("test", config, mock_db)
    assert agent.is_initialized is False

    with pytest.raises(AgentInitializationError):
        await agent.run(mode=AgentMode.OBSERVATION)
```

**Mock Strategy**: All external dependencies
**Count**: 20-30% of all tests

### Integration Tests (0.5-2s each)

Test component interactions.

```python
@pytest.mark.asyncio
async def test_service_manages_agent_lifecycle():
    """Verify multi-component workflow"""
    service = TradingService(mock_db)

    await service.execute_single_mode(
        agent_id="test-agent",
        mode=AgentMode.OBSERVATION
    )

    assert service.session_service.update_session_status.called
```

**Mock Strategy**: External APIs and databases only
**Count**: 30-40% of all tests

### E2E Tests (2-5s each)

Test complete workflows.

```python
@pytest.mark.asyncio
async def test_e2e_initialization_flow():
    """Verify complete execution path"""
    service.agents_service.get_agent_config = AsyncMock(...)
    service.session_service.create_session = AsyncMock(...)

    result = await service.execute_single_mode(
        agent_id="test-agent",
        mode=AgentMode.OBSERVATION
    )

    assert result["success"] is True
    assert service.session_service.update_session_status.called
```

**Mock Strategy**: External dependencies only
**Count**: 30-50% of all tests

## Naming Conventions

- **Unit**: `test_<method>_<scenario>_<expected_result>`
- **Integration**: `test_<component1>_<component2>_<interaction>`
- **E2E**: `test_e2e_<workflow>_<verification>`

Example: `test_e2e_agent_execution_and_cleanup`

## Assertion Best Practices

```python
# Verify actual results, not mock calls
assert result["success"] is True
assert "session_id" in result

# Verify state transitions
assert agent.is_initialized is False  # Before
await agent.initialize()
assert agent.is_initialized is True   # After

# Verify constraints
with pytest.raises(AgentInitializationError):
    await uninitialized_agent.run()
```

## Fixtures

```python
@pytest.fixture
async def trading_service(mock_db_session):
    """Service with mocked external dependencies"""
    service = TradingService(mock_db_session)
    service.agents_service.get_agent_config = AsyncMock(...)
    service.session_service.create_session = AsyncMock(...)
    return service

@pytest.fixture
async def clean_service(trading_service):
    """Service with cleanup"""
    yield trading_service
    await trading_service.cleanup()
```

## API Contract Testing

Validate response schemas to prevent serialization issues.

```python
def test_list_agents_response_schema():
    """Verify API contract compliance"""
    response = client.get("/api/agents")
    assert response.status_code == 200

    data = response.json()
    for agent in data:
        assert isinstance(agent["investment_preferences"], list)
        assert isinstance(agent["enabled_tools"], dict)
        assert isinstance(agent["id"], str)
```

Test complete CRUD cycles with data integrity:

```python
async def test_agent_crud_lifecycle():
    """Verify data consistency across operations"""
    # Create
    create_resp = await client.post("/api/agents", json={
        "name": "Test",
        "investment_preferences": "2330,2454"
    })
    agent = create_resp.json()
    assert isinstance(agent["investment_preferences"], list)

    # Read & Update
    get_resp = await client.get(f"/api/agents/{agent['id']}")
    assert get_resp.json()["investment_preferences"] == agent["investment_preferences"]

    # Delete
    delete_resp = await client.delete(f"/api/agents/{agent['id']}")
    assert delete_resp.status_code == 204
```

## Common Pitfalls

| Issue | ❌ Wrong | ✅ Correct |
|-------|---------|-----------|
| Over-mocking | Mock business logic | Mock only external deps |
| Lifecycle | Skip initialization | Explicitly verify state transitions |
| Assertions | Verify mock was called | Verify actual behavior |
| Speed | Slow unit tests | Mock external dependencies |
| Reliability | Hardcoded test data | Use fixtures for consistency |
