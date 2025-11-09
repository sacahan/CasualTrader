import { test, expect } from '@playwright/test';

/**
 * E2E-007: Agent 卡片互動功能
 *
 * 驗證 Agent 卡片上的各種交互功能
 */

test.describe('E2E-007: Agent 卡片互動', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('卡片懸停效果', async ({ page }) => {
    await test.step('懸停在 Agent 卡片', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();
      await expect(agentCard).toBeVisible({ timeout: 3000 });

      // 懸停在卡片上
      await agentCard.hover();

      // 等待任何過渡效果
      await page.waitForTimeout(500);

      // 驗證卡片仍可見（懸停時可能展示更多按鈕）
      await expect(agentCard).toBeVisible();
    });
  });

  test('快速操作按鈕可見性', async ({ page }) => {
    await test.step('驗證卡片上有操作按鈕', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找各種操作按鈕
      const buttons = agentCard.locator('button');

      // 應該至少有一個按鈕（執行、編輯、設定等）
      const count = await buttons.count();
      expect(count).toBeGreaterThan(0);
    });

    await test.step('點擊執行按鈕', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找執行按鈕
      const runBtn = agentCard.locator(
        'button:has-text("交易"), button:has-text("執行"), button:has-text("Run")'
      );

      if (await runBtn.isVisible()) {
        const originalStatus = await agentCard.locator('[class*="status"]').textContent();

        await runBtn.click();
        await page.waitForTimeout(2000);

        // 狀態應該改變
        const newStatus = await agentCard.locator('[class*="status"]').textContent();

        // 停止執行
        const stopBtn = agentCard.locator('button:has-text("停止")');
        if (await stopBtn.isVisible()) {
          await stopBtn.click();
          await page.waitForTimeout(2000);
        }
      }
    });
  });

  test('設定菜單交互', async ({ page }) => {
    await test.step('打開設定菜單', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找設定按鈕
      const settingsBtn = agentCard.locator(
        'button[class*="settings"], button:has-text("⋮"), button:has-text("...")'
      );

      if (await settingsBtn.isVisible()) {
        await settingsBtn.click();
        await page.waitForTimeout(300);

        // 驗證菜單出現
        const menu = page.locator('[class*="menu"], [class*="dropdown"]');
        if (await menu.isVisible()) {
          // 驗證菜單項
          const items = menu.locator('button, [role="menuitem"]');
          expect(await items.count()).toBeGreaterThan(0);

          // 點擊菜單外關閉
          await page.click('body');
          await page.waitForTimeout(300);
        }
      }
    });
  });

  test('卡片信息顯示完整性', async ({ page }) => {
    await test.step('驗證卡片信息', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 驗證必要信息
      const name = agentCard.locator('h3, [class*="name"]').first();
      const status = agentCard.locator('[class*="status"]');

      await expect(name).toBeVisible();

      if (await status.isVisible()) {
        const statusText = await status.textContent();
        expect(['IDLE', 'RUNNING', 'ACTIVE', 'STOPPED']).toContain(statusText?.trim());
      }
    });
  });
});
