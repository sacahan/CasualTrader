#!/usr/bin/env zsh
# CasualTrader API Server Startup Script

echo "🚀 Starting CasualTrader API Server..."
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
	echo "⚠️  Virtual environment not activated"
	echo "Activating .venv..."
	source .venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if FastAPI is installed
if ! python -c "import fastapi" 2>/dev/null; then
	echo "📦 Installing dependencies..."
	uv pip install fastapi 'uvicorn[standard]' python-multipart websockets
fi

# Start the server
echo ""
echo "🌐 Server will be available at:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - WebSocket: ws://localhost:8000/ws"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
