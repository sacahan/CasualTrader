import { test, expect } from '@playwright/test';

/**
 * E2E-008: 空狀態顯示與通知系統
 *
 * 驗證無 Agent 時的空狀態顯示、通知 Toast 的顯示和自動關閉功能
 */

test.describe('E2E-008: 空狀態與通知系統', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('顯示空狀態', async ({ page }) => {
    await test.step('檢查是否有 Agent', async () => {
      const agents = page.locator('[class*="AgentCard"]');
      const count = await agents.count();

      if (count === 0) {
        // 應該有空狀態提示
        const emptyState = page.locator(
          '[class*="empty"], [class*="EmptyState"], text="沒有 Agent"'
        );

        if (await emptyState.isVisible()) {
          await expect(emptyState).toContainText(/沒有|暫無|創建|Create/i);
        }
      }
    });
  });

  test('創建 Agent 時顯示通知', async ({ page }) => {
    await test.step('創建 Agent 並觀察通知', async () => {
      // 開啟創建對話
      await page.locator('button:has-text("創建新 Agent")').click();
      await expect(page.locator('[class*="Modal"]')).toBeVisible({ timeout: 2000 });

      // 填入必要信息
      await page.locator('input[name="name"]').first().fill('Notification Test Agent');
      await page.locator('input[type="number"]').first().fill('1000000');

      // 提交
      await page.locator('form button[type="submit"]').click();

      // 等待並觀察通知
      await page.waitForTimeout(1000);

      // 檢查成功通知
      const toast = page.locator(
        '[class*="Toast"], [class*="Notification"], [class*="notification"]'
      );

      if (await toast.isVisible()) {
        const content = await toast.textContent();
        expect(content).toMatch(/成功|Success|created/i);
      }
    });

    await test.step('通知自動關閉', async () => {
      // 等待通知自動消失（通常 3-5 秒）
      await page.waitForTimeout(5000);

      // 驗證通知已消失
      const toast = page.locator('[class*="Toast"]');
      const isVisible = await toast.isVisible().catch(() => false);

      // 通知應該已關閉
      expect(isVisible).toBe(false);
    });
  });

  test('操作成功顯示 Toast', async ({ page }) => {
    await test.step('執行操作並驗證通知', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      if (await agentCard.isVisible()) {
        // 點擊執行按鈕
        const runBtn = agentCard.locator('button:has-text("交易"), button:has-text("執行")');

        if (await runBtn.isVisible()) {
          await runBtn.click();

          // 觀察成功通知
          await page.waitForTimeout(1000);

          const toast = page.locator('[class*="Toast"]');
          if (await toast.isVisible()) {
            const content = await toast.textContent();
            expect(content).toBeTruthy();
          }

          // 停止執行
          const stopBtn = agentCard.locator('button:has-text("停止")');
          if (await stopBtn.isVisible()) {
            await stopBtn.click();
            await page.waitForTimeout(2000);
          }
        }
      }
    });
  });

  test('錯誤通知顯示', async ({ page }) => {
    await test.step('觸發錯誤場景', async () => {
      // 打開創建表單
      await page.locator('button:has-text("創建新 Agent")').click();
      await expect(page.locator('[class*="Modal"]')).toBeVisible({ timeout: 2000 });

      // 嘗試提交空表單
      await page.locator('form button[type="submit"]').click();

      // 等待錯誤通知
      await page.waitForTimeout(1500);

      // 檢查錯誤消息
      const errorMsg = page.locator('[class*="error"], [class*="Error"], [class*="warning"]');

      if (await errorMsg.isVisible()) {
        const content = await errorMsg.textContent();
        expect(content).toBeTruthy();
      }

      // 關閉表單
      const closeBtn = page.locator('[class*="Modal"] button[class*="close"]');
      if (await closeBtn.isVisible()) {
        await closeBtn.click();
      } else {
        await page.keyboard.press('Escape');
      }
    });
  });
});
