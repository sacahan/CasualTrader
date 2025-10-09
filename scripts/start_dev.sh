#!/bin/zsh
# CasualTrader Development Environment Starter
# 同時啟動前後端服務

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting CasualTrader Development Environment..."

# 啟動後端
echo "🐍 Starting Backend API..."
cd "$PROJECT_ROOT/backend"
uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 未來啟動前端 (Phase 4)
# echo "🎨 Starting Frontend..."
# cd "$PROJECT_ROOT/frontend"
# npm run dev &
# FRONTEND_PID=$!

echo ""
echo "✅ Backend running at http://localhost:8000"
echo "✅ API Docs at http://localhost:8000/docs"
# echo "✅ Frontend running at http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

# 捕獲中斷信號
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID 2>/dev/null; exit 0" INT TERM

# 等待後端進程
wait $BACKEND_PID
