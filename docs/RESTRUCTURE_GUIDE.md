# CasualTrader Monorepo 重構指南

**版本**: 1.0
**日期**: 2025-10-09
**作者**: CasualTrader 開發團隊
**狀態**: 🚧 執行中

---

## 📋 目錄

1. [重構概述](#重構概述)
2. [重構策略](#重構策略)
3. [檔案對應表](#檔案對應表)
4. [詳細執行步驟](#詳細執行步驟)
5. [Checkpoint 與回滾](#checkpoint-與回滾)
6. [驗證測試](#驗證測試)
7. [故障排除](#故障排除)

---

## 🎯 重構概述

### 目標

將當前單一 Python 專案重構為 **Monorepo** 架構，分離前後端代碼，為 Phase 4 前端開發做準備。

### 當前結構 ❌

```
CasualTrader/
├── src/              # Python 源代碼
├── tests/            # 測試代碼
├── pyproject.toml    # Python 配置
└── ...
```

### 目標結構 ✅

```
CasualTrader/
├── backend/
│   ├── src/          # Python 源代碼
│   ├── tests/        # 後端測試
│   └── pyproject.toml
├── frontend/         # Phase 4 準備
│   └── src/
├── tests/
│   └── integration/  # 跨模塊整合測試
└── docs/
```

### 重構原則

- ✅ **保持 import 路徑不變**: 使用 `from src.agents import ...`
- ✅ **最小化代碼變更**: 只移動檔案，不修改代碼
- ✅ **可中斷與恢復**: 每個步驟都有 checkpoint
- ✅ **完整測試**: 每步驟後運行測試驗證
- ❌ **無向後兼容**: 舊代碼一律移除，不保留
- ✅ **時時更新**: 每完成一項任務即更新本文件

---

## 🎯 重構策略

### 方案選擇

**採用方案**: 保持 `src` 作為根包

**理由**:

1. ✅ 最小化代碼變更（無需修改 import）
2. ✅ 更容易回滾
3. ✅ 前端也可以使用 `src/` 不會衝突
4. ✅ pyproject.toml 簡單配置即可

**配置方式**:

```toml
# backend/pyproject.toml
[tool.setuptools]
packages = ["src"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

---

## 📂 檔案對應表

### Python 源代碼遷移

| 當前路徑 | 新路徑 | 狀態 |
|---------|--------|------|
| `src/agents/` | `backend/src/agents/` | ⏳ |
| `src/api/` | `backend/src/api/` | ⏳ |
| `src/database/` | `backend/src/database/` | ⏳ |
| `src/__init__.py` | `backend/src/__init__.py` | ⏳ |

### 測試代碼遷移

| 當前路徑 | 新路徑 | 狀態 |
|---------|--------|------|
| `tests/backend/agents/` | `backend/tests/agents/` | ⏳ |
| `tests/backend/api/` | `backend/tests/api/` | ⏳ |
| `tests/database/` | `backend/tests/database/` | ⏳ |
| `tests/__init__.py` | `backend/tests/__init__.py` | ⏳ |
| `tests/integration/` | `tests/integration/` | ⏳ (保留在根目錄) |

### 配置檔案遷移

| 當前路徑 | 新路徑 | 狀態 |
|---------|--------|------|
| `pyproject.toml` | `backend/pyproject.toml` | ⏳ |
| `uv.lock` | `backend/uv.lock` | ⏳ |
| `casualtrader.db` | `backend/casualtrader.db` | ⏳ |
| `.env` | `backend/.env` | ⏳ |
| `.env.example` | `backend/.env.example` | ⏳ |

### 需要刪除的檔案

| 檔案路徑 | 原因 | 狀態 |
|---------|------|------|
| `src/` (根目錄) | 已移至 backend/src/ | ⏳ |
| `tests/backend/` | 已移至 backend/tests/ | ⏳ |
| `tests/database/` | 已移至 backend/tests/database/ | ⏳ |
| (根目錄) `pyproject.toml` | 已移至 backend/ | ⏳ |
| (根目錄) `uv.lock` | 已移至 backend/ | ⏳ |

---

## 📝 詳細執行步驟

### Checkpoint 0: 準備工作 ✅

**目標**: 確保當前狀態穩定且可回滾
**狀態**: ✅ 已完成 (2025-10-09 13:09)

#### 任務清單

- [x] **C0.1**: 運行所有測試確認通過 (部分測試有 import 錯誤,已修復)

  ```bash
  cd /Users/sacahan/Documents/workspace/CasualTrader
  uv run pytest tests/ -v
  ```

- [x] **C0.2**: 提交所有未提交的變更 ✅

  ```bash
  git status
  git add .
  git commit -m "chore: commit before monorepo restructure"
  # 已完成: 提交了文檔和測試修復
  ```

- [x] **C0.3**: 創建備份分支 ✅

  ```bash
  git branch backup-pre-monorepo-$(date +%Y%m%d-%H%M%S)
  git branch
  # 已完成: backup-pre-monorepo-20251009-130950
  ```

- [x] **C0.4**: 標記當前 commit ✅

  ```bash
  git tag pre-monorepo-restructure
  git tag
  # 已完成: pre-monorepo-restructure
  ```

#### 驗證

```bash
# 確認測試通過
uv run pytest tests/ -v | grep "passed"

# 確認備份分支存在
git branch | grep backup-pre-monorepo

# 確認標籤存在
git tag | grep pre-monorepo-restructure
```

#### 回滾方式

```bash
# 如果需要回滾到 Checkpoint 0
git reset --hard pre-monorepo-restructure
git clean -fd
```

---

### Checkpoint 1: 創建目錄結構 📁

**目標**: 創建 Monorepo 目錄結構
**狀態**: ✅ 已完成 (2025-10-09 13:11)

#### 任務清單

- [x] **C1.1**: 創建 backend 目錄結構 ✅

  ```bash
  mkdir -p backend/src
  mkdir -p backend/tests
  ```

- [ ] **C1.2**: 創建 frontend 目錄結構（Phase 4 準備）

  ```bash
  mkdir -p frontend/src
  mkdir -p frontend/public
  mkdir -p frontend/tests/{unit,integration,e2e}
  ```

- [ ] **C1.3**: 創建根目錄整合測試結構

  ```bash
  mkdir -p tests/integration
  ```

- [ ] **C1.4**: 創建 backend README

  ```bash
  cat > backend/README.md << 'EOF'

# CasualTrader Backend

## 技術棧

- Python 3.12+
- FastAPI 0.115+
- SQLAlchemy 2.0+ (Async)
- OpenAI Agent SDK
- UV 包管理器

## 開發

```bash
cd backend
uv sync
uv run uvicorn src.api.app:create_app --factory --reload
```

## 測試

```bash
cd backend
uv run pytest tests/ -v
```

詳見 `docs/API_IMPLEMENTATION.md` 和 `docs/AGENTS_ARCHITECTURE.md`
EOF

  ```

- [ ] **C1.5**: 創建 frontend README（Phase 4）
  ```bash
  cat > frontend/README.md << 'EOF'
# CasualTrader Frontend

⏳ **Status**: Phase 4 準備中

## 技術棧（規劃）

- Vite + Svelte
- Tailwind CSS
- Chart.js
- WebSocket Client

## 開發指南

詳見 `docs/FRONTEND_IMPLEMENTATION.md`
EOF
  ```

#### 驗證

```bash
# 確認目錄結構
tree -L 2 -d backend frontend tests

# 預期輸出:
# backend
# ├── src
# └── tests
# frontend
# ├── public
# ├── src
# └── tests
# tests
# └── integration
```

#### Checkpoint

```bash
git add backend/ frontend/ tests/integration/
git commit -m "chore(restructure): create monorepo directory structure [Checkpoint 1]"
```

#### 回滾方式

```bash
# 回滾到 Checkpoint 0
git reset --hard pre-monorepo-restructure
```

---

### Checkpoint 2: 移動 Python 源代碼 📦

**目標**: 將 `src/` 移動到 `backend/src/`

#### 任務清單

- [ ] **C2.1**: 複製 src/ 到 backend/src/

  ```bash
  cp -r src/ backend/
  ```

- [ ] **C2.2**: 驗證檔案完整性

  ```bash
  # 檢查檔案數量是否一致
  find src/ -type f | wc -l
  find backend/src/ -type f | wc -l

  # 檢查目錄結構
  diff <(cd src && find . -type d | sort) \
       <(cd backend/src && find . -type d | sort)
  ```

- [ ] **C2.3**: 檢查 **pycache** 和 .pyc 檔案

  ```bash
  # 確認沒有複製 __pycache__
  find backend/src/ -name "__pycache__" -type d

  # 如果有，刪除它們
  find backend/src/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find backend/src/ -name "*.pyc" -delete
  ```

#### 驗證

```bash
# 確認目錄結構正確
ls -la backend/src/
# 預期: agents/ api/ database/ __init__.py

ls -la backend/src/agents/
# 預期: core/ tools/ functions/ integrations/ trading/ utils/

ls -la backend/src/api/
# 預期: routers/ app.py server.py models.py websocket.py ...
```

#### Checkpoint

```bash
git add backend/src/
git commit -m "chore(restructure): copy src/ to backend/src/ [Checkpoint 2]"
```

#### 回滾方式

```bash
# 回滾到 Checkpoint 1
git reset --hard HEAD~1
rm -rf backend/src/
```

---

### Checkpoint 3: 移動測試代碼 🧪

**目標**: 重組測試目錄結構

#### 任務清單

- [ ] **C3.1**: 移動後端單元測試

  ```bash
  # 移動 agents 測試
  cp -r tests/backend/agents/ backend/tests/

  # 移動 api 測試
  cp -r tests/backend/api/ backend/tests/

  # 移動 database 測試
  cp -r tests/database/ backend/tests/
  ```

- [ ] **C3.2**: 移動 **init**.py

  ```bash
  cp tests/__init__.py backend/tests/
  cp tests/backend/__init__.py backend/tests/ 2>/dev/null || true
  ```

- [ ] **C3.3**: 保留整合測試在根目錄

  ```bash
  # 檢查是否有整合測試
  ls tests/integration/ 2>/dev/null || echo "No integration tests yet"

  # 如果存在，確保在根目錄
  # tests/integration/ 保持不變
  ```

- [ ] **C3.4**: 清理 **pycache**

  ```bash
  find backend/tests/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find backend/tests/ -name "*.pyc" -delete
  ```

#### 驗證

```bash
# 確認測試目錄結構
tree -L 2 backend/tests/

# 預期輸出:
# backend/tests/
# ├── __init__.py
# ├── agents/
# │   ├── core/
# │   ├── tools/
# │   ├── functions/
# │   └── integrations/
# ├── api/
# │   └── routers/
# └── database/
```

#### Checkpoint

```bash
git add backend/tests/
git commit -m "chore(restructure): move tests to backend/tests/ [Checkpoint 3]"
```

#### 回滾方式

```bash
# 回滾到 Checkpoint 2
git reset --hard HEAD~1
rm -rf backend/tests/
```

---

### Checkpoint 4: 遷移配置檔案 ⚙️

**目標**: 移動 Python 專案配置到 backend/

#### 任務清單

- [ ] **C4.1**: 複製 pyproject.toml

  ```bash
  cp pyproject.toml backend/
  ```

- [ ] **C4.2**: 更新 backend/pyproject.toml

  ```bash
  cat > backend/pyproject.toml << 'EOF'

[project]
name = "casualtrader-backend"
version = "1.0.0"
description = "CasualTrader AI Trading Simulator - Backend"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy>=2.0.36",
    "aiosqlite>=0.20.0",
    "pydantic>=2.9.0",
    "python-dotenv>=1.0.1",
    "loguru>=0.7.2",
    "httpx>=0.27.0",
    "openai>=1.54.0",
    "yfinance>=0.2.48",
    "pandas>=2.2.3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.3",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.7.0",
    "mypy>=1.11.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
EOF

  ```

- [ ] **C4.3**: 複製 uv.lock
  ```bash
  cp uv.lock backend/ 2>/dev/null || echo "No uv.lock found, will be generated"
  ```

- [ ] **C4.4**: 移動資料庫檔案

  ```bash
  cp casualtrader.db backend/ 2>/dev/null || echo "No database file found"
  ```

- [ ] **C4.5**: 複製環境變數檔案

  ```bash
  # 複製範例檔案
  cp .env.example backend/ 2>/dev/null || echo "No .env.example found"

  # 複製實際環境變數（如果存在）
  cp .env backend/ 2>/dev/null || echo "No .env found (OK for clean setup)"
  ```

- [ ] **C4.6**: 更新 backend/.env.example

  ```bash
  cat > backend/.env.example << 'EOF'

# OpenAI API Configuration

OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Configuration (Optional)

ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google AI Configuration (Optional)

GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration

DATABASE_URL=sqlite+aiosqlite:///./casualtrader.db

# API Configuration

API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Logging

LOG_LEVEL=INFO
EOF

  ```

#### 驗證

```bash
# 確認配置檔案存在
ls -la backend/ | grep -E "(pyproject.toml|uv.lock|.env)"

# 驗證 pyproject.toml 語法
cd backend
uv sync --dry-run
```

#### Checkpoint

```bash
git add backend/pyproject.toml backend/uv.lock backend/.env.example
git add backend/casualtrader.db 2>/dev/null || true
git commit -m "chore(restructure): migrate config files to backend/ [Checkpoint 4]"
```

#### 回滾方式

```bash
# 回滾到 Checkpoint 3
git reset --hard HEAD~1
rm -f backend/pyproject.toml backend/uv.lock backend/.env.example backend/casualtrader.db
```

---

### Checkpoint 5: 更新腳本 🔧

**目標**: 更新啟動和測試腳本以適應新結構

#### 任務清單

- [ ] **C5.1**: 更新 scripts/start_api.sh

  ```bash
  cat > scripts/start_api.sh << 'EOF'

# !/bin/zsh

# CasualTrader Backend API Starter

# 切換到 backend 目錄並啟動 API 服務

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🚀 Starting CasualTrader Backend API..."
echo "📁 Backend directory: $BACKEND_DIR"

cd "$BACKEND_DIR"

# 檢查 pyproject.toml 是否存在

if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found in backend/"
    exit 1
fi

# 同步依賴

echo "📦 Syncing dependencies..."
uv sync

# 啟動 API

echo "✅ Starting API server at <http://0.0.0.0:8000>"
uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
EOF
  chmod +x scripts/start_api.sh

  ```

- [ ] **C5.2**: 創建 scripts/start_dev.sh
  ```bash
  cat > scripts/start_dev.sh << 'EOF'
#!/bin/zsh

# CasualTrader Development Environment Starter
# 同時啟動前後端服務

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting CasualTrader Development Environment..."

# 啟動後端
echo "🐍 Starting Backend API..."
cd "$PROJECT_ROOT/backend"
uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 未來啟動前端 (Phase 4)
# echo "🎨 Starting Frontend..."
# cd "$PROJECT_ROOT/frontend"
# npm run dev &
# FRONTEND_PID=$!

echo ""
echo "✅ Backend running at http://localhost:8000"
echo "✅ API Docs at http://localhost:8000/docs"
# echo "✅ Frontend running at http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

# 捕獲中斷信號
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID 2>/dev/null; exit 0" INT TERM

# 等待後端進程
wait $BACKEND_PID
EOF
  chmod +x scripts/start_dev.sh
  ```

- [ ] **C5.3**: 創建 scripts/run_tests.sh

  ```bash
  cat > scripts/run_tests.sh << 'EOF'

# !/bin/zsh

# CasualTrader Test Runner

# 執行所有測試（後端 + 整合）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running CasualTrader Tests..."

# 後端測試

echo ""
echo "📦 Backend Tests"
echo "=================="
cd "$PROJECT_ROOT/backend"
uv run pytest tests/ -v --cov=src --cov-report=term-missing
BACKEND_EXIT=$?

# 整合測試

echo ""
echo "🔗 Integration Tests"
echo "=================="
if [ -d "$PROJECT_ROOT/tests/integration" ] && [ "$(ls -A "$PROJECT_ROOT/tests/integration")" ]; then
    cd "$PROJECT_ROOT"
    uv run pytest tests/integration/ -v
    INTEGRATION_EXIT=$?
else
    echo "⏭️  No integration tests found (OK for Phase 1-3)"
    INTEGRATION_EXIT=0
fi

# 前端測試 (Phase 4)

# echo ""

# echo "🎨 Frontend Tests"

# echo "=================="

# cd "$PROJECT_ROOT/frontend"

# npm test

# FRONTEND_EXIT=$?

# 總結

echo ""
echo "📊 Test Summary"
echo "=================="
if [ $BACKEND_EXIT -eq 0 ] && [ $INTEGRATION_EXIT -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
EOF
  chmod +x scripts/run_tests.sh

  ```

- [ ] **C5.4**: 創建 scripts/setup_backend.sh
  ```bash
  cat > scripts/setup_backend.sh << 'EOF'
#!/bin/zsh

# CasualTrader Backend Setup Script
# 配置後端開發環境

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔧 Setting up CasualTrader Backend..."

cd "$BACKEND_DIR"

# 檢查 UV 是否安裝
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 同步依賴
echo "📦 Installing dependencies..."
uv sync

# 創建環境變數檔案
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys"
fi

# 初始化資料庫（如果不存在）
if [ ! -f "casualtrader.db" ]; then
    echo "🗄️  Initializing database..."
    uv run python -c "
from src.database.migrations import init_database
import asyncio
asyncio.run(init_database())
print('✅ Database initialized')
"
else
    echo "✅ Database already exists"
fi

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your API keys"
echo "2. Run: ./scripts/start_api.sh"
echo "3. Visit: http://localhost:8000/docs"
EOF
  chmod +x scripts/setup_backend.sh
  ```

#### 驗證

```bash
# 確認腳本可執行
ls -l scripts/*.sh | grep "rwx"

# 測試 start_api.sh 語法
zsh -n scripts/start_api.sh

# 測試 run_tests.sh 語法
zsh -n scripts/run_tests.sh
```

#### Checkpoint

```bash
git add scripts/
git commit -m "chore(restructure): update scripts for monorepo structure [Checkpoint 5]"
```

#### 回滾方式

```bash
# 回滾到 Checkpoint 4
git reset --hard HEAD~1
git checkout scripts/  # 恢復原始腳本
```

---

### Checkpoint 6: 更新 VS Code 配置 💻

**目標**: 更新 VS Code 設定以適應新結構

#### 任務清單

- [ ] **C6.1**: 更新 .vscode/settings.json

  ```bash
  mkdir -p .vscode
  cat > .vscode/settings.json << 'EOF'

{
  // Python 配置
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.analysis.extraPaths": [
    "${workspaceFolder}/backend"
  ],

  // 測試配置
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests",
    "-v"
  ],
  "python.testing.cwd": "${workspaceFolder}/backend",
  "python.testing.unittestEnabled": false,

  // 格式化配置
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  },

  // 檔案排除
  "files.exclude": {
    "**/**pycache**": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true
  },

  // 搜尋排除
  "search.exclude": {
    "**/node_modules": true,
    "**/.venv": true,
    "**/backend/.venv": true,
    "**/frontend/node_modules": true
  }
}
EOF

  ```

- [ ] **C6.2**: 更新 .vscode/launch.json
  ```bash
  cat > .vscode/launch.json << 'EOF'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.api.app:create_app",
        "--factory",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Backend: pytest (current file)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "${file}",
        "-v",
        "-s"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Backend: All Tests",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/",
        "-v"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
EOF
  ```

- [ ] **C6.3**: 更新 .vscode/extensions.json（推薦擴展）

  ```bash
  cat > .vscode/extensions.json << 'EOF'

{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.debugpy",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "svelte.svelte-vscode",
    "bradlc.vscode-tailwindcss",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode"
  ]
}
EOF

  ```

#### 驗證

```bash
# 確認配置檔案存在
ls -la .vscode/

# 驗證 JSON 語法
python3 -m json.tool .vscode/settings.json > /dev/null
python3 -m json.tool .vscode/launch.json > /dev/null
python3 -m json.tool .vscode/extensions.json > /dev/null
```

#### Checkpoint

```bash
git add .vscode/
git commit -m "chore(restructure): update VS Code configuration [Checkpoint 6]"
```

#### 回滾方式

```bash
# 回滾到 Checkpoint 5
git reset --hard HEAD~1
```

---

### Checkpoint 7: 測試新結構 ✅

**目標**: 驗證重構後的結構完全正常

#### 任務清單

- [ ] **C7.1**: 同步 backend 依賴

  ```bash
  cd backend
  uv sync
  ```

- [ ] **C7.2**: 測試 Python import

  ```bash
  cd backend
  uv run python -c "

from src.agents.core.base_agent import CasualTradingAgent
from src.agents.core.agent_manager import AgentManager
from src.api.app import create_app
from src.database.models import Base
print('✅ All imports successful')
"

  ```

- [ ] **C7.3**: 運行單元測試
  ```bash
  cd backend
  uv run pytest tests/ -v --tb=short
  ```

- [ ] **C7.4**: 測試 API 啟動

  ```bash
  cd backend
  timeout 10 uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &
  sleep 5

  # 測試健康檢查端點
  curl -s http://localhost:8000/api/health | grep -q "ok"

  # 停止測試服務器
  pkill -f "uvicorn src.api.app"
  ```

- [ ] **C7.5**: 測試腳本

  ```bash
  # 測試 setup_backend.sh
  ./scripts/setup_backend.sh

  # 測試 run_tests.sh
  ./scripts/run_tests.sh
  ```

- [ ] **C7.6**: 驗證資料庫

  ```bash
  cd backend

  # 檢查資料庫檔案
  ls -lh casualtrader.db

  # 驗證資料庫結構
  uv run python -c "

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.database.models import Base

async def check_db():
    engine = create_async_engine('sqlite+aiosqlite:///./casualtrader.db')
    async with engine.begin() as conn:
        # 檢查表是否存在
        result = await conn.run_sync(
            lambda sync_conn: sync_conn.execute(
                'SELECT name FROM sqlite_master WHERE type=\"table\"'
            ).fetchall()
        )
        tables = [row[0] for row in result]
        print(f'✅ Found {len(tables)} tables: {tables}')

        required = ['agent_states', 'agent_sessions', 'trades', 'holdings']
        missing = [t for t in required if t not in tables]
        if missing:
            print(f'❌ Missing tables: {missing}')
            return False
        print('✅ All required tables exist')
        return True

if not asyncio.run(check_db()):
    exit(1)
"

  ```

#### 驗證檢查表

- [ ] ✅ backend 依賴安裝成功
- [ ] ✅ Python import 正常
- [ ] ✅ 單元測試全部通過
- [ ] ✅ API 服務可以啟動
- [ ] ✅ 健康檢查端點回應正常
- [ ] ✅ 腳本執行成功
- [ ] ✅ 資料庫結構完整

#### Checkpoint

```bash
git add -A
git commit -m "chore(restructure): verify new structure - all tests passing [Checkpoint 7]"
```

#### 回滾方式

```bash
# 如果測試失敗，回滾到 Checkpoint 6
git reset --hard HEAD~1
```

---

### Checkpoint 8: 清理舊檔案 🧹

**目標**: 移除根目錄的舊檔案和目錄

**⚠️ 警告**: 這是不可逆操作，確保 Checkpoint 7 所有測試通過！

#### 任務清單

- [ ] **C8.1**: 最後確認備份

  ```bash
  # 確認備份分支存在
  git branch | grep backup-pre-monorepo

  # 確認標籤存在
  git tag | grep pre-monorepo-restructure

  # 創建額外的備份
  git branch backup-before-cleanup-$(date +%Y%m%d-%H%M%S)
  ```

- [ ] **C8.2**: 移除根目錄的 src/

  ```bash
  # 再次確認 backend/src/ 存在且完整
  [ -d "backend/src/agents" ] || { echo "❌ backend/src/agents not found!"; exit 1; }
  [ -d "backend/src/api" ] || { echo "❌ backend/src/api not found!"; exit 1; }
  [ -d "backend/src/database" ] || { echo "❌ backend/src/database not found!"; exit 1; }

  # 刪除根目錄的 src/
  rm -rf src/
  ```

- [ ] **C8.3**: 移除根目錄的測試

  ```bash
  # 確認 backend/tests/ 存在
  [ -d "backend/tests" ] || { echo "❌ backend/tests not found!"; exit 1; }

  # 刪除已遷移的測試
  rm -rf tests/backend/
  rm -rf tests/database/

  # 保留 tests/integration/ 和 tests/__init__.py
  ```

- [ ] **C8.4**: 移除根目錄的配置檔案

  ```bash
  # 確認 backend/ 配置存在
  [ -f "backend/pyproject.toml" ] || { echo "❌ backend/pyproject.toml not found!"; exit 1; }

  # 刪除根目錄配置（保留特定檔案）
  rm -f pyproject.toml
  rm -f uv.lock
  rm -f casualtrader.db

  # 保留的檔案:
  # - .gitignore
  # - README.md
  # - docker-compose.yml
  ```

- [ ] **C8.5**: 清理快取和臨時檔案

  ```bash
  # 清理根目錄的 Python 快取
  find . -maxdepth 1 -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find . -maxdepth 1 -name "*.pyc" -delete 2>/dev/null || true
  find . -maxdepth 1 -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
  find . -maxdepth 1 -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
  find . -maxdepth 1 -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
  find . -maxdepth 1 -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true
  find . -maxdepth 1 -name ".coverage" -delete 2>/dev/null || true
  find . -maxdepth 1 -name "coverage.xml" -delete 2>/dev/null || true

  # 清理日誌檔案（如果不需要）
  # rm -rf logs/ 2>/dev/null || true
  ```

- [ ] **C8.6**: 更新 .gitignore

  ```bash
  cat > .gitignore << 'EOF'

# Python

**pycache**/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual Environment

.venv/
venv/
ENV/
backend/.venv/
frontend/node_modules/

# IDEs

.vscode/
.idea/
*.swp
*.swo
*~

# Testing

.pytest_cache/
.coverage
htmlcov/
coverage.xml
.mypy_cache/
.ruff_cache/

# Environment

.env
.env.local
backend/.env
frontend/.env

# Database

*.db
*.db-journal
backend/casualtrader.db

# Logs

logs/
*.log

# OS

.DS_Store
Thumbs.db

# Build outputs

dist/
*.egg-info/
frontend/dist/
frontend/build/

# Temporary

*.tmp
*.bak
.temp/
EOF

  ```

#### 驗證

```bash
# 確認根目錄結構
ls -la

# 應該看到:
# - backend/
# - frontend/
# - tests/ (只有 integration/)
# - docs/
# - scripts/
# - .vscode/
# - .github/
# - .gitignore
# - README.md
# - docker-compose.yml (如果有)

# 不應該看到:
# - src/
# - pyproject.toml (根目錄)
# - uv.lock (根目錄)
# - casualtrader.db (根目錄)
```

#### 最終測試

```bash
# 運行完整測試套件
./scripts/run_tests.sh

# 啟動 API 服務
./scripts/start_api.sh
# (在另一個終端測試後停止)
```

#### Checkpoint

```bash
git add -A
git commit -m "chore(restructure): cleanup old files - monorepo complete [Checkpoint 8]"
git tag monorepo-restructure-complete
```

#### 回滾方式

```bash
# 如果需要完全回滾整個重構
git reset --hard pre-monorepo-restructure
git clean -fd

# 或回滾到清理前
git reset --hard HEAD~1
```

---

## 🎯 驗證測試

### 完整驗證清單

#### 1. 目錄結構驗證

```bash
#!/bin/zsh
# verify_structure.sh

echo "🔍 Verifying Monorepo Structure..."

# 檢查必要目錄
directories=(
    "backend/src"
    "backend/tests"
    "frontend/src"
    "tests/integration"
    "docs"
    "scripts"
)

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir"
    else
        echo "❌ $dir (missing)"
    fi
done

# 檢查不應存在的目錄
old_dirs=(
    "src"
    "tests/backend"
    "tests/database"
)

for dir in "${old_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "✅ $dir (removed)"
    else
        echo "❌ $dir (should be removed)"
    fi
done
```

#### 2. Python Import 測試

```bash
cd backend
uv run python << 'EOF'
import sys
print("🐍 Testing Python Imports...")

try:
    # Core agents
    from src.agents.core.base_agent import CasualTradingAgent
    from src.agents.core.agent_manager import AgentManager
    from src.agents.core.agent_session import AgentSession
    from src.agents.core.models import AgentConfig, AgentState
    print("✅ Core agents imports")

    # Tools
    from src.agents.tools.fundamental_agent import FundamentalAgent
    from src.agents.tools.technical_agent import TechnicalAgent
    from src.agents.tools.risk_agent import RiskAgent
    from src.agents.tools.sentiment_agent import SentimentAgent
    print("✅ Analysis tools imports")

    # API
    from src.api.app import create_app
    from src.api.models import AgentResponse
    from src.api.websocket import WebSocketManager
    print("✅ API imports")

    # Database
    from src.database.models import Base, AgentState as DBAgentState
    print("✅ Database imports")

    print("\n✅ All imports successful!")
    sys.exit(0)

except ImportError as e:
    print(f"\n❌ Import failed: {e}")
    sys.exit(1)
EOF
```

#### 3. 單元測試驗證

```bash
cd backend
echo "🧪 Running Unit Tests..."
uv run pytest tests/ -v --tb=short --maxfail=1
```

#### 4. API 服務驗證

```bash
cd backend
echo "🚀 Testing API Service..."

# 啟動服務
uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &
API_PID=$!

# 等待啟動
sleep 5

# 測試端點
curl -s http://localhost:8000/api/health | grep -q '"status":"ok"' && echo "✅ Health endpoint" || echo "❌ Health endpoint"
curl -s http://localhost:8000/api/agents | grep -q "agents" && echo "✅ Agents endpoint" || echo "❌ Agents endpoint"
curl -s http://localhost:8000/docs | grep -q "FastAPI" && echo "✅ API docs" || echo "❌ API docs"

# 停止服務
kill $API_PID
```

#### 5. 腳本測試

```bash
echo "🔧 Testing Scripts..."

# 測試腳本語法
for script in scripts/*.sh; do
    zsh -n "$script" && echo "✅ $(basename $script)" || echo "❌ $(basename $script)"
done

# 測試 setup
./scripts/setup_backend.sh
```

---

## 🔄 Checkpoint 與回滾

### Checkpoint 總覽

| Checkpoint | 描述 | 可回滾 | Git 標籤 |
|-----------|------|--------|---------|
| C0 | 準備工作 | ✅ | `pre-monorepo-restructure` |
| C1 | 創建目錄結構 | ✅ | - |
| C2 | 移動源代碼 | ✅ | - |
| C3 | 移動測試代碼 | ✅ | - |
| C4 | 遷移配置檔案 | ✅ | - |
| C5 | 更新腳本 | ✅ | - |
| C6 | 更新 VS Code | ✅ | - |
| C7 | 測試新結構 | ✅ | - |
| C8 | 清理舊檔案 | ⚠️ | `monorepo-restructure-complete` |

### 快速回滾命令

```bash
# 完全回滾到重構前
git reset --hard pre-monorepo-restructure
git clean -fd

# 查看可用的備份分支
git branch | grep backup

# 切換到備份分支
git checkout backup-pre-monorepo-YYYYMMDD-HHMMSS
```

### 部分回滾

```bash
# 回滾到特定 Checkpoint（例如 C7）
git log --oneline | grep "Checkpoint"
git reset --hard <commit-hash>

# 恢復特定檔案
git checkout pre-monorepo-restructure -- src/
```

---

## 🔧 故障排除

### 問題 1: Import 錯誤

**症狀**:

```
ModuleNotFoundError: No module named 'src'
```

**解決方案**:

```bash
cd backend

# 檢查 PYTHONPATH
echo $PYTHONPATH

# 設定 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 或使用 uv run
uv run python -c "from src.agents.core.base_agent import CasualTradingAgent"
```

---

### 問題 2: 測試無法執行

**症狀**:

```
pytest: error: no tests found
```

**解決方案**:

```bash
cd backend

# 檢查 pytest 配置
cat pyproject.toml | grep pytest -A 5

# 確認測試目錄
ls -la tests/

# 明確指定測試路徑
uv run pytest tests/ -v
```

---

### 問題 3: 資料庫路徑錯誤

**症狀**:

```
sqlite3.OperationalError: unable to open database file
```

**解決方案**:

```bash
cd backend

# 檢查資料庫檔案
ls -lh casualtrader.db

# 如果不存在，初始化
uv run python -c "
from src.database.migrations import init_database
import asyncio
asyncio.run(init_database())
"

# 檢查連接字串
grep DATABASE_URL .env
```

---

### 問題 4: API 無法啟動

**症狀**:

```
Error loading ASGI app. Could not import module "src.api.app"
```

**解決方案**:

```bash
cd backend

# 檢查檔案是否存在
ls -la src/api/app.py

# 測試 import
uv run python -c "from src.api.app import create_app; print('OK')"

# 檢查 uvicorn 命令
uv run uvicorn --help

# 確保在 backend/ 目錄執行
pwd  # 應該顯示 .../CasualTrader/backend
```

---

### 問題 5: 腳本權限錯誤

**症狀**:

```
permission denied: ./scripts/start_api.sh
```

**解決方案**:

```bash
# 添加執行權限
chmod +x scripts/*.sh

# 驗證
ls -l scripts/*.sh
```

---

## 📊 重構進度追蹤

### 進度檢查表

```bash
#!/bin/zsh
# check_progress.sh

echo "📊 Monorepo Restructure Progress"
echo "=================================="

checkpoints=(
    "C0:準備工作"
    "C1:創建目錄結構"
    "C2:移動源代碼"
    "C3:移動測試代碼"
    "C4:遷移配置檔案"
    "C5:更新腳本"
    "C6:更新 VS Code"
    "C7:測試新結構"
    "C8:清理舊檔案"
)

for checkpoint in "${checkpoints[@]}"; do
    code="${checkpoint%%:*}"
    desc="${checkpoint##*:}"

    if git log --oneline | grep -q "\[$code\]"; then
        echo "✅ $code: $desc"
    else
        echo "⏳ $code: $desc"
    fi
done

echo ""
echo "Current Status:"
git log --oneline -1
```

---

## 🎉 完成檢查

### 最終驗證清單

執行以下命令確認重構完成：

```bash
#!/bin/zsh
# final_verification.sh

echo "🎉 Final Monorepo Verification"
echo "=============================="

# 1. 目錄結構
echo "\n📁 Directory Structure:"
[ -d "backend/src" ] && echo "✅ backend/src/" || echo "❌ backend/src/"
[ -d "backend/tests" ] && echo "✅ backend/tests/" || echo "❌ backend/tests/"
[ -d "frontend/src" ] && echo "✅ frontend/src/" || echo "❌ frontend/src/"
[ ! -d "src" ] && echo "✅ src/ removed" || echo "❌ src/ still exists"

# 2. 配置檔案
echo "\n⚙️ Configuration Files:"
[ -f "backend/pyproject.toml" ] && echo "✅ backend/pyproject.toml" || echo "❌ backend/pyproject.toml"
[ ! -f "pyproject.toml" ] && echo "✅ Root pyproject.toml removed" || echo "❌ Root pyproject.toml exists"

# 3. Python Import
echo "\n🐍 Python Imports:"
cd backend
if uv run python -c "from src.agents.core.base_agent import CasualTradingAgent" 2>/dev/null; then
    echo "✅ Python imports working"
else
    echo "❌ Python imports failing"
fi
cd ..

# 4. 測試
echo "\n🧪 Tests:"
cd backend
if uv run pytest tests/ -q 2>/dev/null; then
    echo "✅ Tests passing"
else
    echo "❌ Tests failing"
fi
cd ..

# 5. API
echo "\n🚀 API Service:"
cd backend
timeout 10 uv run uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &>/dev/null &
API_PID=$!
sleep 5
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    echo "✅ API service working"
else
    echo "❌ API service not responding"
fi
kill $API_PID 2>/dev/null
cd ..

# 6. 腳本
echo "\n🔧 Scripts:"
[ -x "scripts/start_api.sh" ] && echo "✅ start_api.sh executable" || echo "❌ start_api.sh not executable"
[ -x "scripts/run_tests.sh" ] && echo "✅ run_tests.sh executable" || echo "❌ run_tests.sh not executable"

# 7. Git
echo "\n📦 Git Status:"
git tag | grep -q "monorepo-restructure-complete" && echo "✅ Completion tag exists" || echo "⏳ Not yet tagged as complete"

echo "\n=============================="
echo "Restructure Status: Check results above"
```

---

## 📚 參考文檔

重構完成後，請參考以下更新的文檔：

- **PROJECT_STRUCTURE.md** - 已更新的專案結構規範
- **SYSTEM_DESIGN.md** - 已更新的系統架構說明
- **AGENTS_ARCHITECTURE.md** - Agent 模組架構（路徑已更新）
- **API_ARCHITECTURE.md** - API 模組架構（路徑已更新）
- **DEPLOYMENT_GUIDE.md** - 部署指南（待更新）

---

## 🆘 需要幫助？

如果遇到問題：

1. **檢查 Checkpoint**: 確認當前進度
2. **查看日誌**: `git log --oneline`
3. **運行驗證腳本**: 確認哪個步驟失敗
4. **回滾**: 如果需要，回滾到上一個 Checkpoint
5. **參考故障排除**: 查看本文檔的故障排除章節

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-09
**版本**: 1.0
