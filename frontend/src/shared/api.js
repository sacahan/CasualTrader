import { API_BASE_URL } from './constants.js';
import { extractErrorMessage } from './utils.js';

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      // Handle non-2xx responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message =
          errorData.error?.message || errorData.message || `HTTP Error ${response.status}`;
        throw new Error(message);
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw new Error(extractErrorMessage(error));
    }
  }

  // ========== Agent Management APIs ==========

  /**
   * Get all agents
   */
  getAgents() {
    return this.request('/api/agents');
  }

  /**
   * Get agent by ID
   */
  getAgent(agentId) {
    return this.request(`/api/agents/${agentId}`);
  }

  /**
   * Create a new agent
   */
  createAgent(agentData) {
    return this.request('/api/agents', {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  /**
   * Update agent configuration
   */
  updateAgent(agentId, updates) {
    return this.request(`/api/agents/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete an agent
   */
  deleteAgent(agentId) {
    return this.request(`/api/agents/${agentId}`, {
      method: 'DELETE',
    });
  }

  // ========== Agent Control APIs ==========

  // TODO: 以下啟動/停止方法已暫時註解，因後端 API 已移除
  // 未來需重新實現 Agent 生命週期管理

  // /**
  //  * Start an agent
  //  */
  // startAgent(agentId, config = {}) {
  //   return this.request(`/api/agents/${agentId}/start`, {
  //     method: 'POST',
  //     body: JSON.stringify(config),
  //   });
  // }

  // /**
  //  * Stop an agent
  //  */
  // stopAgent(agentId) {
  //   return this.request(`/api/agents/${agentId}/stop`, {
  //     method: 'POST',
  //   });
  // }

  /**
   * Execute agent cycle
   * Note: 後端路徑為 /api/agent-execution/{agent_id}/execute
   */
  executeAgent(agentId, task = '執行交易週期', mode = null, context = null) {
    const body = {
      task,
      mode,
      context,
    };
    return this.request(`/api/agent-execution/${agentId}/execute`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Get agent status
   * Note: 後端路徑為 /api/agent-execution/{agent_id}/status
   */
  getAgentStatus(agentId) {
    return this.request(`/api/agent-execution/${agentId}/status`);
  }

  /**
   * Get execution history
   * Note: 後端路徑為 /api/agent-execution/{agent_id}/history
   */
  getExecutionHistory(agentId, limit = 20, statusFilter = null) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (statusFilter) params.append('status_filter', statusFilter);
    return this.request(`/api/agent-execution/${agentId}/history?${params}`);
  }

  /**
   * Get session details
   * Note: 後端路徑為 /api/agent-execution/{agent_id}/sessions/{session_id}
   */
  getSessionDetails(agentId, sessionId) {
    return this.request(`/api/agent-execution/${agentId}/sessions/${sessionId}`);
  }

  /**
   * Get agent statistics
   * Note: 後端路徑為 /api/agent-execution/{agent_id}/statistics
   */
  getAgentStatistics(agentId) {
    return this.request(`/api/agent-execution/${agentId}/statistics`);
  }

  // ========== Agent Mode & Reset APIs ==========

  /**
   * Switch agent mode
   * Note: 後端已實現 POST /api/agents/{agent_id}/mode
   */
  switchAgentMode(agentId, mode) {
    return this.request(`/api/agents/${agentId}/mode`, {
      method: 'POST',
      body: JSON.stringify({ mode }),
    });
  }

  /**
   * Reset agent (clear portfolio and history)
   * Note: 後端已實現 POST /api/agents/{agent_id}/reset
   */
  resetAgent(agentId) {
    return this.request(`/api/agents/${agentId}/reset`, {
      method: 'POST',
    });
  }

  // ========== Portfolio & Trading APIs ==========

  /**
   * Get agent portfolio
   * Note: 後端已實現 GET /api/trading/agents/{agent_id}/portfolio
   */
  getPortfolio(agentId) {
    return this.request(`/api/trading/agents/${agentId}/portfolio`);
  }

  /**
   * Get agent trades
   * Note: 後端已實現 GET /api/trading/agents/{agent_id}/trades
   */
  getTrades(agentId, limit = 50, offset = 0) {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    return this.request(`/api/trading/agents/${agentId}/trades?${params}`);
  }

  /**
   * Get agent performance metrics
   * Note: 後端已實現 GET /api/trading/agents/{agent_id}/performance
   */
  getPerformance(agentId) {
    return this.request(`/api/trading/agents/${agentId}/performance`);
  }

  /**
   * Get agent holdings
   * Note: 後端已實現 GET /api/trading/agents/{agent_id}/holdings
   */
  getHoldings(agentId) {
    return this.request(`/api/trading/agents/${agentId}/holdings`);
  }

  /**
   * Get agent transactions
   * Note: 後端已實現 GET /api/trading/agents/{agent_id}/transactions
   */
  getTransactions(agentId, limit = 50, offset = 0) {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    return this.request(`/api/trading/agents/${agentId}/transactions?${params}`);
  }

  // ========== System APIs ==========

  /**
   * Health check
   */
  healthCheck() {
    return this.request('/api/health');
  }

  // ========== AI Models APIs ==========

  /**
   * Get available AI models
   */
  getAvailableModels() {
    return this.request('/api/models/available');
  }

  /**
   * Get available AI models grouped
   */
  getAvailableModelsGrouped() {
    return this.request('/api/models/available/grouped');
  }

  /**
   * Get specific AI model by key
   */
  getModelByKey(modelKey) {
    return this.request(`/api/models/${modelKey}`);
  }

  /**
   * Get all AI models (including disabled)
   */
  getAllModels(includeDisabled = false) {
    const params = new URLSearchParams({
      include_disabled: String(includeDisabled),
    });
    return this.request(`/api/models/?${params}`);
  }
}

// Create singleton instance
export const apiClient = new APIClient();

// Export class for testing
export { APIClient };
