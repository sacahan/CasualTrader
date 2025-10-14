"""
OpenAPI Documentation Configuration

Enhanced Swagger documentation with examples and detailed descriptions.
"""

from typing import Any

# API Response Examples
AGENT_EXAMPLE = {
    "id": "agent_20251008_123456",
    "name": "保守型價值投資者",
    "description": "專注於穩健成長的價值型股票",
    "ai_model": "gpt-4o",
    "strategy_prompt": "尋找本益比低於15、股息殖利率高於4%的穩定企業",
    "color_theme": "#28a745",
    "current_mode": "TRADING",
    "status": "running",
    "initial_funds": 1000000.0,
    "current_funds": 1050000.0,
    "max_turns": 50,
    "enabled_tools": {
        "get_taiwan_stock_price": True,
        "buy_taiwan_stock": True,
        "sell_taiwan_stock": True,
    },
    "investment_preferences": {
        "max_position_size": 200000,
        "sectors": ["金融", "電信"],
    },
    "custom_instructions": "避免高科技股，專注傳統產業",
    "created_at": "2025-10-08T10:30:00",
    "updated_at": "2025-10-08T12:15:00",
    "portfolio": {
        "total_value": 1050000.0,
        "cash": 850000.0,
        "stocks_value": 200000.0,
        "positions": [
            {
                "symbol": "2330",
                "shares": 1000,
                "avg_cost": 500.0,
                "current_price": 520.0,
            }
        ],
    },
    "performance": {
        "total_return": 0.05,
        "sharpe_ratio": 1.2,
        "max_drawdown": -0.03,
        "win_rate": 0.65,
    },
}

CREATE_AGENT_EXAMPLE = {
    "name": "積極型成長投資者",
    "description": "追求高成長的科技股",
    "ai_model": "gpt-4o",
    "strategy_prompt": "尋找營收成長率超過20%、本益比在合理範圍的科技股",
    "color_theme": "#dc3545",
    "initial_funds": 1000000.0,
    "max_turns": 100,
    "enabled_tools": {
        "get_taiwan_stock_price": True,
        "buy_taiwan_stock": True,
        "sell_taiwan_stock": True,
        "get_stock_daily_trading": True,
    },
    "investment_preferences": {
        "max_position_size": 300000,
        "sectors": ["半導體", "電子"],
    },
    "custom_instructions": "重點關注台積電、聯發科等龍頭股",
}

PORTFOLIO_EXAMPLE = {
    "agent_id": "agent_20251008_123456",
    "total_value": 1050000.0,
    "cash": 850000.0,
    "stocks_value": 200000.0,
    "total_return": 0.05,
    "positions": [
        {
            "symbol": "2330",
            "company_name": "台積電",
            "shares": 1000,
            "avg_cost": 500.0,
            "current_price": 520.0,
            "market_value": 520000.0,
            "unrealized_pnl": 20000.0,
            "unrealized_pnl_percent": 0.04,
        }
    ],
    "updated_at": "2025-10-08T12:15:00",
}

TRADE_EXAMPLE = {
    "id": "trade_20251008_001",
    "agent_id": "agent_20251008_123456",
    "symbol": "2330",
    "company_name": "台積電",
    "action": "buy",
    "quantity": 1000,
    "price": 500.0,
    "total_amount": 500000.0,
    "fee": 1425.0,
    "tax": 0.0,
    "net_amount": 501425.0,
    "timestamp": "2025-10-08T10:45:00",
    "reason": "技術指標顯示突破支撐位，適合進場",
}

PERFORMANCE_EXAMPLE = {
    "agent_id": "agent_20251008_123456",
    "period": "all_time",
    "total_return": 0.05,
    "total_return_percent": 5.0,
    "sharpe_ratio": 1.2,
    "max_drawdown": -0.03,
    "win_rate": 0.65,
    "total_trades": 20,
    "winning_trades": 13,
    "losing_trades": 7,
    "avg_profit_per_trade": 2500.0,
    "best_trade": 15000.0,
    "worst_trade": -5000.0,
    "calculated_at": "2025-10-08T12:15:00",
}

WEBSOCKET_MESSAGE_EXAMPLE = {
    "event_type": "agent_status_changed",
    "agent_id": "agent_20251008_123456",
    "timestamp": "2025-10-08T12:15:00",
    "data": {"status": "running", "current_turn": 5, "total_turns": 50},
}

ERROR_EXAMPLE = {"detail": "Agent not found"}


def get_openapi_tags() -> list[dict[str, Any]]:
    """Get OpenAPI tags with descriptions."""
    return [
        {
            "name": "system",
            "description": "系統狀態與健康檢查",
        },
        {
            "name": "agents",
            "description": """
## 交易代理管理

提供完整的 AI 交易代理生命週期管理功能：

- **創建代理**: 配置 AI 模型、交易策略、風險偏好
- **查詢代理**: 獲取代理詳細資訊、狀態、配置
- **控制代理**: 啟動、停止、切換模式
- **更新代理**: 修改策略、調整參數
- **刪除代理**: 移除不需要的代理

### 支援的 AI 模型
- GPT-4o, GPT-4o-mini
- Claude Sonnet 4.5, Claude Opus 4
- Gemini 2.5 Pro, Gemini 2.0 Flash
- DeepSeek V3, Llama 3.3

### 交易模式
- **TRADING**: 正常交易模式
- **ANALYSIS**: 純分析模式（不執行交易）
- **PAPER**: 模擬交易模式
            """,
        },
        {
            "name": "trading",
            "description": """
## 交易數據查詢

提供完整的交易數據和績效分析功能：

- **投資組合**: 查詢持股、現金、總資產
- **交易歷史**: 所有買賣記錄
- **策略變更**: 策略調整記錄
- **績效指標**: 報酬率、夏普比率、最大回撤
- **市場狀態**: 當前市場狀況

### 績效指標說明
- **總報酬率**: (當前總資產 - 初始資金) / 初始資金
- **夏普比率**: 風險調整後報酬，數值越高越好
- **最大回撤**: 從高點下跌的最大幅度
- **勝率**: 獲利交易數 / 總交易數
            """,
        },
        {
            "name": "websocket",
            "description": """
## 即時通訊

WebSocket 連接用於接收即時交易事件和狀態更新。

### 連接方式
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Event:', message.event_type, message.data);
};
```

### 事件類型
- `agent_status_changed`: 代理狀態變更
- `trade_executed`: 交易執行通知
- `strategy_changed`: 策略調整通知
- `portfolio_updated`: 投資組合更新
- `performance_updated`: 績效指標更新

### 訊息格式
所有訊息都是 JSON 格式，包含:
- `event_type`: 事件類型
- `agent_id`: 相關代理 ID
- `timestamp`: 事件時間戳
- `data`: 事件數據
            """,
        },
    ]


def get_openapi_examples() -> dict[str, Any]:
    """Get OpenAPI response examples."""
    return {
        "agent": AGENT_EXAMPLE,
        "create_agent": CREATE_AGENT_EXAMPLE,
        "portfolio": PORTFOLIO_EXAMPLE,
        "trade": TRADE_EXAMPLE,
        "performance": PERFORMANCE_EXAMPLE,
        "websocket_message": WEBSOCKET_MESSAGE_EXAMPLE,
        "error": ERROR_EXAMPLE,
    }
