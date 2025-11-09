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

  /**
   * Start an agent in a specific mode (async, returns session_id)
   * Note: 後端路徑為 POST /api/agent-execution/{agent_id}/start
   * 回應包含: { success, session_id, mode, message }
   * @param {string} agentId - Agent ID
   * @param {string} mode - 執行模式 (TRADING | REBALANCING)
   * @returns {Promise<{success: boolean, session_id: string, mode: string, message: string}>}
   */
  startAgent(agentId, mode = 'TRADING') {
    const body = {
      mode,
    };
    return this.request(`/api/agent-execution/${agentId}/start`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Stop an agent
   * Note: 後端路徑為 /api/agent-execution/{agent_id}/stop
   */
  stopAgent(agentId) {
    return this.request(`/api/agent-execution/${agentId}/stop`, {
      method: 'POST',
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
    let endpoint = `/api/agent-execution/${agentId}/history?limit=${limit}`;
    if (statusFilter) {
      endpoint += `&status_filter=${statusFilter}`;
    }
    return this.request(endpoint);
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
   * Note: 後端路徑為 POST /api/agents/{agent_id}/mode
   * mode 作為查詢參數傳遞
   */
  switchAgentMode(agentId, mode) {
    return this.request(`/api/agents/${agentId}/mode?mode=${mode}`, {
      method: 'POST',
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
    return this.request(`/api/trading/agents/${agentId}/trades?limit=${limit}&offset=${offset}`);
  }

  /**
   * Get agent performance metrics
   * Note: 後端已實現 GET /api/trading/agents/{agent_id}/performance
   */
  getPerformance(agentId) {
    return this.request(`/api/trading/agents/${agentId}/performance`);
  }

  /**
   * Get agent performance history for chart display
   * Returns historical performance data in time series format
   * Note: 後端已實現 GET /api/trading/agents/{agent_id}/performance-history
   */
  getPerformanceHistory(agentId, limit = 30, order = 'asc') {
    return this.request(
      `/api/trading/agents/${agentId}/performance-history?limit=${limit}&order=${order}`
    );
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
    return this.request(
      `/api/trading/agents/${agentId}/transactions?limit=${limit}&offset=${offset}`
    );
  }

  // ========== System APIs ==========

  /**
   * Health check
   * Note: 後端路徑為 /api/health
   */
  healthCheck() {
    return this.request('/api/health');
  }

  // ========== Market Data APIs ==========

  /**
   * Get market status
   * Note: 後端路徑為 /api/trading/market/status
   */
  getMarketStatus() {
    return this.request('/api/trading/market/status');
  }

  /**
   * Get stock quote
   * Note: 後端路徑為 /api/trading/market/quote/{ticker}
   */
  getStockQuote(ticker) {
    return this.request(`/api/trading/market/quote/${ticker}`);
  }

  /**
   * Get market indices
   * Note: 後端路徑為 /api/trading/market/indices
   */
  getMarketIndices() {
    return this.request('/api/trading/market/indices');
  }

  // ========== AI Models APIs ==========

  /**
   * Get available AI models
   * Note: 後端路徑為 /api/models/available
   */
  getAvailableModels() {
    return this.request('/api/models/available');
  }

  /**
   * Get available AI models grouped
   * Note: 後端路徑為 /api/models/available/grouped
   */
  getAvailableModelsGrouped() {
    return this.request('/api/models/available/grouped');
  }

  /**
   * Get specific AI model by key
   * Note: 後端路徑為 /api/models/{model_key}
   */
  getModelByKey(modelKey) {
    return this.request(`/api/models/${modelKey}`);
  }

  /**
   * Get all AI models (including disabled)
   * Note: 後端路徑為 /api/models/?include_disabled={true|false}
   */
  getAllModels(includeDisabled = false) {
    return this.request(`/api/models/?include_disabled=${includeDisabled}`);
  }
}

// Create singleton instance
export const apiClient = new APIClient();

// Export class for testing
export { APIClient };
