import { test, expect } from '@playwright/test';

/**
 * E2E-001: Agent 創建與執行完整流程
 *
 * 驗證用戶可以通過前端介面完成 Agent 創建、執行 TRADING 模式、停止執行和刪除 Agent 的完整流程
 *
 * Priority: Critical
 * Tags: agent, creation, trading, crud, core
 */

const TEST_DATA = {
  agentName: 'E2E Test Agent',
  model: 'gpt-4o-mini',
  initialFunds: '1000000',
  investmentPrefs: '2330,2454,2317',
  systemPrompt: '你是一個穩健的價值投資者,專注於台股大型權值股的長期投資。',
};

test.describe('E2E-001: Agent 創建與執行完整流程', () => {
  test.beforeEach(async ({ page }) => {
    // 導航到首頁
    await page.goto('/');
    // 等待頁面載入
    await page.waitForLoadState('networkidle');
  });

  test('Agent 創建、執行和刪除的完整流程', async ({ page }) => {
    // Phase 1: 頁面初始化檢查
    await test.step('Phase 1: 驗證首頁載入', async () => {
      // 驗證頁面標題
      await expect(page).toHaveTitle(/Casual Trader/i);

      // 驗證主標題
      const heading = page.locator('h1').first();
      await expect(heading).toBeVisible();

      // 驗證 Navbar
      await expect(page.locator('nav')).toBeVisible();

      // 驗證創建按鈕
      await expect(page.locator('button:has-text("創建新 Agent")')).toBeVisible();
    });

    // Phase 2: 開啟創建 Agent 表單
    await test.step('Phase 2: 開啟創建 Agent 表單', async () => {
      // 點擊創建按鈕
      await page.locator('button:has-text("創建新 Agent")').click();

      // 等待 Modal 出現
      await expect(page.locator('[class*="Modal"], [role="dialog"]')).toBeVisible({
        timeout: 2000,
      });

      // 驗證表單欄位存在
      await expect(page.locator('input[name="name"], input[placeholder*="名稱"]')).toBeVisible();
      await expect(page.locator('select[name="model"], select')).toBeVisible();
      await expect(page.locator('input[type="number"]')).toBeVisible();
    });

    // Phase 3: 填寫表單
    await test.step('Phase 3: 填寫 Agent 創建表單', async () => {
      // 填寫名稱
      await page
        .locator('input[name="name"], input[placeholder*="名稱"]')
        .fill(TEST_DATA.agentName);

      // 選擇模型
      const modelSelect = page.locator('select[name="model"], select').first();
      await modelSelect.selectOption(TEST_DATA.model);

      // 填寫初始資金
      await page
        .locator('input[type="number"], input[name="initial_funds"]')
        .fill(TEST_DATA.initialFunds);

      // 填寫投資偏好
      const investmentInput = page
        .locator('input[name="investment_preferences"], textarea[name="investment_preferences"]')
        .first();
      await investmentInput.fill(TEST_DATA.investmentPrefs);

      // 填寫系統提示詞
      await page.locator('textarea[name="system_prompt"]').fill(TEST_DATA.systemPrompt);
    });

    // Phase 4: 提交表單
    await test.step('Phase 4: 提交表單並驗證創建', async () => {
      // 提交表單
      await page.locator('form button[type="submit"]').click();

      // 等待 API 請求完成
      await page.waitForTimeout(3000);

      // 驗證成功通知
      await expect(
        page.locator('[class*="NotificationToast"], [class*="toast"]:has-text("成功")')
      ).toBeVisible({ timeout: 3000 });
    });

    // Phase 5: 驗證 Agent 卡片顯示
    await test.step('Phase 5: 驗證 Agent 卡片顯示', async () => {
      // 等待 Agent 卡片
      await expect(page.locator('[class*="AgentCard"]')).toBeVisible({ timeout: 2000 });

      // 驗證 Agent 名稱
      await expect(
        page.locator(`[class*="AgentCard"]:has-text("${TEST_DATA.agentName}")`)
      ).toBeVisible();

      // 驗證初始狀態為 IDLE
      const agentCard = page.locator(`[class*="AgentCard"]:has-text("${TEST_DATA.agentName}")`);
      await expect(agentCard.locator('[class*="status"]')).toContainText('IDLE');
    });

    // Phase 6: 查看 Agent 詳情
    await test.step('Phase 6: 查看 Agent 詳情', async () => {
      // 點擊 Agent 卡片
      await page.locator(`[class*="AgentCard"]:has-text("${TEST_DATA.agentName}")`).click();

      // 等待詳情 Modal
      await expect(page.locator('[class*="AgentDetailModal"]')).toBeVisible({ timeout: 1000 });

      // 關閉詳情 Modal
      const closeBtn = page.locator('[class*="AgentDetailModal"] button[class*="close"]');
      if (await closeBtn.isVisible()) {
        await closeBtn.click();
      } else {
        // 或按 Esc 鍵
        await page.keyboard.press('Escape');
      }
    });

    // Phase 7: 執行 Trading 模式
    await test.step('Phase 7: 執行 TRADING 模式', async () => {
      // 設置網路監聽（可選）
      const responsePromise = page
        .waitForResponse(
          (response) =>
            response.url().includes('/api/agents') && response.request().method() === 'POST'
        )
        .catch(() => null); // 忽略超時

      // 點擊交易按鈕
      const agentCard = page.locator(`[class*="AgentCard"]:has-text("${TEST_DATA.agentName}")`);
      await agentCard.locator('button:has-text("交易")').click();

      // 等待執行
      await page.waitForTimeout(3000);

      // 驗證狀態變更為 RUNNING
      await expect(agentCard.locator('[class*="status"]')).toContainText('RUNNING', {
        timeout: 5000,
      });
    });

    // Phase 8: 停止執行
    await test.step('Phase 8: 停止 Agent 執行', async () => {
      // 點擊停止按鈕
      const agentCard = page.locator(`[class*="AgentCard"]:has-text("${TEST_DATA.agentName}")`);
      const stopBtn = agentCard.locator('button:has-text("停止")');

      if (await stopBtn.isVisible()) {
        await stopBtn.click();
      }

      // 等待停止完成
      await page.waitForTimeout(3000);

      // 驗證狀態回到 IDLE
      await expect(agentCard.locator('[class*="status"]')).toContainText('IDLE', { timeout: 5000 });
    });

    // Phase 9: 刪除 Agent
    await test.step('Phase 9: 刪除測試 Agent', async () => {
      const agentCard = page.locator(`[class*="AgentCard"]:has-text("${TEST_DATA.agentName}")`);

      // 點擊設定按鈕
      const settingsBtn = agentCard.locator('button[class*="settings"]');
      if (await settingsBtn.isVisible()) {
        await settingsBtn.click();
        await page.waitForTimeout(500);
      }

      // 點擊刪除選項
      await page.locator('button:has-text("刪除")').click();
      await page.waitForTimeout(500);

      // 確認刪除
      await page.locator('button:has-text("確定")').click();

      // 等待刪除完成
      await page.waitForTimeout(3000);

      // 驗證 Agent 已移除
      await expect(
        page.locator(`[class*="AgentCard"]:has-text("${TEST_DATA.agentName}")`)
      ).not.toBeVisible({ timeout: 5000 });
    });
  });
});
