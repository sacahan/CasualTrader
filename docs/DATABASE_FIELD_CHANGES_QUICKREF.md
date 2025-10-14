# 資料庫欄位變更快速參考

## 🎯 必須更新的檔案清單

### 🔥 核心檔案 (必須更新)

1. **`/backend/src/database/migrations.py`** - 新增 migration 類別
2. **`/backend/src/database/models.py`** - 更新 SQLAlchemy 模型
3. **`/backend/src/api/models.py`** - 更新 Pydantic 模型
4. **`/backend/src/api/routers/agents.py`** - 更新 API 路由
5. **前端 Svelte 元件** - 更新 UI 顯示和表單

### 🔧 可能需要更新

- `/backend/src/database/agent_database_service.py` - 如有特殊查詢邏輯
- `/frontend/src/shared/api.js` - 如 API 參數變更
- `/frontend/src/stores/agents.js` - 如資料結構變更

## 📋 操作步驟檢查清單

### 步驟 1: 資料庫遷移

- [ ] 新增 Migration 類別到 `migrations.py`
- [ ] 實作 `up()` 和 `down()` 方法
- [ ] 註冊到 `DatabaseMigrationManager`
- [ ] 考慮 SQLite vs PostgreSQL 差異

### 步驟 2: 後端模型更新

- [ ] 更新 SQLAlchemy 模型 (`models.py`)
- [ ] 更新 Pydantic 請求/回應模型 (`api/models.py`)
- [ ] 更新 API 路由處理器 (`routers/agents.py`)

### 步驟 3: 前端更新

- [ ] 更新 Svelte 元件檔案
- [ ] 修改表單欄位和資料綁定
- [ ] 更新顯示邏輯和 UI 元件

### 步驟 4: 測試和驗證

- [ ] 執行 migration: `python -m src.database.migrations up`
- [ ] 測試 API 端點
- [ ] 驗證前端功能
- [ ] 測試回滾: `python -m src.database.migrations down`

## ⚠️ 關鍵注意事項

### SQLite 特殊處理

- SQLite 不支援 `RENAME COLUMN` 和 `DROP COLUMN`
- 必須重建表格並遷移資料
- 參考現有 migration 範例

### 版本控制

- Migration 版本號必須遞增且唯一
- 不要修改已應用的 migration
- 先備份資料庫

### 前後端一致性

- 確保欄位名稱在前後端保持一致
- 處理預設值和 null 值
- 更新所有相關的 UI 元件

## 🔍 參考範例

已實作的欄位變更範例：

- **新增**: `AddAgentColorMigration` (v1.4.0)
- **重命名**: `RenameModelToAIModelMigration` (v1.6.0)
- **刪除**: `RemoveUnusedAgentColumnsMigration` (v1.7.0)

## 🚀 執行命令

```bash
# 執行遷移
cd backend
python -m src.database.migrations up

# 查看狀態
python -m src.database.migrations status

# 回滾到指定版本
python -m src.database.migrations down [version]
```

---

## 📝 備註

快速參考 - 詳細指南請參閱 DATABASE_FIELD_CHANGES_GUIDE.md
