#!/bin/bash

# Symbol → Ticker 資料庫遷移執行腳本

set -e

DB_FILE="casualtrader.db"
MIGRATION_SQL="scripts/migrate_symbol_to_ticker.sql"
BACKUP_DIR="backups"

echo "🗄️  Symbol → Ticker 資料庫遷移工具"
echo "=================================="
echo ""

# 檢查資料庫檔案
if [ ! -f "$DB_FILE" ]; then
  echo "❌ 錯誤: 找不到資料庫檔案 '$DB_FILE'"
  echo "請確認您在專案根目錄執行此腳本"
  exit 1
fi

# 檢查遷移 SQL 檔案
if [ ! -f "$MIGRATION_SQL" ]; then
  echo "❌ 錯誤: 找不到遷移 SQL 檔案 '$MIGRATION_SQL'"
  exit 1
fi

# 創建備份目錄
mkdir -p "$BACKUP_DIR"

# 備份資料庫
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/casualtrader_before_migration_${TIMESTAMP}.db"

echo "📦 備份資料庫..."
cp "$DB_FILE" "$BACKUP_FILE"
echo "✅ 備份完成: $BACKUP_FILE"
echo ""

# 顯示當前資料庫狀態
echo "📊 當前資料庫狀態:"
echo "-------------------"
sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM agent_holdings;" | xargs -I {} echo "  agent_holdings 記錄數: {}"
sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM transactions;" | xargs -I {} echo "  transactions 記錄數: {}"
echo ""

# 確認執行
read -p "⚠️  確定要執行遷移嗎? (y/N): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ 遷移已取消"
  exit 0
fi

# 執行遷移
echo "🔄 執行資料庫遷移..."
sqlite3 "$DB_FILE" <"$MIGRATION_SQL"

# 檢查結果
if [ $? -eq 0 ]; then
  echo "✅ 遷移執行成功！"
  echo ""

  # 驗證資料完整性
  echo "🔍 驗證資料完整性..."
  echo "-------------------"
  sqlite3 "$DB_FILE" "SELECT * FROM (
        SELECT
            'agent_holdings' as table_name,
            (SELECT COUNT(*) FROM agent_holdings_backup) as backup_count,
            (SELECT COUNT(*) FROM agent_holdings) as current_count
    );" | tr '|' ' ' | xargs echo "  "

  sqlite3 "$DB_FILE" "SELECT * FROM (
        SELECT
            'transactions' as table_name,
            (SELECT COUNT(*) FROM transactions_backup) as backup_count,
            (SELECT COUNT(*) FROM transactions) as current_count
    );" | tr '|' ' ' | xargs echo "  "
  echo ""

  echo "📝 遷移後資料庫狀態:"
  echo "-------------------"
  sqlite3 "$DB_FILE" "PRAGMA table_info(agent_holdings);" | grep ticker && echo "  ✅ agent_holdings.ticker 欄位已建立"
  sqlite3 "$DB_FILE" "PRAGMA table_info(transactions);" | grep ticker && echo "  ✅ transactions.ticker 欄位已建立"
  echo ""

  # 提示清理備份表
  echo "💡 提示: 如果資料驗證無誤，可以執行以下命令清理備份表:"
  echo "   sqlite3 $DB_FILE \"DROP TABLE agent_holdings_backup; DROP TABLE transactions_backup;\""
  echo ""

  echo "🎉 遷移完成！"
else
  echo "❌ 遷移失敗！"
  echo ""
  echo "🔄 正在從備份恢復..."
  cp "$BACKUP_FILE" "$DB_FILE"
  echo "✅ 已恢復到遷移前狀態"
  exit 1
fi
