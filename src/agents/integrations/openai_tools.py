"""
OpenAI Hosted Tools 整合
整合 WebSearchTool 和 CodeInterpreterTool
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class WebSearchResult(BaseModel):
    """網路搜尋結果"""

    query: str
    results: list[dict[str, Any]]
    search_timestamp: datetime
    source: str = "web_search_tool"


class CodeExecutionResult(BaseModel):
    """程式碼執行結果"""

    code: str
    output: str
    error: str | None = None
    execution_time: float
    timestamp: datetime
    language: str = "python"


class OpenAIToolsIntegrator:
    """
    OpenAI Hosted Tools 整合器
    提供 WebSearchTool 和 CodeInterpreterTool 的統一介面
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("openai_tools_integrator")

    async def web_search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "general",
    ) -> WebSearchResult:
        """
        執行網路搜尋

        Args:
            query: 搜尋關鍵字
            max_results: 最大結果數量
            search_type: 搜尋類型 ("general", "news", "finance")

        Returns:
            搜尋結果
        """
        try:
            # 實際實作時會使用 OpenAI WebSearchTool
            # 目前返回模擬結果

            self.logger.info(f"Executing web search: {query}")

            # 模擬搜尋結果
            mock_results = [
                {
                    "title": f"搜尋結果 {i + 1} - {query}",
                    "url": f"https://example.com/result{i + 1}",
                    "snippet": f"這是關於 {query} 的搜尋結果摘要 {i + 1}",
                    "relevance_score": 0.9 - i * 0.1,
                }
                for i in range(min(max_results, 5))
            ]

            # 根據搜尋類型調整結果
            if search_type == "finance":
                for result in mock_results:
                    result["category"] = "財經新聞"
                    result["source"] = "financial_media"
            elif search_type == "news":
                for result in mock_results:
                    result["category"] = "新聞"
                    result["publish_date"] = datetime.now().isoformat()

            return WebSearchResult(
                query=query,
                results=mock_results,
                search_timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Web search failed for query '{query}': {e}")
            raise

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30,
    ) -> CodeExecutionResult:
        """
        執行程式碼

        Args:
            code: 要執行的程式碼
            language: 程式語言
            timeout: 執行超時時間（秒）

        Returns:
            執行結果
        """
        try:
            self.logger.info(f"Executing {language} code")

            # 實際實作時會使用 OpenAI CodeInterpreterTool
            # 目前返回模擬結果

            start_time = datetime.now()

            # 模擬程式碼執行
            if "import" in code and "pandas" in code:
                output = "DataFrame created successfully\nShape: (100, 5)\nColumns: ['date', 'open', 'high', 'low', 'close']"
            elif "plot" in code or "matplotlib" in code:
                output = "Plot generated successfully\nChart saved to memory"
            elif "calculate" in code or "math" in code:
                output = "Calculation completed\nResult: 42.85"
            else:
                output = f"Code executed successfully\nInput code:\n{code[:100]}..."

            execution_time = (datetime.now() - start_time).total_seconds()

            return CodeExecutionResult(
                code=code,
                output=output,
                execution_time=execution_time,
                timestamp=datetime.now(),
                language=language,
            )

        except Exception as e:
            self.logger.error(f"Code execution failed: {e}")
            return CodeExecutionResult(
                code=code,
                output="",
                error=str(e),
                execution_time=0.0,
                timestamp=datetime.now(),
                language=language,
            )

    async def search_financial_news(
        self,
        symbols: list[str] | None = None,
        keywords: list[str] | None = None,
        time_range: str = "24h",
    ) -> list[dict[str, Any]]:
        """
        搜尋財經新聞

        Args:
            symbols: 股票代碼列表
            keywords: 關鍵字列表
            time_range: 時間範圍

        Returns:
            新聞搜尋結果
        """
        search_terms = []

        if symbols:
            search_terms.extend([f"股票 {symbol}" for symbol in symbols])

        if keywords:
            search_terms.extend(keywords)

        if not search_terms:
            search_terms = ["台股 財經新聞"]

        query = " OR ".join(search_terms)

        result = await self.web_search(
            query=query, max_results=20, search_type="finance"
        )

        return result.results

    async def analyze_data_with_code(
        self,
        data_description: str,
        analysis_type: str = "statistical",
        code_template: str | None = None,
    ) -> dict[str, Any]:
        """
        使用程式碼分析數據

        Args:
            data_description: 數據描述
            analysis_type: 分析類型
            code_template: 程式碼模板

        Returns:
            分析結果
        """
        # 根據分析類型生成程式碼
        if analysis_type == "statistical":
            code = f"""
import pandas as pd
import numpy as np
from scipy import stats

# 數據分析: {data_description}
# 生成模擬數據進行統計分析
data = np.random.normal(100, 15, 1000)
df = pd.DataFrame({{'values': data}})

# 基本統計
mean_val = df['values'].mean()
std_val = df['values'].std()
median_val = df['values'].median()

print(f"平均值: {{mean_val:.2f}}")
print(f"標準差: {{std_val:.2f}}")
print(f"中位數: {{median_val:.2f}}")

# 正態性檢驗
statistic, p_value = stats.normaltest(data)
print(f"正態性檢驗 p-value: {{p_value:.4f}}")
            """
        elif analysis_type == "technical":
            code = f"""
import pandas as pd
import numpy as np

# 技術分析: {data_description}
# 計算技術指標
prices = np.random.uniform(95, 105, 30)
df = pd.DataFrame({{'close': prices}})

# 移動平均
df['ma5'] = df['close'].rolling(5).mean()
df['ma20'] = df['close'].rolling(20).mean()

# RSI 計算
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

print("技術指標計算完成")
print(f"當前價格: {{df['close'].iloc[-1]:.2f}}")
print(f"MA5: {{df['ma5'].iloc[-1]:.2f}}")
print(f"RSI: {{df['rsi'].iloc[-1]:.2f}}")
            """
        else:
            code = (
                code_template or f"# 自定義分析: {data_description}\nprint('分析完成')"
            )

        # 執行程式碼
        execution_result = await self.execute_code(code)

        return {
            "analysis_type": analysis_type,
            "data_description": data_description,
            "code_executed": execution_result.code,
            "output": execution_result.output,
            "error": execution_result.error,
            "execution_time": execution_result.execution_time,
            "success": execution_result.error is None,
            "timestamp": execution_result.timestamp,
        }

    async def research_investment_topic(
        self,
        topic: str,
        depth: str = "comprehensive",
        focus_areas: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        研究投資主題

        Args:
            topic: 研究主題
            depth: 研究深度
            focus_areas: 重點領域

        Returns:
            研究結果
        """
        # 構建搜尋查詢
        search_queries = [
            f"{topic} 投資分析",
            f"{topic} 市場趨勢",
            f"{topic} 財報分析",
        ]

        if focus_areas:
            for area in focus_areas:
                search_queries.append(f"{topic} {area}")

        # 執行多個搜尋
        research_results = []
        for query in search_queries[:3]:  # 限制搜尋次數
            try:
                search_result = await self.web_search(query, max_results=5)
                research_results.append(
                    {
                        "query": query,
                        "results": search_result.results,
                    }
                )
            except Exception as e:
                self.logger.warning(f"Search failed for query '{query}': {e}")

        # 分析數據
        analysis_code = f"""
# 投資主題研究分析: {topic}
import json

research_data = {research_results}

# 統計分析
total_results = sum(len(r['results']) for r in research_data)
unique_sources = set()

for research in research_data:
    for result in research['results']:
        if 'source' in result:
            unique_sources.add(result['source'])

print(f"研究主題: {topic}")
print(f"總搜尋結果: {{total_results}}")
print(f"資料來源數量: {{len(unique_sources)}}")
print(f"研究深度: {depth}")

# 生成摘要洞察
insights = [
    "市場關注度較高，相關資訊豐富",
    "建議進一步分析基本面數據",
    "技術面走勢需要持續關注"
]

for i, insight in enumerate(insights, 1):
    print(f"洞察 {{i}}: {{insight}}")
        """

        analysis_result = await self.execute_code(analysis_code)

        return {
            "topic": topic,
            "research_depth": depth,
            "focus_areas": focus_areas or [],
            "search_results": research_results,
            "analysis": {
                "code": analysis_result.code,
                "output": analysis_result.output,
                "success": analysis_result.error is None,
            },
            "summary": f"完成 {topic} 的 {depth} 研究分析",
            "timestamp": datetime.now(),
        }

    def get_tool_capabilities(self) -> dict[str, Any]:
        """獲取工具功能說明"""
        return {
            "web_search_tool": {
                "description": "網路資訊搜尋和市場新聞收集",
                "capabilities": [
                    "即時市場新聞搜尋",
                    "公司資訊查詢",
                    "產業趨勢研究",
                    "政策法規查詢",
                    "競爭對手分析",
                ],
                "best_use_cases": [
                    "獲取最新財經新聞",
                    "研究投資主題",
                    "市場情緒分析",
                    "事件驅動分析",
                ],
            },
            "code_interpreter_tool": {
                "description": "程式碼執行和量化分析",
                "capabilities": [
                    "統計分析計算",
                    "技術指標運算",
                    "數據處理和清理",
                    "圖表生成",
                    "回測分析",
                ],
                "supported_libraries": [
                    "pandas",
                    "numpy",
                    "scipy",
                    "matplotlib",
                    "seaborn",
                    "sklearn",
                    "statsmodels",
                ],
                "best_use_cases": [
                    "量化分析計算",
                    "技術指標驗證",
                    "投資組合優化",
                    "風險指標計算",
                ],
            },
            "integration_features": [
                "搜尋結果程式碼分析",
                "數據驅動決策支持",
                "多源資訊整合",
                "實時計算驗證",
            ],
        }

    async def execute_integrated_analysis(
        self,
        symbol: str,
        analysis_request: str,
    ) -> dict[str, Any]:
        """
        執行整合分析（結合搜尋和程式碼分析）

        Args:
            symbol: 股票代碼
            analysis_request: 分析要求

        Returns:
            整合分析結果
        """
        # 第一步：搜尋相關資訊
        search_result = await self.search_financial_news(
            symbols=[symbol],
            keywords=[analysis_request],
        )

        # 第二步：使用程式碼分析數據
        analysis_result = await self.analyze_data_with_code(
            data_description=f"{symbol} - {analysis_request}",
            analysis_type="technical" if "技術" in analysis_request else "statistical",
        )

        return {
            "symbol": symbol,
            "analysis_request": analysis_request,
            "web_search": {
                "results_count": len(search_result),
                "top_results": search_result[:3],
            },
            "code_analysis": analysis_result,
            "integrated_summary": f"完成 {symbol} 的 {analysis_request} 整合分析",
            "timestamp": datetime.now(),
        }

    def get_web_search_tool(self) -> dict[str, Any]:
        """
        獲取 WebSearchTool 配置

        Returns:
            Web Search Tool 配置
        """
        return {
            "type": "web_search",
            "web_search": {
                "description": "搜尋最新市場新聞和資訊",
                "max_results": 10,
                "search_types": ["general", "news", "finance"],
            },
        }

    def get_code_interpreter_tool(self) -> dict[str, Any]:
        """
        獲取 CodeInterpreterTool 配置

        Returns:
            Code Interpreter Tool 配置
        """
        return {
            "type": "code_interpreter",
            "code_interpreter": {
                "description": "執行量化分析和計算",
                "supported_languages": ["python"],
                "timeout": 30,
                "libraries": [
                    "pandas",
                    "numpy",
                    "matplotlib",
                    "scipy",
                    "scikit-learn",
                ],
            },
        }
