"""
Agent Management API Router

Endpoints for creating, managing, and controlling trading agents.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from ...agents.core.agent_manager import AgentManager
from ...agents.core.models import AgentConfig, AgentMode
from ..models import (
    AgentListResponse,
    AgentResponse,
    CreateAgentRequest,
    StartAgentRequest,
    UpdateAgentRequest,
    UpdateModeRequest,
)
from ..websocket import websocket_manager

router = APIRouter()

# Global agent manager instance
agent_manager = AgentManager()


def _map_agent_to_response(agent_data: dict[str, Any]) -> AgentResponse:
    """Map agent data to response model."""
    return AgentResponse(
        id=agent_data["id"],
        name=agent_data["name"],
        description=agent_data.get("description", ""),
        ai_model=agent_data.get("ai_model", "gpt-4o"),
        strategy_type=agent_data.get("strategy_type", "balanced"),
        strategy_prompt=agent_data.get("strategy_prompt", ""),
        color_theme=agent_data.get("color_theme", "#007bff"),
        current_mode=agent_data.get("current_mode", "TRADING"),
        status=agent_data.get("status", "idle"),
        initial_funds=agent_data.get("initial_funds", 1000000.0),
        current_funds=agent_data.get("current_funds"),
        max_turns=agent_data.get("max_turns", 50),
        risk_tolerance=agent_data.get("risk_tolerance", 0.5),
        enabled_tools=agent_data.get("enabled_tools", {}),
        investment_preferences=agent_data.get("investment_preferences", {}),
        custom_instructions=agent_data.get("custom_instructions", ""),
        created_at=agent_data.get("created_at", datetime.now()),
        updated_at=agent_data.get("updated_at", datetime.now()),
        portfolio=agent_data.get("portfolio"),
        performance=agent_data.get("performance"),
    )


@router.get("", response_model=AgentListResponse, summary="列出所有代理")
async def list_agents():
    """
    列出所有交易代理

    返回系統中所有已創建的交易代理及其狀態。
    """
    logger.info("Listing all agents")
    try:
        agents = await agent_manager.list_agents()
        agent_responses = [_map_agent_to_response(agent) for agent in agents]
        logger.info(f"Found {len(agent_responses)} agents")
        return AgentListResponse(agents=agent_responses, total=len(agent_responses))
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}",
        ) from e


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="創建代理",
)
async def create_agent(request: CreateAgentRequest):
    """
    創建新的交易代理

    根據指定的配置創建一個新的 AI 交易代理。

    - **name**: 代理名稱
    - **ai_model**: 使用的 AI 模型
    - **strategy_prompt**: 交易策略描述
    - **initial_funds**: 初始資金
    """
    logger.info(f"Creating new agent: {request.name} with model {request.ai_model.value}")
    try:
        # Convert request to AgentConfig
        logger.debug(
            f"Agent config: initial_funds={request.initial_funds}, max_turns={request.max_turns}"
        )

        # Import InvestmentPreferences from agent models
        from ...agents.core.models import (
            InvestmentPreferences as AgentInvestmentPreferences,
        )

        # Convert risk_tolerance from float to string category
        risk_category = AgentInvestmentPreferences.risk_tolerance_from_float(request.risk_tolerance)

        # Create InvestmentPreferences dataclass
        agent_investment_prefs = AgentInvestmentPreferences(
            preferred_sectors=request.investment_preferences.preferred_sectors,
            excluded_tickers=request.investment_preferences.excluded_tickers,
            max_position_size=request.investment_preferences.max_position_size
            * 100,  # Convert to percentage
            risk_tolerance=risk_category,
            strategy_type=request.strategy_type.value,
        )

        config = AgentConfig(
            name=request.name,
            description=request.description,
            model=request.ai_model.value,
            initial_funds=request.initial_funds,
            max_turns=request.max_turns,
            instructions=request.strategy_prompt,
            additional_instructions=request.custom_instructions,
            enabled_tools=request.enabled_tools.model_dump(),
            investment_preferences=agent_investment_prefs,
        )

        # Create agent
        agent_id = await agent_manager.create_agent(config=config)
        logger.success(f"Agent created successfully: {agent_id}")

        # Get created agent (now returns dict)
        agent_dict = await agent_manager.get_agent(agent_id)

        # Add color_theme to agent_dict (not stored in agent config)
        agent_dict["color_theme"] = request.color_theme

        # Broadcast creation event
        logger.debug(f"Broadcasting agent creation event for {agent_id}")
        await websocket_manager.broadcast_agent_status(
            agent_id=agent_id,
            status="created",
            details={"name": request.name, "ai_model": request.ai_model.value},
        )

        return _map_agent_to_response(agent_dict)

    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}",
        ) from e


@router.get("/{agent_id}", response_model=AgentResponse, summary="查詢代理")
async def get_agent(agent_id: str):
    """
    查詢特定代理的詳細資訊

    返回指定 ID 的交易代理的完整配置和狀態。
    """
    logger.info(f"Getting agent: {agent_id}")
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            logger.warning(f"Agent not found: {agent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )
        logger.debug(f"Agent {agent_id} status: {agent_data.get('status')}")
        return _map_agent_to_response(agent_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent: {str(e)}",
        ) from e


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, request: UpdateAgentRequest):
    """Update agent configuration."""
    try:
        # Get current agent
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Update fields
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.strategy_prompt is not None:
            update_data["strategy_prompt"] = request.strategy_prompt
        if request.color_theme is not None:
            update_data["color_theme"] = request.color_theme
        if request.risk_tolerance is not None:
            update_data["risk_tolerance"] = request.risk_tolerance
        if request.enabled_tools is not None:
            update_data["enabled_tools"] = request.enabled_tools.model_dump()
        if request.investment_preferences is not None:
            update_data["investment_preferences"] = request.investment_preferences.model_dump()
        if request.custom_instructions is not None:
            update_data["custom_instructions"] = request.custom_instructions

        # Apply updates
        await agent_manager.update_agent(agent_id, update_data)

        # Get updated agent
        updated_agent = await agent_manager.get_agent(agent_id)

        # Broadcast update event
        await websocket_manager.broadcast_agent_status(
            agent_id=agent_id,
            status="updated",
            details={"updated_fields": list(update_data.keys())},
        )

        return _map_agent_to_response(updated_agent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}",
        ) from e


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str):
    """Delete an agent."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Stop if running
        if agent_data.get("status") == "running":
            await agent_manager.stop_agent(agent_id)

        # Delete agent
        await agent_manager.delete_agent(agent_id)

        # Broadcast deletion event
        await websocket_manager.broadcast_agent_status(
            agent_id=agent_id, status="deleted", details={}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}",
        ) from e


@router.post("/{agent_id}/start", response_model=dict[str, Any])
async def start_agent(agent_id: str, request: StartAgentRequest):
    """Start an agent."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Start agent
        await agent_manager.start_agent(
            agent_id=agent_id,
            max_cycles=request.max_cycles,
            stop_loss_threshold=request.stop_on_loss_threshold,
        )

        # Broadcast start event
        await websocket_manager.broadcast_agent_status(
            agent_id=agent_id,
            status="running",
            details={
                "max_cycles": request.max_cycles,
                "execution_mode": request.execution_mode.value,
            },
        )

        return {
            "agent_id": agent_id,
            "status": "running",
            "message": "Agent started successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting agent {agent_id}: {e}")
        await websocket_manager.broadcast_error(
            agent_id=agent_id, error_message=f"Failed to start agent: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start agent: {str(e)}",
        ) from e


@router.post("/{agent_id}/stop", response_model=dict[str, Any])
async def stop_agent(agent_id: str):
    """Stop a running agent."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Stop agent
        await agent_manager.stop_agent(agent_id)

        # Broadcast stop event
        await websocket_manager.broadcast_agent_status(
            agent_id=agent_id, status="stopped", details={}
        )

        return {
            "agent_id": agent_id,
            "status": "stopped",
            "message": "Agent stopped successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop agent: {str(e)}",
        ) from e


@router.put("/{agent_id}/mode", response_model=dict[str, Any])
async def update_agent_mode(agent_id: str, request: UpdateModeRequest):
    """Update agent trading mode."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Update mode
        new_mode = AgentMode[request.mode.value]
        await agent_manager.update_agent_mode(
            agent_id=agent_id,
            new_mode=new_mode,
            reason=request.reason,
            trigger=request.trigger,
        )

        # Broadcast mode change
        await websocket_manager.broadcast_agent_status(
            agent_id=agent_id,
            status="mode_changed",
            details={
                "mode": request.mode.value,
                "reason": request.reason,
                "trigger": request.trigger,
            },
        )

        return {
            "agent_id": agent_id,
            "mode": request.mode.value,
            "message": "Agent mode updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent mode {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent mode: {str(e)}",
        ) from e


@router.post("/{agent_id}/reset", response_model=dict[str, Any])
async def reset_agent(agent_id: str):
    """Reset agent portfolio and history."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        # Stop if running
        if agent_data.get("status") == "running":
            await agent_manager.stop_agent(agent_id)

        # Reset agent
        await agent_manager.reset_agent(agent_id)

        # Broadcast reset event
        await websocket_manager.broadcast_agent_status(
            agent_id=agent_id, status="reset", details={}
        )

        return {
            "agent_id": agent_id,
            "status": "reset",
            "message": "Agent reset successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset agent: {str(e)}",
        ) from e
