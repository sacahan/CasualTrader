# 交易原子性改進實施指南

**日期:** 2025-11-01
**版本:** 最終簡化版
**狀態:** 推薦實施
**預計工時:** 8-12 天

---

## 🎯 核心問題

### 當前流程的風險 ❌

```
AI Agent 分別呼叫三個函數：
1. buy_taiwan_stock()         ✅ 成功
2. record_trade()              ❌ 失敗
3. update_agent_funds()        ⏸️ 未執行

結果: 市場已交易，DB 無記錄 → 不一致
```

### 您的改進方案 ✅

> "AI Agent 可以發動買賣流程，只是需要鞏固整體交易原子性"

**解決方案:** 創建單一的 `execute_trade_atomic()` 函數，所有操作在一個事務中

```
execute_trade_atomic() [事務開始]
  ├─ 買賣 (MCP)        ✅
  ├─ 記錄 (DB)         ✅
  ├─ 更新資金 (DB)     ✅
  └─ 更新績效 (DB)     ✅
[事務結束]

保證: 全成功或全失敗 (自動回滾)
```

---

## 📋 實施清單

### Phase 1: 創建原子函數 (3-5 天)

**文件:** `backend/src/trading/tools/trading_tools.py`

```python
@function_tool(strict_mode=False)
async def execute_trade_atomic(
    ticker: str,
    action: str,           # "BUY" 或 "SELL"
    quantity: int,
    price: float | None = None,
    decision_reason: str = None,
    company_name: str | None = None,
) -> str:
    """執行完整交易 - 原子操作

    所有操作在單一事務中，保證:
    - 全成功 → 提交所有變更
    - 任何失敗 → 回滾所有變更
    """
    try:
        # ⭐ 開始事務
        async with agent_service.session.begin():

            # Step 1: 驗證參數
            if action not in ["BUY", "SELL"]:
                raise ValueError(f"無效的 action: {action}")
            if quantity <= 0 or quantity % 1000 != 0:
                raise ValueError(f"股數必須是 1000 的倍數")

            # Step 2: 執行市場交易 (MCP)
            market_result = await casual_market_mcp.session.call_tool(
                f"{action.lower()}_taiwan_stock",
                {
                    "symbol": ticker,
                    "quantity": quantity,
                    "price": price,
                }
            )
            logger.info(f"市場交易完成: {ticker} {action} {quantity}")

            # Step 3: 記錄交易到資料庫
            transaction = await agent_service.create_transaction(
                agent_id=agent_id,
                ticker=ticker,
                action=action,
                quantity=quantity,
                price=market_result["executed_price"],
                commission=market_result["commission"],
                reason=decision_reason,
            )
            logger.info(f"交易已記錄: {transaction.id}")

            # Step 4: 更新持股明細
            await agent_service.update_agent_holdings(
                agent_id=agent_id,
                ticker=ticker,
                quantity_change=quantity if action == "BUY" else -quantity,
            )
            logger.info(f"持股已更新")

            # Step 5: 更新資金餘額
            total_amount = quantity * market_result["executed_price"]
            fee = market_result["commission"]
            if action == "BUY":
                amount_change = -(total_amount + fee)
            else:
                amount_change = total_amount - fee

            await agent_service.update_agent_funds(
                agent_id=agent_id,
                amount_change=amount_change,
            )
            logger.info(f"資金已更新")

            # Step 6: 更新績效指標
            await agent_service.calculate_and_update_performance(
                agent_id=agent_id,
            )
            logger.info(f"績效已更新")

            # ⭐ 事務自動提交（所有步驟都成功）
            return (
                f"✅ 交易執行成功 (原子操作)\n\n"
                f"📊 交易詳情:\n"
                f"  • 股票: {ticker} ({company_name or '未知'})\n"
                f"  • 類型: {action}\n"
                f"  • 股數: {quantity:,}\n"
                f"  • 成交價: {market_result['executed_price']:,.2f}\n"
                f"  • 實際成本: {total_amount + fee:,.2f}\n\n"
                f"✅ 所有操作已原子性完成 ✓"
            )

    except Exception as e:
        # ⭐ 任何失敗 → 事務自動回滾
        logger.error(f"交易失敗: {e}", exc_info=True)
        return (
            f"❌ 交易執行失敗，已完全回滾\n\n"
            f"❌ 錯誤: {str(e)}\n\n"
            f"💡 系統狀態完全恢復，無任何痕跡"
        )
```

**檢查項:**

- [ ] 添加 `execute_trade_atomic()` 函數
- [ ] 所有操作都在 `async with transaction:` 中
- [ ] 包含完整的錯誤處理
- [ ] 添加詳細日誌記錄

### Phase 2: 集成 AI Agent (2 天)

**文件:** `backend/src/trading/tools/trading_agent.py`

```python
# 在工具列表中添加
tools = [
    execute_trade_atomic,  # ← 優先使用
    buy_taiwan_stock_tool,  # 備用
    sell_taiwan_stock_tool,  # 備用
    get_portfolio_status,
]

# 更新 AI prompt
system_prompt = """
...
使用交易工具時，優先使用 execute_trade_atomic()，因為它提供原子性保證。
...
"""
```

**檢查項:**

- [ ] 添加到工具列表
- [ ] 更新 AI prompt
- [ ] 驗證 AI 可呼叫

### Phase 3: 測試驗證 (3-5 天)

**單元測試:** `backend/tests/unit/test_atomic_trade.py`

```python
@pytest.mark.asyncio
async def test_execute_trade_atomic_buy_success():
    """測試成功的買入"""
    result = await execute_trade_atomic(
        agent_service,
        "agent_1",
        "2330",
        "BUY",
        1000,
        520.0,
        decision_reason="技術突破",
    )
    assert "✅" in result
    # 驗證 DB 有交易記錄
    # 驗證資金已更新

@pytest.mark.asyncio
async def test_execute_trade_atomic_failure_rollback():
    """測試失敗時回滾"""
    # 模擬 update_agent_funds 失敗
    with patch.object(
        agent_service, "update_agent_funds", side_effect=Exception("DB Error")
    ):
        result = await execute_trade_atomic(...)
        assert "❌" in result
        # 驗證事務回滾
        # 驗證 DB 無交易記錄
```

**檢查項:**

- [ ] 成功買入測試
- [ ] 成功賣出測試
- [ ] 失敗回滾測試
- [ ] 參數驗證測試
- [ ] 測試覆蓋率 > 85%

---

## 🔄 對比圖表

| 方面 | 當前 | 改後 |
|------|------|------|
| **原子性** | ❌ 無 | ✅ 有 |
| **故障回滾** | ❌ 無 | ✅ 自動 |
| **代碼複雜度** | 🟠 中 | 🟢 低 |
| **維護性** | 🟡 差 | 🟢 好 |
| **可靠性** | 🔴 低 | 🟢 高 |
| **AI 權限** | ✅ 有 | ✅ 有 |

---

## 💾 受影響的文件

### 新增

```
backend/src/trading/tools/trading_tools.py
  └─ 添加 execute_trade_atomic() 函數

backend/tests/unit/test_atomic_trade.py
  └─ 新增單元測試
```

### 修改

```
backend/src/trading/tools/trading_agent.py
  └─ 添加新函數到工具列表

backend/src/trading/trading_agent.py
  └─ 更新 AI prompt
```

### 保留（標記為 deprecated）

```
record_trade()
buy_taiwan_stock_tool()
sell_taiwan_stock_tool()
```

---

## 🚀 上線步驟

1. **測試環境** - 完整測試驗證
2. **灰度發布** - 10% 流量測試
3. **監控** - 24 小時無異常
4. **全量發布** - 100% 使用
5. **持續監控** - 1 週監控期

---

## 📌 關鍵要點

✅ **AI Agent 保有完整權限** - 仍可發動交易
✅ **系統層提供保障** - 原子性操作
✅ **代碼簡潔易維護** - 單一函數
✅ **故障自動恢復** - 事務回滾
✅ **無需複雜架構** - 實用簡約

---

**下一步:** 開始 Phase 1 實現 🚀
