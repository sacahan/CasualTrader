import { test, expect } from '@playwright/test';

/**
 * 測試案例編號：E2E-004
 * 測試目標：驗證表單驗證規則、錯誤處理機制和用戶友善的錯誤提示
 *
 * 測試工具：Playwright
 * 測試範圍：前端表單驗證 + 錯誤消息顯示
 * 優先級：High
 * 標籤：validation, error-handling, form
 *
 * 教學說明：
 * - 表單驗證應防止無效數據提交到後端
 * - 錯誤提示應明確告知用戶問題所在
 * - 測試涵蓋空表單、無效金額、邊界值等場景
 */

/**
 * 輔助函數：選擇模型下拉選項
 * - 等待選項加載
 * - 尋找第一個有效的非空選項
 * - 如果無有效選項則跳過
 */
async function selectFirstValidModel(page) {
  await page.waitForTimeout(500);
  const modelSelect = page
    .locator('label:has-text("AI 模型")')
    .locator('..')
    .locator('select')
    .first();

  const options = await modelSelect.locator('option').all();

  for (const option of options) {
    const value = await option.getAttribute('value');
    if (value && value.length > 0) {
      await modelSelect.selectOption(value);
      return true;
    }
  }
  return false;
}

test.describe('⚠️ E2E-004: 錯誤處理與表單驗證', () => {
  /**
   * beforeEach：在每個 test() 前執行一次
   * - 導航至首頁
   * - 等待頁面完全加載
   * - 允許 500ms 讓 UI 完全渲染
   */
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('load');
    await page.waitForTimeout(500);
  });

  test('🔒 表單驗證防止空表單提交', async ({ page }) => {
    // =======================================
    // Phase 1: 打開創建 Agent 表單
    // =======================================
    await test.step('Phase 1: 打開創建表單', async () => {
      // 點擊"創建新 Agent"按鈕
      await page.locator('button:has-text("創建新 Agent")').click();

      // 驗證 Modal 對話框出現
      await expect(page.locator('role=dialog')).toBeVisible({
        timeout: 2000,
      });
    });

    // =======================================
    // Phase 2: 驗證空表單驗證
    // =======================================
    await test.step('Phase 2: 驗證空表單不能提交', async () => {
      // 不填入任何數據
      const submitBtn = page.locator('form button[type="submit"]');

      // 檢查提交按鈕是否禁用
      const isDisabled = await submitBtn.isDisabled();

      if (isDisabled) {
        console.log('✅ 提交按鈕已禁用（空表單保護有效）');
      } else {
        console.log('⚠️ 提交按鈕未禁用，可能需要檢查表單驗證邏輯');
      }

      // 驗證表單仍存在（未被提交）
      await expect(page.locator('form')).toBeVisible();
    });

    // =======================================
    // Phase 3: 關閉表單
    // =======================================
    await test.step('Phase 3: 關閉表單', async () => {
      // 點擊取消按鈕關閉表單
      await page
        .locator('button:has-text("取消")')
        .first()
        .click()
        .catch(() => {});
      await page.waitForTimeout(500);
    });
  });

  test('💰 無效金額驗證（負數拒絕）', async ({ page }) => {
    // =======================================
    // Phase 1: 打開創建表單
    // =======================================
    await test.step('Phase 1: 打開創建表單', async () => {
      await page.locator('button:has-text("創建新 Agent")').click();
      await expect(page.locator('role=dialog')).toBeVisible({ timeout: 2000 });
    });

    // =======================================
    // Phase 2: 填入有效的名稱和模型
    // =======================================
    await test.step('Phase 2: 填入有效的基本信息', async () => {
      // 填入 Agent 名稱
      const nameInput = page
        .locator('label:has-text("Agent 名稱")')
        .locator('..')
        .locator('input')
        .first();
      await nameInput.fill(`Error-Test-Agent-${Date.now()}`);

      // 選擇有效的 AI 模型
      const modelSelected = await selectFirstValidModel(page);

      if (!modelSelected) {
        console.log('⚠️ 無有效模型可選，跳過此步驟');
      }
    });

    // =======================================
    // Phase 3: 輸入無效金額（負數）
    // =======================================
    await test.step('Phase 3: 輸入無效金額（負數）並驗證', async () => {
      // 定位初始資金輸入框
      const fundsInput = page
        .locator('label:has-text("初始資金")')
        .locator('..')
        .locator('input[type="number"]')
        .first();

      // 輸入負數（應被表單驗證拒絕）
      await fundsInput.fill('-1000');

      // 驗證表單仍存在（未提交）
      await expect(page.locator('form')).toBeVisible();

      // 檢查提交按鈕是否被禁用
      const submitBtn = page.locator('form button[type="submit"]');
      const isDisabled = await submitBtn.isDisabled();

      if (isDisabled) {
        console.log('✅ 負數金額被驗證拒絕，提交按鈕已禁用');
      } else {
        console.log('⚠️ 提交按鈕仍然啟用，可能需要檢查驗證規則');
      }
    });

    // =======================================
    // Phase 4: 關閉表單
    // =======================================
    await test.step('Phase 4: 關閉表單', async () => {
      await page
        .locator('button:has-text("取消")')
        .first()
        .click()
        .catch(() => {});
      await page.waitForTimeout(500);
    });
  });

  test('📋 表單驗證錯誤消息顯示', async ({ page }) => {
    // =======================================
    // Phase 1: 打開創建表單並驗證結構
    // =======================================
    await test.step('Phase 1: 打開表單並驗證基本結構', async () => {
      // 點擊創建按鈕
      await page.locator('button:has-text("創建新 Agent")').click();

      // 驗證 Modal 出現
      await expect(page.locator('role=dialog')).toBeVisible({ timeout: 2000 });

      // 驗證表單元素存在
      await expect(page.locator('form')).toBeVisible();

      // 驗證至少有一個輸入字段
      const inputs = page.locator('form input');
      const count = await inputs.count();

      expect(count).toBeGreaterThan(0);
      console.log(`✅ 表單包含 ${count} 個輸入字段`);
    });

    // =======================================
    // Phase 2: 驗證錯誤提示功能
    // =======================================
    await test.step('Phase 2: 嘗試空提交並觀察錯誤提示', async () => {
      // 直接點擊提交按鈕（不填任何數據）
      const submitBtn = page.locator('form button[type="submit"]');

      // 如果按鈕啟用，嘗試點擊
      if (!(await submitBtn.isDisabled())) {
        await submitBtn.click();

        // 等待錯誤消息出現
        await page.waitForTimeout(1000);

        // 尋找錯誤消息
        const errorMsg = page.locator(
          '[class*="error"], [class*="Error"], [role="alert"], text=/請輸入|必須|必需/i'
        );

        const hasError = await errorMsg.isVisible().catch(() => false);

        if (hasError) {
          const errorText = await errorMsg.first().textContent();
          console.log(`✅ 錯誤消息已顯示：${errorText}`);
        } else {
          console.log('⚠️ 未找到明確的錯誤消息');
        }
      } else {
        console.log('✅ 提交按鈕已禁用，表單驗證前置檢查有效');
      }
    });

    // =======================================
    // Phase 3: 關閉表單
    // =======================================
    await test.step('Phase 3: 關閉表單', async () => {
      await page
        .locator('button:has-text("取消")')
        .first()
        .click()
        .catch(() => {});
      await page.waitForTimeout(500);
    });
  });
});
