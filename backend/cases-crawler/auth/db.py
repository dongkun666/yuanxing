"""
LexPrime Auth Database 接入
2026-06-28 · W1 脚手架

策略: 复用 core.db.Database 单一连接池
- 跟 cases / laws / lawyers 共享同一张表空间 (SQLAlchemy metadata 统一)
- 避免连接池分裂 (生产 PG 资源宝贵)
- auth_users/auth_lawyer_profiles/auth_tokens/auth_otp_logs 4 表会跟 cases/laws/lawyers 共存
- W2 业务表分库时, 可独立切到独立 engine (现在 0 必要)
"""

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Database

# 复用现有 Database 单例
# 关键: 不在 auth 重新 create_engine, 避免多 connection pool
__all__ = ["Database", "get_db", "init_auth_tables"]


async def get_db() -> AsyncSession:
    """
    FastAPI Depends 用法:
        @app.post("/...")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with Database.session() as session:
        yield session


async def init_auth_tables() -> bool:
    """
    创建 auth_* 4 张表 (幂等)

    用法:
        python -m auth.db   # CLI 创建
        或 main.py startup 调用
    """
    # 导入 models 触发 SQLAlchemy 注册到 Base.metadata
    from core.models import Base  # noqa: F401
    from auth import models  # noqa: F401  # 触发模型注册

    if Database._engine is None:
        await Database.init()

    try:
        async with Database._engine.begin() as conn:
            # create_all 是幂等的, IF NOT EXISTS 语义
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ Auth tables created (auth_users / auth_lawyer_profiles / auth_tokens / auth_otp_logs)")
        return True
    except Exception as e:
        logger.error(f"✗ Auth tables init failed: {e}")
        return False


if __name__ == "__main__":
    """CLI 入口: python -m auth.db"""
    import asyncio

    async def main():
        success = await init_auth_tables()
        if success:
            logger.info("Auth schema ready.")
        else:
            logger.error("Auth schema init failed.")
            raise SystemExit(1)

    asyncio.run(main())
