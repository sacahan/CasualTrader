#!/bin/zsh
# CasualTrader Backend Setup Script
# 配置後端開發環境

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔧 Setting up CasualTrader Backend..."

cd "$BACKEND_DIR"

# 檢查 UV 是否安裝
if ! command -v uv &>/dev/null; then
	echo "❌ UV is not installed. Please install it first:"
	echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
	exit 1
fi

# 同步依賴
echo "📦 Installing dependencies..."
uv sync

# 創建環境變數檔案
if [ ! -f ".env" ]; then
	echo "📝 Creating .env file from template..."
	cp .env.example .env
	echo "⚠️  Please update .env with your API keys"
fi

# 初始化資料庫（如果不存在）
if [ ! -f "casualtrader.db" ]; then
	echo "🗄️  Initializing database..."
	uv run python -c "
from src.database.migrations import init_database
import asyncio
asyncio.run(init_database())
print('✅ Database initialized')
"
else
	echo "✅ Database already exists"
fi

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your API keys"
echo "2. Run: ./scripts/start_api.sh"
echo "3. Visit: http://localhost:8000/docs"
