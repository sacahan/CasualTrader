---
mode: agent
description: "Create a pre-commit hook to enforce code quality standards before committing changes."
---

# 建立 Pre-commit Hook 步驟如下

## 1. 在專案根目錄 (${workspaceFolder}) 下使用系統/global 的 pip 安裝 pre-commit

- 檢查是否已安裝 pip（使用系統 / global）

```zsh
# 檢查系統是否有 pip（global）
if ! command -v pip &> /dev/null; then
    echo "pip 未安裝，請先安裝系統的 pip（global）。"
    exit 1
fi
```

- (可選) 使用系統（global）pip 安裝 pre-commit

```zsh
# 檢查是否已安裝 pre-commit（使用系統 / global）

if ! command -v pre-commit &> /dev/null; then
  echo "pre-commit 未安裝，將使用 pip 安裝 pre-commit。"
  # 將 pre-commit 安裝到系統環境（global）
  # macOS / Linux（如需安裝到系統環境可能需要 sudo）
  pip install pre-commit
  pre-commit --version
else
  echo "pre-commit 已安裝，跳過安裝步驟。"
fi
```

- 使用系統/global 的 pre-commit 來安裝 hook 並執行

```zsh
# 安裝 Git hook（會使用系統的 pre-commit 執行）
pre-commit install
```

## 2. 在 ${workspaceFolderBasename} 根目錄新增 .pre-commit-config.yaml，並增加以下內容

```yaml
# .pre-commit-config.yaml 範例
repos:
  # 使用 pre-commit 官方提供的常用 hook 工具集
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0 # 使用的版本
    hooks:
      - id: trailing-whitespace # 移除每行結尾多餘的空白
      - id: end-of-file-fixer # 確保檔案結尾有一個換行符號
      - id: check-yaml # 驗證 YAML 格式是否正確
      - id: check-added-large-files # 阻止加入超過預設大小的新檔案
        args: ["--maxkb=5000"] # 調整為 5000KB
      - id: check-merge-conflict # 檢查是否有合併衝突的標記
```

## 3. (可選) 依據程式語言增加額外的 hook

```yaml
repos:
  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.5
    hooks:
      - id: ruff-format # 格式化 Python 檔案（類似 black）
      - id: ruff # 使用 Ruff 檢查 Python 程式碼品質（如 flake8）
        args: ["--fix"]

  # Java
  - repo: https://github.com/detekt/detekt
    rev: v1.22.0
    hooks:
      - id: detekt # 檢查 Java 程式碼品質

  # JavaScript / TypeScript
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.45.0
    hooks:
      - id: eslint # 檢查 JavaScript/TypeScript 程式碼品質
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier # 格式化前端檔案

  # C#
  - repo: https://github.com/josefpihrt/pre-commit-hooks
    rev: v1.0.0
    hooks:
      - id: dotnet-format # 格式化 C# 檔案
      - id: dotnet-analyzers # 使用 .NET 分析器檢查 C# 程式碼品質
```

## 4. 手動測試所有檔案

```zsh
pre-commit run --all-files
```

Let's do it step by step!
