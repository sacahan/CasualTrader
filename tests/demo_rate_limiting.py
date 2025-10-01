#!/usr/bin/env python3
"""
Demo script showing the rate limiting and caching system in action.
Simulates real-world usage of the Taiwan Stock Exchange API protection.
"""

import asyncio
import time
from market_mcp.cache.rate_limited_cache_service import RateLimitedCacheService
from market_mcp.utils.config_manager import ConfigManager


async def simulate_stock_request(service, symbol: str) -> dict:
    """Simulate making a stock price API request."""

    # Check if we can make the request or use cache
    data, is_cached, message = await service.get_cached_or_wait(symbol)

    if data:
        print(
            f"✅ {symbol}: Got cached data - {data['data']['price']} (Reason: {message})"
        )
        await service.record_cached_response(symbol)
        return data["data"]

    if "cache_miss_can_make_request" in message:
        # Simulate API call delay
        print(f"🌐 {symbol}: Making API request...")
        await asyncio.sleep(0.05)  # Simulate 50ms API call

        # Simulate response data
        fake_data = {
            "symbol": symbol,
            "price": 100 + hash(symbol) % 50,  # Fake price based on symbol
            "volume": 1000 + hash(symbol) % 5000,
            "timestamp": time.time(),
        }

        # Record successful request
        await service.record_successful_request(symbol, fake_data, 50.0)
        print(
            f"✅ {symbol}: API success - Price: {fake_data['price']}, Volume: {fake_data['volume']}"
        )
        return fake_data

    else:
        print(f"🚫 {symbol}: Rate limited and no cache available (Reason: {message})")
        return None


async def demonstrate_rate_limiting():
    """Demonstrate the rate limiting and caching system."""

    print("🚀 Taiwan Stock Exchange API Rate Limiting Demo")
    print("=" * 60)

    # Configure for demo (faster limits)
    config = ConfigManager()
    config.set("rate_limiting.per_stock_interval_seconds", 2.0)  # 2 sec per stock
    config.set("rate_limiting.global_limit_per_minute", 5)  # 5 requests per minute
    config.set("rate_limiting.per_second_limit", 2)  # 2 per second
    config.set("caching.ttl_seconds", 3)  # 3 second cache

    service = RateLimitedCacheService(config)

    print("\n📋 Configuration:")
    print(f"   • Per stock: 1 request every 2 seconds")
    print(f"   • Global: 5 requests per minute")
    print(f"   • Per second: 2 requests maximum")
    print(f"   • Cache TTL: 3 seconds")

    # Test scenarios
    symbols = ["2330", "2317", "0050", "1101", "2454"]

    print("\n🧪 Test 1: Initial requests (should work)")
    print("-" * 40)
    for symbol in symbols[:3]:
        await simulate_stock_request(service, symbol)
        await asyncio.sleep(0.6)  # Space out requests

    print("\n🧪 Test 2: Immediate re-requests (should use cache)")
    print("-" * 40)
    for symbol in symbols[:3]:
        await simulate_stock_request(service, symbol)

    print("\n🧪 Test 3: Hit global rate limit")
    print("-" * 40)
    await simulate_stock_request(service, symbols[3])
    await simulate_stock_request(service, symbols[4])

    print("\n🧪 Test 4: Per-second rate limiting")
    print("-" * 40)
    print("Making 3 rapid requests...")
    for i in range(3):
        await simulate_stock_request(service, f"RAPID_{i}")

    print("\n📊 System Statistics:")
    print("-" * 40)
    stats = service.get_comprehensive_stats()

    # Global stats
    global_stats = stats["request_tracker"]["global"]
    print(f"Total requests: {global_stats['total_requests']}")
    print(f"Success rate: {global_stats['success_rate_percent']}%")
    print(f"Cache hit rate: {global_stats['cache_hit_rate_percent']}%")

    # Rate limiter stats
    rate_stats = stats["rate_limiter"]
    print(
        f"Requests last minute: {rate_stats['global_requests_last_minute']}/{rate_stats['global_limit_per_minute']}"
    )
    print(
        f"Requests last second: {rate_stats['requests_last_second']}/{rate_stats['per_second_limit']}"
    )

    # Cache stats
    cache_stats = stats["cache_manager"]
    print(f"Cache entries: {cache_stats['cache_entries']}/{cache_stats['max_entries']}")
    print(
        f"Memory usage: {cache_stats['memory_usage_mb']:.2f}MB/{cache_stats['memory_limit_mb']}MB"
    )

    # Rate limit events
    rate_limit_summary = stats["request_tracker"]["rate_limits"]
    print(f"Rate limit events: {rate_limit_summary['total_events']}")

    print("\n🏥 Health Check:")
    print("-" * 40)
    health = await service.health_check()
    print(f"Overall healthy: {'✅ YES' if health['overall_healthy'] else '❌ NO'}")

    if health["issues"]:
        print("Issues found:")
        for issue in health["issues"]:
            print(f"  • {issue}")

    if health["recommendations"]:
        print("Recommendations:")
        for rec in health["recommendations"]:
            print(f"  • {rec}")

    print("\n🧪 Test 5: Wait for cache expiry and retry")
    print("-" * 40)
    print("Waiting 4 seconds for cache to expire...")
    await asyncio.sleep(4)

    await simulate_stock_request(service, "2330")  # Should be rate limited but no cache

    print("\n✨ Demo completed!")


if __name__ == "__main__":
    asyncio.run(demonstrate_rate_limiting())
