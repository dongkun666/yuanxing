"""
LexPrime 数据库连接 (PG / ES / Neo4j)
2026-06-28
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from elasticsearch import AsyncElasticsearch
from neo4j import AsyncGraphDatabase, AsyncDriver
from loguru import logger

from .config import settings


# ========== PostgreSQL ==========
class Database:
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None

    @classmethod
    async def init(cls):
        if cls._engine is None:
            cls._engine = create_async_engine(
                settings.database_url,
                echo=settings.api_debug,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
            )
            cls._session_factory = async_sessionmaker(
                cls._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            logger.info(f"PostgreSQL engine initialized: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

    @classmethod
    async def close(cls):
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None
            logger.info("PostgreSQL engine closed")

    @classmethod
    @asynccontextmanager
    async def session(cls) -> AsyncGenerator[AsyncSession, None]:
        if cls._session_factory is None:
            await cls.init()
        async with cls._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# ========== Elasticsearch ==========
class ESClient:
    _client: Optional[AsyncElasticsearch] = None

    @classmethod
    async def init(cls):
        if cls._client is None:
            cls._client = AsyncElasticsearch(
                hosts=[{
                    "scheme": settings.es_scheme,
                    "host": settings.es_host,
                    "port": settings.es_port,
                }],
                basic_auth=(settings.es_user, settings.es_password),
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True,
            )
            # 测试连接
            info = await cls._client.info()
            logger.info(f"Elasticsearch connected: {info['version']['number']}")

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("Elasticsearch client closed")

    @classmethod
    def get(cls) -> AsyncElasticsearch:
        if cls._client is None:
            raise RuntimeError("ESClient not initialized. Call init() first.")
        return cls._client


# ========== Neo4j ==========
class Neo4jClient:
    _driver: Optional[AsyncDriver] = None

    @classmethod
    async def init(cls):
        if cls._driver is None:
            cls._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                max_connection_pool_size=50,
            )
            # 测试连接
            async with cls._driver.session() as session:
                result = await session.run("RETURN 1 AS num")
                await result.single()
            logger.info(f"Neo4j connected: {settings.neo4j_uri}")

    @classmethod
    async def close(cls):
        if cls._driver:
            await cls._driver.close()
            cls._driver = None
            logger.info("Neo4j driver closed")

    @classmethod
    def get(cls) -> AsyncDriver:
        if cls._driver is None:
            raise RuntimeError("Neo4jClient not initialized. Call init() first.")
        return cls._driver
