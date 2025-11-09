# GitHub Copilot + LiteLLM 集成指南（簡化版）

**日期**: 2025-10-25
**狀態**: ✅ POC 驗證完成
**設計**: 簡化 - 無複雜封裝層

---

## 概述

GitHub Copilot 通過 LiteLLM 支持直接集成到 OpenAI Agent SDK。使用 `LitellmModel` + `ModelSettings` 處理特殊的 Headers。

### 關鍵成果

✅ LiteLLM GitHub Copilot 認證成功
✅ OpenAI Agent SDK 完全兼容
✅ OAuth device flow 自動快取
✅ 模型選項: gpt-5, gpt-5-mini

---

## 快速集成

### 基本用法

```python
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

# 創建模型
model = LitellmModel(
    model="github_copilot/gpt-5",
    api_key="ghp_xxxxx"  # 或使用 os.getenv("GITHUB_COPILOT_TOKEN")
)

# 創建 Agent
agent = Agent(
    name="My Agent",
    instructions="Be helpful",
    model=model,
)

# 執行
result = await Runner.run(agent, "Hello")
```

### GitHub Copilot 特殊配置

GitHub Copilot 需要額外的 HTTP Headers：

```python
from agents import Agent, Runner, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel

model = LitellmModel(
    model="github_copilot/gpt-5",
    api_key=os.getenv("GITHUB_COPILOT_TOKEN")
)

# 必需的 ModelSettings
model_settings = ModelSettings(
    extra_headers={
        "editor-version": "vscode/1.85.1",
        "Copilot-Integration-Id": "vscode-chat",
    }
)

agent = Agent(
    name="My Agent",
    instructions="Be helpful",
    model=model,
    model_settings=model_settings,  # 傳遞 ModelSettings
)

result = await Runner.run(agent, "Your prompt")
```

---

## 認證方式

### 方式 1: OAuth Device Flow（推薦）

```python
# 首次使用會提示設備代碼
model = LitellmModel(model="github_copilot/gpt-5")

# 按提示訪問 GitHub 授權，tokens 會自動快取
```

**優勢**: 無需手動配置 token
**劣勢**: 首次需要手動交互

### 方式 2: GitHub Personal Access Token

```python
model = LitellmModel(
    model="github_copilot/gpt-5",
    api_key="ghp_xxxxxxxxxxxxxx"
)
```

**優勢**: 非互動式，可用於 CI/CD
**劣勢**: 需要手動管理 token

### 方式 3: 環境變數

```bash
# .env
GITHUB_COPILOT_TOKEN=ghp_xxxxxxxxxxxxxx
```

```python
import os
model = LitellmModel(
    model="github_copilot/gpt-5",
    api_key=os.getenv("GITHUB_COPILOT_TOKEN")
)
```

---

## 模型選項

### gpt-5

- 高能力通用模型
- 推薦用於複雜任務
- 響應時間較長

### gpt-5-mini

- 快速輕量級模型
- 推薦用於簡單任務
- 響應快速

```python
# 使用 gpt-5-mini 獲得更快響應
model = LitellmModel(
    model="github_copilot/gpt-5-mini",
    api_key=os.getenv("GITHUB_COPILOT_TOKEN")
)
```

---

## TradingAgent 集成示例

```python
# src/trading/trading_agent.py

from agents import Agent, Runner, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel
import os

class TradingAgent:
    def __init__(self, agent_id: str, agent_config, agent_service):
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.agent_service = agent_service

    def _create_llm_model(self) -> LitellmModel:
        """創建 LiteLLM 模型"""
        provider = self.agent_config.llm_provider  # 'github_copilot'
        model = self.agent_config.ai_model        # 'gpt-5'
        api_key = os.getenv(f"{provider.upper()}_API_KEY")

        return LitellmModel(
            model=f"{provider}/{model}",
            api_key=api_key
        )

    async def run(self, mode: str, **kwargs):
        """執行 Agent"""
        llm_model = self._create_llm_model()

        # GitHub Copilot 特殊配置
        model_settings = None
        if self.agent_config.llm_provider.lower() == 'github_copilot':
            model_settings = ModelSettings(
                extra_headers={
                    "editor-version": "vscode/1.85.1",
                    "Copilot-Integration-Id": "vscode-chat",
                }
            )

        agent = Agent(
            name=f"Agent-{self.agent_id}",
            instructions=self._build_instructions(),
            model=llm_model,
            tools=self._get_tools(),
            model_settings=model_settings,
        )

        result = await Runner.run(agent, self._build_prompt(**kwargs))

        return {
            "success": True,
            "output": result.final_output
        }
```

---

## 環境設置

### 安裝

```bash
pip install litellm>=1.0.0
```

### 環境變數

```bash
# .env
GITHUB_COPILOT_TOKEN=ghp_xxxxxxxxxxxxxx
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

### 驗證

```python
import asyncio
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

async def test():
    model = LitellmModel(
        model="github_copilot/gpt-5-mini",
        api_key=os.getenv("GITHUB_COPILOT_TOKEN")
    )

    agent = Agent(
        name="Test",
        instructions="Say hello",
        model=model,
    )

    result = await Runner.run(agent, "Say OK")
    print(f"✅ {result.final_output}")

asyncio.run(test())
```

---

## 常見問題

**Q: 首次使用為什麼需要 OAuth？**
A: GitHub Copilot 使用 OAuth 認證。LiteLLM 自動處理設備流程，tokens 自動快取。

**Q: 為什麼需要 ModelSettings？**
A: GitHub Copilot API 需要特殊的 HTTP headers。ModelSettings 用於傳遞這些。

**Q: 可以混用多個模型嗎？**
A: 可以。創建多個 LitellmModel，在不同 Agent 中使用。

**Q: 為什麼不需要複雜的配置層？**
A: 簡化設計。LitellmModel 已提供統一接口，直接使用即可。

---

## POC 測試

完整的 POC 測試位置:

```
backend/tests/labs/GithubCopilot_LiteLLM_POC.ipynb
```

### 驗證的功能

- ✅ 基本認證和調用
- ✅ 流式調用
- ✅ OpenAI Agents 集成
- ✅ 工具調用

---

## 相關文檔

- [LiteLLM 重構計畫](./LITELLM_REFACTOR_PLAN.md)
- [LiteLLM 快速開始](./LITELLM_QUICK_START.md)
- [LiteLLM 遷移索引](./LITELLM_MIGRATION_INDEX.md)

---

**版本**: 2.0 - 簡化版
**狀態**: ✅ POC 驗證完成，準備集成
**最後更新**: 2025-10-25
