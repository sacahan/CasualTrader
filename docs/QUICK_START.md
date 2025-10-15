# 🚀 快速開始：CasualTrader 重構

從 **補充文檔 → 概念驗證 → 正式重構** 的完整流程已準備就緒！

## 📚 文檔導覽

```
docs/
├── REFACTOR_PLAN.md                      # 主計劃（必讀）
├── REFACTOR_IMPLEMENTATION_GUIDE.md      # 實施指南（詳細）
├── REFACTOR_PROGRESS.md                  # 進度追蹤
└── QUICK_START.md                        # 本文檔

backend/src/agents/
└── POC_README.md                         # POC 使用說明
```

## 🎯 三步驟流程

### Step 1: 閱讀文檔 (15-30 分鐘)

```bash
# 1. 先閱讀主計劃
cat docs/REFACTOR_PLAN.md

# 2. 閱讀實施指南（重點看錯誤處理和測試）
cat docs/REFACTOR_IMPLEMENTATION_GUIDE.md

# 3. 查看當前進度
cat docs/REFACTOR_PROGRESS.md
```

### Step 2: 運行 POC (5-10 分鐘)

```bash
# 設置環境
cd backend
export OPENAI_API_KEY='your-key-here'

# 運行 POC（驗證架構可行性）
python -m src.agents.poc_full_workflow

# 預期看到：
# ✓ 資料庫配置載入成功
# ✓ Agent 初始化成功
# ✓ 執行成功（如果 API key 和 MCP 配置正確）
```

### Step 3: 開始重構 (7-10 天)

```bash
# 創建重構分支
git checkout -b refactor/simplified-agent-architecture

# 備份當前狀態
git tag backup-before-refactor

# 開始實作（按優先級）
# 1. agent_service.py (基於 POC)
# 2. trading_agent.py (基於 POC)
# 3. executor.py
# 4. sub-agents
# 5. 測試
# 6. API 整合
```

## 📋 實作檢查清單

### Phase 1: 核心重構 (3-5 天)

#### Day 1-2: 資料庫和核心 Agent

- [ ] 實作 `backend/src/database/agent_service.py`
  - 基於 `poc_agent_service.py`
  - 連接實際資料庫
  - 添加更多查詢方法
  - 完整錯誤處理

- [ ] 實作 `backend/src/agents/trading_agent.py`
  - 基於 `poc_trading_agent.py`
  - 添加 Sub-agents 載入
  - 完善配置管理
  - 完整錯誤處理

- [ ] 單元測試
  - `tests/database/test_agent_service.py`
  - `tests/agents/test_trading_agent.py`

#### Day 3-4: Sub-agents 和執行器

- [ ] 重構 Sub-agents（tools/ 目錄）
  - `tools/fundamental_agent.py`
  - `tools/technical_agent.py`
  - `tools/risk_agent.py`
  - `tools/sentiment_agent.py`

- [ ] 實作 `backend/src/agents/executor.py`
  - 多 Agent 管理
  - 並發控制
  - 狀態追蹤

- [ ] 單元測試
  - `tests/agents/test_executor.py`
  - `tests/agents/tools/test_*.py`

#### Day 5: 整合測試

- [ ] 整合測試
  - `tests/integration/test_agent_workflow.py`
  - `tests/integration/test_database_integration.py`

- [ ] E2E 測試
  - `tests/e2e/test_complete_workflow.py`

### Phase 2: API 整合 (1-2 天)

- [ ] 更新 API 路由
  - `api/routers/agents.py`
  - 支援新的執行模式
  - 返回 trace 資訊

- [ ] 更新 API 文檔
  - OpenAPI schema
  - 使用範例

- [ ] API 測試
  - `tests/api/test_agent_routes.py`

### Phase 3: 部署 (1-2 天)

- [ ] 運行所有測試
- [ ] 檢查測試覆蓋率 (> 80%)
- [ ] 代碼審查
- [ ] 部署到測試環境
- [ ] 監控和調整

## 🛠️ 開發工具

### 運行測試

```bash
# 所有測試
pytest backend/tests/ -v

# 單元測試
pytest backend/tests/agents/ -v
pytest backend/tests/database/ -v

# 整合測試
pytest backend/tests/integration/ -v

# 測試覆蓋率
pytest --cov=src --cov-report=html
```

### 代碼檢查

```bash
# Lint
ruff check backend/src/

# Format
ruff format backend/src/

# Type check
mypy backend/src/
```

## 📊 進度追蹤

在 `docs/REFACTOR_PROGRESS.md` 中更新進度：

```markdown
### 整體進度

[████████████████░░░░] 80%  # 更新百分比

已完成:
✅ 重構計劃制定
✅ 實施細節補充
✅ 概念驗證 (POC)
✅ 核心重構  # 標記為完成
```

## 🚨 重要提醒

### 1. Git 工作流

```bash
# 經常 commit
git add .
git commit -m "feat: implement agent_service.py"

# 推送到遠端
git push origin refactor/simplified-agent-architecture

# 如果遇到問題，可以回滾
git reset --hard HEAD~1
```

### 2. 測試驅動開發

```python
# 先寫測試
def test_agent_service_get_config():
    # 測試邏輯
    pass

# 再實作功能
class AgentDatabaseService:
    async def get_agent_config(self, agent_id: str):
        # 實作邏輯
        pass
```

### 3. 漸進式重構

- 不要一次改太多
- 每個模組完成後就測試
- 保持系統可運行狀態

## 💡 最佳實踐

### 1. 代碼風格

```python
# ✅ 好的命名
async def get_agent_config(self, agent_id: str) -> Agent:
    """載入 Agent 配置"""
    pass

# ❌ 不好的命名
async def get(self, id: str):
    pass
```

### 2. 錯誤處理

```python
# ✅ 具體的異常
try:
    agent = await self.get_agent_config(agent_id)
except AgentNotFoundError:
    logger.error(f"Agent {agent_id} not found")
    raise
except AgentConfigurationError:
    logger.error(f"Invalid config for {agent_id}")
    raise

# ❌ 籠統的異常
try:
    agent = await self.get_agent_config(agent_id)
except Exception:
    pass
```

### 3. 日誌記錄

```python
# ✅ 結構化日誌
logger.info(
    "Agent initialized",
    extra={
        "agent_id": agent_id,
        "model": ai_model,
        "duration_ms": elapsed_ms
    }
)

# ❌ 簡單字串
logger.info("Agent initialized")
```

## 🔗 相關連結

- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [SQLAlchemy 2.0 文檔](https://docs.sqlalchemy.org/en/20/)
- [Pytest 文檔](https://docs.pytest.org/)

## 🆘 獲取幫助

如果遇到問題：

1. 檢查 POC 是否運行成功
2. 閱讀實施指南的錯誤處理章節
3. 查看現有的測試範例
4. 提交 Issue 附帶詳細錯誤訊息

## ✅ 完成標準

重構完成的標準：

- [ ] 所有測試通過（單元、整合、E2E）
- [ ] 測試覆蓋率 > 80%
- [ ] 代碼審查通過
- [ ] 文檔更新完成
- [ ] API 正常運作
- [ ] 前端可以連接
- [ ] Trace 功能正常
- [ ] 監控日誌正常

---

**準備開始！祝重構順利！** 🎉

**維護**: CasualTrader Development Team
**最後更新**: 2025-10-15
