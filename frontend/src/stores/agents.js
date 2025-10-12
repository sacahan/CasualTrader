import { writable, derived, get } from 'svelte/store';
import { apiClient } from '../lib/api.js';
import { extractErrorMessage } from '../lib/utils.js';

/**
 * Agent Store
 *
 * 管理 Agent 狀態,提供 CRUD 操作和配置鎖定機制
 * 符合 FRONTEND_IMPLEMENTATION.md 規格
 */

// 原始 agents 資料
export const agents = writable([]);

// 當前選中的 agent ID
export const selectedAgentId = writable(null);

// 載入狀態
export const loading = writable(false);

// 錯誤訊息
export const error = writable(null);

// 衍生 store: 當前選中的 agent
export const selectedAgent = derived([agents, selectedAgentId], ([$agents, $selectedAgentId]) => {
  if (!$selectedAgentId) return null;
  return $agents.find((agent) => agent.agent_id === $selectedAgentId);
});

// 衍生 store: 執行中的 agents
export const runningAgents = derived(agents, ($agents) =>
  $agents.filter((agent) => agent.status === 'running')
);

// 衍生 store: 閒置的 agents
export const idleAgents = derived(agents, ($agents) =>
  $agents.filter((agent) => agent.status === 'idle')
);

/**
 * 載入所有 agents
 */
export async function loadAgents() {
  loading.set(true);
  error.set(null);

  try {
    const data = await apiClient.getAgents();
    // 映射後端的 id 欄位到前端的 agent_id
    const mappedAgents = (data.agents || []).map((agent) => ({
      ...agent,
      agent_id: agent.id || agent.agent_id,
    }));
    agents.set(mappedAgents);
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to load agents:', err);
  } finally {
    loading.set(false);
  }
}

/**
 * 載入單一 agent 詳細資料
 */
export async function loadAgent(agentId) {
  loading.set(true);
  error.set(null);

  try {
    const rawAgent = await apiClient.getAgent(agentId);
    // 映射後端的 id 欄位到前端的 agent_id
    const agent = {
      ...rawAgent,
      agent_id: rawAgent.id || rawAgent.agent_id,
    };

    // 更新 agents 列表中的對應項目
    agents.update((list) => {
      const index = list.findIndex((a) => a.agent_id === agentId);
      if (index >= 0) {
        list[index] = agent;
      } else {
        list.push(agent);
      }
      return list;
    });

    return agent;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to load agent:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 創建新 agent
 */
export async function createAgent(agentData) {
  loading.set(true);
  error.set(null);

  try {
    const rawAgent = await apiClient.createAgent(agentData);
    // 映射後端的 id 欄位到前端的 agent_id
    const newAgent = {
      ...rawAgent,
      agent_id: rawAgent.id || rawAgent.agent_id,
    };

    // 添加到 agents 列表
    agents.update((list) => [...list, newAgent]);

    // 自動選中新創建的 agent
    selectedAgentId.set(newAgent.agent_id);

    return newAgent;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to create agent:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 更新 agent 配置
 * 注意:執行中的 agent 會被拒絕更新(配置鎖定機制)
 */
export async function updateAgent(agentId, updates) {
  loading.set(true);
  error.set(null);

  // 檢查配置鎖定
  const agent = get(agents).find((a) => a.agent_id === agentId);
  if (agent && agent.status === 'running') {
    const lockError = '無法更新執行中的 Agent 配置。請先停止 Agent。';
    error.set(lockError);
    loading.set(false);
    throw new Error(lockError);
  }

  try {
    const rawAgent = await apiClient.updateAgent(agentId, updates);
    // 映射後端的 id 欄位到前端的 agent_id
    const updatedAgent = {
      ...rawAgent,
      agent_id: rawAgent.id || rawAgent.agent_id,
    };

    // 更新 agents 列表
    agents.update((list) => list.map((a) => (a.agent_id === agentId ? updatedAgent : a)));

    return updatedAgent;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to update agent:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 刪除 agent
 */
export async function deleteAgent(agentId) {
  loading.set(true);
  error.set(null);

  try {
    await apiClient.deleteAgent(agentId);

    // 從列表中移除
    agents.update((list) => list.filter((a) => a.agent_id !== agentId));

    // 如果刪除的是當前選中的 agent,清除選中狀態
    if (get(selectedAgentId) === agentId) {
      selectedAgentId.set(null);
    }
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to delete agent:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 啟動 agent
 */
export async function startAgent(agentId, config = {}) {
  loading.set(true);
  error.set(null);

  try {
    const result = await apiClient.startAgent(agentId, config);

    // 更新 agent 狀態為 running
    agents.update((list) =>
      list.map((a) => (a.agent_id === agentId ? { ...a, status: 'running' } : a))
    );

    return result;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to start agent:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 停止 agent
 */
export async function stopAgent(agentId) {
  loading.set(true);
  error.set(null);

  try {
    const result = await apiClient.stopAgent(agentId);

    // 更新 agent 狀態為 idle
    agents.update((list) =>
      list.map((a) => (a.agent_id === agentId ? { ...a, status: 'idle' } : a))
    );

    return result;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to stop agent:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 執行 agent 週期
 */
export async function executeAgent(agentId, mode = null) {
  loading.set(true);
  error.set(null);

  try {
    const result = await apiClient.executeAgent(agentId, mode);
    return result;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to execute agent:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 切換 agent 模式
 */
export async function switchAgentMode(agentId, mode) {
  loading.set(true);
  error.set(null);

  try {
    const result = await apiClient.switchAgentMode(agentId, mode);

    // 更新 agent 的 current_mode
    agents.update((list) =>
      list.map((a) => (a.agent_id === agentId ? { ...a, current_mode: mode } : a))
    );

    return result;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to switch agent mode:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 重置 agent (清除投資組合和歷史記錄)
 */
export async function resetAgent(agentId) {
  loading.set(true);
  error.set(null);

  try {
    const result = await apiClient.resetAgent(agentId);

    // 重新載入 agent 資料
    await loadAgent(agentId);

    return result;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to reset agent:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 選中某個 agent
 */
export function selectAgent(agentId) {
  selectedAgentId.set(agentId);
}

/**
 * 清除選中狀態
 */
export function clearSelection() {
  selectedAgentId.set(null);
}

/**
 * 清除錯誤訊息
 */
export function clearError() {
  error.set(null);
}

/**
 * 檢查 agent 是否可以被編輯 (配置鎖定檢查)
 */
export function isAgentEditable(agentId) {
  const agent = get(agents).find((a) => a.agent_id === agentId);
  return agent ? agent.status !== 'running' : false;
}
