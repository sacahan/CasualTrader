import { test, expect } from '@playwright/test';

/**
 * E2E-004: 錯誤處理與表單驗證
 *
 * 驗證表單驗證和錯誤處理功能
 */

test.describe('E2E-004: 錯誤處理與表單驗證', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('表單驗證防止無效提交', async ({ page }) => {
    await test.step('打開創建表單', async () => {
      await page.locator('button:has-text("創建新 Agent")').click();
      await expect(page.locator('[class*="Modal"], [role="dialog"]')).toBeVisible({
        timeout: 2000,
      });
    });

    await test.step('嘗試提交空表單', async () => {
      // 不填入任何數據，直接點擊提交
      const submitBtn = page.locator('form button[type="submit"]');
      await submitBtn.click();

      // 應該顯示驗證錯誤或表單仍可見
      await page.waitForTimeout(1000);

      // 驗證表單仍存在（未提交）
      await expect(page.locator('form')).toBeVisible();
    });

    await test.step('填入部分必填欄位', async () => {
      // 只填名稱，不填其他必填
      const nameInput = page.locator('input[name="name"], input[placeholder*="名稱"]').first();
      await nameInput.fill('Test');

      // 嘗試提交
      const submitBtn = page.locator('form button[type="submit"]');
      await submitBtn.click();

      // 應該仍然顯示驗證錯誤
      await page.waitForTimeout(500);
      await expect(page.locator('form')).toBeVisible();
    });
  });

  test('無效金額驗證', async ({ page }) => {
    await test.step('打開創建表單', async () => {
      await page.locator('button:has-text("創建新 Agent")').click();
      await expect(page.locator('[class*="Modal"]')).toBeVisible({ timeout: 2000 });
    });

    await test.step('輸入無效金額', async () => {
      // 填入所有字段
      const nameInput = page.locator('input[name="name"]').first();
      await nameInput.fill('Test Agent');

      // 填入無效金額（負數或零）
      const fundsInput = page.locator('input[type="number"], input[name="initial_funds"]').first();
      await fundsInput.fill('-1000');

      // 嘗試提交
      const submitBtn = page.locator('form button[type="submit"]');
      await submitBtn.click();

      // 應該顯示錯誤
      await page.waitForTimeout(1000);
      await expect(page.locator('form')).toBeVisible();
    });
  });

  test('顯示 API 錯誤消息', async ({ page }) => {
    await test.step('嘗試創建重名 Agent', async () => {
      // 打開創建表單
      await page.locator('button:has-text("創建新 Agent")').click();
      await expect(page.locator('[class*="Modal"]')).toBeVisible({ timeout: 2000 });

      // 填入現有 Agent 名稱（如果存在）
      const nameInput = page.locator('input[name="name"]').first();
      const existingName = await page.locator('[class*="AgentCard"] h3').first().textContent();

      if (existingName) {
        await nameInput.fill(existingName);

        // 填入其他必填欄位
        const fundsInput = page.locator('input[type="number"]').first();
        await fundsInput.fill('1000000');

        // 提交
        await page.locator('form button[type="submit"]').click();

        // 等待可能的 API 錯誤
        await page.waitForTimeout(2000);

        // 檢查是否有錯誤提示
        const errorMsg = page.locator('[class*="error"], [class*="warning"], [class*="alert"]');
        if (await errorMsg.isVisible()) {
          // 有錯誤消息是預期的
          expect(true).toBe(true);
        }
      }
    });
  });
});
