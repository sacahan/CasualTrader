#!/bin/zsh
# CasualTrader Unified Starter Script
# 同時啟動前端和後端服務

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Function to kill process using a specific port
kill_port() {
	local port=$1
	local pids=$(lsof -ti:$port 2>/dev/null)
	if [[ -n "$pids" ]]; then
		echo "🔄 Killing existing process on port $port..."
		echo "$pids" | xargs kill -9 2>/dev/null || true
		sleep 1
	fi
}

# Parse command-line options
FRONTEND_ONLY=false
BACKEND_ONLY=false

usage() {
	cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -f, --frontend    Only start frontend (port $FRONTEND_PORT)
  -b, --backend     Only start backend (port $BACKEND_PORT)
  -a, --all         Start both frontend and backend (default)
  -h, --help        Show this help message

Examples:
  $(basename "$0")              # Start both services
  $(basename "$0") -f           # Start frontend only
  $(basename "$0") -b           # Start backend only
  $(basename "$0") --all        # Start both services (explicit)

Without options, starts both frontend and backend services.
EOF
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
	-a | --all)
		FRONTEND_ONLY=false
		BACKEND_ONLY=false
		shift
		;;
	-h | --help)
		usage
		;;
	*)
		echo "❌ Unknown option: $1"
		echo ""
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
echo ""

# Show what will be started
if [[ "$FRONTEND_ONLY" == true ]]; then
	echo "📋 Mode: Frontend Only"
elif [[ "$BACKEND_ONLY" == true ]]; then
	echo "📋 Mode: Backend Only"
else
	echo "📋 Mode: Full Stack (Frontend + Backend)"
fi

echo ""

# Clean up any existing processes on required ports
if [[ "$FRONTEND_ONLY" == false ]]; then
	kill_port $BACKEND_PORT
fi

if [[ "$BACKEND_ONLY" == false ]]; then
	kill_port $FRONTEND_PORT
fi

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

	# Start backend server using run_server.py (handles Python path correctly)
	uv run python run_server.py &
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

	# Kill processes and their children (macOS compatible)
	if [[ -n "$BACKEND_PID" ]]; then
		# Try to kill the process group first, then the process itself
		pkill -P $BACKEND_PID 2>/dev/null || true
		kill $BACKEND_PID 2>/dev/null || true
		echo "✓ Backend stopped"
	fi

	if [[ -n "$FRONTEND_PID" ]]; then
		# Try to kill the process group first, then the process itself
		pkill -P $FRONTEND_PID 2>/dev/null || true
		kill $FRONTEND_PID 2>/dev/null || true
		echo "✓ Frontend stopped"
	fi

	# Double-check and force kill any remaining processes on ports
	sleep 1
	if [[ "$FRONTEND_ONLY" == false ]]; then
		kill_port $BACKEND_PORT 2>/dev/null || true
	fi
	if [[ "$BACKEND_ONLY" == false ]]; then
		kill_port $FRONTEND_PORT 2>/dev/null || true
	fi

	echo "✓ All services stopped and ports released"
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
