"""
Comprehensive tests for rate limiting and caching system.
Tests all components: RateLimiter, CacheManager, RequestTracker, and RateLimitedCacheService.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, patch

from market_mcp.cache.rate_limiter import RateLimiter
from market_mcp.cache.cache_manager import CacheManager
from market_mcp.cache.request_tracker import RequestTracker
from market_mcp.cache.rate_limited_cache_service import RateLimitedCacheService
from market_mcp.utils.config_manager import ConfigManager


class TestRateLimiter:
    """Test the RateLimiter component."""

    @pytest.fixture
    def rate_limiter(self):
        return RateLimiter(
            per_stock_interval=0.1,  # 100ms for faster testing
            global_limit_per_minute=5,  # Lower limit for testing
            per_second_limit=2,
        )

    @pytest.mark.asyncio
    async def test_per_stock_rate_limiting(self, rate_limiter):
        """Test per-stock rate limiting works correctly."""
        # First request should be allowed
        can_request, reason, wait_time = await rate_limiter.can_request("2330")
        assert can_request is True
        assert wait_time == 0.0

        # Record the request
        await rate_limiter.record_request("2330")

        # Immediate second request should be blocked
        can_request, reason, wait_time = await rate_limiter.can_request("2330")
        assert can_request is False
        assert "stock_limit" in reason
        assert wait_time > 0

        # Different stock should still be allowed
        can_request, reason, wait_time = await rate_limiter.can_request("2317")
        assert can_request is True

    @pytest.mark.asyncio
    async def test_global_rate_limiting(self, rate_limiter):
        """Test global rate limiting across all stocks."""
        # Make requests up to the limit (5 requests allowed)
        for i in range(5):
            can_request, _, _ = await rate_limiter.can_request(f"stock_{i}")
            # Only assert if request should be allowed
            if i < 5:  # First 5 should pass
                assert can_request is True
            await rate_limiter.record_request(f"stock_{i}")

        # Next request should be blocked by global limit (6th request)
        can_request, reason, wait_time = await rate_limiter.can_request("new_stock")
        assert can_request is False
        assert "global_limit" in reason

    @pytest.mark.asyncio
    async def test_per_second_rate_limiting(self, rate_limiter):
        """Test per-second rate limiting."""
        # Make 2 requests quickly (should be allowed)
        for i in range(2):
            can_request, _, _ = await rate_limiter.can_request(f"fast_stock_{i}")
            assert can_request is True
            await rate_limiter.record_request(f"fast_stock_{i}")

        # Third request in same second should be blocked
        can_request, reason, wait_time = await rate_limiter.can_request("fast_stock_3")
        assert can_request is False
        assert "per_second_limit" in reason

    def test_rate_limiter_stats(self, rate_limiter):
        """Test rate limiter statistics."""
        stats = rate_limiter.get_stats()

        assert "global_requests_last_minute" in stats
        assert "per_second_limit" in stats
        assert "tracked_stocks_count" in stats
        assert stats["per_second_limit"] == 2


class TestCacheManager:
    """Test the CacheManager component."""

    @pytest.fixture
    def cache_manager(self):
        return CacheManager(ttl_seconds=1, max_size=10, max_memory_mb=50.0)

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache_manager):
        """Test basic cache operations."""
        test_data = {"price": 100, "volume": 1000}

        # Set cache data
        success = await cache_manager.set_cached_data("2330", test_data)
        assert success is True

        # Retrieve cached data
        cached_data = await cache_manager.get_cached_data("2330")
        assert cached_data is not None
        assert cached_data["data"] == test_data
        assert cached_data["symbol"] == "2330"

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache_manager):
        """Test that cache expires after TTL."""
        test_data = {"price": 100}

        # Set cache data
        await cache_manager.set_cached_data("2330", test_data)

        # Should be available immediately
        cached_data = await cache_manager.get_cached_data("2330")
        assert cached_data is not None

        # Wait for TTL to expire (1 second + buffer)
        await asyncio.sleep(1.2)

        # Should be expired now
        cached_data = await cache_manager.get_cached_data("2330")
        assert cached_data is None

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_manager):
        """Test manual cache invalidation."""
        test_data = {"price": 100}

        await cache_manager.set_cached_data("2330", test_data)

        # Verify data is cached
        cached_data = await cache_manager.get_cached_data("2330")
        assert cached_data is not None

        # Invalidate cache
        success = await cache_manager.invalidate("2330")
        assert success is True

        # Should be gone now
        cached_data = await cache_manager.get_cached_data("2330")
        assert cached_data is None

    def test_cache_stats(self, cache_manager):
        """Test cache statistics."""
        stats = cache_manager.get_cache_stats()

        assert "hit_count" in stats
        assert "miss_count" in stats
        assert "hit_rate_percent" in stats
        assert "cache_entries" in stats
        assert "memory_usage_mb" in stats

    def test_cache_health_check(self, cache_manager):
        """Test cache health monitoring."""
        is_healthy, issues = cache_manager.is_cache_healthy()

        # Should be healthy with no data
        assert is_healthy is True
        assert len(issues) == 0


class TestRequestTracker:
    """Test the RequestTracker component."""

    @pytest.fixture
    def request_tracker(self):
        return RequestTracker(stats_retention_hours=1)

    @pytest.mark.asyncio
    async def test_request_tracking(self, request_tracker):
        """Test basic request tracking functionality."""
        # Record a successful request
        request_id = await request_tracker.record_request_start("2330", "quote")
        assert request_id is not None

        await request_tracker.record_request_complete(
            request_id, "2330", True, 150.0, False, "quote"
        )

        # Check global stats
        stats = request_tracker.get_global_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 0

    @pytest.mark.asyncio
    async def test_cached_response_tracking(self, request_tracker):
        """Test tracking of cached responses."""
        await request_tracker.record_cached_response("2330", "quote")

        stats = request_tracker.get_global_stats()
        assert stats["cached_responses"] == 1
        assert stats["cache_hit_rate_percent"] > 0

    @pytest.mark.asyncio
    async def test_rate_limit_event_tracking(self, request_tracker):
        """Test rate limit event recording."""
        await request_tracker.record_rate_limit_hit("2330", "stock_limit", 5.0)

        rate_limit_summary = request_tracker.get_rate_limit_summary()
        assert rate_limit_summary["total_events"] == 1
        assert rate_limit_summary["most_common_limit_type"] == "stock_limit"

    def test_symbol_stats(self, request_tracker):
        """Test per-symbol statistics."""
        # Should return None for unknown symbol
        stats = request_tracker.get_symbol_stats("UNKNOWN")
        assert stats is None

    def test_top_symbols(self, request_tracker):
        """Test top symbols by request count."""
        top_symbols = request_tracker.get_top_symbols(5)
        assert isinstance(top_symbols, list)
        assert len(top_symbols) <= 5


class TestRateLimitedCacheService:
    """Test the integrated RateLimitedCacheService."""

    @pytest.fixture
    def config_manager(self):
        config = ConfigManager()
        # Use faster settings for testing
        config.set("rate_limiting.per_stock_interval_seconds", 0.1)
        config.set("rate_limiting.global_limit_per_minute", 5)
        config.set("caching.ttl_seconds", 1)
        return config

    @pytest.fixture
    def cache_service(self, config_manager):
        return RateLimitedCacheService(config_manager)

    @pytest.mark.asyncio
    async def test_integrated_cache_and_rate_limiting(self, cache_service):
        """Test integrated functionality of cache and rate limiting."""
        # First request - should allow and return None (no cache)
        data, is_cached, message = await cache_service.get_cached_or_wait("2330")
        assert data is None
        assert is_cached is False
        assert "cache_miss_can_make_request" in message

        # Simulate successful API request
        test_data = {"price": 100, "volume": 1000}
        success = await cache_service.record_successful_request(
            "2330", test_data, 150.0
        )
        assert success is True

        # Second request - should return cached data
        data, is_cached, message = await cache_service.get_cached_or_wait("2330")
        assert data is not None
        assert is_cached is True
        assert "cache_hit" in message

        # Wait for cache to expire
        await asyncio.sleep(1.2)

        # Should now return None again (cache expired)
        data, is_cached, message = await cache_service.get_cached_or_wait("2330")
        assert data is None

    @pytest.mark.asyncio
    async def test_rate_limiting_with_cache_fallback(self, cache_service):
        """Test that cache is returned when rate limited."""
        # First request and cache data
        test_data = {"price": 100}
        await cache_service.record_successful_request("2330", test_data, 150.0)

        # Second immediate request should be rate limited but return cache
        data, is_cached, message = await cache_service.get_cached_or_wait("2330")
        assert data is not None
        assert is_cached is True
        assert "rate_limited_returned_cache" in message

    def test_comprehensive_stats(self, cache_service):
        """Test comprehensive statistics gathering."""
        stats = cache_service.get_comprehensive_stats()

        assert "service_status" in stats
        assert "rate_limiter" in stats
        assert "cache_manager" in stats
        assert "request_tracker" in stats
        assert "cache_health" in stats
        assert "configuration" in stats

    @pytest.mark.asyncio
    async def test_health_check(self, cache_service):
        """Test comprehensive health check."""
        health = await cache_service.health_check()

        assert "overall_healthy" in health
        assert "timestamp" in health
        assert "components" in health
        assert "issues" in health
        assert "recommendations" in health

        # Should be healthy initially
        assert health["overall_healthy"] is True

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_service):
        """Test cache invalidation through service."""
        # Cache some data
        test_data = {"price": 100}
        await cache_service.record_successful_request("2330", test_data, 150.0)

        # Verify it's cached
        data, _, _ = await cache_service.get_cached_or_wait("2330")
        assert data is not None

        # Invalidate cache
        success = await cache_service.invalidate_symbol_cache("2330")
        assert success is True

        # Should be gone now (but rate limited)
        data, is_cached, message = await cache_service.get_cached_or_wait("2330")
        assert data is None
        assert "rate_limited_no_cache" in message

    @pytest.mark.asyncio
    async def test_service_enable_disable(self, cache_service):
        """Test service enable/disable functionality."""
        assert cache_service.is_enabled() is True

        cache_service.disable_service()
        assert cache_service.is_enabled() is False

        cache_service.enable_service()
        assert cache_service.is_enabled() is True


# Integration test
@pytest.mark.asyncio
async def test_full_integration_scenario():
    """Test a complete usage scenario with all components."""
    # Create service with test configuration
    config = ConfigManager()
    config.set("rate_limiting.per_stock_interval_seconds", 0.1)
    config.set("rate_limiting.global_limit_per_minute", 3)
    config.set("caching.ttl_seconds", 0.5)

    service = RateLimitedCacheService(config)

    # Simulate multiple API requests
    symbols = ["2330", "2317", "0050"]

    for i, symbol in enumerate(symbols):
        # Check if request is allowed
        data, is_cached, message = await service.get_cached_or_wait(symbol)
        assert data is None  # No cache initially
        assert "cache_miss_can_make_request" in message

        # Simulate API call
        test_data = {"price": 100 + i, "volume": 1000 * (i + 1)}
        await service.record_successful_request(symbol, test_data, 100.0 + i * 10)

    # Now all symbols should be cached
    for symbol in symbols:
        data, is_cached, message = await service.get_cached_or_wait(symbol)
        assert data is not None
        assert is_cached is True

    # Try one more symbol - should hit global rate limit
    data, is_cached, message = await service.get_cached_or_wait("1101")
    assert data is None
    assert "rate_limited_no_cache" in message

    # Get comprehensive stats
    stats = service.get_comprehensive_stats()
    assert stats["request_tracker"]["global"]["total_requests"] >= 3
    assert stats["cache_manager"]["cache_entries"] == 3

    # Health check should be good
    health = await service.health_check()
    assert health["overall_healthy"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
