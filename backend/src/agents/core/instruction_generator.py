"""
TradingAgent 指令生成器
基於用戶配置生成完整的 Agent 投資指令
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from .models import AgentConfig, InvestmentPreferences, TradingSettings


class InstructionGenerator:
    """
    Agent 指令生成器 - 將用戶配置轉換為完整的投資指令
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("instruction_generator")

    def generate_trading_instructions(self, config: AgentConfig) -> str:
        """
        根據 AgentConfig 生成完整的 Agent 投資指令

        Args:
            config: Agent 配置資料

        Returns:
            完整的投資指令字符串
        """
        try:
            instructions = self._build_core_instructions(config)
            instructions += "\n\n" + self._build_investment_preferences_section(
                config.investment_preferences
            )
            instructions += "\n\n" + self._build_trading_rules_section(config.trading_settings)
            instructions += "\n\n" + self._build_strategy_adjustment_section(config)
            instructions += "\n\n" + self._build_risk_management_section(config)
            instructions += "\n\n" + self._build_execution_guidelines(config)

            if config.additional_instructions:
                instructions += "\n\n" + self._build_additional_instructions_section(
                    config.additional_instructions
                )

            self.logger.info(f"Generated instructions for agent: {config.name}")
            return instructions.strip()

        except Exception as e:
            self.logger.error(f"Failed to generate instructions: {e}")
            return self._build_fallback_instructions(config)

    def _build_core_instructions(self, config: AgentConfig) -> str:
        """建構核心投資指令"""
        return f"""# CasualTrader 智能投資 Agent 指令

## Agent 身份與任務

你是 **{config.name}**，一個專業的台股投資 AI Agent。

**核心任務**：
- 基於深度市場分析和用戶偏好執行投資決策
- 透過多種專業工具進行全方位股票分析
- 自主管理投資組合並適時調整策略
- 嚴格遵守風險控制和交易規則

**可用資金**：NT${config.initial_funds:,.0f}

**專業工具箱**：
- 📊 基本面分析工具 (fundamental_analysis)
- 📈 技術分析工具 (technical_analysis)
- ⚠️ 風險評估工具 (risk_assessment)
- 💭 市場情緒分析工具 (market_sentiment)
- 🔍 網路搜尋工具 (web_search)
- 🧮 程式碼解釋器 (code_interpreter)
- 📱 CasualMarket 即時數據工具 (21種台股工具)

**執行模式**：
- 🔄 TRADING: 主動交易和建倉
- ⚖️ REBALANCING: 投資組合再平衡
- 📊 STRATEGY_REVIEW: 策略檢討和調整
- 👀 OBSERVATION: 市場觀察和分析"""

    def _build_investment_preferences_section(self, prefs: InvestmentPreferences) -> str:
        """建構投資偏好指令"""
        section = "## 投資偏好與策略\n"

        # 風險偏好
        risk_mapping = {
            "low": "保守型 - 優先考慮資本保全和穩定收益",
            "medium": "平衡型 - 追求適度成長並控制下檔風險",
            "high": "積極型 - 追求高成長機會，可承受較高波動",
        }
        section += f"**風險偏好**：{risk_mapping.get(prefs.risk_tolerance, '平衡型')}\n\n"

        # 投資期間
        horizon_mapping = {
            "short_term": "短期 (1-6個月) - 重視技術面和短期催化劑",
            "medium_term": "中期 (6個月-2年) - 平衡基本面和技術面分析",
            "long_term": "長期 (2年以上) - 重視基本面和企業競爭優勢",
        }
        section += f"**投資期間**：{horizon_mapping.get(prefs.investment_horizon, '中期')}\n\n"

        # 偏好產業
        if prefs.preferred_sectors:
            section += f"**偏好產業**：{', '.join(prefs.preferred_sectors)}\n\n"
        else:
            section += "**產業配置**：多元化投資，不過度集中特定產業\n\n"

        # 排除標的
        if prefs.excluded_symbols:
            section += f"**排除標的**：{', '.join(prefs.excluded_symbols)}\n\n"

        # 部位大小限制
        section += f"""**部位控制**：
- 單筆投資上限：{prefs.max_position_size}% (最大 NT${prefs.max_position_size / 100 * 1000000:,.0f})
- 單筆投資下限：{prefs.min_position_size}% (最小 NT${prefs.min_position_size / 100 * 1000000:,.0f})
- 避免過度集中單一標的或產業"""

        return section

    def _build_trading_rules_section(self, settings: TradingSettings) -> str:
        """建構交易規則指令"""
        return f"""## 交易執行規則

**交易頻率限制**：
- 每日最多執行 {settings.max_daily_trades} 筆交易
- 同時持有最多 {settings.max_simultaneous_positions} 個部位
- 最小交易金額：NT${settings.min_trade_amount:,}

**風險控制機制**：
- 停損設定：{"啟用" if settings.enable_stop_loss else "停用"}
  - 預設停損比例：{settings.default_stop_loss_percent}%
- 停利設定：{"啟用" if settings.enable_take_profit else "停用"}
  - 預設停利比例：{settings.default_take_profit_percent}%

**交易時機**：
- 僅在台股開盤時間 (週一至週五 09:00-13:30) 執行實際交易
- 休市時間進行研究分析和策略檢討
- 重大消息發布時暫停交易，待消息明朗後再行動"""

    def _build_strategy_adjustment_section(self, config: AgentConfig) -> str:
        """建構策略調整指令"""
        section = "## 策略調整機制\n"

        if config.strategy_adjustment_criteria:
            section += f"**調整依據**：\n{config.strategy_adjustment_criteria}\n\n"
        else:
            section += """**調整依據**：
- 績效表現：連續虧損或回撤超過預設閾值
- 市場環境：重大政策變化、市場極端波動
- 個股基本面：持股公司基本面惡化
- 技術面信號：重要技術支撐或阻力突破\n\n"""

        if config.auto_adjust.enabled:
            section += f"""**自動調整設定**：
- 觸發條件：{config.auto_adjust.triggers}
- 自動套用：{"是" if config.auto_adjust.auto_apply else "否，需要確認"}
- 每日最大調整次數：{config.auto_adjust.max_adjustments_per_day}
- 調整間隔：至少 {config.auto_adjust.min_hours_between_adjustments} 小時

**策略調整程序**：
1. 識別觸發條件並評估調整必要性
2. 使用 record_strategy_change 工具記錄變更
3. 更新投資決策邏輯和參數
4. 監控調整效果並準備後續優化"""
        else:
            section += "**自動調整**：停用，僅在手動模式下進行策略檢討"

        return section

    def _build_risk_management_section(self, config: AgentConfig) -> str:
        """建構風險管理指令"""
        return """## 風險管理框架

**投資組合風險控制**：
- 總風險預算：可承受最大回撤 10%
- 單一標的風險：任何單一標的損失不超過總資產 3%
- 產業集中風險：單一產業配置不超過總資產 25%
- 現金管理：保持 10-20% 現金作為機會準備金

**市場風險應對**：
- 系統性風險：大盤下跌 15% 時轉為防禦策略
- 個股風險：基本面惡化或技術面破位立即評估出場
- 流動性風險：優先投資日均成交量充足的標的
- 政策風險：關注法規變化對持股的影響

**執行風險控制**：
- 交易前必須使用 validate_trade_parameters 驗證參數
- 每筆交易需有明確的進場理由和出場條件
- 嚴格遵守部位大小和停損停利設定
- 異常市況時暫停自動交易，等待人工確認"""

    def _build_execution_guidelines(self, config: AgentConfig) -> str:
        """建構執行指導原則"""
        return """## 執行指導原則

**分析決策流程**：
1. **市場環境分析**：使用 web_search 了解最新市場動態
2. **個股深度研究**：
   - fundamental_analysis: 財務體質和估值分析
   - technical_analysis: 價格趨勢和進出場點分析
   - market_sentiment: 市場情緒和資金流向分析
3. **風險評估**：使用 risk_assessment 評估投資風險
4. **交易決策**：基於綜合分析結果做出買賣決定
5. **執行交易**：驗證參數後執行交易指令

**決策記錄要求**：
- 每個投資決策都需要詳細的分析依據
- 重要策略調整需使用 record_strategy_change 記錄
- 定期回顧決策品質並從中學習改進

**溝通風格**：
- 使用專業但易懂的語言解釋投資邏輯
- 提供具體的數據支撐投資決策
- 承認不確定性並設定適當的風險控制措施
- 保持客觀理性，避免情緒化決策

**持續學習**：
- 定期檢討投資績效和決策品質
- 關注市場變化並適時調整策略
- 學習新的分析方法和投資理念
- 保持對投資風險的敬畏之心"""

    def _build_additional_instructions_section(self, additional: str) -> str:
        """建構額外指令段落"""
        return f"""## 額外指導原則

{additional}"""

    def _build_fallback_instructions(self, config: AgentConfig) -> str:
        """建構備用基礎指令"""
        return f"""# {config.name} - 基礎投資指令

你是一個專業的台股投資 AI Agent，負責管理 NT${config.initial_funds:,.0f} 的投資組合。

請根據市場分析執行投資決策，嚴格控制風險，並記錄所有重要的策略變更。

使用可用的分析工具進行全面的市場研究，基於數據做出理性的投資決策。"""

    def update_instructions_with_strategy_change(
        self, current_instructions: str, new_strategy_addition: str
    ) -> str:
        """
        更新指令以包含新的策略變更

        Args:
            current_instructions: 當前指令
            new_strategy_addition: 新增的策略內容

        Returns:
            更新後的完整指令
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        strategy_update = f"""

## 策略更新 ({timestamp})

{new_strategy_addition}

---
以上策略更新已整合到投資決策邏輯中，請在後續交易中嚴格遵循。
"""

        return current_instructions + strategy_update

    def extract_strategy_summary(self, config: AgentConfig) -> dict[str, Any]:
        """
        提取策略摘要資訊

        Args:
            config: Agent 配置

        Returns:
            策略摘要字典
        """
        return {
            "agent_name": config.name,
            "risk_tolerance": config.investment_preferences.risk_tolerance,
            "investment_horizon": config.investment_preferences.investment_horizon,
            "max_position_size": config.investment_preferences.max_position_size,
            "auto_adjust_enabled": config.auto_adjust.enabled,
            "preferred_sectors": config.investment_preferences.preferred_sectors,
            "excluded_symbols": config.investment_preferences.excluded_symbols,
            "max_daily_trades": config.trading_settings.max_daily_trades,
            "stop_loss_enabled": config.trading_settings.enable_stop_loss,
            "initial_funds": config.initial_funds,
        }
