"""
Dynamic configuration manager for rate limiting and cache parameters.
Allows runtime adjustment of system parameters for optimal performance.
"""

import json
import logging
from pathlib import Path
from typing import Any
import threading

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Thread-safe configuration manager for dynamic parameter adjustment.
    Supports runtime updates and configuration persistence.
    """

    def __init__(self, config_file: str | None = None):
        self.config_file = Path(config_file) if config_file else None
        self.lock = threading.RLock()

        # Default configuration
        self._config = {
            "rate_limiting": {
                "per_stock_interval_seconds": 30.0,
                "global_limit_per_minute": 20,
                "per_second_limit": 2,
                "enabled": True,
            },
            "caching": {
                "ttl_seconds": 30,
                "max_size": 1000,
                "max_memory_mb": 200.0,
                "enabled": True,
            },
            "api": {
                "base_url": "https://www.twse.com.tw",
                "timeout_seconds": 10.0,
                "retry_attempts": 3,
                "retry_delay_seconds": 1.0,
            },
            "monitoring": {
                "stats_retention_hours": 24,
                "performance_threshold_ms": 5000.0,
                "cache_hit_rate_target_percent": 80.0,
                "enable_detailed_logging": False,
            },
        }

        # Load configuration from file if it exists
        self.load_config()

    def load_config(self) -> bool:
        """Load configuration from file. Returns True if successful."""
        if not self.config_file or not self.config_file.exists():
            logger.info("No configuration file found, using defaults")
            return False

        try:
            with self.lock:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)

                # Merge with defaults (file config takes precedence)
                self._merge_config(self._config, file_config)

                logger.info(f"Configuration loaded from {self.config_file}")
                return True
        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_file}: {e}")
            return False

    def save_config(self) -> bool:
        """Save current configuration to file. Returns True if successful."""
        if not self.config_file:
            logger.warning("No configuration file path specified")
            return False

        try:
            with self.lock:
                # Create directory if it doesn't exist
                self.config_file.parent.mkdir(parents=True, exist_ok=True)

                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)

                logger.info(f"Configuration saved to {self.config_file}")
                return True
        except Exception as e:
            logger.error(f"Failed to save configuration to {self.config_file}: {e}")
            return False

    def _merge_config(self, target: dict, source: dict) -> None:
        """Recursively merge source config into target config."""
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_config(target[key], value)
            else:
                target[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        Example: get('rate_limiting.per_stock_interval_seconds')
        """
        with self.lock:
            keys = key_path.split(".")
            value = self._config

            try:
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                logger.debug(
                    f"Configuration key '{key_path}' not found, returning default"
                )
                return default

    def set(self, key_path: str, value: Any, save_to_file: bool = False) -> bool:
        """
        Set configuration value using dot notation.
        Returns True if successful.
        """
        with self.lock:
            keys = key_path.split(".")
            config = self._config

            try:
                # Navigate to the parent of the target key
                for key in keys[:-1]:
                    if key not in config:
                        config[key] = {}
                    config = config[key]

                # Set the final key
                config[keys[-1]] = value

                logger.info(f"Configuration updated: {key_path} = {value}")

                if save_to_file:
                    return self.save_config()

                return True
            except Exception as e:
                logger.error(f"Failed to set configuration {key_path}: {e}")
                return False

    def get_rate_limiting_config(self) -> dict[str, Any]:
        """Get rate limiting configuration."""
        with self.lock:
            return self._config.get("rate_limiting", {}).copy()

    def get_caching_config(self) -> dict[str, Any]:
        """Get caching configuration."""
        with self.lock:
            return self._config.get("caching", {}).copy()

    def get_api_config(self) -> dict[str, Any]:
        """Get API configuration."""
        with self.lock:
            return self._config.get("api", {}).copy()

    def get_monitoring_config(self) -> dict[str, Any]:
        """Get monitoring configuration."""
        with self.lock:
            return self._config.get("monitoring", {}).copy()

    def update_rate_limits(
        self,
        per_stock_interval: float | None = None,
        global_limit_per_minute: int | None = None,
        per_second_limit: int | None = None,
        save_to_file: bool = False,
    ) -> bool:
        """Update rate limiting parameters."""
        try:
            with self.lock:
                if per_stock_interval is not None:
                    self._config["rate_limiting"]["per_stock_interval_seconds"] = (
                        per_stock_interval
                    )

                if global_limit_per_minute is not None:
                    self._config["rate_limiting"]["global_limit_per_minute"] = (
                        global_limit_per_minute
                    )

                if per_second_limit is not None:
                    self._config["rate_limiting"]["per_second_limit"] = per_second_limit

                logger.info("Rate limiting configuration updated")

                if save_to_file:
                    return self.save_config()

                return True
        except Exception as e:
            logger.error(f"Failed to update rate limiting config: {e}")
            return False

    def update_cache_settings(
        self,
        ttl_seconds: int | None = None,
        max_size: int | None = None,
        max_memory_mb: float | None = None,
        save_to_file: bool = False,
    ) -> bool:
        """Update cache configuration."""
        try:
            with self.lock:
                if ttl_seconds is not None:
                    self._config["caching"]["ttl_seconds"] = ttl_seconds

                if max_size is not None:
                    self._config["caching"]["max_size"] = max_size

                if max_memory_mb is not None:
                    self._config["caching"]["max_memory_mb"] = max_memory_mb

                logger.info("Cache configuration updated")

                if save_to_file:
                    return self.save_config()

                return True
        except Exception as e:
            logger.error(f"Failed to update cache config: {e}")
            return False

    def is_rate_limiting_enabled(self) -> bool:
        """Check if rate limiting is enabled."""
        return self.get("rate_limiting.enabled", True)

    def is_caching_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.get("caching.enabled", True)

    def enable_feature(self, feature: str, save_to_file: bool = False) -> bool:
        """Enable a feature (rate_limiting or caching)."""
        return self.set(f"{feature}.enabled", True, save_to_file)

    def disable_feature(self, feature: str, save_to_file: bool = False) -> bool:
        """Disable a feature (rate_limiting or caching)."""
        return self.set(f"{feature}.enabled", False, save_to_file)

    def get_all_config(self) -> dict[str, Any]:
        """Get a copy of the entire configuration."""
        with self.lock:
            return json.loads(json.dumps(self._config))  # Deep copy

    def reset_to_defaults(self, save_to_file: bool = False) -> bool:
        """Reset configuration to default values."""
        try:
            with self.lock:
                self._config = {
                    "rate_limiting": {
                        "per_stock_interval_seconds": 30.0,
                        "global_limit_per_minute": 20,
                        "per_second_limit": 2,
                        "enabled": True,
                    },
                    "caching": {
                        "ttl_seconds": 30,
                        "max_size": 1000,
                        "max_memory_mb": 200.0,
                        "enabled": True,
                    },
                    "api": {
                        "base_url": "https://www.twse.com.tw",
                        "timeout_seconds": 10.0,
                        "retry_attempts": 3,
                        "retry_delay_seconds": 1.0,
                    },
                    "monitoring": {
                        "stats_retention_hours": 24,
                        "performance_threshold_ms": 5000.0,
                        "cache_hit_rate_target_percent": 80.0,
                        "enable_detailed_logging": False,
                    },
                }

                logger.info("Configuration reset to defaults")

                if save_to_file:
                    return self.save_config()

                return True
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            return False
