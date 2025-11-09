import { test, expect } from '@playwright/test';

/**
 * E2E-003: Rebalancing 模式執行
 *
 * 驗證用戶能夠選擇和執行 REBALANCING 模式
 */

test.describe('E2E-003: Rebalancing 模式', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('執行 Rebalancing 模式', async ({ page }) => {
    await test.step('選擇 Rebalancing 模式', async () => {
      // 找到 Agent 卡片
      const agentCard = page.locator('[class*="AgentCard"]').first();
      await expect(agentCard).toBeVisible({ timeout: 3000 });

      // 尋找再平衡/Rebalancing 按鈕
      const rebalanceBtn = agentCard.locator(
        'button:has-text("再平衡"), button:has-text("Rebalancing"), button:has-text("平衡")'
      );

      if (await rebalanceBtn.isVisible()) {
        await rebalanceBtn.click();
      } else {
        // 可能在下拉菜單中
        const moreBtn = agentCard.locator('button[class*="more"]');
        if (await moreBtn.isVisible()) {
          await moreBtn.click();
          await page.waitForTimeout(300);
          await page.locator('button:has-text("再平衡"), button:has-text("Rebalancing")').click();
        }
      }

      // 等待執行
      await page.waitForTimeout(3000);
    });

    await test.step('驗證執行狀態', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 檢查狀態是否變更為 RUNNING
      const status = agentCard.locator('[class*="status"]');
      const statusText = await status.textContent();

      // 應該是 RUNNING 或 ACTIVE 狀態
      expect(['RUNNING', 'ACTIVE']).toContain(statusText?.trim() || '');
    });

    await test.step('停止 Rebalancing', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();
      const stopBtn = agentCard.locator('button:has-text("停止")');

      if (await stopBtn.isVisible()) {
        await stopBtn.click();
        await page.waitForTimeout(2000);
      }

      // 驗證狀態回到 IDLE
      await expect(agentCard.locator('[class*="status"]')).toContainText('IDLE', { timeout: 5000 });
    });
  });
});
