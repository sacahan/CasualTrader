"""
Multi-layered API rate limiting mechanism for protecting Taiwan Stock Exchange API.
Implements per-stock, global, and per-second rate limiting.
"""

import asyncio
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Multi-layered rate limiter with the following constraints:
    - Per stock: 1 request per 30 seconds
    - Global: 20 requests per minute
    - Per second: 2 requests maximum
    """

    def __init__(
        self,
        per_stock_interval: float = 30.0,  # 30 seconds per stock
        global_limit_per_minute: int = 20,  # 20 requests per minute
        per_second_limit: int = 2,  # 2 requests per second
    ):
        self.per_stock_interval = per_stock_interval
        self.global_limit_per_minute = global_limit_per_minute
        self.per_second_limit = per_second_limit

        # Per-stock tracking
        self.last_request_time: Dict[str, float] = defaultdict(float)
        self.stock_lock = Lock()

        # Global request tracking (sliding window)
        self.global_requests: deque = deque()
        self.global_lock = Lock()

        # Per-second tracking
        self.per_second_requests: deque = deque()
        self.per_second_lock = Lock()

    def _clean_old_requests(self, request_deque: deque, time_window: float) -> None:
        """Remove requests older than time_window seconds."""
        current_time = time.time()
        while request_deque and request_deque[0] <= current_time - time_window:
            request_deque.popleft()

    def can_request_stock(self, symbol: str) -> tuple[bool, float]:
        """
        Check if we can make a request for a specific stock.
        Returns (can_request, wait_time_seconds)
        """
        with self.stock_lock:
            current_time = time.time()
            last_request = self.last_request_time.get(symbol, 0)
            time_since_last = current_time - last_request

            if time_since_last >= self.per_stock_interval:
                return True, 0.0
            else:
                wait_time = self.per_stock_interval - time_since_last
                return False, wait_time

    def can_request_global(self) -> tuple[bool, float]:
        """
        Check global rate limit (20 requests per minute).
        Returns (can_request, wait_time_seconds)
        """
        with self.global_lock:
            current_time = time.time()
            self._clean_old_requests(self.global_requests, 60.0)  # 1 minute window

            if len(self.global_requests) < self.global_limit_per_minute:
                return True, 0.0
            else:
                # Calculate wait time until oldest request expires
                oldest_request = self.global_requests[0]
                wait_time = 60.0 - (current_time - oldest_request)
                return False, max(0, wait_time)

    def can_request_per_second(self) -> tuple[bool, float]:
        """
        Check per-second rate limit (2 requests per second).
        Returns (can_request, wait_time_seconds)
        """
        with self.per_second_lock:
            current_time = time.time()
            self._clean_old_requests(self.per_second_requests, 1.0)  # 1 second window

            if len(self.per_second_requests) < self.per_second_limit:
                return True, 0.0
            else:
                # Calculate wait time until oldest request expires
                oldest_request = self.per_second_requests[0]
                wait_time = 1.0 - (current_time - oldest_request)
                return False, max(0, wait_time)

    async def can_request(self, symbol: str) -> tuple[bool, str, float]:
        """
        Check if we can make a request for a specific stock across all rate limits.
        Returns (can_request, reason, max_wait_time_seconds)
        """
        # Check all rate limits
        stock_ok, stock_wait = self.can_request_stock(symbol)
        global_ok, global_wait = self.can_request_global()
        per_sec_ok, per_sec_wait = self.can_request_per_second()

        # Find the most restrictive limit
        max_wait = max(stock_wait, global_wait, per_sec_wait)

        if stock_ok and global_ok and per_sec_ok:
            return True, "allowed", 0.0

        # Determine which limit is blocking
        if not stock_ok and stock_wait == max_wait:
            reason = f"stock_limit_exceeded_for_{symbol}"
        elif not global_ok and global_wait == max_wait:
            reason = "global_limit_exceeded"
        else:
            reason = "per_second_limit_exceeded"

        return False, reason, max_wait

    async def record_request(self, symbol: str) -> None:
        """Record that a request was made for a specific stock."""
        current_time = time.time()

        # Record per-stock request
        with self.stock_lock:
            self.last_request_time[symbol] = current_time

        # Record global request
        with self.global_lock:
            self.global_requests.append(current_time)
            self._clean_old_requests(self.global_requests, 60.0)

        # Record per-second request
        with self.per_second_lock:
            self.per_second_requests.append(current_time)
            self._clean_old_requests(self.per_second_requests, 1.0)

        logger.debug(f"Recorded API request for symbol: {symbol}")

    def get_stats(self) -> Dict[str, any]:
        """Get current rate limiter statistics."""
        current_time = time.time()

        with self.global_lock:
            self._clean_old_requests(self.global_requests, 60.0)
            global_requests_count = len(self.global_requests)

        with self.per_second_lock:
            self._clean_old_requests(self.per_second_requests, 1.0)
            per_second_count = len(self.per_second_requests)

        with self.stock_lock:
            tracked_stocks = len(self.last_request_time)

        return {
            "global_requests_last_minute": global_requests_count,
            "global_limit_per_minute": self.global_limit_per_minute,
            "requests_last_second": per_second_count,
            "per_second_limit": self.per_second_limit,
            "tracked_stocks_count": tracked_stocks,
            "per_stock_interval_seconds": self.per_stock_interval,
        }

    def reset_limits(self) -> None:
        """Reset all rate limiting counters. Use with caution."""
        with self.stock_lock:
            self.last_request_time.clear()

        with self.global_lock:
            self.global_requests.clear()

        with self.per_second_lock:
            self.per_second_requests.clear()

        logger.info("Rate limiter counters have been reset")
