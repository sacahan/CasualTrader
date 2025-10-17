"""
Agent 循環執行器

管理 trading agent 的後台循環執行任務。
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..common.enums import AgentMode
from .trading_service import TradingService

if TYPE_CHECKING:
    from ..api.config import Settings
    from ..api.holiday_client import TaiwanHolidayAPIClient
    from ..api.websocket import ConnectionManager


# ==========================================
# 自定義異常
# ==========================================


class AgentExecutorError(Exception):
    """Agent 執行器異常基類"""

    pass


class AlreadyRunningError(AgentExecutorError):
    """Agent 已經在運行中"""

    pass


class NotRunningError(AgentExecutorError):
    """Agent 未在運行中"""

    pass


# ==========================================
# Agent 執行器
# ==========================================


class AgentExecutor:
    """
    Agent 循環執行器

    管理 agent 的後台任務，執行固定三階段循環：
    OBSERVATION → TRADING → REBALANCING
    """

    def __init__(
        self,
        session_maker: async_sessionmaker,
        websocket_manager: ConnectionManager,
        settings: Settings,
    ):
        """
        初始化 Agent 執行器

        Args:
            session_maker: SQLAlchemy async session maker
            websocket_manager: WebSocket 連接管理器
            settings: 應用配置
        """
        self._session_maker = session_maker
        self._websocket_manager = websocket_manager
        self._settings = settings

        # 任務管理
        self._tasks: dict[str, asyncio.Task] = {}
        self._running_agents: set[str] = set()

        # 運行時狀態追蹤
        self._agent_status: dict[str, dict] = {}
        # 格式: {
        #   agent_id: {
        #     "interval_minutes": 60,
        #     "current_mode": AgentMode.OBSERVATION,
        #     "last_cycle_at": datetime,
        #     "cycle_count": 5
        #   }
        # }

        # 節假日客戶端（延遲初始化避免循環導入）
        self._holiday_client: TaiwanHolidayAPIClient | None = None

        logger.info("AgentExecutor 初始化完成")

    async def start(self, agent_id: str, interval_minutes: int = 60) -> None:
        """
        啟動 agent 循環執行

        Args:
            agent_id: Agent ID
            interval_minutes: 循環間隔（分鐘）

        Raises:
            AlreadyRunningError: Agent 已在運行中
        """
        if agent_id in self._running_agents:
            raise AlreadyRunningError(f"Agent {agent_id} is already running")

        logger.info(f"啟動 agent 循環執行: {agent_id}, 間隔 {interval_minutes} 分鐘")

        # 初始化狀態
        self._agent_status[agent_id] = {
            "interval_minutes": interval_minutes,
            "current_mode": None,
            "last_cycle_at": None,
            "cycle_count": 0,
        }

        # 創建並啟動後台任務
        task = asyncio.create_task(self._run_loop(agent_id, interval_minutes))
        self._tasks[agent_id] = task
        self._running_agents.add(agent_id)

        # 廣播啟動事件
        await self._broadcast_event(
            "agent_started",
            {
                "agent_id": agent_id,
                "interval_minutes": interval_minutes,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def stop(self, agent_id: str) -> None:
        """
        停止 agent 循環執行

        Args:
            agent_id: Agent ID

        Raises:
            NotRunningError: Agent 未在運行中
        """
        if agent_id not in self._running_agents:
            raise NotRunningError(f"Agent {agent_id} is not running")

        logger.info(f"停止 agent 循環執行: {agent_id}")

        # 移除運行標記（循環會檢查此標記並自動退出）
        self._running_agents.discard(agent_id)

        # 取消任務
        if agent_id in self._tasks:
            task = self._tasks[agent_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._tasks[agent_id]

        # 清理狀態
        if agent_id in self._agent_status:
            self._agent_status[agent_id]["current_mode"] = None

        # 廣播停止事件
        await self._broadcast_event(
            "agent_stopped",
            {
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def stop_all(self) -> None:
        """停止所有運行中的 agent"""
        logger.info(f"停止所有運行中的 agent（共 {len(self._running_agents)} 個）")

        # 複製一份列表，避免在迭代時修改集合
        agents_to_stop = list(self._running_agents)

        for agent_id in agents_to_stop:
            try:
                await self.stop(agent_id)
            except Exception as e:
                logger.error(f"停止 agent {agent_id} 時發生錯誤: {e}")

        # 關閉節假日客戶端
        await self._holiday_client.close()

    def get_status(self, agent_id: str) -> dict:
        """
        獲取 agent 運行時狀態

        Args:
            agent_id: Agent ID

        Returns:
            運行時狀態字典
        """
        is_running = agent_id in self._running_agents

        if not is_running:
            return {
                "is_running": False,
                "current_mode": None,
                "last_cycle_at": None,
                "cycle_count": 0,
                "interval_minutes": None,
            }

        status = self._agent_status.get(agent_id, {})
        return {
            "is_running": True,
            "current_mode": status.get("current_mode"),
            "last_cycle_at": status.get("last_cycle_at"),
            "cycle_count": status.get("cycle_count", 0),
            "interval_minutes": status.get("interval_minutes"),
        }

    async def _run_loop(self, agent_id: str, interval_minutes: int) -> None:
        """
        循環執行邏輯

        Args:
            agent_id: Agent ID
            interval_minutes: 循環間隔（分鐘）
        """
        logger.info(f"Agent {agent_id} 進入循環執行模式")

        while agent_id in self._running_agents:
            try:
                # 檢查是否為交易日
                if not await self._is_market_open():
                    logger.debug(f"市場休市，跳過循環 - Agent {agent_id}")
                    # 廣播休市事件
                    await self._broadcast_event(
                        "market_closed_skip",
                        {
                            "agent_id": agent_id,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                    # 休市時每分鐘檢查一次
                    await asyncio.sleep(60)
                    continue

                # 執行完整循環
                await self._execute_cycle(agent_id)

                # 更新最後循環時間
                if agent_id in self._agent_status:
                    self._agent_status[agent_id]["last_cycle_at"] = datetime.now().isoformat()
                    self._agent_status[agent_id]["cycle_count"] += 1

                # 等待下次循環
                await asyncio.sleep(interval_minutes * 60)

            except asyncio.CancelledError:
                logger.info(f"Agent {agent_id} 循環被取消")
                break

            except Exception as e:
                logger.error(f"Agent {agent_id} 循環執行錯誤: {e}", exc_info=True)
                # 發生錯誤時等待一段時間後繼續
                await asyncio.sleep(60)

        logger.info(f"Agent {agent_id} 退出循環執行模式")

    async def _execute_cycle(self, agent_id: str) -> None:
        """
        執行一次完整的三階段循環

        Args:
            agent_id: Agent ID
        """
        logger.info(f"開始執行循環 - Agent {agent_id}")

        # 廣播循環開始事件
        await self._broadcast_event(
            "cycle_started",
            {
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # 固定執行三個階段
        modes = [AgentMode.OBSERVATION, AgentMode.TRADING, AgentMode.REBALANCING]

        for mode in modes:
            try:
                # 更新當前階段
                if agent_id in self._agent_status:
                    self._agent_status[agent_id]["current_mode"] = mode.value

                # 廣播階段開始事件
                await self._broadcast_event(
                    "phase_started",
                    {
                        "agent_id": agent_id,
                        "mode": mode.value,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                logger.info(f"執行 {mode.value} 階段 - Agent {agent_id}")

                # 創建 trading service 並執行任務
                async with self._session_maker() as db_session:
                    trading_service = TradingService(db_session)
                    await trading_service.execute_agent_task(
                        agent_id=agent_id,
                        mode=mode,
                        context=None,
                        max_turns=None,
                    )
                    await db_session.commit()

                # 廣播階段完成事件
                await self._broadcast_event(
                    "phase_completed",
                    {
                        "agent_id": agent_id,
                        "mode": mode.value,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            except Exception as e:
                logger.error(f"執行 {mode.value} 階段失敗 - Agent {agent_id}: {e}", exc_info=True)
                # 繼續執行下一階段，不中斷整個循環

        # 清除當前階段標記
        if agent_id in self._agent_status:
            self._agent_status[agent_id]["current_mode"] = None

        # 廣播循環完成事件
        await self._broadcast_event(
            "cycle_completed",
            {
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        logger.info(f"完成循環 - Agent {agent_id}")

    async def _is_market_open(self) -> bool:
        """
        檢查台灣股市是否開市

        Returns:
            True 如果是交易日，False 如果休市
        """
        # 測試模式：跳過開市檢查
        if self._settings.skip_market_check:
            logger.debug("測試模式：跳過開市檢查")
            return True

        try:
            # 延遲初始化節假日客戶端
            if self._holiday_client is None:
                from ..api.holiday_client import TaiwanHolidayAPIClient

                self._holiday_client = TaiwanHolidayAPIClient()

            today = datetime.now().date()
            is_trading_day = await self._holiday_client.is_trading_day(today)
            logger.debug(f"開市檢查結果: {is_trading_day} ({today})")
            return is_trading_day

        except Exception as e:
            logger.error(f"檢查開市時間失敗: {e}")
            # 發生錯誤時保守處理，假設是交易日
            return True

    async def _broadcast_event(self, event_type: str, data: dict) -> None:
        """
        通過 WebSocket 廣播事件

        Args:
            event_type: 事件類型
            data: 事件數據
        """
        try:
            message = {"type": event_type, **data}
            await self._websocket_manager.broadcast(message)
        except Exception as e:
            logger.error(f"廣播事件失敗 ({event_type}): {e}")
