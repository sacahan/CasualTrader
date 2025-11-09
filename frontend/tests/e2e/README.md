# 🧪 E2E 測試

Playwright 端到端測試套件，包含 8 個完整的測試用例。

---

## 🚀 快速開始

### 執行測試

```bash
# 執行單個測試（推薦先執行 E2E-001 驗證環境）
npx playwright test E2E-001-agent-creation.spec.js --ui

# 執行所有 E2E 測試
npx playwright test E2E-*.spec.js

# 帶調試器
npx playwright test E2E-001-agent-creation.spec.js --debug

# 查看測試報告
npx playwright show-report
```

---

## 📋 測試列表

| ID | 功能 | 檔案 |
|----|------|------|
| E2E-001 | Agent 創建與執行流程 | `E2E-001-agent-creation.spec.js` |
| E2E-002 | Agent 編輯功能 | `E2E-002-agent-edit.spec.js` |
| E2E-003 | Rebalancing 模式 | `E2E-003-rebalancing-mode.spec.js` |
| E2E-004 | 錯誤處理與表單驗證 | `E2E-004-error-handling.spec.js` |
| E2E-005 | Agent 詳情彈窗 | `E2E-005-agent-detail-modal.spec.js` |
| E2E-006 | 市場狀態顯示 | `E2E-006-market-status-display.spec.js` |
| E2E-007 | Agent 卡片互動 | `E2E-007-agent-card-interactions.spec.js` |
| E2E-008 | 空狀態與通知系統 | `E2E-008-empty-state-and-notifications.spec.js` |

---

## 📝 修改測試

所有測試邏輯都在 `.spec.js` 檔內。直接編輯相應的檔案：

### 調整選擇器

根據實際 UI 結構修改 locator：

```javascript
// 原始
await page.locator('[class*="AgentCard"]').click();

// 如果類名不同，嘗試其他方式
await page.locator('.agent-card').click();
await page.locator('[role="article"]').click();
await page.locator('button:has-text("創建")').click();
```

**常見選擇器**：

```javascript
// 按屬性
await page.locator('input[name="name"]').fill('value');
await page.locator('button[type="submit"]').click();

// 按文字
await page.locator('button:has-text("創建")').click();

// 按角色
await page.locator('[role="dialog"]').isVisible();

// 複合
await page.locator('[class*="Modal"] button:has-text("保存")').click();
```

### 調整超時

根據系統性能調整等待時間：

```javascript
// 增加超時時間
await expect(element).toBeVisible({ timeout: 5000 });

// 明確等待
await page.waitForTimeout(3000);
```

### 更新測試數據

修改 `TEST_DATA` 物件中的值以匹配業務邏輯：

```javascript
const TEST_DATA = {
  agentName: 'Your Agent Name',
  initialFunds: '1000000',
  // ... 其他配置
};
```

---

## 📚 測試結構

所有測試遵循統一的結構：

```javascript
test.describe('功能描述', () => {
  test.beforeEach(async ({ page }) => {
    // 測試前置操作
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('測試名稱', async ({ page }) => {
    await test.step('Step 1: 描述', async () => {
      // 步驟 1 的實現
    });

    await test.step('Step 2: 描述', async () => {
      // 步驟 2 的實現
    });
  });
});
```

### 特性

- ✅ `test.describe()` — 組織測試
- ✅ `test.step()` — 邏輯分組（易於追蹤）
- ✅ `beforeEach()` — 測試設置
- ✅ 多種選擇器策略 — 容錯性設計
- ✅ 動態等待 — 而非固定延遲
- ✅ 完整文檔 — JSDoc 和詳細註解

---

## 📏 命名規約

檔案遵循統一的命名格式：

**格式**：`E2E-{ID:03d}-{feature-slug}.spec.js`

### 構成

| 部分 | 說明 | 範例 |
|------|------|------|
| `E2E` | 前綴（固定） | `E2E` |
| `{ID:03d}` | 三位數字 ID | `001`, `002`, ..., `999` |
| `{feature-slug}` | 功能名稱（kebab-case） | `agent-creation`, `error-handling` |
| `.spec.js` | 副檔名 | `.spec.js` |

### 有效範例

✅ `E2E-001-agent-creation.spec.js`
✅ `E2E-002-agent-edit.spec.js`
✅ `E2E-099-error-handling.spec.js`

### 無效範例

❌ `E2E-1-agent-creation.js`（ID 格式錯誤）
❌ `E2E_001_agent_creation.js`（分隔符錯誤）
❌ `E2E-001-AgentCreation.js`（case 錯誤）

### Feature Slug 規約

使用 **kebab-case**（小寫、用連字號分隔）：

| 功能 | 正確 | 錯誤 |
|------|------|------|
| Agent 創建 | `agent-creation` | `AgentCreation`, `agent_creation` |
| 錯誤處理 | `error-handling` | `ErrorHandling`, `error_handling` |
| 市場狀態 | `market-status` | `MarketStatus`, `market_status` |

### ID 自動遞增

```bash
# 查看最大 ID
ls frontend/tests/e2e/E2E-*.spec.js | sort | tail -1
# 輸出：E2E-008-empty-state-and-notifications.spec.js

# 下一個 ID 為 E2E-009
```

---

## 🆕 新增測試

### 步驟 1: 確定下一個 ID

```bash
ls frontend/tests/e2e/E2E-*.spec.js | sort | tail -1
# 下一個 ID 為 E2E-009
```

### 步驟 2: 建立新檔案

基於現有測試複製並修改，確保：

- [ ] 檔名遵循 `E2E-{ID:03d}-{slug}.spec.js` 格式
- [ ] feature slug 使用 kebab-case
- [ ] 選擇器基於角色或語義屬性
- [ ] 使用 `test.step()` 組織代碼
- [ ] 包含 `beforeEach()` 設置
- [ ] 適當的等待和超時處理

---

## 📂 結構

```
frontend/tests/e2e/
├── E2E-001-agent-creation.spec.js
├── E2E-002-agent-edit.spec.js
├── E2E-003-rebalancing-mode.spec.js
├── E2E-004-error-handling.spec.js
├── E2E-005-agent-detail-modal.spec.js
├── E2E-006-market-status-display.spec.js
├── E2E-007-agent-card-interactions.spec.js
├── E2E-008-empty-state-and-notifications.spec.js
└── README.md (本檔案)

test-results/
└── e2e/
    ├── E2E-001/
    ├── E2E-002/
    └── ... (測試報告)
```

---

## 💡 常用命令速查

```bash
# UI 模式執行（推薦開發時使用）
npx playwright test E2E-001-agent-creation.spec.js --ui

# 調試模式
npx playwright test E2E-001-agent-creation.spec.js --debug

# 指定瀏覽器
npx playwright test E2E-001-agent-creation.spec.js --project=chromium

# 執行所有測試
npx playwright test E2E-*.spec.js

# 並行執行（加快速度）
npx playwright test E2E-*.spec.js --workers=4

# 查看 HTML 報告
npx playwright show-report

# 查看 JSON 報告
cat test-results/results.json
```

---

## 🎯 核心理念

**.spec.js 是唯一真相** — Playwright 測試檔是實際執行的代碼，這是業界標準做法。

不需要額外的配置檔或中間層 — 直接在 .spec.js 中修改和執行。

---

## 📌 下一步建議

1️⃣ **執行測試驗證環境**

   ```bash
   npx playwright test E2E-001-agent-creation.spec.js --ui
   ```

2️⃣ **根據實際 UI 調整**

- 更新選擇器以匹配實際 DOM
- 調整超時和等待時間
- 驗證測試數據

3️⃣ **批量執行驗證**

   ```bash
   npx playwright test E2E-*.spec.js
   ```

4️⃣ **整合到 CI/CD**

- GitHub Actions
- GitLab CI
- 其他 CI 系統

5️⃣ **定期運行**

- 發現 UI 變更
- 確保功能完整性

---

## 📖 Playwright 資源

- [Playwright 官方文檔](https://playwright.dev/)
- [Locator 最佳實踐](https://playwright.dev/docs/locators)
- [Test 組織結構](https://playwright.dev/docs/test-structure)
- [Expect 匹配器](https://playwright.dev/docs/test-assertions)

---

**版本**：1.0
**最後更新**：2025-11-09
**狀態**：✅ 生產就緒
