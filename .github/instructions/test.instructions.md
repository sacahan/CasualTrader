---
description: "Testing standards and best practices for test development"
applyTo: ["**/test*", "**/tests/**/*", "**/*test*", "**/conftest.py"]
---

# Testing Guidelines

## Key Principles

- **Mock only external dependencies** - databases, APIs, file systems
- **Test real business logic** - don't mock core functionality
- **Verify complete workflows** - unit + integration + E2E
- **Test lifecycle constraints** - initialization, cleanup, state transitions
- **Write meaningful tests** - that fail when production fails
- **Organize tests hierarchically** - unit < integration < E2E
- **Document test intent** - why we test, not just what

---

## MOCK_STRATEGY

### What to Mock

Mock these components to isolate tests:

- **Database connections**: AsyncSession and database queries
- **External APIs**: Third-party service calls, MCP servers
- **File system operations**: File reads/writes that require test environments
- **Network calls**: HTTP requests to external services
- **Time-dependent operations**: Current time, delays (use time mocking)

### What NOT to Mock

These should be tested realistically:

- **Business logic**: Core service methods and workflows
- **Lifecycle management**: Initialization, cleanup, state transitions
- **Constraint checks**: Validation, error handling, preconditions
- **Multi-component interactions**: Service-to-Service or Service-to-Agent communication
- **Real workflows**: Complete execution paths that need verification

### Mock Decision Framework

Ask these questions to decide whether to mock:

1. Is this an external system? YES → Mock it (database, API, file system)
2. Is this business logic that should be tested? YES → Don't mock it
3. Does testing this realistically impact test reliability? YES → Mock it

---

## TEST_ARCHITECTURE

### Layer 1: Unit Tests

**Purpose**: Test individual methods in isolation

**Mock Strategy**: Mock all external dependencies, test single code paths

Example unit test:

```python
def test_agent_initialization_check():
    """Unit test: verify is_initialized flag check"""
    agent = TradingAgent("test", config, mock_db)
    assert agent.is_initialized is False

    with pytest.raises(AgentInitializationError):
        await agent.run(mode=AgentMode.OBSERVATION)
```

**Speed**: < 100ms per test
**Coverage**: Specific logic branches
**Count**: 20-30% of all tests

### Layer 2: Integration Tests

**Purpose**: Test interactions between multiple components

**Mock Strategy**: Mock databases and external APIs, don't mock service interactions

Example integration test:

```python
@pytest.mark.asyncio
async def test_service_manages_agent_lifecycle():
    """Integration test: verify complete lifecycle"""
    service = TradingService(mock_db)

    # Real business logic execution
    await service.execute_single_mode(
        agent_id="test-agent",
        mode=AgentMode.OBSERVATION
    )

    # Verify complete workflow
    assert service.session_service.update_session_status.called
```

**Speed**: 0.5-2 seconds per test
**Coverage**: Component interactions
**Count**: 30-40% of all tests

### Layer 3: E2E Tests

**Purpose**: Test complete workflows from API to database

**Mock Strategy**: Mock database and external APIs for speed/reliability, don't mock business logic

Example E2E test:

```python
@pytest.mark.asyncio
async def test_e2e_initialization_flow():
    """E2E test: verify initialization in full workflow"""
    # Setup mocks for external dependencies only
    service.agents_service.get_agent_config = AsyncMock(...)
    service.session_service.create_session = AsyncMock(...)

    # Let business logic run realistically
    result = await service.execute_single_mode(
        agent_id="test-agent",
        mode=AgentMode.OBSERVATION
    )

    # Verify complete workflow including constraints
    assert result["success"] is True
    assert service.session_service.update_session_status.called
```

**Speed**: 2-5 seconds per test
**Coverage**: Complete workflows
**Count**: 30-50% of all tests

---

## COMMON_ANTI_PATTERNS

### Anti-Pattern 1: Over-Mocking Business Logic

**Wrong Approach**:

```python
# Mocks the core business logic - hides real problems
service._get_or_create_agent = AsyncMock(return_value=mock_agent)
mock_agent.run = AsyncMock(return_value={"success": True})

# Result: Test passes but production fails
```

**Correct Approach**:

```python
# Only mock database access
service.agents_service.get_agent_config = AsyncMock(...)
service.session_service.create_session = AsyncMock(...)

# Let business logic run realistically
```

### Anti-Pattern 2: Skipping Lifecycle Verification

**Wrong Approach**:

```python
# Doesn't verify initialization
agent = TradingAgent(...)
await agent.run()  # May fail in production
```

**Correct Approach**:

```python
# Explicitly verify state transitions
agent = TradingAgent(...)
assert agent.is_initialized is False  # Initial state

await agent.initialize()  # Explicit initialization

await agent.run()  # Now safe to run
```

### Anti-Pattern 3: Testing Mock Infrastructure

**Wrong Approach**:

```python
# Verifies mock was called, not actual behavior
mock_method = AsyncMock()
await service.method()
mock_method.assert_called_once()
```

**Correct Approach**:

```python
# Verify actual effects of execution
result = await service.execute_single_mode(...)
assert result["success"] is True
assert "session_id" in result
```

---

## TEST_NAMING_CONVENTIONS

### Unit Test Naming

Use format: `test_<method>_<scenario>_<expected_result>`

```python
def test_run_without_initialization_raises_error():
    """Test individual method behavior"""
    pass

def test_initialize_sets_is_initialized_true():
    pass

def test_cleanup_removes_from_active_agents():
    pass
```

### Integration Test Naming

Use format: `test_<component1>_<component2>_<interaction>`

```python
@pytest.mark.asyncio
async def test_service_and_agent_lifecycle_management():
    """Test component interactions"""
    pass

@pytest.mark.asyncio
async def test_service_and_database_session_handling():
    pass
```

### E2E Test Naming

Use format: `test_e2e_<workflow>_<verification>`

```python
@pytest.mark.asyncio
async def test_e2e_agent_execution_and_cleanup():
    """Test complete workflow"""
    pass

@pytest.mark.asyncio
async def test_e2e_initialization_before_execution():
    pass
```

---

## ASSERTION_PATTERNS

### Verifying Business Logic

```python
# Verify actual results
assert result["success"] is True
assert "session_id" in result
assert result["mode"] == AgentMode.OBSERVATION.value
```

### Verifying Lifecycle

```python
# Verify state transitions
assert agent.is_initialized is False  # Before
await agent.initialize()
assert agent.is_initialized is True   # After
```

### Verifying Constraints

```python
# Verify preconditions are enforced
with pytest.raises(AgentInitializationError):
    await uninitialized_agent.run()
```

### Verifying External System Calls

```python
# Only mock external system calls (rarely)
service.session_service.update_session_status.assert_called_with(
    session_id, SessionStatus.COMPLETED
)
```

---

## FIXTURES_AND_SETUP

### Database Fixtures

```python
@pytest.fixture
def mock_db_session():
    """Mock AsyncSession for database operations"""
    return AsyncMock()
```

### Configuration Fixtures

```python
@pytest.fixture
def mock_agent_config():
    """Mock Agent configuration from database"""
    config = MagicMock()
    config.id = "test-agent"
    config.ai_model = "gpt-4"
    config.description = "Test agent"
    return config
```

### Service Fixtures

```python
@pytest.fixture
async def trading_service(mock_db_session):
    """Create TradingService with mocked dependencies"""
    service = TradingService(mock_db_session)

    # Only mock external dependencies
    service.agents_service.get_agent_config = AsyncMock(...)
    service.session_service.create_session = AsyncMock(...)

    return service
```

---

## ERROR_HANDLING_IN_TESTS

### Catching Expected Exceptions

```python
@pytest.mark.asyncio
async def test_handles_initialization_error():
    """Verify expected errors are raised"""
    agent = TradingAgent(...)

    with pytest.raises(AgentInitializationError, match="not initialized"):
        await agent.run()
```

### Distinguishing Real Errors from Test Errors

```python
@pytest.mark.asyncio
async def test_execution_error_handling():
    """Verify error doesn't hide the real problem"""
    try:
        await service.execute_single_mode(...)
    except Exception as e:
        # Ensure it's not an initialization error
        assert "not initialized" not in str(e), \
            f"Should not fail with initialization: {e}"
```

---

## TEST_DOCUMENTATION

### Docstring Template

```python
@pytest.mark.asyncio
async def test_e2e_agent_lifecycle():
    """
    Scenario: Verify complete Agent lifecycle management

    Given: TradingService with mocked database
    When:  execute_single_mode() is called
    Then:  Agent is initialized, executed, and cleaned up

    Verifies:
    - initialize() is called before run()
    - is_initialized flag transitions correctly
    - cleanup() is called even on error
    """
    # Test implementation
    pass
```

---

## PERFORMANCE_CONSIDERATIONS

### Test Execution Times

Expected execution times for different test types:

| Test Type | Target | Acceptable | Too Slow |
|-----------|--------|-----------|----------|
| Unit | < 100ms | < 500ms | > 1s |
| Integration | 0.5s | 2s | > 5s |
| E2E | 2s | 5s | > 10s |

### Optimization Strategies

Parallelize tests for faster execution:

```bash
pytest -n auto backend/tests/
```

Cache expensive operations with session-scoped fixtures:

```python
@pytest.fixture(scope="session")
def expensive_resource():
    # Load once per test session
    pass
```

Use fixtures for setup/teardown to avoid duplication:

```python
@pytest.fixture
async def clean_service():
    service = create_service()
    yield service
    await service.cleanup()
```

---

## CI_CD_INTEGRATION

### Running Tests Locally

```bash
# All tests
pytest backend/tests/

# Specific test file
pytest backend/tests/test_e2e_real_integration.py

# With coverage
pytest --cov=backend/src backend/tests/

# Parallel execution
pytest -n auto backend/tests/
```

### GitHub Actions Example

```yaml
- name: Run Tests
  run: |
    pytest backend/tests/ \
      --cov=backend/src \
      --cov-report=xml \
      -v
```

---

## DEBUGGING_TESTS

### Verbose Logging

```python
def test_with_debug_logging(caplog):
    """Capture and verify log messages"""
    import logging
    caplog.set_level(logging.DEBUG)

    # Your test code

    assert "Initializing agent" in caplog.text
```

### Printing Debug Information

```python
@pytest.mark.asyncio
async def test_with_debug(capsys):
    """Capture print output for debugging"""
    # Your test code

    captured = capsys.readouterr()
    print(f"Debug output: {captured.out}")
```

### Inspecting Mock Calls

```python
def test_with_inspection(mocker):
    """Use mocker to inspect calls"""
    mock = mocker.MagicMock()

    # Call code with mock

    # Inspect all calls
    print(mock.call_args_list)
```

---

## IMPORTANT_LEARNINGS

### Over-Mocking Problem

Over-mocking business logic hides real problems instead of preventing them:

- Tests pass but production fails (false negative)
- Root cause: Mocks return hardcoded values, not actual behavior
- Solution: Only mock external dependencies

### Lifecycle Management

Agent-based systems require explicit lifecycle:

- **Create**: Instantiate the agent
- **Initialize**: Call `await agent.initialize()`
- **Execute**: Call `await agent.run()`
- **Cleanup**: Call `await agent.cleanup()`

Missing any step causes runtime errors that tests should catch.

### Layered Testing Strategy

Don't try to test everything at every layer:

- **Unit tests** (20-30%): Test isolated methods with full mocking
- **Integration tests** (30-40%): Test component interactions with minimal mocking
- **E2E tests** (30-50%): Test complete workflows with only external deps mocked

This approach balances speed, reliability, and coverage.

---

## RELATED_DOCUMENTS

- `python.instructions.md` - Python development standards
- `timestamp.instructions.md` - Timestamp management in tests
- Project test strategy files in root documentation
