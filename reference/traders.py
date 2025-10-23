# 匯入異步上下文管理器，用於管理多個 MCP server 的生命週期
import json
import os
from contextlib import AsyncExitStack

# 匯入帳戶資源與策略讀取函式
from accounts_client import read_accounts_resource, read_strategy_resource

# 匯入 Agents SDK 相關類別與函式
from agents import Agent, OpenAIChatCompletionsModel, Runner, Tool, trace

# 匯入 MCP server 標準輸入/輸出介面
from agents.mcp import MCPServerStdio

# 匯入 dotenv 用於載入環境變數
from dotenv import load_dotenv

# 匯入 MCP server 參數
from mcp_params import researcher_mcp_server_params, trader_mcp_server_params

# 匯入 OpenAI 非同步 API 客戶端
from openai import AsyncOpenAI

# 匯入指令與訊息模板
from templates import (
    rebalance_message,
    research_tool,
    researcher_instructions,
    trade_message,
    trader_instructions,
)

# 匯入追蹤 ID 產生器
from tracers import make_trace_id

# 載入 .env 檔案中的環境變數
load_dotenv(override=True)

# 取得各種 API 金鑰
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

# 設定各大模型 API 的 base url
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# 設定最大回合數
MAX_TURNS = 30

# 初始化各模型的非同步 API 客戶端
openrouter_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key
)
deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
grok_client = AsyncOpenAI(base_url=GROK_BASE_URL, api_key=grok_api_key)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)


# 根據模型名稱取得對應的模型物件
def get_model(model_name: str):
    # 若模型名稱包含 '/'，則使用 openrouter_client
    if "/" in model_name:
        return OpenAIChatCompletionsModel(
            model=model_name, openai_client=openrouter_client
        )
    # 若模型名稱包含 'deepseek'，則使用 deepseek_client
    elif "deepseek" in model_name:
        return OpenAIChatCompletionsModel(
            model=model_name, openai_client=deepseek_client
        )
    # 若模型名稱包含 'grok'，則使用 grok_client
    elif "grok" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=grok_client)
    # 若模型名稱包含 'gemini'，則使用 gemini_client
    elif "gemini" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)
    # 否則直接回傳模型名稱字串
    else:
        return model_name


# 建立金融研究員 Agent
async def get_researcher(mcp_servers, model_name) -> Agent:
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),  # 研究員指令
        model=get_model(model_name),
        mcp_servers=mcp_servers,
    )
    return researcher


# 將研究員 Agent 包裝成工具 Tool
async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool())


# 交易員類別，負責管理交易流程
class Trader:
    # 初始化交易員物件
    def __init__(self, name: str, lastname="Trader", model_name="gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.agent = None
        self.model_name = model_name
        self.do_trade = True  # 是否執行交易（True: 交易, False: 重新平衡）

    # 建立交易員 Agent，並加入研究員工具
    async def create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        tool = await get_researcher_tool(researcher_mcp_servers, self.model_name)
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),  # 交易員指令
            model=get_model(self.model_name),
            tools=[tool],  # 加入研究員工具
            mcp_servers=trader_mcp_servers,
        )
        return self.agent

    # 取得交易員帳戶報告（移除 portfolio_value_time_series，僅回傳主要資訊）
    async def get_account_report(self) -> str:
        account = await read_accounts_resource(self.name)
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)

    # 執行交易或重新平衡流程
    async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        self.agent = await self.create_agent(trader_mcp_servers, researcher_mcp_servers)
        account = await self.get_account_report()
        strategy = await read_strategy_resource(self.name)
        # 根據 do_trade 狀態決定訊息內容
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        await Runner.run(self.agent, message, max_turns=MAX_TURNS)

    # 使用 MCP server 執行交易流程
    async def run_with_mcp_servers(self):
        # 使用 AsyncExitStack 管理多個 MCP server 的生命週期
        async with AsyncExitStack() as stack:
            trader_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]
            async with AsyncExitStack() as stack:
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)

    # 執行交易流程並加入 trace 追蹤
    async def run_with_trace(self):
        trace_name = (
            f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
        )
        trace_id = make_trace_id(f"{self.name.lower()}")
        with trace(trace_name, trace_id=trace_id):
            await self.run_with_mcp_servers()

    # 交易員主流程入口
    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        # 每次執行後切換 do_trade 狀態（交易/重新平衡）
        self.do_trade = not self.do_trade
