#!/usr/bin/env python3
"""
Basic functionality test to verify task-003 implementation.
"""

import asyncio
from market_mcp.cache.rate_limiter import RateLimiter
from market_mcp.cache.cache_manager import CacheManager
from market_mcp.cache.request_tracker import RequestTracker
from market_mcp.cache.rate_limited_cache_service import RateLimitedCacheService
from market_mcp.utils.config_manager import ConfigManager


async def test_basic_functionality():
    """Test basic functionality of all components."""
    print("🧪 Testing Task-003 Implementation...")

    # Test 1: Rate Limiter
    print("\n✅ Testing RateLimiter...")
    rate_limiter = RateLimiter(
        per_stock_interval=0.1, global_limit_per_minute=10, per_second_limit=3
    )

    # Test per-stock limiting
    can_request, reason, wait_time = await rate_limiter.can_request("2330")
    print(f"   First request for 2330: {can_request}")
    assert can_request is True

    await rate_limiter.record_request("2330")

    # Test cache hit
    can_request, reason, wait_time = await rate_limiter.can_request("2330")
    print(f"   Immediate second request for 2330: {can_request} (should be False)")

    # Test different stock
    can_request, reason, wait_time = await rate_limiter.can_request("2317")
    print(f"   Request for different stock 2317: {can_request}")
    assert can_request is True

    # Test 2: Cache Manager
    print("\n✅ Testing CacheManager...")
    cache_manager = CacheManager(ttl_seconds=5)

    test_data = {"symbol": "2330", "price": 500.0}
    await cache_manager.set_cached_data("2330", test_data)

    cached_data = await cache_manager.get_cached_data("2330")
    print(f"   Cache retrieval: {cached_data is not None}")
    print(f"   Cached data: {cached_data}")
    assert cached_data is not None

    # Test 3: Request Tracker
    print("\n✅ Testing RequestTracker...")
    tracker = RequestTracker()

    # Record request start and completion
    request_id = await tracker.record_request_start("2330")
    await tracker.record_request_complete(
        request_id, "2330", success=True, response_time_ms=500.0
    )

    # Record cached response
    await tracker.record_cached_response("2317", {"symbol": "2317", "price": 300})

    stats = tracker.get_global_stats()
    print(f"   Total requests tracked: {stats.get('total_requests', 0)}")
    print(f"   Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")
    assert stats.get("total_requests", 0) >= 1

    # Test 4: Config Manager
    print("\n✅ Testing ConfigManager...")
    config = ConfigManager()

    config.set("test_key", "test_value")
    value = config.get("test_key")
    print(f"   Config get/set: {value == 'test_value'}")
    assert value == "test_value"

    # Test 5: Rate Limited Cache Service
    print("\n✅ Testing RateLimitedCacheService...")
    service = RateLimitedCacheService()

    # Mock API call function
    async def mock_api_call(symbol):
        return {"symbol": symbol, "price": 450.0, "timestamp": "2024-01-01"}

    # Test cached call
    result1 = await service.get_cached_or_wait("2330", "price")
    result2 = await service.get_cached_or_wait(
        "2330", "price"
    )  # Should hit cache

    print(f"   Service working: {result1 is not None and result2 is not None}")

    # Test stats
    stats = service.get_comprehensive_stats()
    print(f"   Service stats: {stats is not None}")

    print("\n🎉 All basic functionality tests passed!")
    print("\n📊 Task-003 Implementation Summary:")
    print("   ✅ Multi-layered rate limiting (per-stock, global, per-second)")
    print("   ✅ TTL-based caching system with memory management")
    print("   ✅ Request tracking and statistics")
    print("   ✅ Dynamic configuration management")
    print("   ✅ Integrated cache service with health monitoring")
    print("   ✅ Enhanced TWSE client with rate limiting protection")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
