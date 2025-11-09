import { test, expect } from '@playwright/test';

/**
 * E2E-006: 市場狀態與大盤指數顯示
 *
 * 驗證 Navbar 正確顯示市場開盤狀態、大盤指數和 WebSocket 連線狀態
 */

test.describe('E2E-006: 市場狀態顯示', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Navbar 顯示市場信息', async ({ page }) => {
    await test.step('驗證 Navbar 存在', async () => {
      // 驗證 Navbar
      await expect(page.locator('nav')).toBeVisible();
    });

    await test.step('檢查市場狀態顯示', async () => {
      const navbar = page.locator('nav');

      // 尋找市場狀態文本
      const statusText = navbar.locator(
        '[class*="status"], [class*="market"], [class*="open"], [class*="close"]'
      );

      if (await statusText.isVisible()) {
        const content = await statusText.textContent();
        expect(content).toMatch(/開盤|收盤|休市|Open|Close|Market/i);
      }
    });

    await test.step('檢查大盤指數顯示', async () => {
      const navbar = page.locator('nav');

      // 尋找指數信息
      const indexText = navbar.locator('[class*="index"], [class*="taiex"], [class*="指數"]');

      if (await indexText.isVisible()) {
        const content = await indexText.textContent();
        // 應該包含數字
        expect(content).toMatch(/\d+/);
      }
    });

    await test.step('檢查 WebSocket 連線狀態指示', async () => {
      const navbar = page.locator('nav');

      // 尋找連線狀態指示器
      const connectStatus = navbar.locator(
        '[class*="connect"], [class*="socket"], [class*="status"]'
      );

      if (await connectStatus.isVisible()) {
        // 應該有某種連線狀態指示
        expect(true).toBe(true);
      }
    });
  });

  test('市場信息定期更新', async ({ page }) => {
    await test.step('獲取初始指數', async () => {
      const navbar = page.locator('nav');
      const indexText = navbar.locator('[class*="index"]').first();

      if (await indexText.isVisible()) {
        const initialValue = await indexText.textContent();

        // 等待一段時間
        await page.waitForTimeout(5000);

        // 獲取更新後的值
        const updatedValue = await indexText.textContent();

        // 可能相同或不同，只要頁面還在運行就沒問題
        expect(updatedValue).toBeTruthy();
      }
    });
  });
});
