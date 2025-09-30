"""
High-performance cache manager with TTL (Time To Live) strategy.
Implements intelligent caching for Taiwan Stock Exchange API responses.
"""

import time
import logging
from typing import Any, Optional
from cachetools import TTLCache
from threading import RLock
import sys

logger = logging.getLogger(__name__)


class CacheManager:
    """
    TTL-based cache manager with memory usage control.
    Target: 80% cache hit rate, <200MB memory usage.
    """

    def __init__(
        self,
        ttl_seconds: int = 30,
        max_size: int = 1000,
        max_memory_mb: float = 200.0,
    ):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb

        # Thread-safe TTL cache
        self.cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self.cache_lock = RLock()

        # Statistics tracking
        self.hit_count = 0
        self.miss_count = 0
        self.stats_lock = RLock()

    def _generate_cache_key(self, symbol: str, request_type: str = "quote") -> str:
        """Generate a unique cache key for the request."""
        return f"{request_type}:{symbol.upper()}"

    def _estimate_memory_usage(self) -> float:
        """Estimate current memory usage in MB."""
        try:
            # Get the size of the cache object
            cache_size = sys.getsizeof(self.cache)

            # Estimate size of cached data
            data_size = 0
            with self.cache_lock:
                # TTLCache uses internal data structure
                for key, value in self.cache.items():
                    data_size += sys.getsizeof(key) + sys.getsizeof(value)

            total_mb = (cache_size + data_size) / (1024 * 1024)
            return total_mb
        except Exception as e:
            logger.warning(f"Could not estimate memory usage: {e}")
            return 0.0

    async def get_cached_data(
        self, symbol: str, request_type: str = "quote"
    ) -> Optional[dict]:
        """
        Retrieve cached data for a stock symbol.
        Returns None if not found or expired.
        """
        cache_key = self._generate_cache_key(symbol, request_type)

        with self.cache_lock:
            try:
                data = self.cache.get(cache_key)
                if data is not None:
                    with self.stats_lock:
                        self.hit_count += 1
                    logger.debug(f"Cache HIT for {cache_key}")
                    return data
                else:
                    with self.stats_lock:
                        self.miss_count += 1
                    logger.debug(f"Cache MISS for {cache_key}")
                    return None
            except Exception as e:
                logger.error(f"Error retrieving cached data for {cache_key}: {e}")
                with self.stats_lock:
                    self.miss_count += 1
                return None

    async def set_cached_data(
        self, symbol: str, data: dict, request_type: str = "quote"
    ) -> bool:
        """
        Store data in cache with TTL.
        Returns True if successfully cached, False otherwise.
        """
        cache_key = self._generate_cache_key(symbol, request_type)

        # Check memory usage before adding new data
        current_memory = self._estimate_memory_usage()
        if current_memory > self.max_memory_mb:
            logger.warning(
                f"Memory usage ({current_memory:.1f}MB) exceeds limit "
                f"({self.max_memory_mb}MB). Not caching new data."
            )
            return False

        with self.cache_lock:
            try:
                # Add metadata to cached data
                enriched_data = {
                    "symbol": symbol.upper(),
                    "request_type": request_type,
                    "cached_at": time.time(),
                    "ttl_seconds": self.ttl_seconds,
                    "data": data,
                }

                self.cache[cache_key] = enriched_data
                logger.debug(f"Cached data for {cache_key}")
                return True
            except Exception as e:
                logger.error(f"Error caching data for {cache_key}: {e}")
                return False

    async def invalidate(self, symbol: str, request_type: str = "quote") -> bool:
        """Remove specific data from cache."""
        cache_key = self._generate_cache_key(symbol, request_type)

        with self.cache_lock:
            try:
                if cache_key in self.cache:
                    del self.cache[cache_key]
                    logger.debug(f"Invalidated cache for {cache_key}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Error invalidating cache for {cache_key}: {e}")
                return False

    async def clear_all(self) -> None:
        """Clear all cached data."""
        with self.cache_lock:
            self.cache.clear()

        with self.stats_lock:
            self.hit_count = 0
            self.miss_count = 0

        logger.info("Cache cleared completely")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get detailed cache statistics."""
        with self.stats_lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (
                (self.hit_count / total_requests * 100) if total_requests > 0 else 0.0
            )

        with self.cache_lock:
            cache_size = len(self.cache)
            memory_usage = self._estimate_memory_usage()

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_entries": cache_size,
            "max_entries": self.max_size,
            "memory_usage_mb": round(memory_usage, 2),
            "memory_limit_mb": self.max_memory_mb,
            "ttl_seconds": self.ttl_seconds,
        }

    def is_cache_healthy(self) -> tuple[bool, list[str]]:
        """
        Check if cache is performing within acceptable parameters.
        Returns (is_healthy, list_of_issues)
        """
        issues = []
        stats = self.get_cache_stats()

        # Check hit rate (target: 80%+)
        if stats["total_requests"] > 10 and stats["hit_rate_percent"] < 80.0:
            issues.append(f"Low hit rate: {stats['hit_rate_percent']}% (target: 80%+)")

        # Check memory usage
        if stats["memory_usage_mb"] > stats["memory_limit_mb"]:
            issues.append(
                f"Memory usage exceeded: {stats['memory_usage_mb']}MB "
                f"(limit: {stats['memory_limit_mb']}MB)"
            )

        # Check cache utilization
        utilization = (stats["cache_entries"] / stats["max_entries"]) * 100
        if utilization > 95.0:
            issues.append(
                f"Cache nearly full: {utilization:.1f}% "
                f"({stats['cache_entries']}/{stats['max_entries']})"
            )

        return len(issues) == 0, issues

    async def get_all_cached_symbols(self) -> list[str]:
        """Get list of all currently cached symbols."""
        symbols = set()

        with self.cache_lock:
            for key in self.cache.keys():
                # Extract symbol from cache key format "request_type:SYMBOL"
                if ":" in key:
                    symbol = key.split(":", 1)[1]
                    symbols.add(symbol)

        return sorted(list(symbols))
