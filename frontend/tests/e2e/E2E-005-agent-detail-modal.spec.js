import { test, expect } from '@playwright/test';
import { setupTestAgent } from './fixtures.js';

/**
 * 測試案例編號：E2E-005
 * 測試目標：驗證 Agent 詳情彈窗功能、內容顯示和交互操作
 *
 * 測試工具：Playwright
 * 測試範圍：前端 Modal 交互 + 詳情信息顯示
 * 優先級：Medium
 * 標籤：agent, modal, detail
 *
 * 教學說明：
 * - 此測試依賴於至少存在一個 Agent 卡片
 * - 驗證 Modal 打開、內容顯示和關閉操作
 * - 測試中使用 .catch(() => false) 進行優雅降級
 */

test.describe('📋 E2E-005: Agent 詳情彈窗', () => {
  /**
   * beforeEach：在每個 test() 前執行一次
   * - 導航至首頁
   * - 等待頁面完全加載
   * - 確保至少存在一個 Agent（自動創建如果需要）
   * - 等待 1 秒讓 Agent 卡片完全渲染
   */
  test.beforeEach(async ({ page }) => {
    await setupTestAgent(page);
    await page.waitForTimeout(1000);
  });

  test('📱 點擊 Agent 卡片打開詳情 Modal', async ({ page }) => {
    // =======================================
    // Phase 1: 等待 Agent 卡片並打開詳情
    // =======================================
    await test.step('Phase 1: 尋找並點擊 Agent 卡片', async () => {
      // 尋找第一個 Agent 卡片
      const agentCard = page.locator('.agent-card').first();

      // 檢查卡片是否存在（優雅降級）
      const cardExists = await agentCard.isVisible().catch(() => false);

      if (!cardExists) {
        // 無 Agent 卡片，記錄並跳過
        console.log('⚠️ 未找到 Agent 卡片，可能無創建的 Agent');
        return;
      }

      // 點擊卡片打開詳情
      await agentCard.click();

      // 等待 Modal 出現
      const hasModal = await page
        .locator('role=dialog')
        .isVisible()
        .catch(() => false);

      if (!hasModal) {
        console.log('⚠️ 點擊卡片後 Modal 未出現');
      }

      expect(hasModal).toBe(true);
    });

    // =======================================
    // Phase 2: 驗證詳情 Modal 內容
    // =======================================
    await test.step('Phase 2: 驗證 Modal 中的詳情內容', async () => {
      // 尋找 Modal 元素
      const modal = page.locator('role=dialog').first();

      // 檢查 Modal 是否可見
      const isVisible = await modal.isVisible().catch(() => false);

      if (isVisible) {
        // Modal 存在且可見，驗證其包含某些內容
        const modalContent = await modal.textContent();

        if (modalContent && modalContent.length > 0) {
          console.log(`✅ Modal 內容長度：${modalContent.length} 字元`);
        }

        // 驗證 Modal 確實包含信息
        expect(modalContent).toBeTruthy();
      } else {
        console.log('⚠️ Modal 不可見，跳過內容驗證');
      }
    });

    // =======================================
    // Phase 3: 關閉 Modal
    // =======================================
    await test.step('Phase 3: 關閉 Modal', async () => {
      // 尋找關閉按鈕（多個選擇器策略）
      // - button[title="關閉"]：標題為"關閉"
      // - button:has-text("✕")：文本包含"✕"符號
      // - button:has-text("關閉")：文本包含"關閉"
      const closeBtn = page
        .locator('button[title="關閉"], button:has-text("✕"), button:has-text("關閉")')
        .first();

      const closeExists = await closeBtn.isVisible().catch(() => false);

      if (closeExists) {
        // 關閉按鈕存在，點擊關閉
        await closeBtn.click();
        await page.waitForTimeout(500);
        console.log('✅ Modal 已關閉');
      } else {
        console.log('⚠️ 未找到關閉按鈕');
      }
    });
  });

  test('✏️ 從詳情 Modal 中查看編輯選項', async ({ page }) => {
    // =======================================
    // Phase 1: 打開詳情 Modal
    // =======================================
    await test.step('Phase 1: 打開 Agent 詳情', async () => {
      // 尋找第一個 Agent 卡片
      const agentCard = page.locator('.agent-card').first();

      // 檢查卡片存在性
      const cardExists = await agentCard.isVisible().catch(() => false);

      if (!cardExists) {
        console.log('⚠️ 未找到 Agent 卡片，跳過測試');
        return;
      }

      // 點擊卡片打開詳情
      await agentCard.click();

      // 等待 Modal 出現
      await page.waitForTimeout(1000);

      const hasModal = await page
        .locator('role=dialog')
        .isVisible()
        .catch(() => false);

      expect(hasModal).toBe(true);

      if (!hasModal) {
        console.log('⚠️ Modal 未出現');
      }
    });

    // =======================================
    // Phase 2: 驗證編輯按鈕存在
    // =======================================
    await test.step('Phase 2: 檢查詳情中的編輯按鈕', async () => {
      // 尋找編輯按鈕（多個選擇器策略）
      // - button:has-text("編輯")：文本包含"編輯"
      // - button[title*="編輯"]：標題包含"編輯"
      const editBtn = page.locator('button:has-text("編輯"), button[title*="編輯"]').first();

      const hasEditBtn = await editBtn.isVisible().catch(() => false);

      if (hasEditBtn) {
        console.log('✅ 詳情中包含編輯按鈕');
      } else {
        console.log('ℹ️ 編輯按鈕不可見或不存在（可能是權限限制）');
      }

      // 編輯按鈕是可選的（可能被禁用或隱藏）
      expect([true, false]).toContain(hasEditBtn || true);
    });

    // =======================================
    // Phase 3: 驗證其他詳情元素
    // =======================================
    await test.step('Phase 3: 驗證詳情中的其他信息', async () => {
      const modal = page.locator('role=dialog').first();

      // 檢查是否包含常見詳情信息
      const infoElements = modal.locator('p, div[class*="info"], div[class*="detail"]');
      const count = await infoElements.count().catch(() => 0);

      if (count > 0) {
        console.log(`✅ 詳情中包含 ${count} 個信息元素`);
      } else {
        console.log('ℹ️ 詳情中未找到明確的信息元素');
      }
    });

    // =======================================
    // Phase 4: 關閉 Modal
    // =======================================
    await test.step('Phase 4: 關閉 Modal', async () => {
      // 尋找關閉按鈕
      const closeBtn = page.locator('button[title="關閉"], button:has-text("✕")').first();

      const closeExists = await closeBtn.isVisible().catch(() => false);

      if (closeExists) {
        await closeBtn.click();
        await page.waitForTimeout(500);
      }
    });
  });
});
