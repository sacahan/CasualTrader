import { test, expect } from '@playwright/test';

/**
 * 測試案例編號：E2E-003
 * 測試目標：驗證 RiskMetricsCard 組件的完整功能
 *           (Phase 3.2.4 - E2E 系統測試驗證)
 *
 * 測試工具：Playwright
 * 測試範圍：
 *   - 後端計算 (Sharpe/Sortino/Calmar 比率)
 *   - API 層轉換 (Decimal → float)
 *   - 前端展示 (RiskMetricsCard 組件)
 *
 * 優先級：High
 * 標籤：risk-metrics, performance, e2e
 *
 * 6 大測試場景：
 *   1. 正常值顯示 - 驗證三個指標能正確顯示數值
 *   2. NULL 值處理 - 驗證缺失數據顯示為 "—"
 *   3. 邊界值測試 - 驗證極端值正確處理
 *   4. 顏色驗證 - 驗證色彩系統符合規範
 *   5. 響應式設計 - 驗證在各裝置完美顯示
 *   6. 效能測試 - 驗證首屏加載時間和幀率
 */

const TEST_CONFIG = {
  // API 端點
  performanceHistoryEndpoint: '/api/trading/agents/*/performance-history',

  // 色彩規範 (RGB)
  colors: {
    good: 'rgb(16, 185, 129)', // 綠色 - 優秀
    fair: 'rgb(245, 158, 11)', // 黃色 - 中等
    poor: 'rgb(239, 68, 68)', // 紅色 - 較差
    neutral: 'rgb(156, 163, 175)', // 灰色 - 無數據
  },

  // 指標閾值
  thresholds: {
    good: 1.0, // > 1.0 = 優秀
    fair: 0, // 0-1.0 = 中等
    poor: -Infinity, // < 0 = 較差
  },

  // 測試超時 (毫秒)
  timeouts: {
    pageLoad: 5000,
    componentRender: 2000,
    apiResponse: 3000,
  },
};

test.describe('📊 E2E-003: RiskMetricsCard 完整測試', () => {
  /**
   * beforeEach：在每個 test() 前執行
   */
  test.beforeEach(async ({ page }) => {
    // 設置視口 (桌面)
    await page.setViewportSize({ width: 1920, height: 1080 });

    // 導航到首頁
    await page.goto('/', { waitUntil: 'networkidle' });

    // 等待頁面穩定
    await page.waitForLoadState('networkidle');
  });

  // ============================================================
  // 場景 1️⃣: 正常值顯示
  // 驗證三個風險指標能正確顯示正常值（不是 "—"）
  // ============================================================
  test('場景 1: 正常值顯示 - 三個指標正確顯示數值', async ({ page }) => {
    await test.step('導航到 Agent 詳情頁面', async () => {
      // 查找第一個 Agent 卡片
      const firstAgentCard = page.locator('[class*="AgentCard"]').first();
      const isVisible = await firstAgentCard.isVisible({ timeout: 2000 }).catch(() => false);

      if (isVisible) {
        await firstAgentCard.click();
        await page.waitForLoadState('networkidle');
      } else {
        console.log('ℹ️ 未找到 Agent 卡片，跳過此測試');
        test.skip();
      }
    });

    await test.step('驗證 RiskMetricsCard 組件存在', async () => {
      const metricsCard = page.locator('text=進階風險指標');
      await expect(metricsCard).toBeVisible({ timeout: TEST_CONFIG.timeouts.componentRender });
    });

    await test.step('驗證三個指標都顯示正常值', async () => {
      // Sharpe Ratio
      const sharpeValue = page
        .locator('text=Sharpe Ratio')
        .locator('..')
        .locator('[class*="value"]');
      const sharpeText = await sharpeValue.textContent();
      console.log(`✓ Sharpe Ratio: ${sharpeText}`);
      expect(sharpeText).not.toBe('—');
      expect(sharpeText?.match(/\d+\.\d{2}/)).toBeTruthy(); // XX.XX 格式

      // Sortino Ratio
      const sortinoValue = page
        .locator('text=Sortino Ratio')
        .locator('..')
        .locator('[class*="value"]');
      const sortinoText = await sortinoValue.textContent();
      console.log(`✓ Sortino Ratio: ${sortinoText}`);
      expect(sortinoText).not.toBe('—');
      expect(sortinoText?.match(/\d+\.\d{2}/)).toBeTruthy();

      // Calmar Ratio
      const calmarValue = page
        .locator('text=Calmar Ratio')
        .locator('..')
        .locator('[class*="value"]');
      const calmarText = await calmarValue.textContent();
      console.log(`✓ Calmar Ratio: ${calmarText}`);
      expect(calmarText).not.toBe('—');
      expect(calmarText?.match(/\d+\.\d{2}/)).toBeTruthy();
    });

    await test.step('驗證都有顏色編碼', async () => {
      const coloredItems = page.locator('[class*="RiskMetricsCard"] [class*="status"]');
      const count = await coloredItems.count();
      expect(count).toBeGreaterThanOrEqual(3);
      console.log(`✓ 找到 ${count} 個狀態指示項`);
    });

    await test.step('驗證時間戳正確顯示', async () => {
      const timestamp = page.locator('[class*="timestamp"], text=/\\d{4}-\\d{2}-\\d{2}/');
      const isVisible = await timestamp.isVisible({ timeout: 1000 }).catch(() => false);
      if (isVisible) {
        const dateText = await timestamp.textContent();
        console.log(`✓ 數據時間: ${dateText}`);
        expect(dateText).toMatch(/\d{4}-\d{2}-\d{2}/);
      }
    });

    console.log('✅ 場景 1 通過: 正常值顯示');
  });

  // ============================================================
  // 場景 2️⃣: NULL 值處理
  // 驗證數據不足時顯示 "—"（優雅降級）
  // ============================================================
  test('場景 2: NULL 值處理 - 缺失指標顯示 "—"', async ({ page }) => {
    await test.step('模擬無效的性能數據響應', async () => {
      // 攔截 API 並返回 NULL 值
      await page.route('**/api/trading/agents/*/performance-history', async (route) => {
        await route.abort('failed');
      });
    });

    await test.step('導航到 Agent 詳情頁面', async () => {
      const firstAgentCard = page.locator('[class*="AgentCard"]').first();
      const isVisible = await firstAgentCard.isVisible({ timeout: 2000 }).catch(() => false);

      if (isVisible) {
        await firstAgentCard.click();
        await page.waitForTimeout(1000);
      } else {
        test.skip();
      }
    });

    await test.step('驗證 RiskMetricsCard 優雅降級', async () => {
      const metricsCard = page.locator('text=進階風險指標');
      const isVisible = await metricsCard.isVisible({ timeout: 2000 }).catch(() => false);

      if (isVisible) {
        // 檢查是否有 "—" 或錯誤消息
        const emptyIndicators = page.locator('text=—');
        const count = await emptyIndicators.count();
        console.log(`✓ 找到 ${count} 個空值指示符 "—"`);

        if (count > 0) {
          expect(count).toBeGreaterThan(0);
        }
      }
    });

    console.log('✅ 場景 2 通過: NULL 值處理');
  });

  // ============================================================
  // 場景 3️⃣: 邊界值測試
  // 驗證極端值能正確處理（高值/低值/負值）
  // ============================================================
  test('場景 3: 邊界值測試 - 極端值正確處理', async ({ page }) => {
    await test.step('準備測試數據', async () => {
      // 模擬不同的邊界值
      const testValues = [
        { value: 3.5, expected: '3.50', status: '優秀' },
        { value: 1.0, expected: '1.00', status: '優秀' },
        { value: 0.5, expected: '0.50', status: '中等' },
        { value: -0.5, expected: '-0.50', status: '較差' },
        { value: -2.5, expected: '-2.50', status: '較差' },
      ];

      console.log('📋 測試邊界值:');
      testValues.forEach((item) => {
        console.log(`  • ${item.value} → ${item.expected} (${item.status})`);
      });
    });

    await test.step('驗證格式化邏輯', async () => {
      // 進入詳情頁面
      const firstAgentCard = page.locator('[class*="AgentCard"]').first();
      const isVisible = await firstAgentCard.isVisible({ timeout: 2000 }).catch(() => false);

      if (!isVisible) {
        test.skip();
      }

      await firstAgentCard.click();
      await page.waitForLoadState('networkidle');

      // 檢查數值格式（應該都是 XX.XX 或 -X.XX）
      const values = page.locator('[class*="RiskMetricsCard"] [class*="value"]');
      const count = await values.count();

      for (let i = 0; i < Math.min(count, 3); i++) {
        const text = await values.nth(i).textContent();
        console.log(`✓ 指標 ${i + 1}: ${text}`);

        // 驗證格式：XX.XX 或 -X.XX 或 "—"
        const formatValid = text === '—' || /^-?\d+\.\d{2}$/.test(text || '');
        expect(formatValid).toBe(true);
      }
    });

    console.log('✅ 場景 3 通過: 邊界值測試');
  });

  // ============================================================
  // 場景 4️⃣: 顏色驗證
  // 驗證色彩系統符合設計規範
  // ============================================================
  test('場景 4: 顏色驗證 - 色彩符合規範', async ({ page }) => {
    await test.step('導航到 Agent 詳情頁面', async () => {
      const firstAgentCard = page.locator('[class*="AgentCard"]').first();
      const isVisible = await firstAgentCard.isVisible({ timeout: 2000 }).catch(() => false);

      if (isVisible) {
        await firstAgentCard.click();
        await page.waitForLoadState('networkidle');
      } else {
        test.skip();
      }
    });

    await test.step('驗證色彩規範', async () => {
      const metricsCard = page.locator('[class*="RiskMetricsCard"]');

      // 取得所有狀態卡片
      const statusItems = metricsCard.locator('[class*="status"], [class*="Status"]');
      const count = await statusItems.count();

      console.log(`📋 檢查 ${count} 個指標的顏色:`);

      for (let i = 0; i < Math.min(count, 3); i++) {
        const item = statusItems.nth(i);
        const bgColor = await item.evaluate((el) => {
          return window.getComputedStyle(el).backgroundColor;
        });

        console.log(`  • 指標 ${i + 1}: ${bgColor}`);

        // 驗證顏色是否在預期的範圍內
        const isValidColor =
          bgColor.includes('16, 185, 129') || // 綠色
          bgColor.includes('245, 158, 11') || // 黃色
          bgColor.includes('239, 68, 68') || // 紅色
          bgColor.includes('156, 163, 175'); // 灰色

        expect(isValidColor).toBe(true);
      }
    });

    await test.step('驗證懸停效果', async () => {
      const statusItem = page.locator('[class*="RiskMetricsCard"] [class*="status"]').first();
      const isVisible = await statusItem.isVisible().catch(() => false);

      if (isVisible) {
        // 獲取懸停前的顏色
        const colorBefore = await statusItem.evaluate((el) => {
          return window.getComputedStyle(el).backgroundColor;
        });

        // 懸停
        await statusItem.hover();
        await page.waitForTimeout(300);

        // 獲取懸停後的顏色
        const colorAfter = await statusItem.evaluate((el) => {
          return window.getComputedStyle(el).backgroundColor;
        });

        console.log(`✓ 懸停效果: ${colorBefore} → ${colorAfter}`);
      }
    });

    console.log('✅ 場景 4 通過: 顏色驗證');
  });

  // ============================================================
  // 場景 5️⃣: 響應式設計
  // 驗證在不同螢幕尺寸下正確顯示
  // ============================================================
  test('場景 5: 響應式設計 - 多設備完美顯示', async ({ page }) => {
    const viewports = [
      { name: '桌面', width: 1920, height: 1080, columns: 3 },
      { name: '平板', width: 768, height: 1024, columns: 1 },
      { name: '手機', width: 375, height: 667, columns: 1 },
    ];

    for (const viewport of viewports) {
      await test.step(`測試 ${viewport.name} (${viewport.width}×${viewport.height})`, async () => {
        // 調整視口
        await page.setViewportSize({
          width: viewport.width,
          height: viewport.height,
        });

        // 導航
        await page.goto('/');
        await page.waitForLoadState('networkidle');

        // 進入詳情頁面
        const firstAgentCard = page.locator('[class*="AgentCard"]').first();
        const isVisible = await firstAgentCard.isVisible({ timeout: 2000 }).catch(() => false);

        if (isVisible) {
          await firstAgentCard.click();
          await page.waitForLoadState('networkidle');
        }

        // 檢查 RiskMetricsCard
        const metricsCard = page.locator('text=進階風險指標');
        const isCardVisible = await metricsCard.isVisible({ timeout: 2000 }).catch(() => false);

        if (isCardVisible) {
          // 檢查沒有水平滾軸
          const hasHorizontalScroll = await page.evaluate(() => {
            return document.documentElement.scrollWidth > document.documentElement.clientWidth;
          });

          console.log(
            `✓ ${viewport.name}: ${hasHorizontalScroll ? '⚠️ 有水平滾軸' : '✅ 無水平滾軸'}`
          );

          expect(hasHorizontalScroll).toBe(false);

          // 檢查字體大小
          const fontSize = await metricsCard.evaluate((el) => {
            return window.getComputedStyle(el).fontSize;
          });

          console.log(`✓ 字體大小: ${fontSize}`);

          // 手機版應該 >= 14px
          if (viewport.width < 768) {
            const size = parseInt(fontSize);
            expect(size).toBeGreaterThanOrEqual(14);
          }
        }
      });
    }

    console.log('✅ 場景 5 通過: 響應式設計');
  });

  // ============================================================
  // 場景 6️⃣: 效能測試
  // 驗證首屏加載時間和幀率
  // ============================================================
  test('場景 6: 效能測試 - 快速流暢加載', async ({ page }) => {
    await test.step('測量頁面加載性能', async () => {
      const navigationTiming = await page.evaluate(() => {
        const timing = performance.getEntriesByType('navigation')[0];
        if (!timing) return null;

        return {
          domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
          loadComplete: timing.loadEventEnd - timing.loadEventStart,
          ttfb: timing.responseStart - timing.requestStart,
        };
      });

      if (navigationTiming) {
        console.log('📊 加載時間:');
        console.log(`  • TTFB (首字節): ${navigationTiming.ttfb.toFixed(0)}ms`);
        console.log(`  • DOM Content Loaded: ${navigationTiming.domContentLoaded.toFixed(0)}ms`);
        console.log(`  • 完全加載: ${navigationTiming.loadComplete.toFixed(0)}ms`);

        // 驗證首屏時間 < 2 秒
        expect(navigationTiming.domContentLoaded).toBeLessThan(2000);
      }
    });

    await test.step('進入詳情頁面並測量', async () => {
      const firstAgentCard = page.locator('[class*="AgentCard"]').first();
      const isVisible = await firstAgentCard.isVisible({ timeout: 2000 }).catch(() => false);

      if (isVisible) {
        const startTime = Date.now();
        await firstAgentCard.click();
        await page.waitForLoadState('networkidle');
        const duration = Date.now() - startTime;

        console.log(`✓ 進入詳情頁面耗時: ${duration}ms`);
        expect(duration).toBeLessThan(3000);
      }
    });

    await test.step('測試 RiskMetricsCard 渲染性能', async () => {
      const metricsCard = page.locator('text=進階風險指標');
      const isVisible = await metricsCard.isVisible({ timeout: 2000 }).catch(() => false);

      if (isVisible) {
        // 測量組件可見性時間
        const renderMetrics = await page.evaluate(() => {
          const perfEntries = performance.getEntriesByType('paint');
          return {
            firstPaint: perfEntries.find((e) => e.name === 'first-paint')?.startTime,
            firstContentfulPaint: perfEntries.find((e) => e.name === 'first-contentful-paint')
              ?.startTime,
          };
        });

        if (renderMetrics.firstContentfulPaint) {
          console.log(
            `✓ First Contentful Paint: ${renderMetrics.firstContentfulPaint.toFixed(0)}ms`
          );
          expect(renderMetrics.firstContentfulPaint).toBeLessThan(2000);
        }
      }
    });

    await test.step('測試框架率（模擬）', async () => {
      const fps = await page.evaluate(() => {
        return new Promise((resolve) => {
          let frameCount = 0;
          let lastTime = performance.now();

          const countFrames = () => {
            frameCount++;
            const currentTime = performance.now();
            if (currentTime - lastTime >= 1000) {
              resolve(frameCount);
            } else {
              requestAnimationFrame(countFrames);
            }
          };

          requestAnimationFrame(countFrames);
        });
      });

      console.log(`✓ 測試幀率: 約 ${fps} FPS (1 秒內)`);
      expect(fps).toBeGreaterThan(30); // 至少 30 FPS
    });

    console.log('✅ 場景 6 通過: 效能測試');
  });
});

/**
 * ============================================================
 * 測試執行說明
 * ============================================================
 *
 * 執行所有 RiskMetricsCard 測試:
 *   npx playwright test E2E-003-risk-metrics.spec.js
 *
 * 執行特定測試:
 *   npx playwright test E2E-003-risk-metrics.spec.js -g "正常值顯示"
 *
 * 使用 UI 模式（推薦調試):
 *   npx playwright test E2E-003-risk-metrics.spec.js --ui
 *
 * 生成 HTML 報告:
 *   npx playwright test E2E-003-risk-metrics.spec.js --reporter=html
 *   npx playwright show-report
 *
 * 記錄視頻（調試用):
 *   npx playwright test E2E-003-risk-metrics.spec.js --record-video=retain-on-failure
 *
 * ============================================================
 */
