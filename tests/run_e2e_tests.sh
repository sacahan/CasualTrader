#!/usr/bin/env zsh

# E2E Testing Script
# Runs complete end-to-end tests for the CasualTrader API

set -e

echo "======================================"
echo "CasualTrader E2E Testing Suite"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if uv is available
if ! command -v uv &>/dev/null; then
	echo "${RED}Error: uv not found. Please install uv first.${NC}"
	exit 1
fi

echo "${YELLOW}Step 1: Setting up test environment...${NC}"
uv sync

echo ""
echo "${YELLOW}Step 2: Running E2E API Integration Tests...${NC}"
uv run pytest tests/test_e2e_api_integration.py -v --tb=short

echo ""
echo "${YELLOW}Step 3: Running Complete Data Flow Tests...${NC}"
uv run pytest tests/test_e2e_complete_flow.py -v --tb=short

echo ""
echo "${GREEN}======================================"
echo "All E2E Tests Completed!"
echo "======================================${NC}"
