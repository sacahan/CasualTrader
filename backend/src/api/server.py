"""
FastAPI Server Entry Point

Run this file to start the CasualTrader API server.
"""

import uvicorn

from src.api.app import create_app

# Create app instance for uvicorn to import
app = create_app()


def main():
    """Start the FastAPI server."""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,  # Enable auto-reload during development
    )


if __name__ == "__main__":
    main()
