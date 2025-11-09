# mcp-memory-libsql 完整指南

## 1. 核心概念：Entity、Observation、Relation

### 知識圖譜結構

mcp-memory-libsql 實現的是一個**知識圖譜（Knowledge Graph）**系統，由三個核心組件組成：

圖譜中的實體透過觀測展示其詳細信息，透過關係邊連接到其他實體。

### 三者的具體定義

#### Entity（實體/節點）

- **定義**：知識圖中的節點，代表一個重要概念或事件
- **特點**：
  - 唯一標識 (name, PRIMARY KEY)
  - 有類型 (entityType)
  - 可有向量表示 (embedding)
- **例子**：
  - "trading_decision_2025_01_15"
  - "market_analysis_2025_01_15"
  - "TSMC_stock"

#### Observation（觀測/屬性）

- **定義**：實體的詳細屬性或事實信息
- **特點**：
  - 文本形式，無結構
  - 與 Entity 是 1:N 關係
  - 通過外鍵 (entity_name) 關聯到 Entity
- **例子**：
  - "時間: 2025-01-15 10:30"
  - "決策: 買入 TSMC 2330"
  - "數量: 1000 股"

#### Relation（關係/邊）

- **定義**：實體間的有向邊，表示邏輯關係
- **特點**：
  - 有方向性 (source → target)
  - 有類型 (relationType)
  - source 和 target 都必須是存在的 Entity
- **例子**：
  - decision -[based_on]-> market_analysis
  - result -[executes]-> decision

### 數據庫Schema

```sql
-- 實體表
CREATE TABLE entities (
  name TEXT PRIMARY KEY,           -- 唯一標識
  entity_type TEXT NOT NULL,       -- 實體類型
  embedding F32_BLOB,              -- 語義向量
  created_at DATETIME              -- 建立時間
);

-- 觀測表
CREATE TABLE observations (
  id INTEGER PRIMARY KEY,
  entity_name TEXT NOT NULL,       -- 外鍵
  content TEXT NOT NULL,           -- 觀測內容
  created_at DATETIME,
  FOREIGN KEY (entity_name) REFERENCES entities(name)
);

-- 關係表
CREATE TABLE relations (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,            -- 外鍵
  target TEXT NOT NULL,            -- 外鍵
  relation_type TEXT NOT NULL,     -- 關係類型
  created_at DATETIME,
  FOREIGN KEY (source) REFERENCES entities(name),
  FOREIGN KEY (target) REFERENCES entities(name)
);
```

## 2. API 使用指南

### 創建實體（包含觀測和關係）

```python
await memory_mcp.session.call_tool(
  "create_entities",
  {
    "entities": [{
      "name": "trading_decision_2025_01_15",
      "entityType": "trading_decision",
      "observations": [
        "時間: 2025-01-15 10:30",
        "決策: 買入 TSMC 2330",
        "數量: 1000 股",
        "目標價: 620 元"
      ],
      "relations": [{
        "target": "market_analysis_2025_01_15",
        "relationType": "based_on"
      }]
    }]
  }
)
```

**返回格式**：

```json
{
  "content": [{
    "type": "text",
    "text": "Successfully processed 1 entities ..."
  }]
}
```

### 單獨創建關係

```python
await memory_mcp.session.call_tool(
  "create_relations",
  {
    "relations": [{
      "source": "trading_result_2025_01_15",
      "target": "trading_decision_2025_01_15",
      "type": "executes"
    }]
  }
)
```

### 搜尋實體

#### 文本查詢

```python
result = await memory_mcp.session.call_tool(
  "search_nodes",
  {
    "query": "TSMC 買入",
    "limit": 10  # 實際最多 5 個
  }
)

# 解析結果
data = json.loads(result.content[0].text)
nodes = data["nodes"]        # 找到的實體列表
relations = data["relations"] # 相關的關係列表
```

#### 按 entity_type 查詢

```python
# 方式 1：直接查詢 entity_type 名稱（最簡單）
result = await memory_mcp.session.call_tool(
  "search_nodes",
  {"query": "trading_decision"}  # 返回所有 entity_type="trading_decision" 的實體
)

# 方式 2：結合 entity_type 和其他條件
result = await memory_mcp.session.call_tool(
  "search_nodes",
  {"query": "trading_decision TSMC"}  # 精度更高
)

# 方式 3：應用層精確過濾（推薦用於精確匹配）
async def search_by_entity_type(entity_type: str):
    result = await memory_mcp.session.call_tool(
        "search_nodes",
        {"query": entity_type, "limit": 10}
    )
    data = json.loads(result.content[0].text)
    # 應用層過濾：只返回精確匹配的實體
    return [e for e in data["nodes"] if e.get("entityType") == entity_type]

# 使用
trading_decisions = await search_by_entity_type("trading_decision")
```

#### 向量查詢

```python
result = await memory_mcp.session.call_tool(
  "search_nodes",
  {
    "query": [0.1, 0.2, 0.3, ...],  # embedding 數組
    "limit": 10
  }
)
```

### 讀取完整圖譜

```python
result = await memory_mcp.session.call_tool("read_graph", {})
data = json.loads(result.content[0].text)

entities = data["nodes"]      # 所有實體
relations = data["relations"]  # 所有關係

# 構造圖譜
for relation in relations:
    from_entity = relation["from"]
    to_entity = relation["to"]
    rel_type = relation["relationType"]
    # from_entity -[rel_type]-> to_entity
```

### 刪除操作

```python
# 刪除實體及其所有觀測和關係
await memory_mcp.session.call_tool(
  "delete_entity",
  {"name": "entity_name"}
)

# 刪除特定關係
await memory_mcp.session.call_tool(
  "delete_relation",
  {
    "source": "entity1",
    "target": "entity2",
    "type": "relation_type"
  }
)
```

## 3. search_nodes 詳細說明

### 查詢流程

執行順序：檢查是否為向量查詢 → 直接向量搜尋或生成 embedding → 向量搜尋失敗時轉文本搜尋

搜尋時會檢查以下三個字段：

- `Entity.name`：實體的唯一名稱
- `Entity.entity_type`：實體的類型 ✅ 可用於按類型篩選
- `Observation.content`：觀測內容

### 官方實現原理

根據官方源碼（`src/services/graph-service.ts`），`search_nodes` 在執行文本搜尋時的 SQL 語句為：

```sql
SELECT DISTINCT e.name
FROM entities e
LEFT JOIN observations o ON e.name = o.entity_name
WHERE e.name LIKE ?
   OR e.entity_type LIKE ?
   OR o.content LIKE ?
LIMIT 5
```

**關鍵點**：同時檢查 `e.entity_type` 字段 ✅

### 按 entity_type 查詢 - 三種方式

#### 方式 1：直接查詢 entity_type（推薦）

最簡單的方法。直接將 entity_type 的值作為查詢詞：

```python
result = await memory_mcp.session.call_tool(
    "search_nodes",
    {"query": "trading_decision"}  # 直接使用 entity_type 的值
)

data = json.loads(result.content[0].text)
entities = data["nodes"]  # 返回所有 entity_type="trading_decision" 的實體
```

**優點**：簡潔明了、一行代碼完成、自動通過 LIKE 匹配
**缺點**：可能搜到包含該詞的其他字段（如 observations 中提及該詞的實體）

#### 方式 2：結合 entity_type 和其他條件

提高搜尋精度：

```python
result = await memory_mcp.session.call_tool(
    "search_nodes",
    {"query": "trading_decision TSMC"}  # 組合多個詞
)

data = json.loads(result.content[0].text)
entities = data["nodes"]  # 返回同時包含這些詞的實體
```

**應用場景**：查詢特定類型的實體，並且內容涉及特定主題（如找 "trading_decision" 類型中關於 "TSMC" 的決策）

#### 方式 3：應用層精確過濾（最準確）

如果需要 100% 精確匹配 entity_type，在應用層進行過濾：

```python
async def search_by_entity_type_exact(memory_mcp, entity_type: str):
    """精確查詢指定 entity_type 的所有實體"""
    result = await memory_mcp.session.call_tool(
        "search_nodes",
        {"query": entity_type, "limit": 10}
    )

    data = json.loads(result.content[0].text)
    nodes = data.get("nodes", [])

    # 應用層過濾：只返回精確匹配的實體
    filtered = [n for n in nodes if n.get("entityType") == entity_type]

    return {
        "total_found": len(nodes),
        "exact_matched": len(filtered),
        "nodes": filtered
    }

# 使用
result = await search_by_entity_type_exact(memory_mcp, "trading_decision")
print(f"精確匹配: {len(result['nodes'])} 個實體")
```

**優點**：100% 精確匹配、可控且透明
**缺點**：需要在應用層處理、代碼較複雜

#### 方式對比

| 方式 | 代碼 | 複雜度 | 精確度 | 適用場景 |
|-----|------|------|------|--------|
| **方式 1** | `{"query": "trading_decision"}` | 低 | 中 | 日常查詢 |
| **方式 2** | `{"query": "trading_decision TSMC"}` | 低 | 中高 | 精細搜尋 |
| **方式 3** | 查詢後用 Python 過濾 | 中 | 高 | 需要精確結果 |

### 重要限制

| 限制 | 說明 |
|-----|------|
| **最多 5 個結果** | 硬限制，無法通過 limit 參數改變 |
| **模糊匹配** | 使用 LIKE %query%，不是精確等於 |
| **向量搜尋優先** | 如果有 embedding，會優先使用向量搜尋 |
| **無專用參數** | search_nodes 沒有 `entityType` 或 `filter` 參數 |

### 查詢無結果的診斷

| 症狀 | 可能原因 | 檢查方法 | 解決方案 |
|-----|--------|--------|--------|
| 所有查詢無結果 | 資料庫為空 | `read_graph()` 返回 0 實體 | 執行 `create_entities` 創建數據 |
| 創建成功但查詢無結果 | DB 路徑錯誤 | 檢查 `LIBSQL_URL` | 確保每次都指向同一 .db 文件 |
| 搜尋特定詞失敗 | 查詢詞不匹配 | 檢查 Entity name/type/observations | 使用存在的關鍵詞或前綴 |
| 向量搜尋無結果 | 無 embedding | 檢查實體是否有 embedding 字段 | 在 `create_entities` 時提供 embedding |

## 4. 實踐案例：交易決策系統

### 場景描述

建立一個交易決策追蹤系統，記錄：

- 市場分析信息
- 交易決策過程
- 交易執行結果
- 三者之間的因果關係

### 實現步驟

#### Step 1: 創建市場分析實體

```python
market_analysis = {
  "name": "market_analysis_2025_01_15",
  "entityType": "market_analysis",
  "observations": [
    "台灣股市開盤 17,500 點",
    "半導體板塊漲幅 2.3%",
    "外資淨買超 150 億",
    "TSMC 出現技術買入機會"
  ]
}

await memory_mcp.session.call_tool(
  "create_entities",
  {"entities": [market_analysis]}
)
```

#### Step 2: 創建交易決策（基於市場分析）

```python
trading_decision = {
  "name": "trading_decision_2025_01_15",
  "entityType": "trading_decision",
  "observations": [
    "時間: 2025-01-15 10:30",
    "決策: 買入 TSMC 2330",
    "數量: 1000 股",
    "目標價: 620 元",
    "技術指標: RSI 35(超賣), MACD 正向交叉"
  ],
  "relations": [{
    "target": "market_analysis_2025_01_15",
    "relationType": "based_on"
  }]
}

await memory_mcp.session.call_tool(
  "create_entities",
  {"entities": [trading_decision]}
)
```

#### Step 3: 創建交易結果（執行決策）

```python
trading_result = {
  "name": "trading_result_2025_01_15",
  "entityType": "trading_result",
  "observations": [
    "成交時間: 2025-01-15 10:35",
    "成交價: 615 元",
    "成交股數: 1000 股",
    "交易總額: 615,000 元"
  ],
  "relations": [{
    "target": "trading_decision_2025_01_15",
    "relationType": "executes"
  }]
}

await memory_mcp.session.call_tool(
  "create_entities",
  {"entities": [trading_result]}
)
```

#### Step 4: 查詢完整知識圖

```python
result = await memory_mcp.session.call_tool("read_graph", {})
data = json.loads(result.content[0].text)

# 圖譜結構：
# market_analysis --based_on--> trading_decision --executes--> trading_result
```

## 5. 與 memory_tools.py 的整合

在 `backend/src/trading/tools/memory_tools.py` 中的使用：

```python
async def load_execution_memory(memory_mcp, agent_id: str) -> dict:
    """
    查詢過往 3 天的執行記憶體和決策
    """
    result = await memory_mcp.session.call_tool(
        "search_nodes",
        {
            "query": f"agent {agent_id} decision",
            "limit": 10,
        },
    )

    # 解析回應
    if result and hasattr(result, "content") and result.content:
        content_item = result.content[0]
        text_content = content_item.text
        data = json.loads(text_content)
        nodes = data.get("nodes", [])

        # 轉換為記憶體格式
        past_decisions = [
            {
                "date": node.get("created_at", ""),
                "action": node.get("observations", [])[0] if node.get("observations") else "",
                "reason": node.get("observations", [])[1] if len(node.get("observations", [])) > 1 else "",
            }
            for node in nodes
        ]

        return {"past_decisions": past_decisions}

    return {"past_decisions": []}
```

## 6. 故障排除

### 問題 1：search_nodes 返回空數組

**診斷流程**：

```python
# 1. 檢查資料庫是否有實體
result = await memory_mcp.session.call_tool("read_graph", {})
nodes = json.loads(result.content[0].text).get("nodes", [])
print(f"實體數: {len(nodes)}")  # 應 > 0

# 2. 如果為 0，檢查 DB 路徑
print(LIBSQL_URL)  # 確認是否指向正確的 .db

# 3. 測試查詢詞
result = await memory_mcp.session.call_tool(
    "search_nodes",
    {"query": nodes[0].get("name") if nodes else "test"}
)
```

### 問題 2：創建實體後 read_graph 無法看到

**可能原因**：

- DB 路徑不一致（每次初始化指向不同的 .db）
- **解決**：確保 LIBSQL_URL 環境變數始終相同

### 問題 3：向量搜尋無結果

**可能原因**：

- 實體沒有 embedding
- embedding 格式不正確
- **解決**：在 `create_entities` 時提供正確的 embedding 陣列

## 7. 參考資源

- 官方倉庫：[https://github.com/joleyline/mcp-memory-libsql](https://github.com/joleyline/mcp-memory-libsql)
- 核心文件：
  - `src/models/index.ts` - 數據模型定義
  - `src/services/graph-service.ts` - 圖譜操作
  - `src/services/database-service.ts` - 數據庫架構
  - `src/index.ts` - MCP 工具定義

## 8. 設計最佳實踐

1. **Entity 設計**
   - 使用有意義的名稱（包含日期/時間戳便於追蹤）
   - 明確定義 entityType 便於分類
   - 考慮提供 embedding 便於語義搜尋

2. **Observation 設計**
   - 保持 observation 的原子性（一個觀測一條消息）
   - 使用結構化格式便於解析（如 "key: value"）
   - 添加時間戳便於順序理解

3. **Relation 設計**
   - 明確定義 relationType（如 "based_on", "causes", "related_to"）
   - 確保 target entity 必須存在
   - 避免循環依賴（除非有特殊設計意圖）

4. **查詢最佳實踐**
   - 優先使用 Entity name 或類型進行查詢（精確度高）
   - 對長期保存的決策添加 embedding（便於後續語義搜尋）
   - 定期使用 read_graph 檢查數據完整性

## 9. 快速參考 - 常見場景

### 一行代碼查詢

```python
# 查詢所有 "trading_decision" 類型的實體
result = await memory_mcp.session.call_tool("search_nodes", {"query": "trading_decision"})
```

### 常見場景

```python
# 查詢所有交易決策
result = await memory_mcp.session.call_tool("search_nodes", {"query": "trading_decision"})

# 查詢特定股票的分析
result = await memory_mcp.session.call_tool("search_nodes", {"query": "market_analysis TSMC"})

# 查詢所有交易結果
result = await memory_mcp.session.call_tool("search_nodes", {"query": "trading_result"})
```

### 解析結果

```python
data = json.loads(result.content[0].text)
entities = data.get("nodes", [])  # 找到的實體列表

for entity in entities:
    print(f"名稱: {entity.get('name')}")
    print(f"類型: {entity.get('entityType')}")
    print(f"觀測: {entity.get('observations', [])}")
```

### 在交易系統中的完整用法

```python
class TradeMemoryManager:
    def __init__(self, memory_mcp):
        self.memory_mcp = memory_mcp

    async def get_all_decisions(self):
        """查詢所有交易決策"""
        result = await self.memory_mcp.session.call_tool(
            "search_nodes",
            {"query": "trading_decision"}
        )
        data = json.loads(result.content[0].text)
        return data.get("nodes", [])

    async def get_all_results(self):
        """查詢所有交易結果"""
        result = await self.memory_mcp.session.call_tool(
            "search_nodes",
            {"query": "trading_result"}
        )
        data = json.loads(result.content[0].text)
        return data.get("nodes", [])

    async def get_analysis_for_stock(self, symbol: str):
        """查詢特定股票的市場分析"""
        result = await self.memory_mcp.session.call_tool(
            "search_nodes",
            {"query": f"market_analysis {symbol}"}
        )
        data = json.loads(result.content[0].text)
        return data.get("nodes", [])

# 使用
manager = TradeMemoryManager(memory_mcp)
decisions = await manager.get_all_decisions()
results = await manager.get_all_results()
tsmc_analysis = await manager.get_analysis_for_stock("TSMC")
```

### 常見問題

**Q: 怎麼確保只返回 trading_decision 類型的實體？**
A: 在應用層過濾：`filtered = [e for e in entities if e.get("entityType") == "trading_decision"]`

**Q: 為什麼有時候搜不到？**
A: 可能因為沒有 embedding 而搜尋失敗。確認實體確實在 DB 中：使用 `read_graph` 檢查。

**Q: limit 參數能改變返回結果數嗎？**
A: 不能。最多返回 5 個結果是硬限制。

**Q: 可以搜尋多個 entity_type 嗎？**
A: 不能。建議多次查詢或在應用層組合結果。
