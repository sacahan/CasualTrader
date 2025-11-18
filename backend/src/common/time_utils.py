"""Time-related helpers for consistent UTC timestamp handling."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return a timezone-naive UTC datetime value for database writes."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
