/**
 * AI Models Store
 *
 * 管理 AI 模型列表的狀態
 * 提供動態獲取和緩存模型數據的功能
 */

import { writable, derived, get } from 'svelte/store';
import {
  fetchAvailableModelsGrouped,
  transformModelsForSelect,
  createModelLabelsMap,
} from '../shared/api/models.js';

// ==========================================
// Store 定義
// ==========================================

/**
 * 模型分組數據 store
 * 格式: {groupName: [models]}
 */
export const modelGroups = writable({});

/**
 * 模型標籤映射 store
 * 格式: {model_key: display_name}
 */
export const modelLabels = writable({});

/**
 * 加載狀態
 */
export const modelsLoading = writable(false);

/**
 * 錯誤訊息
 */
export const modelsError = writable(null);

/**
 * 最後更新時間
 */
export const modelsLastUpdated = writable(null);

// ==========================================
// Derived Stores
// ==========================================

/**
 * Select 組件所需格式的模型選項
 * 格式: {groupName: [{value, label}]}
 */
export const modelOptionsForSelect = derived(modelGroups, ($modelGroups) => {
  return transformModelsForSelect($modelGroups);
});

/**
 * 所有模型的扁平列表
 */
export const allModels = derived(modelGroups, ($modelGroups) => {
  const models = [];

  for (const group of Object.values($modelGroups)) {
    models.push(...group);
  }

  return models;
});

/**
 * 模型總數
 */
export const modelCount = derived(allModels, ($allModels) => {
  return $allModels.length;
});

// ==========================================
// Actions
// ==========================================

/**
 * 從 API 獲取模型列表並更新 store
 *
 * @param {boolean} forceRefresh - 是否強制刷新(忽略緩存)
 * @returns {Promise<void>}
 */
export async function loadModels(forceRefresh = false) {
  // 如果已有數據且不強制刷新,則跳過
  const currentGroups = get(modelGroups);
  if (!forceRefresh && Object.keys(currentGroups).length > 0) {
    // 模型已載入，略過重新整理
    return;
  }

  modelsLoading.set(true);
  modelsError.set(null);

  try {
    const response = await fetchAvailableModelsGrouped();
    const groups = response.groups;

    // 更新模型分組
    modelGroups.set(groups);

    // 創建標籤映射
    const labels = {};
    for (const models of Object.values(groups)) {
      Object.assign(labels, createModelLabelsMap(models));
    }
    modelLabels.set(labels);

    // 更新最後更新時間
    modelsLastUpdated.set(new Date());
    // 成功載入模型群組
  } catch (error) {
    console.error('Failed to load models:', error);
    modelsError.set(error.message);
  } finally {
    modelsLoading.set(false);
  }
}

/**
 * 根據 model_key 獲取模型顯示名稱
 *
 * @param {string} modelKey - 模型 key
 * @returns {string} 模型顯示名稱,如果找不到則返回 modelKey
 */
export function getModelDisplayName(modelKey) {
  const labels = get(modelLabels);
  return labels[modelKey] || modelKey;
}

/**
 * 檢查模型是否存在
 *
 * @param {string} modelKey - 模型 key
 * @returns {boolean} 是否存在
 */
export function hasModel(modelKey) {
  const labels = get(modelLabels);
  return modelKey in labels;
}

/**
 * 獲取特定分組的模型列表
 *
 * @param {string} groupName - 分組名稱
 * @returns {Array} 模型列表
 */
export function getModelsByGroup(groupName) {
  const groups = get(modelGroups);
  return groups[groupName] || [];
}

/**
 * 清除模型數據緩存
 */
export function clearModelsCache() {
  modelGroups.set({});
  modelLabels.set({});
  modelsLastUpdated.set(null);
  modelsError.set(null);
}

// ==========================================
// 初始化
// ==========================================

/**
 * 自動加載模型(在應用啟動時調用)
 */
export function initializeModels() {
  loadModels(false);
}
