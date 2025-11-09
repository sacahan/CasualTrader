"""
Agents API Router

提供 Agent 的 CRUD 操作 API。
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from common.enums import AgentMode
from common.logger import logger
from service.agents_service import (
    AgentConfigurationError,
    AgentDatabaseError,
    AgentNotFoundError,
    AgentsService,
)
from api.config import get_db_session
from schemas.agent import CreateAgentRequest, UpdateAgentRequest

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ==========================================
# Dependencies
# ==========================================


def get_agents_service(db_session: AsyncSession = Depends(get_db_session)) -> AgentsService:
    """
    獲取 AgentsService 實例

    Args:
        db_session: SQLAlchemy 異步 session

    Returns:
        AgentsService 實例
    """
    return AgentsService(db_session)


# ==========================================
# API Endpoints
# ==========================================


@router.get(
    "",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="列出所有 Agents",
    description="獲取系統中所有 Agent 的列表",
)
async def list_agents(
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    列出所有 Agents

    Returns:
        Agent 列表

    Raises:
        500: 查詢失敗
    """
    try:
        logger.info("Listing all agents")

        # 獲取所有活躍的 agents
        agents = await agents_service.list_agents()
        logger.debug(f"Queried agents from database: {len(agents)} agents found")

        # 轉換為字典格式
        result = []
        for agent in agents:
            try:
                # 解析 investment_preferences JSON 字符串為列表
                investment_prefs = []
                if agent.investment_preferences:
                    try:
                        investment_prefs = json.loads(agent.investment_preferences)
                    except (json.JSONDecodeError, TypeError) as json_err:
                        logger.warning(
                            f"Failed to parse investment_preferences for agent {agent.id}: {json_err}",
                            extra={"investment_prefs_raw": agent.investment_preferences},
                        )
                        investment_prefs = []

                agent_dict = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "ai_model": agent.ai_model,
                    "status": agent.status.value
                    if hasattr(agent.status, "value")
                    else agent.status,
                    "current_mode": (
                        agent.current_mode.value
                        if hasattr(agent.current_mode, "value")
                        else agent.current_mode
                    ),
                    "initial_funds": float(agent.initial_funds),
                    "current_funds": float(agent.current_funds),
                    "max_position_size": float(agent.max_position_size)
                    if agent.max_position_size
                    else None,
                    "color_theme": agent.color_theme,
                    "investment_preferences": investment_prefs,
                    "created_at": agent.created_at.isoformat() if agent.created_at else None,
                    "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                    "last_active_at": agent.last_active_at.isoformat()
                    if agent.last_active_at
                    else None,
                }
                result.append(agent_dict)
            except AttributeError as attr_err:
                # Catch detached instance or missing attribute errors
                logger.error(
                    f"Error accessing agent properties for agent ID {getattr(agent, 'id', 'UNKNOWN')}: {attr_err}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing agent data: {str(attr_err)}",
                ) from attr_err
            except Exception as agent_err:
                logger.error(
                    f"Unexpected error processing agent {getattr(agent, 'id', 'UNKNOWN')}: {agent_err}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing agent data: {str(agent_err)}",
                ) from agent_err

        logger.info(f"Successfully formatted {len(result)} agents for response")
        return result

    except AgentDatabaseError as e:
        logger.error(f"Database error while listing agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    except HTTPException:
        # Re-raise HTTPException as-is
        raise

    except Exception as e:
        logger.error(f"Unexpected error while listing agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}",
        ) from e


@router.get(
    "/{agent_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得單一 Agent",
    description="根據 ID 獲取特定 Agent 的詳細資訊",
)
async def get_agent(
    agent_id: str,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    取得單一 Agent 詳情

    Args:
        agent_id: Agent ID
        agents_service: AgentsService 實例

    Returns:
        Agent 詳細資訊

    Raises:
        404: Agent 不存在
        500: 查詢失敗
    """
    try:
        logger.info(f"Getting agent: {agent_id}")

        # 獲取 agent 配置
        agent = await agents_service.get_agent_config(agent_id)

        # 獲取持股資訊
        holdings = await agents_service.get_agent_holdings(agent_id)

        # 解析 investment_preferences JSON 字符串為列表
        investment_prefs = []
        if agent.investment_preferences:
            try:
                investment_prefs = json.loads(agent.investment_preferences)
            except (json.JSONDecodeError, TypeError):
                investment_prefs = []

        # 組裝回應
        agent_dict = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "ai_model": agent.ai_model,
            "status": agent.status.value if hasattr(agent.status, "value") else agent.status,
            "current_mode": (
                agent.current_mode.value
                if hasattr(agent.current_mode, "value")
                else agent.current_mode
            ),
            "initial_funds": float(agent.initial_funds) if agent.initial_funds else None,
            "current_funds": float(agent.current_funds) if agent.current_funds else None,
            "max_position_size": float(agent.max_position_size)
            if agent.max_position_size
            else None,
            "color_theme": agent.color_theme,
            "investment_preferences": investment_prefs,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "last_active_at": agent.last_active_at.isoformat() if agent.last_active_at else None,
            "holdings": [
                {
                    "ticker": holding.ticker,
                    "company_name": holding.company_name,
                    "quantity": holding.quantity,
                    "average_cost": float(holding.average_cost),
                    "total_cost": float(holding.total_cost),
                    # Note: current_price and unrealized_pnl are not stored in DB
                    # They should be calculated by frontend or enriched separately
                }
                for holding in holdings
            ],
        }

        return agent_dict

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="創建新 Agent",
    description="創建一個新的交易 Agent",
)
async def create_agent(
    request: CreateAgentRequest,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    創建新 Agent

    Args:
        request: 創建請求
        agents_service: AgentsService 實例

    Returns:
        新創建的 Agent 資訊

    Raises:
        400: 請求資料無效
        500: 創建失敗
    """
    try:
        logger.info(f"Creating new agent: {request.name}")

        # 驗證 AI 模型是否存在
        model_config = await agents_service.get_ai_model_config(request.ai_model)
        if not model_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"AI model '{request.ai_model}' not found or not enabled",
            )

        # 創建 agent
        agent = await agents_service.create_agent(
            name=request.name,
            description=request.description,
            ai_model=request.ai_model,
            initial_funds=request.initial_funds,
            max_position_size=request.max_position_size,
            color_theme=request.color_theme,
            investment_preferences=request.investment_preferences,
        )

        # 提交資料庫變更
        await agents_service.session.commit()

        logger.success(f"Agent created successfully: {agent.id}")

        # 解析 investment_preferences JSON 字符串為列表
        investment_prefs = []
        if agent.investment_preferences:
            try:
                investment_prefs = json.loads(agent.investment_preferences)
            except (json.JSONDecodeError, TypeError):
                investment_prefs = []

        # 返回創建的 agent 資訊
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "ai_model": agent.ai_model,
            "status": agent.status.value if hasattr(agent.status, "value") else agent.status,
            "current_mode": (
                agent.current_mode.value
                if hasattr(agent.current_mode, "value")
                else agent.current_mode
            ),
            "initial_funds": float(agent.initial_funds),
            "max_position_size": float(agent.max_position_size)
            if agent.max_position_size
            else None,
            "color_theme": agent.color_theme,
            "investment_preferences": investment_prefs,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
        }

    except HTTPException:
        raise

    except AgentConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        await agents_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}",
        ) from e


@router.put(
    "/{agent_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="更新 Agent",
    description="更新現有 Agent 的配置",
)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    更新 Agent 配置

    Args:
        agent_id: Agent ID
        request: 更新請求
        agents_service: AgentsService 實例

    Returns:
        更新後的 Agent 資訊

    Raises:
        404: Agent 不存在
        400: 請求資料無效
        500: 更新失敗
    """
    try:
        logger.info(f"Updating agent: {agent_id}")

        # 檢查 agent 是否存在
        agent = await agents_service.get_agent_config(agent_id)

        # 準備更新資料
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.color_theme is not None:
            update_data["color_theme"] = request.color_theme
        if request.ai_model is not None:
            # 驗證新模型是否存在
            model_config = await agents_service.get_ai_model_config(request.ai_model)
            if not model_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"AI model '{request.ai_model}' not found or not enabled",
                )
            update_data["ai_model"] = request.ai_model
        if request.max_position_size is not None:
            update_data["max_position_size"] = request.max_position_size
        if request.investment_preferences is not None:
            # 序列化投資偏好為 JSON
            preferences_json = json.dumps(request.investment_preferences, ensure_ascii=False)
            update_data["investment_preferences"] = preferences_json

        # 更新 agent
        for key, value in update_data.items():
            setattr(agent, key, value)

        # 提交變更
        await agents_service.session.commit()
        await agents_service.session.refresh(agent)

        logger.success(f"Agent updated successfully: {agent_id}")

        # 解析 investment_preferences JSON 字符串為列表
        investment_prefs = []
        if agent.investment_preferences:
            try:
                investment_prefs = json.loads(agent.investment_preferences)
            except (json.JSONDecodeError, TypeError):
                investment_prefs = []

        # 返回更新後的資訊
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "ai_model": agent.ai_model,
            "status": agent.status.value if hasattr(agent.status, "value") else agent.status,
            "current_mode": (
                agent.current_mode.value
                if hasattr(agent.current_mode, "value")
                else agent.current_mode
            ),
            "color_theme": agent.color_theme,
            "max_position_size": float(agent.max_position_size)
            if agent.max_position_size
            else None,
            "investment_preferences": investment_prefs,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
        }

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to update agent {agent_id}: {e}")
        await agents_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除 Agent",
    description="刪除指定的 Agent",
)
async def delete_agent(
    agent_id: str,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    刪除 Agent

    Args:
        agent_id: Agent ID
        agents_service: AgentsService 實例

    Raises:
        404: Agent 不存在
        500: 刪除失敗
    """
    try:
        logger.info(f"Deleting agent: {agent_id}")

        # 檢查 agent 是否存在
        agent = await agents_service.get_agent_config(agent_id)

        # 刪除 agent
        await agents_service.session.delete(agent)
        await agents_service.session.commit()

        logger.success(f"Agent deleted successfully: {agent_id}")

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {e}")
        await agents_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/{agent_id}/mode",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="切換 Agent 模式",
    description="切換 Agent 的交易模式",
)
async def switch_agent_mode(
    agent_id: str,
    mode: str,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    切換 Agent 模式

    Args:
        agent_id: Agent ID
        mode: 新模式 (TRADING/REBALANCING)
        agents_service: AgentsService 實例

    Returns:
        更新後的狀態

    Raises:
        404: Agent 不存在
        400: 無效的模式
        500: 切換失敗
    """
    try:
        logger.info(f"Switching agent {agent_id} mode to {mode}")

        # 驗證模式
        try:
            agent_mode = AgentMode[mode.upper()]
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mode: {mode}. Valid modes: {[m.name for m in AgentMode]}",
            ) from e

        # 更新模式
        await agents_service.update_agent_status(
            agent_id=agent_id,
            status=None,  # 不改變狀態
            mode=agent_mode,
        )

        await agents_service.session.commit()

        logger.success(f"Agent mode switched successfully: {agent_id} -> {mode}")

        return {
            "success": True,
            "agent_id": agent_id,
            "mode": mode,
            "message": f"Agent mode switched to {mode}",
        }

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to switch mode for agent {agent_id}: {e}")
        await agents_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/{agent_id}/reset",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="重置 Agent",
    description="重置 Agent (清除投資組合和交易歷史)",
)
async def reset_agent(
    agent_id: str,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    重置 Agent

    清除 Agent 的所有持股和交易歷史，資金重置為初始值

    Args:
        agent_id: Agent ID
        agents_service: AgentsService 實例

    Returns:
        重置結果

    Raises:
        404: Agent 不存在
        500: 重置失敗
    """
    try:
        logger.info(f"Resetting agent: {agent_id}")

        # 獲取 agent 配置
        agent = await agents_service.get_agent_config(agent_id)

        # 清除持股
        holdings = await agents_service.get_agent_holdings(agent_id)
        for holding in holdings:
            await agents_service.session.delete(holding)

        # 重置資金
        agent.current_funds = agent.initial_funds

        # 提交變更
        await agents_service.session.commit()

        logger.success(f"Agent reset successfully: {agent_id}")

        return {
            "success": True,
            "agent_id": agent_id,
            "message": "Agent reset successfully",
            "initial_funds": float(agent.initial_funds),
            "current_funds": float(agent.current_funds),
        }

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to reset agent {agent_id}: {e}")
        await agents_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
