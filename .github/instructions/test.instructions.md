---
description: "Testing standards and best practices for test development"
applyTo: ["**/test*", "**/tests/**/*", "**/*test*", "**/conftest.py"]
---

# Testing Guidelines

## ⚠️ Critical Principle: Never Mask Problems with Skip

**Skip markers (`@pytest.mark.skip`, `@pytest.mark.xfail`) are NOT for hiding architectural problems.**

When you can't test something:

- ❌ **Don't**: Add `@pytest.mark.skip` to pretend it's tested
- ✅ **Do**: Either fix the architecture, test through a framework, or delete the test + document the limitation

See [Anti-Pattern: Masking Problems with Skip](#anti-pattern-masking-problems-with-skip) below for details.

---

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

- **Mock Strategy**: All external dependencies
- **Count**: 20-30% of all tests

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

- **Mock Strategy**: External APIs and databases only
- **Count**: 30-40% of all tests

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

- **Mock Strategy**: External dependencies only
- **Count**: 30-50% of all tests

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

## Anti-Pattern: Masking Problems with Skip

### ❌ What NOT to Do

**Never use `@pytest.mark.skip` or `@pytest.mark.xfail` to hide architectural problems.**

```python
# ❌ Anti-pattern: Masking Problems
@pytest.mark.skip(reason="Cannot directly call @function_tool decorated functions")
def test_tool_robustness():
    """This doesn't solve the problem, it just hides it"""
    from tools import calculate_financial_ratios
    result = calculate_financial_ratios()  # This raises TypeError
    assert result is not None
```

**Problems**:

1. **Masks architectural limitations** - Skip 40 tests and pretend there's no problem
2. **Wastes code** - Test files become useless code
3. **Misleads developers** - Appears to have 40 tests, actually 0 run
4. **Cart before horse** - "Why do we need this file if everything's skipped?"

### ✅ What to Do Instead

**Three options when facing architectural constraints:**

#### 1️⃣ **Redesign to Support Testing** (Best)

If the architecture can't be tested directly, redesign it:

```python
# ✅ Changed design to support testing
from agents import FunctionTool

# Original design: @function_tool decorator prevents direct calls
@function_tool
def calculate_financial_ratios(ticker: str) -> dict:
    """Calculate financial ratios"""
    pass

# New design: Separate core logic from decorator
def _calculate_financial_ratios_impl(ticker: str) -> dict:
    """Core logic, testable in isolation"""
    if not ticker:
        raise ValueError("ticker is required")
    return {"ratio": 1.5}

@function_tool
def calculate_financial_ratios(ticker: str) -> dict:
    """Wrapped with @function_tool"""
    return _calculate_financial_ratios_impl(ticker)

# Now we can test the core logic
def test_calculate_financial_ratios_impl():
    """Test core logic"""
    result = _calculate_financial_ratios_impl("2330")
    assert result["ratio"] == 1.5

    with pytest.raises(ValueError):
        _calculate_financial_ratios_impl(None)
```

#### 2️⃣ **Create Integration Tests Through Framework** (Second-best)

Can't call directly → Test indirectly through the Agent framework:

```python
# ✅ Test through Agent framework
@pytest.mark.asyncio
async def test_tool_through_agent_framework():
    """Verify tools work through the Agent framework"""
    # Not calling the tool directly, but validating it works
    from trading.tools.fundamental_agent import calculate_financial_ratios
    from agents import FunctionTool

    # Verify tool is properly initialized
    assert isinstance(calculate_financial_ratios, FunctionTool)
    assert calculate_financial_ratios.params_json_schema is not None

    # Verify Agent can use the tool
    agent = TradingAgent()
    agent.register_tool(calculate_financial_ratios)
    assert calculate_financial_ratios in agent.tools
```

#### 3️⃣ **Delete Test and Document the Limitation** (Last resort)

If you can't test it and can't redesign, delete the test and explicitly document:

```python
# ✅ Delete untestable test, add documentation
"""
Why there's no direct test of @function_tool decorated functions:

The @function_tool decorator is designed to transform functions into FunctionTool objects.
These objects aren't directly callable—they're only usable through the Agent framework.

Alternatives:
1. Integration tests through the Agent framework
2. Validate tool definition validity
3. Code review (parameter validation, error handling)

See: test_agent_tools_robustness.py
"""
```

### Decision Matrix

| Scenario | Choice | Example |
|----------|--------|---------|
| Can't test, can redesign | ✅ Redesign | Separate core logic from wrapper |
| Can't test, can use framework | ✅ Integration test | Test tools through Agent |
| Can't test, can't change | ✅ Delete test + document | Remove skip test, record limitation |
| Unsure why can't test | ❌ Don't skip | Do architecture analysis |

### Proper Use of Skip

`@pytest.mark.skip` should **only** be used for temporary situations:

```python
# ✅ Temporarily skip test (with clear tracking)
@pytest.mark.skip(reason="TODO: Issue #123 - Waiting for API endpoint")
def test_future_feature():
    """Feature not yet implemented, planned for v2.0"""
    pass

# ✅ Conditional skip (based on environment)
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Unix-only test"
)
def test_unix_specific():
    pass

# ❌ Never permanently skip without a reason
@pytest.mark.skip(reason="Cannot directly call tool")
def test_tool():
    """This indicates an architectural problem that should be fixed or deleted"""
    pass
```

### Code Review Checklist

When reviewing code and finding `@pytest.mark.skip`, ask:

- [ ] Is there a clear GitHub Issue or TODO?
- [ ] Is the skip temporary or permanent?
- [ ] Was a redesign attempted instead of skipping?
- [ ] Are there alternative testing approaches (integration, E2E)?
- [ ] Will the skip be removed before release?

If **all answers are NO**, the test should **not be skipped**.
