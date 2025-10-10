"""
AI Model 配置種子資料
用於初始化可用的 AI 模型列表
"""

from decimal import Decimal

from .models import ModelType

# AI 模型種子資料
SEED_AI_MODELS = [
    # ==========================================
    # OpenAI Models
    # ==========================================
    {
        "model_key": "gpt-5-mini",
        "display_name": "GPT-5 Mini",
        "provider": "OpenAI",
        "group_name": "OpenAI",
        "model_type": ModelType.OPENAI,
        "litellm_prefix": None,
        "full_model_name": "gpt-5-mini",
        "is_enabled": True,
        "requires_api_key": True,
        "api_key_env_var": "OPENAI_API_KEY",
        "api_base_url": None,
        "max_tokens": 128000,
        "cost_per_1k_tokens": Decimal("0.01"),
        "display_order": 1,
        "description": "Most capable OpenAI model for complex tasks",
    },
    {
        "model_key": "gpt-4o-mini",
        "display_name": "GPT-4o Mini",
        "provider": "OpenAI",
        "group_name": "OpenAI",
        "model_type": ModelType.OPENAI,
        "litellm_prefix": None,
        "full_model_name": "gpt-4o-mini",
        "is_enabled": True,
        "requires_api_key": True,
        "api_key_env_var": "OPENAI_API_KEY",
        "api_base_url": None,
        "max_tokens": 128000,
        "cost_per_1k_tokens": Decimal("0.003"),
        "display_order": 2,
        "description": "Fast and affordable OpenAI model",
    },
    {
        "model_key": "gpt-4.1-mini",
        "display_name": "GPT-4.1 Mini",
        "provider": "OpenAI",
        "group_name": "OpenAI",
        "model_type": ModelType.OPENAI,
        "litellm_prefix": None,
        "full_model_name": "gpt-4.1-mini",
        "is_enabled": True,
        "requires_api_key": True,
        "api_key_env_var": "OPENAI_API_KEY",
        "api_base_url": None,
        "max_tokens": 128000,
        "cost_per_1k_tokens": Decimal("0.008"),
        "display_order": 3,
        "description": "Fast and affordable OpenAI model",
    },
    # ==========================================
    # Google Gemini Models (via LiteLLM)
    # ==========================================
    {
        "model_key": "gemini-2.5-pro",
        "display_name": "Gemini 2.5 Pro",
        "provider": "Google",
        "group_name": "Google Gemini",
        "model_type": ModelType.LITELLM,
        "litellm_prefix": "gemini/",
        "full_model_name": "gemini/gemini-2.5-pro-preview-05-06",
        "is_enabled": True,
        "requires_api_key": True,
        "api_key_env_var": "GEMINI_API_KEY",
        "api_base_url": None,
        "max_tokens": 1048576,
        "cost_per_1k_tokens": Decimal("0.00125"),
        "display_order": 6,
        "description": "1M token context for long document analysis",
    },
    {
        "model_key": "gemini-2.0-flash",
        "display_name": "Gemini 2.0 Flash",
        "provider": "Google",
        "group_name": "Google Gemini",
        "model_type": ModelType.LITELLM,
        "litellm_prefix": "gemini/",
        "full_model_name": "gemini/gemini-2.0-flash",
        "is_enabled": True,
        "requires_api_key": True,
        "api_key_env_var": "GEMINI_API_KEY",
        "api_base_url": None,
        "max_tokens": 1048576,
        "cost_per_1k_tokens": Decimal("0.0001"),
        "display_order": 7,
        "description": "Fast and cost-effective Gemini model",
    },
]


async def seed_ai_models(session) -> None:
    """
    初始化 AI 模型種子資料

    Args:
        session: Async SQLAlchemy session
    """
    from sqlalchemy import select

    from .models import AIModelConfig

    # 檢查是否已有資料
    result = await session.execute(select(AIModelConfig).limit(1))
    existing = result.scalar_one_or_none()

    if existing:
        print("AI models already seeded, skipping...")
        return

    # 插入種子資料
    print(f"Seeding {len(SEED_AI_MODELS)} AI models...")

    for model_data in SEED_AI_MODELS:
        model = AIModelConfig(**model_data)
        session.add(model)

    await session.commit()
    print("AI models seeded successfully!")
