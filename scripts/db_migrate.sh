#!/usr/bin/env bash
# =============================================================================
# Database Migration Script
# =============================================================================
#
# 提供資料庫遷移管理功能
#
# 使用方式:
#   ./scripts/db_migrate.sh [command] [options]
#
# 命令:
#   status              - 查看 migration 狀態
#   up [version]        - 執行 migrations (可選指定版本)
#   down <version>      - 回滾到指定版本
#   reset               - 重置資料庫 (危險操作!)
#
# 範例:
#   ./scripts/db_migrate.sh status
#   ./scripts/db_migrate.sh up
#   ./scripts/db_migrate.sh up 1.2.0
#   ./scripts/db_migrate.sh down 1.0.0
#   ./scripts/db_migrate.sh reset
#
# =============================================================================

set -e # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

# Change to backend directory where the database should be located
cd "$BACKEND_DIR"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
	echo -e "${BLUE}================================================${NC}"
	echo -e "${BLUE}  $1${NC}"
	echo -e "${BLUE}================================================${NC}"
}

print_success() {
	echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
	echo -e "${RED}❌ $1${NC}"
}

print_warning() {
	echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
	echo -e "${BLUE}ℹ️  $1${NC}"
}

# =============================================================================
# Migration Commands
# =============================================================================

run_migration() {
	local command=$1
	shift
	local args=("$@")

	print_header "Database Migration: $command"

	# Execute migration
	uv run python -m src.database.migrations "$command" "${args[@]}"

	local exit_code=$?

	if [ $exit_code -eq 0 ]; then
		print_success "Migration command completed successfully"
	else
		print_error "Migration command failed with exit code $exit_code"
		exit $exit_code
	fi
}

show_usage() {
	cat <<EOF
${BLUE}Database Migration Script${NC}

${GREEN}Usage:${NC}
  ./scripts/db_migrate.sh [command] [options]

${GREEN}Commands:${NC}
  ${YELLOW}status${NC}              查看 migration 狀態
  ${YELLOW}up [version]${NC}        執行 migrations (可選指定版本)
  ${YELLOW}down <version>${NC}      回滾到指定版本
  ${YELLOW}reset${NC}               重置資料庫 (危險操作!)

${GREEN}Examples:${NC}
  ./scripts/db_migrate.sh status
  ./scripts/db_migrate.sh up
  ./scripts/db_migrate.sh up 1.2.0
  ./scripts/db_migrate.sh down 1.0.0
  ./scripts/db_migrate.sh reset

${GREEN}Available Migrations:${NC}
  ${BLUE}v1.0.0${NC} - initial_schema
    創建初始資料表結構 (agents, sessions, transactions 等)

  ${BLUE}v1.1.0${NC} - add_performance_indexes
    新增績效查詢優化索引

  ${BLUE}v1.2.0${NC} - add_ai_model_config
    新增 AI 模型配置表並插入種子資料
    包含 OpenAI, Anthropic, Google Gemini, DeepSeek, xAI 模型

  ${BLUE}v1.3.0${NC} - rename_symbol_to_ticker
    重命名 symbol 欄位為 ticker (agent_holdings, transactions)
    統一使用 ticker 命名以保持代碼一致性

EOF
}

# =============================================================================
# Main Script
# =============================================================================

main() {
	# Check if command is provided
	if [ $# -eq 0 ]; then
		show_usage
		exit 1
	fi

	local command=$1
	shift

	case "$command" in
	status)
		run_migration "status" "$@"
		;;
	up)
		if [ $# -eq 0 ]; then
			print_info "Executing all pending migrations..."
			run_migration "up"
		else
			print_info "Executing migrations up to version: $1"
			run_migration "up" "$1"
		fi
		;;
	down)
		if [ $# -eq 0 ]; then
			print_error "Target version required for down migration"
			echo "Usage: ./scripts/db_migrate.sh down <version>"
			exit 1
		fi
		print_warning "Rolling back to version: $1"
		run_migration "down" "$1"
		;;
	reset)
		print_warning "This will reset the entire database!"
		read -p "Are you sure? Type 'YES' to confirm: " -r
		echo
		if [[ $REPLY == "YES" ]]; then
			print_info "Resetting database..."
			run_migration "reset"
		else
			print_info "Reset cancelled"
			exit 0
		fi
		;;
	help | --help | -h)
		show_usage
		;;
	*)
		print_error "Unknown command: $command"
		echo
		show_usage
		exit 1
		;;
	esac
}

# Execute main function
main "$@"
