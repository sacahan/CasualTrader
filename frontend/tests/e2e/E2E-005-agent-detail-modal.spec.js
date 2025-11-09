import { test, expect } from '@playwright/test';

/**
 * E2E-005: Agent 詳情彈窗
 *
 * 驗證 Agent 詳細資訊 Modal 的顯示和功能
 */

test.describe('E2E-005: Agent 詳情彈窗', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('顯示 Agent 詳情 Modal', async ({ page }) => {
    await test.step('打開詳情 Modal', async () => {
      // 等待 Agent 卡片
      const agentCard = page.locator('[class*="AgentCard"]').first();
      await expect(agentCard).toBeVisible({ timeout: 3000 });

      // 點擊卡片打開詳情
      await agentCard.click();

      // 等待 Modal 出現
      await expect(page.locator('[class*="Modal"], [class*="Detail"]')).toBeVisible({
        timeout: 2000,
      });
    });

    await test.step('驗證詳情信息', async () => {
      const modal = page.locator('[class*="Modal"], [class*="Detail"]').first();

      // 驗證 Agent 名稱
      await expect(modal.locator('h1, h2, h3').first()).toBeVisible();

      // 驗證 Agent 信息（狀態、資金等）
      const content = await modal.textContent();
      expect(content).toBeTruthy();
    });

    await test.step('關閉 Modal', async () => {
      // 尋找關閉按鈕
      const closeBtn = page
        .locator(
          '[class*="Modal"] button[class*="close"], button:has-text("✕"), button:has-text("×")'
        )
        .first();

      if (await closeBtn.isVisible()) {
        await closeBtn.click();
      } else {
        // 按 Esc 鍵
        await page.keyboard.press('Escape');
      }

      // 驗證 Modal 已關閉
      await expect(page.locator('[class*="Modal"]')).not.toBeVisible({ timeout: 2000 });
    });
  });

  test('從詳情 Modal 編輯 Agent', async ({ page }) => {
    await test.step('打開詳情並尋找編輯按鈕', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();
      await agentCard.click();

      // 等待 Modal
      const modal = page.locator('[class*="Modal"]').first();
      await expect(modal).toBeVisible({ timeout: 2000 });

      // 尋找編輯按鈕
      const editBtn = modal.locator('button:has-text("編輯")');

      if (await editBtn.isVisible()) {
        await editBtn.click();
        await page.waitForTimeout(500);

        // 驗證編輯表單出現
        await expect(page.locator('form')).toBeVisible();
      }
    });
  });
});
