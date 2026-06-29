"""
pytest 全局 fixtures
2026-06-28 · W1 脚手架

策略:
- 每个测试用独立 SQLite in-memory DB (隔离 + 0 副作用)
- 用 aiosqlite + StaticPool 保证单 connection 跨 session 复用
  (in-memory DB 多 connection 会看不到对方的表)
- W6 (lex-coder): pytest-asyncio auto mode 启用, async tests 直接写 async def 即可
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def event_loop():
    """pytest-asyncio 0.24+ 需要显式 event_loop fixture"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# W6 (lex-coder) - 启用 auto mode, 这样 async test/fixture 不需要 @pytest.mark.asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    每个测试拿一个干净的 in-memory DB
    - StaticPool 保证连接复用 (in-memory 必须)
    - expire_on_commit=False 避免 lazy load 跨 session 失败
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # 建表 (含 auth.* 4 张 + core.models 全部 + W12 A2 doc_workflow DocReviewState + Signature)
    from core.models import Base  # noqa: F401
    from core import doc_workflow as _doc_workflow  # noqa: F401  (注册 DocReviewState + Signature)
    from auth import models  # noqa: F401

    async with engine.begin() as conn:
        # W6 (lex-coder): 确保 review_scores 表在 metadata 中 (Side-effect import)
        from api import review_router  # noqa: F401
        # W7 (lex-coder): 注册 ReviewQuestion 表 (Side-effect import 已含在 review_router)
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    """
    FastAPI TestClient (用 httpx.AsyncClient + ASGITransport)
    关键: 手动驱动 lifespan, 否则 httpx ASGITransport 默认不触发 FastAPI 启动
    """
    from httpx import AsyncClient, ASGITransport
    from auth.main import app, lifespan

    async with lifespan(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
