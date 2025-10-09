"""
FastAPI Application Factory

Main application instance and configuration.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .config import settings
from .docs import get_openapi_tags
from .routers import agents, trading, websocket_router
from .routers.agents import agent_manager
from .websocket import websocket_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("=" * 80)
    logger.info("🚀 CasualTrader API Server Starting...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"Max Agents: {settings.max_agents}")
    logger.info(f"Database: {settings.database_url}")
    logger.info("=" * 80)

    # Initialize Agent Manager
    logger.info("Initializing Agent Manager...")
    await agent_manager.start()
    logger.success("Agent Manager initialized successfully")

    # Initialize WebSocket manager
    logger.info("Initializing WebSocket manager...")
    await websocket_manager.startup()
    logger.success("WebSocket manager initialized successfully")

    logger.success("✅ CasualTrader API Server started successfully")

    yield

    # Shutdown
    logger.info("=" * 80)
    logger.info("⏹️ CasualTrader API Server Shutting Down...")
    logger.info("Closing WebSocket connections...")
    await websocket_manager.shutdown()
    logger.info("Shutting down Agent Manager...")
    await agent_manager.shutdown()
    logger.success("✅ CasualTrader API Server shut down successfully")
    logger.info("=" * 80)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Setup logging first
    settings.setup_logging()
    logger.info("Creating FastAPI application...")

    app = FastAPI(
        title="CasualTrader API",
        description="""
# CasualTrader AI 交易模擬器 API

完整的 AI 股票交易代理管理與即時數據查詢平台。

## 功能特色

- 🤖 **多 AI 模型支援**: GPT-4, Claude, Gemini, DeepSeek 等
- 📊 **完整數據查詢**: 投資組合、交易歷史、績效分析
- ⚡ **即時通訊**: WebSocket 推送交易事件和狀態更新
- 🎯 **策略自訂**: 靈活的交易策略和風險參數配置
- 📈 **績效追蹤**: 詳細的績效指標和回測分析

## 快速開始

1. 創建交易代理: `POST /api/agents`
2. 啟動代理: `POST /api/agents/{agent_id}/start`
3. 查詢投資組合: `GET /api/trading/agents/{agent_id}/portfolio`
4. 連接 WebSocket: `ws://localhost:8000/ws`

## 技術支援

- 文件: [GitHub](https://github.com/sacahan/CasualTrader)
- 問題回報: [Issues](https://github.com/sacahan/CasualTrader/issues)
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        openapi_tags=get_openapi_tags(),
        contact={
            "name": "CasualTrader Team",
            "url": "https://github.com/sacahan/CasualTrader",
            "email": "casualtrader@example.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests."""
        logger.info(f"→ {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            logger.info(
                f"← {request.method} {request.url.path} - Status: {response.status_code}"
            )
            return response
        except Exception as e:
            logger.error(f"✗ {request.method} {request.url.path} - Error: {e!s}")
            raise

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions."""
        logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc) if settings.debug else "An error occurred",
            },
        )

    # CORS middleware
    logger.info(f"Configuring CORS with origins: {settings.cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if not settings.debug else ["*"],
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    logger.info("Registering API routers...")
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
    app.include_router(websocket_router.router, tags=["websocket"])
    logger.info("✓ All routers registered")

    # Static files (for frontend)
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        logger.info(f"Mounting frontend static files from: {frontend_dist}")
        app.mount(
            "/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend"
        )
    else:
        logger.warning(f"Frontend dist directory not found: {frontend_dist}")

    @app.get("/api/health", tags=["system"], summary="健康檢查")
    async def health_check():
        """
        健康檢查端點

        返回 API 伺服器的健康狀態和基本資訊。
        """
        logger.debug("Health check requested")
        return {
            "status": "healthy",
            "version": "1.0.0",
            "service": "CasualTrader API",
            "environment": settings.environment,
            "debug": settings.debug,
        }

    logger.success("FastAPI application created successfully")
    return app
