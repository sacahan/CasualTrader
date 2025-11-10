/**
 * E2E 測試 Fixtures
 *
 * 提供測試用的共享數據和設置函數
 * 確保每個測試都有必要的前置條件
 */

const TEST_AGENTS = {
  basic: {
    name: 'Test-Agent-Basic',
    description: 'Basic test agent for editing and interactions',
    initialFunds: '1000000',
    maxPositionSize: '50',
    preferredStocks: '2330,2454,2317',
  },
  detailed: {
    name: 'Test-Agent-Detailed',
    description: 'Detailed test agent with complete configuration',
    initialFunds: '5000000',
    maxPositionSize: '30',
    preferredStocks: '2330,2454,2317,0050,1301',
  },
};

/**
 * 創建或確認測試 Agent 存在
 *
 * 嘗試多種方式確保 Agent 存在：
 * 1. 檢查頁面上是否已有卡片
 * 2. 如果無，嘗試通過 UI 創建
 * 3. 添加詳細的錯誤日誌幫助調試
 *
 * @param {Page} page - Playwright page object
 * @param {Object} agentConfig - Agent configuration
 * @returns {Promise<boolean>} 是否成功確保 Agent 存在
 */
export async function ensureAgentExists(page, agentConfig = TEST_AGENTS.basic) {
  // ====================================
  // Step 1: 檢查頁面上是否已有 Agent 卡片
  // ====================================
  const existingCard = await page
    .locator('.agent-card, [class*="AgentCard"]')
    .first()
    .isVisible()
    .catch(() => false);

  if (existingCard) {
    console.log('✅ 頁面上已存在 Agent 卡片，無需創建');
    return true;
  }

  console.log('📝 未找到現有 Agent，開始創建新 Agent...');

  // ====================================
  // Step 2: 打開創建表單
  // ====================================
  const createBtn = page
    .locator('button:has-text("創建新 Agent"), button:has-text("建立 Agent")')
    .first();
  const btnExists = await createBtn.isVisible().catch(() => false);

  if (!btnExists) {
    console.error('❌ 找不到創建 Agent 按鈕');
    return false;
  }

  await createBtn.click().catch((err) => {
    console.error('❌ 點擊創建按鈕失敗:', err.message);
  });

  await page.waitForTimeout(500);

  // ====================================
  // Step 3: 填入表單
  // ====================================
  try {
    // Agent 名稱（添加時間戳確保唯一性）
    const nameInput = page
      .locator('label:has-text("Agent 名稱")')
      .locator('..')
      .locator('input')
      .first();

    const nameVisible = await nameInput.isVisible({ timeout: 2000 }).catch(() => false);
    if (nameVisible) {
      await nameInput.fill(`${agentConfig.name}-${Date.now()}`);
      console.log('✅ 已填入 Agent 名稱');
    }

    // 投資偏好描述
    const descInput = page
      .locator('label:has-text("投資偏好描述")')
      .locator('..')
      .locator('textarea')
      .first();

    const descVisible = await descInput.isVisible({ timeout: 2000 }).catch(() => false);
    if (descVisible) {
      await descInput.fill(agentConfig.description);
      console.log('✅ 已填入投資偏好描述');
    }

    // 初始資金
    const fundsInput = page
      .locator('label:has-text("初始資金")')
      .locator('..')
      .locator('input[type="number"]')
      .first();

    const fundsVisible = await fundsInput.isVisible({ timeout: 2000 }).catch(() => false);
    if (fundsVisible) {
      await fundsInput.fill(agentConfig.initialFunds);
      console.log('✅ 已填入初始資金');
    }

    // 單一持股比例上限
    const maxPosInput = page
      .locator('label:has-text("單一持股比例上限")')
      .locator('..')
      .locator('input[type="number"]')
      .first();

    const maxPosVisible = await maxPosInput.isVisible({ timeout: 2000 }).catch(() => false);
    if (maxPosVisible) {
      await maxPosInput.fill(agentConfig.maxPositionSize);
      console.log('✅ 已填入持股比例上限');
    }

    // 偏好公司代號（可選）
    const stocksInput = page
      .locator('label:has-text("偏好公司代號")')
      .locator('..')
      .locator('input')
      .first();

    const stocksVisible = await stocksInput.isVisible({ timeout: 2000 }).catch(() => false);
    if (stocksVisible) {
      await stocksInput.fill(agentConfig.preferredStocks);
      console.log('✅ 已填入偏好公司代號');
    }
  } catch (err) {
    console.error('❌ 填入表單時出錯:', err.message);
    return false;
  }

  // ====================================
  // Step 4: 提交表單
  // ====================================
  const submitBtn = page.locator('form button[type="submit"]');
  const submitVisible = await submitBtn.isVisible().catch(() => false);

  if (!submitVisible) {
    console.error('❌ 找不到提交按鈕');
    return false;
  }

  await submitBtn.click().catch((err) => {
    console.error('❌ 點擊提交按鈕失敗:', err.message);
  });

  console.log('📤 已提交表單，等待響應...');

  // ====================================
  // Step 5: 等待創建完成
  // ====================================
  await page.waitForTimeout(2000);

  // 嘗試等待 Modal 關閉
  const modal = page.locator('role=dialog');
  const modalOpen = await modal.isVisible().catch(() => false);

  if (modalOpen) {
    console.warn('⚠️ Modal 仍然打開，嘗試等待...');
    await modal.waitFor({ state: 'hidden', timeout: 3000 }).catch(() => {
      console.warn('⚠️ Modal 未在規定時間內關閉');
    });
  }

  // 等待頁面更新
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(1000);

  // ====================================
  // Step 6: 驗證 Agent 已創建
  // ====================================
  const createdCard = await page
    .locator('.agent-card, [class*="AgentCard"]')
    .first()
    .isVisible()
    .catch(() => false);

  if (createdCard) {
    console.log('✅ Agent 已成功創建並在頁面上顯示');
    return true;
  }

  console.warn('⚠️ Agent 可能已創建但尚未在頁面上顯示，嘗試刷新...');

  // 刷新頁面重新加載
  await page.reload().catch(() => {});
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(1000);

  // 最後檢查
  const finalCard = await page
    .locator('.agent-card, [class*="AgentCard"]')
    .first()
    .isVisible()
    .catch(() => false);

  if (finalCard) {
    console.log('✅ Agent 在頁面刷新後成功顯示');
    return true;
  }

  console.error('❌ 無法確認 Agent 已創建');
  return false;
}

/**
 * 使用現有 Agent 或創建新的 Agent
 *
 * 這是最健壯的方式，確保測試始終有可用的 Agent
 * 優先使用現有 Agent，避免不必要的創建
 *
 * @param {Page} page - Playwright page object
 * @returns {Promise<void>}
 */
export async function setupTestAgent(page) {
  console.log('🔧 設置測試 Agent...');

  // 導航到首頁
  await page.goto('/');
  await page.waitForLoadState('load');
  await page.waitForTimeout(500);

  // 檢查是否已有 Agent（優先使用現有的）
  const existingCard = await page
    .locator('.agent-card, [class*="AgentCard"]')
    .first()
    .isVisible()
    .catch(() => false);

  if (existingCard) {
    console.log('✅ 頁面已存在 Agent，無需創建新的');
    return;
  }

  // 如果沒有 Agent，嘗試創建
  console.log('📝 未找到現有 Agent，嘗試創建新 Agent...');
  const success = await ensureAgentExists(page);

  if (!success) {
    console.warn('⚠️ 無法創建新 Agent，但測試將繼續嘗試使用現有 Agent');
  }
}

/**
 * 確保頁面有多個 Agent（用於需要選擇/交互的測試）
 *
 * @param {Page} page - Playwright page object
 * @param {number} count - 所需的 Agent 數量
 * @returns {Promise<number>} 實際 Agent 數量
 */
export async function ensureMultipleAgents(page, count = 2) {
  console.log(`🔧 確保頁面上至少有 ${count} 個 Agent...`);

  for (let i = 0; i < count; i++) {
    const cards = await page.locator('.agent-card, [class*="AgentCard"]').count();

    if (cards >= count) {
      console.log(`✅ 已確保有 ${cards} 個 Agent`);
      return cards;
    }

    // 創建更多 Agent
    console.log(`📝 創建第 ${i + 1} 個 Agent...`);
    const created = await ensureAgentExists(page, TEST_AGENTS.basic);

    if (!created) {
      console.warn(`⚠️ 第 ${i + 1} 個 Agent 創建失敗，退出`);
      break;
    }
  }

  const finalCount = await page.locator('.agent-card, [class*="AgentCard"]').count();
  console.log(`✅ 最終 Agent 數量：${finalCount}`);
  return finalCount;
}
