"""
API usage statistics tracking and monitoring for Taiwan Stock Exchange API.
Provides detailed metrics for rate limiting and performance monitoring.
"""

import time
import logging
from collections import defaultdict, deque
from threading import RLock
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class RequestStats:
    """Statistics for API requests."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_responses: int = 0
    rate_limited_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: float = 0.0


@dataclass
class SymbolStats:
    """Per-symbol request statistics."""

    symbol: str
    request_count: int = 0
    last_request: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    rate_limits_hit: int = 0
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))


class RequestTracker:
    """
    Comprehensive API usage tracking and monitoring system.
    Tracks requests, performance metrics, and provides detailed statistics.
    """

    def __init__(self, stats_retention_hours: int = 24):
        self.stats_retention_hours = stats_retention_hours
        self.lock = RLock()

        # Global statistics
        self.global_stats = RequestStats()

        # Per-symbol statistics
        self.symbol_stats: dict[str, SymbolStats] = defaultdict(
            lambda: SymbolStats(symbol="")
        )

        # Time-series data for analysis
        self.hourly_request_counts: deque = deque(maxlen=stats_retention_hours)
        self.request_timestamps: deque = deque()

        # Performance tracking
        self.response_times: deque = deque(maxlen=1000)  # Last 1000 requests

        # Rate limiting events
        self.rate_limit_events: deque = deque(maxlen=500)

    def _clean_old_data(self) -> None:
        """Remove data older than retention period."""
        cutoff_time = time.time() - (self.stats_retention_hours * 3600)

        # Clean request timestamps
        while self.request_timestamps and self.request_timestamps[0] <= cutoff_time:
            self.request_timestamps.popleft()

        # Clean rate limit events
        while (
            self.rate_limit_events
            and self.rate_limit_events[0]["timestamp"] <= cutoff_time
        ):
            self.rate_limit_events.popleft()

    async def record_request_start(
        self, symbol: str, request_type: str = "quote"
    ) -> str:
        """
        Record the start of an API request.
        Returns a unique request_id for tracking.
        """
        request_id = f"{symbol}_{request_type}_{time.time()}"
        current_time = time.time()

        with self.lock:
            self._clean_old_data()

            # Update global stats
            self.global_stats.total_requests += 1
            self.global_stats.last_request_time = current_time

            # Update symbol stats
            if symbol not in self.symbol_stats:
                self.symbol_stats[symbol] = SymbolStats(symbol=symbol)

            self.symbol_stats[symbol].request_count += 1
            self.symbol_stats[symbol].last_request = current_time

            # Record timestamp
            self.request_timestamps.append(current_time)

        logger.debug(f"Started tracking request {request_id}")
        return request_id

    async def record_request_complete(
        self,
        request_id: str,
        symbol: str,
        success: bool,
        response_time_ms: float,
        was_cached: bool = False,
        request_type: str = "quote",
    ) -> None:
        """Record the completion of an API request."""
        with self.lock:
            # Update global stats
            if success:
                self.global_stats.successful_requests += 1
            else:
                self.global_stats.failed_requests += 1

            if was_cached:
                self.global_stats.cached_responses += 1

            # Update average response time
            self.response_times.append(response_time_ms)
            if self.response_times:
                self.global_stats.average_response_time = sum(
                    self.response_times
                ) / len(self.response_times)

            # Update symbol-specific stats
            if symbol in self.symbol_stats:
                symbol_stat = self.symbol_stats[symbol]
                symbol_stat.response_times.append(response_time_ms)

                if symbol_stat.response_times:
                    symbol_stat.average_response_time = sum(
                        symbol_stat.response_times
                    ) / len(symbol_stat.response_times)

                if was_cached:
                    symbol_stat.cache_hits += 1
                else:
                    symbol_stat.cache_misses += 1

        logger.debug(
            f"Completed request {request_id}: "
            f"success={success}, cached={was_cached}, time={response_time_ms:.2f}ms"
        )

    async def record_rate_limit_hit(
        self,
        symbol: str,
        limit_type: str,
        wait_time_seconds: float,
        request_type: str = "quote",
    ) -> None:
        """Record when a rate limit is encountered."""
        event = {
            "timestamp": time.time(),
            "symbol": symbol,
            "limit_type": limit_type,
            "wait_time_seconds": wait_time_seconds,
            "request_type": request_type,
        }

        with self.lock:
            self.global_stats.rate_limited_requests += 1

            if symbol in self.symbol_stats:
                self.symbol_stats[symbol].rate_limits_hit += 1

            self.rate_limit_events.append(event)

        logger.info(
            f"Rate limit hit: {limit_type} for {symbol}, "
            f"wait time: {wait_time_seconds:.2f}s"
        )

    async def record_cached_response(
        self, symbol: str, request_type: str = "quote"
    ) -> None:
        """Record when a cached response was returned."""
        request_id = await self.record_request_start(symbol, request_type)
        await self.record_request_complete(
            request_id,
            symbol,
            True,
            0.0,  # 0ms for cached response
            True,
            request_type,
        )

        logger.debug(f"Recorded cached response for {symbol}")

    def get_global_stats(self) -> dict[str, Any]:
        """Get global API usage statistics."""
        with self.lock:
            self._clean_old_data()

            # Calculate requests per hour
            current_time = time.time()
            hour_ago = current_time - 3600
            requests_last_hour = sum(
                1 for ts in self.request_timestamps if ts > hour_ago
            )

            # Calculate success rate
            total_completed = (
                self.global_stats.successful_requests
                + self.global_stats.failed_requests
            )
            success_rate = (
                (self.global_stats.successful_requests / total_completed * 100)
                if total_completed > 0
                else 0.0
            )

            # Calculate cache hit rate
            cache_total = self.global_stats.cached_responses + (
                total_completed - self.global_stats.cached_responses
            )
            cache_hit_rate = (
                (self.global_stats.cached_responses / cache_total * 100)
                if cache_total > 0
                else 0.0
            )

            return {
                "total_requests": self.global_stats.total_requests,
                "successful_requests": self.global_stats.successful_requests,
                "failed_requests": self.global_stats.failed_requests,
                "cached_responses": self.global_stats.cached_responses,
                "rate_limited_requests": self.global_stats.rate_limited_requests,
                "success_rate_percent": round(success_rate, 2),
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "average_response_time_ms": round(
                    self.global_stats.average_response_time, 2
                ),
                "requests_last_hour": requests_last_hour,
                "tracked_symbols": len(self.symbol_stats),
                "last_request_time": self.global_stats.last_request_time,
            }

    def get_symbol_stats(self, symbol: str) -> dict[str, Any] | None:
        """Get statistics for a specific symbol."""
        with self.lock:
            if symbol not in self.symbol_stats:
                return None

            stats = self.symbol_stats[symbol]
            cache_total = stats.cache_hits + stats.cache_misses
            cache_hit_rate = (
                (stats.cache_hits / cache_total * 100) if cache_total > 0 else 0.0
            )

            return {
                "symbol": symbol,
                "request_count": stats.request_count,
                "last_request": stats.last_request,
                "cache_hits": stats.cache_hits,
                "cache_misses": stats.cache_misses,
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "rate_limits_hit": stats.rate_limits_hit,
                "average_response_time_ms": round(stats.average_response_time, 2),
            }

    def get_top_symbols(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top symbols by request count."""
        with self.lock:
            sorted_symbols = sorted(
                self.symbol_stats.values(), key=lambda s: s.request_count, reverse=True
            )

            result = []
            for stats in sorted_symbols[:limit]:
                symbol_data = self.get_symbol_stats(stats.symbol)
                if symbol_data:
                    result.append(symbol_data)

            return result

    def get_rate_limit_summary(self) -> dict[str, Any]:
        """Get summary of rate limiting events."""
        with self.lock:
            if not self.rate_limit_events:
                return {
                    "total_events": 0,
                    "events_last_hour": 0,
                    "most_common_limit_type": None,
                    "most_affected_symbol": None,
                }

            current_time = time.time()
            hour_ago = current_time - 3600

            events_last_hour = sum(
                1 for event in self.rate_limit_events if event["timestamp"] > hour_ago
            )

            # Count limit types
            limit_type_counts = defaultdict(int)
            symbol_counts = defaultdict(int)

            for event in self.rate_limit_events:
                limit_type_counts[event["limit_type"]] += 1
                symbol_counts[event["symbol"]] += 1

            most_common_limit = (
                max(limit_type_counts.items(), key=lambda x: x[1])
                if limit_type_counts
                else (None, 0)
            )
            most_affected_symbol = (
                max(symbol_counts.items(), key=lambda x: x[1])
                if symbol_counts
                else (None, 0)
            )

            return {
                "total_events": len(self.rate_limit_events),
                "events_last_hour": events_last_hour,
                "most_common_limit_type": most_common_limit[0],
                "most_common_limit_count": most_common_limit[1],
                "most_affected_symbol": most_affected_symbol[0],
                "most_affected_symbol_count": most_affected_symbol[1],
            }

    async def reset_stats(self) -> None:
        """Reset all statistics. Use with caution."""
        with self.lock:
            self.global_stats = RequestStats()
            self.symbol_stats.clear()
            self.hourly_request_counts.clear()
            self.request_timestamps.clear()
            self.response_times.clear()
            self.rate_limit_events.clear()

        logger.info("All request tracking statistics have been reset")
