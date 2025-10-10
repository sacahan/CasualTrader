"""
AI 模型管理 API 路由
提供 AI 模型的查詢和管理功能
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.agents.integrations.database_service import (
    AgentDatabaseService,
    DatabaseConfig,
)

# ==========================================
# Pydantic Models
# ==========================================


class AIModelResponse(BaseModel):
    """AI 模型回應模型"""

    model_key: str = Field(..., description="模型唯一識別碼")
    display_name: str = Field(..., description="模型顯示名稱")
    provider: str = Field(..., description="模型提供商")
    group_name: str = Field(..., description="模型分組名稱")
    model_type: str = Field(..., description="模型類型 (openai/litellm)")
    litellm_prefix: str | None = Field(None, description="LiteLLM 前綴")
    full_model_name: str = Field(..., description="完整模型名稱")
    max_tokens: int | None = Field(None, description="最大 token 數")
    cost_per_1k_tokens: float | None = Field(None, description="每 1K tokens 成本")
    description: str | None = Field(None, description="模型描述")
    display_order: int | None = Field(None, description="顯示順序")


class AIModelListResponse(BaseModel):
    """AI 模型列表回應"""

    total: int = Field(..., description="模型總數")
    models: list[AIModelResponse] = Field(..., description="模型列表")


class AIModelsGroupedResponse(BaseModel):
    """按 group 分組的 AI 模型回應"""

    groups: dict[str, list[AIModelResponse]] = Field(..., description="分組的模型列表")


# ==========================================
# Dependencies
# ==========================================


async def get_db_service() -> AgentDatabaseService:
    """獲取資料庫服務依賴"""
    db_service = AgentDatabaseService(DatabaseConfig())
    await db_service.initialize()
    try:
        yield db_service
    finally:
        await db_service.close()


# ==========================================
# Router
# ==========================================

router = APIRouter(
    prefix="/models",
    tags=["AI Models"],
    responses={
        404: {"description": "Model not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get("/available", response_model=AIModelListResponse, summary="獲取可用的 AI 模型列表")
async def list_available_models(
    db_service: AgentDatabaseService = Depends(get_db_service),
) -> dict[str, Any]:
    """
    獲取所有可用(已啟用)的 AI 模型列表

    返回:
    - 按照 display_order 排序的模型列表
    - 包含模型的完整配置資訊
    """
    try:
        models = await db_service.list_ai_models(enabled_only=True)

        return {
            "total": len(models),
            "models": models,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


@router.get(
    "/available/grouped",
    response_model=AIModelsGroupedResponse,
    summary="獲取按分組的 AI 模型列表",
)
async def list_available_models_grouped(
    db_service: AgentDatabaseService = Depends(get_db_service),
) -> dict[str, Any]:
    """
    獲取按 group_name 分組的 AI 模型列表

    返回:
    - 按照 group_name 分組的模型字典
    - 每個 group 內按 display_order 排序
    - 只返回已啟用的模型
    """
    try:
        models = await db_service.list_ai_models(enabled_only=True)

        # 按 group_name 分組
        grouped_models: dict[str, list[dict[str, Any]]] = {}
        for model in models:
            group = model["group_name"]
            if group not in grouped_models:
                grouped_models[group] = []
            grouped_models[group].append(model)

        return {"groups": grouped_models}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch grouped models: {str(e)}")


@router.get("/{model_key}", response_model=AIModelResponse, summary="獲取特定 AI 模型資訊")
async def get_model_by_key(
    model_key: str,
    db_service: AgentDatabaseService = Depends(get_db_service),
) -> dict[str, Any]:
    """
    根據 model_key 獲取特定模型的詳細資訊

    參數:
    - model_key: 模型唯一識別碼 (例如: "gpt-4o", "claude-sonnet-4.5")

    返回:
    - 模型的完整配置資訊
    """
    try:
        model_config = await db_service.get_ai_model_config(model_key)

        if not model_config:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_key}' not found or not enabled",
            )

        return model_config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch model: {str(e)}")


@router.get("/", response_model=AIModelListResponse, summary="獲取所有 AI 模型列表(包含禁用)")
async def list_all_models(
    include_disabled: bool = False,
    db_service: AgentDatabaseService = Depends(get_db_service),
) -> dict[str, Any]:
    """
    獲取所有 AI 模型列表

    參數:
    - include_disabled: 是否包含已禁用的模型 (默認: False)

    返回:
    - 所有模型的列表,按照 display_order 排序
    """
    try:
        models = await db_service.list_ai_models(enabled_only=not include_disabled)

        return {
            "total": len(models),
            "models": models,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")
