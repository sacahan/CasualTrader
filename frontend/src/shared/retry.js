/**
 * Execution Error Retry Logic
 *
 * 管理 Agent 執行的重試邏輯和錯誤恢復
 */

export class ExecutionRetryManager {
  constructor(maxRetries = 3, delayMs = 1000) {
    this.maxRetries = maxRetries;
    this.delayMs = delayMs;
    this.retryCount = new Map(); // agent_id -> count
    this.lastError = new Map(); // agent_id -> error
  }

  /**
   * 是否可以重試
   */
  canRetry(agentId) {
    const count = this.retryCount.get(agentId) || 0;
    return count < this.maxRetries;
  }

  /**
   * 記錄重試
   */
  recordRetry(agentId, error) {
    const count = this.retryCount.get(agentId) || 0;
    this.retryCount.set(agentId, count + 1);
    this.lastError.set(agentId, error);
  }

  /**
   * 重置重試計數
   */
  reset(agentId) {
    this.retryCount.delete(agentId);
    this.lastError.delete(agentId);
  }

  /**
   * 獲取重試次數
   */
  getRetryCount(agentId) {
    return this.retryCount.get(agentId) || 0;
  }

  /**
   * 獲取最後的錯誤
   */
  getLastError(agentId) {
    return this.lastError.get(agentId);
  }

  /**
   * 計算等待時間（指數退避）
   */
  getBackoffDelay(agentId) {
    const count = this.getRetryCount(agentId);
    return this.delayMs * Math.pow(2, count);
  }
}

/**
 * 全局重試管理器實例
 */
export const executionRetryManager = new ExecutionRetryManager();

/**
 * 執行帶重試的 Agent 動作
 */
export async function executeWithRetry(agentId, mode, executeFunc, onRetry = null) {
  const manager = executionRetryManager;

  while (manager.canRetry(agentId)) {
    try {
      // 執行操作
      const result = await executeFunc(agentId, mode);
      manager.reset(agentId); // 成功則重置計數
      return result;
    } catch (error) {
      manager.recordRetry(agentId, error);

      if (manager.canRetry(agentId)) {
        // 還可以重試
        const delay = manager.getBackoffDelay(agentId);
        const retryCount = manager.getRetryCount(agentId);

        if (onRetry) {
          onRetry({
            agentId,
            error,
            retryCount,
            nextRetryIn: delay,
          });
        }

        // 等待後重試
        await new Promise((resolve) => setTimeout(resolve, delay));
      } else {
        // 已達最大重試次數，拋出錯誤
        throw new Error(`執行失敗 (已重試 ${manager.getRetryCount(agentId)} 次): ${error.message}`);
      }
    }
  }

  throw new Error('執行失敗：重試管理器異常');
}

/**
 * 判斷是否為可重試的錯誤
 */
export function isRetryableError(error) {
  // 網路錯誤、超時等可重試
  const retryableMessages = [
    'Network',
    'timeout',
    'temporarily',
    'unavailable',
    'connection refused',
  ];

  const errorMessage = error.message?.toLowerCase() || '';
  return retryableMessages.some((msg) => errorMessage.includes(msg.toLowerCase()));
}

/**
 * 判斷是否為致命錯誤（不應重試）
 */
export function isFatalError(error) {
  // 認證、授權、驗證錯誤等不應重試
  const fatalPatterns = ['unauthorized', 'forbidden', 'not found', 'invalid', 'malformed'];

  const errorMessage = error.message?.toLowerCase() || '';
  return fatalPatterns.some((pattern) => errorMessage.includes(pattern));
}
