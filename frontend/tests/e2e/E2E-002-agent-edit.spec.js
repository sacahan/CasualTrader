import { test, expect } from '@playwright/test';

/**
 * E2E-002: Agent 編輯功能
 *
 * 驗證用戶可以編輯現有 Agent 的配置，包括保存變更、取消編輯和表單驗證
 */

test.describe('E2E-002: Agent 編輯功能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('可以編輯 Agent 配置', async ({ page }) => {
    await test.step('查找並編輯現有 Agent', async () => {
      // 等待 Agent 卡片出現
      const agentCard = page.locator('[class*="AgentCard"]').first();
      await expect(agentCard).toBeVisible({ timeout: 3000 });

      // 點擊編輯按鈕或設定菜單
      const editBtn = agentCard.locator('button[class*="edit"]');
      if (await editBtn.isVisible()) {
        await editBtn.click();
      } else {
        // 或點擊設定按鈕打開菜單
        await agentCard.locator('button[class*="settings"]').click();
        await page.waitForTimeout(300);
        await page.locator('button:has-text("編輯")').click();
      }

      // 等待編輯表單出現
      await expect(page.locator('[class*="Modal"], form')).toBeVisible({ timeout: 2000 });
    });

    await test.step('修改配置並保存', async () => {
      // 修改 Agent 名稱
      const nameInput = page.locator('input[name="name"]').first();
      await nameInput.clear();
      await nameInput.fill('Updated Agent Name');

      // 保存更改
      await page.locator('button:has-text("保存"), button[type="submit"]').click();

      // 等待保存完成
      await page.waitForTimeout(2000);

      // 驗證成功消息
      await expect(
        page.locator('[class*="Toast"]:has-text("成功"), [class*="notification"]:has-text("成功")')
      ).toBeVisible({ timeout: 3000 });
    });

    await test.step('驗證變更已保存', async () => {
      // 驗證名稱已更新
      await expect(
        page.locator('[class*="AgentCard"]:has-text("Updated Agent Name")')
      ).toBeVisible();
    });
  });

  test('取消編輯會丟棄變更', async ({ page }) => {
    await test.step('打開編輯並取消', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 打開編輯
      const settingsBtn = agentCard.locator('button[class*="settings"]');
      if (await settingsBtn.isVisible()) {
        await settingsBtn.click();
        await page.waitForTimeout(300);
        await page.locator('button:has-text("編輯")').click();
      }

      // 等待表單
      await expect(page.locator('[class*="Modal"], form')).toBeVisible({ timeout: 2000 });

      // 修改但不保存
      const nameInput = page.locator('input[name="name"]').first();
      const originalName = await nameInput.inputValue();
      await nameInput.clear();
      await nameInput.fill('This will be cancelled');

      // 點擊取消按鈕
      await page.locator('button:has-text("取消")').click();

      // 等待 modal 關閉
      await page.waitForTimeout(500);
    });

    await test.step('驗證名稱未改變', async () => {
      // 應該還是舊名字
      await expect(
        page.locator('[class*="AgentCard"]:has-text("This will be cancelled")')
      ).not.toBeVisible();
    });
  });
});
