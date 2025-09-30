"""
Integrated rate limiting and caching service for Taiwan Stock Exchange API.
Combines all cache components into a unified high-level interface.
"""

import asyncio
import time
import logging
from typing import Any

from .rate_limiter import RateLimiter
from .cache_manager import CacheManager
from .request_tracker import RequestTracker
from ..utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class RateLimitedCacheService:
    """
    High-level service that integrates rate limiting, caching, and statistics tracking.
    This is the main interface for protected API access with intelligent caching.
    """

    def __init__(self, config_manager: ConfigManager | None = None):
        self.config = config_manager or ConfigManager()

        # Initialize components with configuration
        rate_config = self.config.get_rate_limiting_config()
        cache_config = self.config.get_caching_config()
        monitoring_config = self.config.get_monitoring_config()

        self.rate_limiter = RateLimiter(
            per_stock_interval=rate_config.get("per_stock_interval_seconds", 30.0),
            global_limit_per_minute=rate_config.get("global_limit_per_minute", 20),
            per_second_limit=rate_config.get("per_second_limit", 2),
        )

        self.cache_manager = CacheManager(
            ttl_seconds=cache_config.get("ttl_seconds", 30),
            max_size=cache_config.get("max_size", 1000),
            max_memory_mb=cache_config.get("max_memory_mb", 200.0),
        )

        self.request_tracker = RequestTracker(
            stats_retention_hours=monitoring_config.get("stats_retention_hours", 24)
        )

        self._is_enabled = True

    async def can_make_request(
        self, symbol: str, request_type: str = "quote"
    ) -> tuple[bool, str, float]:
        """
        Check if a request can be made for the given symbol.
        Returns (allowed, reason, wait_time_seconds).
        """
        if not self.config.is_rate_limiting_enabled():
            return True, "rate_limiting_disabled", 0.0

        return await self.rate_limiter.can_request(symbol)

    async def get_cached_or_wait(
        self, symbol: str, request_type: str = "quote"
    ) -> tuple[dict | None, bool, str]:
        """
        Smart cache retrieval with rate limiting awareness.
        Returns (data, is_from_cache, message).

        Logic:
        1. Check cache first
        2. If cache miss, check rate limits
        3. Return cached data if rate limited
        4. Return None if no cached data and rate limited
        """
        # Always try cache first
        cached_data = None
        if self.config.is_caching_enabled():
            cached_data = await self.cache_manager.get_cached_data(symbol, request_type)

        # Check rate limits
        can_request, reason, wait_time = await self.can_make_request(
            symbol, request_type
        )

        if can_request:
            if cached_data:
                return cached_data, True, "cache_hit_but_can_make_new_request"
            else:
                return None, False, "cache_miss_can_make_request"
        else:
            # Rate limited - return cached data if available
            if cached_data:
                await self.request_tracker.record_rate_limit_hit(
                    symbol, reason, wait_time, request_type
                )
                return cached_data, True, f"rate_limited_returned_cache_{reason}"
            else:
                await self.request_tracker.record_rate_limit_hit(
                    symbol, reason, wait_time, request_type
                )
                return None, False, f"rate_limited_no_cache_{reason}"

    async def record_successful_request(
        self,
        symbol: str,
        response_data: dict,
        response_time_ms: float,
        request_type: str = "quote",
    ) -> bool:
        """
        Record a successful API request and cache the response.
        Returns True if everything was recorded successfully.
        """
        try:
            # Record the request with rate limiter
            await self.rate_limiter.record_request(symbol)

            # Cache the response data
            cache_success = True
            if self.config.is_caching_enabled():
                cache_success = await self.cache_manager.set_cached_data(
                    symbol, response_data, request_type
                )

            # Track the request for statistics
            request_id = await self.request_tracker.record_request_start(
                symbol, request_type
            )
            await self.request_tracker.record_request_complete(
                request_id, symbol, True, response_time_ms, False, request_type
            )

            logger.debug(
                f"Recorded successful request for {symbol}: "
                f"{response_time_ms:.2f}ms, cached: {cache_success}"
            )

            return cache_success

        except Exception as e:
            logger.error(f"Error recording successful request for {symbol}: {e}")
            return False

    async def record_failed_request(
        self, symbol: str, response_time_ms: float, request_type: str = "quote"
    ) -> None:
        """Record a failed API request for statistics."""
        try:
            request_id = await self.request_tracker.record_request_start(
                symbol, request_type
            )
            await self.request_tracker.record_request_complete(
                request_id, symbol, False, response_time_ms, False, request_type
            )

            logger.debug(
                f"Recorded failed request for {symbol}: {response_time_ms:.2f}ms"
            )

        except Exception as e:
            logger.error(f"Error recording failed request for {symbol}: {e}")

    async def record_cached_response(
        self, symbol: str, request_type: str = "quote"
    ) -> None:
        """Record when a cached response was returned."""
        try:
            request_id = await self.request_tracker.record_request_start(
                symbol, request_type
            )
            await self.request_tracker.record_request_complete(
                request_id,
                symbol,
                True,
                0.0,  # 0ms for cached response
                True,
                request_type,
            )

            logger.debug(f"Recorded cached response for {symbol}")

        except Exception as e:
            logger.error(f"Error recording cached response for {symbol}: {e}")

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics from all components."""
        try:
            return {
                "service_status": {
                    "enabled": self._is_enabled,
                    "rate_limiting_enabled": self.config.is_rate_limiting_enabled(),
                    "caching_enabled": self.config.is_caching_enabled(),
                },
                "rate_limiter": self.rate_limiter.get_stats(),
                "cache_manager": self.cache_manager.get_cache_stats(),
                "request_tracker": {
                    "global": self.request_tracker.get_global_stats(),
                    "rate_limits": self.request_tracker.get_rate_limit_summary(),
                    "top_symbols": self.request_tracker.get_top_symbols(5),
                },
                "cache_health": {
                    "is_healthy": self.cache_manager.is_cache_healthy()[0],
                    "issues": self.cache_manager.is_cache_healthy()[1],
                },
                "configuration": {
                    "rate_limiting": self.config.get_rate_limiting_config(),
                    "caching": self.config.get_caching_config(),
                },
            }
        except Exception as e:
            logger.error(f"Error getting comprehensive stats: {e}")
            return {"error": str(e)}

    async def health_check(self) -> dict[str, Any]:
        """Perform a comprehensive health check of all components."""
        health_status = {
            "overall_healthy": True,
            "timestamp": time.time(),
            "components": {},
            "issues": [],
            "recommendations": [],
        }

        try:
            # Check cache health
            cache_healthy, cache_issues = self.cache_manager.is_cache_healthy()
            health_status["components"]["cache"] = {
                "healthy": cache_healthy,
                "issues": cache_issues,
            }

            if not cache_healthy:
                health_status["overall_healthy"] = False
                health_status["issues"].extend(
                    [f"Cache: {issue}" for issue in cache_issues]
                )

            # Check rate limiter stats
            rate_stats = self.rate_limiter.get_stats()
            rate_healthy = True
            rate_issues = []

            # Check if global rate limit is being hit frequently
            if (
                rate_stats["global_requests_last_minute"]
                > rate_stats["global_limit_per_minute"] * 0.9
            ):
                rate_healthy = False
                rate_issues.append("Approaching global rate limit")

            health_status["components"]["rate_limiter"] = {
                "healthy": rate_healthy,
                "issues": rate_issues,
            }

            if not rate_healthy:
                health_status["overall_healthy"] = False
                health_status["issues"].extend(
                    [f"Rate Limiter: {issue}" for issue in rate_issues]
                )

            # Check request tracker stats
            global_stats = self.request_tracker.get_global_stats()
            tracker_healthy = True
            tracker_issues = []

            # Check success rate
            if (
                global_stats["success_rate_percent"] < 90.0
                and global_stats["total_requests"] > 10
            ):
                tracker_healthy = False
                tracker_issues.append(
                    f"Low success rate: {global_stats['success_rate_percent']}%"
                )

            # Check cache hit rate
            target_hit_rate = self.config.get(
                "monitoring.cache_hit_rate_target_percent", 80.0
            )
            if (
                global_stats["cache_hit_rate_percent"] < target_hit_rate
                and global_stats["total_requests"] > 10
            ):
                tracker_healthy = False
                tracker_issues.append(
                    f"Low cache hit rate: {global_stats['cache_hit_rate_percent']}% "
                    f"(target: {target_hit_rate}%)"
                )

            health_status["components"]["request_tracker"] = {
                "healthy": tracker_healthy,
                "issues": tracker_issues,
            }

            if not tracker_healthy:
                health_status["overall_healthy"] = False
                health_status["issues"].extend(
                    [f"Request Tracker: {issue}" for issue in tracker_issues]
                )

            # Generate recommendations
            if not cache_healthy:
                health_status["recommendations"].append(
                    "Consider increasing cache size or memory limit"
                )

            if not rate_healthy:
                health_status["recommendations"].append(
                    "Consider adjusting rate limits or request patterns"
                )

            if global_stats["cache_hit_rate_percent"] < target_hit_rate:
                health_status["recommendations"].append(
                    "Optimize cache TTL or request patterns to improve hit rate"
                )

        except Exception as e:
            health_status["overall_healthy"] = False
            health_status["issues"].append(f"Health check error: {str(e)}")
            logger.error(f"Error during health check: {e}")

        return health_status

    async def invalidate_symbol_cache(
        self, symbol: str, request_type: str = "quote"
    ) -> bool:
        """Manually invalidate cache for a specific symbol."""
        if self.config.is_caching_enabled():
            return await self.cache_manager.invalidate(symbol, request_type)
        return True

    async def clear_all_cache(self) -> None:
        """Clear all cached data."""
        if self.config.is_caching_enabled():
            await self.cache_manager.clear_all()

    async def reset_rate_limits(self) -> None:
        """Reset all rate limiting counters."""
        self.rate_limiter.reset_limits()

    async def reset_all_stats(self) -> None:
        """Reset all statistics and clear cache."""
        await self.clear_all_cache()
        self.rate_limiter.reset_limits()
        await self.request_tracker.reset_stats()
        logger.info("All statistics and cache have been reset")

    def enable_service(self) -> None:
        """Enable the rate limiting and caching service."""
        self._is_enabled = True
        logger.info("Rate limited cache service enabled")

    def disable_service(self) -> None:
        """Disable the rate limiting and caching service."""
        self._is_enabled = False
        logger.info("Rate limited cache service disabled")

    def is_enabled(self) -> bool:
        """Check if the service is enabled."""
        return self._is_enabled
