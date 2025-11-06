# CasualTrader Backend

## 技術棧

- Python 3.12+
- FastAPI 0.115+
- SQLAlchemy 2.0+ (Async)
- OpenAI Agent SDK
- UV 包管理器

---

## 🎯 Agent 執行模式 (Phase 4 完成)

後端現已支援 **2 種動態 Agent 執行模式**：

### 🎯 TRADING 模式 (完整工具集)
- **用途**: 完整的股票交易決策和執行
- **工具配置**:
  - ✅ 所有 MCP 伺服器（Memory、Market、Tavily）
  - ✅ 買賣交易工具（buy_stock, sell_stock）
  - ✅ 投資組合管理工具
  - ✅ 全部 4 個 Sub-agents（基本面、技術面、風險、情緒）

### ⚖️ REBALANCING 模式 (簡化工具集)
- **用途**: 投資組合再平衡和微調
- **工具配置**:
  - ✅ 核心 MCP 伺服器（Memory、Market）
  - ❌ 無買賣工具（僅查詢組合）
  - ✅ 投資組合管理工具
  - ✅ 2 個 Sub-agents（技術面、風險）

**相關文檔**:
- [完整模式說明](../docs/MIGRATION_GUIDE_OBSERVATION_TO_2MODES.md)
- [主項目文檔](../README.md)

---

## 開發

```bash
cd backend
uv sync
uv run uvicorn src.api.app:create_app --factory --reload
```

## 測試

```bash
cd backend
uv run pytest tests/ -v
```

詳見 [測試指南](./tests/README.md)、`docs/API_IMPLEMENTATION.md` 和 `docs/AGENTS_ARCHITECTURE.md`

---

## 📊 Phase 4 重構完成 (2025-10-31)

✅ **核心成就：**
- OBSERVATION 模式完全移除（代碼層級 0 個遺留）
- 動態工具配置已實現（TRADING + REBALANCING）
- 記憶體工作流程已整合（完整的加載/保存/規劃）
- 67 個核心測試 100% 通過 ✅
- 18 個新的 E2E 迴歸測試 ✅

📈 **測試統計:**
- 核心模組測試: 67/67 (100%)
- 整體通過率: 302/322 (93.7%)

📚 **重要文檔：**
- [Phase 4 完成摘要](../PHASE4_COMPLETION_SUMMARY.md)
- [遷移和部署指南](../docs/MIGRATION_GUIDE_OBSERVATION_TO_2MODES.md)
- [服務契約規範](../docs/SERVICE_CONTRACT_SPECIFICATION.md)

---

**最後更新**: 2025-11-06
