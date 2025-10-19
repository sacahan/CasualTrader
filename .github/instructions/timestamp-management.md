---
description: "Timestamp management standards and best practices for database models and service layers"
applyTo: "**/*.py"
---

# Timestamp Management Guidelines

## Overview

Timestamps are critical for audit trails, data consistency, and analytics. This guide establishes standards for implementing and maintaining timestamps across the CasualTrader backend.

---

## CORE_PRINCIPLES

### 1. Explicit Over Implicit

- **Always explicitly set timestamps** in update operations, not relying on ORM auto-updates alone.
- Use `datetime.now()` explicitly at the point of state change.
- Document the timestamp update logic in comments.

### 2. Complete Lifecycle Tracking

- **Every persistent entity** should have `created_at` and `updated_at` fields.
- **Domain-specific timestamps** should track business events (e.g., `last_active_at`, `end_time`).
- Never delete timestamp data; treat it as immutable once set.

### 3. Consistency and Accuracy

- Use `datetime.now()` consistently; avoid mixing different time sources.
- Always set `updated_at` when any field changes, not just for major state changes.
- Calculate derived timestamps (e.g., `execution_time_ms`) explicitly from base timestamps.

### 4. Time Zone Awareness

- Store all timestamps in UTC (using Python's `datetime.now()` which defaults to UTC).
- Use timezone-aware datetime objects in type hints when applicable.
- Document any timezone conversions needed for display.

---

## MODEL_DEFINITION_PATTERNS

### Pattern 1: Basic Timestamps

For any new database model, include these base timestamps:

```python
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

class BaseModel(Base):
    """Base model with audit timestamps"""

    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(),
        nullable=False,
        doc="Record creation timestamp (UTC)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now(),
        nullable=False,
        doc="Last record update timestamp (UTC)"
    )
```

**Why `onupdate`?**

- Provides a safety net for ORM-generated updates.
- **Not a replacement** for explicit updates in service layer.
- Use as a fallback, not primary mechanism.

### Pattern 2: Domain-Specific Timestamps

For business-domain tracking:

```python
class Agent(Base):
    """Agent model with activity tracking"""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # Domain-specific: when agent was last active
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
        doc="Last time agent performed any operation (UTC)"
    )

    # Domain-specific: when agent was stopped
    stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
        doc="When agent was stopped (UTC)"
    )
```

### Pattern 3: Execution/Duration Tracking

For time-duration measurements:

```python
class AgentSession(Base):
    """Session with execution timing"""

    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(),
        doc="Session start time (UTC)"
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
        doc="Session end time (UTC), set when session completes"
    )

    # Duration in milliseconds (calculated field)
    execution_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        default=None,
        doc="Total execution time in milliseconds"
    )
```

---

## SERVICE_LAYER_IMPLEMENTATION

### Pattern 1: Update with Explicit Timestamps

**Correct Implementation:**

```python
async def update_agent_status(
    self,
    agent_id: str,
    status: AgentStatus,
) -> Agent:
    """
    Update agent status and track activity timestamp.

    This method MUST update both status and timestamp fields.
    """
    agent = await self.get_agent(agent_id)

    # Update business state
    agent.status = status

    # Update timestamps - ALWAYS explicit, ALWAYS here
    agent.updated_at = datetime.now()
    agent.last_active_at = datetime.now()  # Track activity

    await self.session.commit()
    return agent
```

**Why this matters:**

- `last_active_at` tracks when the agent last did something
- Explicit timestamp update guarantees it's set, even if ORM fails
- Comment explains the business intent

### Pattern 2: Resource Update with Modification Tracking

```python
async def update_agent_funds(
    self,
    agent_id: str,
    amount_change: float,
) -> Agent:
    """
    Update agent's available funds.

    Tracks both the resource change AND the activity time.
    """
    agent = await self.get_agent(agent_id)

    # Update business data
    agent.current_funds = Decimal(str(agent.current_funds + amount_change))

    # Update tracking timestamps
    agent.updated_at = datetime.now()
    agent.last_active_at = datetime.now()

    await self.session.commit()
    return agent
```

### Pattern 3: Completion with Duration Calculation

```python
async def complete_session(
    self,
    session_id: str,
    final_output: dict[str, Any],
) -> AgentSession:
    """
    Mark session as complete and calculate duration.

    Args:
        session_id: Session to complete
        final_output: Final output data

    Returns:
        Updated session with end_time and execution_time_ms set
    """
    session = await self.get_session(session_id)

    # Update business data
    session.final_output = final_output
    session.status = SessionStatus.COMPLETED

    # Set end time - MUST be done explicitly
    if session.end_time is None:
        session.end_time = datetime.now()

    # Calculate duration if not already set
    if session.execution_time_ms is None and session.start_time:
        execution_ms = int(
            (session.end_time - session.start_time).total_seconds() * 1000
        )
        session.execution_time_ms = execution_ms

    await self.session.commit()
    await self.session.refresh(session)
    return session
```

### Pattern 4: Conditional Timestamp Updates

For operations that may or may not change timestamps:

```python
async def process_agent_transaction(
    self,
    agent_id: str,
    transaction_type: str,
    amount: float,
) -> Agent:
    """
    Process transaction and track activity.

    Always update activity timestamp, conditionally update data timestamp.
    """
    agent = await self.get_agent(agent_id)

    # Track activity regardless of transaction outcome
    agent.last_active_at = datetime.now()

    # Only update data timestamp if transaction succeeds
    if transaction_type == "withdrawal":
        agent.current_funds -= amount
        agent.updated_at = datetime.now()
    elif transaction_type == "deposit":
        agent.current_funds += amount
        agent.updated_at = datetime.now()

    await self.session.commit()
    return agent
```

---

## COMMON_PATTERNS_AND_ANTI_PATTERNS

### ✅ GOOD: Explicit Updates

```python
# GOOD: Clear intent, guaranteed to work
agent.updated_at = datetime.now()
agent.last_active_at = datetime.now()
await session.commit()
```

### ❌ BAD: Implicit ORM Updates

```python
# BAD: Relying on ORM onupdate - unreliable
agent.status = new_status
# Hoping ORM updates 'updated_at'...
await session.commit()
```

### ✅ GOOD: Calculated Duration

```python
# GOOD: Calculate from base timestamps
if session.start_time and session.end_time:
    execution_ms = int(
        (session.end_time - session.start_time).total_seconds() * 1000
    )
    session.execution_time_ms = execution_ms
```

### ❌ BAD: Hardcoded Duration

```python
# BAD: Duration not tied to actual times
session.execution_time_ms = 5000  # arbitrary!
```

### ✅ GOOD: Null Safety

```python
# GOOD: Check for None before using
if session.end_time is None:
    session.end_time = datetime.now()

if session.execution_time_ms is None and session.start_time:
    # safe to calculate
    exec_ms = int((session.end_time - session.start_time).total_seconds() * 1000)
```

### ❌ BAD: Unsafe Calculations

```python
# BAD: May raise exception if timestamps are None
execution_ms = int((session.end_time - session.start_time).total_seconds() * 1000)
```

---

## TESTING_TIMESTAMP_LOGIC

### Pattern: Test Timestamp Updates

```python
import pytest
from datetime import datetime, timedelta

async def test_update_agent_status_updates_timestamps():
    """Verify timestamps are updated when status changes."""
    # Arrange
    agent = await agents_service.create_agent(agent_id="test_agent")
    old_updated_at = agent.updated_at
    old_last_active_at = agent.last_active_at

    # Act: Wait slightly to ensure time difference
    await asyncio.sleep(0.01)
    await agents_service.update_agent_status(
        agent_id="test_agent",
        status=AgentStatus.ACTIVE
    )

    # Assert
    updated_agent = await agents_service.get_agent("test_agent")
    assert updated_agent.updated_at > old_updated_at
    assert updated_agent.last_active_at is not None
    assert updated_agent.last_active_at > (old_last_active_at or datetime.min)


async def test_session_execution_time_calculation():
    """Verify execution time is correctly calculated."""
    # Arrange
    session = await session_service.create_session(
        agent_id="test_agent",
        session_type="manual_task"
    )
    start = session.start_time

    # Act: Simulate work
    await asyncio.sleep(0.1)
    await session_service.complete_session(
        session_id=session.id,
        final_output={"result": "ok"}
    )

    # Assert
    completed = await session_service.get_session(session.id)
    assert completed.end_time is not None
    assert completed.execution_time_ms is not None
    # Should be ~100ms, allow ±50ms for timing variations
    assert 50 < completed.execution_time_ms < 200
```

---

## TIMESTAMP_MIGRATION_PATTERNS

### Adding Timestamps to Existing Model

When adding timestamp fields to an existing model:

```python
# Step 1: Define fields in model
class AgentPerformance(Base):
    # ... existing fields ...

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(),
        onupdate=lambda: datetime.now()
    )

# Step 2: Migration SQL
"""
ALTER TABLE agent_performance
ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE agent_performance
ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
"""

# Step 3: Update service layer to set timestamps
async def update_performance(self, performance: AgentPerformance):
    """Always set updated_at on performance updates."""
    performance.updated_at = datetime.now()
    await self.session.commit()
```

---

## QUERY_AND_ANALYSIS_PATTERNS

### Querying by Timestamp

```python
from datetime import datetime, timedelta

async def get_recently_active_agents(self, hours: int = 24) -> list[Agent]:
    """Get agents active within the past N hours."""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    stmt = select(Agent).where(
        Agent.last_active_at > cutoff_time
    ).order_by(Agent.last_active_at.desc())

    result = await self.session.execute(stmt)
    return result.scalars().all()


async def get_slow_sessions(self, min_duration_ms: int = 5000) -> list[AgentSession]:
    """Find sessions that took longer than threshold."""
    stmt = select(AgentSession).where(
        AgentSession.execution_time_ms > min_duration_ms
    ).order_by(AgentSession.execution_time_ms.desc())

    result = await self.session.execute(stmt)
    return result.scalars().all()
```

### Audit Trail Queries

```python
async def get_audit_trail(
    self,
    agent_id: str,
    start_date: datetime,
    end_date: datetime
) -> list[Agent]:
    """Get agent history between dates."""
    stmt = select(Agent).where(
        (Agent.id == agent_id) &
        (Agent.updated_at >= start_date) &
        (Agent.updated_at <= end_date)
    ).order_by(Agent.updated_at)

    result = await self.session.execute(stmt)
    return result.scalars().all()
```

---

## LOGGING_AND_MONITORING

### Log Timestamp Changes

```python
logger.info(
    f"Updated agent {agent_id} at {datetime.now().isoformat()}",
    extra={
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "updated_at": agent.updated_at.isoformat(),
    }
)
```

### Monitor Timestamp Anomalies

```python
def validate_timestamp_consistency(entity):
    """Check for timestamp anomalies."""
    now = datetime.now()

    # created_at should never be in future
    if entity.created_at > now:
        logger.warning(f"created_at in future: {entity.created_at}")

    # updated_at should not be before created_at
    if entity.updated_at < entity.created_at:
        logger.error(f"updated_at before created_at: {entity}")

    # updated_at should not be far in future
    if entity.updated_at > now + timedelta(seconds=5):
        logger.warning(f"updated_at significantly in future: {entity.updated_at}")
```

---

## DOCUMENTATION_REQUIREMENTS

### Docstring Template

```python
async def update_resource(self, resource_id: str, **updates) -> Resource:
    """
    Update resource and track changes.

    Timestamps Updated:
        - updated_at: Set to current time
        - last_modified_by: Set to current user (if applicable)

    Args:
        resource_id: ID of resource to update
        **updates: Fields to update

    Returns:
        Updated resource with current timestamps

    Raises:
        ResourceNotFoundError: If resource not found
    """
```

### Timestamp Field Documentation

Always document timestamp fields in model docstrings:

```python
class Agent(Base):
    """Agent model.

    Timestamps:
        created_at: Record creation time (UTC)
        updated_at: Last update time (UTC)
        last_active_at: Last operation time (UTC), tracks user activity
    """

    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime)
```

---

## REVIEW_CHECKLIST

When reviewing code that modifies data, verify:

- [ ] **Model definitions** have `created_at` and `updated_at`
- [ ] **Update methods** explicitly set `updated_at = datetime.now()`
- [ ] **Domain-specific timestamps** are set at appropriate state changes
- [ ] **Duration calculations** use actual timestamps, not hardcoded values
- [ ] **Null checks** prevent accessing None timestamps
- [ ] **Tests** verify timestamp updates occur
- [ ] **Docstrings** document which timestamps are affected
- [ ] **Logging** includes relevant timestamps
- [ ] **No time zones** are mixed (everything in UTC)
- [ ] **Backward compatibility** is maintained for migrations

---

## COMMON_ISSUES_AND_SOLUTIONS

### Issue: Timestamps Not Updating

**Problem:** Updates happen but timestamps unchanged

**Solution:**

```python
# BEFORE (broken)
agent.status = new_status
await session.commit()

# AFTER (fixed)
agent.status = new_status
agent.updated_at = datetime.now()  # Explicit!
await session.commit()
```

### Issue: Wrong Duration Calculated

**Problem:** `execution_time_ms` is incorrect

**Solution:**

```python
# BEFORE (broken)
session.execution_time_ms = some_external_value

# AFTER (fixed)
if session.start_time and session.end_time:
    execution_ms = int(
        (session.end_time - session.start_time).total_seconds() * 1000
    )
    session.execution_time_ms = execution_ms
```

### Issue: NoneType Errors on Timestamp Fields

**Problem:** Code crashes on None timestamps

**Solution:**

```python
# BEFORE (broken)
duration_ms = (session.end_time - session.start_time).total_seconds() * 1000

# AFTER (fixed)
if session.end_time and session.start_time:
    duration_ms = int(
        (session.end_time - session.start_time).total_seconds() * 1000
    )
else:
    duration_ms = None
```

---

## EXAMPLES_BY_USE_CASE

### Use Case 1: Agent Lifecycle Tracking

```python
async def create_agent(self, config: AgentConfig) -> Agent:
    """Create new agent. Timestamps auto-set by model defaults."""
    agent = Agent(...)
    self.session.add(agent)
    await self.session.commit()
    return agent


async def activate_agent(self, agent_id: str) -> Agent:
    """Activate agent and record activity."""
    agent = await self.get_agent(agent_id)
    agent.status = AgentStatus.ACTIVE
    agent.updated_at = datetime.now()
    agent.last_active_at = datetime.now()
    await self.session.commit()
    return agent


async def stop_agent(self, agent_id: str) -> Agent:
    """Stop agent and record stop time."""
    agent = await self.get_agent(agent_id)
    agent.status = AgentStatus.STOPPED
    agent.updated_at = datetime.now()
    agent.stopped_at = datetime.now()
    await self.session.commit()
    return agent
```

### Use Case 2: Session Execution Tracking

```python
async def start_session(
    self,
    agent_id: str,
    session_type: str
) -> AgentSession:
    """Start session. start_time auto-set by model default."""
    session = AgentSession(
        agent_id=agent_id,
        session_type=session_type,
        status=SessionStatus.RUNNING
    )
    self.session.add(session)
    await self.session.commit()
    return session


async def complete_session(
    self,
    session_id: str,
    output: dict[str, Any]
) -> AgentSession:
    """Complete session and calculate execution time."""
    session = await self.get_session(session_id)

    session.final_output = output
    session.status = SessionStatus.COMPLETED
    session.end_time = datetime.now()

    # Calculate execution duration
    if session.start_time:
        exec_ms = int(
            (session.end_time - session.start_time).total_seconds() * 1000
        )
        session.execution_time_ms = exec_ms

    await self.session.commit()
    return session
```

---

## RESOURCES

- **Standards:**
  - [PEP 8 - Style Guide](https://pep8.org/)
  - [Python datetime documentation](https://docs.python.org/3/library/datetime.html)
  - [SQLAlchemy ORM documentation](https://docs.sqlalchemy.org/en/20/)

---

**Last Updated:** 2025-10-19
**Version:** 1.0
**Status:** Active
