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
   * Start an agent
   */
  startAgent(agentId, config = {}) {
    return this.request(`/api/agents/${agentId}/start`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  /**
   * Stop an agent
   */
  stopAgent(agentId) {
    return this.request(`/api/agents/${agentId}/stop`, {
      method: 'POST',
    });
  }

  /**
   * Execute agent cycle
   */
  executeAgent(agentId, mode = null) {
    const body = mode ? { mode } : {};
    return this.request(`/api/agents/${agentId}/execute`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Switch agent mode
   */
  switchAgentMode(agentId, mode) {
    return this.request(`/api/agents/${agentId}/mode`, {
      method: 'POST',
      body: JSON.stringify({ mode }),
    });
  }

  /**
   * Reset agent (clear portfolio and history)
   */
  resetAgent(agentId) {
    return this.request(`/api/agents/${agentId}/reset`, {
      method: 'POST',
    });
  }

  // ========== Portfolio & Trading APIs ==========

  /**
   * Get agent portfolio
   */
  getPortfolio(agentId) {
    return this.request(`/api/trading/agents/${agentId}/portfolio`);
  }

  /**
   * Get agent trades
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
   */
  getPerformance(agentId) {
    return this.request(`/api/trading/agents/${agentId}/performance`);
  }

  /**
   * Get agent holdings
   */
  getHoldings(agentId) {
    return this.request(`/api/trading/agents/${agentId}/holdings`);
  }

  /**
   * Get agent transactions
   */
  getTransactions(agentId, limit = 50, offset = 0) {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    return this.request(`/api/trading/agents/${agentId}/transactions?${params}`);
  }

  // ========== Strategy Change APIs ==========

  /**
   * Get strategy changes
   */
  getStrategyChanges(agentId, limit = 50, offset = 0, changeType = null) {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (changeType) params.append('change_type', changeType);
    return this.request(`/api/trading/agents/${agentId}/strategy-changes?${params}`);
  }

  /**
   * Get latest strategy
   */
  getLatestStrategy(agentId) {
    return this.request(`/api/trading/agents/${agentId}/strategy-changes/latest`);
  }

  /**
   * Get strategy evolution summary
   */
  getStrategyEvolution(agentId) {
    return this.request(`/api/trading/agents/${agentId}/strategy-changes/evolution`);
  }

  // ========== Market APIs ==========

  /**
   * Get market status
   */
  getMarketStatus() {
    return this.request('/api/trading/market/status');
  }

  /**
   * Get stock quote
   */
  getStockQuote(ticker) {
    return this.request(`/api/trading/market/quote/${ticker}`);
  }

  /**
   * Get market indices
   */
  getMarketIndices() {
    return this.request('/api/trading/market/indices');
  }

  // ========== System APIs ==========

  /**
   * Health check
   */
  healthCheck() {
    return this.request('/api/health');
  }

  /**
   * Get system stats
   */
  getSystemStats() {
    return this.request('/api/system/stats');
  }
}

// Create singleton instance
export const apiClient = new APIClient();

// Export class for testing
export { APIClient };
