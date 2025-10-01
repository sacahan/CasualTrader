"""
Enhanced Taiwan Stock Exchange API client with rate limiting and caching.
Integrates the rate limiting and caching system with the existing TWSE API client.
"""

import asyncio
import time
from typing import Any

from ..cache.rate_limited_cache_service import RateLimitedCacheService
from ..models.stock_data import APIError, TWStockResponse, ValidationError
from ..utils.config_manager import ConfigManager
from ..utils.logging import logger
from .twse_client import TWStockAPIClient


class EnhancedTWStockAPIClient:
    """
    Enhanced Taiwan Stock Exchange API client with intelligent rate limiting and caching.

    This client wraps the original TWStockAPIClient and adds:
    - Multi-layered rate limiting (per-stock, global, per-second)
    - Intelligent TTL-based caching
    - Performance monitoring and statistics
    - Automatic fallback to cached data when rate limited
    """

    def __init__(self, config_file: str | None = None):
        """Initialize the enhanced API client."""
        self.config = ConfigManager(config_file)
        self.cache_service = RateLimitedCacheService(self.config)
        self.original_client = TWStockAPIClient()

        logger.info(
            "Enhanced TWSE API client initialized with rate limiting and caching"
        )

    async def get_stock_quote(
        self, symbol: str, market: str | None = None, force_refresh: bool = False
    ) -> TWStockResponse:
        """
        Get real-time stock quote with intelligent caching and rate limiting.

        Args:
            symbol: Stock symbol (4-digit code)
            market: Market type ('tse' or 'otc'), auto-detected if None
            force_refresh: If True, bypass cache and make fresh API request

        Returns:
            TWStockResponse: Stock quote data

        Raises:
            ValidationError: Invalid stock symbol format
            APIError: API request failed and no cached data available
        """
        start_time = time.time()

        try:
            # If force refresh requested, invalidate cache first
            if force_refresh:
                await self.cache_service.invalidate_symbol_cache(symbol, "quote")

            # Check cache and rate limits
            (
                cached_data,
                is_from_cache,
                message,
            ) = await self.cache_service.get_cached_or_wait(symbol, "quote")

            if cached_data:
                # Return cached data
                response_time = (time.time() - start_time) * 1000
                await self.cache_service.record_cached_response(symbol, "quote")

                logger.debug(
                    f"Returned cached data for {symbol} ({response_time:.2f}ms)"
                )
                return self._cached_data_to_response(cached_data["data"])

            if "cache_miss_can_make_request" in message:
                # Make fresh API request
                try:
                    response = await self.original_client.get_stock_quote(
                        symbol, market
                    )
                    response_time = (time.time() - start_time) * 1000

                    # Cache the successful response
                    response_dict = self._response_to_dict(response)
                    await self.cache_service.record_successful_request(
                        symbol, response_dict, response_time, "quote"
                    )

                    logger.debug(f"Fresh API data for {symbol} ({response_time:.2f}ms)")
                    return response

                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    await self.cache_service.record_failed_request(
                        symbol, response_time, "quote"
                    )

                    logger.error(f"API request failed for {symbol}: {e}")
                    raise APIError(f"API request failed for {symbol}: {str(e)}")

            else:
                # Rate limited and no cache available
                logger.warning(
                    f"Rate limited for {symbol} with no cached data available: {message}"
                )
                raise APIError(
                    f"Rate limited for stock {symbol} and no cached data available. "
                    f"Please try again later. (Reason: {message})"
                )

        except (ValidationError, APIError):
            # Re-raise validation and API errors as-is
            raise
        except Exception as e:
            # Handle unexpected errors
            response_time = (time.time() - start_time) * 1000
            await self.cache_service.record_failed_request(
                symbol, response_time, "quote"
            )

            logger.error(f"Unexpected error for {symbol}: {e}")
            raise APIError(f"Unexpected error retrieving data for {symbol}: {str(e)}")

    async def get_multiple_quotes(
        self, symbols: list[str], force_refresh: bool = False
    ) -> list[TWStockResponse]:
        """
        Get real-time quotes for multiple stocks with intelligent batching.

        Args:
            symbols: List of stock symbols
            force_refresh: If True, bypass cache for all symbols

        Returns:
            List of stock quote responses (may be fewer than requested due to rate limits)
        """
        logger.info(f"Fetching quotes for {len(symbols)} symbols")

        # Create tasks for all symbols
        tasks = []
        for symbol in symbols:
            task = self.get_stock_quote(symbol, force_refresh=force_refresh)
            tasks.append(task)

        # Execute with proper rate limiting
        results = []
        for i, task in enumerate(tasks):
            try:
                result = await task
                results.append(result)

                # Add small delay between requests to respect rate limits
                if i < len(tasks) - 1:  # Don't delay after last request
                    await asyncio.sleep(0.1)  # 100ms delay

            except Exception as e:
                logger.warning(f"Failed to get quote for symbol {symbols[i]}: {e}")
                # Continue with other symbols

        logger.info(f"Successfully retrieved {len(results)}/{len(symbols)} quotes")
        return results

    def _response_to_dict(self, response: TWStockResponse) -> dict:
        """Convert TWStockResponse to dictionary for caching."""
        return {
            "symbol": response.symbol,
            "name": response.name,
            "market": response.market,
            "timestamp": response.timestamp,
            "price": response.price,
            "change": response.change,
            "change_percent": response.change_percent,
            "volume": response.volume,
            "high": response.high,
            "low": response.low,
            "open": response.open,
            "yesterday_close": response.yesterday_close,
        }

    def _cached_data_to_response(self, data: dict) -> TWStockResponse:
        """Convert cached dictionary data back to TWStockResponse."""
        return TWStockResponse(**data)

    async def get_system_stats(self) -> dict[str, Any]:
        """Get comprehensive system statistics."""
        return self.cache_service.get_comprehensive_stats()

    async def get_health_status(self) -> dict[str, Any]:
        """Get system health status."""
        return await self.cache_service.health_check()

    async def clear_cache(self) -> None:
        """Clear all cached data."""
        await self.cache_service.clear_all_cache()
        logger.info("Cache cleared")

    async def reset_rate_limits(self) -> None:
        """Reset all rate limiting counters."""
        await self.cache_service.reset_rate_limits()
        logger.info("Rate limits reset")

    async def invalidate_symbol_cache(self, symbol: str) -> bool:
        """Manually invalidate cache for a specific symbol."""
        success = await self.cache_service.invalidate_symbol_cache(symbol, "quote")
        logger.info(f"Cache invalidated for {symbol}: {success}")
        return success

    def get_configuration(self) -> dict[str, Any]:
        """Get current system configuration."""
        return self.cache_service.config.get_all_config()

    def update_rate_limits(
        self,
        per_stock_interval: float | None = None,
        global_limit_per_minute: int | None = None,
        per_second_limit: int | None = None,
        save_to_file: bool = False,
    ) -> bool:
        """Update rate limiting parameters."""
        success = self.cache_service.config.update_rate_limits(
            per_stock_interval, global_limit_per_minute, per_second_limit, save_to_file
        )
        logger.info(f"Rate limits updated: {success}")
        return success

    def update_cache_settings(
        self,
        ttl_seconds: int | None = None,
        max_size: int | None = None,
        max_memory_mb: float | None = None,
        save_to_file: bool = False,
    ) -> bool:
        """Update cache configuration."""
        success = self.cache_service.config.update_cache_settings(
            ttl_seconds, max_size, max_memory_mb, save_to_file
        )
        logger.info(f"Cache settings updated: {success}")
        return success

    def enable_rate_limiting(self, save_to_file: bool = False) -> bool:
        """Enable rate limiting feature."""
        return self.cache_service.config.enable_feature("rate_limiting", save_to_file)

    def disable_rate_limiting(self, save_to_file: bool = False) -> bool:
        """Disable rate limiting feature."""
        return self.cache_service.config.disable_feature("rate_limiting", save_to_file)

    def enable_caching(self, save_to_file: bool = False) -> bool:
        """Enable caching feature."""
        return self.cache_service.config.enable_feature("caching", save_to_file)

    def disable_caching(self, save_to_file: bool = False) -> bool:
        """Disable caching feature."""
        return self.cache_service.config.disable_feature("caching", save_to_file)

    def is_rate_limiting_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self.cache_service.config.is_rate_limiting_enabled()

    def is_caching_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.cache_service.config.is_caching_enabled()


# Convenience function to create enhanced client
def create_enhanced_client(config_file: str | None = None) -> EnhancedTWStockAPIClient:
    """Create an enhanced TWSE API client with rate limiting and caching."""
    return EnhancedTWStockAPIClient(config_file)
