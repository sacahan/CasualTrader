# Agent 動態策略架構設計

**版本**: 1.0
**日期**: 2025-10-06
**相關設計**: AGENT_IMPLEMENTATION.md, SYSTEM_DESIGN.md
**基於**: OpenAI Agents SDK + 動態策略演化系統

---

## 📋 概述

本文檔詳細描述 CasualTrader 中四種 Agent 模式的動態策略系統架構，實現根據投資效益自動調整交易策略的智能機制。

### 核心設計理念

1. **台股交易時間限定**: 模式循環嚴格限定在台股交易時間（週一至週五 09:00-13:30）
2. **四階段交易循環**: 開盤前準備 → 早盤交易 → 中場調整 → 午盤交易 → 收盤檢討
3. **動態策略演化**: 基於實際投資效益自動生成和測試策略變體
4. **智能模式切換**: 交易時間內根據市場條件和性能指標動態切換
5. **非交易時間深度分析**: 收盤後進行深度市場研究和策略優化

### 台股交易時間架構

**交易日時間分配 (週一至週五)**:

- **08:30-09:00**: 開盤前準備 (OBSERVATION)
- **09:00-11:00**: 早盤交易 (TRADING)
- **11:00-11:30**: 中場調整 (REBALANCING)
- **11:30-13:00**: 午盤交易 (TRADING)
- **13:00-13:30**: 收盤檢討 (STRATEGY_REVIEW)

**非交易時間**:

- **13:30-次日08:30**: 深度觀察分析 (DEEP_OBSERVATION)
- **週末**: 週度策略檢討 (WEEKLY_REVIEW)

---

## 🤖 四種 Agent 模式詳細設計

### 1. OBSERVATION 模式 - 開盤前準備

**交易日時間**: 08:30-09:00 (30分鐘)
**主要目標**: 開盤前市場分析和交易準備

#### 執行策略

```python
class PreMarketObservationMode:
    """開盤前準備模式執行邏輯"""

    async def execute(self):
        # 1. 盤前重要資訊掃描
        overnight_news = await self.scan_overnight_developments()

        # 2. 美股收盤影響分析
        us_market_impact = await self.analyze_us_market_close()

        # 3. 今日交易計畫檢視
        trading_plan = await self.review_daily_trading_plan()

        # 4. 風險因子更新
        risk_factors = await self.update_risk_factors()

        # 5. 開盤交易清單準備
        await self.prepare_opening_watchlist(overnight_news, us_market_impact)
```

#### 核心任務

- **盤前資訊掃描**: 檢視隔夜重要新聞、公告、國際市場動態
- **美股影響分析**: 分析美股收盤對台股可能影響
- **交易計畫檢視**: 確認今日交易目標和策略重點
- **風險因子更新**: 檢查可能影響今日交易的風險事件
- **開盤清單準備**: 準備開盤後優先關注的股票清單

#### 觸發條件

- 交易日 08:30 定時啟動
- 重大突發事件 (政策宣布、財報意外等)
- 美股大幅波動 (±3%以上)
- 外匯市場異常波動

### 2. TRADING 模式 - 主動交易決策

**交易日時間**: 09:00-11:00 (早盤) + 11:30-13:00 (午盤) = 210分鐘
**主要目標**: 執行交易決策並獲取超額報酬

#### 執行策略

```python
class TradingMode:
    """交易模式執行邏輯"""

    async def execute_morning_session(self):
        """早盤交易執行 (09:00-11:00)"""
        # 1. 開盤動能分析
        opening_momentum = await self.analyze_opening_momentum()

        # 2. 主要交易執行
        primary_trades = await self.execute_primary_trades(opening_momentum)

        # 3. 早盤績效監控
        await self.monitor_morning_performance(primary_trades)

    async def execute_afternoon_session(self):
        """午盤交易執行 (11:30-13:00)"""
        # 1. 中場調整後市況評估
        market_reassessment = await self.reassess_market_conditions()

        # 2. 補充交易機會捕捉
        supplementary_trades = await self.capture_afternoon_opportunities()

        # 3. 收盤前部位調整
        await self.pre_close_position_adjustment()

    async def execute(self):
        # 根據交易時段執行對應策略
        current_time = datetime.now(taiwan_tz).time()

        if time(9, 0) <= current_time < time(11, 0):
            await self.execute_morning_session()
        elif time(11, 30) <= current_time < time(13, 0):
            await self.execute_afternoon_session()
```

#### 核心任務

**早盤交易 (09:00-11:00)**:

- **開盤動能捕捉**: 分析開盤價格行為和成交量變化
- **主要部位建立**: 執行主要交易決策，建立核心部位
- **趨勢確認**: 確認日內趨勢方向和強度

**午盤交易 (11:30-13:00)**:

- **機會補強**: 捕捉早盤錯過的交易機會
- **部位優化**: 調整持倉以優化風險收益比
- **收盤準備**: 為收盤做好部位管理準備

#### 觸發條件

- 定時調度 (早盤09:00、午盤11:30)
- 技術突破確認訊號
- 成交量異常放大 (>平均3倍)
- 重要消息發布觸發

#### 績效目標

- **日內超額報酬**: 目標單日超越基準 0.5%
- **勝率目標**: 維持 60% 以上勝率
- **最大單日回撤**: 不超過 2%
- **交易頻率**: 每日 1-3 筆主要交易

### 3. REBALANCING 模式 - 中場組合調整

**交易日時間**: 11:00-11:30 (30分鐘)
**主要目標**: 中場風險檢視和組合優化

#### 執行策略

```python
class MidSessionRebalancingMode:
    """中場重新平衡模式執行邏輯"""

    async def execute(self):
        # 1. 早盤交易效果評估
        morning_performance = await self.evaluate_morning_performance()

        # 2. 當前組合風險檢視
        current_risk_profile = await self.analyze_current_risk_exposure()

        # 3. 午盤策略調整決策
        afternoon_adjustments = await self.determine_afternoon_strategy()

        # 4. 快速風險調整
        risk_adjustments = await self.execute_risk_adjustments()

        # 5. 午盤交易準備
        await self.prepare_afternoon_trading_plan(afternoon_adjustments)
```

#### 核心任務

- **早盤檢討**: 快速評估早盤交易效果和部位狀況
- **風險檢視**: 檢查當前組合的風險暴露和集中度
- **部位調整**: 必要時進行快速的風險控制調整
- **策略微調**: 根據市場變化調整午盤交易策略
- **流動性管理**: 確保午盤有足夠的交易彈性

#### 觸發條件

- 定時調度 (11:00 固定啟動)
- 早盤單一部位虧損 >3%
- 組合集中度警示 (單股權重 >8%)
- 市場情緒指標異常變化

#### 目標指標

- **風險控制**: 確保組合風險在可控範圍
- **執行效率**: 30分鐘內完成所有調整
- **成本控制**: 調整成本不超過預期收益的10%

### 4. STRATEGY_REVIEW 模式 - 收盤檢討

**交易日時間**: 13:00-13:30 (30分鐘)
**主要目標**: 當日交易檢討和明日策略準備

#### 執行策略

```python
class PreCloseStrategyReviewMode:
    """收盤前策略檢討模式執行邏輯"""

    async def execute(self):
        # 1. 當日交易總結
        daily_summary = await self.summarize_daily_trading()

        # 2. 收盤前部位檢查
        final_position_check = await self.final_position_review()

        # 3. 隔夜風險評估
        overnight_risk = await self.assess_overnight_risks()

        # 4. 明日策略準備
        tomorrow_strategy = await self.prepare_next_day_strategy()

        # 5. 學習點記錄
        await self.record_daily_learnings(daily_summary)
```

#### 核心任務

- **當日總結**: 快速回顧當日所有交易決策和結果
- **部位檢查**: 確認收盤前部位是否符合風險要求
- **隔夜風險**: 評估持倉過夜的潛在風險
- **明日準備**: 基於當日學習調整明日交易計畫
- **經驗累積**: 記錄當日的成功經驗和改進點

#### 觸發條件

- 定時調度 (13:00 固定啟動)
- 當日異常績效 (±3%以上)
- 重要持股出現異常波動
- 收盤前重大消息發布

#### 評估指標

- **當日績效**: 與基準比較的超額報酬
- **執行品質**: 交易執行偏差和成本分析
- **風險控制**: 最大回撤和風險暴露檢查
- **策略適應性**: 對當日市場變化的反應評估

### 5. DEEP_OBSERVATION 模式 - 非交易時間深度分析

**非交易時間**: 13:30-次日08:30 (平日19小時)
**主要目標**: 深度市場研究和策略優化

#### 執行策略

```python
class DeepObservationMode:
    """非交易時間深度觀察模式"""

    async def execute_evening_analysis(self):
        """收盤後分析 (13:30-18:00)"""
        # 1. 當日市場深度檢討
        market_review = await self.conduct_daily_market_review()

        # 2. 個股深度研究
        stock_research = await self.deep_dive_stock_analysis()

        # 3. 策略績效全面評估
        strategy_evaluation = await self.comprehensive_strategy_evaluation()

    async def execute_overnight_monitoring(self):
        """隔夜監控 (18:00-次日08:30)"""
        # 1. 國際市場監控
        international_markets = await self.monitor_global_markets()

        # 2. 重大新聞事件追蹤
        news_monitoring = await self.track_significant_events()

        # 3. 策略模型優化
        model_optimization = await self.optimize_strategy_models()
```

#### 核心任務

- **深度研究**: 進行個股、產業、總經的深度分析
- **策略優化**: 基於當日結果優化交易策略和模型
- **國際監控**: 追蹤國際市場動態對台股的潛在影響
- **模型訓練**: 更新和訓練量化模型
- **知識累積**: 建立和更新市場知識圖譜

### 6. WEEKLY_REVIEW 模式 - 週末策略檢討

**週末時間**: 週六、週日
**主要目標**: 週度績效檢討和策略調整

#### 執行策略

```python
class WeeklyReviewMode:
    """週末策略檢討模式"""

    async def execute(self):
        # 1. 週度績效全面分析
        weekly_performance = await self.analyze_weekly_performance()

        # 2. 策略有效性評估
        strategy_effectiveness = await self.evaluate_strategy_effectiveness()

        # 3. 市場環境變化分析
        market_regime_analysis = await self.analyze_market_regime_changes()

        # 4. 下週策略調整
        next_week_strategy = await self.prepare_next_week_strategy()

        # 5. 策略演化決策
        if weekly_performance['needs_evolution']:
            await self.trigger_strategy_evolution(weekly_performance)
```

#### 核心任務

- **週度檢討**: 完整評估一週的交易績效和策略表現
- **策略演化**: 決定是否需要進行策略調整或演化
- **市場研究**: 深度分析市場環境和趨勢變化
- **下週準備**: 制定下週的交易計畫和重點關注事項

---

## 🕒 台股交易時間限定的狀態機架構

```python
from enum import Enum
from datetime import datetime, timedelta, time
import pytz

class AgentMode(Enum):
    # 交易時間模式
    OBSERVATION = "OBSERVATION"           # 開盤前準備
    TRADING = "TRADING"                   # 主動交易
    REBALANCING = "REBALANCING"           # 中場調整
    STRATEGY_REVIEW = "STRATEGY_REVIEW"   # 收盤檢討

    # 非交易時間模式
    DEEP_OBSERVATION = "DEEP_OBSERVATION"  # 深度分析
    WEEKLY_REVIEW = "WEEKLY_REVIEW"        # 週末檢討
    STANDBY = "STANDBY"                    # 待機模式

class TradingTimeManager:
    """台股交易時間管理器"""

    def __init__(self):
        self.taiwan_tz = pytz.timezone('Asia/Taipei')
        self.trading_schedule = {
            'pre_market': {'start': time(8, 30), 'end': time(9, 0), 'mode': AgentMode.OBSERVATION},
            'morning_trading': {'start': time(9, 0), 'end': time(11, 0), 'mode': AgentMode.TRADING},
            'mid_session': {'start': time(11, 0), 'end': time(11, 30), 'mode': AgentMode.REBALANCING},
            'afternoon_trading': {'start': time(11, 30), 'end': time(13, 0), 'mode': AgentMode.TRADING},
            'closing_review': {'start': time(13, 0), 'end': time(13, 30), 'mode': AgentMode.STRATEGY_REVIEW}
        }

    def get_current_mode(self, dt: datetime = None) -> AgentMode:
        """根據當前時間決定應該執行的模式"""
        if dt is None:
            dt = datetime.now(self.taiwan_tz)

        # 週末執行週度檢討
        if dt.weekday() >= 5:  # 週六日
            return AgentMode.WEEKLY_REVIEW

        # 非交易日待機
        if dt.weekday() > 4:
            return AgentMode.STANDBY

        current_time = dt.time()

        # 檢查是否在交易時間內
        for phase, schedule in self.trading_schedule.items():
            if schedule['start'] <= current_time < schedule['end']:
                return schedule['mode']

        # 非交易時間執行深度觀察
        return AgentMode.DEEP_OBSERVATION

    def get_next_mode_transition(self, dt: datetime = None) -> tuple[AgentMode, datetime]:
        """獲取下一個模式切換的時間和模式"""
        if dt is None:
            dt = datetime.now(self.taiwan_tz)

        current_mode = self.get_current_mode(dt)

        # 計算下一個切換時間
        for phase, schedule in self.trading_schedule.items():
            phase_start = dt.replace(
                hour=schedule['start'].hour,
                minute=schedule['start'].minute,
                second=0,
                microsecond=0
            )

            if phase_start > dt:
                return schedule['mode'], phase_start

        # 如果當天沒有更多切換，返回明天的第一個模式
        next_day = dt + timedelta(days=1)
        if next_day.weekday() < 5:  # 下一個交易日
            next_start = next_day.replace(hour=8, minute=30, second=0, microsecond=0)
            return AgentMode.OBSERVATION, next_start
        else:  # 週末
            return AgentMode.WEEKLY_REVIEW, next_day.replace(hour=9, minute=0, second=0, microsecond=0)
```

---

## 🔄 動態策略演化系統

### 策略變體生成機制

```python
class StrategyVariant:
    """策略變體定義"""

    def __init__(self, base_strategy: Dict, modifications: Dict,
                 creation_time: datetime, expected_improvement: float):
        self.base_strategy = base_strategy
        self.modifications = modifications
        self.creation_time = creation_time
        self.expected_improvement = expected_improvement
        self.trial_period = timedelta(days=7)  # 7天試驗期
        self.actual_performance: Optional[Dict] = None

    def to_prompt_context(self) -> str:
        """轉換為提示詞上下文"""
        context = f"STRATEGY EVOLUTION - Variant {self.creation_time.strftime('%Y%m%d_%H%M')}\n"
        context += f"Expected Improvement: {self.expected_improvement:.2%}\n\n"

        for category, changes in self.modifications.items():
            context += f"{category.upper()}:\n"
            for key, value in changes.items():
                context += f"  - {key}: {value}\n"
            context += "\n"

        return context
```

### 策略修改規則引擎

```python
class StrategyEvolutionEngine:
    """策略演化引擎"""

    def generate_modifications(self, performance_feedback: Dict) -> Dict:
        """基於績效回饋生成策略修改"""
        modifications = {}

        # 風險管理調整
        if performance_feedback.get('sharpe_ratio', 0) < 0.5:
            modifications['risk_management'] = {
                'max_position_size': max(0.02, self.current_max_position * 0.6),
                'stop_loss_tightening': True,
                'volatility_filtering': True,
                'correlation_limit': 0.6
            }

        # 選股條件調整
        if performance_feedback.get('win_rate', 0) < 0.4:
            modifications['entry_criteria'] = {
                'technical_confirmation': True,
                'volume_confirmation': True,
                'trend_alignment': True,
                'fundamental_screening': True
            }

        # 持倉管理調整
        if performance_feedback.get('max_drawdown', 0) > 0.15:
            modifications['portfolio_management'] = {
                'diversification_requirement': True,
                'sector_rotation': True,
                'dynamic_hedging': True,
                'position_sizing_scaling': 0.8
            }

        # 交易頻率調整
        if performance_feedback.get('transaction_cost_ratio', 0) > 0.02:
            modifications['trading_frequency'] = {
                'holding_period_extension': True,
                'commission_consideration': True,
                'batch_trading': True
            }

        return modifications
```

### 性能評估框架

```python
class PerformanceEvaluator:
    """性能評估器"""

    async def evaluate_strategy_performance(self, period_start: datetime,
                                          period_end: datetime) -> Dict[str, float]:
        """評估策略在特定期間的表現"""

        # 獲取交易數據
        trades = await self.get_trades_in_period(period_start, period_end)
        portfolio_values = await self.get_portfolio_values(period_start, period_end)
        benchmark_values = await self.get_benchmark_values(period_start, period_end)

        # 計算基礎指標
        total_return = self.calculate_total_return(portfolio_values)
        benchmark_return = self.calculate_total_return(benchmark_values)
        volatility = self.calculate_volatility(portfolio_values)
        max_drawdown = self.calculate_max_drawdown(portfolio_values)

        # 計算風險調整指標
        sharpe_ratio = self.calculate_sharpe_ratio(portfolio_values)
        sortino_ratio = self.calculate_sortino_ratio(portfolio_values)
        alpha = self.calculate_alpha(portfolio_values, benchmark_values)
        beta = self.calculate_beta(portfolio_values, benchmark_values)
        information_ratio = self.calculate_information_ratio(portfolio_values, benchmark_values)

        # 計算交易指標
        win_rate = self.calculate_win_rate(trades)
        avg_win = self.calculate_average_win(trades)
        avg_loss = self.calculate_average_loss(trades)
        profit_factor = self.calculate_profit_factor(trades)

        return {
            'total_return': total_return,
            'benchmark_return': benchmark_return,
            'excess_return': total_return - benchmark_return,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'alpha': alpha,
            'beta': beta,
            'information_ratio': information_ratio,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'num_trades': len(trades),
            'needs_evolution': self.assess_evolution_need(sharpe_ratio, max_drawdown, win_rate)
        }
```

---

## ⚡ 模式切換控制系統

### 雙重驅動切換機制

```python
class AgentModeController:
    """Agent模式控制器"""

    def __init__(self, trader):
        self.trader = trader
        self.transition_rules = {
            'scheduled_cycle': [
                AgentMode.OBSERVATION,    # 17小時
                AgentMode.TRADING,        # 4小時
                AgentMode.REBALANCING,    # 1小時
                AgentMode.STRATEGY_REVIEW # 2小時
            ],
            'emergency_triggers': {
                'max_drawdown_10pct': (0.10, AgentMode.STRATEGY_REVIEW),
                'consecutive_losses_5': (5, AgentMode.OBSERVATION),
                'volatility_spike_30pct': (0.30, AgentMode.OBSERVATION),
                'correlation_spike_90pct': (0.90, AgentMode.REBALANCING)
            },
            'performance_triggers': {
                'exceptional_return_5pct': (0.05, AgentMode.STRATEGY_REVIEW),
                'low_volatility_period': (0.05, AgentMode.TRADING),
                'high_alpha_opportunity': (0.02, AgentMode.TRADING),
                'rebalance_drift_signal': (0.05, AgentMode.REBALANCING)
            }
        }

    async def check_mode_transition(self):
        """檢查並執行模式切換"""
        current_mode = self.trader.agent_state.current_mode
        mode_duration = datetime.now() - self.trader.agent_state.mode_start_time

        # 1. 緊急觸發檢查 (最高優先級)
        emergency_switch = await self.check_emergency_triggers()
        if emergency_switch:
            await self.transition_to_mode(emergency_switch[0], emergency_switch[1])
            return

        # 2. 性能觸發檢查
        performance_switch = await self.check_performance_triggers()
        if performance_switch:
            await self.transition_to_mode(performance_switch[0], performance_switch[1])
            return

        # 3. 時間調度檢查
        if mode_duration >= self.trader.agent_state.mode_duration_config[current_mode]:
            next_mode = self.get_next_scheduled_mode(current_mode)
            await self.transition_to_mode(next_mode, "scheduled_transition")
```

### 切換條件詳細定義

#### 緊急切換條件

```python
async def check_emergency_triggers(self) -> Optional[Tuple[AgentMode, str]]:
    """檢查緊急切換條件"""
    performance = await self.trader.performance_evaluator.get_current_metrics()

    # 最大回撤超過10%
    if performance.get('max_drawdown', 0) > 0.10:
        return (AgentMode.STRATEGY_REVIEW, "emergency_max_drawdown")

    # 連續虧損5筆交易
    if performance.get('consecutive_losses', 0) >= 5:
        return (AgentMode.OBSERVATION, "emergency_consecutive_losses")

    # 波動率異常飆升30%
    if performance.get('volatility_spike', 0) > 0.30:
        return (AgentMode.OBSERVATION, "emergency_volatility_spike")

    # 持股相關性過高90%
    if performance.get('portfolio_correlation', 0) > 0.90:
        return (AgentMode.REBALANCING, "emergency_high_correlation")

    return None
```

#### 性能觸發條件

```python
async def check_performance_triggers(self) -> Optional[Tuple[AgentMode, str]]:
    """檢查性能觸發條件"""
    performance = await self.trader.performance_evaluator.get_current_metrics()
    current_mode = self.trader.agent_state.current_mode

    # 異常高報酬觸發策略檢討
    if (performance.get('daily_return', 0) > 0.05 and
        current_mode == AgentMode.TRADING):
        return (AgentMode.STRATEGY_REVIEW, "high_performance_review")

    # 低波動環境適合交易
    if (performance.get('market_volatility', 0) < 0.05 and
        current_mode == AgentMode.OBSERVATION):
        return (AgentMode.TRADING, "low_volatility_opportunity")

    # Alpha機會信號
    if (performance.get('alpha_opportunity_score', 0) > 0.02 and
        current_mode == AgentMode.OBSERVATION):
        return (AgentMode.TRADING, "alpha_opportunity")

    # 組合偏離信號
    if (performance.get('portfolio_drift', 0) > 0.05 and
        current_mode != AgentMode.REBALANCING):
        return (AgentMode.REBALANCING, "portfolio_drift_signal")

    return None
```

---

## 🎯 台股交易時間限定的實際運作流程

### 交易日完整流程示例

```python
async def run_taiwan_stock_trading_system():
    """運行台股交易時間限定的Agent系統"""

    # 初始化系統
    trader = TaiwanStockTradingAgent("TSETAgent", model_name="gpt-4o")
    time_manager = TaiwanStockTradingTimeManager()

    # 設定台股交易策略
    taiwan_stock_strategy = {
        "style": "taiwan_momentum",
        "risk_tolerance": "moderate",
        "time_horizon": "intraday",
        "max_position_size": 0.05,
        "stop_loss": 0.06,
        "target_sectors": ["semiconductor", "electronics", "financial"],
        "trading_hours_only": True,
        "currency": "TWD"
    }

    trader.strategy_manager.set_base_strategy(taiwan_stock_strategy)

    while True:
        current_time = datetime.now(time_manager.taiwan_tz)
        current_mode = time_manager.get_current_mode(current_time)

        try:
            match current_mode:
                case AgentMode.OBSERVATION:
                    # === 開盤前準備 (08:30-09:00) ===
                    logger.info("🌅 Starting pre-market preparation")
                    await trader.execute_pre_market_preparation()

                case AgentMode.TRADING:
                    # === 交易執行 (09:00-11:00, 11:30-13:00) ===
                    if time(9, 0) <= current_time.time() < time(11, 0):
                        logger.info("📈 Morning trading session")
                        await trader.execute_morning_trading()
                    elif time(11, 30) <= current_time.time() < time(13, 0):
                        logger.info("📊 Afternoon trading session")
                        await trader.execute_afternoon_trading()

                case AgentMode.REBALANCING:
                    # === 中場調整 (11:00-11:30) ===
                    logger.info("⚖️  Mid-session rebalancing")
                    await trader.execute_mid_session_rebalancing()

                case AgentMode.STRATEGY_REVIEW:
                    # === 收盤檢討 (13:00-13:30) ===
                    logger.info("📋 Pre-close review")
                    daily_summary = await trader.execute_pre_close_review()

                case AgentMode.DEEP_OBSERVATION:
                    # === 非交易時間深度分析 (13:30-次日08:30) ===
                    logger.info("🔍 Deep observation and analysis")
                    await trader.execute_deep_observation()

                case AgentMode.WEEKLY_REVIEW:
                    # === 週末檢討 (週六、週日) ===
                    logger.info("📅 Weekly strategy review")
                    weekly_results = await trader.execute_weekly_review()

                    # 決定是否需要策略演化
                    if weekly_results['needs_evolution']:
                        logger.info("🧬 Triggering strategy evolution")
                        await trader.trigger_strategy_evolution(weekly_results)

                case AgentMode.STANDBY:
                    # === 待機模式 ===
                    logger.info("💤 System standby")
                    await asyncio.sleep(300)  # 5分鐘後重新檢查

            # 等待下一個時間檢查點
            await asyncio.sleep(60)  # 每分鐘檢查一次

        except Exception as e:
            logger.error(f"Error in {current_mode.value}: {e}")
            # 緊急情況下切換到深度觀察模式
            await trader.emergency_mode_switch("error_recovery")
            await asyncio.sleep(180)  # 等待3分鐘後重試

class TaiwanStockTradingAgent:
    """台股交易專用Agent"""

    async def execute_pre_market_preparation(self):
        """開盤前準備 (08:30-09:00)"""
        tasks = [
            self.scan_overnight_news(),
            self.analyze_us_market_impact(),
            self.review_daily_trading_plan(),
            self.check_earnings_calendar(),
            self.prepare_opening_watchlist()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Pre-market preparation completed: {len([r for r in results if not isinstance(r, Exception)])} tasks successful")

    async def execute_morning_trading(self):
        """早盤交易 (09:00-11:00)"""
        # 1. 開盤動能分析
        opening_analysis = await self.analyze_opening_momentum()

        # 2. 執行主要交易
        if opening_analysis['trade_signals']:
            trading_results = await self.execute_primary_trades(opening_analysis)
            logger.info(f"Morning trades executed: {len(trading_results)} positions")

        # 3. 持續監控
        await self.monitor_intraday_performance()

    async def execute_afternoon_trading(self):
        """午盤交易 (11:30-13:00)"""
        # 1. 重新評估市場
        market_reassessment = await self.reassess_market_conditions()

        # 2. 捕捉午盤機會
        if market_reassessment['opportunities']:
            afternoon_trades = await self.capture_afternoon_opportunities()

        # 3. 收盤前調整
        await self.prepare_for_close()

    async def execute_mid_session_rebalancing(self):
        """中場重新平衡 (11:00-11:30)"""
        # 快速風險檢查和調整
        risk_assessment = await self.quick_risk_assessment()

        if risk_assessment['needs_adjustment']:
            adjustments = await self.execute_quick_adjustments(risk_assessment)
            logger.info(f"Mid-session adjustments: {adjustments}")

    async def execute_pre_close_review(self):
        """收盤前檢討 (13:00-13:30)"""
        daily_summary = {
            'trades_executed': await self.get_daily_trades(),
            'performance': await self.calculate_daily_performance(),
            'lessons_learned': await self.extract_daily_lessons(),
            'overnight_risks': await self.assess_overnight_risks(),
            'next_day_plan': await self.prepare_next_day_strategy()
        }

        await self.save_daily_summary(daily_summary)
        return daily_summary

    async def execute_deep_observation(self):
        """深度觀察分析 (非交易時間)"""
        if datetime.now(self.time_manager.taiwan_tz).hour < 18:
            # 收盤後深度分析 (13:30-18:00)
            await self.conduct_post_market_analysis()
        else:
            # 隔夜監控 (18:00-次日08:30)
            await self.overnight_monitoring()

    async def execute_weekly_review(self):
        """週末策略檢討"""
        weekly_analysis = {
            'weekly_performance': await self.analyze_weekly_performance(),
            'strategy_effectiveness': await self.evaluate_strategy_effectiveness(),
            'market_regime_changes': await self.detect_regime_changes(),
            'next_week_preparation': await self.prepare_next_week_strategy()
        }

        return weekly_analysis
```

### 台股交易時間模式切換示例

```python
async def demonstrate_mode_switching():
    """展示台股交易時間的模式切換"""

    time_manager = TaiwanStockTradingTimeManager()

    # 模擬一個完整交易日的模式切換
    trading_day_schedule = [
        (time(8, 30), "開盤前準備開始"),
        (time(9, 0), "早盤交易開始"),
        (time(11, 0), "中場調整開始"),
        (time(11, 30), "午盤交易開始"),
        (time(13, 0), "收盤檢討開始"),
        (time(13, 30), "深度觀察開始"),
    ]

    for schedule_time, description in trading_day_schedule:
        # 模擬到達指定時間
        simulated_datetime = datetime.now(time_manager.taiwan_tz).replace(
            hour=schedule_time.hour,
            minute=schedule_time.minute,
            second=0
        )

        current_mode = time_manager.get_current_mode(simulated_datetime)
        next_mode, next_time = time_manager.get_next_mode_transition(simulated_datetime)

        print(f"🕒 {schedule_time.strftime('%H:%M')} - {description}")
        print(f"   當前模式: {current_mode.value}")
        print(f"   下次切換: {next_time.strftime('%H:%M')} -> {next_mode.value}")
        print()

# 輸出示例：
# 🕒 08:30 - 開盤前準備開始
#    當前模式: OBSERVATION
#    下次切換: 09:00 -> TRADING
#
# 🕒 09:00 - 早盤交易開始
#    當前模式: TRADING
#    下次切換: 11:00 -> REBALANCING
#
# 🕒 11:00 - 中場調整開始
#    當前模式: REBALANCING
#    下次切換: 11:30 -> TRADING
#
# 🕒 11:30 - 午盤交易開始
#    當前模式: TRADING
#    下次切換: 13:00 -> STRATEGY_REVIEW
#
# 🕒 13:00 - 收盤檢討開始
#    當前模式: STRATEGY_REVIEW
#    下次切換: 13:30 -> DEEP_OBSERVATION
#
# 🕒 13:30 - 深度觀察開始
#    當前模式: DEEP_OBSERVATION
#    下次切換: 08:30(次日) -> OBSERVATION
```

### 策略演化實例

```python
async def strategy_evolution_example():
    """策略演化實例"""

    # 假設收到的績效回饋
    performance_feedback = {
        'sharpe_ratio': 0.3,      # 低於0.5閾值
        'win_rate': 0.35,         # 低於0.4閾值
        'max_drawdown': 0.18,     # 高於0.15閾值
        'volatility': 0.25,
        'alpha': -0.02,
        'transaction_cost_ratio': 0.025  # 高於0.02閾值
    }

    # 策略管理器生成修改建議
    strategy_manager = StrategyManager("DynamicTrader")
    modifications = strategy_manager._generate_modifications(performance_feedback)

    print("Generated Strategy Modifications:")
    print(json.dumps(modifications, indent=2))

    # 輸出示例:
    # {
    #   "risk_management": {
    #     "max_position_size": 0.03,
    #     "stop_loss_tightening": true,
    #     "volatility_filtering": true,
    #     "correlation_limit": 0.6
    #   },
    #   "entry_criteria": {
    #     "technical_confirmation": true,
    #     "volume_confirmation": true,
    #     "trend_alignment": true,
    #     "fundamental_screening": true
    #   },
    #   "portfolio_management": {
    #     "diversification_requirement": true,
    #     "sector_rotation": true,
    #     "dynamic_hedging": true,
    #     "position_sizing_scaling": 0.8
    #   },
    #   "trading_frequency": {
    #     "holding_period_extension": true,
    #     "commission_consideration": true,
    #     "batch_trading": true
    #   }
    # }

    # 創建策略變體
    variant = strategy_manager.create_strategy_variant(performance_feedback)

    # 在提示詞中應用新策略
    evolved_prompt = f"""
    {trader.base_instructions}

    STRATEGY EVOLUTION ACTIVE:
    {variant.to_prompt_context()}

    Apply these modifications in your trading decisions and risk management.
    Monitor the effectiveness of these changes over the trial period.
    """

    return variant, evolved_prompt
```

---

## 📊 監控和診斷

### 實時監控指標

```python
class SystemMonitor:
    """系統監控器"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()

    async def collect_real_time_metrics(self) -> Dict:
        """收集實時監控指標"""
        return {
            # 模式狀態
            'current_mode': self.agent.agent_state.current_mode.value,
            'mode_duration': self.calculate_mode_duration(),
            'mode_switches_today': self.count_mode_switches_today(),

            # 性能指標
            'current_drawdown': await self.calculate_current_drawdown(),
            'daily_pnl': await self.calculate_daily_pnl(),
            'position_count': await self.get_position_count(),
            'cash_utilization': await self.calculate_cash_utilization(),

            # 風險指標
            'portfolio_beta': await self.calculate_portfolio_beta(),
            'concentration_risk': await self.calculate_concentration_risk(),
            'sector_exposure': await self.get_sector_exposure(),

            # 策略指標
            'strategy_variant_active': self.is_strategy_variant_active(),
            'evolution_count': self.get_evolution_count(),
            'last_evolution_date': self.get_last_evolution_date(),

            # 系統健康
            'execution_errors': self.count_execution_errors(),
            'api_latency': await self.measure_api_latency(),
            'memory_usage': self.get_memory_usage()
        }
```

### 警報系統

```python
class AlertManager:
    """警報管理器"""

    def __init__(self):
        self.alert_rules = self.define_alert_rules()
        self.notification_channels = ['email', 'webhook', 'dashboard']

    def define_alert_rules(self) -> Dict:
        """定義警報規則"""
        return {
            'critical': {
                'max_drawdown_15pct': {'threshold': 0.15, 'action': 'immediate_stop'},
                'system_error_rate_high': {'threshold': 0.1, 'action': 'emergency_observation'},
                'api_failure_consecutive': {'threshold': 3, 'action': 'system_pause'}
            },
            'warning': {
                'win_rate_declining': {'threshold': 0.4, 'action': 'strategy_review'},
                'position_concentration': {'threshold': 0.15, 'action': 'rebalance_signal'},
                'memory_usage_high': {'threshold': 0.8, 'action': 'performance_check'}
            },
            'info': {
                'strategy_evolution': {'action': 'log_notification'},
                'mode_switch': {'action': 'status_update'},
                'exceptional_performance': {'threshold': 0.05, 'action': 'success_notification'}
            }
        }

    async def check_and_send_alerts(self, metrics: Dict):
        """檢查指標並發送警報"""
        for level, rules in self.alert_rules.items():
            for rule_name, rule_config in rules.items():
                if await self.evaluate_rule(rule_name, rule_config, metrics):
                    await self.send_alert(level, rule_name, metrics)
```

---

## 🔧 實作檢查清單

### 核心系統組件

- [ ] **AgentState** - 模式狀態管理
- [ ] **AgentModeController** - 模式切換控制器
- [ ] **StrategyManager** - 策略管理器
- [ ] **PerformanceEvaluator** - 性能評估器
- [ ] **StrategyEvolutionEngine** - 策略演化引擎

### 四種執行模式實作

- [ ] **ObservationMode** - 觀察模式執行邏輯
- [ ] **TradingMode** - 交易模式執行邏輯
- [ ] **RebalancingMode** - 重平衡模式執行邏輯
- [ ] **StrategyReviewMode** - 策略檢討模式執行邏輯

### 動態策略系統

- [ ] **StrategyVariant** - 策略變體定義
- [ ] **策略修改規則引擎** - 自動生成策略調整
- [ ] **性能回饋分析** - 基於結果的策略優化
- [ ] **提示詞動態生成** - 模式和策略適應的指令

### 切換控制機制

- [ ] **雙重驅動切換** - 時間 + 性能觸發
- [ ] **緊急切換條件** - 風險控制機制
- [ ] **性能觸發條件** - 機會捕捉機制
- [ ] **切換日誌記錄** - 決策可追溯性

### 監控和診斷

- [ ] **實時監控指標** - 系統健康檢查
- [ ] **警報系統** - 異常狀況通知
- [ ] **性能儀表板** - 可視化監控界面
- [ ] **診斷工具** - 問題分析和調試

### 測試和驗證

- [ ] **單元測試** - 各組件功能測試
- [ ] **整合測試** - 模式切換流程測試
- [ ] **回測驗證** - 策略演化效果驗證
- [ ] **壓力測試** - 極端市場條件測試

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
**相關文檔**: AGENT_IMPLEMENTATION.md, SYSTEM_DESIGN.md
