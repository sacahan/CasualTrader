---
mode: agent
description: "Initialize a development environment with Git repository, pre-commit hook, .gitignore, and .editorconfig."
---

# 開發環境初始化的步驟如下

## 1. 初始化 Git 儲存庫

在終端機中，進入專案目錄 (${workspaceFolder})，執行以下指令：

```zsh
git init
```

## 2. 建立Pre-commit Hook

請參考 #file:./create_pre_commit.prompt.md 的相關步驟來設定 Pre-commit Hook。
這將有助於在提交前自動檢查和格式化代碼。

## 3. 新增 .gitignore 檔案

請參考 #file:./create_gitignore.prompt.md 的相關步驟來建立 `.gitignore` 檔案。
這將有助於忽略不需要提交到 Git 的檔案和目錄。

## 4. 新增 .editorconfig 檔案

在 ${workspaceFolderBasename} 目錄下新增 `.editorconfig` 檔案，並加入以下內容以統一編碼風格：

```editorconfig
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true
```

這將確保所有開發人員在不同編輯器中使用一致的格式。

## 5. 進行首次檔案提交

```zsh
git add .
git commit -m "Initial commit"
```

## 6. 設定遠端儲存庫（可選）

````zsh
git remote add origin <遠端儲存庫 URL>
git branch -M main
git push -u origin main
```zsh
git remote add origin <遠端儲存庫 URL>
git branch -M main
git push -u origin main
````

```zsh
git remote add origin <遠端儲存庫 URL>
git branch -M main
git push -u origin main
```

完成以上步驟後，即提示用戶已成功建立一個基本的開發環境，並且已經設定好 Git 儲存庫和 Pre-commit Hook。接下來可以開始進行專案開發工作。

Let's do it step by step!
