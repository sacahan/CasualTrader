---
id: task-002
type: development
status: in_progress
priority: HIGH
epic: epic-002
created: 2025-09-30T08:45:00.000Z
updated: 2025-09-30T11:18:24.3NZ
depends_on: [task-001]
blocks: []
estimated_effort: 2-3 days
recommended_agent: backend-expert
complexity: high
---

# Task Overview

整合台灣證券交易所即時股價 API，實作完整的資料請求、解析和處理功能。本任務專注於建立與證交所 API 的穩定連線，實作 JSON 資料解析邏輯，以及處理各種 API 回應狀況，確保能夠取得準確的即時股價資訊。

## Implementation Scope

- 建立與台灣證交所 `mis.twse.com.tw/stock/api/getStockInfo.jsp` 的 API 整合
- [參考範例](https://hackmd.io/@aaronlife/python-ex-stock-by-api)
- 實作股票代號驗證和請求參數處理邏輯
- 開發 JSON 資料解析器，處理證交所複雜的回應格式
- 建立完整的錯誤處理和重試機制
- 實作資料清理和驗證功能，確保回傳資料品質

## Technical Requirements

**Depends On**: task-001

**Blocks**: None - this task doesn't block other tasks

### API 整合需求

- 使用 httpx 實作非同步 HTTP 請求處理
- 支援台灣股票代號格式驗證 (4位數字)

- 處理證交所 API 的查詢參數格式 (`ex_ch=tse_{股票代碼}.tw` or `ex_ch=otc_{股票代碼}.tw`)
  - tse_開頭為上市股票
  - otc_開頭為上櫃股票
  - 如果是興櫃股票則無法取得
- 使用 http Get 方法向 API 發送請求
- 實作適當的 User-Agent 和請求標頭設定

### 資料處理需求

- 解析證交所回傳的 msgArray JSON 結構
- 提取關鍵股價欄位：當前價格、開高低價、成交量等
- 處理五檔買賣價量資訊的字串分割和解析
- 實作資料型別轉換和驗證

## Development Specifications

### 主要開發檔案

- **market_mcp/api/twse_client.py**: 證交所 API 客戶端
- **market_mcp/models/stock_data.py**: 股票資料 Pydantic 模型
- **market_mcp/parsers/twse_parser.py**: 證交所資料解析器
- **market_mcp/utils/validators.py**: 輸入驗證工具
- **tests/test_twse_integration.py**: API 整合測試

### 資料模型設計

```python
class TWStockResponse(BaseModel):
    symbol: str
    company_name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    open_price: float
    high_price: float
    low_price: float
    previous_close: float
    upper_limit: float
    lower_limit: float
    bid_prices: List[float]
    bid_volumes: List[int]
    ask_prices: List[float]
    ask_volumes: List[int]
    update_time: datetime
    last_trade_time: str
```

### 錯誤處理策略

- 網路連線錯誤的指數退避重試 (最多 3 次)
- 無效股票代號的清晰錯誤訊息
- API 回應格式異常的處理機制
- 超時控制 (5 秒請求超時)

## Acceptance Criteria

- [ ] 成功整合台灣證交所即時股價 API
- [ ] 正確解析所有必要股價欄位 (當前價、開高低、成交量等)
- [ ] 處理五檔買賣價量資訊的解析
- [ ] 實作完整的錯誤處理機制
- [ ] API 回應時間在正常情況下小於 2 秒
- [ ] 支援至少 95% 的台灣上市櫃股票查詢
- [ ] 通過模擬測試驗證 API 整合穩定性
- [ ] 處理各種異常情況 (網路錯誤、無效代號等)

## AI Development Metadata

- **Recommended Agent**: backend-expert
- **Skills Required**: Python, HTTP APIs, JSON Processing, Error Handling
- **Complexity Level**: high
- **Estimated Effort**: 2-3 days

## Context Files

- specs/tsd/tsd-001.md - 技術規格參考
- specs/epics/epic-002.md - Epic 詳細規格
- 證交所 API 文件和範例回應格式
