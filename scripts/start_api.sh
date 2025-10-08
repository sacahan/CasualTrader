#!/usr/bin/env zsh
# CasualTrader API Server Startup Script

# Get the project root directory (parent of scripts directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

echo "🚀 Starting CasualTrader API Server..."
echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
	echo "⚠️  Virtual environment not activated"
	echo "Activating .venv..."
	source .venv/bin/activate
fi

# Set PYTHONPATH to project root
export PYTHONPATH="$PROJECT_ROOT"

# Check if FastAPI is installed
if ! python -c "import fastapi" 2>/dev/null; then
	echo "📦 Installing dependencies..."
	uv pip install fastapi 'uvicorn[standard]' python-multipart websockets
fi

# Start the server
echo ""
echo "🌐 Server will be available at:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/api/docs"
echo "   - ReDoc: http://localhost:8000/api/redoc"
echo "   - Health: http://localhost:8000/api/health"
echo "   - WebSocket: ws://localhost:8000/ws"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Use uvicorn directly with the factory pattern
uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
