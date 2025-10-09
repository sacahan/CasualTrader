#!/bin/zsh
# CasualTrader Backend API Starter
# 切換到 backend 目錄並啟動 API 服務

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🚀 Starting CasualTrader Backend API..."
echo "📁 Backend directory: $BACKEND_DIR"

cd "$BACKEND_DIR"

# 檢查 pyproject.toml 是否存在
if [ ! -f "pyproject.toml" ]; then
	echo "❌ Error: pyproject.toml not found in backend/"
	exit 1
fi

# 同步依賴
echo "📦 Syncing dependencies..."
uv sync

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
