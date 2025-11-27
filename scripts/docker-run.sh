#!/bin/bash

# ============================================
# CasualTrader Docker 執行腳本 (docker run 版本)
# ============================================
# 用法：./docker-run.sh [command] [options]
#
# 命令：
#   build       - 構建 Docker 鏡像
#   up          - 啟動容器（後台）
#   down        - 停止並移除容器
#   logs        - 查看容器日誌
#   shell       - 進入容器 shell
#   test        - 執行測試
#   db          - 啟動 PostgreSQL 容器
#   db-stop     - 停止 PostgreSQL 容器
#   clean       - 清理所有 Docker 資源
#

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案根目錄
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 預設環境文件
ENV_FILE="${PROJECT_DIR}/.env.docker"

# Docker 鏡像和容器名稱
IMAGE_NAME="sacahan/casual-trader:latest"
CONTAINER_NAME="casual-trader"
HOST_PORT="${HOST_PORT:-8877}"

# Docker 網路配置 - 用於與 casual-market 容器通訊
NETWORK_NAME="casual-network"

# 主機 IP 地址 (Linux 上用於連接主機服務)
HOST_IP="${HOST_IP:-127.0.0.1}"

# Memory MCP 資料庫存儲位置
MEMORY_DB_HOST_PATH="${PROJECT_DIR}/memory"

# GitHub Copilot 認證資料路徑
GITHUB_COPILOT_AUTH_PATH="${PROJECT_DIR}/github_copilot"

# 日誌存儲目錄
LOGS_DIR="${PROJECT_DIR}/logs"

# 檢查 .env.docker 是否存在
check_env_file() {
	if [ ! -f "$ENV_FILE" ]; then
		echo -e "${YELLOW}⚠️  未找到 $ENV_FILE${NC}"
		echo -e "${YELLOW}正在從示例複製...${NC}"
		if [ -f "${ENV_FILE}.example" ]; then
			cp "${ENV_FILE}.example" "$ENV_FILE"
			echo -e "${GREEN}✓ 已建立 $ENV_FILE (請編輯後再執行)${NC}"
			echo -e "${YELLOW}請編輯 .env.docker 檔案配置必要的環境變數${NC}"
			exit 1
		else
			echo -e "${RED}✗ 找不到 .env.docker.example${NC}"
			exit 1
		fi
	fi
}

# 確保 Docker 網路存在
ensure_network() {
	if ! docker network ls --format '{{.Name}}' | grep -q "^${NETWORK_NAME}$"; then
		echo -e "${BLUE}📡 建立 Docker 網路: $NETWORK_NAME${NC}"
		docker network create "$NETWORK_NAME"
		echo -e "${GREEN}✓ Docker 網路已建立${NC}"
	fi
}

# 啟動後端容器
start_container() {
	ensure_network
	check_env_file

	# 檢查是否已運行
	if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
		echo -e "${YELLOW}ℹ️ 容器已在運行${NC}"
		return 0
	fi

	# 檢查是否存在但未運行
	if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
		echo -e "${BLUE}啟動現有容器...${NC}"
		docker start "$CONTAINER_NAME"
		show_info
		return 0
	fi

	echo -e "${BLUE}🚀 啟動容器...${NC}"

	# 確保主機上的 memory 目錄存在
	mkdir -p "$MEMORY_DB_HOST_PATH"

	docker run -d \
		--name "$CONTAINER_NAME" \
		--network "$NETWORK_NAME" \
		--add-host host.docker.internal:host-gateway \
		--env-file "$ENV_FILE" \
		-p "${HOST_PORT}:8000" \
		-v "${MEMORY_DB_HOST_PATH}:/app/memory" \
		-v "${GITHUB_COPILOT_AUTH_PATH}:/root/.config/litellm/github_copilot" \
		-v "${LOGS_DIR}:/app/logs" \
		-e TZ=Asia/Taipei \
		--restart unless-stopped \
		"$IMAGE_NAME"

	echo -e "${GREEN}✓ 容器已啟動${NC}"
	echo ""
	show_info
}

# 停止容器
stop_container() {
	if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
		echo -e "${YELLOW}ℹ️  容器不存在${NC}"
		return 0
	fi

	echo -e "${BLUE}🛑 停止 容器...${NC}"
	docker stop "$CONTAINER_NAME"
	echo -e "${GREEN}✓ 容器已停止${NC}"
}

# 拉取 Docker 鏡像
pull_image() {
	echo -e "${BLUE}📥 從 Docker Hub 拉取鏡像: $IMAGE_NAME${NC}"

	if docker pull "$IMAGE_NAME"; then
		echo -e "${GREEN}✓ 鏡像拉取成功${NC}"
		echo ""
		echo -e "${BLUE}💡 下一步:${NC}"
		echo -e "   使用 ${GREEN}./docker-run.sh up${NC} 啟動容器"
	else
		echo -e "${RED}✗ 鏡像拉取失敗${NC}"
		echo -e "${YELLOW}請確保:${NC}"
		echo "   1. Docker 已安裝並運行"
		echo "   2. 網路連接正常"
		echo "   3. 有足夠的磁碟空間"
		exit 1
	fi
}

# 查看日誌
show_logs() {
	local container=$1

	if [ -z "$container" ]; then
		container="$CONTAINER_NAME"
	fi

	echo -e "${BLUE}📋 顯示 $container 容器日誌（按 Ctrl+C 退出）...${NC}"
	docker logs -f "$container"
}

# 進入容器 shell
enter_shell() {
	local container=$1

	if [ -z "$container" ]; then
		container="$CONTAINER_NAME"
	fi

	echo -e "${BLUE}🐚 進入 $container 容器...${NC}"
	docker exec -it "$container" /bin/bash
}

# 執行測試
run_tests() {
	echo -e "${BLUE}🧪 執行測試...${NC}"
	docker exec -T "$CONTAINER_NAME" pytest tests/ -v
}

# 移除容器
remove_container() {
	if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
		echo -e "${BLUE}移除 容器...${NC}"
		docker stop "$CONTAINER_NAME" 2>/dev/null || true
		docker rm "$CONTAINER_NAME"
	fi
}

# 清理資源
clean_up() {
	echo -e "${YELLOW}⚠️  此操作將刪除所有容器、鏡像和卷...${NC}"
	read -p "確認要繼續嗎？(y/N) " -n 1 -r
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		echo -e "${BLUE}清理中...${NC}"

		# 停止並移除容器
		remove_container

		# 移除鏡像
		docker rmi "$IMAGE_NAME" 2>/dev/null || true

		# 系統清理
		docker system prune -f

		echo -e "${GREEN}✓ 清理完成${NC}"
	else
		echo -e "${YELLOW}已取消${NC}"
	fi
}

# 顯示幫助信息
show_help() {
	cat << 'EOF'
CasualTrader Docker 執行腳本

用法: ./docker-run.sh [command]

📋 命令:

  up         啟動容器
	down       停止並移除容器
  pull       拉取鏡像
  logs       查看日誌
  shell      進入容器 shell
  test       執行測試
  info       服務信息
  clean      清理資源
  help       顯示此幫助信息

🚀 快速開始:

  1. 拉取鏡像:
     ./docker-run.sh pull

  2. 啟動服務:
     ./docker-run.sh up

  3. 查看日誌:
     ./docker-run.sh logs

 4. 停止並移除服務:
	 ./docker-run.sh down

🔗 服務端點:
  Backend:  http://localhost:${HOST_PORT}
  API 文檔:  http://localhost:${HOST_PORT}/api/docs

📝 環境配置:
  配置文件: .env.docker

💡 更多幫助: ./docker-run.sh info

EOF
}

# 顯示服務信息
show_info() {
	echo -e "${BLUE}📊 服務信息：${NC}"
	echo -e "  Backend: http://localhost:${HOST_PORT}"
	echo -e "  API 文檔: http://localhost:${HOST_PORT}/api/docs"
	echo -e "  PostgreSQL: localhost:5432"
	echo ""
	echo -e "${BLUE}常用命令：${NC}"
	echo -e "  查看日誌: ${GREEN}./docker-run.sh logs${NC}"
	echo -e "  進入 Shell: ${GREEN}./docker-run.sh shell${NC}"
	echo -e "  執行測試: ${GREEN}./docker-run.sh test${NC}"
	echo -e "  停止並移除服務: ${GREEN}./docker-run.sh down${NC}"
}

# 主函式
main() {
	local command=${1:-up}

	case "$command" in
	up)
		start_container
		;;
	down)
		remove_container
		;;
	pull)
		pull_image
		;;
	logs)
		show_logs "${2:-$CONTAINER_NAME}"
		;;
	shell)
		enter_shell "${2:-$CONTAINER_NAME}"
		;;
	test)
		run_tests
		;;
	clean)
		clean_up
		;;
	info)
		show_info
		;;
	help|-h|--help)
		show_help
		;;
	*)
		echo -e "${RED}❌ 未知命令: $command${NC}"
		echo ""
		echo -e "${BLUE}使用 '${GREEN}./docker-run.sh help${BLUE}' 查看完整幫助信息${NC}"
		echo ""
		echo "快速命令列表:"
		echo "  up      - 啟動服務"
		echo "  down    - 停止並移除服務"
		echo "  pull    - 拉取鏡像"
		echo "  logs    - 查看日誌"
		echo "  shell   - 進入容器"
		echo "  test    - 執行測試"
		echo "  info    - 顯示信息"
		echo "  clean   - 清理資源"
		echo "  help    - 顯示幫助"
		exit 1
		;;
	esac
}

main "$@"
