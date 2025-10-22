/**
 * WebSocket Execution Events Integration Tests
 *
 * 測試 WebSocket 事件監聽和 UI 更新的集成邏輯
 *
 * 執行步驟：
 * 1. npm install vitest --save-dev (或使用其他測試框架)
 * 2. npm test
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { handleEvent, addEventListener } from '../../src/stores/websocket.js';
import { WS_EVENT_TYPES } from '../../src/shared/constants.js';

describe('WebSocket Execution Events', () => {
  let eventCallback;

  beforeEach(() => {
    eventCallback = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('事件監聽', () => {
    it('應該訂閱執行開始事件', () => {
      const unsubscribe = addEventListener(WS_EVENT_TYPES.EXECUTION_STARTED, eventCallback);

      expect(typeof unsubscribe).toBe('function');
    });

    it('應該在事件觸發時調用回調', () => {
      addEventListener(WS_EVENT_TYPES.EXECUTION_STARTED, eventCallback);

      const payload = {
        agent_id: 'test-agent',
        session_id: 'session-123',
        mode: 'TRADING',
      };

      // 模擬事件
      handleEvent({ type: WS_EVENT_TYPES.EXECUTION_STARTED, ...payload });

      // 由於 handleEvent 是同步的，回調應該被調用
      // 注意：實際測試需要根據實現情況調整
      expect(eventCallback).toHaveBeenCalled();
    });

    it('應該能夠取消訂閱', () => {
      const unsubscribe = addEventListener(WS_EVENT_TYPES.EXECUTION_STARTED, eventCallback);
      unsubscribe();

      const payload = { agent_id: 'test-agent', session_id: 'session-123', mode: 'TRADING' };
      handleEvent({ type: WS_EVENT_TYPES.EXECUTION_STARTED, ...payload });

      // 取消訂閱後，回調不應該被調用
      // 注意：實際測試需要根據實現情況調整
      expect(eventCallback).not.toHaveBeenCalled();
    });
  });

  describe('事件格式相容性', () => {
    it('應該相容 "type" 字段（後端格式）', () => {
      addEventListener(WS_EVENT_TYPES.EXECUTION_COMPLETED, eventCallback);

      const payload = {
        type: 'execution_completed',
        agent_id: 'test-agent',
        execution_time_ms: 5000,
        mode: 'TRADING',
      };

      // 後端發送格式
      handleEvent(payload);

      expect(eventCallback).toHaveBeenCalled();
    });

    it('應該相容舊版 "event_type" 字段', () => {
      addEventListener(WS_EVENT_TYPES.EXECUTION_FAILED, eventCallback);

      const payload = {
        event_type: 'execution_failed',
        agent_id: 'test-agent',
        error: 'Test error',
      };

      // 舊版格式
      handleEvent(payload);

      expect(eventCallback).toHaveBeenCalled();
    });

    it('應該提取 payload 字段（如果存在）', () => {
      addEventListener(WS_EVENT_TYPES.EXECUTION_STOPPED, eventCallback);

      const actualPayload = {
        agent_id: 'test-agent',
        status: 'stopped',
      };

      const message = {
        type: 'execution_stopped',
        payload: actualPayload,
      };

      handleEvent(message);

      // 回調應該接收 payload
      expect(eventCallback).toHaveBeenCalled();
    });
  });

  describe('事件類型覆蓋', () => {
    it('應該支持 EXECUTION_STARTED 事件', () => {
      addEventListener(WS_EVENT_TYPES.EXECUTION_STARTED, eventCallback);
      handleEvent({ type: 'execution_started', agent_id: 'test' });
      expect(eventCallback).toHaveBeenCalled();
    });

    it('應該支持 EXECUTION_COMPLETED 事件', () => {
      addEventListener(WS_EVENT_TYPES.EXECUTION_COMPLETED, eventCallback);
      handleEvent({ type: 'execution_completed', agent_id: 'test', execution_time_ms: 1000 });
      expect(eventCallback).toHaveBeenCalled();
    });

    it('應該支持 EXECUTION_FAILED 事件', () => {
      addEventListener(WS_EVENT_TYPES.EXECUTION_FAILED, eventCallback);
      handleEvent({ type: 'execution_failed', agent_id: 'test', error: 'Test error' });
      expect(eventCallback).toHaveBeenCalled();
    });

    it('應該支持 EXECUTION_STOPPED 事件', () => {
      addEventListener(WS_EVENT_TYPES.EXECUTION_STOPPED, eventCallback);
      handleEvent({ type: 'execution_stopped', agent_id: 'test', status: 'stopped' });
      expect(eventCallback).toHaveBeenCalled();
    });
  });

  describe('多個監聽器', () => {
    it('應該支持多個監聽器訂閱同一事件', () => {
      const callback1 = vi.fn();
      const callback2 = vi.fn();

      addEventListener(WS_EVENT_TYPES.EXECUTION_COMPLETED, callback1);
      addEventListener(WS_EVENT_TYPES.EXECUTION_COMPLETED, callback2);

      handleEvent({ type: 'execution_completed', agent_id: 'test', execution_time_ms: 1000 });

      expect(callback1).toHaveBeenCalled();
      expect(callback2).toHaveBeenCalled();
    });

    it('移除一個監聽器不應該影響其他監聽器', () => {
      const callback1 = vi.fn();
      const callback2 = vi.fn();

      const unsubscribe1 = addEventListener(WS_EVENT_TYPES.EXECUTION_COMPLETED, callback1);
      addEventListener(WS_EVENT_TYPES.EXECUTION_COMPLETED, callback2);

      unsubscribe1();

      handleEvent({ type: 'execution_completed', agent_id: 'test', execution_time_ms: 1000 });

      expect(callback1).not.toHaveBeenCalled();
      expect(callback2).toHaveBeenCalled();
    });
  });

  describe('錯誤處理', () => {
    it('應該處理沒有事件類型的消息', () => {
      // 不應該拋出錯誤
      expect(() => {
        handleEvent({ some_field: 'value' });
      }).not.toThrow();
    });

    it('應該處理回調中的錯誤', () => {
      const errorCallback = () => {
        throw new Error('Test error in callback');
      };

      addEventListener(WS_EVENT_TYPES.EXECUTION_STARTED, errorCallback);

      // 不應該拋出錯誤，應該被捕獲
      expect(() => {
        handleEvent({ type: 'execution_started', agent_id: 'test' });
      }).not.toThrow();
    });
  });
});
