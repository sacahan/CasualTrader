---
id: task-004
type: development
status: new
priority: HIGH
epic: epic-004
created: 2025-09-30T08:45:00.000Z
updated: 2025-09-30T08:45:00.000Z
depends_on: [task-001, task-002, task-003]
blocks: []
estimated_effort: 1-2 days
recommended_agent: frontend-expert
complexity: medium
---

# Task Overview

建立標準化的 MCP 工具介面，提供一致且易於使用的股票查詢功能。本任務專注於設計使用者友善的工具介面、定義清晰的資料格式，以及實作完整的錯誤處理機制，確保 MCP 客戶端能夠方便地整合和使用股價查詢服務。

## Implementation Scope

- 設計和實作 `get_taiwan_stock_price` MCP 工具介面
- 建立標準化的 Pydantic 資料模型和回應格式
- 實作完整的參數驗證和錯誤處理機制
- 建立 MCP 客戶端整合範例和設定檔案
- 撰寫工具使用文件和 API 規格說明

## Technical Requirements

**Depends On**: task-001, task-002, task-003

**Blocks**: None - this task doesn't block other tasks

### MCP 工具介面需求

- 實作符合 MCP 協議標準的工具定義
- 提供清晰的工具描述和參數說明
- 支援中英文錯誤訊息和工具說明
- 回應時間符合 MCP 協議要求 (< 30 秒)

### 資料格式標準化

- 使用 Pydantic 模型確保資料一致性
- 定義標準化的錯誤回應格式
- 支援 JSON Schema 驗證
- 提供清晰的 API 文件和範例

## Development Specifications

### 主要開發檔案

- **casualtrader_mcp/tools/stock_price_tool.py**: 主要工具實作
- **casualtrader_mcp/models/mcp_responses.py**: MCP 回應模型
- **casualtrader_mcp/validators/input_validator.py**: 輸入驗證
- **casualtrader_mcp/handlers/error_handler.py**: 錯誤處理
- **docs/mcp_integration_guide.md**: 整合指南
- **examples/claude_desktop_config.json**: 客戶端設定範例

### MCP 工具定義

```python
@app.tool()
async def get_taiwan_stock_price(symbol: str) -> dict:
    """取得台灣股票即時價格資訊
    
    Args:
        symbol: 台灣股票代號 (4位數字，例如: 2330)
        
    Returns:
        包含完整股價資訊的字典，包括當前價格、開高低價、
        成交量、五檔買賣價量等詳細資料
        
    Raises:
        ValidationError: 股票代號格式錯誤
        APIError: API 呼叫失敗或頻率限制
    """
```

### 資料回應模型

```python
class StockPriceResponse(BaseModel):
    symbol: str = Field(description="股票代號")
    company_name: str = Field(description="公司名稱")
    current_price: float = Field(description="當前成交價")
    change: float = Field(description="漲跌金額")
    change_percent: float = Field(description="漲跌幅百分比")
    volume: int = Field(description="累積成交量")
    open_price: float = Field(description="開盤價")
    high_price: float = Field(description="最高價")
    low_price: float = Field(description="最低價")
    previous_close: float = Field(description="昨日收盤價")
    upper_limit: float = Field(description="漲停價")
    lower_limit: float = Field(description="跌停價")
    bid_prices: List[float] = Field(description="買價五檔")
    bid_volumes: List[int] = Field(description="買量五檔")
    ask_prices: List[float] = Field(description="賣價五檔")
    ask_volumes: List[int] = Field(description="賣量五檔")
    update_time: datetime = Field(description="資料更新時間")
    last_trade_time: str = Field(description="最近成交時刻")
```

### 客戶端整合

- 提供 Claude Desktop 設定範例
- 建立 VS Code MCP 整合說明
- 撰寫 uvx 執行和設定指南
- 提供常見問題解答和故障排除

## Acceptance Criteria

- [ ] MCP 客戶端能夠成功註冊和呼叫 get_taiwan_stock_price 工具
- [ ] 工具介面提供清楚的參數說明和限制
- [ ] 回應資料格式完整包含所有股價資訊欄位
- [ ] 錯誤處理提供有意義的錯誤碼和訊息
- [ ] 支援 Claude Desktop、VS Code MCP 等主要客戶端
- [ ] 工具回應時間符合 MCP 協議要求 (通常 < 30 秒)
- [ ] 通過完整的 MCP 協議相容性測試
- [ ] 提供完整的整合文件和範例

## AI Development Metadata

- **Recommended Agent**: frontend-expert
- **Skills Required**: MCP Protocol, API Design, Documentation
- **Complexity Level**: medium
- **Estimated Effort**: 1-2 days

## Context Files

- specs/tsd/tsd-001.md - 技術規格參考
- specs/epics/epic-004.md - Epic 詳細規格
- task-001.md - 基礎架構參考
- task-002.md - API 整合參考
- task-003.md - 快取系統參考
- MCP 協議官方文件
