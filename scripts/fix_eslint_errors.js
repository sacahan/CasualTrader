#!/usr/bin/env node

/**
 * 自動修正 ESLint 錯誤的腳本
 * 主要修正 no-inner-declarations 問題
 */

const fs = require('fs');
const path = require('path');

const svelteFiles = [
    'frontend/src/components/Agent/AgentCreationForm.svelte',
    'frontend/src/components/Agent/AgentCard.svelte',
    'frontend/src/components/Agent/AgentGrid.svelte',
    'frontend/src/components/Agent/StrategyHistoryView.svelte',
    'frontend/src/components/UI/StatusIndicator.svelte',
    'frontend/src/components/UI/Modal.svelte',
    'frontend/src/components/Layout/NotificationToast.svelte',
];

function fixSvelteFile(filePath) {
    console.log(`Processing ${filePath}...`);

    const fullPath = path.join('/Users/sacahan/Documents/workspace/CasualTrader', filePath);
    if (!fs.existsSync(fullPath)) {
        console.log(`File ${fullPath} not found, skipping...`);
        return;
    }

    let content = fs.readFileSync(fullPath, 'utf8');

    // 找到所有函數定義的位置
    const lines = content.split('\n');
    const scriptStartIndex = lines.findIndex(line => line.trim() === '<script>');
    const scriptEndIndex = lines.findIndex(line => line.trim() === '</script>');

    if (scriptStartIndex === -1 || scriptEndIndex === -1) {
        console.log(`No script tag found in ${filePath}`);
        return;
    }

    const scriptLines = lines.slice(scriptStartIndex + 1, scriptEndIndex);

    // 提取所有函數定義
    const functions = [];
    let currentFunction = null;
    let braceCount = 0;
    let inFunction = false;

    for (let i = 0; i < scriptLines.length; i++) {
        const line = scriptLines[i];
        const trimmed = line.trim();

        // 檢查是否是函數定義開始
        if (trimmed.match(/^\s*(async\s+)?function\s+\w+\s*\(/)) {
            if (currentFunction) {
                functions.push(currentFunction);
            }
            currentFunction = {
                startIndex: i,
                lines: [line],
                indentLevel: line.length - line.trimStart().length
            };
            inFunction = true;
            braceCount = (line.match(/{/g) || []).length - (line.match(/}/g) || []).length;
        } else if (inFunction && currentFunction) {
            currentFunction.lines.push(line);
            braceCount += (line.match(/{/g) || []).length - (line.match(/}/g) || []).length;

            if (braceCount === 0) {
                currentFunction.endIndex = i;
                functions.push(currentFunction);
                currentFunction = null;
                inFunction = false;
            }
        }
    }

    if (currentFunction) {
        functions.push(currentFunction);
    }

    console.log(`Found ${functions.length} functions in ${filePath}`);

    // 如果沒有函數需要移動，跳過
    if (functions.length === 0) {
        return;
    }

    // 重新組織代碼：將函數移到 onMount/onDestroy 之前
    const newScriptLines = [];
    const nonFunctionLines = [];

    // 收集非函數的行
    for (let i = 0; i < scriptLines.length; i++) {
        const isPartOfFunction = functions.some(func =>
            i >= func.startIndex && i <= func.endIndex
        );

        if (!isPartOfFunction) {
            nonFunctionLines.push(scriptLines[i]);
        }
    }

    // 找到合適的位置插入函數（在 onMount 之前）
    let insertPosition = nonFunctionLines.length;
    for (let i = 0; i < nonFunctionLines.length; i++) {
        if (nonFunctionLines[i].trim().startsWith('onMount(') ||
            nonFunctionLines[i].trim().startsWith('onDestroy(') ||
            nonFunctionLines[i].trim().startsWith('$effect(')) {
            insertPosition = i;
            break;
        }
    }

    // 重新組織內容
    newScriptLines.push(...nonFunctionLines.slice(0, insertPosition));

    // 添加函數定義（帶註釋）
    if (functions.length > 0) {
        newScriptLines.push('  // 函數定義 - 移到根層級以符合 eslint no-inner-declarations 規則');
        functions.forEach(func => {
            newScriptLines.push(...func.lines);
        });
        newScriptLines.push('');
    }

    newScriptLines.push(...nonFunctionLines.slice(insertPosition));

    // 重建完整檔案
    const newLines = [
        ...lines.slice(0, scriptStartIndex + 1),
        ...newScriptLines,
        ...lines.slice(scriptEndIndex)
    ];

    const newContent = newLines.join('\n');

    // 只有當內容真的改變時才寫入
    if (newContent !== content) {
        fs.writeFileSync(fullPath, newContent, 'utf8');
        console.log(`Fixed ${filePath}`);
    } else {
        console.log(`No changes needed for ${filePath}`);
    }
}

// 處理所有檔案
svelteFiles.forEach(fixSvelteFile);

console.log('ESLint error fixing completed!');
