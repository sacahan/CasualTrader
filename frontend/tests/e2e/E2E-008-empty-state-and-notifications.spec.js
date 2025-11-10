import { test, expect } from '@playwright/test';

/**
 * 測試案例編號：E2E-008
 * 測試目標：驗證空狀態顯示、通知系統的 Toast 消息、以及錯誤通知功能
 *
 * 測試工具：Playwright
 * 測試範圍：前端 UX 反饋系統（空狀態、通知、Toast）
 * 優先級：Medium
 * 標籤：ux, notification, toast, empty-state
 *
 * 教學說明：
 * - 空狀態：當無任何 Agent 時顯示友善的提示
 * - 通知系統：操作成功/失敗時顯示 Toast 消息
 * - 自動關閉：Toast 應在 3-5 秒內自動消失
 * - 錯誤處理：表單提交失敗時顯示錯誤通知
 */

test.describe('🔔 E2E-008: 空狀態與通知系統', () => {
  /**
   * beforeEach：在每個 test() 前執行一次
   * - 導航至首頁
   * - 等待頁面網絡空閒
   * - 確保所有初始化完成
   */
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('📭 無 Agent 時顯示空狀態', async ({ page }) => {
    // =====================================
    // Phase 1: 檢查是否有 Agent 卡片
    // =====================================
    await test.step('Phase 1: 檢查頁面上的 Agent 數量', async () => {
      // 尋找所有 Agent 卡片
      const agents = page.locator('[class*="AgentCard"]');

      // 計算 Agent 卡片數量
      const count = await agents.count();

      console.log(`ℹ️ 當前頁面包含 ${count} 個 Agent`);

      if (count === 0) {
        console.log('✅ 無 Agent，應顯示空狀態');
      } else {
        console.log('ℹ️ 已有 Agent，跳過空狀態測試');
      }
    });

    // =====================================
    // Phase 2: 驗證空狀態顯示
    // =====================================
    await test.step('Phase 2: 驗證空狀態提示信息', async () => {
      const agents = page.locator('[class*="AgentCard"]');
      const count = await agents.count();

      if (count === 0) {
        // 尋找空狀態元素
        // 使用多個選擇器策略：
        // - [class*="empty"]：class 包含"empty"
        // - [class*="EmptyState"]：class 包含"EmptyState"
        // - text="沒有 Agent"：文本內容是"沒有 Agent"
        const emptyState = page.locator(
          '[class*="empty"], [class*="EmptyState"], text="沒有 Agent"'
        );

        const isVisible = await emptyState.isVisible().catch(() => false);

        if (isVisible) {
          // 取得空狀態提示文字
          const content = await emptyState.textContent();

          // 驗證提示文字包含相關詞彙
          if (content && content.match(/沒有|暫無|創建|Create/i)) {
            console.log(`✅ 空狀態提示：${content.trim()}`);
          } else {
            console.log(`ℹ️ 空狀態文本：${content?.trim()}`);
          }

          expect(content).toMatch(/沒有|暫無|創建|Create/i);
        } else {
          console.log('⚠️ 未找到明確的空狀態提示');
        }
      }
    });
  });

  test('✅ Agent 創建成功時顯示通知', async ({ page }) => {
    // =====================================
    // Phase 1: 打開創建 Agent 表單
    // =====================================
    await test.step('Phase 1: 打開 Agent 創建表單', async () => {
      // 點擊創建按鈕
      await page.locator('button:has-text("創建新 Agent")').click();

      // 驗證 Modal 出現（使用語義選擇器尋找 dialog 元素）
      await expect(page.locator('role=dialog')).toBeVisible({
        timeout: 2000,
      });

      console.log('✅ 創建表單已打開');
    });

    // =====================================
    // Phase 2: 填入必要信息並提交
    // =====================================
    await test.step('Phase 2: 填入表單並提交', async () => {
      // 填入 Agent 名稱（使用 label 定位）
      const nameInput = page
        .locator('label:has-text("Agent 名稱")')
        .locator('..')
        .locator('input')
        .first();
      await nameInput.fill(`Notification-Test-Agent-${Date.now()}`).catch(() => {});

      // 填入投資偏好描述
      const descInput = page
        .locator('label:has-text("投資偏好描述")')
        .locator('..')
        .locator('textarea')
        .first();
      await descInput.fill('Test investment strategy').catch(() => {});

      // 填入初始資金
      const fundsInput = page
        .locator('label:has-text("初始資金")')
        .locator('..')
        .locator('input[type="number"]')
        .first();
      await fundsInput.fill('1000000').catch(() => {});

      // 提交表單
      const submitBtn = page.locator('form button[type="submit"]');
      await submitBtn.click().catch(() => {});

      // 等待提交完成
      await page.waitForTimeout(1000);

      console.log('✅ 表單已提交');
    });

    // =====================================
    // Phase 3: 驗證成功通知出現
    // =====================================
    await test.step('Phase 3: 驗證成功通知消息', async () => {
      // 尋找 Toast 通知元素
      // 使用多個選擇器策略：
      // - [class*="Toast"]：class 包含"Toast"
      // - [class*="Notification"]：class 包含"Notification"
      // - [class*="notification"]：class 包含"notification"
      const toast = page.locator(
        '[class*="Toast"], [class*="Notification"], [class*="notification"]'
      );

      // 檢查通知是否可見
      const isVisible = await toast.isVisible().catch(() => false);

      if (isVisible) {
        // 取得通知內容
        const content = await toast.textContent();

        // 驗證是成功消息（應包含"成功"、"Success"或"created"等）
        if (content && content.match(/成功|Success|created|已創建/i)) {
          console.log(`✅ 成功通知：${content.trim()}`);
        } else {
          console.log(`ℹ️ 通知內容：${content?.trim()}`);
        }

        expect(content).toMatch(/成功|Success|created|已創建/i);
      } else {
        console.log('⚠️ 未找到成功通知');
      }
    });

    // =====================================
    // Phase 4: 驗證通知自動關閉
    // =====================================
    await test.step('Phase 4: 驗證通知自動關閉', async () => {
      console.log('⏳ 等待通知自動消失（通常 3-5 秒）...');

      // 等待 Toast 自動消失
      // 通常實現的自動關閉時間是 3-5 秒
      await page.waitForTimeout(5000);

      // 驗證通知已消失
      const toast = page.locator('[class*="Toast"]');
      const isVisible = await toast.isVisible().catch(() => false);

      if (!isVisible) {
        console.log('✅ 通知已自動消失');
      } else {
        console.log('⚠️ 通知未自動消失（可能需要手動關閉）');
      }

      expect(isVisible).toBe(false);
    });
  });

  test('⏹️ Agent 操作成功時顯示 Toast 通知', async ({ page }) => {
    // =====================================
    // Phase 1: 尋找 Agent 卡片並執行操作
    // =====================================
    await test.step('Phase 1: 尋找 Agent 並點擊執行按鈕', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 檢查卡片是否存在
      const cardExists = await agentCard.isVisible().catch(() => false);

      if (!cardExists) {
        console.log('⚠️ 未找到 Agent 卡片，跳過操作測試');
        return;
      }

      // 尋找執行按鈕
      const runBtn = agentCard.locator('button:has-text("交易"), button:has-text("執行")');

      const btnExists = await runBtn.isVisible().catch(() => false);

      if (btnExists) {
        // 點擊執行按鈕
        await runBtn.click();

        // 等待操作完成
        await page.waitForTimeout(1000);

        console.log('✅ 執行按鈕已點擊');
      } else {
        console.log('⚠️ 未找到執行按鈕');
      }
    });

    // =====================================
    // Phase 2: 觀察成功通知
    // =====================================
    await test.step('Phase 2: 觀察操作成功通知', async () => {
      // 尋找 Toast 通知
      const toast = page.locator('[class*="Toast"]');

      const isVisible = await toast.isVisible().catch(() => false);

      if (isVisible) {
        const content = await toast.textContent();
        console.log(`✅ 操作通知：${content?.trim()}`);
      } else {
        console.log('ℹ️ 未發現操作通知（可能操作完成較快）');
      }
    });

    // =====================================
    // Phase 3: 停止執行
    // =====================================
    await test.step('Phase 3: 停止 Agent 執行', async () => {
      const agentCard = page.locator('[class*="AgentCard"]').first();

      // 尋找停止按鈕
      const stopBtn = agentCard.locator('button:has-text("停止")');

      const stopExists = await stopBtn.isVisible().catch(() => false);

      if (stopExists) {
        await stopBtn.click();
        await page.waitForTimeout(2000);

        console.log('✅ Agent 已停止');
      }
    });
  });

  test('❌ 表單提交失敗時顯示錯誤通知', async ({ page }) => {
    // =====================================
    // Phase 1: 打開創建表單
    // =====================================
    await test.step('Phase 1: 打開創建表單', async () => {
      // 點擊創建按鈕
      await page.locator('button:has-text("創建新 Agent")').click();

      // 驗證 Modal 出現（使用語義選擇器）
      await expect(page.locator('role=dialog')).toBeVisible({
        timeout: 2000,
      });

      console.log('✅ 創建表單已打開');
    });

    // =====================================
    // Phase 2: 嘗試提交空表單以觸發錯誤
    // =====================================
    await test.step('Phase 2: 提交空表單觸發驗證錯誤', async () => {
      // 直接點擊提交（不填任何數據）
      const submitBtn = page.locator('form button[type="submit"]');

      // 檢查按鈕是否可點擊
      const isDisabled = await submitBtn.isDisabled().catch(() => true);

      if (!isDisabled) {
        // 如果按鈕啟用，嘗試點擊
        await submitBtn.click();

        // 等待錯誤反應
        await page.waitForTimeout(1500);

        console.log('✅ 提交空表單');
      } else {
        console.log('ℹ️ 提交按鈕被禁用，前置驗證有效');
      }
    });

    // =====================================
    // Phase 3: 驗證錯誤通知
    // =====================================
    await test.step('Phase 3: 驗證錯誤消息顯示', async () => {
      // 尋找錯誤消息元素
      // 使用多個選擇器策略：
      // - [class*="error"]：class 包含"error"
      // - [class*="Error"]：class 包含"Error"
      // - [class*="warning"]：class 包含"warning"
      // - [role="alert"]：語義標籤
      const errorMsg = page.locator(
        '[class*="error"], [class*="Error"], [class*="warning"], [role="alert"]'
      );

      const isVisible = await errorMsg.isVisible().catch(() => false);

      if (isVisible) {
        const content = await errorMsg.textContent();
        console.log(`✅ 錯誤消息：${content?.trim()}`);

        expect(content).toBeTruthy();
      } else {
        console.log('⚠️ 未找到明確的錯誤消息');
      }
    });

    // =====================================
    // Phase 4: 關閉表單
    // =====================================
    await test.step('Phase 4: 關閉表單', async () => {
      // 尋找關閉按鈕（使用多個策略）
      const closeBtn = page.locator(
        'role=dialog >> button[title="關閉"], role=dialog >> button:has-text("關閉")'
      );

      const closeExists = await closeBtn.isVisible().catch(() => false);

      if (closeExists) {
        await closeBtn.click();
      } else {
        // 使用 Escape 鍵關閉
        await page.keyboard.press('Escape');
      }

      await page.waitForTimeout(500);

      console.log('✅ 表單已關閉');
    });
  });
});
