---
mode: "agent"
---

# Pre-commit 命令執行

## 功能概述

執行 pre-commit 命令以確保在提交代碼之前，所有的代碼質量標準都已經被檢查和修正。這包括自動格式化代碼、檢查語法錯誤、移除多餘的空白等。

## 執行步驟

- 確保虛擬環境已經啟動。

```bash
cd ${workspaceFolder}
source .venv/bin/activate
```

- 執行 pre-commit 命令：

```bash
pre-commit run --all-files
```

- 執行後行為
  根據 pre-commit 執行結果，檢查輸出是否有錯誤或警告。如果有錯誤，請根據提示修正代碼，然後再次執行 pre-commit 命令。
