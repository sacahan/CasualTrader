/**
 * AI Models API Service
 *
 * 提供 AI 模型的 API 調用功能
 */

import { API_BASE_URL } from '../constants.js';

/**
 * 獲取所有可用的 AI 模型列表
 *
 * @returns {Promise<{total: number, models: Array}>} 模型列表
 */
export async function fetchAvailableModels() {
  const response = await fetch(`${API_BASE_URL}/api/models/available`);

  if (!response.ok) {
    throw new Error(`Failed to fetch available models: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * 獲取按分組的 AI 模型列表
 *
 * @returns {Promise<{groups: Object}>} 分組的模型列表
 */
export async function fetchAvailableModelsGrouped() {
  const response = await fetch(`${API_BASE_URL}/api/models/available/grouped`);

  if (!response.ok) {
    throw new Error(`Failed to fetch grouped models: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * 根據 model_key 獲取特定模型資訊
 *
 * @param {string} modelKey - 模型唯一識別碼
 * @returns {Promise<Object>} 模型詳細資訊
 */
export async function fetchModelByKey(modelKey) {
  const response = await fetch(`${API_BASE_URL}/api/models/${modelKey}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Model '${modelKey}' not found`);
    }
    throw new Error(`Failed to fetch model: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * 獲取所有 AI 模型列表 (包含禁用的)
 *
 * @param {boolean} includeDisabled - 是否包含已禁用的模型
 * @returns {Promise<{total: number, models: Array}>} 模型列表
 */
export async function fetchAllModels(includeDisabled = false) {
  const url = new URL(`${API_BASE_URL}/api/models/`);
  url.searchParams.append('include_disabled', includeDisabled);

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch all models: ${response.statusText}`);
  }

  return await response.json();
}

/**
 * 將分組的模型列表轉換為 Select 組件格式
 *
 * @param {Object} groups - 分組的模型列表 {groupName: [models]}
 * @returns {Object} Select 組件所需的格式 {groupName: [{value, label}]}
 */
export function transformModelsForSelect(groups) {
  const result = {};

  for (const [groupName, models] of Object.entries(groups)) {
    result[groupName] = models.map((model) => ({
      value: model.model_key,
      label: model.display_name,
    }));
  }

  return result;
}

/**
 * 創建模型的簡單映射表
 *
 * @param {Array} models - 模型列表
 * @returns {Object} {model_key: display_name}
 */
export function createModelLabelsMap(models) {
  const labels = {};

  for (const model of models) {
    labels[model.model_key] = model.display_name;
  }

  return labels;
}
