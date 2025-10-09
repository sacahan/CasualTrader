#!/bin/zsh
# CasualTrader Test Runner
# 執行所有測試（後端）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running CasualTrader Tests..."

# 後端測試
echo ""
echo "📦 Backend Tests"
echo "=================="
cd "$PROJECT_ROOT/backend"
uv run pytest tests/ -v --cov=src --cov-report=term-missing
BACKEND_EXIT=$?

# 前端測試 (Phase 4+)
# echo ""
# echo "🎨 Frontend Tests"
# echo "=================="
# cd "$PROJECT_ROOT/frontend"
# npm test
# FRONTEND_EXIT=$?

# 整合測試 (Phase 4+ - 前後端整合)
# echo ""
# echo "🔗 Integration Tests"
# echo "=================="
# if [ -d "$PROJECT_ROOT/tests/integration" ]; then
#     cd "$PROJECT_ROOT"
#     uv run pytest tests/integration/ -v
#     INTEGRATION_EXIT=$?
# fi

# 總結
echo ""
echo "📊 Test Summary"
echo "=================="
if [ $BACKEND_EXIT -eq 0 ]; then
	echo "✅ All tests passed!"
	exit 0
else
	echo "❌ Some tests failed"
	exit 1
fi
