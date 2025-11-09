# Agent Performance 計算邏輯分析報告

**日期**: 2025-11-09
**分析範圍**: `agent_performance` 表中所有績效指標欄位
**資料來源**: backend/src/service/agents_service.py, backend/src/service/trading_service.py

---

## 執行摘要

分析 `agent_performance` 表中 8 個績效指標欄位的計算邏輯實現狀態。

### 結論

- ✅ **已實現**: 5 個欄位有完整計算邏輯
- ⚠️ **部分實現**: 1 個欄位有簡化計算
- ❌ **未實現**: 2 個欄位標註 TODO，目前設為預設值

---

## 欄位實現狀態總覽

| 欄位名 | 狀態 | 實現位置 | 說明 |
|--------|------|---------|------|
| `unrealized_pnl` | ❌ 未實現 | agents_service.py:792 | 標註 TODO，目前固定為 0 |
| `realized_pnl` | ❌ 未實現 | agents_service.py:793 | 標註 TODO，目前固定為 0 |
| `daily_return` | ❌ 未實現 | - | 無計算邏輯，預設為 NULL |
| `total_return` | ✅ 已實現 | agents_service.py:755-759 | 完整實現 |
| `win_rate` | ⚠️ 簡化實現 | agents_service.py:762-766 | 基於交易完成率，非真實獲利率 |
| `max_drawdown` | ❌ 未實現 | - | 無計算邏輯，預設為 NULL |
| `total_trades` | ✅ 已實現 | agents_service.py:751 | 完整實現 |
| `winning_trades` | ⚠️ 誤用 | agents_service.py:783, 797 | 實際為 completed_trades (賣出交易數) |

---

## 詳細分析

### 1. unrealized_pnl (未實現損益) ❌

**狀態**: 未實現
**當前行為**: 固定設為 `Decimal("0")`

#### 位置

```python
# backend/src/service/agents_service.py:792
unrealized_pnl=Decimal("0"),  # TODO: 計算未實現損益

# backend/src/service/trading_service.py:684
unrealized_pnl=Decimal("0"),
```

#### 應有邏輯

```python
# 未實現損益 = Σ (當前市價 - 平均成本) × 持有股數
unrealized_pnl = Decimal("0")
for holding in holdings:
    current_price = get_current_price(holding.ticker)  # 需要實時價格 API
    pnl = (current_price - holding.average_cost) * holding.quantity
    unrealized_pnl += Decimal(str(pnl))
```

#### 缺少的資源

- ✗ 實時股價查詢 API
- ✗ 股價快取機制
- ✗ 收盤價資料源

#### 影響

- 投資組合的浮動盈虧無法顯示
- 無法評估持倉部位的即時表現
- 總資產價值計算不準確 (使用成本價而非市價)

---

### 2. realized_pnl (已實現損益) ❌

**狀態**: 未實現
**當前行為**: 固定設為 `Decimal("0")`

#### 位置

```python
# backend/src/service/agents_service.py:793
realized_pnl=Decimal("0"),  # TODO: 計算已實現損益

# backend/src/service/trading_service.py:685
realized_pnl=Decimal("0"),
```

#### 部分實現 (僅在 API 層)

```python
# backend/src/api/routers/trading.py:393-408
# 僅在 API 查詢時計算，未持久化到資料庫
realized_pnl = 0.0
for tx in transactions:
    if tx.action == "SELL":
        buy_tx = find_matching_buy_transaction(tx)
        if buy_tx:
            realized_pnl += float(tx.total_amount) - (float(buy_tx.price) * tx.quantity)
```

#### 應有邏輯

```python
# 已實現損益 = Σ (賣出價格 - 買入成本) × 賣出股數 - 手續費
realized_pnl = Decimal("0")

# 取得所有已執行的交易
executed_transactions = get_executed_transactions(agent_id)

# 追蹤每檔股票的成本基礎 (FIFO)
cost_basis = {}  # {ticker: [(quantity, price), ...]}

for tx in executed_transactions:
    if tx.action == "BUY":
        # 記錄買入成本
        cost_basis.setdefault(tx.ticker, []).append((tx.quantity, tx.price))
    elif tx.action == "SELL":
        # 計算賣出損益
        remaining_qty = tx.quantity
        tx_pnl = Decimal("0")

        while remaining_qty > 0 and cost_basis.get(tx.ticker):
            buy_qty, buy_price = cost_basis[tx.ticker][0]
            qty_to_sell = min(remaining_qty, buy_qty)

            # 計算此批次損益
            tx_pnl += (tx.price - buy_price) * qty_to_sell

            # 更新剩餘數量
            remaining_qty -= qty_to_sell
            cost_basis[tx.ticker][0] = (buy_qty - qty_to_sell, buy_price)

            if cost_basis[tx.ticker][0][0] == 0:
                cost_basis[tx.ticker].pop(0)

        # 減去手續費和證交稅
        tx_pnl -= tx.commission
        realized_pnl += tx_pnl

return realized_pnl
```

#### 缺少的資源

- ✗ 成本基礎追蹤系統 (FIFO/LIFO)
- ✗ 買賣配對邏輯
- ✗ 手續費正確計算

#### 影響

- 無法顯示真實交易獲利/虧損
- 投資績效評估不準確
- 稅務計算基礎資料缺失

---

### 3. daily_return (當日報酬率) ❌

**狀態**: 未實現
**當前行為**: 預設為 `NULL`

#### 位置

無明確實現

#### 應有邏輯

```python
# 當日報酬率 = (今日總資產 - 昨日總資產) / 昨日總資產 × 100%
from datetime import date, timedelta

today = date.today()
yesterday = today - timedelta(days=1)

# 取得昨日績效記錄
yesterday_performance = get_performance_by_date(agent_id, yesterday)

if yesterday_performance and yesterday_performance.total_value > 0:
    daily_return = (
        (today_total_value - yesterday_performance.total_value) /
        yesterday_performance.total_value * 100
    )
else:
    daily_return = None  # 無前一日資料

return Decimal(str(daily_return)) if daily_return else None
```

#### 缺少的資源

- ✗ 歷史績效資料查詢
- ✗ 交易日判斷 (週末/假日處理)
- ✗ 前一日資料存在性檢查

#### 影響

- 無法追蹤短期績效變化
- 無法計算日波動率
- 無法監控異常績效波動

---

### 4. total_return (累計報酬率) ✅

**狀態**: 已實現
**當前行為**: 完整計算

#### 位置

```python
# backend/src/service/agents_service.py:755-759
total_return = (
    (total_value - agent.initial_funds) / agent.initial_funds
    if agent.initial_funds > 0
    else Decimal("0")
)
```

#### 公式

```
累計報酬率 = (目前總資產 - 初始資金) / 初始資金
```

#### 評估

✅ 實現正確
✅ 有除零保護
✅ 邏輯清晰

#### 注意事項

- 使用**簡化公式**，未考慮期間入金/出金
- 假設無額外注資或提領

---

### 5. win_rate (勝率) ⚠️

**狀態**: 簡化實現
**當前行為**: 基於賣出交易數 / 總交易數

#### 位置

```python
# backend/src/service/agents_service.py:762-766
win_rate = (
    Decimal(str(completed_trades / total_trades * 100))
    if total_trades > 0
    else Decimal("0")
)

# 其中 completed_trades 實際為賣出交易數
stmt_transactions = (
    select(
        func.count(Transaction.id).label("total_trades"),
        func.sum(
            case((Transaction.action == TransactionAction.SELL, 1), else_=0)
        ).label("completed_trades"),  # ← 這是賣出交易數，非獲利交易數
    )
    .where(Transaction.agent_id == agent_id)
    .where(Transaction.status == TransactionStatus.EXECUTED)
)
```

#### 問題

**目前計算的是"交易完成率"，非真實勝率**

```python
# ❌ 錯誤定義
win_rate = (賣出交易數 / 總交易數) × 100%

# ✅ 正確定義應為
win_rate = (獲利交易數 / 已完成交易數) × 100%
```

#### 應有邏輯

```python
# 勝率 = 獲利交易數 / 已完成交易對數 × 100%
winning_trades = 0
total_completed_pairs = 0

# 追蹤每檔股票的買賣配對
for ticker in unique_tickers:
    buy_txs = get_buy_transactions(agent_id, ticker)
    sell_txs = get_sell_transactions(agent_id, ticker)

    # 配對買賣交易 (FIFO)
    for sell_tx in sell_txs:
        remaining_qty = sell_tx.quantity

        for buy_tx in buy_txs:
            if remaining_qty <= 0:
                break

            qty_to_match = min(remaining_qty, buy_tx.remaining_qty)

            # 計算損益
            pnl = (sell_tx.price - buy_tx.price) * qty_to_match - commissions

            if pnl > 0:
                winning_trades += 1

            total_completed_pairs += 1
            remaining_qty -= qty_to_match
            buy_tx.remaining_qty -= qty_to_match

win_rate = (winning_trades / total_completed_pairs * 100) if total_completed_pairs > 0 else 0
```

#### 影響

- 顯示的勝率數值**不代表獲利率**
- 誤導使用者對交易績效的判斷
- 無法評估交易策略的有效性

---

### 6. max_drawdown (最大回撤) ❌

**狀態**: 未實現
**當前行為**: 預設為 `NULL`

#### 位置

無明確實現

#### 部分提及

```python
# backend/src/api/routers/trading.py:434
"max_drawdown": None,  # 需要歷史淨值數據

# backend/src/trading/tools/risk_agent.py:237
# 這是部位風險計算，非績效指標
max_drawdown = position_value * (volatility * 2)
```

#### 應有邏輯

```python
# 最大回撤 = (歷史最高淨值 - 當前最低淨值) / 歷史最高淨值 × 100%
from datetime import timedelta

# 取得歷史績效記錄
start_date = agent.created_at.date()
end_date = date.today()

historical_values = []
stmt = (
    select(AgentPerformance.date, AgentPerformance.total_value)
    .where(AgentPerformance.agent_id == agent_id)
    .where(AgentPerformance.date >= start_date)
    .where(AgentPerformance.date <= end_date)
    .order_by(AgentPerformance.date)
)
result = await session.execute(stmt)
historical_values = result.all()

if not historical_values:
    return None

# 計算最大回撤
max_value = Decimal("0")
max_drawdown = Decimal("0")

for date, total_value in historical_values:
    if total_value > max_value:
        max_value = total_value

    current_drawdown = (max_value - total_value) / max_value * 100
    if current_drawdown > max_drawdown:
        max_drawdown = current_drawdown

return max_drawdown
```

#### 缺少的資源

- ✗ 歷史績效資料查詢
- ✗ 淨值曲線追蹤
- ✗ 回撤期間記錄

#### 影響

- 無法評估投資風險
- 無法識別最差情境
- 無法比較不同策略的風險特徵

---

### 7. total_trades (累計交易次數) ✅

**狀態**: 已實現
**當前行為**: 完整計算

#### 位置

```python
# backend/src/service/agents_service.py:735-751
stmt_transactions = (
    select(
        func.count(Transaction.id).label("total_trades"),
        # ...
    )
    .where(Transaction.agent_id == agent_id)
    .where(Transaction.status == TransactionStatus.EXECUTED)
)

result = await self.session.execute(stmt_transactions)
trade_stats = result.first()
total_trades = trade_stats.total_trades or 0
```

#### 公式

```sql
SELECT COUNT(id) FROM transactions
WHERE agent_id = ? AND status = 'EXECUTED'
```

#### 評估

✅ 實現正確
✅ 只統計已執行交易
✅ 邏輯清晰

---

### 8. winning_trades (獲利交易數) ⚠️

**狀態**: 誤用
**當前行為**: 實際儲存的是**賣出交易數**，非獲利交易數

#### 位置

```python
# backend/src/service/agents_service.py:742-752
stmt_transactions = (
    select(
        func.count(Transaction.id).label("total_trades"),
        func.sum(
            case((Transaction.action == TransactionAction.SELL, 1), else_=0)
        ).label("completed_trades"),  # ← 賣出交易數
    )
    # ...
)

# ...

performance.winning_trades = completed_trades  # ← 錯誤：這是賣出交易數
```

#### 問題

**欄位命名為 `winning_trades`，但實際儲存的是 `sell_trades_count`**

#### 正確定義

```python
# winning_trades 應該是：獲利的交易對數
# 需要比對買入和賣出價格

winning_trades = 0

for sell_tx in sell_transactions:
    # 找到對應的買入交易
    matched_buy_txs = find_matching_buy_transactions(sell_tx)

    for buy_tx in matched_buy_txs:
        # 計算損益
        pnl = (sell_tx.price - buy_tx.price) * matched_qty - commission

        if pnl > 0:
            winning_trades += 1
```

#### 影響

- 欄位語義不正確
- 與 `win_rate` 計算邏輯不一致
- 誤導資料分析

---

## 其他發現

### API 層有部分計算邏輯

```python
# backend/src/api/routers/trading.py:390-438
# 在 API 查詢時臨時計算 realized_pnl 和 unrealized_pnl
# 但這些計算結果沒有持久化到資料庫
```

**問題**:

- 計算邏輯分散在多處
- API 層和 Service 層邏輯不一致
- 每次查詢都要重新計算，效能較差

### Risk Agent 工具有相關計算

```python
# backend/src/trading/tools/risk_agent.py:225-226
# 計算部位的未實現損益
unrealized_pnl = (current_price - avg_cost) * quantity
```

**用途**: 這是用於風險評估，非績效追蹤

---

## 建議修正方案

### 優先級 1: 修正語義錯誤 (立即執行)

#### 1.1 修正 winning_trades 定義

**選項 A**: 重新命名欄位 (建議)

```sql
ALTER TABLE agent_performance
RENAME COLUMN winning_trades TO sell_trades_count;

-- 新增正確的欄位
ALTER TABLE agent_performance
ADD COLUMN winning_trades INTEGER DEFAULT 0;
```

**選項 B**: 修正計算邏輯

```python
# 實作真實的獲利交易數計算
winning_trades = calculate_profitable_trade_pairs(agent_id)
performance.winning_trades = winning_trades
```

#### 1.2 修正 win_rate 計算

```python
# 基於真實獲利交易數計算
if total_completed_pairs > 0:
    win_rate = Decimal(str(winning_trades / total_completed_pairs * 100))
else:
    win_rate = Decimal("0")
```

### 優先級 2: 實現缺失的計算 (短期目標)

#### 2.1 實現 realized_pnl

**步驟**:

1. 建立交易配對演算法 (FIFO)
2. 計算每筆賣出交易的損益
3. 累加所有已實現損益
4. 在每次賣出交易後更新

**實施位置**: `trading_service.py` 中的 `record_trade()` 方法

#### 2.2 實現 unrealized_pnl

**步驟**:

1. 整合實時股價 API (如 Yahoo Finance, TWSE API)
2. 建立股價快取機制
3. 計算持倉浮動盈虧
4. 定期更新 (每日收盤後)

**實施位置**: 新增 `price_service.py` 和定時任務

#### 2.3 實現 daily_return

**步驟**:

1. 查詢前一日績效記錄
2. 計算日回報率
3. 處理交易日判斷 (週末/假日)

**實施位置**: `agents_service.py` 的 `calculate_and_update_performance()`

### 優先級 3: 實現進階指標 (長期目標)

#### 3.1 實現 max_drawdown

**步驟**:

1. 建立歷史淨值曲線
2. 追蹤滾動最高點
3. 計算最大回撤百分比
4. 記錄回撤期間

**實施位置**: 新增 `performance_analytics_service.py`

---

## 資料一致性問題

### 問題 1: 計算邏輯分散

**現況**:

- Service 層: 簡化計算，部分欄位為 0
- API 層: 臨時計算，未持久化
- Tool 層: 風險評估專用

**建議**: 統一在 Service 層實現所有計算邏輯

### 問題 2: 即時 vs 歷史資料

**現況**:

- `agent_performance` 是每日快照
- 但部分欄位 (unrealized_pnl) 需要即時價格

**建議**:

- 定期任務: 每日收盤後更新歷史記錄
- 即時查詢: API 層提供即時計算 (不持久化)

---

## 實施計劃

### 階段 1: 修正現有錯誤 (1 週)

- [ ] 重新命名或修正 `winning_trades` 欄位
- [ ] 修正 `win_rate` 計算邏輯
- [ ] 更新相關文件

### 階段 2: 實現基本計算 (2-3 週)

- [ ] 實現 `realized_pnl` 計算 (交易配對邏輯)
- [ ] 實現 `daily_return` 計算
- [ ] 整合實時股價 API
- [ ] 實現 `unrealized_pnl` 計算

### 階段 3: 實現進階指標 (4-6 週)

- [ ] 實現 `max_drawdown` 計算
- [ ] 新增 Sharpe Ratio, Sortino Ratio 等進階指標
- [ ] 建立績效分析儀表板
- [ ] 實現回測系統

---

## 測試需求

### 單元測試

```python
# test_performance_calculation.py

async def test_calculate_realized_pnl():
    """測試已實現損益計算"""
    # 建立測試交易記錄
    # 驗證 FIFO 配對邏輯
    # 驗證手續費計算
    pass

async def test_calculate_win_rate():
    """測試勝率計算"""
    # 建立獲利和虧損交易
    # 驗證勝率百分比
    pass

async def test_calculate_daily_return():
    """測試日回報率計算"""
    # 建立歷史績效記錄
    # 驗證回報率計算
    pass
```

### 集成測試

```python
async def test_performance_update_workflow():
    """測試完整績效更新流程"""
    # 建立 agent
    # 執行多筆交易
    # 更新績效
    # 驗證所有欄位正確計算
    pass
```

---

## 參考資料

### 績效指標定義

- **Realized P&L**: [Investopedia - Realized Profit/Loss](https://www.investopedia.com/terms/r/realizedprofit.asp)
- **Unrealized P&L**: [Investopedia - Unrealized Gain/Loss](https://www.investopedia.com/terms/u/unrealizedgain.asp)
- **Win Rate**: [Investopedia - Win Rate](https://www.investopedia.com/terms/w/win-loss-ratio.asp)
- **Maximum Drawdown**: [Investopedia - Maximum Drawdown](https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp)

### 實施參考

- Yahoo Finance API: <https://github.com/ranaroussi/yfinance>
- TWSE API: <https://www.twse.com.tw/zh/api-reference>
- 成本基礎追蹤: FIFO, LIFO, Average Cost

---

## 結論

`agent_performance` 表中的 8 個績效指標：

### ✅ 已正確實現 (2/8)

- `total_return` - 累計報酬率
- `total_trades` - 累計交易次數

### ⚠️ 需要修正 (2/8)

- `win_rate` - 當前為交易完成率，非真實勝率
- `winning_trades` - 當前為賣出交易數，非獲利交易數

### ❌ 尚未實現 (4/8)

- `unrealized_pnl` - 未實現損益 (需要實時價格)
- `realized_pnl` - 已實現損益 (需要交易配對邏輯)
- `daily_return` - 當日報酬率 (需要歷史資料)
- `max_drawdown` - 最大回撤 (需要淨值曲線)

**建議**: 優先修正語義錯誤，然後逐步實現缺失的計算邏輯。

---

**分析人員**: Claude (AI Assistant)
**分析日期**: 2025-11-09
**下次檢查**: 實施修正後
