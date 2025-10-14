# 資料庫欄位變更操作指南

## 📋 概述

當需要對 `casualtrader.db` 的欄位進行**新增/刪除/改名**操作時，此文件提供完整的操作流程和注意事項。

---

## 🎯 影響範圍分析

### 資料庫層 (Database Layer)

- **`/backend/src/database/migrations.py`** - 遷移腳本 🔥**必須**
- **`/backend/src/database/models.py`** - SQLAlchemy 模型 🔥**必須**
- **`/backend/src/database/schema.sql`** - SQL schema 文件 🔧**建議**

### 後端 API 層 (Backend API Layer)

- **`/backend/src/api/models.py`** - Pydantic 模型 🔥**必須**
- **`/backend/src/api/routers/agents.py`** - API 路由處理 🔥**必須**
- **`/backend/src/database/agent_database_service.py`** - 資料服務層 🔧**可能需要**

### 前端層 (Frontend Layer)

- **Svelte 元件檔案** 🔥**必須**
  - `/frontend/src/components/Agent/AgentCard.svelte`
  - `/frontend/src/components/Agent/AgentDetailModal.svelte`
  - `/frontend/src/components/Agent/AgentCreationForm.svelte`
- **前端資料層** 🔧**可能需要**
  - `/frontend/src/shared/api.js`
  - `/frontend/src/stores/agents.js`
  - `/frontend/src/shared/models.js`

---

## 📝 操作步驟清單

### 第一步：資料庫遷移設計

#### 1.1 新增 Migration 類別

在 `/backend/src/database/migrations.py` 中新增 migration：

```python
class YourNewMigration:
    """描述你的變更 (vX.X.X)"""

    version = "X.X.X"  # 遞增版本號
    name = "your_migration_name"
    description = "Clear description of what this migration does"

    async def up(self, engine: AsyncEngine) -> None:
        """執行遷移"""
        logging.info("Starting your migration...")

        async with engine.begin() as conn:
            # SQLite 和 PostgreSQL 的處理方式不同
            if "sqlite" in str(engine.url):
                await self._migrate_sqlite(conn)
            else:
                await self._migrate_postgres(conn)

    async def down(self, engine: AsyncEngine) -> None:
        """回滾遷移"""
        # 實作回滾邏輯
        pass
```

#### 1.2 註冊 Migration
在 `DatabaseMigrationManager.__init__()` 中加入新的 migration：

```python
self.migrations: list[MigrationStep] = [
    InitialSchemaMigration(),
    # ... 其他 migrations
    YourNewMigration(),  # 加在這裡
]
```

### 第二步：更新資料模型

#### 2.1 更新 SQLAlchemy 模型
在 `/backend/src/database/models.py` 中修改對應的模型類別：

```python
class Agent(Base):
    # 新增欄位
    new_field: Mapped[str] = mapped_column(String(100), default="default_value")

    # 修改現有欄位
    existing_field: Mapped[str] = mapped_column(String(200), nullable=False)  # 修改長度

    # 刪除欄位 - 直接移除該行
```

#### 2.2 更新 Pydantic 模型
在 `/backend/src/api/models.py` 中更新 API 模型：

```python
class CreateAgentRequest(BaseModel):
    # 新增欄位
    new_field: str = Field(default="default_value", max_length=100)

    # 修改現有欄位驗證
    existing_field: str = Field(..., min_length=1, max_length=200)

class UpdateAgentRequest(BaseModel):
    # 對應的可選更新欄位
    new_field: str | None = Field(None, max_length=100)
    existing_field: str | None = Field(None, max_length=200)

class AgentResponse(BaseModel):
    # 新增回應欄位
    new_field: str
    existing_field: str
```

### 第三步：更新 API 路由

#### 3.1 修改路由處理器
在 `/backend/src/api/routers/agents.py` 中：

```python
@router.post("/agents/")
async def create_agent(request: CreateAgentRequest, ...):
    # 處理新欄位
    config = AgentConfig(
        # ... 其他欄位
        new_field=request.new_field,  # 新增
        existing_field=request.existing_field,  # 修改
    )
```

#### 3.2 更新資料庫服務
如果需要特殊查詢邏輯，在 `/backend/src/database/agent_database_service.py` 中更新。

### 第四步：更新前端

#### 4.1 更新 Svelte 元件
在相關的 `.svelte` 檔案中：

```javascript
// 新增欄位到表單
<input bind:value={formData.new_field} />

// 修改顯示邏輯
<p>{agent.new_field || '預設值'}</p>

// 更新欄位引用
<span>{agent.existing_field}</span>  // 如果欄位名稱改變
```

#### 4.2 更新前端資料結構
在相關的 `.js` 檔案中更新資料模型和 API 呼叫。

### 第五步：執行遷移

```bash
cd backend
python -m src.database.migrations up
```

---

## ⚠️ 重要注意事項

### SQLite 限制
- SQLite 不支援 `RENAME COLUMN` 和 `DROP COLUMN`
- 必須使用**重建表**的方式進行欄位變更
- 需要妥善處理資料遷移和索引重建

### 資料安全
- **務必備份資料庫**再進行遷移
- 測試 `down()` 回滾功能
- 驗證資料完整性

### 版本控制
- Migration 版本號必須**遞增**且**唯一**
- 不要修改已應用的 migration
- 使用語意化的版本編號

### 效能考量
- 大量資料遷移可能耗時
- 考慮在低峰時段執行
- 監控資料庫鎖定狀況

---

## 🔍 驗證檢查清單

### 資料庫層驗證
- [ ] Migration 腳本測試通過
- [ ] `up()` 和 `down()` 都能正常執行
- [ ] 資料完整性檢查通過
- [ ] 索引和約束正確建立

### API 層驗證
- [ ] API 回應格式正確
- [ ] 欄位驗證規則正確
- [ ] 錯誤處理適當

### 前端層驗證
- [ ] 表單欄位顯示正確
- [ ] 資料綁定正常
- [ ] UI 元件更新到位

### 整合測試
- [ ] 端到端功能測試
- [ ] 各環境部署測試
- [ ] 效能回歸測試

---

## 📚 參考範例

### 新增欄位範例
參考 `AddAgentColorMigration` (v1.4.0) 新增 `color` 欄位的實作

### 重命名欄位範例
參考以下已實作的欄位重命名：
- `RenameSymbolToTickerMigration` (v1.3.0)
- `RenameColorToColorThemeMigration` (v1.5.0)
- `RenameModelToAIModelMigration` (v1.6.0)

### 刪除欄位範例
參考 `RemoveUnusedAgentColumnsMigration` (v1.7.0) 移除不用欄位的實作

---

## 🚨 常見錯誤

### Migration 錯誤
- **重複版本號**：確保版本號唯一
- **SQL 語法錯誤**：注意 SQLite 和 PostgreSQL 的差異
- **外鍵約束違反**：檢查資料完整性

### API 錯誤
- **欄位名稱不一致**：確保前後端欄位名稱對應
- **驗證規則過嚴**：考慮向後相容性
- **預設值缺失**：新增欄位需要合理預設值

### 前端錯誤
- **資料綁定失效**：檢查變數名稱
- **空值處理**：妥善處理 `null` 和 `undefined`
- **UI 元件未更新**：確保所有相關元件都已更新

---

## 📞 支援資源

- **Migration 腳本範例**：`/backend/src/database/migrations.py`
- **資料模型定義**：`/backend/src/database/models.py`
- **API 模型定義**：`/backend/src/api/models.py`
- **測試案例**：`/backend/tests/database/`

---

*最後更新：2025年10月14日*
