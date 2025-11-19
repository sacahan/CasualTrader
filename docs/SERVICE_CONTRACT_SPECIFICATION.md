# Service 層契約規範 (API-Service Layer Contract)

**版本**: 2.0
**最後更新**: 2025-11-09
**狀態**: Active
**變更**: 移除已刪除欄位，更新績效計算欄位

## 概述

本文件定義 CasualTrader 應用中 API 層與 Service 層的契約，確保業務邏輯層的介面一致性。

Service 層作為業務邏輯層，負責協調資料層操作、驗證規則、事務管理等。本文件明確定義 Service 類的方法簽名、參數型別、回傳值和異常。

---

## 核心原則

1. **方法簽名契約**：Service 方法簽名必須保持穩定
2. **異常型別契約**：定義明確的異常型別，便於 API 層統一處理
3. **回傳值契約**：回傳值型別必須明確定義
4. **冪等性契約**：某些操作必須是冪等的

---

## Contract 2: Service 層方法簽名

### 2.1 AgentsService

負責 Agent (代理人) 的所有業務邏輯操作。

#### 2.1.1 get_agent_config

```python
async def get_agent_config(self, agent_id: str) -> AgentResponse:
    """
    取得完整 Agent 配置

    Args:
        agent_id (str): Agent ID (UUID 格式)

    Returns:
        AgentResponse: 包含以下欄位的完整 Agent 物件
            - id: Agent ID
            - name: Agent 名稱
            - description: 描述
            - ai_model: 使用的 AI 模型鑰匙
            - description: Agent 描述
            - investment_preferences: 投資偏好列表
            - created_at: 建立時間 (ISO 8601 格式)
            - last_active_at: 最後活動時間 (ISO 8601 格式，可為 null)
            - updated_at: 更新時間 (ISO 8601 格式)

    Raises:
        AgentNotFoundError: Agent 不存在
        DatabaseError: 資料庫層錯誤

    Examples:
        >>> service = AgentsService(session=db_session)
        >>> agent = await service.get_agent_config("agent_001")
        >>> print(agent.name)
        'My Trading Agent'
    """
    pass
```

**契約驗證**：

- ✓ 回傳型別必須是 `AgentResponse` 物件
- ✓ 時間戳必須是 ISO 8601 格式字串
- ✓ 異常型別必須是 `AgentNotFoundError` 或 `DatabaseError`
- ✗ 不可直接回傳 ORM 模型物件（必須轉換）

#### 2.1.2 delete_agent

```python
async def delete_agent(self, agent_id: str) -> DeleteResult:
    """
    刪除 Agent 及其所有相關記錄（級聯刪除）

    Args:
        agent_id (str): Agent ID

    Returns:
        DeleteResult: 刪除統計資訊
            {
                "deleted_agent": 1,
                "deleted_records": {
                    "performances": <int>,
                    "transactions": <int>,
                    "sessions": <int>
                },
                "deleted_at": "2025-10-23T14:30:00Z"
            }

    Raises:
        AgentNotFoundError: Agent 不存在
        CascadeDeleteError: 級聯刪除失敗
        DatabaseError: 資料庫層錯誤

    Examples:
        >>> result = await service.delete_agent("agent_001")
        >>> print(f"刪除了 {result['deleted_records']['performances']} 筆績效記錄")
        刪除了 30 筆績效記錄
    """
    pass
```

**契約驗證**：

- ✓ 回傳型別必須是字典，包含 `deleted_agent`、`deleted_records`、`deleted_at` 三個鍵
- ✓ `deleted_records` 必須計算所有級聯刪除的記錄數
- ✓ 必須驗證 Agent 存在後再刪除（先檢查再刪除）
- ✓ 異常型別必須是定義的異常類別
- ✗ 不可返回 ORM 物件

#### 2.1.3 create_agent

```python
async def create_agent(self, agent_data: CreateAgentRequest) -> AgentResponse:
    """
    建立新 Agent

    Args:
        agent_data (CreateAgentRequest): Agent 建立請求
            - name: 1-100 字
            - description: 0-500 字
            - ai_model: 模型鑰匙
            - strategy_prompt: 0-2000 字
            - investment_preferences: 投資偏好清單
            - enabled_tools: 啟用的工具

    Returns:
        AgentResponse: 新建立的 Agent 完整資訊

    Raises:
        ValidationError: 輸入驗證失敗
        DatabaseError: 資料庫層錯誤
    """
    pass
```

**契約驗證**：

- ✓ 必須驗證所有輸入欄位
- ✓ 名稱必須唯一性檢查
- ✓ 回傳新建 Agent 的完整資訊（包含 ID）

### 2.2 SessionService

負責交易 Session (交易會話) 的業務邏輯。

#### 2.2.1 get_session

```python
async def get_session(self, session_id: str) -> SessionResponse:
    """
    取得 Session 詳情

    Args:
        session_id (str): Session ID

    Returns:
        SessionResponse: Session 詳細資訊

    Raises:
        SessionNotFoundError: Session 不存在
        DatabaseError: 資料庫層錯誤
    """
    pass
```

#### 2.2.2 end_session

```python
async def end_session(self, session_id: str) -> SessionEndResult:
    """
    結束 Session

    Args:
        session_id (str): Session ID

    Returns:
        SessionEndResult: 結束結果（包含最終損益等資訊）

    Raises:
        SessionNotFoundError: Session 不存在
        SessionAlreadyClosedError: Session 已結束
        DatabaseError: 資料庫層錯誤
    """
    pass
```

### 2.3 TradingService

負責交易相關的業務邏輯。

#### 2.3.1 execute_trade

```python
async def execute_trade(self, trade_request: TradeRequest) -> TradeResult:
    """
    執行交易

    Args:
        trade_request (TradeRequest): 交易請求
            - session_id: Session ID
            - symbol: 股票代碼
            - action: 'buy' 或 'sell'
            - quantity: 交易數量
            - price: 價格（可選，預設市價）

    Returns:
        TradeResult: 交易執行結果
            - success: 是否成功
            - transaction_id: 交易 ID
            - executed_price: 成交價格
            - executed_at: 成交時間

    Raises:
        InsufficientBalanceError: 餘額不足
        InvalidTradeError: 無效交易
        ExternalServiceError: 外部服務錯誤（如股價查詢失敗）
        DatabaseError: 資料庫層錯誤
    """
    pass
```

---

### 2.4 ToolConfigService

負責動態工具配置管理。根據 Agent 執行模式（TRADING 或 REBALANCING）動態決定所需工具集合。

**關鍵特性**:

- 根據 AgentMode 決定工具配置
- 支持 2 種執行模式：TRADING 和 REBALANCING
- TRADING 模式：完整工具集（所有 MCP 伺服器、4 個 Sub-agents）
- REBALANCING 模式：簡化工具集（核心 MCP 伺服器、2 個 Sub-agents）

#### 2.4.1 get_tool_config (全局函數)

```python
def get_tool_config(mode: AgentMode | None = None) -> ToolRequirements:
    """
    取得指定模式的工具配置需求

    Args:
        mode: Agent 執行模式 (AgentMode.TRADING 或 AgentMode.REBALANCING)
        如為 None，預設使用 TRADING 模式

    Returns:
        ToolRequirements: 工具需求規格
            - include_memory_mcp: 是否包含記憶體 MCP 伺服器
            - include_casual_market_mcp: 是否包含市場數據 MCP 伺服器
            - include_perplexity_mcp: 是否包含新聞/投資研究 MCP 伺服器
            - include_buy_sell_tools: 是否包含買賣交易工具
            - include_portfolio_tools: 是否包含投資組合查詢工具
            - include_fundamental_agent: 是否包含基本面分析 Sub-agent
            - include_technical_agent: 是否包含技術面分析 Sub-agent
            - include_risk_agent: 是否包含風險評估 Sub-agent
            - include_sentiment_agent: 是否包含情緒分析 Sub-agent

    Example:
        ```python
        # 取得 TRADING 模式的工具配置
        config = ToolConfig()
        trading_req = config.get_requirements(AgentMode.TRADING)
        # trading_req.include_buy_sell_tools → True
        # trading_req.include_fundamental_agent → True

        # 取得 REBALANCING 模式的工具配置
        rebal_req = config.get_requirements(AgentMode.REBALANCING)
        # rebal_req.include_buy_sell_tools → False
        # rebal_req.include_fundamental_agent → False
        ```
    """
```

#### 2.4.2 ToolConfig.compare_configurations

```python
def compare_configurations(
    mode1: AgentMode,
    mode2: AgentMode
) -> dict[str, Any]:
    """
    比較兩個執行模式的工具配置差異

    Args:
        mode1: 第一個模式
        mode2: 第二個模式

    Returns:
        字典包含差異資訊
            - differences: 詳細差異清單

    Example:
        ```python
        config = ToolConfig()
        diff = config.compare_configurations(AgentMode.TRADING, AgentMode.REBALANCING)
        ```
    """
```

---

## 異常型別契約

Service 層必須定義和拋出以下異常型別：

```python
class ServiceException(Exception):
    """Service 層基礎異常，所有 Service 異常應繼承此類"""
    pass


class AgentNotFoundError(ServiceException):
    """Agent 不存在"""
    def __init__(self, agent_id: str):
        super().__init__(f"Agent '{agent_id}' not found")


class CascadeDeleteError(ServiceException):
    """級聯刪除失敗"""
    def __init__(self, details: str):
        super().__init__(f"Cascade delete failed: {details}")


class SessionNotFoundError(ServiceException):
    """Session 不存在"""
    pass


class SessionAlreadyClosedError(ServiceException):
    """Session 已結束"""
    pass


class InsufficientBalanceError(ServiceException):
    """餘額不足"""
    pass


class InvalidTradeError(ServiceException):
    """無效交易"""
    pass


class ExternalServiceError(ServiceException):
    """外部服務錯誤（API 呼叫失敗等）"""
    pass


class ValidationError(ServiceException):
    """輸入驗證失敗"""
    pass


class DatabaseError(ServiceException):
    """資料庫層錯誤"""
    pass
```

---

## API 層的異常處理契約

API 層必須捕捉 Service 異常並轉換為適當的 HTTP 狀態碼：

```python
from fastapi import HTTPException

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, service: AgentsService = Depends()):
    try:
        result = await service.delete_agent(agent_id)
        return {"success": True, "data": result}

    except AgentNotFoundError:
        raise HTTPException(status_code=404, detail="Agent not found")

    except CascadeDeleteError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Database error")

    except Exception as e:
        # 捕捉未預期的異常
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 異常對應表

| Service 異常 | HTTP 狀態碼 | HTTP 詳情 |
|-------------|-----------|---------|
| `AgentNotFoundError` | 404 | Agent not found |
| `SessionNotFoundError` | 404 | Session not found |
| `CascadeDeleteError` | 500 | Cascade delete failed |
| `SessionAlreadyClosedError` | 409 | Session already closed |
| `InsufficientBalanceError` | 400 | Insufficient balance |
| `InvalidTradeError` | 400 | Invalid trade request |
| `ExternalServiceError` | 502 | Bad gateway |
| `ValidationError` | 422 | Validation error |
| `DatabaseError` | 500 | Internal server error |

---

## Contract 驗證測試 (`tests/contract/test_service_contract.py`)

### 方法存在性驗證

```python
@pytest.mark.asyncio
async def test_agents_service_methods_exist():
    """驗證 AgentsService 擁有所有必需方法"""
    service = AgentsService(session=None)

    # ✓ 驗證方法存在
    assert hasattr(service, 'get_agent_config')
    assert hasattr(service, 'delete_agent')
    assert hasattr(service, 'create_agent')

    # ✓ 驗證方法可呼叫
    assert callable(service.get_agent_config)
    assert callable(service.delete_agent)
    assert callable(service.create_agent)
```

### 異常型別驗證

```python
@pytest.mark.asyncio
async def test_agents_service_raises_correct_exceptions():
    """驗證 Service 方法拋出正確的異常型別"""
    service = AgentsService(session=db_session)

    # ✓ 驗證 AgentNotFoundError
    with pytest.raises(AgentNotFoundError):
        await service.get_agent_config("nonexistent_agent_id")

    # ✓ 驗證 CascadeDeleteError（當刪除失敗時）
    with pytest.raises(CascadeDeleteError):
        await service.delete_agent("agent_with_locked_records")
```

### 回傳值型別驗證

```python
@pytest.mark.asyncio
async def test_agents_service_return_types():
    """驗證 Service 方法回傳正確型別"""
    service = AgentsService(session=db_session)

    # ✓ create_agent 回傳 AgentResponse
    agent = await service.create_agent(create_request)
    assert isinstance(agent, AgentResponse)

    # ✓ delete_agent 回傳字典
    result = await service.delete_agent(agent_id)
    assert isinstance(result, dict)
    assert "deleted_agent" in result
    assert "deleted_records" in result
```

---

## 實施清單

### Contract 2: API-Service 層 (待實施)

- [ ] 建立 `tests/contract/test_service_contract.py`
- [ ] 實施方法存在性驗證測試
- [ ] 實施異常型別驗證測試
- [ ] 實施回傳值型別驗證測試
- [ ] 驗證所有測試通過
- [ ] 文檔完成

---

## 參考資源

- **API 契約**: `API_CONTRACT_SPECIFICATION.md`
- **ORM 契約**: `ORM_CONTRACT_SPECIFICATION.md`
- **遷移契約**: `MIGRATION_CONTRACT_SPECIFICATION.md`
- **完成總結**: `COMPLETION_SUMMARY.md`

---

**版本**: 1.0
**最後更新**: 2025-10-23
**狀態**: ✅ 規範完成，⏳ 測試待實施
