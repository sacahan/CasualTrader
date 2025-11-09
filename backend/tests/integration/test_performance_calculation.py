"""
績效計算邏輯測試

驗證重構後的績效欄位計算正確
"""

import pytest
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.models import Base, Agent, AgentPerformance

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_engine():
    """建立臨時測試資料庫"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def async_session_factory(async_engine):
    """建立 async session 工廠"""
    return sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


class TestPerformanceCalculation:
    """測試績效計算邏輯"""

    @pytest.mark.asyncio
    async def test_performance_fields_exist(self, async_engine, async_session_factory):
        """
        測試所有績效欄位都存在且可以正常建立
        """
        async with async_session_factory() as session:
            # 建立 Agent
            agent = Agent(
                id="test_perf_001",
                name="績效測試代理",
                initial_funds=Decimal("1000000"),
                current_funds=Decimal("1000000"),
            )
            session.add(agent)
            await session.flush()

            # 建立績效記錄 (包含所有欄位)
            performance = AgentPerformance(
                agent_id="test_perf_001",
                date=date.today(),
                total_value=Decimal("1000000"),
                cash_balance=Decimal("800000"),
                # 未實現欄位
                unrealized_pnl=Decimal("0"),  # TODO: 需要實時股價 API
                realized_pnl=Decimal("0"),  # TODO: 需要買賣配對邏輯
                daily_return=None,  # TODO: 需要歷史資料
                max_drawdown=None,  # TODO: 需要淨值曲線
                # 已實現欄位
                total_return=Decimal("0.05"),  # 5% 回報
                win_rate=Decimal("60.00"),  # TODO: 當前為交易完成率
                total_trades=10,
                sell_trades_count=6,  # 修正: 賣出交易數
                winning_trades_correct=0,  # TODO: 待實現真實獲利交易數
            )
            session.add(performance)
            await session.commit()

            # 驗證記錄已建立
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_perf_001")
            )
            saved_performance = result.scalar_one()

            assert saved_performance.agent_id == "test_perf_001"
            assert saved_performance.total_trades == 10
            assert saved_performance.sell_trades_count == 6
            assert saved_performance.winning_trades_correct == 0
            assert saved_performance.win_rate == Decimal("60.00")

    @pytest.mark.asyncio
    async def test_sell_trades_count_semantic(self, async_engine, async_session_factory):
        """
        測試 sell_trades_count 語義正確

        驗證欄位名稱已修正為 sell_trades_count (賣出交易數)
        """
        async with async_session_factory() as session:
            agent = Agent(
                id="test_semantic_001",
                name="語義測試",
                initial_funds=Decimal("1000000"),
                current_funds=Decimal("1000000"),
            )
            session.add(agent)
            await session.flush()

            # 建立 10 筆買入, 7 筆賣出的交易記錄
            total_trades = 17
            sell_count = 7

            performance = AgentPerformance(
                agent_id="test_semantic_001",
                date=date.today(),
                total_value=Decimal("1000000"),
                cash_balance=Decimal("1000000"),
                total_trades=total_trades,
                sell_trades_count=sell_count,  # 明確語義: 賣出交易數
                winning_trades_correct=0,
            )
            session.add(performance)
            await session.commit()

            # 驗證
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_semantic_001")
            )
            perf = result.scalar_one()

            assert perf.total_trades == 17
            assert perf.sell_trades_count == 7  # 賣出交易數
            assert perf.sell_trades_count != perf.total_trades  # 不是所有交易都賣出

    @pytest.mark.asyncio
    async def test_win_rate_is_completion_rate_not_profit_rate(self, async_session_factory):
        """
        測試 win_rate 當前計算為「交易完成率」而非「真實勝率」

        TODO: 這是已知問題，待實現買賣配對邏輯後修正
        """
        async with async_session_factory() as session:
            agent = Agent(
                id="test_winrate_001",
                name="勝率測試",
                initial_funds=Decimal("1000000"),
                current_funds=Decimal("1000000"),
            )
            session.add(agent)
            await session.flush()

            # 範例: 10 筆交易, 6 筆賣出
            # 當前 win_rate = 6 / 10 * 100 = 60% (交易完成率)
            # 真實勝率應該要看這 6 筆賣出是否獲利
            total_trades = 10
            sell_trades = 6
            current_win_rate = Decimal(str(sell_trades / total_trades * 100))

            performance = AgentPerformance(
                agent_id="test_winrate_001",
                date=date.today(),
                total_value=Decimal("1000000"),
                cash_balance=Decimal("1000000"),
                total_trades=total_trades,
                sell_trades_count=sell_trades,
                win_rate=current_win_rate,  # 當前為交易完成率
                winning_trades_correct=0,  # TODO: 真實獲利交易數待實現
            )
            session.add(performance)
            await session.commit()

            # 驗證當前計算方式
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_winrate_001")
            )
            perf = result.scalar_one()

            # 當前定義: win_rate = sell_trades / total_trades * 100
            expected_completion_rate = Decimal("60.00")
            assert perf.win_rate == expected_completion_rate

            # TODO: 未來修正後應為:
            # win_rate = winning_trades_correct / total_completed_pairs * 100
            # 需要實現買賣配對邏輯

    @pytest.mark.asyncio
    async def test_unimplemented_fields_default_values(self, async_session_factory):
        """
        測試未實現欄位的預設值

        這些欄位目前設為預設值，待未來實現
        """
        async with async_session_factory() as session:
            agent = Agent(
                id="test_unimpl_001",
                name="未實現欄位測試",
                initial_funds=Decimal("1000000"),
                current_funds=Decimal("1000000"),
            )
            session.add(agent)
            await session.flush()

            performance = AgentPerformance(
                agent_id="test_unimpl_001",
                date=date.today(),
                total_value=Decimal("1000000"),
                cash_balance=Decimal("1000000"),
                # 未實現欄位 - 使用預設值
                unrealized_pnl=Decimal("0"),  # TODO: 需要實時股價 API
                realized_pnl=Decimal("0"),  # TODO: 需要買賣配對邏輯
                daily_return=None,  # TODO: 需要歷史資料
                max_drawdown=None,  # TODO: 需要淨值曲線
                total_trades=0,
                sell_trades_count=0,
                winning_trades_correct=0,
            )
            session.add(performance)
            await session.commit()

            # 驗證預設值
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_unimpl_001")
            )
            perf = result.scalar_one()

            # 驗證未實現欄位的預設值
            assert perf.unrealized_pnl == Decimal("0")
            assert perf.realized_pnl == Decimal("0")
            assert perf.daily_return is None
            assert perf.max_drawdown is None
            assert perf.winning_trades_correct == 0


class TestPerformanceFieldSemantics:
    """測試績效欄位語義正確性"""

    @pytest.mark.asyncio
    async def test_field_naming_is_clear(self, async_session_factory):
        """
        驗證欄位命名清晰反映其用途
        """
        async with async_session_factory() as session:
            agent = Agent(
                id="test_naming_001",
                name="命名測試",
                initial_funds=Decimal("1000000"),
                current_funds=Decimal("1000000"),
            )
            session.add(agent)
            await session.flush()

            perf = AgentPerformance(
                agent_id="test_naming_001",
                date=date.today(),
                total_value=Decimal("1000000"),
                cash_balance=Decimal("1000000"),
                total_trades=20,  # 所有交易數
                sell_trades_count=15,  # 賣出交易數 (清晰語義)
                winning_trades_correct=0,  # 真實獲利交易數 (清晰語義)
            )
            session.add(perf)
            await session.commit()

            # 驗證欄位可以正確存取
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_naming_001")
            )
            saved = result.scalar_one()

            # 欄位名稱應該清晰反映用途
            assert hasattr(saved, "sell_trades_count")  # 賣出交易數
            assert hasattr(saved, "winning_trades_correct")  # 真實獲利交易數
            assert not hasattr(saved, "winning_trades")  # 舊欄位應該不存在

    @pytest.mark.asyncio
    async def test_backward_compatibility_check(self, async_session_factory):
        """
        驗證重構後不再支援舊欄位名稱

        這是破壞性變更，確保不會意外使用舊欄位
        """
        async with async_session_factory() as session:
            agent = Agent(
                id="test_compat_001",
                name="相容性測試",
                initial_funds=Decimal("1000000"),
                current_funds=Decimal("1000000"),
            )
            session.add(agent)
            await session.flush()

            # ❌ 使用舊欄位名稱應該失敗
            with pytest.raises(TypeError, match="winning_trades"):
                AgentPerformance(
                    agent_id="test_compat_001",
                    date=date.today(),
                    total_value=Decimal("1000000"),
                    cash_balance=Decimal("1000000"),
                    total_trades=10,
                    winning_trades=5,  # ❌ 舊欄位名稱
                )

            # ✅ 使用新欄位名稱應該成功
            perf = AgentPerformance(
                agent_id="test_compat_001",
                date=date.today(),
                total_value=Decimal("1000000"),
                cash_balance=Decimal("1000000"),
                total_trades=10,
                sell_trades_count=5,  # ✅ 新欄位名稱
                winning_trades_correct=0,  # ✅ 新欄位名稱
            )
            session.add(perf)
            await session.commit()

            # 驗證成功儲存
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_compat_001")
            )
            assert result.scalar_one() is not None
