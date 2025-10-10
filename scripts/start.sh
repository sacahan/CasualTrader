#!/bin/zsh
# CasualTrader Unified Starter Script
# 同時啟動前端和後端服務

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Parse command-line options
FRONTEND_ONLY=false
BACKEND_ONLY=false

usage() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  -f, --frontend    Only start frontend"
  echo "  -b, --backend     Only start backend"
  echo "  -h, --help        Show this help message"
  echo ""
  echo "Without options, starts both frontend and backend services."
  exit 0
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -f | --frontend)
      FRONTEND_ONLY=true
      shift
      ;;
    -b | --backend)
      BACKEND_ONLY=true
      shift
      ;;
    -h | --help)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

# If both flags are set or none, start both services
if [[ "$FRONTEND_ONLY" == true && "$BACKEND_ONLY" == true ]] ||
  [[ "$FRONTEND_ONLY" == false && "$BACKEND_ONLY" == false ]]; then
  FRONTEND_ONLY=false
  BACKEND_ONLY=false
fi

echo "🚀 Starting CasualTrader Development Environment..."

# Start Backend
if [[ "$FRONTEND_ONLY" == false ]]; then
  echo ""
  echo "🐍 Starting Backend API..."
  echo "📁 Backend directory: $BACKEND_DIR"

  cd "$BACKEND_DIR"

  # Check if pyproject.toml exists
  if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found in backend/"
    exit 1
  fi

  # Sync dependencies
  echo "📦 Syncing dependencies..."
  uv sync

  # Start backend server in background
  echo ""
  echo "🌐 Backend API will be available at:"
  echo "   - API: http://localhost:8000"
  echo "   - Docs: http://localhost:8000/api/docs"
  echo "   - ReDoc: http://localhost:8000/api/redoc"
  echo "   - Health: http://localhost:8000/api/health"
  echo "   - WebSocket: ws://localhost:8000/ws"

  uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload &
  BACKEND_PID=$!
fi

# Start Frontend
if [[ "$BACKEND_ONLY" == false ]]; then
  echo ""
  echo "🎨 Starting Frontend..."
  echo "📁 Frontend directory: $FRONTEND_DIR"

  cd "$FRONTEND_DIR"

  # Check if package.json exists
  if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in frontend/"
    exit 1
  fi

  # Install dependencies if node_modules doesn't exist
  if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
  fi

  echo ""
  echo "🌐 Frontend will be available at: http://localhost:5173"

  npm run dev &
  FRONTEND_PID=$!
fi

echo ""
echo "✅ All services started successfully!"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap interrupt signal to clean up background processes
cleanup() {
  echo ""
  echo "🛑 Stopping services..."

  if [[ -n "$BACKEND_PID" ]]; then
    kill $BACKEND_PID 2>/dev/null || true
    echo "✓ Backend stopped"
  fi

  if [[ -n "$FRONTEND_PID" ]]; then
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✓ Frontend stopped"
  fi

  exit 0
}

trap cleanup INT TERM

# Wait for all background processes
if [[ -n "$BACKEND_PID" ]] && [[ -n "$FRONTEND_PID" ]]; then
  wait $BACKEND_PID $FRONTEND_PID
elif [[ -n "$BACKEND_PID" ]]; then
  wait $BACKEND_PID
elif [[ -n "$FRONTEND_PID" ]]; then
  wait $FRONTEND_PID
fi
