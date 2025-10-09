#!/bin/bash

# End-to-End 真實資料整合測試執行腳本

set -e # 遇到錯誤立即退出

echo "=========================================="
echo "🚀 End-to-End Real Data Integration Tests"
echo "=========================================="
echo ""

# 設定顏色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 Python 環境
echo -e "${BLUE}📋 Checking Python environment...${NC}"
python --version
echo ""

# 安裝必要的依賴
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -q pytest pytest-asyncio sqlalchemy aiosqlite yfinance
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# 執行測試
echo -e "${BLUE}🧪 Running E2E tests...${NC}"
echo ""

# 測試 1: MCP Client 真實資料測試
echo -e "${YELLOW}Test Suite 1: MCP Client Real Data${NC}"
pytest tests/test_e2e_real_data_integration.py::TestMCPClientRealData -v -s

# 測試 2: Portfolio Queries 資料庫整合測試
echo ""
echo -e "${YELLOW}Test Suite 2: Portfolio Queries Database Integration${NC}"
pytest tests/test_e2e_real_data_integration.py::TestPortfolioQueriesDatabase -v -s

# 測試 3: 完整交易流程測試
echo ""
echo -e "${YELLOW}Test Suite 3: Complete Trade Flow${NC}"
pytest tests/test_e2e_real_data_integration.py::TestCompleteTradeFlow -v -s

# 生成測試報告
echo ""
echo -e "${BLUE}📊 Generating test report...${NC}"
pytest tests/test_e2e_real_data_integration.py -v --tb=short >test_report.txt 2>&1

if [ $? -eq 0 ]; then
	echo -e "${GREEN}✅ All tests passed!${NC}"
	echo ""
	echo "Test report saved to: test_report.txt"
else
	echo -e "${RED}❌ Some tests failed${NC}"
	echo "Check test_report.txt for details"
	exit 1
fi

echo ""
echo "=========================================="
echo "🎉 E2E Testing Complete!"
echo "=========================================="
