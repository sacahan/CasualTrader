"""Sentiment Agent - 市場情緒分析自主型 Agent

這個模組實作具有自主分析能力的市場情緒分析 Agent。
"""

from __future__ import annotations

from datetime import datetime

from dotenv import load_dotenv

from agents import Agent, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel

from common.logger import logger

load_dotenv()


def sentiment_agent_instructions() -> str:
    """情緒分析 Agent 的指令定義，聚焦 perplexity_mcp 精準檢索。"""
    return f"""你是市場情緒偵測專家，負責提出可操作的情緒洞察與風險提示。

## 核心原則

1. **資料可信度 > 自行推導**：情緒判讀必須建立在可靠來源，優先引用 perplexity_mcp 搜尋結果。
2. **每次只做一次昂貴搜尋**：整份報告限用 1 次 perplexity_mcp，除非使用者補充更多範圍再重新分析。
3. **查核記憶**：先透過 memory_mcp 查詢同題歷史情緒，辨識趨勢或反轉，再決定是否重新搜尋。
4. **明確查詢**：向 perplexity_mcp 下達具體指令，包含時間、區域、標的與你想知道的角度（如「機構買賣」「社群熱度」）。
5. **輸出可執行摘要**：回報市場情緒階段、關鍵驅動因子、潛在風險與建議行動，並註記資訊來源與新鮮度。

## Perplexity 查詢策略

- 範例查詢 1："台股 市場情緒 重大新聞 今天 after-hours 資金流向"。
- 範例查詢 2："2330 TSMC investor sentiment latest news institutional flows"。
- 範例查詢 3："台股 社群輿情 PTT Dcard today market fear greed"。
- 每次查詢包含：時間限制（today / past 24h）、情緒角度（fear, greed, flows, volatility）、需要的輸出格式（列出主題+來源+情緒）。
- 若需要多面向，先在一條 prompt 中要求 perplexity_mcp 回傳「市場面」「資金面」「社群面」分段摘要，避免多次查詢。

## 執行流程

1. **記憶檢查**：memory_mcp → 有過去 24h 訊號則比較差異；資料過舊才重新搜尋。
2. **定義焦點**：確認使用者提供的 ticker、市場或題材，寫下欲驗證的假設與三個關鍵問題。
3. **設計單次搜尋 Prompt**：指名需要的輸出，例如「列出 3 則市場情緒新聞、指出情緒方向、每則提供來源、標籤成多/空/中立」。
4. **解析結果**：對照先前記憶，標記變化（升溫、轉冷、分歧)。無可靠資料時要直接說明資料缺口。
5. **提出建議**：包含市場情緒分數（-100~+100）、情緒階段（恐慌/悲觀/中立/樂觀/狂熱）、主因與對應策略建議。

## 輸出格式

- **市場情緒分數**：-100~+100，並解釋主要依據。
- **情緒階段與趨勢**：目前所處階段 + 與上一筆記憶相比的變化。
- **驅動因子**：列出 3 個最重要的新聞或社群論點，附來源與時間。
- **資金與風險訊號**：以文字描述買賣力道、波動、政策/地緣風險。
- **建議行動**：買進 / 逢高減碼 / 觀望 + 風險控管要點。
- **資料新鮮度**：標註每條資訊的時間，若缺資料需明確寫「資料不足」。

## 使用限制

- 單次分析最多觸發 1 次 perplexity_mcp 搜尋；若結果不足，需向使用者說明缺口再請求授權。
- 先利用記憶庫或使用者提供資料，只有無法回答時才真的搜尋。
- 精準提示 perplexity_mcp：說明你在找什麼、需要的欄位、情緒分類方式，並要求按照 JSON 或 bullet 回傳方便解析。

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


async def get_sentiment_agent(
    llm_model: LitellmModel = None,
    extra_headers: dict[str, str] = None,
    mcp_servers: list | None = None,
) -> Agent:
    """創建市場情緒分析 Agent

    Args:
        llm_model: 使用的語言模型實例 (LitellmModel)，如果為 None，則使用預設模型
        extra_headers: 額外的 HTTP 標頭，用於模型 API 請求
        mcp_servers: MCP servers 實例列表（MCPServerStdio 或 MCPServerSse 對象），從 TradingAgent 傳入

    Returns:
        Agent: 配置好的市場情緒分析 Agent

    Note:
        - 不依賴本地統計工具，直接透過 mcp_servers（尤其是 perplexity_mcp）查詢資料
        - Timeout 由主 TradingAgent 的 execution_timeout 統一控制
        - Sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制
    """
    logger.info(f"get_sentiment_agent() called with model={llm_model}")

    if mcp_servers is None:
        mcp_servers = []

    perplexity_available = any(
        getattr(server, "name", "") == "perplexity_mcp" for server in mcp_servers
    )
    logger.info(
        "Creating Sentiment Agent | mcp_servers=%s | perplexity=%s",
        len(mcp_servers),
        "available" if perplexity_available else "missing",
    )

    model_settings_dict = {
        "max_completion_tokens": 500,
    }

    model_name = llm_model.model if llm_model else ""
    if model_name and "github_copilot" not in model_name.lower():
        model_settings_dict["tool_choice"] = "auto"

    if extra_headers:
        model_settings_dict["extra_headers"] = extra_headers

    analyst = Agent(
        name="sentiment_analyst",
        instructions=sentiment_agent_instructions(),
        model=llm_model,
        mcp_servers=mcp_servers,
        tools=[],
        model_settings=ModelSettings(**model_settings_dict),
    )
    logger.info("Sentiment Analyst Agent created successfully")

    return analyst
