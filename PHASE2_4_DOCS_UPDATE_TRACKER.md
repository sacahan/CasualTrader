# Phase 2-4 文檔更新追蹤

## 概述
本文件追蹤在 Phase 2-4 期間需要更新的 `/docs/` 下的所有文檔。

所有更新將在對應 Phase 完成時統一進行，保持文檔與代碼同步。

---

## Phase 2：動態工具配置 (進行中)

### 待更新文檔

#### 1. docs/SERVICE_CONTRACT_SPECIFICATION.md
**更新內容：** 新增 ToolConfig 服務層契約

- [ ] 新增 ToolRequirements 數據模型定義
- [ ] 新增 ToolConfig 服務接口定義
- [ ] 記錄工具加載流程契約
- [ ] 更新版本為 1.2

**相關代碼:**
- `backend/src/trading/tool_config.py` (新建)
- `backend/tests/unit/test_tool_config.py` (新建)

#### 2. docs/API_CONTRACT_SPECIFICATION.md
**更新內容：** 補充執行模式與工具配置的關係

- [ ] 新增 API 調用時的模式參數說明
- [ ] 記錄不同模式返回的工具可用性
- [ ] 更新版本為 1.2

**相關端點:**
- POST `/api/agents/{agent_id}/start` - 指定執行模式

---

## Phase 3：記憶體整合 (待開始)

### 待更新文檔

#### 1. docs/SERVICE_CONTRACT_SPECIFICATION.md
**更新內容：** 新增記憶體服務層契約

- [ ] 新增 Memory 數據模型定義
- [ ] 新增 MemoryService 接口定義
- [ ] 記錄記憶體工作流程契約
- [ ] 更新版本為 1.3

**相關代碼:**
- `backend/src/service/memory_service.py` (待建)

#### 2. docs/API_CONTRACT_SPECIFICATION.md
**更新內容：** 新增記憶體相關 API 端點

- [ ] 新增記憶體查詢端點
- [ ] 新增記憶體更新端點
- [ ] 記錄記憶體格式契約
- [ ] 更新版本為 1.3

**相關端點:**
- GET `/api/agents/{agent_id}/memory` - 查詢 Agent 記憶體
- POST `/api/agents/{agent_id}/memory` - 更新 Agent 記憶體

---

## Phase 4：測試和文檔 (待開始)

### 待更新文檔

#### 1. docs/API_CONTRACT_SPECIFICATION.md
**更新內容：** 最終完整版本發佈

- [ ] 新增 2 模式執行示例
- [ ] 新增記憶體交互示例
- [ ] 新增完整 CRUD 生命週期示例
- [ ] 更新版本為 2.0

**相關內容:**
- 完整的 TRADING 模式工作流
- 完整的 REBALANCING 模式工作流
- 記憶體持久化流程

#### 2. docs/SERVICE_CONTRACT_SPECIFICATION.md
**更新內容：** 最終完整版本發佈

- [ ] 整合所有服務層變更
- [ ] 更新版本為 2.0

#### 3. docs/ORM_CONTRACT_SPECIFICATION.md
**更新內容：** 若有數據模型變更則更新

- [ ] 新增/修改時間戳欄位規範（如適用）
- [ ] 更新版本為 1.1（如有變更）

#### 4. docs/MIGRATION_CONTRACT_SPECIFICATION.md
**更新內容：** 若有數據庫遷移變更則更新

- [ ] 記錄 Phase 2-4 的所有遷移步驟
- [ ] 新增 OBSERVATION session 清理遷移
- [ ] 新增記憶體表初始化遷移（如適用）
- [ ] 更新版本為 1.1（如有變更）

---

## 文檔更新檢查清單

### Phase 2 完成後
- [ ] 運行 `grep -r "ToolConfig" docs/` 驗證更新
- [ ] 驗證所有代碼例子與實現一致
- [ ] 確認版本號正確

### Phase 3 完成後
- [ ] 運行 `grep -r "Memory" docs/` 驗證更新
- [ ] 驗證記憶體 API 示例可執行
- [ ] 確認版本號正確

### Phase 4 完成後
- [ ] 運行 `grep -r "TRADING\|REBALANCING" docs/` 驗證完整性
- [ ] 驗證所有示例的準確性
- [ ] 最終校對所有文檔

---

## 文檔更新優先級

| 優先級 | 文檔 | Phase | 說明 |
|--------|------|-------|------|
| 🔴 高 | SERVICE_CONTRACT_SPECIFICATION.md | 2-4 | 核心服務層變更 |
| 🔴 高 | API_CONTRACT_SPECIFICATION.md | 2-4 | 公開 API 變更 |
| 🟡 中 | MIGRATION_CONTRACT_SPECIFICATION.md | 1, 3-4 | 數據遷移變更 |
| 🟡 中 | ORM_CONTRACT_SPECIFICATION.md | 3-4 | 數據模型變更 |
| 🟢 低 | GITHUB_COPILOT_INTEGRATION.md | 4 | 文檔最後更新 |

---

**最後更新：** 2025-10-30 17:22
**狀態：** Phase 2 進行中
**下一步：** 完成 Phase 2.2 後檢查並更新本文件
