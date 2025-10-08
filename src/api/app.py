"""
FastAPI Application Factory

Main application instance and configuration.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import agents, trading, websocket_router
from .websocket import websocket_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    print("🚀 CasualTrader API Server Starting...")

    # Initialize WebSocket manager
    await websocket_manager.startup()

    yield

    # Shutdown
    print("⏹️ CasualTrader API Server Shutting Down...")
    await websocket_manager.shutdown()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="CasualTrader API",
        description="AI Stock Trading Simulator Backend",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
    app.include_router(websocket_router.router, tags=["websocket"])

    # Static files (for frontend)
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount(
            "/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend"
        )

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.0.0", "service": "CasualTrader API"}

    return app
