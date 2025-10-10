#!/usr/bin/env zsh

# 測試 OpenAI Tools 整合
# 使用方式: ./test_openai_integration.sh

set -e

echo "🔍 檢查環境變數..."

# 檢查 OPENAI_API_KEY
if [ -z "$OPENAI_API_KEY" ]; then
	echo "❌ 錯誤: OPENAI_API_KEY 未設定"
	echo ""
	echo "請設定環境變數:"
	echo "  export OPENAI_API_KEY='sk-your-key-here'"
	echo ""
	echo "或者在 .env 檔案中設定:"
	echo "  echo 'OPENAI_API_KEY=sk-your-key-here' >> .env"
	exit 1
fi

echo "✅ OPENAI_API_KEY 已設定"

# 確保在 backend 目錄
cd "$(dirname "$0")/.."

echo ""
echo "📦 檢查依賴..."

# 檢查是否使用 uv
if command -v uv &>/dev/null; then
	echo "✅ 使用 uv 執行測試"
	uv run tests/agents/integrations/test_openai_tools_integration.py
else
	echo "✅ 使用 python 執行測試"
	python tests/agents/integrations/test_openai_tools_integration.py
fi
