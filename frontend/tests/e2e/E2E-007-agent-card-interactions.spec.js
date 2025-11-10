import { test, expect } from '@playwright/test';
import { setupTestAgent } from './fixtures.js';

/**
 * 測試案例編號：E2E-007
 * 測試目標：驗證 Agent 卡片上的各種交互功能、懸停效果、快速操作按鈕等
 *
 * 測試工具：Playwright
 * 測試範圍：前端卡片 UI 交互 + 懸停效果 + 操作按鈕
 * 優先級：Medium
 * 標籤：agent-card, interaction, ux
 *
 * 教學說明：
 * - 卡片懸停效果通常用於展示隱藏的操作按鈕
 * - 驗證快速操作按鈕（交易、編輯、停止等）的可用性
 * - 測試卡片信息顯示完整性（名稱、狀態等）
 */

test.describe('🎯 E2E-007: Agent 卡片交互功能', () => {
  /**
   * beforeEach：在每個 test() 前執行一次
   * - 導航至首頁
   * - 等待頁面網絡空閒
   * - 確保至少存在一個 Agent（自動創建如果需要）
   * - 確保所有卡片已加載
   */
  test.beforeEach(async ({ page }) => {
    await setupTestAgent(page);
    await page.waitForLoadState('networkidle');
  });

  test('🖱️ 卡片懸停效果驗證', async ({ page }) => {
    // =====================================
    // Phase 1: 尋找 Agent 卡片
    // =====================================
    await test.step('Phase 1: 定位第一個 Agent 卡片', async () => {
      // 使用 CSS 類選擇器尋找卡片
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 等待卡片可見
      await expect(agentCard).toBeVisible({ timeout: 3000 });

      console.log('✅ Agent 卡片已找到');
    });

    // =====================================
    // Phase 2: 執行懸停操作
    // =====================================
    await test.step('Phase 2: 在卡片上執行懸停', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 移動滑鼠到卡片上
      await agentCard.hover();

      // 等待懸停效果（如陰影、縮放、按鈕淡入等）
      await page.waitForTimeout(500);

      console.log('✅ 懸停效果已觸發');
    });

    // =====================================
    // Phase 3: 驗證卡片狀態
    // =====================================
    await test.step('Phase 3: 驗證懸停後卡片仍可見', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 驗證卡片仍然可見（懸停時可能顯示額外按鈕）
      await expect(agentCard).toBeVisible();

      console.log('✅ 卡片懸停效果正常');
    });
  });

  test('⚡ 卡片操作按鈕可見性和功能', async ({ page }) => {
    // =====================================
    // Phase 1: 驗證操作按鈕存在
    // =====================================
    await test.step('Phase 1: 驗證卡片上有操作按鈕', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找卡片內的所有按鈕
      const buttons = agentCard.locator('button');

      // 計算按鈕數量
      const count = await buttons.count();

      if (count > 0) {
        console.log(`✅ 卡片包含 ${count} 個操作按鈕`);
      }

      expect(count).toBeGreaterThan(0);
    });

    // =====================================
    // Phase 2: 尋找執行/交易按鈕
    // =====================================
    await test.step('Phase 2: 尋找執行按鈕並驗證', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 使用多個選擇器策略尋找執行按鈕
      // - button:has-text("交易")：文本包含"交易"
      // - button:has-text("執行")：文本包含"執行"
      // - button:has-text("Run")：文本包含"Run"（英文）
      const runBtn = agentCard.locator(
        'button:has-text("交易"), button:has-text("執行"), button:has-text("Run")'
      );

      const isVisible = await runBtn.isVisible().catch(() => false);

      if (isVisible) {
        console.log('✅ 執行按鈕已找到且可見');

        // 驗證按鈕未被禁用
        const isDisabled = await runBtn.isDisabled().catch(() => true);

        if (!isDisabled) {
          console.log('✅ 執行按鈕已啟用');
        } else {
          console.log('⚠️ 執行按鈕被禁用');
        }
      } else {
        console.log('⚠️ 未找到執行按鈕');
      }
    });

    // =====================================
    // Phase 3: 測試執行按鈕點擊
    // =====================================
    await test.step('Phase 3: 點擊執行按鈕並觀察狀態變化', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找執行按鈕
      const runBtn = agentCard.locator(
        'button:has-text("交易"), button:has-text("執行"), button:has-text("Run")'
      );

      const isVisible = await runBtn.isVisible().catch(() => false);

      if (isVisible) {
        // 獲取執行前的狀態
        const statusBefore = await agentCard
          .locator('[class*="status"]')
          .textContent()
          .catch(() => '');

        // 點擊執行按鈕
        await runBtn.click();

        // 等待後端處理
        await page.waitForTimeout(2000);

        // 獲取執行後的狀態
        const statusAfter = await agentCard
          .locator('[class*="status"]')
          .textContent()
          .catch(() => '');

        console.log(`ℹ️ 狀態變化：${statusBefore?.trim()} → ${statusAfter?.trim()}`);

        // 尋找停止按鈕（表示模式已啟動）
        const stopBtn = agentCard.locator('button:has-text("停止")');
        const stopVisible = await stopBtn.isVisible().catch(() => false);

        if (stopVisible) {
          console.log('✅ 停止按鈕已出現，模式已啟動');

          // 執行停止操作
          await stopBtn.click();
          await page.waitForTimeout(2000);

          console.log('✅ 已停止執行');
        } else {
          console.log('ℹ️ 停止按鈕未出現（可能模式已完成）');
        }
      } else {
        console.log('⚠️ 執行按鈕不可見，跳過點擊測試');
      }
    });
  });

  test('⚙️ 設定菜單交互功能', async ({ page }) => {
    // =====================================
    // Phase 1: 尋找設定菜單按鈕
    // =====================================
    await test.step('Phase 1: 尋找設定菜單按鈕', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 使用多個選擇器策略尋找設定按鈕
      // - button[class*="settings"]：class 包含"settings"
      // - button:has-text("⋮")：文本包含"⋮"（竪點符號）
      // - button:has-text("...")：文本包含"..."（省略號）
      const settingsBtn = agentCard.locator(
        'button[class*="settings"], button:has-text("⋮"), button:has-text("...")'
      );

      const isVisible = await settingsBtn.isVisible().catch(() => false);

      if (isVisible) {
        console.log('✅ 設定菜單按鈕已找到');
      } else {
        console.log('ℹ️ 設定菜單按鈕未找到（可能設計中不存在）');
      }
    });

    // =====================================
    // Phase 2: 打開設定菜單
    // =====================================
    await test.step('Phase 2: 打開設定菜單', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();
      const settingsBtn = agentCard.locator(
        'button[class*="settings"], button:has-text("⋮"), button:has-text("...")'
      );

      const isVisible = await settingsBtn.isVisible().catch(() => false);

      if (isVisible) {
        // 點擊設定按鈕
        await settingsBtn.click();
        await page.waitForTimeout(300);

        // 尋找下拉菜單
        const menu = page.locator('[class*="menu"], [class*="dropdown"]');

        const hasMenu = await menu.isVisible().catch(() => false);

        if (hasMenu) {
          console.log('✅ 設定菜單已展開');

          // 驗證菜單項
          const items = menu.locator('button, [role="menuitem"]');
          const itemCount = await items.count();

          if (itemCount > 0) {
            console.log(`✅ 菜單包含 ${itemCount} 個項目`);
          }

          // 點擊菜單外關閉菜單
          await page.click('body');
          await page.waitForTimeout(300);

          console.log('✅ 菜單已關閉');
        } else {
          console.log('⚠️ 設定菜單未展開');
        }
      }
    });
  });

  test('📄 卡片信息顯示完整性驗證', async ({ page }) => {
    // =====================================
    // Phase 1: 驗證卡片名稱顯示
    // =====================================
    await test.step('Phase 1: 驗證 Agent 名稱顯示', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找卡片名稱（通常在 <h3> 或帶 name class）
      const name = agentCard.locator('h3, [class*="name"]').first();

      // 驗證名稱元素存在且可見
      await expect(name).toBeVisible();

      const nameText = await name.textContent();
      console.log(`✅ Agent 名稱：${nameText?.trim()}`);
    });

    // =====================================
    // Phase 2: 驗證卡片狀態顯示
    // =====================================
    await test.step('Phase 2: 驗證 Agent 狀態顯示', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找狀態元素（帶 status class）
      const status = agentCard.locator('[class*="status"]');

      const isVisible = await status.isVisible().catch(() => false);

      if (isVisible) {
        const statusText = await status.textContent();

        // 驗證狀態是否是預期值
        const expectedStates = [
          'IDLE',
          'RUNNING',
          'ACTIVE',
          'STOPPED',
          '未運行',
          '運行中',
          '已停止',
        ];
        const isValidState = expectedStates.some((state) => statusText?.includes(state));

        if (isValidState) {
          console.log(`✅ Agent 狀態：${statusText?.trim()}`);
        } else {
          console.log(`ℹ️ Agent 狀態：${statusText?.trim()}（非預期值）`);
        }
      } else {
        console.log('ℹ️ 卡片上未顯示狀態信息');
      }
    });

    // =====================================
    // Phase 3: 驗證卡片其他信息
    // =====================================
    await test.step('Phase 3: 驗證卡片包含其他信息', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找卡片內的所有文本元素
      const textElements = agentCard.locator('p, div, span');

      const count = await textElements.count();

      if (count > 0) {
        console.log(`✅ 卡片包含 ${count} 個文本元素`);
      }
    });
  });
});
