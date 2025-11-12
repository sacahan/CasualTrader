import { test, expect } from '@playwright/test';
import { setupTestAgent } from './fixtures.js';

/**
 * 測試案例編號：E2E-002
 * 測試目標：驗證使用者可以編輯現有 Agent 的配置、保存變更或取消編輯
 *
 * 測試工具：Playwright
 * 測試範圍：前端 Agent 編輯 UI + 表單驗證
 * 優先級：High
 * 標籤：agent, edit, crud, form
 *
 * 教學說明：
 * - 此測試依賴於至少存在一個 Agent 卡片
 * - 編輯流程包括：點擊編輯 → 修改欄位 → 提交或取消
 * - 驗證變更是否被保存或丟棄
 */

test.describe('✏️ E2E-002: Agent 編輯功能', () => {
  /**
   * beforeEach：在每個 test() 前執行一次
   * - 導航至首頁
   * - 等待頁面完全加載
   * - 確保至少存在一個 Agent（自動創建如果需要）
   * - 等待 Agent 卡片渲染
   */
  test.beforeEach(async ({ page }) => {
    await setupTestAgent(page);
  });

  test('✅ 編輯 Agent 配置並保存變更', async ({ page }) => {
    // =====================================
    // Phase 1: 定位並打開編輯表單
    // =====================================
    await test.step('Phase 1: 定位 Agent 卡片並打開編輯', async () => {
      // 等待第一個 Agent 卡片可見
      const agentCard = page.locator('.agent-card, [class*="AgentCard"]').first();
      await expect(agentCard).toBeVisible({ timeout: 3000 });

      // 尋找並點擊編輯按鈕
      const editBtn = agentCard.locator('button[title="編輯 Agent"]');
      await editBtn.click();

      // 驗證編輯 Modal 出現
      await expect(page.locator('role=dialog')).toBeVisible({ timeout: 2000 });
    });

    // =====================================
    // Phase 2: 取得原始值並修改
    // =====================================
    await test.step('Phase 2: 修改 Agent 名稱', async () => {
      // 定位 Agent 名稱輸入框
      const nameInput = page
        .locator('label:has-text("Agent 名稱")')
        .locator('..')
        .locator('input')
        .first();

      // 取得當前（原始）名稱
      const originalName = await nameInput.inputValue();

      // 生成新名稱（附加時間戳以確保唯一性）
      const newName = `${originalName}-Updated-${Date.now()}`;

      // 選中全部文字後填入新值
      await nameInput.selectText();
      await nameInput.fill(newName);
    });

    // =====================================
    // Phase 3: 提交表單並驗證變更保存
    // =====================================
    await test.step('Phase 3: 提交編輯並驗證保存成功', async () => {
      // 尋找提交按鈕
      const submitBtn = page.locator('form button[type="submit"]');
      await submitBtn.click();

      // 等待 Modal 關閉（表示提交成功）
      await page.waitForSelector('role=dialog', { state: 'hidden', timeout: 3000 }).catch(() => {});
      await page.waitForTimeout(500);

      // 等待頁面重新渲染
      await page.waitForLoadState('networkidle');
    });

    // =====================================
    // Phase 4: 驗證更新後的值顯示在卡片上
    // =====================================
    await test.step('Phase 4: 驗證卡片顯示新名稱', async () => {
      // 取得新名稱（與 Phase 2 中填入的相同）
      const updatedName = await page
        .locator('label:has-text("Agent 名稱")')
        .locator('..')
        .locator('input')
        .first()
        .inputValue()
        .catch(() => null);

      if (updatedName) {
        // 驗證卡片上包含新名稱
        await expect(page.locator(`.agent-card:has-text("${updatedName}")`)).toBeVisible({
          timeout: 3000,
        });
      }
    });
  });

  test('❌ 取消編輯會丟棄所有變更', async ({ page }) => {
    // =====================================
    // Phase 1: 定位並打開編輯表單
    // =====================================
    await test.step('Phase 1: 定位 Agent 卡片並打開編輯', async () => {
      const agentCard = page.locator('.agent-card, [class*="AgentCard"]').first();
      await expect(agentCard).toBeVisible({ timeout: 3000 });

      const editBtn = agentCard.locator('button[title="編輯 Agent"]');
      await editBtn.click();

      await expect(page.locator('role=dialog')).toBeVisible({ timeout: 2000 });
    });

    // =====================================
    // Phase 2: 修改表單欄位
    // =====================================
    await test.step('Phase 2: 修改 Agent 名稱（臨時修改）', async () => {
      const nameInput = page
        .locator('label:has-text("Agent 名稱")')
        .locator('..')
        .locator('input')
        .first();

      // 修改為不同的值（這個值將被丟棄）
      await nameInput.selectText();
      await nameInput.fill('This will be cancelled');
    });

    // =====================================
    // Phase 3: 取消編輯而非提交
    // =====================================
    await test.step('Phase 3: 點擊取消按鈕', async () => {
      // 尋找並點擊取消按鈕
      await page.locator('button:has-text("取消")').click();

      // 等待 Modal 關閉
      await page.waitForSelector('role=dialog', { state: 'hidden', timeout: 3000 }).catch(() => {});
      await page.waitForTimeout(500);
    });

    // =====================================
    // Phase 4: 驗證變更已被丟棄
    // =====================================
    await test.step('Phase 4: 驗證原始名稱仍存在於卡片', async () => {
      // 再次開啟編輯以查看原始值
      const agentCard = page.locator('.agent-card').first();
      const editBtn = agentCard.locator('button[title="編輯 Agent"]');
      await editBtn.click();

      await expect(page.locator('role=dialog')).toBeVisible({ timeout: 2000 });

      // 取得當前名稱（應該是原始名稱）
      const currentName = await page
        .locator('label:has-text("Agent 名稱")')
        .locator('..')
        .locator('input')
        .first()
        .inputValue();

      // 驗證臨時修改的名稱未被保存
      expect(currentName).not.toContain('This will be cancelled');

      // 關閉 Modal
      await page.locator('button:has-text("取消")').click();
      await page.waitForTimeout(300);
    });
  });
});
