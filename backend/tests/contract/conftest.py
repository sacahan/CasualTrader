"""
Contract 測試的共用 fixtures

為所有層間契約測試提供統一的設置
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base


@pytest.fixture
async def async_engine():
    """建立臨時測試資料庫"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
def async_session_factory(async_engine):
    """建立 async session 工廠"""

    class AsyncSessionFactory:
        def __init__(self, engine):
            self.engine = engine
            self.SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        def __call__(self):
            return self.SessionLocal()

    return AsyncSessionFactory(async_engine)
