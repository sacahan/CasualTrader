# 開始閱讀

## 📚 文檔導航

本資料夾包含 3 份核心文檔（共約 20KB）：

| # | 文檔 | 用途 |
|----|------|------|
| 1️⃣ | **DESIGN_OVERVIEW.md** | 核心設計（5 min 讀完）|
| 2️⃣ | **IMPLEMENTATION_GUIDE.md** | 實施指南和代碼示例（30 min 讀完）|
| 3️⃣ | **MIGRATION_CHECKLIST.md** | 部署檢查清單（20 min 讀完）|

## 🚀 快速路線

### 決策者 (15 min)
1. 讀本文件 (2 min)
2. 讀 DESIGN_OVERVIEW.md (10 min)
3. 看 MIGRATION_CHECKLIST.md 中的「成功指標」(3 min)

### 開發者 (2 小時)
1. DESIGN_OVERVIEW.md (5 min)
2. IMPLEMENTATION_GUIDE.md (60 min)
3. MIGRATION_CHECKLIST.md (20 min)
4. 開始編碼

### 專案經理 (30 min)
1. DESIGN_OVERVIEW.md
2. MIGRATION_CHECKLIST.md

## 🎯 核心設計結論

**一句話總結**：維持 `/start` 端點，添加 `mode` 參數，實現單一模式執行。

### API 變更
```
舊: POST /agents/{id}/start → Body: {}
新: POST /agents/{id}/start → Body: { mode: "OBSERVATION|TRADING|REBALANCING" }
```

### UI 變更
```
舊: [開始] [停止]
新: [觀察] [交易] [再平衡] [停止]
```

### 後端邏輯
```
舊: 自動循環 OBSERVATION → TRADING → REBALANCING
新: 用戶手動選擇，單一模式執行完立即返回
```

## ✅ 重要事項

1. **設計一致性**：所有文檔都基於同一設計
   - ✅ 維持 `/start` 端點（無新增 `/execute` 端點）
   - ✅ 無需向後兼容（直接修改簽名）
   - ✅ 復用設計原則

2. **優先順序**
   - P0：API 簽名修改、單一模式執行、finally 清理
   - P1：UI 按鈕、API 調用
   - P2：文檔、測試

3. **成功標誌**
   - 無 cancel scope 錯誤
   - 連續執行多個模式成功
   - 資源正確清理
   - 所有測試通過

## 📖 開始閱讀

**第 1 步**：讀 DESIGN_OVERVIEW.md 理解設計
**第 2 步**：讀 IMPLEMENTATION_GUIDE.md 開始編碼
**第 3 步**：使用 MIGRATION_CHECKLIST.md 追蹤進度

---

**祝實施順利！** 🚀
