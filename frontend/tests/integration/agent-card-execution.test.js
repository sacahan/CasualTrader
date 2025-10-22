/**
 * AgentCard Component Integration Tests
 *
 * 測試 AgentCard 組件的 WebSocket 事件監聽和 UI 更新
 *
 * 手動測試清單（在 Vitest/Jest 設置之前）:
 *
 * 1. 觀察模式執行
 *    [ ] 點擊 "觀察" 按鈕
 *    [ ] 驗證按鈕變為 loading 狀態
 *    [ ] 驗證其他按鈕被禁用
 *    [ ] 驗證藍色提示顯示 "執行中..."
 *    [ ] 等待後端返回 execution_completed
 *    [ ] 驗證綠色提示顯示 "執行完成 (耗時 XXXms)"
 *
 * 2. 交易模式執行
 *    [ ] 點擊 "交易" 按鈕
 *    [ ] 驗證 loading 狀態
 *    [ ] 驗證執行完成提示
 *
 * 3. 再平衡模式執行
 *    [ ] 點擊 "平衡" 按鈕
 *    [ ] 驗證 loading 狀態
 *    [ ] 驗證執行完成提示
 *
 * 4. 執行失敗場景
 *    [ ] 後端返回 execution_failed 事件
 *    [ ] 驗證紅色提示顯示錯誤信息
 *    [ ] 驗證按鈕恢復可用狀態
 *
 * 5. 執行停止場景
 *    [ ] Agent 運行中
 *    [ ] 點擊 "停止" 按鈕
 *    [ ] 驗證 loading 狀態
 *    [ ] 驗證 execution_stopped 事件推送
 *    [ ] 驗證 runtime_status 更新為 "stopped"
 *
 * 6. 狀態持久性
 *    [ ] 執行開始時，runtime_status 應該是 "running"
 *    [ ] 執行完成時，runtime_status 應該是 "idle"
 *    [ ] 執行失敗時，runtime_status 應該是 "stopped"
 *
 * 7. 並發檢查
 *    [ ] 執行中時，不應該開始新的執行
 *    [ ] 執行中時，所有按鈕都應該被禁用（loading=true, disabled=true）
 */

// 將此文件作為測試指南
// 當項目配置 Vitest/Jest 時，使用上面的清單編寫完整的測試用例

export default {
  name: 'AgentCard Component Integration Tests',
  status: 'Manual Testing Guide',
  description: '在 Vitest/Jest 設置完成後實現自動化測試',
};

/**
 * Vitest 測試範本（當添加依賴時）
 *
 * import { describe, it, expect, beforeEach, vi } from 'vitest';
 * import { render, screen, fireEvent } from '@testing-library/svelte';
 * import AgentCard from '../../src/components/Agent/AgentCard.svelte';
 * import { addEventListener } from '../../src/stores/websocket.js';
 *
 * describe('AgentCard Execution Events', () => {
 *   it('should display loading state when executing', async () => {
 *     const agent = {
 *       agent_id: 'test-agent',
 *       name: 'Test Agent',
 *       status: 'active',
 *       runtime_status: 'idle',
 *       portfolio: { total_value: 1000000, cash: 500000 },
 *     };
 *
 *     render(AgentCard, { props: { agent } });
 *
 *     const observeButton = screen.getByText('觀察');
 *     fireEvent.click(observeButton);
 *
 *     // 等待 loading 狀態
 *     await screen.findByText('執行中...');
 *   });
 * });
 */
