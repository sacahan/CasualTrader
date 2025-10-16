"""
SubAgentLoader - Sub-agents 動態載入和管理機制

提供從 tools/ 目錄動態發現、載入、驗證和管理 Sub-agents 的功能。
支援根據 Agent 配置過濾啟用的 Sub-agents。
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Callable

from agents import Agent

logger = logging.getLogger(__name__)


# ==========================================
# Custom Exceptions
# ==========================================


class SubAgentLoadError(Exception):
    """Sub-agent 載入錯誤"""

    pass


class SubAgentValidationError(Exception):
    """Sub-agent 驗證錯誤"""

    pass


# ==========================================
# Sub-Agent 配置
# ==========================================


class SubAgentConfig:
    """Sub-agent 配置資訊"""

    def __init__(
        self,
        name: str,
        module_path: str,
        instructions_fn: Callable[[], str],
        factory_fn: Callable[..., Agent] | None = None,
        description: str = "",
        enabled_by_default: bool = True,
    ):
        """
        初始化 Sub-agent 配置

        Args:
            name: Sub-agent 名稱（例如：'fundamental'）
            module_path: 模組路徑（例如：'src.agents.tools.fundamental_agent'）
            instructions_fn: 返回 instructions 的函數
            factory_fn: 創建 Agent 實例的工廠函數（可選）
            description: Sub-agent 描述
            enabled_by_default: 是否預設啟用
        """
        self.name = name
        self.module_path = module_path
        self.instructions_fn = instructions_fn
        self.factory_fn = factory_fn
        self.description = description
        self.enabled_by_default = enabled_by_default

    def __repr__(self) -> str:
        return f"<SubAgentConfig {self.name} ({self.module_path})>"


# ==========================================
# SubAgentLoader
# ==========================================


class SubAgentLoader:
    """
    Sub-agents 載入器

    負責從 tools/ 目錄動態發現、載入和管理 Sub-agents。
    """

    # 預期的 Sub-agent 模組名稱模式
    SUBAGENT_PATTERNS = [
        "fundamental_agent",
        "technical_agent",
        "risk_agent",
        "sentiment_agent",
    ]

    # Sub-agent 名稱映射（從模組名到顯示名稱）
    NAME_MAPPING = {
        "fundamental_agent": "fundamental",
        "technical_agent": "technical",
        "risk_agent": "risk",
        "sentiment_agent": "sentiment",
    }

    def __init__(self, tools_package: str = "src.agents.tools"):
        """
        初始化 SubAgentLoader

        Args:
            tools_package: tools 套件的完整路徑
        """
        self.tools_package = tools_package
        self.discovered_configs: list[SubAgentConfig] = []
        self.loaded_agents: dict[str, Agent] = {}

        logger.info(f"SubAgentLoader initialized for package: {tools_package}")

    def discover_subagents(self) -> list[SubAgentConfig]:
        """
        發現可用的 Sub-agents

        Returns:
            Sub-agent 配置列表

        Raises:
            SubAgentLoadError: 發現過程失敗
        """
        configs = []

        for module_name in self.SUBAGENT_PATTERNS:
            try:
                config = self._discover_single_subagent(module_name)
                if config:
                    configs.append(config)
                    logger.info(f"Discovered sub-agent: {config.name}")
            except Exception as e:
                logger.warning(f"Failed to discover sub-agent '{module_name}': {e}")
                # 繼續處理其他 Sub-agents

        self.discovered_configs = configs
        logger.info(f"Discovery completed: {len(configs)} sub-agents found")
        return configs

    def _discover_single_subagent(self, module_name: str) -> SubAgentConfig | None:
        """
        發現單一 Sub-agent

        Args:
            module_name: 模組名稱（例如：'fundamental_agent'）

        Returns:
            SubAgentConfig 或 None（如果發現失敗）
        """
        module_path = f"{self.tools_package}.{module_name}"

        try:
            # 動態導入模組
            module = importlib.import_module(module_path)

            # 尋找 instructions 函數
            instructions_fn_name = f"{module_name}_instructions"
            instructions_fn = getattr(module, instructions_fn_name, None)

            if not instructions_fn or not callable(instructions_fn):
                logger.warning(f"Module '{module_name}' missing '{instructions_fn_name}' function")
                return None

            # 嘗試尋找工廠函數（可選）
            factory_fn_name = f"create_{module_name}"
            factory_fn = getattr(module, factory_fn_name, None)

            # 取得 Sub-agent 名稱
            subagent_name = self.NAME_MAPPING.get(module_name, module_name)

            # 嘗試從模組 docstring 取得描述
            description = module.__doc__.strip() if module.__doc__ else ""

            return SubAgentConfig(
                name=subagent_name,
                module_path=module_path,
                instructions_fn=instructions_fn,
                factory_fn=factory_fn,
                description=description,
                enabled_by_default=True,
            )

        except ImportError as e:
            logger.warning(f"Failed to import module '{module_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error discovering '{module_name}': {e}", exc_info=True)
            return None

    def filter_enabled_subagents(self, preferences: dict[str, Any]) -> list[SubAgentConfig]:
        """
        根據投資偏好過濾啟用的 Sub-agents

        Args:
            preferences: 投資偏好字典（包含 enabled_tools）

        Returns:
            啟用的 Sub-agent 配置列表
        """
        enabled_tools = preferences.get("enabled_tools", {})

        if not enabled_tools:
            # 如果沒有配置，返回所有預設啟用的
            logger.info("No enabled_tools config, using all default sub-agents")
            return [c for c in self.discovered_configs if c.enabled_by_default]

        filtered = []
        for config in self.discovered_configs:
            # 檢查對應的工具是否啟用
            # 例如：fundamental -> fundamental_analysis
            tool_key = f"{config.name}_analysis"
            is_enabled = enabled_tools.get(tool_key, config.enabled_by_default)

            if is_enabled:
                filtered.append(config)
                logger.debug(f"Sub-agent enabled: {config.name}")
            else:
                logger.debug(f"Sub-agent disabled: {config.name}")

        logger.info(f"Filtered sub-agents: {len(filtered)}/{len(self.discovered_configs)}")
        return filtered

    def load_subagents(
        self,
        configs: list[SubAgentConfig],
        model: str = "gpt-4o-mini",
        **agent_kwargs: Any,
    ) -> list[Agent]:
        """
        載入 Sub-agents

        Args:
            configs: Sub-agent 配置列表
            model: 使用的 AI 模型
            **agent_kwargs: 傳遞給 Agent 的額外參數

        Returns:
            Agent 實例列表

        Raises:
            SubAgentLoadError: 載入失敗
        """
        agents = []

        for config in configs:
            try:
                agent = self._load_single_subagent(config, model, **agent_kwargs)
                if agent:
                    agents.append(agent)
                    self.loaded_agents[config.name] = agent
                    logger.info(f"Loaded sub-agent: {config.name}")
            except Exception as e:
                logger.error(f"Failed to load sub-agent '{config.name}': {e}", exc_info=True)
                # 繼續載入其他 Sub-agents
                continue

        logger.info(f"Loaded {len(agents)}/{len(configs)} sub-agents")
        return agents

    def _load_single_subagent(
        self, config: SubAgentConfig, model: str, **agent_kwargs: Any
    ) -> Agent | None:
        """
        載入單一 Sub-agent

        Args:
            config: Sub-agent 配置
            model: AI 模型
            **agent_kwargs: 額外參數

        Returns:
            Agent 實例或 None
        """
        try:
            # 如果有工廠函數，使用工廠函數
            if config.factory_fn:
                return config.factory_fn(model=model, **agent_kwargs)

            # 否則直接創建 Agent
            instructions = config.instructions_fn()

            agent = Agent(
                name=f"{config.name.capitalize()} Agent",
                instructions=instructions,
                model=model,
                **agent_kwargs,
            )

            # 驗證 Agent
            self._validate_agent(agent, config.name)

            return agent

        except Exception as e:
            logger.error(f"Error loading sub-agent '{config.name}': {e}")
            raise SubAgentLoadError(f"Failed to load '{config.name}': {str(e)}")

    def _validate_agent(self, agent: Agent, name: str) -> None:
        """
        驗證 Agent 實例

        Args:
            agent: Agent 實例
            name: Sub-agent 名稱

        Raises:
            SubAgentValidationError: 驗證失敗
        """
        # 檢查是否為 Agent 類型（支援 Mock 物件）
        try:
            is_agent = isinstance(agent, Agent)
        except TypeError:
            # 在測試環境中 Agent 可能被 mock，使用鴨子類型檢查
            is_agent = hasattr(agent, "name") and hasattr(agent, "instructions")

        if not is_agent:
            raise SubAgentValidationError(f"Invalid agent type for '{name}'")

        if not agent.name:
            raise SubAgentValidationError(f"Agent '{name}' missing name")

        if not agent.instructions:
            raise SubAgentValidationError(f"Agent '{name}' missing instructions")

        logger.debug(f"Agent '{name}' validation passed")

    def get_agent(self, name: str) -> Agent | None:
        """
        取得已載入的 Sub-agent

        Args:
            name: Sub-agent 名稱

        Returns:
            Agent 實例或 None
        """
        return self.loaded_agents.get(name)

    def get_all_agents(self) -> dict[str, Agent]:
        """取得所有已載入的 Sub-agents"""
        return self.loaded_agents.copy()

    def clear(self) -> None:
        """清除已載入的 Sub-agents"""
        self.loaded_agents.clear()
        logger.info("Cleared all loaded sub-agents")

    def __repr__(self) -> str:
        return (
            f"<SubAgentLoader "
            f"discovered={len(self.discovered_configs)}, "
            f"loaded={len(self.loaded_agents)}>"
        )


# ==========================================
# 便利函數
# ==========================================


def create_subagent_loader(tools_package: str = "src.agents.tools") -> SubAgentLoader:
    """
    創建並初始化 SubAgentLoader

    Args:
        tools_package: tools 套件路徑

    Returns:
        SubAgentLoader 實例
    """
    loader = SubAgentLoader(tools_package)
    loader.discover_subagents()
    return loader


async def load_subagents_for_agent(
    preferences: dict[str, Any],
    model: str = "gpt-4o-mini",
    tools_package: str = "src.agents.tools",
) -> list[Agent]:
    """
    為 Agent 載入 Sub-agents 的便利函數

    Args:
        preferences: 投資偏好字典
        model: AI 模型
        tools_package: tools 套件路徑

    Returns:
        Sub-agent 列表
    """
    loader = create_subagent_loader(tools_package)
    enabled_configs = loader.filter_enabled_subagents(preferences)
    return loader.load_subagents(enabled_configs, model=model)
