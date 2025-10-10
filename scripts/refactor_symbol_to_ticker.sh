#!/bin/bash

# Symbol → Ticker 批量重構腳本
# 使用 sed 批量替換所有檔案中的 symbol 為 ticker

set -e

echo "🔄 開始執行 Symbol → Ticker 重構..."

# 定義要處理的目錄
BACKEND_DIR="backend/src"
TEST_DIR="backend/tests"
FRONTEND_DIR="frontend/src"

# 備份資料庫
echo "📦 備份資料庫..."
if [ -f "casualtrader.db" ]; then
  cp casualtrader.db casualtrader.db.backup_$(date +%Y%m%d_%H%M%S)
  echo "✅ 資料庫已備份"
fi

# 函數: 替換檔案中的內容
replace_in_file() {
  local file=$1

  # 跳過 migrations 檔案
  if [[ "$file" == *"migrations"* ]]; then
    return
  fi

  # Python 檔案
  if [[ "$file" == *.py ]]; then
    # 替換函數參數
    sed -i '' 's/symbol: str/ticker: str/g' "$file"
    sed -i '' 's/symbol: str |/ticker: str |/g' "$file"

    # 替換變數名稱
    sed -i '' 's/\bsymbol,/ticker,/g' "$file"
    sed -i '' 's/\bsymbol:/ticker:/g' "$file"
    sed -i '' 's/\bsymbol =/ticker =/g' "$file"
    sed -i '' 's/\bsymbol}/ticker}/g' "$file"

    # 替換字典 key
    sed -i '' 's/"symbol"/"ticker"/g' "$file"
    sed -i '' "s/'symbol'/'ticker'/g" "$file"

    # 替換註釋
    sed -i '' 's/股票代碼/股票代號/g' "$file"
    sed -i '' 's/# symbol/# ticker/g' "$file"

    # 替換 for 迴圈變數
    sed -i '' 's/for symbol,/for ticker,/g' "$file"
    sed -i '' 's/for symbol in/for ticker in/g' "$file"

    # 替換 f-string
    sed -i '' 's/f"股票: {symbol}/f"股票: {ticker}/g' "$file"
    sed -i '' 's/f"{symbol}/f"{ticker}/g' "$file"

    # 特殊: excluded_symbols
    sed -i '' 's/excluded_symbols/excluded_tickers/g' "$file"
  fi

  # JavaScript 檔案
  if [[ "$file" == *.js ]] || [[ "$file" == *.ts ]]; then
    sed -i '' 's/symbol:/ticker:/g' "$file"
    sed -i '' 's/"symbol"/"ticker"/g' "$file"
    sed -i '' "s/'symbol'/'ticker'/g" "$file"
  fi
}

# 遍歷 Agent Tools
echo "🔧 處理 Agent Tools..."
find "$BACKEND_DIR/agents/tools" -name "*.py" -type f | while read -r file; do
  echo "  Processing: $file"
  replace_in_file "$file"
done

# 遍歷 Agent Core
echo "🔧 處理 Agent Core..."
find "$BACKEND_DIR/agents/core" -name "*.py" -type f | while read -r file; do
  echo "  Processing: $file"
  replace_in_file "$file"
done

# 遍歷 Agent Utils
echo "🔧 處理 Agent Utils..."
find "$BACKEND_DIR/agents/utils" -name "*.py" -type f | while read -r file; do
  echo "  Processing: $file"
  replace_in_file "$file"
done

# 遍歷測試檔案
echo "🧪 處理測試檔案..."
find "$TEST_DIR" -name "*.py" -type f | while read -r file; do
  echo "  Processing: $file"
  replace_in_file "$file"
done

# 遍歷 Frontend
echo "🎨 處理 Frontend..."
if [ -d "$FRONTEND_DIR" ]; then
  find "$FRONTEND_DIR" -name "*.js" -o -name "*.ts" -o -name "*.svelte" | while read -r file; do
    echo "  Processing: $file"
    replace_in_file "$file"
  done
fi

echo ""
echo "✅ 重構完成！"
echo ""
echo "📋 下一步:"
echo "1. 執行資料庫遷移: ./scripts/db_migrate.sh"
echo "2. 運行測試: uv run pytest"
echo "3. 檢查 git diff 確認變更"
echo "4. 提交變更: git commit -m 'refactor: rename symbol to ticker'"
